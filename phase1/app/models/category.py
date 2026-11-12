from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


class Category(Base):
    """
    Category entity classifying incomes and expenses.
    If user_id is NULL, it is a system-wide default category.
    If user_id is set, it is a custom category owned by that user.
    """
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    type = Column(String(20), default="EXPENSE", nullable=False)  # EXPENSE or INCOME
    icon = Column(String(50), default="tag", nullable=False)
    color = Column(String(20), default="#6366F1", nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    user = relationship("User", back_populates="custom_categories")
    expenses = relationship("Expense", back_populates="category")

    def __repr__(self) -> str:
        return f"<Category(id={self.id}, name='{self.name}', type='{self.type}', user_id={self.user_id})>"

