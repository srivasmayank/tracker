# Enterprise Expense Tracker & Splitwise Engine

An enterprise-grade expense management and shared debt settlement platform built with **FastAPI (Python)**, **MySQL 8.0 (InnoDB)**, and **React**.

---

## Architecture & Engineering Highlights

* **Architecture Pattern:** Clean Layered Architecture (Routers -> Services -> Repositories -> Models).
* **Strategy Pattern for Splitting:** Equal, Exact, Percentage, and Proportional Shares split engines adhering to Open/Closed Principle (OCP).
* **Greedy Graph Debt Simplification:** Bipartite matching algorithm utilizing Min-Max heaps to reduce $O(N^2)$ pairwise debts to at most $N-1$ optimal repayment transactions.
* **ACID Transactions:** Multi-record atomicity ensuring header and participant split rows commit or rollback together.
* **Modern React SPA:** JWT-based stateless authentication, dynamic category progress charts, Splitwise Groups view, member invitation, interactive debt simplification, and Settle-Up modal.

---

## Project Structure

```text
tracer/
├── docs/
│   ├── PHASE_1_DESIGN_AND_EXPLANATION.md   # Foundation & Personal CRUD Architecture
│   └── PHASE_2_DESIGN_AND_EXPLANATION.md   # Splitwise Engine, Strategy Pattern & Debt Simplification
├── backend/
│   ├── app/
│   │   ├── core/                           # Config, Security, DB, Dependencies
│   │   ├── models/                         # SQLAlchemy 2.0 Entities (User, Category, Expense, Group, GroupMember, GroupExpense, ExpenseSplit, Settlement)
│   │   ├── schemas/                        # Pydantic v2 DTOs (Group, GroupExpense, Settlement, Token, User, Category)
│   │   ├── repositories/                   # Data Access Layer (GroupRepo, GroupExpenseRepo, SettlementRepo, etc.)
│   │   ├── services/                       # Business Logic (SplitStrategyFactory, DebtSimplifier, GroupExpenseService, SettlementService)
│   │   ├── api/v1/                         # FastAPI Routers (auth, categories, expenses, groups)
│   │   └── main.py                         # Application Entrypoint & CORS
│   ├── tests/                              # Automated Pytest Suite (14/14 tests passing)
│   ├── requirements.txt
│   └── .env
└── frontend/
    ├── src/
    │   ├── api/                            # Axios client with JWT Interceptors
    │   ├── context/                        # AuthContext (Login / Register / State)
    │   ├── components/                     # Navbar, SpendingCharts, ExpenseList, ExpenseModal, GroupsView, GroupDetailView, GroupExpenseModal, SettleUpModal, AddMemberModal
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
