from fastapi import FastAPI, status
from fastapi.responses import JSONResponse
import logging
import httpx
import os
import uvicorn

from controllers.document_controller import router as document_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Orchestrator", version="1.0.0")

app.include_router(document_router)

@app.get("/health")
async def health_check():
    """Simple health check that probes downstream services."""
    try:
        extraction_url = os.getenv("EXTRACTION_SERVICE")
        normalization_url = os.getenv("NORMALIZATION_SERVICE")

        async with httpx.AsyncClient(timeout=5.0) as client:
            extraction_health = await client.get(f"{extraction_url}/health") if extraction_url else None
            normalization_health = await client.get(f"{normalization_url}/health") if normalization_url else None

        healthy = True
        services = {}
        if extraction_health is None or extraction_health.status_code != status.HTTP_200_OK:
            healthy = False
            services["extraction_agent"] = "unhealthy"
        else:
            services["extraction_agent"] = "healthy"

        if normalization_health is None or normalization_health.status_code != status.HTTP_200_OK:
            healthy = False
            services["normalization_agent"] = "unhealthy"
        else:
            services["normalization_agent"] = "healthy"

        return JSONResponse({"status": "healthy" if healthy else "degraded", "services": services})
    except Exception as e:
        logger.exception("Health check failed: %s", e)
        return JSONResponse({"status": "unhealthy", "error": str(e)}, status_code=status.HTTP_503_SERVICE_UNAVAILABLE)


if __name__ == "__main__":
    logger.info("Starting Orchestrator Agent on port 8000...")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")