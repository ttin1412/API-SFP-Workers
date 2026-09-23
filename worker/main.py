"""HTTP entry point for the worker service."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from worker import __version__
from worker.common.logging import configure_logging, get_logger
from worker.config.settings import get_settings

settings = get_settings()
configure_logging(settings.log_level)
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Report service lifecycle events; consumers are added in a later phase."""
    logger.info("worker_started", extra={"app_env": settings.app_env})
    yield
    logger.info("worker_stopped")


app = FastAPI(
    title="Secure File Processing Worker",
    description="Worker runtime and health endpoint. Queue consumption starts in Phase 6.",
    version=__version__,
    lifespan=lifespan,
)


@app.get("/health", tags=["health"])
async def health() -> dict[str, str]:
    """Return liveness information for Cloud Run and container probes."""
    return {
        "status": "ok",
        "service": "api-sfp-workers",
        "environment": settings.app_env,
        "version": __version__,
    }
