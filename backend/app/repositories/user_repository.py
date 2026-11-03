from typing import Optional
from sqlalchemy.orm import Session
from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """Data access repository for User entity operations."""

    def __init__(self, db: Session):
        super().__init__(User, db)

    def get_by_email(self, email: str) -> Optional[User]:
        """Fetch user by unique email address (case-insensitive)."""
        return self.db.query(User).filter(User.email == email.lower().strip()).first()

