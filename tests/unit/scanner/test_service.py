"""Tests for the incrementally implemented scanner pipeline."""

import pytest

from worker.jobs.models import ScanJob
from worker.scanner.extension_checker import UnsupportedExtensionError
from worker.scanner.service import ExtensionSecurityScanner


def scan_job() -> ScanJob:
    return ScanJob(job_id="job_123", file_id="file_123", type="SECURITY_SCAN")


@pytest.mark.asyncio
async def test_extension_scanner_accepts_supported_persisted_filename() -> None:
    await ExtensionSecurityScanner().scan(scan_job(), "photo.JPG")


@pytest.mark.asyncio
async def test_extension_scanner_rejects_unsupported_persisted_filename() -> None:
    with pytest.raises(UnsupportedExtensionError) as error:
        await ExtensionSecurityScanner().scan(scan_job(), "payload.exe")

    assert error.value.reason == "UNSUPPORTED_EXTENSION"
