from typing import List
from fastapi import HTTPException, status
from app.models.category import Category
from app.schemas.category import CategoryCreate
from app.repositories.category_repository import CategoryRepository


class CategoryService:
    """Business logic layer for Category management."""

    def __init__(self, category_repo: CategoryRepository):
        self.category_repo = category_repo

    def get_categories(self, user_id: int) -> List[Category]:
        """Returns all system categories and user custom categories."""
        self.category_repo.seed_defaults_if_empty()
        return self.category_repo.get_accessible_categories(user_id)

    def create_custom_category(self, user_id: int, data: CategoryCreate) -> Category:
        """Creates a custom category owned by the authenticated user."""
        category = Category(
            name=data.name.strip(),
            type=data.type,
            icon=data.icon,
            color=data.color,
            user_id=user_id
        )
        return self.category_repo.create(category)

