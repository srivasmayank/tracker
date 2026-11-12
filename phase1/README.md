# Phase 1: Foundation & Personal Expense CRUD (Python Backend Guide)

> **Welcome to Phase 1!**  
> This guide is written specifically for developers who have never built a Python backend before. It explains everything from zero—how Python web servers work, what each folder does, line-by-line architectural decisions, and why we designed the system using industry-standard enterprise patterns.

---

## 1. What is a Python Web Backend? (The Fundamentals)

In the web development world:
- The **Frontend** (React) runs in the user's browser. It is responsible for buttons, forms, and colors.
- The **Backend** (Python + FastAPI) runs on a server. It is responsible for security, business logic, storing data safely in a database, and answering HTTP requests.

### How Does FastAPI Work?
When a user clicks "Add Expense" in React, the browser sends an **HTTP POST request** over the network:
```text
POST http://localhost:8000/api/v1/expenses
Headers: Authorization: Bearer <jwt-token>
Body: {"amount": 50.00, "description": "Groceries", "category_id": 1}
```

1. **Uvicorn (The Server Engine):**  
   Uvicorn is a lightning-fast **ASGI (Asynchronous Server Gateway Interface)** web server for Python. It listens on network port `8000`, receives raw TCP bytes from the client, parses the HTTP protocol, and passes the request into FastAPI.
2. **FastAPI (The Framework):**  
   FastAPI inspects the URL path (`/api/v1/expenses`) and method (`POST`), verifies the user's login token, runs data validation using **Pydantic**, executes your Python functions, and returns a JSON response.
3. **SQLAlchemy (The ORM - Object Relational Mapper):**  
   Instead of writing messy raw SQL strings like `"INSERT INTO expenses VALUES (50.00, ...)"`, SQLAlchemy lets us work with normal Python classes:
   ```python
   new_expense = Expense(amount=50.00, description="Groceries")
   db.add(new_expense)
   db.commit()
   ```
   SQLAlchemy automatically translates this into the correct SQL dialect for MySQL or SQLite!

---

## 2. Directory Structure & Architecture

In Phase 1, we adopt the **Clean Layered Architecture** (Presentation $\rightarrow$ Service $\rightarrow$ Repository $\rightarrow$ Model):

```text
phase1/
├── app/
│   ├── api/v1/              # 1. PRESENTATION LAYER: HTTP routes & endpoints
│   │   ├── auth.py          # User register & login endpoints
│   │   ├── categories.py    # Expense categories (Food, Rent, Utilities)
│   │   ├── expenses.py      # Personal CRUD (Create, Read, Update, Delete)
│   │   └── router.py        # Central URL dispatcher
│   ├── core/                # 2. CORE INFRASTRUCTURE: Settings, DB & Security
│   │   ├── config.py        # Environment variables (.env reader)
│   │   ├── database.py      # SQLAlchemy Engine & SessionLocal factory
│   │   ├── dependencies.py  # Dependency Injection providers & Auth guard
│   │   └── security.py      # Bcrypt password hashing & JWT token creation
│   ├── models/              # 3. DATABASE MODELS: Table schemas
│   │   ├── category.py      # "categories" table
│   │   ├── expense.py       # "expenses" table
│   │   └── user.py          # "users" table
│   ├── repositories/        # 4. REPOSITORY LAYER: Raw database queries
│   │   ├── base.py          # Generic BaseRepository with reusable CRUD
│   │   ├── category_repository.py
│   │   ├── expense_repository.py
│   │   └── user_repository.py
│   ├── schemas/             # 5. SCHEMAS (DTOs): Request & response validation
│   │   ├── category.py
│   │   ├── expense.py
│   │   ├── token.py
│   │   └── user.py
│   ├── services/            # 6. SERVICE LAYER: Business rules & calculations
│   │   ├── auth_service.py
│   │   ├── category_service.py
│   │   └── expense_service.py
│   └── main.py              # Application entrypoint & CORS configuration
├── tests/                   # Automated pytest suite (9 tests)
│   ├── conftest.py          # Test database fixtures & auth helpers
│   ├── test_auth.py         # Registration & login tests
│   └── test_expenses.py     # Expense CRUD & analytics tests
├── .env.example             # Template for configuration settings
└── requirements.txt         # Pinned Python package dependencies
```

---

## 3. Why Did We Separate Code into Layers? (SOLID Principles)

Many beginners put everything (database queries, validation, math, and HTTP response) inside one giant function inside `main.py`. This is called a **"Fat Controller" anti-pattern** and quickly causes bugs.

