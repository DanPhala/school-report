import os


def get_env(name: str, default: str = None) -> str:
    v = os.getenv(name)
    if v:
        return v
    return default

