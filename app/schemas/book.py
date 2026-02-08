
from pydantic import BaseModel
from typing import List, Optional

class Chapter(BaseModel):
    id: int
    title: str
    content: str
    status: str = "pending"
    audio_path: Optional[str] = None

class Book(BaseModel):
    name: str # folder name
    path: str # absolute path
    total: int
    completed: int
    status: str # pending, processing, completed
