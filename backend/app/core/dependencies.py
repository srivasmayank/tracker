from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.repositories.category_repository import CategoryRepository
from app.repositories.expense_repository import ExpenseRepository
from app.services.auth_service import AuthService
from app.services.category_service import CategoryService
from app.services.expense_service import ExpenseService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


# Repositories Dependency Providers
def get_user_repository(db: Session = Depends(get_db)) -> UserRepository:
    return UserRepository(db)


def get_category_repository(db: Session = Depends(get_db)) -> CategoryRepository:
    return CategoryRepository(db)


def get_expense_repository(db: Session = Depends(get_db)) -> ExpenseRepository:
    return ExpenseRepository(db)


# Services Dependency Providers
def get_auth_service(
    user_repo: UserRepository = Depends(get_user_repository),
    category_repo: CategoryRepository = Depends(get_category_repository)
) -> AuthService:
    return AuthService(user_repo, category_repo)


def get_category_service(
    category_repo: CategoryRepository = Depends(get_category_repository)
) -> CategoryService:
    return CategoryService(category_repo)


def get_expense_service(
    expense_repo: ExpenseRepository = Depends(get_expense_repository),
    category_repo: CategoryRepository = Depends(get_category_repository)
) -> ExpenseService:
    return ExpenseService(expense_repo, category_repo)


# Security / Authentication Guard
def get_current_user(
    token: str = Depends(oauth2_scheme),
    user_repo: UserRepository = Depends(get_user_repository)
) -> User:
    """
    Decodes the Bearer JWT token, validates claims, and injects the authenticated User instance.
    Guards endpoints against unauthenticated access.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_access_token(token)
    if not payload:
        raise credentials_exception

    user_id_str: str = payload.get("sub")
    if not user_id_str:
        raise credentials_exception

    try:
        user_id = int(user_id_str)
    except ValueError:
        raise credentials_exception

    user = user_repo.get_by_id(user_id)
    if not user:
        raise credentials_exception

    return user

