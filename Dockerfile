# ---- Build Stage ----
FROM python:3.11-slim-bookworm AS builder

WORKDIR /build
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ---- Runtime Stage ----
FROM gcr.io/distroless/python3-debian12:nonroot

WORKDIR /app
COPY --from=builder /opt/venv /opt/venv
COPY main.py .

ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1

# non-root user, a hardening meassure 
USER 65532:65532
EXPOSE 8080

# A usual HEALTHCHECK CMD curl localhost:8080/health will fail since the image is distroless
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
 CMD ["/usr/bin/python3", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')"]

 # again, no shell inside the image, so exec form it is instead of shell form
ENTRYPOINT ["python3", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]