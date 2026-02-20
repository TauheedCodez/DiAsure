from fastapi import APIRouter, HTTPException, UploadFile, File
from datetime import datetime
from PIL import Image, UnidentifiedImageError
import io

from schemas_chat import AIMessageRequest
from guest_store import create_guest_session, get_guest_session
from groq_service import groq_chat
from qa_flow import QA_ORDER, QUESTION_TEXT, EXAMPLES
from qa_validator import validate_answer

# Import shared logic from authenticated chat
from ai_chat_routes import format_question, next_unanswered_key, is_dfq_question, generate_recommendation

router = APIRouter(prefix="/guest", tags=["Guest Chat"])

# These will be injected from main.py (global loaded models)
foot_random_model = None
severity_model = None


def set_guest_models(filter_model, sev_model):
    global foot_random_model, severity_model
    foot_random_model = filter_model
    severity_model = sev_model


# Helper functions are now imported from ai_chat_routes


@router.post("/start")
def start_guest_chat():
    session_id = create_guest_session()
    return {
        "session_id": session_id,
        "message": "Guest chat started. This chat will not be saved."
    }


@router.post("/{session_id}/upload-image")
async def guest_upload_image(session_id: str, file: UploadFile = File(...)):
    session = get_guest_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Guest session expired")

    # Validate file type
    if file.content_type not in ["image/jpeg", "image/png", "image/jpg"]:
        raise HTTPException(status_code=400, detail="Only JPG/PNG images are allowed.")

    # Read and validate image
    try:
        contents = await file.read()
        pil_img = Image.open(io.BytesIO(contents))
    except UnidentifiedImageError:
        raise HTTPException(status_code=400, detail="Invalid image file or corrupted image.")
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to read image.")

    # Check if models are loaded
    if foot_random_model is None or severity_model is None:
        raise HTTPException(status_code=500, detail="Models not loaded on server")

    # Import predict_ulcer function
    from predict_service import predict_ulcer
    from dfu_state import default_patient_state
    
    # Predict
    result = predict_ulcer(pil_img, foot_random_model, severity_model)

    state = session["state"]
    messages = session["messages"]

    # Handle non-DFU images (same as authenticated chat)
    if not result["is_foot"]:
        reply = (
            "This image does not look like a foot/DFU image. "
            "Please upload a clear foot ulcer image (good lighting, full foot visible)."
        )
        messages.append({"role": "assistant", "content": reply})
        return {
            "status": "not_foot",
            "prediction": None,
            "assistant_message": reply,
            "patient_state": state
        }

    # Reset state completely - clear all previous Q&A answers
    fresh_state = default_patient_state()
    fresh_state["severity"] = result["severity"]
    fresh_state["qa_active"] = True
    fresh_state["qa_completed"] = False
    fresh_state["current_question_key"] = next_unanswered_key(fresh_state)
    fresh_state["retry_count"] = 0
    
    # Replace old state with fresh state
    session["state"] = fresh_state
    state = fresh_state

    # Create response message
    severity_map = {
        "low": "🟢 LOW",
        "medium": "🟠 MEDIUM",
        "high": "🔴 HIGH"
    }
    severity_display = severity_map.get(result["severity"], result["severity"].upper())

    reply = f"✅ **Image Analysis Complete**\n\n"
    reply += f"**Predicted Severity:** {severity_display}\n\n"
    reply += f"I will now ask you some questions to provide personalized recommendations.\n\n"
    reply += format_question(state["current_question_key"])

    messages.append({"role": "assistant", "content": reply})

    return {
        "status": "success",
        "prediction": result["severity"],
        "assistant_message": reply,
        "patient_state": state
    }


@router.post("/{session_id}/ai-message")
def guest_ai_message(session_id: str, payload: AIMessageRequest):
    session = get_guest_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Guest session expired")

    content = payload.content.strip()
    if not content:
        raise HTTPException(status_code=400, detail="Message required")

    state = session["state"]
    messages = session["messages"]

    messages.append({"role": "user", "content": content})

    # ===========================================================
    # MODE 1 — FREE CHAT (BEFORE IMAGE UPLOAD)
    # ===========================================================
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

        messages.append({"role": "assistant", "content": answer})
        return {
            "assistant_message": answer,
            "patient_state": state
        }

    # ===========================================================
    # MODE 2 — GUIDED Q&A (AFTER IMAGE UPLOAD)
    # ===========================================================

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

        messages.append({"role": "assistant", "content": final_msg})
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

        if next_key:
            assistant_msg = (
                "Okay, we'll move on.\n\n"
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

        messages.append({"role": "assistant", "content": assistant_msg})
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

        messages.append({"role": "assistant", "content": reply})
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
            "I couldn't understand that.\n\n"
            f"{format_question(current_key)}"
        )

        if state["retry_count"] >= 2:
            retry_msg += "\n\nYou may also reply with: `I don't know`"

        messages.append({"role": "assistant", "content": retry_msg})
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

    messages.append({"role": "assistant", "content": assistant_msg})
    return {
        "assistant_message": assistant_msg,
        "patient_state": state
    }
