from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from PIL import Image, UnidentifiedImageError
import io

from database import get_db
from auth_routes import get_current_user
from models_db import User, Chat, Message, Prediction, PatientState
from dfu_state import default_patient_state
from predict_service import predict_ulcer
from ai_chat_routes import next_unanswered_key, format_question

router = APIRouter(prefix="/chat", tags=["Upload + Predict"])


# These will be injected from main.py (global loaded models)
foot_random_model = None
severity_model = None


def set_models(filter_model, sev_model):
    global foot_random_model, severity_model
    foot_random_model = filter_model
    severity_model = sev_model


@router.post("/{chat_id}/upload-image")
async def upload_image_and_predict(
    chat_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # 1) check chat
    chat = db.query(Chat).filter(Chat.id == chat_id, Chat.user_id == current_user.id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    # 2) validate file
    if file.content_type not in ["image/jpeg", "image/png", "image/jpg"]:
        raise HTTPException(status_code=400, detail="Only JPG/PNG images are allowed.")

    # 3) read image
    try:
        contents = await file.read()
        pil_img = Image.open(io.BytesIO(contents))
    except UnidentifiedImageError:
        raise HTTPException(status_code=400, detail="Invalid image file or corrupted image.")
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to read image.")

    # 4) predict
    if foot_random_model is None or severity_model is None:
        raise HTTPException(status_code=500, detail="Models not loaded on server")

    result = predict_ulcer(pil_img, foot_random_model, severity_model)

    # 5) save prediction
    pred = Prediction(
        chat_id=chat.id,
        is_foot="yes" if result["is_foot"] else "no",
        severity=result["severity"],
        confidence=result["confidence"],
        created_at=datetime.utcnow()
    )
    db.add(pred)

    # 6) reset patient state completely on new image upload
    state_row = db.query(PatientState).filter(PatientState.chat_id == chat.id).first()
    
    # Create fresh state - clear all previous Q&A answers
    fresh_state = default_patient_state()
    
    if not state_row:
        state_row = PatientState(
            chat_id=chat.id,
            state_json=fresh_state,
            updated_at=datetime.utcnow()
        )
        db.add(state_row)
    else:
        # Reset existing state to fresh state
        state_row.state_json = fresh_state
        state_row.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(state_row)

    state = dict(state_row.state_json)

    # 7) update state severity and activate Q&A
    if result["is_foot"]:
        state["severity"] = result["severity"]

        state["qa_active"] = True
        state["qa_completed"] = False
        state["current_question_key"] = "ulcer_duration_days"   # first question
        state["retry_count"] = 0

    state_row.state_json = dict(state)
    state_row.updated_at = datetime.utcnow()

    # 8) assistant message after upload
    if not result["is_foot"]:
        assistant_text = (
            "This image does not look like a foot/DFU image. "
            "Please upload a clear foot ulcer image (good lighting, full foot visible)."
        )
    else:
        sev = result["severity"].upper()
        conf = round(float(result["confidence"]), 4)

        assistant_text = (
            f"Foot image accepted.\n"
            f"Predicted ulcer severity: **{sev}** (confidence: {conf}).\n\n"
            f"Now I will ask a few questions like a doctor to understand your case.\n"
        )

        q_key = next_unanswered_key(state)
        if q_key:
            assistant_text += f"\n{format_question(q_key)}"

    assistant_msg = Message(chat_id=chat.id, role="assistant", content=assistant_text)
    db.add(assistant_msg)

    db.commit()
    db.refresh(state_row)

    return {
        "status": result["status"],
        "prediction": result,
        "assistant_message": assistant_text,
        "patient_state": state
    }