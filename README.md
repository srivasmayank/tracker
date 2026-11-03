# Enterprise Expense Tracker & Splitwise Engine

An enterprise-grade expense management and shared debt settlement platform built with **FastAPI (Python)**, **MySQL 8.0 (InnoDB)**, and **React**.

---

## Architecture & Engineering Highlights

* **Architecture Pattern:** Clean Layered Architecture (Routers -> Services -> Repositories -> Models).
* **SOLID Principles:** Strict enforcement of SRP, OCP, LSP, ISP, and DIP via Python type hints and dependency injection.
* **ACID Guarantees:** Transactional integrity with MySQL InnoDB (Atomicity, Consistency, Isolation, Durability).
* **Decoupled Data Access:** Generic Repository pattern separating database operations from business invariants.
* **Modern React SPA:** JWT-based stateless authentication, dynamic category progress charts, paginated transactions, and instant CRUD.

---

## Project Structure

```text
tracer/
├── docs/
│   └── PHASE_1_DESIGN_AND_EXPLANATION.md   # Complete HLD & LLD Masterclass Guide
├── backend/
│   ├── app/
│   │   ├── core/                           # Config, Security, DB, Dependencies
│   │   ├── models/                         # SQLAlchemy 2.0 ORM Entities
│   │   ├── schemas/                        # Pydantic v2 DTOs & Validation
│   │   ├── repositories/                   # Data Access Layer (SOLID: DIP & SRP)
│   │   ├── services/                       # Business Logic Layer
│   │   ├── api/v1/                         # Presentation Layer (FastAPI Routers)
│   │   └── main.py                         # Application Entrypoint & CORS
│   ├── tests/                              # Automated Pytest Suite (100% Pass)
│   ├── requirements.txt
│   └── .env
└── frontend/
    ├── src/
    │   ├── api/                            # Axios client with JWT Interceptors
    │   ├── context/                        # AuthContext (Login / Register / State)
    │   ├── components/                     # Navbar, SpendingCharts, ExpenseList, Modal
    │   ├── pages/                          # AuthPage, Dashboard
    │   └── App.jsx
    ├── package.json
    └── vite.config.js
```

---

## Quickstart Guide

### 1. Run the Backend

```powershell
# In project root:
.\venv\Scripts\activate

# Navigate to backend:
cd backend

# Start the FastAPI server:
uvicorn app.main:app --reload --port 8000
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

