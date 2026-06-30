from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

class ChatRequest(BaseModel):
    session_id: str
    message: str
    language: Optional[str] = "English"
    topic_filter: Optional[List[str]] = None
    topic_name: Optional[str] = None

class ChatResponse(BaseModel):
    session_id: str
    response: str

class DocumentAnalysisResponse(BaseModel):
    session_id: str
    response: str
    filename: str
    file_type: str  # "image" ya "pdf"

class MessageOut(BaseModel):
    role: str
    message: str
    attachment_name: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class SessionOut(BaseModel):
    session_id: str
    title: str
    created_at: datetime

    class Config:
        from_attributes = True