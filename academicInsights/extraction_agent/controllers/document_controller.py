import logging
from fastapi import APIRouter, UploadFile, File, HTTPException, status
from fastapi.responses import JSONResponse
from services.extraction_service import ExtractionService

router = APIRouter()
logger = logging.getLogger(__name__)

service = ExtractionService()


@router.post("/extract")
async def extract_document(file: UploadFile = File(...)) -> JSONResponse:
    try:
        from pathlib import Path
        import tempfile, shutil

        file_extension = Path(file.filename).suffix.lower()
        supported = {'.pdf', '.png', '.jpg', '.jpeg', '.tiff', '.bmp'}
        if file_extension not in supported:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unsupported file type: {file_extension}")

        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
            temp_path = Path(temp_file.name)
            shutil.copyfileobj(file.file, temp_file)

        result = await service.extract(temp_path, file.filename)
        try:
            temp_path.unlink()
        except Exception:
            logger.exception("Failed to remove temp file")

        return JSONResponse(content=result, status_code=status.HTTP_200_OK)

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error extracting document: %s", e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    finally:
        await file.close()


@router.post("/extract-batch")
async def extract_batch(files: list[UploadFile] = File(...)) -> JSONResponse:
    results = []
    for file in files:
        try:
            res = await extract_document(file)
            results.append(res.body if hasattr(res, 'body') else res)
        except Exception as e:
            results.append({"filename": getattr(file, 'filename', None), "status": "error", "error": str(e)})
    return JSONResponse(content={"results": results}, status_code=status.HTTP_200_OK)
