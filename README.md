# API-SFP-Workers

Worker repository for the Secure File Processing platform. This Phase 0 setup provides a
Cloud Run-compatible process, validated environment configuration, a health endpoint, tests,
linting, and a non-root container image. Queue consumption and file scanning are intentionally
deferred to the phases defined in [`SPEC.md`](SPEC.md).

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

Then request `http://localhost:8080/health`. The response identifies the service, version, and
environment. API documentation is available at `http://localhost:8080/docs` in this initial
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
docker run --rm --env-file environments/.env.example -p 8080:8080 api-sfp-workers:local
```

The image runs as the unprivileged `worker` user (UID/GID 10001) and includes a `/health`
container probe.

## Configuration

All configuration is read from environment variables. Copy `environments/.env.example` to
`.env` for local development. Cloud and scanner variables are present for compatibility with
later phases but are not used during Phase 0. Never commit `.env` or service-account credentials.

## Scope

Phase 0 does not consume jobs, download files, connect to Firestore or Cloud Storage, or perform
security scanning. The package boundaries for those components exist so later phases can be
implemented without restructuring this repository.
