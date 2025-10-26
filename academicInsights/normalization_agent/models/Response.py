from typing import Any, Dict
from pydantic import BaseModel

class NormalizeResponse(BaseModel):
    status: str
    report_card: Dict[str, Any]
