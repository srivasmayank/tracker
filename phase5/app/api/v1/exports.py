from fastapi import APIRouter, Depends, BackgroundTasks, status
from fastapi.responses import FileResponse

from app.core.dependencies import get_current_user, get_export_service
from app.models.user import User
from app.schemas.export_job import (
    ExportJobCreate,
    ExportJobResponse,
    ExportStatusResponse,
)
from app.services.export_service import ExportService

router = APIRouter(prefix="/exports", tags=["Statement Exports & Background Jobs"])


@router.post("", response_model=ExportJobResponse, status_code=status.HTTP_202_ACCEPTED)
def request_export_job(
    data: ExportJobCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    service: ExportService = Depends(get_export_service),
):
    """
    Request asynchronous statement generation.
    Returns 202 Accepted with a job_id immediately, preventing client HTTP timeouts.
    Serialization and file generation run in background tasks.
    """
    job = service.request_export_job(
        user_id=current_user.id,
        schema=data,
        background_tasks=background_tasks,
    )
    poll_url = f"/api/v1/exports/{job.job_id}"
    download_url = f"/api/v1/exports/{job.job_id}/download"
    return ExportJobResponse(
        job_id=job.job_id,
        status=job.status,
        format=job.format,
        message="Export job queued successfully. Poll status or download when completed.",
        poll_url=poll_url,
        download_url=download_url,
    )


@router.get("/{job_id}", response_model=ExportStatusResponse)
def check_export_job_status(
    job_id: str,
    current_user: User = Depends(get_current_user),
    service: ExportService = Depends(get_export_service),
):
    """
    Check the current processing status of an export job.
    Status transitions: PENDING -> PROCESSING -> COMPLETED (or FAILED).
    """
    job = service.get_job_status(user_id=current_user.id, job_id=job_id)
    download_url = f"/api/v1/exports/{job.job_id}/download" if job.status == "COMPLETED" else None

    return ExportStatusResponse(
        job_id=job.job_id,
        user_id=job.user_id,
        format=job.format,
        status=job.status,
        total_records=job.total_records,
        error_message=job.error_message,
        created_at=job.created_at,
        completed_at=job.completed_at,
        download_url=download_url,
    )


@router.get("/{job_id}/download")
def download_export_file(
    job_id: str,
    current_user: User = Depends(get_current_user),
    service: ExportService = Depends(get_export_service),
):
    """
    Download the generated statement file (CSV/JSON) once status is COMPLETED.
    Streams the file with appropriate MIME type and Content-Disposition header.
    """
    file_path, media_type, filename = service.get_export_file(
        user_id=current_user.id,
        job_id=job_id,
    )
    return FileResponse(
        path=file_path,
        media_type=media_type,
        filename=filename,
    )
