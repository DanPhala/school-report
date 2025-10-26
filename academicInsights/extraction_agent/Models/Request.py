from pydantic import BaseModel
from typing import Optional

class ExtractRequest(BaseModel):
    url: Optional[str] = None
    filename: Optional[str] = None

__all__ = ["ExtractRequest"]
