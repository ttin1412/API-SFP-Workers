"""Application service for security-scan queue jobs."""

from worker.common.logging import get_logger
from worker.jobs.models import ClaimResult, HandleResult, ScanJob
from worker.jobs.repository import JobRepository
from worker.scanner.extension_checker import UnsupportedExtensionError
from worker.scanner.service import SecurityScanner

logger = get_logger(__name__)


class ScanHandler:
    """Claim a job, invoke the scanner, and persist execution state."""

    def __init__(self, repository: JobRepository, scanner: SecurityScanner) -> None:
        self._repository = repository
        self._scanner = scanner

    async def handle(self, job: ScanJob) -> HandleResult:
        """Process one delivery idempotently."""
        claim = await self._repository.claim_scan(job)
        if claim is ClaimResult.ALREADY_PROCESSED:
            logger.info(
                "scan_job_duplicate",
                extra={"job_id": job.job_id, "file_id": job.file_id},
            )
            return HandleResult.DUPLICATE

        try:
            original_filename = await self._repository.get_original_filename(job.file_id)
            await self._scanner.scan(job, original_filename)
        except UnsupportedExtensionError as exc:
            await self._repository.reject_scan(job, exc.reason)
            logger.info(
                "scan_job_rejected",
                extra={
                    "job_id": job.job_id,
                    "file_id": job.file_id,
                    "reason": exc.reason,
                    "layer": exc.layer,
                },
            )
            return HandleResult.REJECTED
        except Exception as exc:
            await self._repository.release_scan(job, str(exc))
            raise

        await self._repository.complete_scan(job)
        logger.info(
            "scan_job_processed",
            extra={"job_id": job.job_id, "file_id": job.file_id},
        )
        return HandleResult.PROCESSED
