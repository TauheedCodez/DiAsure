from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from database import get_db
from auth_routes import get_current_user
from models_db import Chat, Message, PatientState, User

from schemas_chat import AIMessageRequest
from groq_service import groq_chat
from dfu_state import default_patient_state
from qa_flow import QA_ORDER, QUESTION_TEXT, EXAMPLES
from qa_validator import validate_answer

router = APIRouter(prefix="/chat", tags=["AI Chat"])


# ---------------- HELPERS ----------------

def format_question(key: str) -> str:
    return (
        f"**Doctor Question:** {QUESTION_TEXT[key]}\n"
        f"{EXAMPLES[key]}"
    )


def next_unanswered_key(state: dict):
    for k in QA_ORDER:
        if state.get(k) is None:
            return k
    return None


def is_dfq_question(text: str) -> bool:
    t = text.lower().strip()
    if "?" in t:
        return True
    starters = ("what", "why", "how", "when", "can", "should", "is", "are", "do")
    return t.startswith(starters)

def generate_recommendation(state: dict) -> str:
    """
    Generates final risk classification and action plan
    based on CNN + clinical Q&A.
    """

    severity = state.get("severity")  # low / medium / high
    duration = state.get("ulcer_duration_days")
    sugar = state.get("blood_sugar_recent")
    
    # Convert duration to int for comparison (handle string "unknown" case)
    duration_days = None
    if duration is not None and duration != "unknown":
        try:
            duration_days = int(duration)
        except (ValueError, TypeError):
            duration_days = None

    fever = state.get("fever") is True
    pus = state.get("discharge") is True
    black = state.get("black_tissue") is True
    
    # Get pain level for conditions
    pain_level = state.get("pain_level")
    severe_pain = isinstance(pain_level, int) and pain_level >= 7

    # ---------------- EMERGENCY ----------------
    if fever or pus or black or severe_pain:
        return (
            "🔴 **RISK LEVEL: EMERGENCY**\n\n"
            "**Reason:** Signs of infection or tissue death detected "
            "(fever / pus / black tissue / severe pain).\n\n"
            "**What you should do NOW:**\n"
            "- Go to a hospital immediately\n"
            "- Do NOT self-medicate or apply home remedies\n"
            "- Keep the foot clean and avoid walking on it\n\n"
            "**Doctor to consult:**\n"
            "- Emergency department of nearby hospitals"
            "[[BUTTON:Find nearby hospitals:/find-doctors?query=hospital+near+me]]"
        )

    # ---------------- HIGH RISK ----------------
    very_high_sugar = False
    
    if isinstance(sugar, str) and "mg" in sugar:
        try:
            val = int("".join(filter(str.isdigit, sugar)))
            if val >= 250:
                very_high_sugar = True
        except:
            pass

    # Moderate pain (4-6 range)
    moderate_pain = isinstance(pain_level, int) and pain_level >= 4 and pain_level <= 6
    # no_pain = pain_level == 0

    if (
        severity in ["high", "medium"] or
        (duration_days is not None and duration_days > 14) or
        very_high_sugar or
        moderate_pain 
        # no_pain
    ):
        return (
            "🟠 **RISK LEVEL: HIGH RISK**\n\n"
            "**Reason:** Moderate–high ulcer severity, prolonged duration, "
            "or uncontrolled/unknown blood sugar.\n\n"
            "**Recommended actions:**\n"
            "- Avoid weight bearing on the affected foot\n"
            "- Daily wound cleaning and sterile dressing\n"
            "- Monitor blood sugar regularly\n\n"
            "**Doctor to consult:**\n"
            "- Podiatrist\n"
            "- Diabetologist"
            "[[BUTTON:Find nearby doctors:/find-doctors?doctorTypes=podiatrist,diabetologist]]"
        )

    # ---------------- LOWER RISK ----------------
    return (
        "🟢 **RISK LEVEL: LOWER RISK**\n\n"
        "**Reason:** No signs of infection, short duration, and low visual severity.\n\n"
        "**Recommended actions:**\n"
        "- Basic wound care and clean dressing\n"
        "- Maintain good foot hygiene\n"
        "- Follow diabetic diet and sugar control\n\n"
        "**Doctor to consult:**\n"
        "- Local physician\n"
        "- Diabetologist"
        "[[BUTTON:Find nearby doctors:/find-doctors?doctorTypes=physician,diabetologist]]"
    )

# ---------------- MAIN ROUTE ----------------

