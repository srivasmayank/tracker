import os
from pathlib import Path
import pytest
from typing import Generator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

# Set test environment
TEST_DB_FILE = Path("./test_expenses.db")
SQLALCHEMY_TEST_DATABASE_URL = f"sqlite:///{TEST_DB_FILE.as_posix()}"

from app.core.database import Base, get_db
from app.core.rate_limiter import default_rate_limit_storage
from app.main import app

engine_test = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine_test)


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Create all tables before test session runs, drop and remove file when finished."""
    Base.metadata.drop_all(bind=engine_test)
    Base.metadata.create_all(bind=engine_test)
    yield
    Base.metadata.drop_all(bind=engine_test)
    if TEST_DB_FILE.exists():
        try:
            TEST_DB_FILE.unlink()
        except Exception:
            pass


@pytest.fixture(autouse=True)
def reset_rate_limits():
    """Clear rate limiting counters before and after each test."""
    default_rate_limit_storage.clear()
    yield
    default_rate_limit_storage.clear()


@pytest.fixture()
def db_session() -> Generator[Session, None, None]:
    """Provide a clean session for each test."""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """TestClient with overridden get_db dependency pointing to the test database."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture()
def auth_headers(client: TestClient) -> dict:
    """Helper fixture to register a test user and obtain authenticated Bearer headers."""
    register_payload = {
        "email": "testuser@example.com",
        "full_name": "Test User",
        "password": "Password123!",
        "currency": "USD"
    }
    client.post("/api/v1/auth/register", json=register_payload)

    login_res = client.post("/api/v1/auth/login", json={
        "email": "testuser@example.com",
        "password": "Password123!"
    })
    token = login_res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
