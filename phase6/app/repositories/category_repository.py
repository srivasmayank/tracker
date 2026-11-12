from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.models.category import Category
from app.repositories.base import BaseRepository


class CategoryRepository(BaseRepository[Category]):
    """Data access repository for Category entity operations."""

    def __init__(self, db: Session):
        super().__init__(Category, db)

    def get_accessible_categories(self, user_id: int) -> List[Category]:
        """
        Retrieves all categories available to a user:
        1. System-wide default categories (user_id IS NULL).
        2. Custom categories created by this user (user_id == user_id).
        """
        return (
            self.db.query(Category)
            .filter(or_(Category.user_id.is_(None), Category.user_id == user_id))
            .order_by(Category.name.asc())
            .all()
        )

    def get_user_category_by_id(self, category_id: int, user_id: int) -> Optional[Category]:
        """Verify whether a category exists and is accessible by the specified user."""
        return (
            self.db.query(Category)
            .filter(
                Category.id == category_id,
                or_(Category.user_id.is_(None), Category.user_id == user_id)
            )
            .first()
        )

    def seed_defaults_if_empty(self) -> None:
        """Seed initial default categories if none exist in the database."""
        default_count = self.db.query(Category).filter(Category.user_id.is_(None)).count()
        if default_count == 0:
            defaults = [
                Category(name="Food & Dining", type="EXPENSE", icon="utensils", color="#EF4444", user_id=None),
                Category(name="Rent & Housing", type="EXPENSE", icon="home", color="#3B82F6", user_id=None),
                Category(name="Transportation", type="EXPENSE", icon="car", color="#F59E0B", user_id=None),
                Category(name="Groceries", type="EXPENSE", icon="shopping-cart", color="#10B981", user_id=None),
                Category(name="Entertainment", type="EXPENSE", icon="film", color="#8B5CF6", user_id=None),
                Category(name="Utilities", type="EXPENSE", icon="zap", color="#6366F1", user_id=None),
                Category(name="Healthcare", type="EXPENSE", icon="heart-pulse", color="#EC4899", user_id=None),
                Category(name="Salary", type="INCOME", icon="briefcase", color="#059669", user_id=None),
                Category(name="Other", type="EXPENSE", icon="tag", color="#6B7280", user_id=None),
            ]
            self.db.add_all(defaults)
            self.db.commit()

