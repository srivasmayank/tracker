from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status

from app.core.dependencies import get_current_user, get_recurring_expense_service
from app.models.user import User
from app.schemas.recurring_expense import (
    RecurringExpenseCreate,
    RecurringExpenseUpdate,
    RecurringExpenseResponse,
    BatchProcessResult,
)
from app.services.recurring_expense_service import RecurringExpenseService

router = APIRouter(prefix="/recurring", tags=["Recurring Expenses & Automation"])


@router.post("", response_model=RecurringExpenseResponse, status_code=status.HTTP_201_CREATED)
def create_recurring_expense(
    data: RecurringExpenseCreate,
    current_user: User = Depends(get_current_user),
    service: RecurringExpenseService = Depends(get_recurring_expense_service),
):
    """
    Register a new recurring expense rule (e.g., Netflix monthly subscription, rent).
    Future concrete expenses will be automatically generated upon batch trigger.
    """
    return service.create_recurring(user_id=current_user.id, schema=data)


@router.get("", response_model=List[RecurringExpenseResponse])
def list_recurring_expenses(
    active_only: bool = Query(False, description="Filter only active recurring subscriptions"),
    current_user: User = Depends(get_current_user),
    service: RecurringExpenseService = Depends(get_recurring_expense_service),
):
    """List recurring rules configured for the authenticated user."""
    return service.get_user_recurring(user_id=current_user.id, active_only=active_only)


@router.get("/{recurring_id}", response_model=RecurringExpenseResponse)
def get_recurring_expense(
    recurring_id: int,
    current_user: User = Depends(get_current_user),
    service: RecurringExpenseService = Depends(get_recurring_expense_service),
):
    """Get single recurring subscription by ID."""
    return service.get_by_id(user_id=current_user.id, recurring_id=recurring_id)


@router.put("/{recurring_id}", response_model=RecurringExpenseResponse)
def update_recurring_expense(
    recurring_id: int,
    data: RecurringExpenseUpdate,
    current_user: User = Depends(get_current_user),
    service: RecurringExpenseService = Depends(get_recurring_expense_service),
):
    """Update recurring subscription parameters (amount, frequency, active status)."""
    return service.update_recurring(user_id=current_user.id, recurring_id=recurring_id, schema=data)


@router.delete("/{recurring_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_recurring_expense(
    recurring_id: int,
    current_user: User = Depends(get_current_user),
    service: RecurringExpenseService = Depends(get_recurring_expense_service),
):
    """Delete a recurring subscription rule."""
    service.delete_recurring(user_id=current_user.id, recurring_id=recurring_id)


@router.post("/process-due", response_model=BatchProcessResult)
def process_due_recurring_expenses(
    target_date: Optional[date] = Query(None, description="Target execution date (defaults to today)"),
    current_user: User = Depends(get_current_user),
    service: RecurringExpenseService = Depends(get_recurring_expense_service),
):
    """
    Trigger scheduled recurring expense execution engine.
    Finds all active subscriptions due on or before target_date, generates concrete
    Expense records, and advances recurrence dates in isolated atomic transactions.
    """
    return service.process_due_subscriptions(target_date=target_date)
