import os
    
def get_env(name: str, default: str = None) -> str:
    v = os.getenv(name)
    if v is not None:
        return v
    return default

