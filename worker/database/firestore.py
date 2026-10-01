"""Firestore implementation of atomic job claiming and lifecycle updates."""

from typing import Any

from worker.common.enums import FileStatus, JobStatus, JobType
from worker.common.exceptions import InvalidJobStateError, JobNotFoundError
from worker.jobs.models import ClaimResult, ScanJob


class FirestoreJobRepository:
    """Store worker state in the API's Firestore job and file documents."""

    def __init__(self, project_id: str, database_id: str = "(default)") -> None:
        # Keep Google imports local so unit tests and the health endpoint do not
        # require Application Default Credentials.
        from google.cloud import firestore

        self._firestore = firestore
        self._client = firestore.AsyncClient(
            project=project_id or None,
            database=database_id or "(default)",
        )

    async def claim_scan(self, job: ScanJob) -> ClaimResult:
        """Atomically perform UPLOADED -> SCANNING and claim the job."""
        file_ref = self._client.collection("files").document(job.file_id)
        job_ref = self._client.collection("jobs").document(job.job_id)
        transaction = self._client.transaction()
        firestore = self._firestore

        @firestore.async_transactional
        async def claim(transaction: Any) -> ClaimResult:
            file_snapshot = await file_ref.get(transaction=transaction)
            job_snapshot = await job_ref.get(transaction=transaction)
            if not file_snapshot.exists:
                raise JobNotFoundError(f"file {job.file_id!r} does not exist")
            if not job_snapshot.exists:
                raise JobNotFoundError(f"job {job.job_id!r} does not exist")

            file_data = file_snapshot.to_dict() or {}
            job_data = job_snapshot.to_dict() or {}
            self._validate_identity(job, job_data)

            job_status = job_data.get("status")
            if job_status in {JobStatus.PROCESSING, JobStatus.COMPLETED}:
                return ClaimResult.ALREADY_PROCESSED

            file_status = file_data.get("status")
            if file_status not in {FileStatus.UPLOADED, FileStatus.SCANNING}:
                raise InvalidJobStateError(
                    f"file {job.file_id!r} cannot be scanned from state {file_status!r}"
                )

            timestamp = firestore.SERVER_TIMESTAMP
            if file_status == FileStatus.UPLOADED:
                transaction.update(
                    file_ref,
                    {"status": FileStatus.SCANNING.value, "updated_at": timestamp},
                )
            transaction.update(
                job_ref,
                {
                    "status": JobStatus.PROCESSING.value,
                    "error": None,
                    "updated_at": timestamp,
                },
            )
            return ClaimResult.CLAIMED

        return await claim(transaction)

    async def complete_scan(self, job: ScanJob) -> None:
        """Mark the implemented scanner layers complete without declaring SAFE."""
        await (
            self._client.collection("jobs")
            .document(job.job_id)
            .update(
                {
                    "status": JobStatus.COMPLETED.value,
                    "updated_at": self._firestore.SERVER_TIMESTAMP,
                }
            )
        )

    async def get_original_filename(self, file_id: str) -> str:
        """Load the original filename from the API-owned file document."""
        snapshot = await self._client.collection("files").document(file_id).get()
        if not snapshot.exists:
            raise JobNotFoundError(f"file {file_id!r} does not exist")

        original_filename = (snapshot.to_dict() or {}).get("original_filename")
        if not isinstance(original_filename, str) or not original_filename.strip():
            raise InvalidJobStateError(f"file {file_id!r} has no original filename")
        return original_filename

    async def reject_scan(self, job: ScanJob, reason: str) -> None:
        """Atomically reject a file and complete its scan job."""
        file_ref = self._client.collection("files").document(job.file_id)
        job_ref = self._client.collection("jobs").document(job.job_id)
        batch = self._client.batch()
        timestamp = self._firestore.SERVER_TIMESTAMP
        batch.update(
            file_ref,
            {
                "status": FileStatus.REJECTED.value,
                "rejection_reason": reason,
                "updated_at": timestamp,
            },
        )
        batch.update(
            job_ref,
            {
                "status": JobStatus.COMPLETED.value,
                "error": None,
                "updated_at": timestamp,
            },
        )
        await batch.commit()

    async def release_scan(self, job: ScanJob, error: str) -> None:
        """Record a scanner error and release the job for Cloud Tasks retry."""
        job_ref = self._client.collection("jobs").document(job.job_id)
        await job_ref.update(
            {
                "status": JobStatus.QUEUED.value,
                "error": error[:1_024],
                "retry_count": self._firestore.Increment(1),
                "updated_at": self._firestore.SERVER_TIMESTAMP,
            }
        )

    async def close(self) -> None:
        """Release Firestore transport resources."""
        await self._client.close()

    @staticmethod
    def _validate_identity(job: ScanJob, job_data: dict[str, Any]) -> None:
        if job_data.get("file_id") != job.file_id:
            raise InvalidJobStateError("queue payload does not match the persisted job file")
        if job_data.get("type") != JobType.SECURITY_SCAN:
            raise InvalidJobStateError("persisted job is not a SECURITY_SCAN job")
