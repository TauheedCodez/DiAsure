from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models_db import Chat, Message
from schemas_chat import (
    CreateChatResponse,
    ChatHistoryItem,
    MessageCreateRequest,
    ChatWithMessagesResponse,
)
from auth_routes import get_current_user
from models_db import User

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("/create", response_model=CreateChatResponse)
def create_chat(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    chat = Chat(user_id=current_user.id, title="New Chat")
    db.add(chat)
    db.commit()
    db.refresh(chat)

    return {
        "chat_id": chat.id,
        "title": chat.title,
        "created_at": chat.created_at
    }


@router.get("/history", response_model=list[ChatHistoryItem])
def get_chat_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    chats = (
        db.query(Chat)
        .filter(Chat.user_id == current_user.id)
        .order_by(Chat.created_at.desc())
        .all()
    )

    return [
        {
            "chat_id": c.id,
            "title": c.title,
            "created_at": c.created_at
        }
        for c in chats
    ]


@router.get("/{chat_id}", response_model=ChatWithMessagesResponse)
def get_chat_by_id(
    chat_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    chat = db.query(Chat).filter(Chat.id == chat_id, Chat.user_id == current_user.id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    return {
        "chat_id": chat.id,
        "title": chat.title,
        "created_at": chat.created_at,
        "messages": chat.messages
    }


@router.post("/{chat_id}/message")
def add_message(
    chat_id: int,
    payload: MessageCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    chat = db.query(Chat).filter(Chat.id == chat_id, Chat.user_id == current_user.id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    # Save user message
    user_msg = Message(chat_id=chat.id, role="user", content=payload.content)
    db.add(user_msg)

    # Temporary assistant reply (dummy) - later we connect chatbot AI
    assistant_reply_text = "Got it. (AI will be connected next)"
    assistant_msg = Message(chat_id=chat.id, role="assistant", content=assistant_reply_text)
    db.add(assistant_msg)

    db.commit()

    return {
        "status": "ok",
        "user_message": payload.content,
        "assistant_message": assistant_reply_text
    }

@router.delete("/{chat_id}")
def delete_chat(
    chat_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    chat = db.query(Chat).filter(
        Chat.id == chat_id,
        Chat.user_id == current_user.id
    ).first()

    if not chat:
        raise HTTPException(
            status_code=404,
            detail="Chat not found or you do not have permission"
        )

    db.delete(chat)
    db.commit()

    return {
        "status": "success",
        "message": f"Chat {chat_id} deleted successfully"
    }