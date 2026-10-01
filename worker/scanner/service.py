"""Scanner boundary and the incrementally implemented Phase 7 pipeline."""

from typing import Protocol

from worker.jobs.models import ScanJob
from worker.scanner.extension_checker import ExtensionChecker


class SecurityScanner(Protocol):
    """High-level scanner interface implemented fully in Phase 7."""

    async def scan(self, job: ScanJob, original_filename: str) -> None:
        """Scan the file represented by a queue job."""


class ExtensionSecurityScanner:
    """Phase 7 scanner containing the extension-validation layer."""

    def __init__(self, extension_checker: ExtensionChecker | None = None) -> None:
        self._extension_checker = extension_checker or ExtensionChecker()

    async def scan(self, job: ScanJob, original_filename: str) -> None:
        """Validate the persisted filename before later layers are added."""
        self._extension_checker.validate(original_filename)
