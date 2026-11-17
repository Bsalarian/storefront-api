import os
import socket
import logging
from datetime import datetime, timezone
from fastapi import FastAPI, Response
from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format='{"time": "%(asctime)s", "level": "%(levelname)s", "service": "storefront-api", "message": "%(message)s"}',
)

logger = logging.getLogger("storefront-api")

app = FastAPI(title="Storefront API", version="1.0.0")
REQUEST_COUNT = Counter("app_requests_total", "Total HTTP requests", ["endpoint"])

@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response

@app.get("/")
def root():
    REQUEST_COUNT.labels(endpoint="/").inc()
    api_key_loaded = bool(os.getenv("API_KEY"))
    logger.info(f"Storefront status checked. Secret injected: {api_key_loaded}")

    return {
        "service": "storefront-api",
        "status": "operational",
        "environment": os.getenv("APP_ENV", "local"),
        "region": os.getenv("AWS_REGION", "eu-north-1"),
        "pod": socket.gethostname(),
        "sample_sku": {"id": "DUSTIN-ENT-001", "in_stock": True, "warehouse": "NORDICS-HUB"},
        "security": {"secret_mounted": api_key_loaded, "non_root_uid": os.getuid()},
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/health")
def health():
    return {"status": "healthy"}

@app.get("/metrics")
def metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)