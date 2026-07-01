from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from Backend.database import Base

class ChatHistory(Base):
    __tablename__ = "chat_history"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, index=True)
    role = Column(String)  # "user" ya "assistant"
    message = Column(Text)
    attachment_name = Column(String, nullable=True)  # uploaded file ka naam, agar koi ho
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
class Session(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, unique=True, index=True)
    title = Column(String, default="New Chat")  # pehle message se title banega
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())