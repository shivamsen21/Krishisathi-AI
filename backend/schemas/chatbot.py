from pydantic import BaseModel, Field
from typing import Optional

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    crop: Optional[str] = None

class ChatMessageResponse(BaseModel):
    id: str
    user_id: Optional[str] = None
    role: str
    message: str
    created_at: str

class ChatResponse(BaseModel):
    reply: str
    message_id: Optional[str] = None
    role: str = "assistant"
