from decimal import Decimal
from fastapi.testclient import TestClient


def create_user_and_login(client: TestClient, email: str, name: str) -> dict:
    """Helper to register and authenticate a user, returning auth headers."""
    client.post("/api/v1/auth/register", json={
        "email": email,
        "full_name": name,
        "password": "Password123!",
        "currency": "USD"
    })
    res = client.post("/api/v1/auth/login", json={
        "email": email,
        "password": "Password123!"
    })
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_create_group_and_invite_members(client: TestClient):
    alice_headers = create_user_and_login(client, "alice.group@example.com", "Alice Group")
    bob_headers = create_user_and_login(client, "bob.group@example.com", "Bob Group")

    # Alice creates a group and invites Bob
    res = client.post("/api/v1/groups", json={
        "name": "Trip to Paris",
        "description": "Vacation expenses",
        "member_emails": ["bob.group@example.com"]
    }, headers=alice_headers)
    assert res.status_code == 201
    group_data = res.json()
    assert group_data["name"] == "Trip to Paris"
    assert len(group_data["members"]) == 2

    # Bob should see the group in his list
    bob_groups = client.get("/api/v1/groups", headers=bob_headers).json()
    assert any(g["id"] == group_data["id"] for g in bob_groups)


def test_equal_split_penny_allocation(client: TestClient):
    h_a = create_user_and_login(client, "u1@split.com", "User One")
    h_b = create_user_and_login(client, "u2@split.com", "User Two")
    h_c = create_user_and_login(client, "u3@split.com", "User Three")

    # Create group with 3 members
    grp = client.post("/api/v1/groups", json={
        "name": "Roommates",
        "member_emails": ["u2@split.com", "u3@split.com"]
    }, headers=h_a).json()

    cats = client.get("/api/v1/categories", headers=h_a).json()
    cat_id = cats[0]["id"]

    # Split $100 among 3 people equally
    exp_res = client.post(f"/api/v1/groups/{grp['id']}/expenses", json={
        "category_id": cat_id,
        "amount": 100.00,
        "description": "Internet Bill",
        "split_type": "EQUAL"
    }, headers=h_a)
    assert exp_res.status_code == 201
    exp = exp_res.json()
    assert len(exp["splits"]) == 3

    # Check sum of splits equals exact total ($100.00)
    split_amounts = [Decimal(str(s["owed_amount"])) for s in exp["splits"]]
    assert sum(split_amounts) == Decimal("100.00")
    # One gets 33.34 and two get 33.33
    assert Decimal("33.34") in split_amounts
    assert Decimal("33.33") in split_amounts


def test_exact_split_validation(client: TestClient):
    h_a = create_user_and_login(client, "exact1@test.com", "Exact One")
    create_user_and_login(client, "exact2@test.com", "Exact Two")

    grp = client.post("/api/v1/groups", json={
        "name": "Exact Group",
        "member_emails": ["exact2@test.com"]
    }, headers=h_a).json()
    m_ids = [m["user_id"] for m in grp["members"]]
    cats = client.get("/api/v1/categories", headers=h_a).json()

    # Case 1: Sum != Total (100 total, but 60 + 30 = 90) -> Rejection
    fail_res = client.post(f"/api/v1/groups/{grp['id']}/expenses", json={
        "category_id": cats[0]["id"],
        "amount": 100.00,
        "description": "Dinner",
        "split_type": "EXACT",
        "splits": [
            {"user_id": m_ids[0], "owed_amount": 60.00},
            {"user_id": m_ids[1], "owed_amount": 30.00}
        ]
    }, headers=h_a)
    assert fail_res.status_code == 400

    # Case 2: Sum == Total (100 total, 70 + 30 = 100) -> Success
    success_res = client.post(f"/api/v1/groups/{grp['id']}/expenses", json={
        "category_id": cats[0]["id"],
        "amount": 100.00,
        "description": "Dinner",
        "split_type": "EXACT",
        "splits": [
            {"user_id": m_ids[0], "owed_amount": 70.00},
            {"user_id": m_ids[1], "owed_amount": 30.00}
        ]
    }, headers=h_a)
    assert success_res.status_code == 201


