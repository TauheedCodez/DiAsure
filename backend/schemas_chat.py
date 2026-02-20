from pydantic import BaseModel
from datetime import datetime
from typing import List


class CreateChatResponse(BaseModel):
    chat_id: int
    title: str
    created_at: datetime


class ChatHistoryItem(BaseModel):
    chat_id: int
    title: str
    created_at: datetime


class MessageCreateRequest(BaseModel):
    content: str


class MessageResponse(BaseModel):
    id: int
    role: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


class ChatWithMessagesResponse(BaseModel):
    chat_id: int
    title: str
    created_at: datetime
    messages: List[MessageResponse]

class AIMessageRequest(BaseModel):
    content: str