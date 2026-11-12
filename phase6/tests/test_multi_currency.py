from decimal import Decimal
from fastapi.testclient import TestClient

from app.services.fx_service import FallbackStaticFXAdapter, CachedFXProvider, FXService


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


def test_fx_provider_triangulation_and_caching():
    """Unit test for mathematical triangulation across currencies and cache hit."""
    adapter = FallbackStaticFXAdapter()
    cached = CachedFXProvider(adapter, ttl_seconds=60)
    fx = FXService(provider=cached)

    # 1 USD = 0.92 EUR => 1 EUR = (1 / 0.92) USD = ~1.086957 USD
    rate_eur_usd = fx.get_exchange_rate("EUR", "USD")
    assert rate_eur_usd > Decimal("1.08") and rate_eur_usd < Decimal("1.09")

    # Direct identity
    assert fx.get_exchange_rate("USD", "USD") == Decimal("1.000000")

    # Triangulate EUR -> INR
    # USD -> INR = 84.50, USD -> EUR = 0.92 => EUR -> INR = 84.50 / 0.92 = 91.847826
    rate_eur_inr = fx.get_exchange_rate("EUR", "INR")
    assert rate_eur_inr > Decimal("91.80") and rate_eur_inr < Decimal("91.90")

    # Convert 100 EUR to USD
    converted, rate = fx.convert(Decimal("100.00"), "EUR", "USD")
    assert converted == (Decimal("100.00") * rate).quantize(Decimal("0.01"))


def test_fx_api_endpoints(client: TestClient):
    """Verifies public /fx router endpoints for currencies, rates, and conversion."""
    # 1. Currencies list
    c_res = client.get("/api/v1/fx/currencies")
    assert c_res.status_code == 200
    currencies = c_res.json()["currencies"]
    assert "USD" in currencies
    assert "EUR" in currencies
    assert "INR" in currencies
    assert "GBP" in currencies

    # 2. Benchmark rates
    r_res = client.get("/api/v1/fx/rates?base=USD")
    assert r_res.status_code == 200
    rates = r_res.json()
    assert float(rates["USD"]) == 1.0
    assert float(rates["EUR"]) == 0.92

    # 3. Currency conversion endpoint
    conv_res = client.get("/api/v1/fx/convert?amount=100&from_currency=EUR&to_currency=USD")
    assert conv_res.status_code == 200
    data = conv_res.json()
    assert data["from_currency"] == "EUR"
    assert data["to_currency"] == "USD"
    assert float(data["converted_amount"]) > 100.0


def test_multi_currency_group_expense_and_debt_simplification(client: TestClient):
    """
    Critical multi-currency financial integration test:
    1. Create a group with base currency USD.
    2. Alice pays 100.00 EUR for Alice and Bob (EQUAL split).
    3. Verify rate snapshot is frozen on the group expense.
    4. Group balances verify Bob owes Alice in USD (base currency).
    5. Bob settles up with Alice paying in EUR.
    6. Bob's net balance returns to 0.00.
    """
    h_alice = create_user_and_login(client, "alice.fx@example.com", "Alice FX")
    h_bob = create_user_and_login(client, "bob.fx@example.com", "Bob FX")

    # 1. Create USD group
    grp = client.post("/api/v1/groups", json={
        "name": "Europe Trip",
        "description": "Multi-currency travel group",
        "currency": "USD",
        "member_emails": ["bob.fx@example.com"]
    }, headers=h_alice).json()
    group_id = grp["id"]
    assert grp["currency"] == "USD"

    alice_id = next(m["user_id"] for m in grp["members"] if m["user"]["email"] == "alice.fx@example.com")
    bob_id = next(m["user_id"] for m in grp["members"] if m["user"]["email"] == "bob.fx@example.com")

    cats = client.get("/api/v1/categories", headers=h_alice).json()
    cat_id = cats[0]["id"]

    # 2. Alice incurs expense in EUR (100.00 EUR)
    exp_res = client.post(f"/api/v1/groups/{group_id}/expenses", json={
        "category_id": cat_id,
        "amount": 100.00,
        "currency": "EUR",
        "description": "Louvre Museum Tickets",
        "split_type": "EQUAL"
    }, headers=h_alice)
    assert exp_res.status_code == 201
    exp_data = exp_res.json()

    assert exp_data["currency"] == "EUR"
    assert float(exp_data["exchange_rate"]) > 1.0  # EUR/USD rate is ~1.086957
    assert float(exp_data["base_amount"]) > 100.0  # ~ $108.70 USD

    # 3. Check group balances in Base Currency (USD)
    bal_res = client.get(f"/api/v1/groups/{group_id}/balances", headers=h_alice)
    assert bal_res.status_code == 200
    balances = bal_res.json()
    assert balances["currency"] == "USD"

    bob_bal = next(m for m in balances["members"] if m["user_id"] == bob_id)
    assert float(bob_bal["net_balance"]) < 0  # Bob is a debtor in USD

    # Simplified debts must recommend Bob pay Alice in USD
    assert len(balances["simplified_debts"]) == 1
    debt = balances["simplified_debts"][0]
    assert debt["debtor_id"] == bob_id
    assert debt["creditor_id"] == alice_id
    assert debt["currency"] == "USD"
    debt_in_usd = float(debt["amount"])
    assert debt_in_usd > 50.0  # 50 EUR converted to USD is ~$54.35

    # 4. Bob settles debt by paying in EUR (50.00 EUR)
    settle_res = client.post(f"/api/v1/groups/{group_id}/settle", json={
        "payee_id": alice_id,
        "amount": 50.00,
        "currency": "EUR",
        "notes": "Settling Louvre ticket in EUR"
    }, headers=h_bob)
    assert settle_res.status_code == 201
    settle_data = settle_res.json()
    assert settle_data["currency"] == "EUR"
    assert float(settle_data["base_amount"]) > 50.0

    # 5. Check balances after settlement - Bob's balance is resolved
    bal_after = client.get(f"/api/v1/groups/{group_id}/balances", headers=h_alice).json()
    bob_bal_after = next(m for m in bal_after["members"] if m["user_id"] == bob_id)
    # Remaining debt should be negligible (<= 1 cent due to rounding)
    assert abs(float(bob_bal_after["net_balance"])) < 0.05
