from fastapi import FastAPI
import uvicorn
import logging

from controllers.document_controller import router as document_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Normalization Agent", version="1.0.0")

app.include_router(document_router)


@app.get("/health")
async def health_root():
    return {"status": "healthy", "service": "normalization_agent"}


if __name__ == "__main__":
    logger.info("Starting Normalization Agent on port 8002...")
    uvicorn.run(app, host="0.0.0.0", port=8002, log_level="info")