import os
from typing import Optional


def get_env(name: str, default: Optional[str] = None) -> Optional[str]:
    v = os.getenv(name)
    if v is not None:
        return v
    return default

