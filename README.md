# Enterprise Expense Tracker & Splitwise Engine

An enterprise-grade expense management, shared debt settlement, and asynchronous financial processing platform built with **FastAPI (Python)**, **MySQL 8.0 (InnoDB)**, and **React**.

---

## Architecture & Engineering Highlights

* **Architecture Pattern:** Clean Layered Architecture (Routers -> Services -> Repositories -> Models).
* **Strategy Pattern for Splitting:** Equal, Exact, Percentage, and Proportional Shares split engines adhering to Open/Closed Principle (OCP).
* **Greedy Graph Debt Simplification:** Bipartite matching algorithm utilizing Min-Max heaps to reduce $O(N^2)$ pairwise debts to at most $N-1$ optimal repayment transactions.
* **Idempotency Gate (IETF Standard):** Transparent `X-Idempotency-Key` interceptor with SHA-256 request fingerprinting, atomic `PROCESSING` state locks, and response replay preventing duplicate charges during network retries.
* **Pessimistic Row-Level Locking:** `SELECT ... FOR UPDATE` row locks in MySQL InnoDB guaranteeing transaction serializability and preventing concurrent over-settlements.
* **Optimistic Concurrency Control (OCC):** Aggregate versioning counter checks preventing lost updates under parallel writes.
* **Multi-Tier Rate Limiting (Sliding Window Log):** Thread-safe mathematical sliding window log eliminating boundary traffic spikes, protecting `/auth/login` from brute-force attacks and throttling heavy analytical endpoints. Emits standard IETF headers (`X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`, `Retry-After`).
* **Asynchronous Statement Export (202 Accepted Pattern):** Decoupled heavy statement query and byte generation from the HTTP request cycle using background worker tasks and state machines (`PENDING` -> `PROCESSING` -> `COMPLETED`/`FAILED`). Eliminates 504 Gateway Timeouts on multi-megabyte exports.
* **Strategy Pattern for Export Serialization:** Format-agnostic serializer abstraction (`CSVExportFormatter` with Excel UTF-8 BOM, `JSONExportFormatter`) extensible without modifying business logic.
* **Recurring Subscriptions Engine:** Automated cron/batch processor for subscriptions (Netflix, Rent, SIPs) with safe date-advancement logic (month-end clamping e.g. Jan 31 -> Feb 28, leap year safety) and per-item granular transaction isolation.
* **ACID Transactions:** Granular multi-record atomicity ensuring header, participant split rows, and batch items commit or rollback cleanly without partial state corruptions.
* **Modern React SPA:** JWT-based stateless authentication, dynamic category progress charts, Splitwise Groups view, member invitation, interactive debt simplification, Settle-Up modal, recurring subscriptions management, and out-of-band export download manager.

---

## Project Structure

```text
tracer/
├── docs/
│   ├── PHASE_1_DESIGN_AND_EXPLANATION.md   # Foundation & Personal CRUD Architecture
│   ├── PHASE_2_DESIGN_AND_EXPLANATION.md   # Splitwise Engine, Strategy Pattern & Debt Simplification
│   ├── PHASE_3_DESIGN_AND_EXPLANATION.md   # Race Conditions, Locking, Idempotency & ACID
│   ├── PHASE_4_DESIGN_AND_EXPLANATION.md   # Multi-Tier Rate Limiting & API Security
│   └── PHASE_5_DESIGN_AND_EXPLANATION.md   # Background Processing, Recurring Engine & Async Exports
├── backend/
│   ├── app/
│   │   ├── core/                           # Config, Security, DB, Dependencies, RateLimiter
│   │   ├── models/                         # SQLAlchemy 2.0 Entities (User, Expense, Group, RecurringExpense, ExportJob, etc.)
│   │   ├── schemas/                        # Pydantic v2 DTOs (Request/Response validators)
│   │   ├── repositories/                   # Data Access Layer (with FOR UPDATE, IdempotencyRepo, ExportJobRepo, RecurringRepo)
│   │   ├── services/                       # Business Logic (RecurringExpenseService, ExportService, ExportFormatters, DebtSimplifier)
│   │   ├── api/v1/                         # FastAPI Routers (auth, categories, expenses, groups, recurring, exports)
│   │   └── main.py                         # Application Entrypoint & CORS & Rate Limit Middleware
│   ├── tests/                              # Automated Pytest Suite (26/26 tests passing)
│   ├── requirements.txt
│   └── .env
└── frontend/
    ├── src/
    │   ├── api/                            # Axios client with JWT, X-Idempotency-Key & 429 handler
    │   ├── context/                        # AuthContext (Login / Register / State)
    │   ├── components/                     # Navbar, SpendingCharts, ExpenseList, ExpenseModal, GroupsView, GroupDetailView, GroupExpenseModal, SettleUpModal, AddMemberModal, RecurringView, ExportModal
    │   ├── pages/                          # AuthPage, Dashboard
    │   └── App.jsx
    ├── package.json
    └── vite.config.js
```

---

## Quickstart Guide

### 1. Run the Backend

```powershell
# Navigate to backend:
cd backend

# Start the FastAPI server:
..\venv\Scripts\uvicorn app.main:app --reload --port 8000
```

* **Interactive API Documentation (Swagger):** [http://localhost:8000/api/v1/docs](http://localhost:8000/api/v1/docs)
* **ReDoc Specification:** [http://localhost:8000/api/v1/redoc](http://localhost:8000/api/v1/redoc)

### 2. Run the Frontend

```powershell
# In a new terminal:
cd frontend
npm run dev
```

* **React Application:** [http://localhost:5173](http://localhost:5173)

### 3. Run Automated Tests

```powershell
$env:PYTHONPATH="c:\Users\PC\Downloads\tracer\backend"
.\venv\Scripts\pytest backend\tests -v
```
*(All 26 automated unit & integration tests pass with 100% green coverage)*
