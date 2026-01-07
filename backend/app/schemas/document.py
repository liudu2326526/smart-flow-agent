from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class DocumentBase(BaseModel):
    filename: str
    size: int
    status: str = "pending"

class DocumentInfo(BaseModel):
    id: int
    filename: str
    status: str
    uploaded_at: datetime
    size: int

class DocumentUploadResponse(BaseModel):
    id: int
    filename: str
    size: int
    status: str
    url: Optional[str] = None

class DocumentResponse(BaseModel):
    code: int = 200
    message: str = "success"
    data: DocumentUploadResponse

class DocumentListResponse(BaseModel):
    code: int = 200
    message: str = "success"
    data: List[DocumentInfo]
