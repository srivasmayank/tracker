# Phase 3: Concurrency Control, Race Conditions & Financial Integrity (Python Backend Guide)

> **Welcome to Phase 3!**  
> In Phase 1 and 2, we built functional personal and group expense tracking. But in any real-world financial platform, **multiple requests arrive at the exact same millisecond**.
> In **Phase 3**, we implement enterprise-grade concurrency controls: Pessimistic Row Locking (`SELECT ... FOR UPDATE`), Optimistic Concurrency Control (OCC), and the IETF Idempotency Key standard.

---

## 1. What Changes Were Made From Phase 2 to Phase 3?

### A. New Files Added:
1. **Idempotency Data Model (`app/models/idempotency.py`):**
   - Defines the `IdempotencyRecord` table storing `idempotency_key`, `user_id`, `request_path`, `request_hash` (SHA-256 fingerprint), `status` (`STARTED`, `COMPLETED`), and cached `response_data`.
2. **Idempotency Repository (`app/repositories/idempotency_repository.py`):**
   - Data access for querying keys, reserving pending states atomically, and caching completed HTTP responses.
3. **Idempotency Service (`app/services/idempotency_service.py`):**
   - Implements the **Idempotency Barrier**:
     - Computes SHA-256 cryptographic hash of incoming JSON payloads to detect tampering.
     - Checks if a key was previously completed; if so, replays the cached 201 response immediately without re-running business logic!
     - Rejects concurrent requests that reuse the same key while the first one is still processing (`409 Conflict`).
     - Detects payload tampering if a client reuses a key but changes the amount (`422 Unprocessable Entity`).
4. **Automated Concurrency Tests (`tests/test_concurrency.py`):**
   - 4 mission-critical tests verifying idempotency replay, payload tampering rejection, prevention of over-settlements, and duplicate settlement replays.

### B. Existing Files Modified:
- `app/models/group.py`:
  - Added `version = Column(Integer, default=1, nullable=False)` to enable **Optimistic Concurrency Control (OCC)** on the group aggregate.
- `app/repositories/group_repository.py`:
  - Added `get_group_for_update(group_id)`: executes `query.with_for_update()` which emits `SELECT ... FOR UPDATE` in MySQL InnoDB.
  - Added `increment_version_occ(group)`: bumps the version counter on every state mutation.
- `app/services/group_expense_service.py`:
  - Injected `IdempotencyService`.
  - Added 3-layer concurrency defense: Idempotency Gate $\rightarrow$ Pessimistic Lock on Group $\rightarrow$ OCC Version Increment.
- `app/services/settlement_service.py`:
  - Injected `IdempotencyService`.
  - Locked the group row with `SELECT ... FOR UPDATE` before inspecting member balances.
  - Added real-time invariant: verifies debtor does not overpay, even if two settlements are submitted concurrently.

---

## 2. The Problems We Solved (Why These Changes Were Necessary)

### Problem 1: The "Double-Click" Network Retry Bug
**Scenario:** A user is on a slow 3G mobile connection. They click "Confirm Settlement (\$50.00)". The phone's network pauses for 2 seconds. Thinking nothing happened, the user clicks again.
- **Without Idempotency:** The server processes two separate POST requests, inserts two \$50 settlement rows, and debits the user \$100.
- **With Idempotency (Our Solution):**
  1. The client sends a unique header: `X-Idempotency-Key: 7b8f9e...` (a UUID).
  2. The server records the key in the database with status `STARTED`.
  3. When the second duplicate request arrives, the server sees the key is already `STARTED` or `COMPLETED`.
  4. Instead of executing a second payment, it returns the **exact cached response** of the first payment!
  5. **Result:** Only 1 charge occurs in the database, zero double-billing.

### Problem 2: Payload Tampering Detection
What if an attacker catches an idempotency key and tries to reuse it with a different amount?
- In `app/services/idempotency_service.py`, we compute:
  $$\text{request\_hash} = \text{SHA256}(\text{JSON(payload)})$$
- If the incoming payload does not match the stored hash, the server immediately rejects with:
  `HTTP 422: "Idempotency key was previously submitted with a different request payload."`

### Problem 3: The "Over-Settlement" Race Condition
**Scenario:** Bob owes Alice \$50. Bob sends two requests in parallel:
- Request 1: Pay Alice \$50
- Request 2: Pay Alice \$50
If both requests read Bob's balance at the same time:
1. Thread A reads: "Bob owes \$50 $\rightarrow$ OK to pay \$50."
2. Thread B reads: "Bob owes \$50 $\rightarrow$ OK to pay \$50."
3. Both commit! Bob has now paid \$100 for a \$50 debt.

#### The Solution: Pessimistic Row-Level Locking (`SELECT ... FOR UPDATE`)
In `app/repositories/group_repository.py`:
```python
def get_group_for_update(self, group_id: int) -> Optional[Group]:
    return self.db.query(Group).filter(Group.id == group_id).with_for_update().first()
```
- In MySQL InnoDB, `with_for_update()` places an **exclusive write lock** on the Group row.
- When Request 1 arrives, it locks the Group.
- When Request 2 arrives 1 millisecond later, MySQL pauses Request 2 until Request 1 commits!
- When Request 1 commits, Bob's debt becomes \$0.
- When Request 2 unpauses, it re-checks Bob's debt, sees he owes \$0, and safely rejects with:
  `HTTP 400: "You do not owe any money in this group."`

---

## 3. Benefits & Covered Gaps

| Financial Risk | Phase 2 Splitwise | Phase 3 Concurrency Engine |
| :--- | :--- | :--- |
| **Double-Click Submissions** | Creates duplicate records | Handled idempotently; returns cached response |
| **Network Timeouts & Retries** | Multiple charges | Zero duplicate charges |
| **Payload Tampering** | Unchecked | Rejected with SHA-256 hash validation |
| **Concurrent Over-Settlements** | Possible race condition | Blocked via `SELECT ... FOR UPDATE` serializability |
| **Lost Updates in Write Clashes** | Unchecked | Detected via Optimistic Concurrency Control (OCC) |

---

## 4. What Gaps Still Remained for Phase 4?

While financial transactions are now completely race-condition-proof, our API is still exposed to **security & volumetric abuse**:
1. **Brute-Force Credential Stuffing:** An attacker can write a script trying 1,000 passwords per second against `/api/v1/auth/login`.
2. **Denial of Service (DoS):** A user can send 500 heavy group balance recalculations per second, pinning the database CPU at 100%.

These abuse vectors are addressed in **Phase 4** using Multi-Tier Sliding Window Log Rate Limiting!

---

## 5. How to Run and Test Phase 3 Standalone

```powershell
# 1. Navigate to phase3 directory
cd phase3

# 2. Run all Phase 3 tests (18 tests)
$env:PYTHONPATH="c:\Users\PC\Downloads\tracer\phase3"
..\venv\Scripts\pytest tests -v

# 3. Start the server
..\venv\Scripts\uvicorn app.main:app --reload --port 8000
```
