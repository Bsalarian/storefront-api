import os
import socket
import time
import logging
from datetime import datetime, timezone
from html import escape

from fastapi import FastAPI, Request, Response
from fastapi.responses import HTMLResponse
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format=(
        '{"time": "%(asctime)s", '
        '"level": "%(levelname)s", '
        '"service": "storefront-api", '
        '"message": "%(message)s"}'
    ),
)
logger = logging.getLogger("storefront-api")

app = FastAPI(
    title="Storefront API",
    version="1.0.0",
    description="Cloud-native storefront service running on AWS EKS.",
)

HTTP_REQUESTS = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)

HTTP_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint"],
)


@app.middleware("http")
async def observability_and_security_headers(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    duration = time.perf_counter() - start

    route = request.scope.get("route")
    endpoint = getattr(route, "path", "unmatched")

    HTTP_REQUESTS.labels(request.method, endpoint, str(response.status_code)).inc()
    HTTP_LATENCY.labels(request.method, endpoint).observe(duration)

    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

    if request.url.scheme == "https":
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )

    return response


DASHBOARD_CSS = """
:root {
    color-scheme: dark;
    --bg: #080f1d;
    --surface: #111d30;
    --surface-hover: #17263c;
    --border: #25364e;
    --text: #f1f5f9;
    --muted: #94a3b8;
    --blue: #60a5fa;
    --green: #34d399;
    --purple: #a78bfa;
    --teal: #2dd4bf;
}

* {
    box-sizing: border-box;
}

body {
    margin: 0;
    min-height: 100vh;
    padding: 40px 20px;
    background:
        radial-gradient(ellipse at 50% 0%, #172b4a 0%, transparent 55%),
        var(--bg);
    color: var(--text);
    font-family: Inter, ui-sans-serif, system-ui, -apple-system,
                 BlinkMacSystemFont, "Segoe UI", sans-serif;
    -webkit-font-smoothing: antialiased;
}

.container {
    max-width: 900px;
    margin: 0 auto;
}

header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 20px;
    margin-bottom: 44px;
}

.brand {
    display: flex;
    align-items: center;
    gap: 12px;
}

.brand-icon {
    display: grid;
    place-items: center;
    width: 42px;
    height: 42px;
    border-radius: 12px;
    background: linear-gradient(135deg, #2563eb, #7c3aed);
    font-size: 21px;
    font-weight: 800;
    color: white;
}

.brand-name {
    font-size: 15px;
    font-weight: 750;
    letter-spacing: 1.5px;
}

.brand-subtitle {
    margin-top: 3px;
    color: var(--muted);
    font-size: 10px;
    letter-spacing: 1.5px;
}

.header-label {
    color: var(--muted);
    font-size: 11px;
    letter-spacing: 1.4px;
    text-align: right;
}

.hero {
    margin-bottom: 28px;
}

.eyebrow {
    color: var(--blue);
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 2px;
    text-transform: uppercase;
}

h1 {
    margin: 12px 0 14px;
    font-size: clamp(30px, 5vw, 42px);
    letter-spacing: -1.5px;
    font-weight: 750;
}

.status {
    display: inline-flex;
    align-items: center;
    gap: 9px;
    padding: 8px 13px;
    border: 1px solid #166b50;
    border-radius: 30px;
    background: #0b3029;
    color: #6ee7b7;
    font-size: 12px;
    font-weight: 650;
}

.status-dot {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: var(--green);
    box-shadow: 0 0 10px #34d39980;
}

.section-label {
    margin: 32px 0 14px;
    color: var(--muted);
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 1.5px;
    text-transform: uppercase;
}

.grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 14px;
}

.card {
    padding: 21px;
    border: 1px solid var(--border);
    border-radius: 14px;
    background: linear-gradient(145deg, #142238, #101a2b);
    transition: border-color 160ms ease, transform 160ms ease;
}

.card:hover {
    border-color: #48658a;
    transform: translateY(-2px);
}

.card-label {
    color: var(--muted);
    font-size: 11px;
    font-weight: 650;
    letter-spacing: 1.2px;
    text-transform: uppercase;
}

.card-value {
    margin-top: 11px;
    font-size: 19px;
    font-weight: 700;
    overflow-wrap: anywhere;
}

.card-description {
    margin-top: 6px;
    color: var(--muted);
    font-size: 12px;
}

.blue { color: var(--blue); }
.green { color: var(--green); }
.purple { color: var(--purple); }
.teal { color: var(--teal); }

.details {
    overflow: hidden;
    border: 1px solid var(--border);
    border-radius: 14px;
    background: var(--surface);
}

.detail-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 15px;
    padding: 16px 20px;
    border-bottom: 1px solid var(--border);
}

.detail-row:last-child {
    border-bottom: none;
}

.detail-label {
    color: var(--muted);
    font-size: 13px;
}

.detail-value {
    max-width: 65%;
    overflow-wrap: anywhere;
    color: var(--text);
    font-family: ui-monospace, monospace;
    font-size: 12px;
    text-align: right;
}

.pill {
    padding: 5px 10px;
    border: 1px solid #166b50;
    border-radius: 20px;
    background: #0b3029;
    color: #6ee7b7;
    font-family: inherit;
    font-size: 11px;
    font-weight: 650;
}

.pill.warning {
    border-color: #854d0e;
    background: #422d10;
    color: #fcd34d;
}

.links {
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
    margin-top: 28px;
}

.link {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    padding: 12px 18px;
    border: 1px solid var(--border);
    border-radius: 10px;
    background: var(--surface);
    color: var(--text);
    font-size: 13px;
    font-weight: 650;
    text-decoration: none;
    transition: background 150ms ease, border-color 150ms ease;
}

.link:hover {
    border-color: var(--blue);
    background: var(--surface-hover);
}

.link.primary {
    border-color: #2563eb;
    background: #1d4ed8;
}

.link.primary:hover {
    background: #2563eb;
}

footer {
    display: flex;
    justify-content: space-between;
    gap: 15px;
    margin-top: 48px;
    padding-top: 20px;
    border-top: 1px solid var(--border);
    color: #64748b;
    font-size: 11px;
}

@media (max-width: 560px) {
    body { padding: 26px 16px; }
    header { margin-bottom: 34px; }
    .header-label { display: none; }
    .grid { grid-template-columns: 1fr; }
    .card { padding: 18px; }
    .detail-row { align-items: flex-start; flex-direction: column; gap: 7px; }
    .detail-value { max-width: 100%; text-align: left; }
    footer { flex-direction: column; }
}

@media (prefers-reduced-motion: reduce) {
    *, *::before, *::after {
        scroll-behavior: auto !important;
        transition: none !important;
        animation: none !important;
    }
}
"""


