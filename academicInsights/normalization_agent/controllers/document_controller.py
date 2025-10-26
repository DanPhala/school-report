from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
import logging
import asyncio

from models.Request import NormalizeInput
from models.Response import NormalizeResponse
from services.normalization_service import normalize_document

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health")
async def health_check():
    return {"status": "healthy", "service": "normalization_agent"}


@router.post("/translate")
async def translate_text(payload: NormalizeInput) -> JSONResponse:
    try:
        if not payload.text:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Provide 'text' to translate")
        from translation import translate_to_english

        translated = await asyncio.to_thread(translate_to_english, payload.text)
        return JSONResponse({"status": "success", "original": payload.text, "translated": translated}, status_code=status.HTTP_200_OK)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Translation endpoint error: %s", e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Translation failed")


@router.post("/normalize")
async def normalize(payload: NormalizeInput) -> JSONResponse:
    try:
        result = await normalize_document(payload)
        return JSONResponse(content=result, status_code=status.HTTP_200_OK)
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        logger.exception("Normalization endpoint error: %s", e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Normalization failed")
