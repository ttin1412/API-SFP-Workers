"""Lifecycle values shared by queue, handler, and persistence components."""

from enum import StrEnum


class FileStatus(StrEnum):
    """File states relevant to the worker's scanning lifecycle."""

    UPLOADED = "UPLOADED"
    SCANNING = "SCANNING"
    REJECTED = "REJECTED"


class JobType(StrEnum):
    """Queue job types accepted by this worker."""

    SECURITY_SCAN = "SECURITY_SCAN"


class JobStatus(StrEnum):
    """Worker-owned job execution states."""

    QUEUED = "QUEUED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
