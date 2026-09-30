"""Scanner boundary and the temporary Phase 6 implementation."""

from typing import Protocol

from worker.jobs.models import ScanJob


class SecurityScanner(Protocol):
    """High-level scanner interface implemented fully in Phase 7."""

    async def scan(self, job: ScanJob) -> None:
        """Scan the file represented by a queue job."""


class MockSecurityScanner:
    """Temporary scanner that performs no file-content inspection."""

    async def scan(self, job: ScanJob) -> None:
        """Accept a valid invocation while the real scanner is deferred."""
