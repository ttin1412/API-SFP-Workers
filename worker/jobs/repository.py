"""Persistence boundary used by the scan handler."""

from typing import Protocol

from worker.jobs.models import ClaimResult, ScanJob


class JobRepository(Protocol):
    """Atomically owns file and job lifecycle changes."""

    async def claim_scan(self, job: ScanJob) -> ClaimResult:
        """Move an uploaded file to scanning and claim its job."""

    async def get_original_filename(self, file_id: str) -> str:
        """Load the untrusted original filename for a claimed file."""

    async def complete_scan(self, job: ScanJob) -> None:
        """Mark the Phase 6 mock scan invocation complete."""

    async def reject_scan(self, job: ScanJob, reason: str) -> None:
        """Permanently reject a file and complete its scan job."""

    async def release_scan(self, job: ScanJob, error: str) -> None:
        """Make a failed invocation available for a queue retry."""
