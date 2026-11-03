from datetime import timedelta
from typing import Optional, Tuple
from fastapi import HTTPException, status
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse
from app.schemas.token import Token
from app.repositories.user_repository import UserRepository
from app.repositories.category_repository import CategoryRepository
from app.core.security import verify_password, get_password_hash, create_access_token
from app.core.config import settings


class AuthService:
    """
    Business logic layer for authentication and identity management.
    Follows Single Responsibility Principle (SRP) by isolating authentication rules from HTTP transport.
    """

    def __init__(self, user_repo: UserRepository, category_repo: CategoryRepository):
        self.user_repo = user_repo
        self.category_repo = category_repo

    def register_user(self, user_in: UserCreate) -> User:
        """
        Registers a new user account.
        Enforces business invariants:
        - Email uniqueness
        - Password hashing via bcrypt
        - Auto-seeds default categories for the system if first run
        """
        existing_user = self.user_repo.get_by_email(user_in.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A user with this email address already exists."
            )

        # Make sure default categories exist
        self.category_repo.seed_defaults_if_empty()

        hashed_password = get_password_hash(user_in.password)
        new_user = User(
            email=user_in.email.lower().strip(),
            full_name=user_in.full_name.strip(),
            password_hash=hashed_password,
            currency=user_in.currency.upper()
        )
        return self.user_repo.create(new_user)

    def authenticate_user(self, email: str, password: str) -> Tuple[Token, User]:
        """
        Verifies credentials and issues a signed JWT access token.
        """
        user = self.user_repo.get_by_email(email)
        if not user or not verify_password(password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        token_str = create_access_token(
            subject=user.id,
            expires_delta=access_token_expires
        )
        return Token(access_token=token_str, token_type="bearer"), user

