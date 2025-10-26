import asyncio
import logging
from typing import Dict, Any

from models.Request import NormalizeInput
from mapping import normalize_with_llm
from translation import translate_to_english

logger = logging.getLogger(__name__)


async def normalize_document(input_data: NormalizeInput) -> Dict[str, Any]:
    """
    Async service-layer wrapper that runs blocking translation and LLM calls
    in a threadpool to avoid blocking the event loop.
    Returns a dict suitable for JSONResponse (status + report_card).
    """
    try:
        if input_data.text:
            translated = await asyncio.to_thread(translate_to_english, input_data.text)
            raw_for_mapping = translated
        elif input_data.structured is not None:
            raw_for_mapping = input_data.structured
        else:
            raise ValueError("Provide 'text' or 'structured'")

        report_card = await asyncio.to_thread(
            normalize_with_llm,
            raw_for_mapping,
            input_data.source or "unknown",
            input_data.raw_format or "text",
            input_data.model or "gpt-4o-mini",
            input_data.temperature if input_data.temperature is not None else 0.0,
        )

        return {"status": "success", "report_card": report_card.dict()}

    except Exception as e:
        logger.exception("Normalization service error: %s", e)
        raise
