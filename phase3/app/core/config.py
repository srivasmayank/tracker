from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application configuration settings loaded from environment variables or .env file.
    Follows 12-factor app design methodology.
    """
    PROJECT_NAME: str = "Enterprise Expense Tracker"
    API_V1_STR: str = "/api/v1"
    
    # Security & JWT Secrets
    SECRET_KEY: str = "super-secret-key-change-in-production-min-32-chars-long"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Database Configuration (MySQL 8.0 by default, fallback to SQLite if needed)
    DATABASE_URL: str = "mysql+pymysql://root:password@localhost:3306/expense_tracker"
    
    # CORS Configuration
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",  # Vite React default port
        "http://localhost:3000",
        "http://127.0.0.1:5173"
    ]
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()

