from decimal import Decimal
from fastapi.testclient import TestClient


def test_categories_auto_seeded(client: TestClient, auth_headers: dict):
    response = client.get("/api/v1/categories", headers=auth_headers)
    assert response.status_code == 200
    categories = response.json()
    assert len(categories) >= 8
    category_names = [c["name"] for c in categories]
    assert "Food & Dining" in category_names
    assert "Rent & Housing" in category_names


def test_create_and_get_expense(client: TestClient, auth_headers: dict):
    # Fetch available categories
    cat_res = client.get("/api/v1/categories", headers=auth_headers)
    cat_id = cat_res.json()[0]["id"]

    # Create expense
    expense_payload = {
        "category_id": cat_id,
        "amount": 42.50,
        "description": "Team lunch at bistro",
        "expense_date": "2026-11-04",
        "payment_method": "CARD"
    }
    create_res = client.post("/api/v1/expenses", json=expense_payload, headers=auth_headers)
    assert create_res.status_code == 201
    expense_data = create_res.json()
    assert expense_data["description"] == "Team lunch at bistro"
    assert float(expense_data["amount"]) == 42.50
    assert expense_data["category"]["id"] == cat_id

    # List expenses
    list_res = client.get("/api/v1/expenses", headers=auth_headers)
    assert list_res.status_code == 200
    list_data = list_res.json()
    assert list_data["total"] >= 1
    assert any(item["id"] == expense_data["id"] for item in list_data["items"])


def test_reject_negative_or_zero_expense_amount(client: TestClient, auth_headers: dict):
    cat_res = client.get("/api/v1/categories", headers=auth_headers)
    cat_id = cat_res.json()[0]["id"]

    # Negative amount
    res_neg = client.post("/api/v1/expenses", json={
        "category_id": cat_id,
        "amount": -20.00,
        "description": "Invalid negative expense"
    }, headers=auth_headers)
    assert res_neg.status_code == 422  # Pydantic validation error

    # Zero amount
    res_zero = client.post("/api/v1/expenses", json={
        "category_id": cat_id,
        "amount": 0.00,
        "description": "Invalid zero expense"
    }, headers=auth_headers)
    assert res_zero.status_code == 422


def test_spending_summary_analytics(client: TestClient, auth_headers: dict):
    # Retrieve two distinct categories
    cat_res = client.get("/api/v1/categories", headers=auth_headers)
    categories = cat_res.json()
    cat_1 = categories[0]["id"]
    cat_2 = categories[1]["id"]

    # Add two expenses
    client.post("/api/v1/expenses", json={
        "category_id": cat_1,
        "amount": 100.00,
        "description": "Expense A"
    }, headers=auth_headers)

    client.post("/api/v1/expenses", json={
        "category_id": cat_2,
        "amount": 300.00,
        "description": "Expense B"
    }, headers=auth_headers)

    summary_res = client.get("/api/v1/expenses/summary", headers=auth_headers)
    assert summary_res.status_code == 200
    summary = summary_res.json()
    assert float(summary["total_spent"]) >= 400.00
    assert len(summary["categories"]) >= 2


def test_user_cannot_access_other_users_expense(client: TestClient):
    # Register User 1 and create an expense
    client.post("/api/v1/auth/register", json={
        "email": "user1@example.com",
        "full_name": "User One",
        "password": "Password123"
    })
    token1 = client.post("/api/v1/auth/login", json={
        "email": "user1@example.com",
        "password": "Password123"
    }).json()["access_token"]
    headers1 = {"Authorization": f"Bearer {token1}"}

    cats = client.get("/api/v1/categories", headers=headers1).json()
    exp = client.post("/api/v1/expenses", json={
        "category_id": cats[0]["id"],
        "amount": 99.00,
        "description": "User1 Private Item"
    }, headers=headers1).json()

    # Register User 2
    client.post("/api/v1/auth/register", json={
        "email": "user2@example.com",
        "full_name": "User Two",
        "password": "Password123"
    })
    token2 = client.post("/api/v1/auth/login", json={
        "email": "user2@example.com",
        "password": "Password123"
    }).json()["access_token"]
    headers2 = {"Authorization": f"Bearer {token2}"}

    # User 2 attempts to fetch User 1's expense
    res = client.get(f"/api/v1/expenses/{exp['id']}", headers=headers2)
    assert res.status_code == 404  # Strict multi-tenancy isolation

