from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
from app.schemas.user import UserResponse


class SettlementCreate(BaseModel):
    payee_id: int = Field(..., description="User ID of member receiving the repayment")
    amount: Decimal = Field(..., gt=0, decimal_places=2, description="Settlement amount")
    notes: Optional[str] = Field(None, max_length=255)


class SettlementResponse(BaseModel):
    id: int
    group_id: int
    payer_id: int
    payee_id: int
    amount: Decimal
    notes: Optional[str] = None
    settled_at: datetime
    payer: Optional[UserResponse] = None
    payee: Optional[UserResponse] = None

    model_config = ConfigDict(from_attributes=True)


class DebtItem(BaseModel):
    """Represents a simplified single settlement transaction needed to resolve debts."""
    debtor_id: int
    debtor_name: str
    creditor_id: int
    creditor_name: str
    amount: Decimal


class MemberBalance(BaseModel):
    """Net standing of an individual member inside the group."""
    user_id: int
    full_name: str
    email: str
    net_balance: Decimal
    total_paid: Decimal
    total_owed: Decimal


class GroupBalancesResponse(BaseModel):
    group_id: int
    total_spending: Decimal
    members: List[MemberBalance]
    simplified_debts: List[DebtItem]

