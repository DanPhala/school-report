from pydantic import BaseModel
from typing import Optional, Dict, Any

class ExtractResponse(BaseModel):
    status: str = "success"
    filename: Optional[str] = None
    file_type: Optional[str] = None
    text: Optional[str] = None
    raw_text: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    structure: Optional[Dict[str, Any]] = None
    confidence: Optional[str] = None
    error: Optional[str] = None

    class Config:
        orm_mode = True

__all__ = ["ExtractResponse"]
