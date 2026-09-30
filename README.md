# API-SFP-Workers

Worker repository for the Secure File Processing platform. The Phase 6 worker accepts Cloud
Tasks scan jobs, atomically moves file metadata from `UPLOADED` to `SCANNING`, and invokes an
initial mock scanner. The runtime also provides validated configuration, a health endpoint,
tests, linting, and a non-root container image.

## Requirements

- Python 3.11 or newer
- Docker (optional, for container execution)

## Local setup

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
cp environments/.env.example .env
```

Start the worker process:

```bash
python -m worker
```

Then request `http://localhost:8081/health`. The response identifies the service, version, and
environment. API documentation is available at `http://localhost:8081/docs` in this initial
HTTP-based deployment shell.

## Quality checks

```bash
pytest
ruff check .
ruff format --check .
```

The equivalent shortcuts are `make test` and `make lint`.

## Docker

Build and run the image:

```bash
docker build -f docker/Dockerfile -t api-sfp-workers:local .
docker run --rm --env-file environments/.env.example -p 8081:8081 api-sfp-workers:local
```

The image runs as the unprivileged `worker` user (UID/GID 10001) and includes a `/health`
container probe.

## Configuration

All configuration is read from environment variables. Copy `environments/.env.example` to
`.env` for local development. Cloud credentials use Application Default Credentials. Never
commit `.env` or service-account credentials.

`FIRESTORE_DATABASE_ID` selects the Firestore database. It defaults to `(default)`; the example
environment targets this project's existing `dev-db` database.

## Queue delivery

Configure the scan queue to send an authenticated `POST /tasks/security-scan` request containing:

```json
{"job_id": "job_123", "file_id": "file_123", "type": "SECURITY_SCAN"}
```

The Cloud Run service should require IAM authentication; grant only the Cloud Tasks service
account permission to invoke it. Firestore claims are transactional, so duplicate deliveries do
not invoke the scanner twice. Phase 6 deliberately leaves the file in `SCANNING`; Phase 7 replaces
the mock with the content-scanning pipeline and records `SAFE` or `REJECTED`.
