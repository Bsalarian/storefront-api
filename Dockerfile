# ---- Build Stage ----
FROM python:3.12-alpine AS builder

WORKDIR /build

RUN apk upgrade --no-cache && \
    python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt && \
    pip uninstall -y pip setuptools wheel

# ---- Runtime Stage ----
FROM gcr.io/distroless/python3-debian12:nonroot

WORKDIR /app

# Apply security patches and create non-root user matching K8s UID 65532
RUN apk upgrade --no-cache && \
    adduser -D -u 65532 appuser

COPY --from=builder /opt/venv /opt/venv
COPY main.py .

ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# non-root user, a hardening meassure 
USER 65532:65532
EXPOSE 8080

# A usual HEALTHCHECK CMD curl localhost:8080/health will fail since the image is distroless
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
 CMD ["/usr/bin/python3", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')"]

 # again, no shell inside the image, so exec form it is instead of shell form
ENTRYPOINT ["python3", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]