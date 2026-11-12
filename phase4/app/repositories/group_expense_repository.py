from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from app.models.group_expense import GroupExpense, ExpenseSplit
from app.repositories.base import BaseRepository


class GroupExpenseRepository(BaseRepository[GroupExpense]):
    """Data access repository for Group Expense and Splits persistence."""

    def __init__(self, db: Session):
        super().__init__(GroupExpense, db)

    def create_atomic_group_expense(
        self,
        expense: GroupExpense,
        splits: List[ExpenseSplit]
    ) -> GroupExpense:
        """
        Atomically persists a GroupExpense and its individual ExpenseSplits.
        Guarantees ACID Atomicity: If any split row fails to insert,
        the entire transaction rolls back.
        """
        try:
            self.db.add(expense)
            self.db.flush()  # Flushes to DB to obtain expense.id

            for split in splits:
                split.group_expense_id = expense.id
                self.db.add(split)

            self.db.commit()
            self.db.refresh(expense)

            # Re-fetch with all eager loads
            return self.get_by_id_eager(expense.id)
        except Exception:
            self.db.rollback()
            raise

    def get_by_id_eager(self, expense_id: int) -> Optional[GroupExpense]:
        """Fetch group expense with payer, category, and splits eagerly loaded."""
        return (
            self.db.query(GroupExpense)
            .options(
                joinedload(GroupExpense.payer),
                joinedload(GroupExpense.category),
                joinedload(GroupExpense.splits).joinedload(ExpenseSplit.user)
            )
            .filter(GroupExpense.id == expense_id)
            .first()
        )

    def list_by_group(self, group_id: int) -> List[GroupExpense]:
        """Fetch all expenses for a group sorted by date descending."""
        return (
            self.db.query(GroupExpense)
            .options(
                joinedload(GroupExpense.payer),
                joinedload(GroupExpense.category),
                joinedload(GroupExpense.splits).joinedload(ExpenseSplit.user)
            )
            .filter(GroupExpense.group_id == group_id)
            .order_by(GroupExpense.expense_date.desc(), GroupExpense.id.desc())
            .all()
        )

