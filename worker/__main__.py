"""Run the worker HTTP process."""

import uvicorn

from worker.config.settings import get_settings


def main() -> None:
    """Start the Cloud Run-compatible worker process."""
    settings = get_settings()
    uvicorn.run(
        "worker.main:app",
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()
