from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict, field_validator
from app.schemas.category import CategoryResponse


class ExpenseBase(BaseModel):
    category_id: int
    amount: Decimal = Field(..., gt=0, decimal_places=2, description="Expense amount must be strictly greater than 0")
    currency: str = Field(default="USD", min_length=3, max_length=3)
    description: str = Field(..., min_length=1, max_length=255)
    expense_date: date = Field(default_factory=date.today)
    payment_method: str = Field(default="CASH", pattern="^(CASH|CARD|UPI|TRANSFER|OTHER)$")


class ExpenseCreate(ExpenseBase):
    pass


class ExpenseUpdate(BaseModel):
    category_id: Optional[int] = None
    amount: Optional[Decimal] = Field(None, gt=0, decimal_places=2)
    currency: Optional[str] = Field(None, min_length=3, max_length=3)
    description: Optional[str] = Field(None, min_length=1, max_length=255)
    expense_date: Optional[date] = None
    payment_method: Optional[str] = Field(None, pattern="^(CASH|CARD|UPI|TRANSFER|OTHER)$")


class ExpenseResponse(ExpenseBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    category: Optional[CategoryResponse] = None

    model_config = ConfigDict(from_attributes=True)


class CategorySpendingSummary(BaseModel):
    category_id: int
    category_name: str
    category_color: str
    category_icon: str
    total_amount: Decimal
    percentage: float


class ExpenseSummaryResponse(BaseModel):
    total_spent: Decimal
    total_transactions: int
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    categories: List[CategorySpendingSummary]

