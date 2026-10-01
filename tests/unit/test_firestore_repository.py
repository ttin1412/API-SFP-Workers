"""Unit tests for Firestore lifecycle transition logic."""

from __future__ import annotations

from dataclasses import dataclass, field
from types import SimpleNamespace
from typing import Any

import pytest

from worker.common.exceptions import InvalidJobStateError
from worker.database.firestore import FirestoreJobRepository
from worker.jobs.models import ClaimResult, ScanJob


@dataclass
class FakeSnapshot:
    data: dict[str, Any]
    exists: bool = True

    def to_dict(self) -> dict[str, Any]:
        return self.data


@dataclass
class FakeDocument:
    snapshot: FakeSnapshot

    async def get(self, transaction: FakeTransaction | None = None) -> FakeSnapshot:
        return self.snapshot


@dataclass
class FakeTransaction:
    updates: list[tuple[FakeDocument, dict[str, Any]]] = field(default_factory=list)

    def update(self, document: FakeDocument, values: dict[str, Any]) -> None:
        self.updates.append((document, values))


@dataclass
class FakeBatch:
    updates: list[tuple[FakeDocument, dict[str, Any]]] = field(default_factory=list)
    committed: bool = False

    def update(self, document: FakeDocument, values: dict[str, Any]) -> None:
        self.updates.append((document, values))

    async def commit(self) -> None:
        self.committed = True


class FakeClient:
    def __init__(self, file_document: FakeDocument, job_document: FakeDocument) -> None:
        self.documents = {"files": file_document, "jobs": job_document}
        self.current_collection = ""
        self.transaction_instance = FakeTransaction()
        self.batch_instance = FakeBatch()

    def collection(self, name: str) -> FakeClient:
        self.current_collection = name
        return self

    def document(self, document_id: str) -> FakeDocument:
        return self.documents[self.current_collection]

    def transaction(self) -> FakeTransaction:
        return self.transaction_instance

    def batch(self) -> FakeBatch:
        return self.batch_instance


def make_repository(
    *, file_status: str = "UPLOADED", job_status: str = "QUEUED"
) -> tuple[FirestoreJobRepository, FakeClient, FakeDocument, FakeDocument]:
    file_document = FakeDocument(
        FakeSnapshot({"status": file_status, "original_filename": "photo.jpg"})
    )
    job_document = FakeDocument(
        FakeSnapshot(
            {
                "file_id": "file_123",
                "type": "SECURITY_SCAN",
                "status": job_status,
            }
        )
    )
    client = FakeClient(file_document, job_document)
    repository = FirestoreJobRepository.__new__(FirestoreJobRepository)
    repository._client = client
    repository._firestore = SimpleNamespace(
        SERVER_TIMESTAMP="server timestamp",
        async_transactional=lambda function: function,
    )
    return repository, client, file_document, job_document


def scan_job() -> ScanJob:
    return ScanJob(job_id="job_123", file_id="file_123", type="SECURITY_SCAN")


@pytest.mark.asyncio
async def test_claim_scan_atomically_starts_file_and_job() -> None:
    repository, client, file_document, job_document = make_repository()

    result = await repository.claim_scan(scan_job())

    assert result is ClaimResult.CLAIMED
    assert client.transaction_instance.updates == [
        (
            file_document,
            {"status": "SCANNING", "updated_at": "server timestamp"},
        ),
        (
            job_document,
            {
                "status": "PROCESSING",
                "error": None,
                "updated_at": "server timestamp",
            },
        ),
    ]


@pytest.mark.asyncio
async def test_claim_scan_suppresses_completed_delivery() -> None:
    repository, client, _, _ = make_repository(file_status="SCANNING", job_status="COMPLETED")

    result = await repository.claim_scan(scan_job())

    assert result is ClaimResult.ALREADY_PROCESSED
    assert client.transaction_instance.updates == []


@pytest.mark.asyncio
async def test_claim_scan_rejects_invalid_file_transition() -> None:
    repository, _, _, _ = make_repository(file_status="PENDING_UPLOAD")

    with pytest.raises(InvalidJobStateError, match="cannot be scanned"):
        await repository.claim_scan(scan_job())


@pytest.mark.asyncio
async def test_loads_original_filename_from_file_document() -> None:
    repository, _, _, _ = make_repository()

    result = await repository.get_original_filename("file_123")

    assert result == "photo.jpg"


@pytest.mark.asyncio
async def test_reject_scan_updates_file_and_job_atomically() -> None:
    repository, client, file_document, job_document = make_repository()

    await repository.reject_scan(scan_job(), "UNSUPPORTED_EXTENSION")

    assert client.batch_instance.updates == [
        (
            file_document,
            {
                "status": "REJECTED",
                "rejection_reason": "UNSUPPORTED_EXTENSION",
                "updated_at": "server timestamp",
            },
        ),
        (
            job_document,
            {
                "status": "COMPLETED",
                "error": None,
                "updated_at": "server timestamp",
            },
        ),
    ]
    assert client.batch_instance.committed
