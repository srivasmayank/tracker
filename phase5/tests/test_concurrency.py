import uuid
from decimal import Decimal
from fastapi.testclient import TestClient


def create_user_and_login(client: TestClient, email: str, name: str) -> dict:
    """Helper to register and authenticate a user, returning auth headers from their client IP."""
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


def test_idempotent_duplicate_expense_returns_cached_response(client: TestClient):
    """
    Simulates a client sending a request, suffering a network timeout,
    and retrying with the same X-Idempotency-Key.
    Guarantees:
    1. Returns identical response with identical expense ID.
    2. Only ONE record is created in the database.
    """
    h_alice = create_user_and_login(client, "alice.idem@example.com", "Alice Idem")
    h_bob = create_user_and_login(client, "bob.idem@example.com", "Bob Idem")

    grp = client.post("/api/v1/groups", json={
        "name": "Idempotency Test Group",
        "member_emails": ["bob.idem@example.com"]
    }, headers=h_alice).json()
    group_id = grp["id"]

    cats = client.get("/api/v1/categories", headers=h_alice).json()
    cat_id = cats[0]["id"]

    idem_key = str(uuid.uuid4())
    headers_with_idem = {**h_alice, "X-Idempotency-Key": idem_key}

    payload = {
        "category_id": cat_id,
        "amount": 75.50,
        "description": "Team Groceries",
        "split_type": "EQUAL"
    }

    # First attempt
    res1 = client.post(f"/api/v1/groups/{group_id}/expenses", json=payload, headers=headers_with_idem)
    assert res1.status_code == 201
    exp1 = res1.json()

    # Second duplicate attempt (Simulating network retry)
    res2 = client.post(f"/api/v1/groups/{group_id}/expenses", json=payload, headers=headers_with_idem)
    assert res2.status_code == 201
    exp2 = res2.json()

    # Must return exact same expense ID
    assert exp1["id"] == exp2["id"]
    assert exp1["amount"] == exp2["amount"]

    # Verify total expenses in group is strictly 1 (NOT 2!)
    all_expenses = client.get(f"/api/v1/groups/{group_id}/expenses", headers=h_alice).json()
    assert len(all_expenses) == 1


def test_idempotency_payload_tampering_rejected(client: TestClient):
    """
    If a client reuses an idempotency key with a modified payload,
    the server must detect payload tampering and reject with HTTP 422.
    """
    h_alice = create_user_and_login(client, "alice.tamper@example.com", "Alice Tamper")
    create_user_and_login(client, "bob.tamper@example.com", "Bob Tamper")

    grp = client.post("/api/v1/groups", json={
        "name": "Tamper Test Group",
        "member_emails": ["bob.tamper@example.com"]
    }, headers=h_alice).json()
    group_id = grp["id"]
    cats = client.get("/api/v1/categories", headers=h_alice).json()

    idem_key = str(uuid.uuid4())
    headers_with_idem = {**h_alice, "X-Idempotency-Key": idem_key}

    # First attempt with $50
    res1 = client.post(f"/api/v1/groups/{group_id}/expenses", json={
        "category_id": cats[0]["id"],
        "amount": 50.00,
        "description": "Original Purchase",
        "split_type": "EQUAL"
    }, headers=headers_with_idem)
    assert res1.status_code == 201

    # Second attempt reusing same key but changing amount to $90
    res2 = client.post(f"/api/v1/groups/{group_id}/expenses", json={
        "category_id": cats[0]["id"],
        "amount": 90.00,
        "description": "Tampered Purchase",
        "split_type": "EQUAL"
    }, headers=headers_with_idem)
    assert res2.status_code == 422
    assert "different request payload" in res2.json()["detail"]


def test_concurrency_prevention_of_over_settlement(client: TestClient):
    """
    Verifies that a debtor cannot settle more than their outstanding debt.
    """
    h_alice = create_user_and_login(client, "alice.settle@example.com", "Alice Settle")
    h_bob = create_user_and_login(client, "bob.settle@example.com", "Bob Settle")

    grp = client.post("/api/v1/groups", json={
        "name": "Over-Settlement Group",
        "member_emails": ["bob.settle@example.com"]
    }, headers=h_alice).json()
    group_id = grp["id"]

    alice_id = next(m["user_id"] for m in grp["members"] if m["user"]["email"] == "alice.settle@example.com")
    cats = client.get("/api/v1/categories", headers=h_alice).json()

    # Alice pays $100 for Alice and Bob ($50 each). Bob owes $50.
    client.post(f"/api/v1/groups/{group_id}/expenses", json={
        "category_id": cats[0]["id"],
        "amount": 100.00,
        "description": "Dinner",
        "split_type": "EQUAL"
    }, headers=h_alice)

    # Bob attempts to pay $60 (which is $10 more than the $50 debt)
    fail_res = client.post(f"/api/v1/groups/{group_id}/settle", json={
        "payee_id": alice_id,
        "amount": 60.00,
        "notes": "Attempting over-settle"
    }, headers=h_bob)
    assert fail_res.status_code == 400
    assert "exceeds total outstanding debt" in fail_res.json()["detail"]


def test_idempotent_settlement_replays_without_over_settlement_error(client: TestClient):
    """
    Critical financial flow:
    1. Bob owes Alice $50.
    2. Bob settles $50 with X-Idempotency-Key.
    3. Bob's app sends retry with same X-Idempotency-Key.
    4. Since debt is now $0, a naive check would throw 'You do not owe money'.
       The Idempotency Barrier MUST intercept and replay the cached 201 Created response!
    """
    h_alice = create_user_and_login(client, "alice.replay@example.com", "Alice Replay")
    h_bob = create_user_and_login(client, "bob.replay@example.com", "Bob Replay")

    grp = client.post("/api/v1/groups", json={
        "name": "Replay Group",
        "member_emails": ["bob.replay@example.com"]
    }, headers=h_alice).json()
    group_id = grp["id"]
    alice_id = next(m["user_id"] for m in grp["members"] if m["user"]["email"] == "alice.replay@example.com")
    cats = client.get("/api/v1/categories", headers=h_alice).json()

    # Alice pays $100, Bob owes $50
    client.post(f"/api/v1/groups/{group_id}/expenses", json={
        "category_id": cats[0]["id"],
        "amount": 100.00,
        "description": "Lunch",
        "split_type": "EQUAL"
    }, headers=h_alice)

    settle_idem_key = str(uuid.uuid4())
    headers_with_idem = {**h_bob, "X-Idempotency-Key": settle_idem_key}

    # 1. Bob executes settlement
    s1 = client.post(f"/api/v1/groups/{group_id}/settle", json={
        "payee_id": alice_id,
        "amount": 50.00,
        "notes": "Settling via UPI"
    }, headers=headers_with_idem)
    assert s1.status_code == 201
    settlement_id = s1.json()["id"]

    # 2. Duplicate retry with same key
    s2 = client.post(f"/api/v1/groups/{group_id}/settle", json={
        "payee_id": alice_id,
        "amount": 50.00,
        "notes": "Settling via UPI"
    }, headers=headers_with_idem)
    assert s2.status_code == 201
    assert s2.json()["id"] == settlement_id

    # 3. Verify exactly 1 settlement in group history
    all_settlements = client.get(f"/api/v1/groups/{group_id}/settlements", headers=h_bob).json()
    assert len(all_settlements) == 1

