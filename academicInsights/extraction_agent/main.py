from fastapi import FastAPI, UploadFile, File, HTTPException, status
from fastapi.responses import JSONResponse
import uvicorn
from pathlib import Path
import shutil
import logging
import tempfile

from controllers.document_controller import router as document_router
from fastapi import FastAPI
import logging
import uvicorn

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Extraction Agent", version="1.0.0")

app.include_router(document_router)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "extraction_agent"}


if __name__ == "__main__":
    logger.info("Starting Extraction Agent on port 8001...")
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")

if __name__ == "__main__":
    logger.info("Starting Extraction Agent on port 8001...")
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")