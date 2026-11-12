from datetime import date
from decimal import Decimal
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, desc
from app.models.expense import Expense
from app.models.category import Category
from app.repositories.base import BaseRepository


class ExpenseRepository(BaseRepository[Expense]):
    """Data access repository for Expense entity operations."""

    def __init__(self, db: Session):
        super().__init__(Expense, db)

    def get_user_expense_by_id(self, expense_id: int, user_id: int) -> Optional[Expense]:
        """Fetch a specific expense ensuring it belongs to the given user."""
        return (
            self.db.query(Expense)
            .options(joinedload(Expense.category))
            .filter(Expense.id == expense_id, Expense.user_id == user_id)
            .first()
        )

    def list_user_expenses(
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
        """
        Retrieves a filtered, paginated list of expenses along with the total matching count.
        Eagerly loads related Category to avoid N+1 query performance bottleneck.
        """
        query = (
            self.db.query(Expense)
            .options(joinedload(Expense.category))
            .filter(Expense.user_id == user_id)
        )

        if category_id:
            query = query.filter(Expense.category_id == category_id)
        if start_date:
            query = query.filter(Expense.expense_date >= start_date)
        if end_date:
            query = query.filter(Expense.expense_date <= end_date)
        if payment_method:
            query = query.filter(Expense.payment_method == payment_method)
        if search:
            query = query.filter(Expense.description.ilike(f"%{search}%"))

        total_count = query.count()
        expenses = (
            query.order_by(desc(Expense.expense_date), desc(Expense.id))
            .offset(skip)
            .limit(limit)
            .all()
        )
        return expenses, total_count

    def get_spending_summary(
        self,
        user_id: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[Dict[str, Any]]:
        """
        Executes an aggregate query grouping expenses by category.
        Calculates SUM(amount) per category for financial dashboards.
        """
        query = (
            self.db.query(
                Category.id.label("category_id"),
                Category.name.label("category_name"),
                Category.color.label("category_color"),
                Category.icon.label("category_icon"),
                func.sum(Expense.amount).label("total_amount")
            )
            .join(Category, Expense.category_id == Category.id)
            .filter(Expense.user_id == user_id)
        )

        if start_date:
            query = query.filter(Expense.expense_date >= start_date)
        if end_date:
            query = query.filter(Expense.expense_date <= end_date)

        results = query.group_by(Category.id).all()

        return [
            {
                "category_id": r.category_id,
                "category_name": r.category_name,
                "category_color": r.category_color,
                "category_icon": r.category_icon,
                "total_amount": Decimal(str(r.total_amount or 0))
            }
            for r in results
        ]