Here is why we separate them:
1. **Single Responsibility Principle (SRP):**
   - The **Router** (`api/v1/expenses.py`) only receives the request and returns the response. It does not touch the database directly.
   - The **Service** (`services/expense_service.py`) calculates business rules (e.g. verifying that an expense does not exceed a limit, or computing category percentages).
   - The **Repository** (`repositories/expense_repository.py`) only executes database queries (`SELECT`, `INSERT`, `UPDATE`).
   - The **Model** (`models/expense.py`) only defines the database table structure.
2. **Open/Closed Principle (OCP) via BaseRepository:**
   - Look at `app/repositories/base.py`. It is a generic repository `BaseRepository[ModelType]`. It implements `get_by_id`, `list`, `create`, `update`, and `delete`.
   - When we created `ExpenseRepository`, we didn't rewrite `create()` or `delete()`. We simply inherited from `BaseRepository`, extending it only with specific queries like `get_spending_summary()`.
3. **Financial Precision Guarantee:**
   - Look at `app/models/expense.py`. Notice `amount = Column(Numeric(12, 2))`.
   - **Crucial Financial Lesson:** Never use `FLOAT` or `DOUBLE` for money! In computers, `0.1 + 0.2` in floating point equals `0.30000000000000004`. Over thousands of transactions, fractions of cents vanish. Using `Numeric(12, 2)` (Python `Decimal`) guarantees exact, penny-perfect arithmetic.

---

## 4. Key Files Explained (What Each Does)

### 1. `app/core/database.py` (The Database Bridge)
- Creates the SQLAlchemy `engine` that connects to the database.
- It includes a smart fallback: it tries connecting to MySQL 8.0; if MySQL is not running on your machine, it automatically falls back to local `expense_tracker.db` (SQLite). This means the project runs out of the box with zero external configuration!
- Provides `get_db()`: a FastAPI dependency that gives each HTTP request its own isolated database transaction and guarantees it is closed when the request finishes.

### 2. `app/core/security.py` (Password Hashing & JWT)
- Passwords are never stored in plain text. `hash_password()` uses **Bcrypt** with random salts, making reverse-lookup attacks impossible.
- `create_access_token()` creates an encrypted JSON Web Token (JWT) that expires after 24 hours. When the user logs in, they receive this token and pass it in the `Authorization: Bearer <token>` header for subsequent requests.

### 3. `app/core/dependencies.py` (Dependency Injection)
- Implements FastAPI's `Depends()` pattern.
- `get_current_user()` intercepts protected requests, extracts the JWT token, verifies its cryptographic signature, and loads the active user from the database. If invalid or expired, it automatically rejects the request with `HTTP 401 Unauthorized`.

---

## 5. What Was Built in Phase 1 vs What Gaps Remained

### What Phase 1 Covers:
- Complete user registration, login, and JWT session handling.
- Category management with 6 auto-seeded default categories (Food, Transport, Housing, Entertainment, Healthcare, Utilities).
- Full Personal Expense CRUD (Create, List with pagination, Filter by date/category, Edit, Delete).
- Financial analytics summary (`GET /expenses/summary`) calculating percentage breakdowns.
- Automated testing with 9 passing pytest test cases.

### What Gaps Remained for Future Phases:
1. **Single User Only (No Splitwise):** Users can only record their own private expenses. There is no concept of shared groups, inviting friends, or splitting bills.
2. **No Concurrency Protection:** If a user double-clicks "Submit" rapidly, two identical expenses are created in the database.
3. **No Rate Limiting:** A malicious attacker can send 10,000 login attempts per second to guess user passwords.
4. **Synchronous Only:** If a user wants to download a 5-year statement of 50,000 transactions, the HTTP request hangs for 10 seconds and can timeout.
5. **Single Currency Only:** Everything is assumed to be USD.

---

## 6. How to Run and Test Phase 1 Standalone

### 1. Start the Phase 1 Backend Server:
```powershell
cd phase1
..\venv\Scripts\uvicorn app.main:app --reload --port 8000
```
- Open Swagger Interactive Docs: [http://localhost:8000/api/v1/docs](http://localhost:8000/api/v1/docs)

### 2. Run the Phase 1 Test Suite:
```powershell
$env:PYTHONPATH="c:\Users\PC\Downloads\tracer\phase1"
..\venv\Scripts\pytest tests -v
```
You will see all 9 tests pass with green checks!
