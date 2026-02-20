from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, JSON, Float, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.dialects.postgresql import JSONB


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)

    password_hash = Column(String, nullable=False)
    
    # Email verification
    email_verified = Column(Boolean, default=False, nullable=False)
    verification_token = Column(String, unique=True, nullable=True)
    verification_token_expires = Column(DateTime, nullable=True)
    
    # Password reset
    reset_token = Column(String, unique=True, nullable=True)
    reset_token_expires = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    chats = relationship("Chat", back_populates="user", cascade="all, delete")



class Chat(Base):
    __tablename__ = "chats"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey(
        "users.id", ondelete="CASCADE"), nullable=False)

    title = Column(String, default="New Chat")
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="chats")
    messages = relationship(
        "Message", back_populates="chat", cascade="all, delete-orphan")


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)

    chat_id = Column(Integer, ForeignKey(
        "chats.id", ondelete="CASCADE"), nullable=False)

    role = Column(String, nullable=False)  # "user" or "assistant"
    content = Column(Text, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    chat = relationship("Chat", back_populates="messages")


class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(Integer, ForeignKey(
        "chats.id", ondelete="CASCADE"), nullable=False)

    is_foot = Column(String, nullable=False)  # "yes" / "no"
    severity = Column(String, nullable=True)  # low/medium/high
    confidence = Column(Float, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)


class PatientState(Base):
    __tablename__ = "patient_states"

    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(Integer, ForeignKey(
        "chats.id", ondelete="CASCADE"), nullable=False)

    state_json = Column(MutableDict.as_mutable(JSONB), nullable=False)

    updated_at = Column(DateTime, default=datetime.utcnow)
