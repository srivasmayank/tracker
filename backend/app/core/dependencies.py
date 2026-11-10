from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.repositories.category_repository import CategoryRepository
from app.repositories.expense_repository import ExpenseRepository
from app.repositories.group_repository import GroupRepository
from app.repositories.group_expense_repository import GroupExpenseRepository
from app.repositories.settlement_repository import SettlementRepository
from app.repositories.idempotency_repository import IdempotencyRepository
from app.repositories.recurring_expense_repository import RecurringExpenseRepository
from app.repositories.export_job_repository import ExportJobRepository

from app.services.auth_service import AuthService
from app.services.category_service import CategoryService
from app.services.expense_service import ExpenseService
from app.services.group_service import GroupService
from app.services.group_expense_service import GroupExpenseService
from app.services.settlement_service import SettlementService
from app.services.idempotency_service import IdempotencyService
from app.services.recurring_expense_service import RecurringExpenseService
from app.services.export_service import ExportService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


# Repositories Dependency Providers
def get_user_repository(db: Session = Depends(get_db)) -> UserRepository:
    return UserRepository(db)


def get_category_repository(db: Session = Depends(get_db)) -> CategoryRepository:
    return CategoryRepository(db)


def get_expense_repository(db: Session = Depends(get_db)) -> ExpenseRepository:
    return ExpenseRepository(db)


def get_group_repository(db: Session = Depends(get_db)) -> GroupRepository:
    return GroupRepository(db)


def get_group_expense_repository(db: Session = Depends(get_db)) -> GroupExpenseRepository:
    return GroupExpenseRepository(db)


def get_settlement_repository(db: Session = Depends(get_db)) -> SettlementRepository:
    return SettlementRepository(db)


def get_idempotency_repository(db: Session = Depends(get_db)) -> IdempotencyRepository:
    return IdempotencyRepository(db)


def get_recurring_expense_repository(db: Session = Depends(get_db)) -> RecurringExpenseRepository:
    return RecurringExpenseRepository(db)


def get_export_job_repository(db: Session = Depends(get_db)) -> ExportJobRepository:
    return ExportJobRepository(db)


# Services Dependency Providers
def get_idempotency_service(
    idempotency_repo: IdempotencyRepository = Depends(get_idempotency_repository)
) -> IdempotencyService:
    return IdempotencyService(idempotency_repo)


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


def get_group_service(
    group_repo: GroupRepository = Depends(get_group_repository),
    user_repo: UserRepository = Depends(get_user_repository)
) -> GroupService:
    return GroupService(group_repo, user_repo)


def get_group_expense_service(
    group_repo: GroupRepository = Depends(get_group_repository),
    group_expense_repo: GroupExpenseRepository = Depends(get_group_expense_repository),
    category_repo: CategoryRepository = Depends(get_category_repository),
    idempotency_service: IdempotencyService = Depends(get_idempotency_service)
) -> GroupExpenseService:
    return GroupExpenseService(group_repo, group_expense_repo, category_repo, idempotency_service)


def get_settlement_service(
    group_repo: GroupRepository = Depends(get_group_repository),
    group_expense_repo: GroupExpenseRepository = Depends(get_group_expense_repository),
    settlement_repo: SettlementRepository = Depends(get_settlement_repository),
    idempotency_service: IdempotencyService = Depends(get_idempotency_service)
) -> SettlementService:
    return SettlementService(group_repo, group_expense_repo, settlement_repo, idempotency_service)


def get_recurring_expense_service(
    db: Session = Depends(get_db),
    recurring_repo: RecurringExpenseRepository = Depends(get_recurring_expense_repository),
    expense_repo: ExpenseRepository = Depends(get_expense_repository),
    category_repo: CategoryRepository = Depends(get_category_repository)
) -> RecurringExpenseService:
    return RecurringExpenseService(db, recurring_repo, expense_repo, category_repo)


def get_export_service(
    db: Session = Depends(get_db),
    job_repo: ExportJobRepository = Depends(get_export_job_repository)
) -> ExportService:
    return ExportService(db, job_repo)


# Security / Authentication Guard
def get_current_user(
    token: str = Depends(oauth2_scheme),
    user_repo: UserRepository = Depends(get_user_repository)
) -> User:
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
