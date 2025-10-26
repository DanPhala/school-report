from pydantic import BaseModel
from typing import Any, Dict, Optional


class NormalizationServiceResponse(BaseModel):
    report_card: Optional[Dict[str, Any]] = None
    meta: Optional[Dict[str, Any]] = None
    raw: Optional[Any] = None

