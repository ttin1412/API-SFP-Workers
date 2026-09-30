"""Lifecycle values shared by queue, handler, and persistence components."""

from enum import StrEnum


class FileStatus(StrEnum):
    """File states relevant to the Phase 6 worker."""

    UPLOADED = "UPLOADED"
    SCANNING = "SCANNING"


class JobType(StrEnum):
    """Queue job types accepted by this worker."""

    SECURITY_SCAN = "SECURITY_SCAN"


class JobStatus(StrEnum):
    """Worker-owned job execution states."""

    QUEUED = "QUEUED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
