# Storefront API

Lightweight FastAPI microservice built for containerized deployment on AWS (Amazon Web Services) EKS (Elastic Kubernetes Service) via GitOps.

* **Infrastructure & GitOps Repo:** [`Bsalarian/storefront-gitops`](https://github.com/Bsalarian/storefront-gitops)

## Endpoints

| Endpoint | Description |
| :--- | :--- |
| `GET /` | Returns service metadata as JSON (or renders the status dashboard UI when `Accept: text/html` is sent) |
| `GET /health` | Liveness/readiness probe returning `{"status": "healthy"}` |
| `GET /metrics` | Prometheus metrics (`http_requests_total`, `http_request_duration_seconds`, and Python runtime stats) |

## Run Locally (Hardened Read-Only Container)

```bash
docker build -t storefront-api:local .
docker run --rm --read-only -p 8080:8080 -e APP_ENV=local storefront-api:local
```

Open `http://localhost:8080` in your browser or test with `curl http://localhost:8080/health`.

## CI/CD Pipeline (`.github/workflows/ci.yaml`)

Every push to `main` automatically:
1. Builds a multi-stage `python:3.12-alpine` image running as non-root `UID 65532`.
2. Runs a `--read-only` container smoke test against `/health` and `/`.
3. Scans the image with **Trivy** (failing on fixable `HIGH`/`CRITICAL` CVEs and uploading SARIF results).
4. Pushes the immutable `:<git-sha>` image tag to Amazon ECR and updates `deploy/overlays/test/kustomization.yaml` in `storefront-gitops` for ArgoCD to sync.