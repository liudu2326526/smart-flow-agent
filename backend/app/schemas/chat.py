from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field

class Message(BaseModel):
    role: str
    content: str

class ChatCompletionRequest(BaseModel):
    model: str = "smart-flow-agent-v1"
    messages: List[Message]
    stream: bool = True
    session_id: str
    urls: Optional[List[str]] = []
    deep_thinking: bool = False
    
    class Config:
        json_schema_extra = {
            "example": {
                "model": "smart-flow-agent-v1",
                "messages": [
                    {"role": "user", "content": "Hello"}
                ],
                "stream": True,
                "session_id": "conv_123",
                "deep_thinking": True
            }
        }
