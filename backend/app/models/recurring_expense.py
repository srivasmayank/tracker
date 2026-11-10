from datetime import datetime, timezone, date
from sqlalchemy import Column, Integer, String, Numeric, Date, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


class RecurringExpense(Base):
    """
    Recurring subscription or automated bill template (e.g. Netflix, Rent, Gym).
    A scheduled background worker queries active rules where next_due_date <= today
    and automatically instantiates real Expense records.
    """
    __tablename__ = "recurring_expenses"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="RESTRICT"), nullable=False, index=True)
    amount = Column(Numeric(12, 2), nullable=False)
    description = Column(String(255), nullable=False)
    frequency = Column(String(20), default="MONTHLY", nullable=False)  # DAILY, WEEKLY, MONTHLY, YEARLY
    start_date = Column(Date, default=date.today, nullable=False)
    next_due_date = Column(Date, nullable=False, index=True)
    end_date = Column(Date, nullable=True)
    payment_method = Column(String(50), default="CARD", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Relationships
    user = relationship("User")
    category = relationship("Category")

    def __repr__(self) -> str:
        return f"<RecurringExpense(id={self.id}, user_id={self.user_id}, amount={self.amount}, freq='{self.frequency}', next='{self.next_due_date}')>"
