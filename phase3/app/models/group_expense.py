from datetime import datetime, timezone, date
from sqlalchemy import Column, Integer, String, Numeric, Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


class GroupExpense(Base):
    """
    Group shared expense entity paid by one member on behalf of multiple group participants.
    """
    __tablename__ = "group_expenses"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    group_id = Column(Integer, ForeignKey("groups.id", ondelete="CASCADE"), nullable=False, index=True)
    paid_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="RESTRICT"), nullable=False, index=True)
    amount = Column(Numeric(12, 2), nullable=False)
    description = Column(String(255), nullable=False)
    split_type = Column(String(20), default="EQUAL", nullable=False)  # EQUAL, EXACT, PERCENTAGE, SHARES
    expense_date = Column(Date, default=date.today, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    group = relationship("Group", back_populates="expenses")
    payer = relationship("User", foreign_keys=[paid_by_user_id])
    category = relationship("Category")
    splits = relationship("ExpenseSplit", back_populates="group_expense", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<GroupExpense(id={self.id}, group_id={self.group_id}, amount={self.amount}, split='{self.split_type}')>"


class ExpenseSplit(Base):
    """
    Individual split participant's liability for a shared group expense.
    """
    __tablename__ = "expense_splits"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    group_expense_id = Column(Integer, ForeignKey("group_expenses.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    owed_amount = Column(Numeric(12, 2), nullable=False)
    percentage = Column(Numeric(5, 2), nullable=True)
    shares = Column(Integer, nullable=True)

    # Relationships
    group_expense = relationship("GroupExpense", back_populates="splits")
    user = relationship("User")

    def __repr__(self) -> str:
        return f"<ExpenseSplit(expense_id={self.group_expense_id}, user_id={self.user_id}, owed={self.owed_amount})>"

