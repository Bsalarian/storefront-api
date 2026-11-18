# ---- Stage 1: Builder ----
FROM python:3.12-alpine AS builder

WORKDIR /build

RUN apk upgrade --no-cache && \
    python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt && \
    pip uninstall -y pip setuptools wheel

# ---- Stage 2: Hardened Runtime ----
FROM python:3.12-alpine

WORKDIR /app

RUN apk upgrade --no-cache && \
    adduser -D -u 65532 appuser

COPY --from=builder /opt/venv /opt/venv
COPY main.py .

ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

USER 65532
EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')" || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]