import logging
from typing import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from app.core.config import settings

logger = logging.getLogger(__name__)

# Connect arguments
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

# Try connecting to configured database (e.g. MySQL)
# If unavailable (e.g. service stopped), fallback to SQLite for local development continuity
try:
    test_engine = create_engine(
        settings.DATABASE_URL,
        pool_pre_ping=True,
        connect_args=connect_args
    )
    # Perform immediate probe
    with test_engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    engine = test_engine
    logger.info(f"Connected to primary database: {settings.DATABASE_URL.split('@')[-1] if '@' in settings.DATABASE_URL else settings.DATABASE_URL}")
except Exception as e:
    logger.warning(
        f"Unable to connect to primary database ({settings.DATABASE_URL}). "
        f"Error: {e}. Falling back to SQLite: sqlite:///./expense_tracker.db"
    )
    engine = create_engine(
        "sqlite:///./expense_tracker.db",
        connect_args={"check_same_thread": False}
    )

# Session factory for generating Unit of Work DB sessions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Declarative Base for ORM Models
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency yielding a managed database session.
    Guarantees that the session is closed and any uncommitted exceptions are handled.
    Ensures ACID transaction boundaries per HTTP request.
    """
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
