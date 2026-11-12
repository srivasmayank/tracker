from datetime import date
from typing import Optional, List
from pydantic import BaseModel
from fastapi import APIRouter, Depends, Query, status
from app.models.user import User
from app.schemas.expense import (
    ExpenseCreate,
    ExpenseUpdate,
    ExpenseResponse,
    ExpenseSummaryResponse
)
from app.services.expense_service import ExpenseService
from app.core.dependencies import get_expense_service, get_current_user

router = APIRouter(prefix="/expenses", tags=["Expenses"])


class PaginatedExpenseResponse(BaseModel):
    items: List[ExpenseResponse]
    total: int
    skip: int
    limit: int


@router.post("", response_model=ExpenseResponse, status_code=status.HTTP_201_CREATED)
def create_expense(
    expense_in: ExpenseCreate,
    current_user: User = Depends(get_current_user),
    expense_service: ExpenseService = Depends(get_expense_service)
):
    """Record a new personal expense."""
    return expense_service.create_expense(user_id=current_user.id, data=expense_in)


@router.get("", response_model=PaginatedExpenseResponse)
def list_expenses(
    category_id: Optional[int] = Query(None, description="Filter by category ID"),
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    payment_method: Optional[str] = Query(None, description="Payment method (CASH, CARD, etc.)"),
    search: Optional[str] = Query(None, description="Search description keyword"),
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(50, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user),
    expense_service: ExpenseService = Depends(get_expense_service)
):
    """Retrieve filtered and paginated list of user's personal expenses."""
    items, total = expense_service.get_expenses(
        user_id=current_user.id,
        category_id=category_id,
        start_date=start_date,
        end_date=end_date,
        payment_method=payment_method,
        search=search,
        skip=skip,
        limit=limit
    )
    return PaginatedExpenseResponse(
        items=items,
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/summary", response_model=ExpenseSummaryResponse)
def get_spending_summary(
    start_date: Optional[date] = Query(None, description="Start date for summary"),
    end_date: Optional[date] = Query(None, description="End date for summary"),
    current_user: User = Depends(get_current_user),
    expense_service: ExpenseService = Depends(get_expense_service)
):
    """Aggregate spending summary and category percentages for dashboard analytics."""
    return expense_service.get_analytics_summary(
        user_id=current_user.id,
        start_date=start_date,
        end_date=end_date
    )


@router.get("/{expense_id}", response_model=ExpenseResponse)
def get_expense(
    expense_id: int,
    current_user: User = Depends(get_current_user),
    expense_service: ExpenseService = Depends(get_expense_service)
):
    """Fetch details of a single expense."""
    return expense_service.get_expense_by_id(user_id=current_user.id, expense_id=expense_id)


@router.put("/{expense_id}", response_model=ExpenseResponse)
def update_expense(
    expense_id: int,
    expense_in: ExpenseUpdate,
    current_user: User = Depends(get_current_user),
    expense_service: ExpenseService = Depends(get_expense_service)
):
    """Update an existing expense."""
    return expense_service.update_expense(
        user_id=current_user.id,
        expense_id=expense_id,
        data=expense_in
    )


@router.delete("/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_expense(
    expense_id: int,
    current_user: User = Depends(get_current_user),
    expense_service: ExpenseService = Depends(get_expense_service)
):
    """Delete an expense."""
    expense_service.delete_expense(user_id=current_user.id, expense_id=expense_id)
    return None

