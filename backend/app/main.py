import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

import logging
import json
import time
import uuid
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.routers import upload, profile, detect, score, explain, clean, report, adaptive

class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "timestamp": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(record.created)),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
        }
        if hasattr(record, "request_id"):
            log_record["request_id"] = record.request_id
        return json.dumps(log_record)

logger = logging.getLogger("anomaly_agent")
handler = logging.StreamHandler()
handler.setFormatter(JsonFormatter())
logger.addHandler(handler)
logger.setLevel(logging.INFO)

def create_app() -> FastAPI:
    app = FastAPI(
        title="AI Data Quality & Anomaly Detection Agent API",
        version="1.0.0",
        description="Deterministic data quality and anomaly detection with LLM explanations."
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def request_correlation_middleware(request: Request, call_next):
        req_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        response.headers["X-Request-ID"] = req_id
        response.headers["X-Process-Time"] = f"{process_time:.4f}s"
        logger.info(
            f"{request.method} {request.url.path} returned {response.status_code} in {process_time:.4f}s",
            extra={"request_id": req_id}
        )
        return response

    @app.get("/health", tags=["Health"])
    async def health():
        return {"status": "ok", "version": "1.0.0"}

    # Include all routers
    app.include_router(upload.router)
    app.include_router(profile.router)
    app.include_router(detect.router)
    app.include_router(score.router)
    app.include_router(explain.router)
    app.include_router(clean.router)
    app.include_router(report.router)
    app.include_router(adaptive.router)

    return app

app = create_app()
