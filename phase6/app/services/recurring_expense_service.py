import calendar
import logging
from datetime import date, timedelta
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.expense import Expense
from app.models.recurring_expense import RecurringExpense
from app.repositories.recurring_expense_repository import RecurringExpenseRepository
from app.repositories.expense_repository import ExpenseRepository
from app.repositories.category_repository import CategoryRepository
from app.schemas.recurring_expense import (
    RecurringExpenseCreate,
    RecurringExpenseUpdate,
    BatchProcessResult,
    FrequencyEnum,
)

logger = logging.getLogger(__name__)


def advance_due_date(current_date: date, frequency: str) -> date:
    """
    Computes the next due date based on recurrence frequency.
    Safely handles month-end clamping (e.g., Jan 31 -> Feb 28) and leap years.
    """
    freq = frequency.upper()
    if freq == FrequencyEnum.DAILY:
        return current_date + timedelta(days=1)
    elif freq == FrequencyEnum.WEEKLY:
        return current_date + timedelta(weeks=1)
    elif freq == FrequencyEnum.MONTHLY:
        new_month = current_date.month + 1 if current_date.month < 12 else 1
        new_year = current_date.year if current_date.month < 12 else current_date.year + 1
        max_days = calendar.monthrange(new_year, new_month)[1]
        new_day = min(current_date.day, max_days)
        return date(new_year, new_month, new_day)
    elif freq == FrequencyEnum.YEARLY:
        try:
            return current_date.replace(year=current_date.year + 1)
        except ValueError:
            # Handles Feb 29 on leap years moving to Feb 28
            return current_date.replace(year=current_date.year + 1, day=28)
    else:
        raise ValueError(f"Unknown frequency: {frequency}")


class RecurringExpenseService:
    """
    Business service layer managing recurring subscription rules and their automated execution.
    Adheres to:
    - SRP: Only responsible for subscription lifecycle and scheduling logic.
    - Transaction Isolation (ACID): Each recurring subscription execution commits individually,
      preventing a failure in one rule from aborting processing of other users' subscriptions.
    """

    def __init__(
        self,
        db: Session,
        recurring_repo: RecurringExpenseRepository,
        expense_repo: ExpenseRepository,
        category_repo: CategoryRepository,
    ):
        self.db = db
        self.recurring_repo = recurring_repo
        self.expense_repo = expense_repo
        self.category_repo = category_repo

    def create_recurring(self, user_id: int, schema: RecurringExpenseCreate) -> RecurringExpense:
        # Verify category exists and belongs to user or is system category
        category = self.category_repo.get_by_id(schema.category_id)
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Category with id {schema.category_id} not found."
            )

        if schema.end_date and schema.end_date < schema.start_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="end_date cannot be earlier than start_date."
            )

        recurring = RecurringExpense(
            user_id=user_id,
            category_id=schema.category_id,
            amount=schema.amount,
            description=schema.description,
            frequency=schema.frequency.value,
            start_date=schema.start_date,
            next_due_date=schema.start_date,
            end_date=schema.end_date,
            payment_method=schema.payment_method,
            is_active=True,
        )
        return self.recurring_repo.create(recurring)

    def get_user_recurring(self, user_id: int, active_only: bool = False) -> List[RecurringExpense]:
        return self.recurring_repo.get_user_recurring(user_id=user_id, active_only=active_only)

    def get_by_id(self, user_id: int, recurring_id: int) -> RecurringExpense:
        recurring = self.recurring_repo.get_by_id_and_user(recurring_id, user_id)
        if not recurring:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Recurring expense {recurring_id} not found."
            )
        return recurring

    def update_recurring(
        self, user_id: int, recurring_id: int, schema: RecurringExpenseUpdate
    ) -> RecurringExpense:
        recurring = self.get_by_id(user_id, recurring_id)

        if schema.category_id is not None:
            cat = self.category_repo.get_by_id(schema.category_id)
            if not cat:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Category {schema.category_id} not found."
                )
            recurring.category_id = schema.category_id

        if schema.amount is not None:
            recurring.amount = schema.amount
        if schema.description is not None:
            recurring.description = schema.description
        if schema.frequency is not None:
            recurring.frequency = schema.frequency.value
        if schema.end_date is not None:
            recurring.end_date = schema.end_date
        if schema.payment_method is not None:
            recurring.payment_method = schema.payment_method
        if schema.is_active is not None:
            recurring.is_active = schema.is_active

        return self.recurring_repo.update(recurring)

    def delete_recurring(self, user_id: int, recurring_id: int) -> None:
        recurring = self.get_by_id(user_id, recurring_id)
        self.recurring_repo.delete(recurring)

    def process_due_subscriptions(self, target_date: Optional[date] = None) -> BatchProcessResult:
        """
        Processes all recurring expenses that are due on or before target_date.
        For each due subscription:
        1. Emits a concrete Expense record.
        2. Advances next_due_date.
        3. Deactivates if next_due_date > end_date.
        4. Commits per item so single errors do not block the batch.
        """
        if target_date is None:
            target_date = date.today()

        due_rules = self.recurring_repo.get_due_subscriptions(target_date)
        processed_count = 0
        failed_count = 0
        created_expense_ids: List[int] = []

        for rule in due_rules:
            try:
                # 1. Create concrete Expense
                expense = Expense(
                    user_id=rule.user_id,
                    category_id=rule.category_id,
                    amount=rule.amount,
                    description=f"[Recurring] {rule.description}",
                    expense_date=rule.next_due_date,
                    payment_method=rule.payment_method,
                )
                self.db.add(expense)
                self.db.flush()  # obtain generated expense.id

                # 2. Advance next due date
                next_date = advance_due_date(rule.next_due_date, rule.frequency)
                rule.next_due_date = next_date

                # 3. Check termination criteria
                if rule.end_date and next_date > rule.end_date:
                    rule.is_active = False

                self.db.commit()
                processed_count += 1
                created_expense_ids.append(expense.id)
                logger.info(
                    "Processed recurring subscription id=%d user=%d -> expense=%d next_due=%s",
                    rule.id,
                    rule.user_id,
                    expense.id,
                    rule.next_due_date,
                )
            except Exception as exc:
                self.db.rollback()
                failed_count += 1
                logger.error("Failed processing recurring expense id=%d: %s", rule.id, exc)

        return BatchProcessResult(
            target_date=target_date,
            processed_count=processed_count,
            created_expense_ids=created_expense_ids,
            failed_count=failed_count,
        )
