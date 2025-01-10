from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel

class Message(SQLModel, table=True):
    """Message model for storing chat messages"""
    id: Optional[int] = Field(default=None, primary_key=True)
    message_question: str
    message_content: str
    chat_id: int = Field(index=True)
    role: str
    created_date: datetime = Field(default_factory=datetime.utcnow) 