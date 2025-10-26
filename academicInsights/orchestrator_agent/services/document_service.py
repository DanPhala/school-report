import logging
from typing import Dict, Any, Optional
from pathlib import Path

from utils.http import post_json, RemoteServiceError
from utils.settings import get_env

logger = logging.getLogger(__name__)


class DocumentService:
    def __init__(self):
        self.extraction_url = get_env("EXTRACTION_SERVICE")
        self.normalization_url = get_env("NORMALIZATION_SERVICE")
        if not self.extraction_url or not self.normalization_url:
            logger.warning("EXTRACTION_SERVICE or NORMALIZATION_SERVICE not set in environment")

    async def process_document(self, file_bytes: bytes, filename: str, content_type: str, source_language: Optional[str] = None) -> Dict[str, Any]:
        files = {"file": (filename, file_bytes, content_type)}
        try:
            extraction_response = await post_json(self.extraction_url + "/extract", files=files, timeout_seconds=60.0)
        except RemoteServiceError as e:
            logger.exception("Extraction call failed: %s", e)
            raise

        raw_text = extraction_response.get("raw_text", "")
        raw_format = extraction_response.get("metadata", {}).get("format", "unknown")

        normalize_payload = {
            "text": raw_text,
            "source": "extraction_agent",
            "raw_format": raw_format,
        }

        try:
            normalization_response = await post_json(self.normalization_url + "/normalize", json_payload=normalize_payload, timeout_seconds=180.0)
        except RemoteServiceError as e:
            logger.exception("Normalization call failed: %s", e)
            raise

        return normalization_response

