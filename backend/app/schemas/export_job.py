from datetime import datetime, date
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class ExportFormatEnum(str, Enum):
    CSV = "CSV"
    JSON = "JSON"


class ExportJobStatusEnum(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class ExportJobCreate(BaseModel):
    format: ExportFormatEnum = Field(default=ExportFormatEnum.CSV, description="Target export file format (CSV or JSON)")
    start_date: Optional[date] = Field(None, description="Optional start date filter for exported expenses")
    end_date: Optional[date] = Field(None, description="Optional end date filter for exported expenses")
    category_id: Optional[int] = Field(None, description="Optional category filter")


class ExportJobResponse(BaseModel):
    job_id: str
    status: str
    format: str
    message: str
    poll_url: str
    download_url: Optional[str] = None


class ExportStatusResponse(BaseModel):
    job_id: str
    user_id: int
    format: str
    status: str
    total_records: int
    error_message: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    download_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
