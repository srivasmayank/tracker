from typing import List
from fastapi import APIRouter, Depends, status
from app.models.user import User
from app.schemas.category import CategoryCreate, CategoryResponse
from app.services.category_service import CategoryService
from app.core.dependencies import get_category_service, get_current_user

router = APIRouter(prefix="/categories", tags=["Categories"])


@router.get("", response_model=List[CategoryResponse])
def list_categories(
    current_user: User = Depends(get_current_user),
    category_service: CategoryService = Depends(get_category_service)
):
    """
    List all available categories for the authenticated user,
    including system default categories and user custom categories.
    """
    return category_service.get_categories(user_id=current_user.id)


@router.post("", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_custom_category(
    category_in: CategoryCreate,
    current_user: User = Depends(get_current_user),
    category_service: CategoryService = Depends(get_category_service)
):
    """
    Create a new custom category for the authenticated user.
    """
    return category_service.create_custom_category(user_id=current_user.id, data=category_in)

