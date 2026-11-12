from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
from app.schemas.user import UserResponse
from app.schemas.category import CategoryResponse


class SplitType(str, Enum):
    EQUAL = "EQUAL"
    EXACT = "EXACT"
    PERCENTAGE = "PERCENTAGE"
    SHARES = "SHARES"


class ExpenseSplitInput(BaseModel):
    user_id: int
    owed_amount: Optional[Decimal] = Field(None, gt=0, decimal_places=2)
    percentage: Optional[Decimal] = Field(None, gt=0, le=100, decimal_places=2)
    shares: Optional[int] = Field(None, gt=0)


class ExpenseSplitResponse(BaseModel):
    id: int
    user_id: int
    owed_amount: Decimal
    percentage: Optional[Decimal] = None
    shares: Optional[int] = None
    user: Optional[UserResponse] = None

    model_config = ConfigDict(from_attributes=True)


class GroupExpenseCreate(BaseModel):
    category_id: int
    amount: Decimal = Field(..., gt=0, decimal_places=2)
    currency: Optional[str] = Field(default=None, min_length=3, max_length=3, description="Currency of this expense. Defaults to group base currency if omitted.")
    description: str = Field(..., min_length=1, max_length=255)
    split_type: SplitType = Field(default=SplitType.EQUAL)
    expense_date: date = Field(default_factory=date.today)
    paid_by_user_id: Optional[int] = None  # Defaults to authenticated requester if None
    splits: Optional[List[ExpenseSplitInput]] = Field(
        default=None,
        description="List of participant splits. For EQUAL, can be just user_ids; if omitted, all group members split equally."
    )


class GroupExpenseResponse(BaseModel):
    id: int
    group_id: int
    paid_by_user_id: int
    category_id: int
    amount: Decimal
    currency: str = "USD"
    exchange_rate: Decimal = Decimal("1.000000")
    base_amount: Optional[Decimal] = None
    description: str
    split_type: SplitType
    expense_date: date
    created_at: datetime
    payer: Optional[UserResponse] = None
    category: Optional[CategoryResponse] = None
    splits: List[ExpenseSplitResponse] = []

    model_config = ConfigDict(from_attributes=True)

