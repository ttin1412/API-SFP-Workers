"""Persistence boundary used by the scan handler."""

from typing import Protocol

from worker.jobs.models import ClaimResult, ScanJob


class JobRepository(Protocol):
    """Atomically owns file and job lifecycle changes."""

    async def claim_scan(self, job: ScanJob) -> ClaimResult:
        """Move an uploaded file to scanning and claim its job."""

    async def complete_scan(self, job: ScanJob) -> None:
        """Mark the Phase 6 mock scan invocation complete."""

    async def release_scan(self, job: ScanJob, error: str) -> None:
        """Make a failed invocation available for a queue retry."""
