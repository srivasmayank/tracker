from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from app.schemas.user import UserCreate, UserLogin, UserResponse
from app.schemas.token import Token
from app.models.user import User
from app.services.auth_service import AuthService
from app.core.dependencies import get_auth_service, get_current_user
from app.core.rate_limiter import RateLimiter

router = APIRouter(prefix="/auth", tags=["Authentication"])

# Rate limiters: 5 requests per 60 seconds per IP on auth endpoints
auth_limiter = RateLimiter(limit=5, window_seconds=60, scope="auth_gate")


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(auth_limiter)]
)
def register(
    user_in: UserCreate,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Register a new user account.
    Creates user, hashes password with bcrypt, and seeds initial categories.
    Throttled to 5 requests per 60 seconds per IP to prevent spam accounts.
    """
    return auth_service.register_user(user_in)


@router.post(
    "/login",
    response_model=Token,
    dependencies=[Depends(auth_limiter)]
)
def login_json(
    credentials: UserLogin,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Standard JSON login endpoint for Single Page Applications (React).
    Protected against brute-force password guessing (Max 5 attempts / 60s).
    """
    token, _ = auth_service.authenticate_user(
        email=credentials.email,
        password=credentials.password
    )
    return token


@router.post(
    "/login/form",
    response_model=Token,
    dependencies=[Depends(auth_limiter)]
)
def login_form(
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    OAuth2 standard form-encoded login endpoint (used by Swagger /docs authorize button).
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
