import logging
from typing import Any, Dict, Optional
import httpx

logger = logging.getLogger(__name__)


class RemoteServiceError(Exception):
    pass


async def post_json(url: str, json_payload: Optional[Dict[str, Any]] = None, files: Optional[Dict] = None, timeout_seconds: float = 60.0) -> Dict[str, Any]:
    timeout = httpx.Timeout(timeout_seconds, read=timeout_seconds)
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            if files:
                resp = await client.post(url, files=files)
            else:
                resp = await client.post(url, json=json_payload)
        except httpx.ReadTimeout as e:
            logger.exception("ReadTimeout while calling %s", url)
            raise RemoteServiceError(f"readtimeout: {e}") from e
        except httpx.RequestError as e:
            logger.exception("RequestError while calling %s", url)
            raise RemoteServiceError(f"requesterror: {e}") from e

        try:
            body = resp.json()
        except Exception:
            body = {"text": resp.text}

        if resp.status_code >= 400:
            logger.error("Remote service %s returned status %s body=%s", url, resp.status_code, body)
            raise RemoteServiceError(f"status={resp.status_code} body={body}")

        return body