@router.post("/{chat_id}/ai-message")
def ai_message(
    chat_id: int,
    payload: AIMessageRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    content = payload.content.strip()
    if not content:
        raise HTTPException(status_code=400, detail="Message content required")

    chat = db.query(Chat).filter(
        Chat.id == chat_id,
        Chat.user_id == current_user.id
    ).first()

    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    # save user message
    db.add(Message(chat_id=chat.id, role="user", content=content))

    # load / init state
    state_row = db.query(PatientState).filter(
        PatientState.chat_id == chat.id
    ).first()

    if not state_row:
        state_row = PatientState(
            chat_id=chat.id,
            state_json=default_patient_state(),
            updated_at=datetime.utcnow()
        )
        db.add(state_row)
        db.commit()
        db.refresh(state_row)

    state = dict(state_row.state_json)

    # ==========================================================
    # MODE 1 — FREE CHAT (BEFORE IMAGE UPLOAD)
    # ==========================================================
    if not state.get("qa_active", False):
        system_prompt = """
You are a diabetic foot ulcer (DFU) medical assistant.
Rules:
- Explain DFU clearly and safely.
- Do NOT diagnose or prescribe medication.
- Be short and patient-friendly.
"""
        user_prompt = f"""
User message: {content}

Respond normally.
If relevant, gently mention that uploading an ulcer image allows personalized guidance.
"""
        answer = groq_chat(system_prompt, user_prompt)

        # answer += (
        #     "\n\nIf you want personalized guidance, "
        #     "you can upload an image of your foot ulcer."
        # )

        db.add(Message(chat_id=chat.id, role="assistant", content=answer))
        db.commit()

        return {
            "assistant_message": answer,
            "patient_state": state
        }

    # ==========================================================
    # MODE 2 — GUIDED Q&A (AFTER IMAGE UPLOAD)
    # ==========================================================

    current_key = state.get("current_question_key")
    if current_key is None:
        current_key = next_unanswered_key(state)
        state["current_question_key"] = current_key
        state["retry_count"] = 0

    # Q&A finished → FINAL RECOMMENDATION
    if current_key is None:
        state["qa_completed"] = True
        state["qa_active"] = False

        recommendation = generate_recommendation(state)

        final_msg = (
            "✅ Thank you. I now have the required information.\n\n"
            f"🧾 **Recommended Next Actions:**\n{recommendation}\n\n"
            "⚠️ This is not a medical diagnosis. Please consult a doctor."
        )

        state_row.state_json = state
        state_row.updated_at = datetime.utcnow()
        db.add(Message(chat_id=chat.id, role="assistant", content=final_msg))
        db.commit()

        return {
            "assistant_message": final_msg,
            "patient_state": state
        }
    
    # ---------------------------------------------
    # USER SKIPPED CURRENT QUESTION (dont know / skip)
    # ---------------------------------------------
    if content.lower().strip() in [
        "i don't know", "dont know", "don't know",
        "no idea", "not sure", "skip", "skip this",
        "next", "next question"
    ]:
        # treat as valid skip WITHOUT involving LLM
        state[current_key] = "unknown"
        state["retry_count"] = 0

        next_key = next_unanswered_key(state)
        state["current_question_key"] = next_key

        if     next_key:
            assistant_msg = (
                "Okay, we’ll move on.\n\n"
                f"{format_question(next_key)}"
            )
        else:
            state["qa_completed"] = True
            state["qa_active"] = False
            recommendation = generate_recommendation(state)

            assistant_msg = (
                "Thank you. I have enough information now.\n\n"
                f"{recommendation}\n\n"
                "⚠️ This is not a medical diagnosis. Please consult a doctor."
            )

        db.add(Message(chat_id=chat.id, role="assistant", content=assistant_msg))
        state_row.state_json = state
        state_row.updated_at = datetime.utcnow()
        db.commit()

        return {
            "assistant_message": assistant_msg,
            "patient_state": state
        }


    # ----------------------------------------------------------
    # USER ASKS A DFU QUESTION MID-Q&A
    # ----------------------------------------------------------
    if is_dfq_question(content):
        system_prompt = """
You are a DFU medical assistant.
Rules:
- Answer the user's question clearly.
- Do NOT give final advice yet.
- After answering, return to the pending question.
"""
        user_prompt = f"""
User question: {content}
Known severity: {state.get("severity")}
Known info: {state}

Answer briefly, then continue assessment.
"""
        reply = groq_chat(system_prompt, user_prompt)

        reply += "\n\nNow continuing your assessment:\n"
        reply += format_question(current_key)

        db.add(Message(chat_id=chat.id, role="assistant", content=reply))
        db.commit()

        return {
            "assistant_message": reply,
            "patient_state": state
        }

    # ----------------------------------------------------------
    # USER ANSWERING CURRENT QUESTION
    # ----------------------------------------------------------
    valid, value, normalized = validate_answer(current_key, content)

    if not valid:
        state["retry_count"] += 1

        retry_msg = (
            "I couldn’t understand that.\n\n"
            f"{format_question(current_key)}"
        )

        if state["retry_count"] >= 2:
            retry_msg += "\n\nYou may also reply with: `I don’t know`"

        db.add(Message(chat_id=chat.id, role="assistant", content=retry_msg))
        state_row.state_json = state
        state_row.updated_at = datetime.utcnow()
        db.commit()

        return {
            "assistant_message": retry_msg,
            "patient_state": state
        }

    # VALID ANSWER
    state[current_key] = value
    state["retry_count"] = 0

    next_key = next_unanswered_key(state)
    state["current_question_key"] = next_key

    if next_key:
        assistant_msg = (
            f"✅ Noted: {normalized}\n\n"
            f"{format_question(next_key)}"
        )
    else:
        state["qa_completed"] = True
        state["qa_active"] = False

        recommendation = generate_recommendation(state)

        assistant_msg = (
            f"✅ Noted: {normalized}\n\n"
            "🧾 **Final Assessment & Recommended Actions:**\n"
            f"{recommendation}\n\n"
            "⚠️ This is not a medical diagnosis. Please consult a doctor."
        )

    db.add(Message(chat_id=chat.id, role="assistant", content=assistant_msg))
    state_row.state_json = state
    state_row.updated_at = datetime.utcnow()
    db.commit()

    return {
        "assistant_message": assistant_msg,
        "patient_state": state
    }