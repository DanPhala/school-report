from typing import Optional, Dict, Any
from pydantic import BaseModel

class NormalizeInput(BaseModel):
    text: Optional[str] = None
    structured: Optional[Dict[str, Any]] = None
    source: Optional[str] = "unknown"
    raw_format: Optional[str] = "text"
    model: Optional[str] = "gpt-4o-mini"
    temperature: Optional[float] = 0.0
