import csv
import io
import json
from datetime import date, timedelta
from fastapi.testclient import TestClient

from app.services.recurring_expense_service import advance_due_date


def create_user_and_login(client: TestClient, email: str, name: str) -> dict:
    """Helper to register and authenticate a user with distinct client IP."""
    ip = f"10.0.{abs(hash(email)) % 240 + 1}.1"
    ip_headers = {"X-Forwarded-For": ip}
    client.post("/api/v1/auth/register", json={
        "email": email,
        "full_name": name,
        "password": "Password123!",
        "currency": "USD"
    }, headers=ip_headers)
    res = client.post("/api/v1/auth/login", json={
        "email": email,
        "password": "Password123!"
    }, headers=ip_headers)
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}", "X-Forwarded-For": ip}


def test_advance_due_date_calculation():
    """Unit test for date advancement and leap year / month clamping logic."""
    # Daily
    d1 = date(2026, 11, 10)
    assert advance_due_date(d1, "DAILY") == date(2026, 11, 11)

    # Weekly
    assert advance_due_date(d1, "WEEKLY") == date(2026, 11, 17)

    # Monthly standard
    assert advance_due_date(date(2026, 1, 15), "MONTHLY") == date(2026, 2, 15)

    # Monthly clamping: Jan 31 -> Feb 28
    assert advance_due_date(date(2026, 1, 31), "MONTHLY") == date(2026, 2, 28)

    # Yearly standard
    assert advance_due_date(date(2026, 5, 20), "YEARLY") == date(2027, 5, 20)

    # Yearly leap day clamp: Feb 29 2024 -> Feb 28 2025
    assert advance_due_date(date(2024, 2, 29), "YEARLY") == date(2025, 2, 28)


def test_recurring_subscription_crud_and_batch_processing(client: TestClient):
    """
    Integration test:
    1. Create a monthly recurring subscription for Netflix ($15.99).
    2. Batch process with target_date = today.
    3. Verify concrete Expense created and next_due_date advanced.
    """
    headers = create_user_and_login(client, "sub_user@example.com", "Sub User")
    cats = client.get("/api/v1/categories", headers=headers).json()
    cat_id = cats[0]["id"]

    today = date.today()
    # 1. Create recurring rule starting today
    res = client.post("/api/v1/recurring", json={
        "category_id": cat_id,
        "amount": 15.99,
        "description": "Netflix Subscription",
        "frequency": "MONTHLY",
        "start_date": str(today),
        "payment_method": "CARD"
    }, headers=headers)
    assert res.status_code == 201
    rec_data = res.json()
    recurring_id = rec_data["id"]
    assert rec_data["next_due_date"] == str(today)
    assert rec_data["is_active"] is True

    # 2. Trigger batch processing for today
    batch_res = client.post(f"/api/v1/recurring/process-due?target_date={today}", headers=headers)
    assert batch_res.status_code == 200
    batch_data = batch_res.json()
    assert batch_data["processed_count"] >= 1
    assert len(batch_data["created_expense_ids"]) >= 1

    # 3. Verify concrete expense was created in expenses list
    expenses_res = client.get("/api/v1/expenses", headers=headers)
    assert expenses_res.status_code == 200
    items = expenses_res.json()["items"]
    recurring_expense = next((e for e in items if "[Recurring] Netflix Subscription" in e["description"]), None)
    assert recurring_expense is not None
    assert float(recurring_expense["amount"]) == 15.99

    # 4. Verify subscription rule was advanced by 1 month
    get_rule = client.get(f"/api/v1/recurring/{recurring_id}", headers=headers).json()
    expected_next = advance_due_date(today, "MONTHLY")
    assert get_rule["next_due_date"] == str(expected_next)


def test_recurring_subscription_auto_deactivates_after_end_date(client: TestClient):
    """
    Verifies that recurring subscriptions auto-deactivate when next_due_date exceeds end_date.
    """
    headers = create_user_and_login(client, "expire_user@example.com", "Expire User")
    cats = client.get("/api/v1/categories", headers=headers).json()
    cat_id = cats[0]["id"]

    today = date.today()
    # Rule with end_date equal to today (one-off daily)
    res = client.post("/api/v1/recurring", json={
        "category_id": cat_id,
        "amount": 5.00,
        "description": "Daily Newspaper Promo",
        "frequency": "DAILY",
        "start_date": str(today),
        "end_date": str(today),
        "payment_method": "CASH"
    }, headers=headers)
    assert res.status_code == 201
    rule_id = res.json()["id"]

    # Process due
    client.post(f"/api/v1/recurring/process-due?target_date={today}", headers=headers)

    # Since next_due_date (today + 1 day) > end_date (today), is_active should now be False
    updated_rule = client.get(f"/api/v1/recurring/{rule_id}", headers=headers).json()
    assert updated_rule["is_active"] is False


def test_asynchronous_statement_export_csv_and_json(client: TestClient):
    """
    Verifies asynchronous statement generation:
    1. Creates test expenses.
    2. Enqueues CSV export job, receives 202 Accepted.
    3. Status polls until COMPLETED.
    4. Downloads CSV file and verifies contents.
    5. Enqueues and downloads JSON export.
    """
    headers = create_user_and_login(client, "export_user@example.com", "Export User")
    cats = client.get("/api/v1/categories", headers=headers).json()
    cat_id = cats[0]["id"]

    # Seed 2 expenses
    client.post("/api/v1/expenses", json={
        "category_id": cat_id,
        "amount": 42.50,
        "description": "Book Store",
        "payment_method": "CARD"
    }, headers=headers)

    client.post("/api/v1/expenses", json={
        "category_id": cat_id,
        "amount": 18.00,
        "description": "Coffee Shop",
        "payment_method": "UPI"
    }, headers=headers)

    # 1. Request CSV export job (HTTP 202 Accepted)
    export_req = client.post("/api/v1/exports", json={"format": "CSV"}, headers=headers)
    assert export_req.status_code == 202
    job_info = export_req.json()
    job_id = job_info["job_id"]
    assert job_id.startswith("exp_")

    # In FastAPI TestClient, background_tasks run before the request returns
    status_res = client.get(f"/api/v1/exports/{job_id}", headers=headers)
    assert status_res.status_code == 200
    status_data = status_res.json()
    assert status_data["status"] == "COMPLETED"
    assert status_data["total_records"] == 2
    assert status_data["download_url"] is not None

    # 2. Download and verify CSV file content
    download_res = client.get(f"/api/v1/exports/{job_id}/download", headers=headers)
    assert download_res.status_code == 200
    assert "text/csv" in download_res.headers["content-type"]
    csv_text = download_res.content.decode("utf-8-sig")  # strip BOM
    reader = csv.DictReader(io.StringIO(csv_text))
    rows = list(reader)
    assert len(rows) == 2
    descriptions = [r["description"] for r in rows]
    assert "Book Store" in descriptions
    assert "Coffee Shop" in descriptions

    # 3. Request JSON export job
    json_req = client.post("/api/v1/exports", json={"format": "JSON"}, headers=headers)
    assert json_req.status_code == 202
    json_job_id = json_req.json()["job_id"]

    json_download = client.get(f"/api/v1/exports/{json_job_id}/download", headers=headers)
    assert json_download.status_code == 200
    assert "application/json" in json_download.headers["content-type"]
    data = json.loads(json_download.content.decode("utf-8"))
    assert isinstance(data, list)
    assert len(data) == 2
