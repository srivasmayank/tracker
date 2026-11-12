from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
from app.schemas.category import CategoryResponse


class FrequencyEnum(str, Enum):
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"
    YEARLY = "YEARLY"


class RecurringExpenseBase(BaseModel):
    category_id: int
    amount: Decimal = Field(..., gt=0, decimal_places=2)
    description: str = Field(..., min_length=1, max_length=255)
    frequency: FrequencyEnum = Field(default=FrequencyEnum.MONTHLY)
    start_date: date = Field(default_factory=date.today)
    end_date: Optional[date] = None
    payment_method: str = Field(default="CARD", pattern="^(CASH|CARD|UPI|TRANSFER|OTHER)$")


class RecurringExpenseCreate(RecurringExpenseBase):
    pass


class RecurringExpenseUpdate(BaseModel):
    category_id: Optional[int] = None
    amount: Optional[Decimal] = Field(None, gt=0, decimal_places=2)
    description: Optional[str] = Field(None, min_length=1, max_length=255)
    frequency: Optional[FrequencyEnum] = None
    end_date: Optional[date] = None
    payment_method: Optional[str] = None
    is_active: Optional[bool] = None


class RecurringExpenseResponse(RecurringExpenseBase):
    id: int
    user_id: int
    next_due_date: date
    is_active: bool
    created_at: datetime
    updated_at: datetime
    category: Optional[CategoryResponse] = None

    model_config = ConfigDict(from_attributes=True)


class BatchProcessResult(BaseModel):
    target_date: date
    processed_count: int
    created_expense_ids: List[int]
    failed_count: int
