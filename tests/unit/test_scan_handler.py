"""Unit tests for idempotent scan job handling."""

from __future__ import annotations

from dataclasses import dataclass, field

import pytest

from worker.handlers.scan_handler import ScanHandler
from worker.jobs.models import ClaimResult, HandleResult, ScanJob
from worker.scanner.extension_checker import UnsupportedExtensionError


@dataclass
class FakeRepository:
    claim: ClaimResult = ClaimResult.CLAIMED
    original_filename: str = "photo.jpg"
    completed: list[str] = field(default_factory=list)
    rejected: list[tuple[str, str]] = field(default_factory=list)
    released: list[tuple[str, str]] = field(default_factory=list)

    async def claim_scan(self, job: ScanJob) -> ClaimResult:
        return self.claim

    async def get_original_filename(self, file_id: str) -> str:
        return self.original_filename

    async def complete_scan(self, job: ScanJob) -> None:
        self.completed.append(job.job_id)

    async def reject_scan(self, job: ScanJob, reason: str) -> None:
        self.rejected.append((job.job_id, reason))

    async def release_scan(self, job: ScanJob, error: str) -> None:
        self.released.append((job.job_id, error))


@dataclass
class FakeScanner:
    error: Exception | None = None
    scanned: list[tuple[str, str]] = field(default_factory=list)

    async def scan(self, job: ScanJob, original_filename: str) -> None:
        self.scanned.append((job.file_id, original_filename))
        if self.error is not None:
            raise self.error


def scan_job() -> ScanJob:
    return ScanJob(job_id="job_123", file_id="file_123", type="SECURITY_SCAN")


@pytest.mark.asyncio
async def test_handler_claims_scans_and_completes_job() -> None:
    repository = FakeRepository()
    scanner = FakeScanner()

    result = await ScanHandler(repository, scanner).handle(scan_job())

    assert result is HandleResult.PROCESSED
    assert scanner.scanned == [("file_123", "photo.jpg")]
    assert repository.completed == ["job_123"]
    assert repository.rejected == []
    assert repository.released == []


@pytest.mark.asyncio
async def test_handler_acknowledges_duplicate_without_scanning() -> None:
    repository = FakeRepository(claim=ClaimResult.ALREADY_PROCESSED)
    scanner = FakeScanner()

    result = await ScanHandler(repository, scanner).handle(scan_job())

    assert result is HandleResult.DUPLICATE
    assert scanner.scanned == []
    assert repository.completed == []


@pytest.mark.asyncio
async def test_handler_permanently_rejects_an_unsupported_extension() -> None:
    repository = FakeRepository(original_filename="payload.exe")
    scanner = FakeScanner(error=UnsupportedExtensionError("payload.exe", ".exe"))

    result = await ScanHandler(repository, scanner).handle(scan_job())

    assert result is HandleResult.REJECTED
    assert scanner.scanned == [("file_123", "payload.exe")]
    assert repository.rejected == [("job_123", "UNSUPPORTED_EXTENSION")]
    assert repository.completed == []
    assert repository.released == []


@pytest.mark.asyncio
async def test_handler_releases_failed_job_for_retry() -> None:
    repository = FakeRepository()
    scanner = FakeScanner(error=RuntimeError("scanner unavailable"))

    with pytest.raises(RuntimeError, match="scanner unavailable"):
        await ScanHandler(repository, scanner).handle(scan_job())

    assert repository.completed == []
    assert repository.released == [("job_123", "scanner unavailable")]