def test_percentage_split_validation(client: TestClient):
    h_a = create_user_and_login(client, "pct1@test.com", "Pct One")
    create_user_and_login(client, "pct2@test.com", "Pct Two")

    grp = client.post("/api/v1/groups", json={
        "name": "Pct Group",
        "member_emails": ["pct2@test.com"]
    }, headers=h_a).json()
    m_ids = [m["user_id"] for m in grp["members"]]
    cats = client.get("/api/v1/categories", headers=h_a).json()

    # Sum of percentages = 90% -> Rejection
    fail_res = client.post(f"/api/v1/groups/{grp['id']}/expenses", json={
        "category_id": cats[0]["id"],
        "amount": 200.00,
        "description": "Hotel",
        "split_type": "PERCENTAGE",
        "splits": [
            {"user_id": m_ids[0], "percentage": 50.00},
            {"user_id": m_ids[1], "percentage": 40.00}
        ]
    }, headers=h_a)
    assert fail_res.status_code == 400

    # Sum of percentages = 100% -> Success
    success_res = client.post(f"/api/v1/groups/{grp['id']}/expenses", json={
        "category_id": cats[0]["id"],
        "amount": 200.00,
        "description": "Hotel",
        "split_type": "PERCENTAGE",
        "splits": [
            {"user_id": m_ids[0], "percentage": 60.00},
            {"user_id": m_ids[1], "percentage": 40.00}
        ]
    }, headers=h_a)
    assert success_res.status_code == 201
    splits = success_res.json()["splits"]
    assert float(splits[0]["owed_amount"]) == 120.00
    assert float(splits[1]["owed_amount"]) == 80.00


def test_debt_simplification_and_settlement_workflow(client: TestClient):
    """
    Scenario:
    Alice, Bob, and Charlie in a group.
    1. Alice pays $90 for all 3 equally ($30 each).
       Net: Alice: +$60, Bob: -$30, Charlie: -$30.
    2. Bob pays $60 for Bob and Charlie ($30 each).
       Net:
         Alice: +$60
         Bob: -$30 + $60 (paid) - $30 (share) = $0
         Charlie: -$30 - $30 = -$60
    3. Simplification should produce: Charlie pays Alice $60.
    4. Charlie settles $60 to Alice.
    5. Net balances all become $0.00 and simplified debts become empty.
    """
    h_alice = create_user_and_login(client, "alice.debt@example.com", "Alice")
    h_bob = create_user_and_login(client, "bob.debt@example.com", "Bob")
    h_charlie = create_user_and_login(client, "charlie.debt@example.com", "Charlie")

    # Alice creates group with Bob and Charlie
    grp = client.post("/api/v1/groups", json={
        "name": "Trip Simplification",
        "member_emails": ["bob.debt@example.com", "charlie.debt@example.com"]
    }, headers=h_alice).json()
    group_id = grp["id"]

    user_ids = {m["user"]["email"]: m["user_id"] for m in grp["members"]}
    alice_id = user_ids["alice.debt@example.com"]
    bob_id = user_ids["bob.debt@example.com"]
    charlie_id = user_ids["charlie.debt@example.com"]

    cats = client.get("/api/v1/categories", headers=h_alice).json()
    cat_id = cats[0]["id"]

    # 1. Alice pays $90 equally among all 3
    client.post(f"/api/v1/groups/{group_id}/expenses", json={
        "category_id": cat_id,
        "amount": 90.00,
        "description": "Groceries",
        "split_type": "EQUAL"
    }, headers=h_alice)

    # 2. Bob pays $60 split equally between Bob and Charlie
    client.post(f"/api/v1/groups/{group_id}/expenses", json={
        "category_id": cat_id,
        "amount": 60.00,
        "description": "Fuel",
        "split_type": "EQUAL",
        "splits": [
            {"user_id": bob_id},
            {"user_id": charlie_id}
        ]
    }, headers=h_bob)

    # 3. Check group balances and simplified debts
    bal_res = client.get(f"/api/v1/groups/{group_id}/balances", headers=h_alice)
    assert bal_res.status_code == 200
    bal_data = bal_res.json()
    assert float(bal_data["total_spending"]) == 150.00

    member_map = {m["user_id"]: float(m["net_balance"]) for m in bal_data["members"]}
    assert member_map[alice_id] == 60.00
    assert member_map[bob_id] == 0.00
    assert member_map[charlie_id] == -60.00

    # Verify simplified debt: Exactly 1 transaction: Charlie -> Alice $60
    debts = bal_data["simplified_debts"]
    assert len(debts) == 1
    assert debts[0]["debtor_id"] == charlie_id
    assert debts[0]["creditor_id"] == alice_id
    assert float(debts[0]["amount"]) == 60.00

    # 4. Charlie settles up: pays Alice $60
    settle_res = client.post(f"/api/v1/groups/{group_id}/settle", json={
        "payee_id": alice_id,
        "amount": 60.00,
        "notes": "Paid via Venmo"
    }, headers=h_charlie)
    assert settle_res.status_code == 201

    # 5. Balances after settlement: all zero, simplified debts empty
    after_res = client.get(f"/api/v1/groups/{group_id}/balances", headers=h_alice).json()
    for m in after_res["members"]:
        assert float(m["net_balance"]) == 0.00
    assert len(after_res["simplified_debts"]) == 0

