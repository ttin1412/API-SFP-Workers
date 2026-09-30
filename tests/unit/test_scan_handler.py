"""Unit tests for idempotent scan job handling."""

from __future__ import annotations

from dataclasses import dataclass, field

import pytest

from worker.handlers.scan_handler import ScanHandler
from worker.jobs.models import ClaimResult, HandleResult, ScanJob


@dataclass
class FakeRepository:
    claim: ClaimResult = ClaimResult.CLAIMED
    completed: list[str] = field(default_factory=list)
    released: list[tuple[str, str]] = field(default_factory=list)

    async def claim_scan(self, job: ScanJob) -> ClaimResult:
        return self.claim

    async def complete_scan(self, job: ScanJob) -> None:
        self.completed.append(job.job_id)

    async def release_scan(self, job: ScanJob, error: str) -> None:
        self.released.append((job.job_id, error))


@dataclass
class FakeScanner:
    error: Exception | None = None
    scanned: list[str] = field(default_factory=list)

    async def scan(self, job: ScanJob) -> None:
        self.scanned.append(job.file_id)
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
    assert scanner.scanned == ["file_123"]
    assert repository.completed == ["job_123"]
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
async def test_handler_releases_failed_job_for_retry() -> None:
    repository = FakeRepository()
    scanner = FakeScanner(error=RuntimeError("scanner unavailable"))

    with pytest.raises(RuntimeError, match="scanner unavailable"):
        await ScanHandler(repository, scanner).handle(scan_job())

    assert repository.completed == []
    assert repository.released == [("job_123", "scanner unavailable")]
