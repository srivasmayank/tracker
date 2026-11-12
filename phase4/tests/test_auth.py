from fastapi.testclient import TestClient


def test_register_user_success(client: TestClient):
    response = client.post("/api/v1/auth/register", json={
        "email": "alice@example.com",
        "full_name": "Alice Wonder",
        "password": "SecurePassword999",
        "currency": "EUR"
    })
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "alice@example.com"
    assert data["full_name"] == "Alice Wonder"
    assert data["currency"] == "EUR"
    assert "id" in data
    assert "password" not in data  # Never expose hashed or raw password


def test_register_duplicate_email_fails(client: TestClient):
    payload = {
        "email": "duplicate@example.com",
        "full_name": "First User",
        "password": "Password123"
    }
    client.post("/api/v1/auth/register", json=payload)

    # Attempt to register again with same email
    second_res = client.post("/api/v1/auth/register", json=payload)
    assert second_res.status_code == 409
    assert "already exists" in second_res.json()["detail"]


def test_login_success(client: TestClient):
    client.post("/api/v1/auth/register", json={
        "email": "bob@example.com",
        "full_name": "Bob Builder",
        "password": "SecretPassword123"
    })

    login_res = client.post("/api/v1/auth/login", json={
        "email": "bob@example.com",
        "password": "SecretPassword123"
    })
    assert login_res.status_code == 200
    token_data = login_res.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"


def test_login_invalid_password(client: TestClient):
    client.post("/api/v1/auth/register", json={
        "email": "charlie@example.com",
        "full_name": "Charlie Chaplin",
        "password": "CorrectPassword123"
    })

    login_res = client.post("/api/v1/auth/login", json={
        "email": "charlie@example.com",
        "password": "WrongPassword!"
    })
    assert login_res.status_code == 401

