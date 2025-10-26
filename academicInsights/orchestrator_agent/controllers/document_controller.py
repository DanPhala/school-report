import logging
from fastapi import APIRouter, UploadFile, File, HTTPException, status
from fastapi.responses import JSONResponse

from services.document_service import DocumentService
from utils.http import RemoteServiceError

router = APIRouter()
logger = logging.getLogger(__name__)

service = DocumentService()


@router.post("/process-document")
async def process_document(file: UploadFile = File(...), source_language: str = None) -> JSONResponse:
    try:
        file_content = await file.read()
        normalization_data = await service.process_document(file_content, file.filename, file.content_type or "application/octet-stream", source_language)

        return JSONResponse(content=normalization_data, status_code=status.HTTP_200_OK)

    except RemoteServiceError as e:
        logger.exception("Remote service error: %s", e)
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Unexpected error in controller: %s", e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

