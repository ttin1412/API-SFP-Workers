"""Logging setup for the worker process."""

import logging


def configure_logging(level: str) -> None:
    """Configure application logging once at process startup."""
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


def get_logger(name: str) -> logging.Logger:
    """Create a named application logger."""
    return logging.getLogger(name)
