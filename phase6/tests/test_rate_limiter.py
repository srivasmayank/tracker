import time
from fastapi.testclient import TestClient
from app.core.rate_limiter import default_rate_limit_storage, InMemorySlidingWindowStorage


def test_rate_limiter_emits_headers_and_decrements_remaining(client: TestClient):
    """
    Verifies that requests within quota receive:
    - X-RateLimit-Limit
    - X-RateLimit-Remaining (decrementing)
    - X-RateLimit-Reset (epoch timestamp)
    """
    default_rate_limit_storage.clear()

    # Register user
    reg_res = client.post("/api/v1/auth/register", json={
        "email": "ratelimit1@example.com",
        "full_name": "Rate User",
        "password": "Password123!",
        "currency": "USD"
    }, headers={"X-Forwarded-For": "192.168.1.100"})
    assert reg_res.status_code == 201

    assert "x-ratelimit-limit" in reg_res.headers
    assert "x-ratelimit-remaining" in reg_res.headers
    assert "x-ratelimit-reset" in reg_res.headers
    assert reg_res.headers["x-ratelimit-limit"] == "5"
    assert int(reg_res.headers["x-ratelimit-remaining"]) == 4


def test_auth_login_brute_force_blocked_with_429(client: TestClient):
    """
    Simulates a brute-force credential stuffing attack against /auth/login.
    Guarantees:
    - First 5 attempts processed.
    - 6th attempt blocked with HTTP 429 Too Many Requests and Retry-After header.
    """
    default_rate_limit_storage.clear()
    ip_headers = {"X-Forwarded-For": "10.0.0.50"}

    # Attempt 5 incorrect logins
    for _ in range(5):
        res = client.post("/api/v1/auth/login", json={
            "email": "victim@example.com",
            "password": "WrongPasswordAttempt"
        }, headers=ip_headers)
        assert res.status_code == 401

    # 6th attempt should be blocked by Rate Limiter before touching DB/bcrypt
    res_blocked = client.post("/api/v1/auth/login", json={
        "email": "victim@example.com",
        "password": "WrongPasswordAttempt"
    }, headers=ip_headers)

    assert res_blocked.status_code == 429
    assert "retry-after" in res_blocked.headers
    assert int(res_blocked.headers["retry-after"]) > 0
    assert res_blocked.headers["x-ratelimit-remaining"] == "0"
    assert "Rate limit exceeded" in res_blocked.json()["detail"]


def test_rate_limiter_ip_isolation(client: TestClient):
    """
    Verifies that IP '1.1.1.1' exceeding limit does NOT affect a separate IP '2.2.2.2'.
    """
    default_rate_limit_storage.clear()
    attacker_headers = {"X-Forwarded-For": "1.1.1.1"}
    legitimate_headers = {"X-Forwarded-For": "2.2.2.2"}

    # Exhaust quota for IP 1.1.1.1
    for _ in range(5):
        client.post("/api/v1/auth/login", json={"email": "a@test.com", "password": "123"}, headers=attacker_headers)

    # 1.1.1.1 is throttled
    blocked = client.post("/api/v1/auth/login", json={"email": "a@test.com", "password": "123"}, headers=attacker_headers)
    assert blocked.status_code == 429

    # 2.2.2.2 must be allowed through normally
    allowed = client.post("/api/v1/auth/login", json={"email": "a@test.com", "password": "123"}, headers=legitimate_headers)
    assert allowed.status_code == 401  # Normal credential failure, NOT 429 rate limit!
    assert int(allowed.headers["x-ratelimit-remaining"]) == 4


def test_in_memory_sliding_window_storage_logic():
    """
    Direct unit test of the sliding window mathematical algorithm.
    """
    storage = InMemorySlidingWindowStorage()
    key = "unit_test_key"
    limit = 3
    window = 2  # 2 seconds

    # 1. First 3 requests allowed
    ok1, rem1, _, _ = storage.record_and_check(key, limit, window)
    ok2, rem2, _, _ = storage.record_and_check(key, limit, window)
    ok3, rem3, _, _ = storage.record_and_check(key, limit, window)
    assert ok1 and ok2 and ok3
    assert rem1 == 2 and rem2 == 1 and rem3 == 0

    # 2. 4th request rejected
    ok4, rem4, _, retry_after = storage.record_and_check(key, limit, window)
    assert not ok4
    assert rem4 == 0
    assert retry_after >= 1

    # 3. Sleep beyond window and verify quota replenishment
    time.sleep(2.1)
    ok5, rem5, _, _ = storage.record_and_check(key, limit, window)
    assert ok5
    assert rem5 == 2
