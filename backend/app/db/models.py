from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlmodel import Field, SQLModel, Relationship, JSON
from sqlalchemy import Column
from sqlalchemy.types import JSON as JSONType

# User Model
class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    email: str = Field(unique=True)
    password_hash: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    conversations: List["Conversation"] = Relationship(back_populates="user")
    documents: List["Document"] = Relationship(back_populates="user")

# Conversation Model
class Conversation(SQLModel, table=True):
    id: str = Field(primary_key=True) # session_id (UUID)
    user_id: int = Field(foreign_key="user.id")
    title: Optional[str] = None
    is_deleted: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    user: User = Relationship(back_populates="conversations")
    messages: List["Message"] = Relationship(back_populates="conversation")

# Message Model
class Message(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: str = Field(foreign_key="conversation.id")
    type: str # human, ai, tool
    content: str
    response_metadata: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSONType))
    tool_calls: Optional[List[Dict[str, Any]]] = Field(default=None, sa_column=Column(JSONType))
    tool_call_id: Optional[str] = None
    name: Optional[str] = None # tool name
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    conversation: Conversation = Relationship(back_populates="messages")

# Document Model
class Document(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    filename: str
    file_path: str
    file_type: str
    size: int
    status: str = "pending" # pending, indexing, indexed, failed
    vector_id: Optional[str] = None
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    
    user: User = Relationship(back_populates="documents")
