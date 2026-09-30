"""Worker-specific failures that the HTTP consumer can classify."""


class JobError(Exception):
    """Base class for job-processing errors."""


class JobNotFoundError(JobError):
    """The queued job or its file metadata does not exist."""


class InvalidJobStateError(JobError):
    """The job cannot perform the requested lifecycle transition."""
