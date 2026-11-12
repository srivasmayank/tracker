from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.export_job import ExportJob
from app.repositories.base import BaseRepository


class ExportJobRepository(BaseRepository[ExportJob]):
    """
    Repository layer for managing asynchronous export job tracking records.
    """

    def __init__(self, db: Session):
        super().__init__(ExportJob, db)

    def get_by_job_id(self, job_id: str) -> Optional[ExportJob]:
        return self.db.query(ExportJob).filter(ExportJob.job_id == job_id).first()

    def get_by_job_id_and_user(self, job_id: str, user_id: int) -> Optional[ExportJob]:
        return (
            self.db.query(ExportJob)
            .filter(ExportJob.job_id == job_id, ExportJob.user_id == user_id)
            .first()
        )

    def get_user_jobs(self, user_id: int, limit: int = 10) -> List[ExportJob]:
        return (
            self.db.query(ExportJob)
            .filter(ExportJob.user_id == user_id)
            .order_by(ExportJob.created_at.desc())
            .limit(limit)
            .all()
        )

    def mark_processing(self, job: ExportJob) -> ExportJob:
        job.status = "PROCESSING"
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        return job

    def mark_completed(self, job: ExportJob, file_path: str, total_records: int) -> ExportJob:
        job.status = "COMPLETED"
        job.file_path = file_path
        job.total_records = total_records
        job.completed_at = datetime.now(timezone.utc)
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        return job

    def mark_failed(self, job: ExportJob, error_message: str) -> ExportJob:
        job.status = "FAILED"
        job.error_message = error_message
        job.completed_at = datetime.now(timezone.utc)
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        return job
