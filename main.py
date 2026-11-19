import os
import socket
import time
import logging
from datetime import datetime, timezone
from fastapi import FastAPI, Request, Response
from fastapi.responses import HTMLResponse
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format='{"time": "%(asctime)s", "level": "%(levelname)s", "service": "storefront-api", "message": "%(message)s"}',
)
logger = logging.getLogger("storefront-api")

app = FastAPI(title="Storefront API", version="1.0.0")

HTTP_REQUESTS = Counter(
    "http_requests_total", "Total HTTP requests", ["method", "endpoint", "status"]
)
HTTP_LATENCY = Histogram(
    "http_request_duration_seconds", "HTTP request latency in seconds", ["method", "endpoint"]
)


@app.middleware("http")
async def observability_and_security_headers(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    duration = time.perf_counter() - start

    HTTP_REQUESTS.labels(request.method, request.url.path, response.status_code).inc()
    HTTP_LATENCY.labels(request.method, request.url.path).observe(duration)

    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


@app.get("/")
def root(request: Request):
    api_key_loaded = bool(os.getenv("API_KEY"))
    logger.info(f"Storefront status checked. Secret injected: {api_key_loaded}")

    payload = {
        "service": "storefront-api",
        "status": "operational",
        "environment": os.getenv("APP_ENV", "local"),
        "region": os.getenv("AWS_REGION", "eu-north-1"),
        "pod": socket.gethostname(),
        "sample_sku": {"id": "DUSTIN-ENT-001", "in_stock": True, "warehouse": "NORDICS-HUB"},
        "security": {"secret_mounted": api_key_loaded, "non_root_uid": os.getuid()},
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    if "text/html" in request.headers.get("accept", ""):
        html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Storefront API — Status</title>
  <style>
    body {{ font-family: system-ui, sans-serif; background: #0f172a; color: #f8fafc; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; }}
    .card {{ background: #1e293b; border: 1px solid #334155; border-radius: 12px; padding: 2rem; max-width: 520px; width: 90%; box-shadow: 0 10px 25px rgba(0,0,0,0.4); }}
    .badge {{ display: inline-block; background: #065f46; color: #6ee7b7; padding: 4px 10px; border-radius: 999px; font-size: 0.8rem; font-weight: 600; }}
    h1 {{ margin: 0.6rem 0 1.2rem; font-size: 1.5rem; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 0.92rem; }}
    td {{ padding: 8px 0; border-bottom: 1px solid #334155; }}
    td:first-child {{ color: #94a3b8; }}
    td:last-child {{ text-align: right; font-family: monospace; }}
    .links {{ margin-top: 1.4rem; display: flex; gap: 12px; }}
    a {{ color: #38bdf8; text-decoration: none; font-size: 0.9rem; }}
    a:hover {{ text-decoration: underline; }}
  </style>
</head>
<body>
  <div class="card">
    <span class="badge">● OPERATIONAL</span>
    <h1>Storefront API</h1>
    <table>
      <tr><td>Environment</td><td>{payload["environment"]}</td></tr>
      <tr><td>AWS Region</td><td>{payload["region"]}</td></tr>
      <tr><td>Pod Hostname</td><td>{payload["pod"]}</td></tr>
      <tr><td>Runtime UID</td><td>{payload["security"]["non_root_uid"]} (non-root)</td></tr>
      <tr><td>Warehouse SKU</td><td>{payload["sample_sku"]["id"]} ({payload["sample_sku"]["warehouse"]})</td></tr>
    </table>
    <div class="links">
      <a href="/health">/health</a>
      <a href="/metrics">/metrics</a>
      <a href="/docs">/docs</a>
    </div>
  </div>
</body>
</html>"""
        return HTMLResponse(content=html)

    return payload


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.get("/metrics")
def metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)