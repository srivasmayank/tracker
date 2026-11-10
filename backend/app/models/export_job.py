from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


class ExportJob(Base):
    """
    Asynchronous export job state tracker.
    Allows clients to trigger large CSV/PDF generation out-of-band and poll or download
    the generated file when ready, eliminating HTTP request timeouts.
    """
    __tablename__ = "export_jobs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    job_id = Column(String(64), unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    format = Column(String(10), default="CSV", nullable=False)  # CSV, JSON
    status = Column(String(20), default="PENDING", nullable=False, index=True)  # PENDING, PROCESSING, COMPLETED, FAILED
    file_path = Column(String(255), nullable=True)
    total_records = Column(Integer, default=0, nullable=False)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User")

    def __repr__(self) -> str:
        return f"<ExportJob(job_id='{self.job_id}', user_id={self.user_id}, status='{self.status}', records={self.total_records})>"
