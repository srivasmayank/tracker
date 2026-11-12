from datetime import date
from typing import List, Optional
from sqlalchemy import or_
from sqlalchemy.orm import Session
from app.models.recurring_expense import RecurringExpense
from app.repositories.base import BaseRepository


class RecurringExpenseRepository(BaseRepository[RecurringExpense]):
    """
    Repository layer for managing recurring subscription templates.
    Isolates database querying from background execution logic.
    """

    def __init__(self, db: Session):
        super().__init__(RecurringExpense, db)

    def get_by_id_and_user(self, recurring_id: int, user_id: int) -> Optional[RecurringExpense]:
        return (
            self.db.query(RecurringExpense)
            .filter(RecurringExpense.id == recurring_id, RecurringExpense.user_id == user_id)
            .first()
        )

    def get_user_recurring(self, user_id: int, active_only: bool = False) -> List[RecurringExpense]:
        query = self.db.query(RecurringExpense).filter(RecurringExpense.user_id == user_id)
        if active_only:
            query = query.filter(RecurringExpense.is_active == True)
        return query.order_by(RecurringExpense.next_due_date.asc()).all()

    def get_due_subscriptions(self, target_date: date) -> List[RecurringExpense]:
        """
        Retrieves all active recurring rules that have reached or passed their due date,
        and have not exceeded their optional end_date.
        """
        return (
            self.db.query(RecurringExpense)
            .filter(
                RecurringExpense.is_active == True,
                RecurringExpense.next_due_date <= target_date,
                or_(
                    RecurringExpense.end_date.is_(None),
                    RecurringExpense.next_due_date <= RecurringExpense.end_date
                )
            )
            .order_by(RecurringExpense.next_due_date.asc())
            .all()
        )
