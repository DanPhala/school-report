import logging
from pathlib import Path
from typing import Any, Dict

from utils import process_document
from settings import get_env

logger = logging.getLogger(__name__)


class ExtractionService:
    def __init__(self):
        val = get_env("PDF_DPI")
        try:
            self.pdf_dpi = int(val) if val is not None else 300
        except Exception:
            logger.warning("Invalid PDF_DPI value '%s', falling back to 300", val)
            self.pdf_dpi = 300

        self.tesseract_cmd = get_env("TESSERACT_CMD")
        if self.tesseract_cmd:
            try:
                import pytesseract
                pytesseract.pytesseract.tesseract_cmd = self.tesseract_cmd
            except Exception:
                logger.exception("Failed to set tesseract cmd from env")

    async def extract(self, file_path: Path, filename: str) -> Dict[str, Any]:
        result = await process_document(file_path, filename)
        return result.dict() if hasattr(result, 'dict') else result

