from typing import Optional
from pydantic import BaseModel

class ConversationCreate(BaseModel):
    user_id: str
    title: Optional[str] = None

class ConversationResponse(BaseModel):
    id: str
    title: str
    created_at: str
