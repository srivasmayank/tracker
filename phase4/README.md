# Phase 4: Multi-Tier Rate Limiting & API Security (Python Backend Guide)

> **Welcome to Phase 4!**  
> In Phase 1, 2, and 3, we built a mathematically sound, race-condition-proof financial engine.
> In **Phase 4**, we harden our system against **malicious volumetric abuse**, **credential-stuffing brute-force attacks**, and **denial-of-service (DoS)** using the mathematical **Sliding Window Log Rate Limiting Algorithm** and standard IETF response headers.

---

## 1. What Changes Were Made From Phase 3 to Phase 4?

### A. New Files Added:
1. **Rate Limiting Engine (`app/core/rate_limiter.py`):**
   - Implements `SlidingWindowLogRateLimiter`: an in-memory, thread-safe sliding window log algorithm using `collections.deque` guarded by `threading.Lock`.
   - Defines `RateLimitRule(max_requests, window_seconds)`: defines rate limit tiers for endpoints.
   - Provides `rate_limit()` dependency for FastAPI route guards.
   - Emits standardized IETF rate limit headers on every response:
     - `X-RateLimit-Limit`: Maximum requests allowed in the current window.
     - `X-RateLimit-Remaining`: Number of requests the client can still make.
     - `X-RateLimit-Reset`: UTC epoch timestamp when the window completely clears.
     - `Retry-After`: Seconds to wait before retrying (when throttled with `429 Too Many Requests`).
2. **Automated Security Tests (`tests/test_rate_limiter.py`):**
   - 4 tests verifying:
     - Correct emission of `X-RateLimit-*` headers and decrementing counters.
     - Brute-force protection on `/auth/login` blocking the 6th attempt with `HTTP 429`.
     - IP isolation (ensuring throttling IP A does not affect legitimate user IP B).
     - Mathematical eviction of expired timestamps in the sliding window.

### B. Existing Files Modified:
- `app/main.py`:
  - Added `rate_limit_header_middleware`: an ASGI middleware ensuring that `X-RateLimit-*` headers are attached to the HTTP response even if the endpoint encounters an exception or validation error.
- `app/api/v1/auth.py`:
  - Protected the `/auth/login` endpoint with strict rule: `5 requests per 60 seconds`.
- `app/api/v1/groups.py`:
  - Protected state-mutating endpoints (`POST /groups`, `POST /groups/{id}/expenses`, `POST /groups/{id}/settle`) with tiered limits (30 req/min).
- `tests/conftest.py`:
  - Added `reset_rate_limits` autouse fixture to reset rate-limit deques before and after each test.

---

## 2. Why Were These Changes Made? (Deep Pedagogical Dive)

### A. The Flaw with "Fixed Window" Rate Limiters
Many naive tutorials implement rate limiting with a simple counter reset every minute:
```python
# NAIVE FLAWED APPROACH:
if current_minute != stored_minute:
    counter = 0
counter += 1
if counter > 10:
    reject()
```
#### Why Does This Fail? (The 2x Boundary Burst Vulnerability)
Suppose the limit is **10 requests per minute**:
- At `00:59`, an attacker sends **10 requests**. (Allowed).
- At `01:00`, the clock rolls over and the counter resets to 0.
- At `01:01`, the attacker sends another **10 requests**. (Allowed).
- **The Result:** The attacker sent **20 requests in 2 seconds**! The server CPU spikes and database connections are exhausted.

---

### B. The Solution: Mathematical Sliding Window Log
Instead of fixed clock buckets, our `SlidingWindowLogRateLimiter` tracks the exact timestamp ($t_i$) of every incoming request:
1. When a request arrives at timestamp $T_{now}$ from client IP $X$:
2. Calculate the window boundary: $T_{cutoff} = T_{now} - \text{window\_seconds}$.
3. **Eviction Step:** Discard all timestamps in the client's log that occurred before $T_{cutoff}$.
4. **Evaluation Step:** Count the remaining timestamps in the deque:
   - If $\text{count} < \text{max\_requests}$: Record $T_{now}$ into the deque and allow the request.
   - If $\text{count} \ge \text{max\_requests}$: Reject with `HTTP 429 Too Many Requests`.
5. Calculate `Retry-After`:
   $$\text{Retry-After} = \lceil \text{oldest\_timestamp} + \text{window\_seconds} - T_{now} \rceil$$

---

### C. Client IP Extraction & Reverse Proxy Defense
In production, your FastAPI server sits behind a reverse proxy (Nginx, AWS CloudFront, Cloudflare).
If you naively check `request.client.host`, every request appears to come from `127.0.0.1`! One user getting throttled would accidentally block everyone in the entire world!

In `app/core/rate_limiter.py`:
```python
def get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "127.0.0.1"
```
We inspect the `X-Forwarded-For` header to identify the real originating client IP.

---

## 3. Benefits & Covered Gaps

| Security Vector | Phase 3 Concurrency Engine | Phase 4 Rate Limiting & Security |
| :--- | :--- | :--- |
| **Password Brute-Force** | Unrestricted login attempts | Hard-blocked after 5 failed attempts with 429 |
| **Denial of Service (DoS)** | Database pool exhaustion | Throttled with sliding window eviction |
| **Traffic Spikes at Minute Rollover** | Vulnerable to 2x boundary bursts | Completely smoothed out across rolling window |
| **Client Visibility** | None | IETF Headers (`X-RateLimit-*`, `Retry-After`) |

---

## 4. What Gaps Still Remained for Phase 5?

Even with race-condition safety and rate limiting, our architecture is still **strictly synchronous**:
1. **Gateway Timeouts on Large Exports (HTTP 504):**  
   If an active user requests a 3-year financial statement with 50,000 transactions formatted into CSV or PDF, compiling the document takes 5–10 seconds. In standard HTTP cycles, reverse proxies timeout after 15–30 seconds.
2. **No Recurring Expense Automation:**  
   Users must manually create recurring bills (Netflix, Rent, Internet) every single month.

These background and scheduling needs are solved in **Phase 5** using Asynchronous Background Workers and the `202 Accepted` polling pattern!

---

## 5. How to Run and Test Phase 4 Standalone

```powershell
# 1. Navigate to phase4 directory
cd phase4

# 2. Run all Phase 4 tests (22 tests)
$env:PYTHONPATH="c:\Users\PC\Downloads\tracer\phase4"
..\venv\Scripts\pytest tests -v

# 3. Start the server
..\venv\Scripts\uvicorn app.main:app --reload --port 8000
```
