import os
import uuid
import logging
from datetime import date
from typing import Optional, Tuple
from fastapi import HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session

from app.core import database
from app.models.expense import Expense
from app.models.export_job import ExportJob
from app.repositories.export_job_repository import ExportJobRepository
from app.schemas.export_job import ExportJobCreate
from app.services.export_formatters import ExportFormatterFactory

logger = logging.getLogger(__name__)

EXPORT_DIR = os.path.join(os.getcwd(), "storage", "exports")


def background_export_worker(
    job_id: str,
    user_id: int,
    format_type: str,
    start_date: Optional[date],
    end_date: Optional[date],
    category_id: Optional[int],
) -> None:
    """
    Independent worker executed in the background thread/task.
    Opens its own isolated database session to prevent transaction leakage
    or using closed connection handles from finished HTTP requests.
    """
    db: Session = database.SessionLocal()
    try:
        job_repo = ExportJobRepository(db)
        job = job_repo.get_by_job_id(job_id)
        if not job:
            logger.error("Background export worker could not find job %s", job_id)
            return

        job_repo.mark_processing(job)

        # Query user expenses with filters
        query = db.query(Expense).filter(Expense.user_id == user_id)
        if category_id:
            query = query.filter(Expense.category_id == category_id)
        if start_date:
            query = query.filter(Expense.expense_date >= start_date)
        if end_date:
            query = query.filter(Expense.expense_date <= end_date)

        expenses = query.order_by(Expense.expense_date.desc(), Expense.id.desc()).all()

        records = [
            {
                "id": exp.id,
                "date": str(exp.expense_date),
                "category": exp.category.name if exp.category else "Uncategorized",
                "amount": float(exp.amount),
                "description": exp.description,
                "payment_method": exp.payment_method,
                "created_at": exp.created_at.isoformat() if exp.created_at else "",
            }
            for exp in expenses
        ]

        formatter = ExportFormatterFactory.get_formatter(format_type)
        content_bytes = formatter.format(records)

        os.makedirs(EXPORT_DIR, exist_ok=True)
        filename = f"{job_id}{formatter.file_extension}"
        file_path = os.path.join(EXPORT_DIR, filename)

        with open(file_path, "wb") as f:
            f.write(content_bytes)

        job_repo.mark_completed(job, file_path=file_path, total_records=len(records))
        logger.info("Export job %s completed successfully (%d records)", job_id, len(records))

    except Exception as exc:
        logger.exception("Error executing export job %s: %s", job_id, exc)
        try:
            job_repo = ExportJobRepository(db)
            job = job_repo.get_by_job_id(job_id)
            if job:
                job_repo.mark_failed(job, error_message=str(exc))
        except Exception as inner_exc:
            logger.error("Failed recording job error state: %s", inner_exc)
    finally:
        db.close()


class ExportService:
    """
    Business service layer managing asynchronous export jobs.
    Uses FastAPI BackgroundTasks to offload heavy serialization and disk I/O,
    responding immediately with HTTP 202 Accepted.
    """

    def __init__(self, db: Session, job_repo: ExportJobRepository):
        self.db = db
        self.job_repo = job_repo

    def request_export_job(
        self,
        user_id: int,
        schema: ExportJobCreate,
        background_tasks: BackgroundTasks,
    ) -> ExportJob:
        job_id = f"exp_{uuid.uuid4().hex[:16]}"
        job = ExportJob(
            job_id=job_id,
            user_id=user_id,
            format=schema.format.value,
            status="PENDING",
            total_records=0,
        )
        saved_job = self.job_repo.create(job)

        # Enqueue background task
        background_tasks.add_task(
            background_export_worker,
            job_id=job_id,
            user_id=user_id,
            format_type=schema.format.value,
            start_date=schema.start_date,
            end_date=schema.end_date,
            category_id=schema.category_id,
        )

        return saved_job

    def get_job_status(self, user_id: int, job_id: str) -> ExportJob:
        job = self.job_repo.get_by_job_id_and_user(job_id=job_id, user_id=user_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Export job '{job_id}' not found.",
            )
        return job

    def get_export_file(self, user_id: int, job_id: str) -> Tuple[str, str, str]:
        job = self.get_job_status(user_id=user_id, job_id=job_id)

        if job.status == "PENDING" or job.status == "PROCESSING":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Export is still being generated. Please retry shortly.",
            )

        if job.status == "FAILED":
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Export generation failed: {job.error_message or 'Unknown error'}",
            )

        if not job.file_path or not os.path.exists(job.file_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Export file was deleted or cannot be located on disk.",
            )

        formatter = ExportFormatterFactory.get_formatter(job.format)
        filename = f"expenses_export_{job.job_id}{formatter.file_extension}"
        return job.file_path, formatter.content_type, filename
