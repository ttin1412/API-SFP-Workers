"""Tests for the Cloud Tasks HTTP consumer."""

from __future__ import annotations

from dataclasses import dataclass, field

import pytest
from fastapi.testclient import TestClient

from worker.common.exceptions import InvalidJobStateError, JobNotFoundError
from worker.jobs.models import HandleResult, ScanJob
from worker.main import app


@dataclass
class FakeHandler:
    error: Exception | None = None
    handled: list[ScanJob] = field(default_factory=list)

    async def handle(self, job: ScanJob) -> HandleResult:
        self.handled.append(job)
        if self.error is not None:
            raise self.error
        return HandleResult.PROCESSED


@pytest.fixture
def inject_handler() -> list[FakeHandler]:
    handlers: list[FakeHandler] = []
    yield handlers
    if hasattr(app.state, "scan_handler"):
        del app.state.scan_handler


def test_consumer_dispatches_valid_security_scan(inject_handler: list[FakeHandler]) -> None:
    handler = FakeHandler()
    inject_handler.append(handler)
    app.state.scan_handler = handler

    with TestClient(app) as client:
        response = client.post(
            "/tasks/security-scan",
            json={"job_id": "job_123", "file_id": "file_123", "type": "SECURITY_SCAN"},
        )

    assert response.status_code == 204
    assert response.content == b""
    assert handler.handled == [ScanJob(job_id="job_123", file_id="file_123", type="SECURITY_SCAN")]


@pytest.mark.parametrize(
    ("error", "expected_status"),
    [
        (JobNotFoundError("missing"), 404),
        (InvalidJobStateError("invalid transition"), 409),
    ],
)
def test_consumer_maps_permanent_job_errors(
    inject_handler: list[FakeHandler], error: Exception, expected_status: int
) -> None:
    handler = FakeHandler(error=error)
    inject_handler.append(handler)
    app.state.scan_handler = handler

    with TestClient(app) as client:
        response = client.post(
            "/tasks/security-scan",
            json={"job_id": "job_123", "file_id": "file_123", "type": "SECURITY_SCAN"},
        )

    assert response.status_code == expected_status


def test_consumer_rejects_unknown_job_type(inject_handler: list[FakeHandler]) -> None:
    handler = FakeHandler()
    inject_handler.append(handler)
    app.state.scan_handler = handler

    with TestClient(app) as client:
        response = client.post(
            "/tasks/security-scan",
            json={"job_id": "job_123", "file_id": "file_123", "type": "THUMBNAIL"},
        )

    assert response.status_code == 422
    assert handler.handled == []
