from datetime import date
from decimal import Decimal
from typing import List, Optional, Tuple
from fastapi import HTTPException, status
from app.models.expense import Expense
from app.schemas.expense import (
    ExpenseCreate,
    ExpenseUpdate,
    ExpenseSummaryResponse,
    CategorySpendingSummary
)
from app.repositories.expense_repository import ExpenseRepository
from app.repositories.category_repository import CategoryRepository


class ExpenseService:
    """
    Business logic layer for personal Expense management.
    Enforces business rules and authorization policies.
    """

    def __init__(self, expense_repo: ExpenseRepository, category_repo: CategoryRepository):
        self.expense_repo = expense_repo
        self.category_repo = category_repo

    def create_expense(self, user_id: int, data: ExpenseCreate) -> Expense:
        """
        Validates category ownership/accessibility, then creates the expense record.
        """
        category = self.category_repo.get_user_category_by_id(data.category_id, user_id)
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found or you do not have permission to use it."
            )

        expense = Expense(
            user_id=user_id,
            category_id=data.category_id,
            amount=data.amount,
            description=data.description.strip(),
            expense_date=data.expense_date,
            payment_method=data.payment_method
        )
        created = self.expense_repo.create(expense)
        # Fetch with eager loaded category relation for complete response serialization
        return self.expense_repo.get_user_expense_by_id(created.id, user_id)

    def get_expenses(
        self,
        user_id: int,
        category_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        payment_method: Optional[str] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 50
    ) -> Tuple[List[Expense], int]:
        """Retrieves user's filtered paginated expenses."""
        return self.expense_repo.list_user_expenses(
            user_id=user_id,
            category_id=category_id,
            start_date=start_date,
            end_date=end_date,
            payment_method=payment_method,
            search=search,
            skip=skip,
            limit=limit
        )

    def get_expense_by_id(self, user_id: int, expense_id: int) -> Expense:
        """Fetch expense ensuring strict user tenancy."""
        expense = self.expense_repo.get_user_expense_by_id(expense_id, user_id)
        if not expense:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Expense not found or access denied."
            )
        return expense

    def update_expense(self, user_id: int, expense_id: int, data: ExpenseUpdate) -> Expense:
        """Updates an expense if authorized."""
        expense = self.get_expense_by_id(user_id, expense_id)

        if data.category_id is not None and data.category_id != expense.category_id:
            category = self.category_repo.get_user_category_by_id(data.category_id, user_id)
            if not category:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Specified target category does not exist."
                )
            expense.category_id = data.category_id

        if data.amount is not None:
            expense.amount = data.amount
        if data.description is not None:
            expense.description = data.description.strip()
        if data.expense_date is not None:
            expense.expense_date = data.expense_date
        if data.payment_method is not None:
            expense.payment_method = data.payment_method

        updated = self.expense_repo.update(expense)
        return self.expense_repo.get_user_expense_by_id(updated.id, user_id)

    def delete_expense(self, user_id: int, expense_id: int) -> None:
        """Removes an expense record from the ledger."""
        expense = self.get_expense_by_id(user_id, expense_id)
        self.expense_repo.delete(expense)

    def get_analytics_summary(
        self,
        user_id: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> ExpenseSummaryResponse:
        """
        Calculates total spent and breakdown percentages across categories.
        """
        breakdown = self.expense_repo.get_spending_summary(user_id, start_date, end_date)
        total_spent = sum((item["total_amount"] for item in breakdown), Decimal("0.00"))

        category_summaries = []
        for item in breakdown:
            total = item["total_amount"]
            pct = float((total / total_spent) * 100) if total_spent > 0 else 0.0
            category_summaries.append(
                CategorySpendingSummary(
                    category_id=item["category_id"],
                    category_name=item["category_name"],
                    category_color=item["category_color"],
                    category_icon=item["category_icon"],
                    total_amount=total,
                    percentage=round(pct, 2)
                )
            )

        # Count total transactions in interval
        _, total_count = self.expense_repo.list_user_expenses(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
            limit=1
        )

        return ExpenseSummaryResponse(
            total_spent=total_spent,
            total_transactions=total_count,
            start_date=start_date,
            end_date=end_date,
            categories=category_summaries
        )

