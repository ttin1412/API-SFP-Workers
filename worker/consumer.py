"""HTTP push consumer used by Cloud Tasks."""

from fastapi import APIRouter, HTTPException, Request, Response, status

from worker.common.exceptions import InvalidJobStateError, JobNotFoundError
from worker.database.firestore import FirestoreJobRepository
from worker.handlers.scan_handler import ScanHandler
from worker.jobs.models import ScanJob
from worker.scanner.service import ExtensionSecurityScanner

router = APIRouter(prefix="/tasks", tags=["queue"])


def build_scan_handler(project_id: str, database_id: str) -> ScanHandler:
    """Build production dependencies lazily on the first queue delivery."""
    return ScanHandler(
        FirestoreJobRepository(project_id, database_id),
        ExtensionSecurityScanner(),
    )


def get_scan_handler(request: Request) -> ScanHandler:
    """Return a cached handler while allowing tests to inject a fake."""
    handler = getattr(request.app.state, "scan_handler", None)
    if handler is None:
        settings = request.app.state.settings
        handler = build_scan_handler(
            settings.gcp_project_id,
            settings.firestore_database_id,
        )
        request.app.state.scan_handler = handler
    return handler


@router.post("/security-scan", status_code=status.HTTP_204_NO_CONTENT)
async def consume_security_scan(job: ScanJob, request: Request) -> Response:
    """Validate and acknowledge one Cloud Tasks security-scan delivery."""
    try:
        await get_scan_handler(request).handle(job)
    except JobNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except InvalidJobStateError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)