def render_dashboard(payload: dict) -> str:
    env = escape(str(payload["environment"]))
    region = escape(str(payload["region"]))
    pod = escape(str(payload["pod"]))
    uid = escape(str(payload["security"]["non_root_uid"]))
    sku = escape(str(payload["sample_sku"]["id"]))
    warehouse = escape(str(payload["sample_sku"]["warehouse"]))

    api_key_configured = payload["security"]["api_key_configured"]

    secret_label = (
        '<span class="pill">Configured</span>'
        if api_key_configured
        else '<span class="pill warning">Not configured</span>'
    )

    inventory_label = (
        '<span class="pill">In stock</span>'
        if payload["sample_sku"]["in_stock"]
        else '<span class="pill warning">Out of stock</span>'
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta name="theme-color" content="#080f1d">
    <meta name="description" content="Storefront API service status dashboard">
    <title>Storefront API | Platform Console</title>
    <style>{DASHBOARD_CSS}</style>
</head>
<body>
<div class="container">
    <header>
        <div class="brand">
            <div class="brand-icon">S</div>
            <div>
                <div class="brand-name">STOREFRONT</div>
                <div class="brand-subtitle">PLATFORM CONSOLE</div>
            </div>
        </div>
        <div class="header-label">
            CLOUD INFRASTRUCTURE<br>
            SERVICE MONITORING
        </div>
    </header>
    <main>
        <section class="hero">
            <div class="eyebrow">Application overview</div>
            <h1>Storefront API</h1>
            <div class="status">
                <span class="status-dot"></span>
                All systems operational
            </div>
        </section>
        <div class="section-label">Runtime environment</div>
        <section class="grid">
            <div class="card">
                <div class="card-label">AWS Region</div>
                <div class="card-value blue">{region}</div>
                <div class="card-description">Cloud deployment region</div>
            </div>
            <div class="card">
                <div class="card-label">Environment</div>
                <div class="card-value purple">{env}</div>
                <div class="card-description">Application deployment stage</div>
            </div>
            <div class="card">
                <div class="card-label">Runtime UID</div>
                <div class="card-value teal">{uid}</div>
                <div class="card-description">Container process identity</div>
            </div>
            <div class="card">
                <div class="card-label">Container Security</div>
                <div class="card-value green">Non-root</div>
                <div class="card-description">Unprivileged application process</div>
            </div>
        </section>
        <div class="section-label">Security configuration</div>
        <section class="details">
            <div class="detail-row">
                <span class="detail-label">API key configuration</span>
                {secret_label}
            </div>
            <div class="detail-row">
                <span class="detail-label">Runtime identity</span>
                <span class="detail-value">UID {uid}</span>
            </div>
            <div class="detail-row">
                <span class="detail-label">Pod hostname</span>
                <span class="detail-value">{pod}</span>
            </div>
        </section>
        <div class="section-label">Sample inventory</div>
        <section class="details">
            <div class="detail-row">
                <span class="detail-label">Product SKU</span>
                <span class="detail-value">{sku}</span>
            </div>
            <div class="detail-row">
                <span class="detail-label">Warehouse</span>
                <span class="detail-value">{warehouse}</span>
            </div>
            <div class="detail-row">
                <span class="detail-label">Availability</span>
                {inventory_label}
            </div>
        </section>
        <nav class="links" aria-label="API resources">
            <a class="link primary" href="/docs">API Documentation ↗</a>
            <a class="link" href="/health">Health Check ↗</a>
            <a class="link" href="/metrics">Prometheus Metrics ↗</a>
        </nav>
    </main>
    <footer>
        <span>STOREFRONT API · v1.0.0</span>
        <span>Last rendered: {escape(str(payload["timestamp"]))}</span>
    </footer>
</div>
</body>
</html>"""


@app.get("/", response_model=None)
def root(request: Request):
    api_key_configured = bool(os.getenv("API_KEY"))
    logger.info("Storefront status checked. API key configured: %s", api_key_configured)

    payload = {
        "service": "storefront-api",
        "status": "operational",
        "environment": os.getenv("APP_ENV", "local"),
        "region": os.getenv("AWS_REGION", "eu-north-1"),
        "pod": socket.gethostname(),
        "sample_sku": {
            "id": "DUSTIN-ENT-001",
            "in_stock": True,
            "warehouse": "NORDICS-HUB",
        },
        "security": {
            "api_key_configured": api_key_configured,
            "non_root_uid": os.getuid(),
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    if "text/html" in request.headers.get("accept", ""):
        return HTMLResponse(content=render_dashboard(payload))

    return payload


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.get("/metrics")
def metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)