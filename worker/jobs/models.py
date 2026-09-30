"""Validated queue messages and handler outcomes."""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from worker.common.enums import JobType


class ScanJob(BaseModel):
    """Payload published by the API for a file security scan."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    job_id: str = Field(min_length=1, max_length=128)
    file_id: str = Field(min_length=1, max_length=128)
    type: JobType


class ClaimResult(StrEnum):
    """Result of atomically claiming a queued scan job."""

    CLAIMED = "CLAIMED"
    ALREADY_PROCESSED = "ALREADY_PROCESSED"


class HandleResult(StrEnum):
    """Externally useful result of handling one delivery."""

    PROCESSED = "PROCESSED"
    DUPLICATE = "DUPLICATE"
