from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from app.schemas.user import UserCreate, UserLogin, UserResponse
from app.schemas.token import Token
from app.models.user import User
from app.services.auth_service import AuthService
from app.core.dependencies import get_auth_service, get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(
    user_in: UserCreate,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Register a new user account.
    Creates user, hashes password with bcrypt, and seeds initial categories.
    """
    return auth_service.register_user(user_in)


@router.post("/login", response_model=Token)
def login_json(
    credentials: UserLogin,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Standard JSON login endpoint for Single Page Applications (React).
    Returns JWT access token.
    """
    token, _ = auth_service.authenticate_user(
        email=credentials.email,
        password=credentials.password
    )
    return token


@router.post("/login/form", response_model=Token)
def login_form(
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    OAuth2 standard form-encoded login endpoint (used by Swagger /docs authorize button).
    Uses username field as email.
    """
    token, _ = auth_service.authenticate_user(
        email=form_data.username,
        password=form_data.password
    )
    return token


@router.get("/me", response_model=UserResponse)
def get_current_user_profile(
    current_user: User = Depends(get_current_user)
):
    """
    Returns the profile information of the currently authenticated user.
    """
    return current_user

