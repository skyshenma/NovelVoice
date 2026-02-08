
from pydantic import BaseModel
from typing import Optional, List, Any

class TTSConfig(BaseModel):
    voice: str
    rate: str
    volume: str
    pitch: str

class GenerateRequest(BaseModel):
    book_name: str
    config: TTSConfig
    chapter_ids: Optional[List[int]] = None

class PreviewRequest(BaseModel):
    book_name: str
    chapter_id: Optional[int] = None
    text: Optional[str] = None
    config: TTSConfig

class CustomPreviewRequest(BaseModel):
    text: str
    voice: str
    rate: str = "+0%"
    volume: str = "+0%"
    pitch: Optional[str] = "+0Hz"
