# Phase 5: High-Level Design (HLD) & Low-Level Design (LLD)
## Background Processing, Asynchronous Task Queues & Scheduled Jobs

In **Phase 1**, we built the core single-user ledger.
In **Phase 2**, we implemented the Splitwise multi-user engine with debt simplification.
In **Phase 3**, we enforced ACID financial reliability with idempotency keys and row locks.
In **Phase 4**, we protected our APIs with sliding window rate limiting and security gates.

Now in **Phase 5**, we complete the enterprise architecture by solving the **Synchronous Request Bottleneck** through **Asynchronous Background Processing, Recurring Expense Automation, and Out-of-Band Financial Exports**.

---

## 1. High-Level Design (HLD)

### 1.1 The Synchronous Request Bottleneck

In a traditional web application, HTTP request-response cycles are strictly synchronous: the client sends a request, the server thread handles it, and the client waits until completion.

```mermaid
sequenceDiagram
    autonumber
    actor Client as Client Browser
    participant Gateway as Reverse Proxy / Nginx
    participant Worker as Web Server Worker (FastAPI)
    participant DB as MySQL Database

    Note over Client,DB: Problem: Synchronous Long-Running Request (e.g. 5-Year CSV/PDF Statement)
    Client->>Gateway: POST /api/v1/exports/statement (Download CSV)
    Gateway->>Worker: Forward Request
    Note over Worker,DB: Worker thread queries 50,000 rows, formats CSV, computes running balances... (Takes 8 seconds!)
    Note over Gateway: Gateway Timeout (504) after 5 seconds!
    Gateway-->>Client: 504 Gateway Timeout Error
    Note over Worker: Worker wasted 8s of CPU & connection pool holding a broken connection!
```

**The Core Rule of Production Web Architecture:**
> **HTTP requests must complete in $< 100\text{ms}$.** 
> Any task that takes longer—such as generating analytical exports, sending notification emails, or processing recurring subscription batches—must be offloaded out-of-band to a **Background Worker**.

---

### 1.2 The Asynchronous Job Pattern (Producer-Consumer)

Instead of making the client wait for a long task, we implement the **Asynchronous Polling & Job Pattern**:

```mermaid
sequenceDiagram
    autonumber
    actor Client as React Client
    participant API as FastAPI Producer
    participant Queue as Background Task Queue / Broker
    participant Worker as Async Worker (Consumer)
    participant DB as MySQL Database

    Client->>API: POST /api/v1/exports (Start CSV Export)
    API->>DB: Create Job (id="job-123", status="PENDING")
    API->>Queue: Enqueue task(job_id="job-123")
    API-->>Client: 202 Accepted {"job_id": "job-123", "status": "PENDING"} (Response time: 15ms!)

    par Async Execution
        Queue->>Worker: Dequeue task
        Worker->>DB: Update status="PROCESSING"
        Worker->>DB: Query expenses, format CSV, write to storage
        Worker->>DB: Update status="COMPLETED", result_path="/exports/statement-123.csv"
    and Client Polling
        Client->>API: GET /api/v1/exports/job-123
        API-->>Client: 200 OK {"status": "PROCESSING"}
        Note over Client: Wait 1 second...
        Client->>API: GET /api/v1/exports/job-123
        API-->>Client: 200 OK {"status": "COMPLETED", "download_url": "/api/v1/exports/job-123/download"}
        Client->>API: GET /api/v1/exports/job-123/download
        API-->>Client: 200 OK (File Stream: expenses_statement.csv)
    end
```

---

### 1.3 The Recurring Expenses Engine (Automated Subscriptions)

Many personal expenses repeat on a fixed cadence:
* Monthly rent, Netflix subscription, Gym membership, Weekly groceries, Utility bills.

Instead of requiring users to manually re-enter these transactions, we implement an **Automated Recurring Subscriptions Engine**:
1. Users define a `RecurringExpense` rule:
   * `amount`, `category_id`, `description`, `frequency` (`DAILY`, `WEEKLY`, `MONTHLY`, `YEARLY`), `next_due_date`, `is_active`.
2. A scheduled cron / background worker executes periodically (e.g. daily at midnight or triggered via maintenance API):
   * Queries all active recurring rules where `next_due_date <= today`.
   * **Atomic Transaction per Rule:** For each due subscription, it inserts a concrete `expenses` transaction and advances `next_due_date` to the subsequent cycle (e.g. $+ 1 \text{ month}$).
   * **Failure Isolation:** If subscription #3 fails, it rolls back individually without aborting subscriptions #1 and #2.

---

## 2. Low-Level Design (LLD)

### 2.1 Entity Additions & Schema Updates

```mermaid
erDiagram
    USERS ||--o{ RECURRING_EXPENSES : "owns"
    CATEGORIES ||--o{ RECURRING_EXPENSES : "categorizes"
    USERS ||--o{ EXPORT_JOBS : "requests"

    RECURRING_EXPENSES {
        int id PK
        int user_id FK "Indexed"
        int category_id FK
        decimal amount "DECIMAL(12, 2)"
        string description
        string frequency "DAILY, WEEKLY, MONTHLY, YEARLY"
        date start_date
        date next_due_date "Indexed for worker query"
        date end_date "Nullable"
        string payment_method
        boolean is_active "Default True"
        datetime created_at
    }

    EXPORT_JOBS {
        int id PK
        string job_id UK "UUIDv4, indexed"
        int user_id FK "Indexed"
        string format "CSV, JSON"
        string status "PENDING, PROCESSING, COMPLETED, FAILED"
        string file_path "Local or S3 path"
        int total_records "Row count exported"
        string error_message "Nullable"
        datetime created_at
        datetime completed_at
    }
```

---

### 2.2 Component Architecture & The Strategy Pattern for Exports

To ensure the export system can scale to multiple file formats (CSV, PDF, Excel) without modifying the service pipeline, we use the **Strategy Pattern**:

```mermaid
classDiagram
    class ExportFormatter {
        <<interface>>
        +format_expenses(expenses: List~Expense~) Tuple~bytes, str~
    }

    class CSVExportFormatter {
        +format_expenses(expenses: List~Expense~) Tuple~bytes, str~
    }

    class JSONExportFormatter {
        +format_expenses(expenses: List~Expense~) Tuple~bytes, str~
    }

    class ExportService {
        -export_repo: ExportJobRepository
        -expense_repo: ExpenseRepository
        -formatter_factory: ExportFormatterFactory
        +create_export_job(user_id: int, format: str) ExportJob
        +process_export_task(job_id: str) None
        +get_job_status(job_id: str, user_id: int) ExportJob
    }

    class RecurringExpenseService {
        -recurring_repo: RecurringExpenseRepository
        -expense_repo: ExpenseRepository
        +create_recurring(user_id: int, data: RecurringCreate) RecurringExpense
        +process_due_subscriptions(target_date: date) BatchResult
    }

    ExportFormatter <|.. CSVExportFormatter
    ExportFormatter <|.. JSONExportFormatter
    ExportService --> ExportFormatter : uses
```

---

## 3. SOLID Principles in Phase 5

1. **Single Responsibility Principle (SRP):**
   * `CSVExportFormatter` is solely responsible for serializing domain expenses into RFC 4180 compliant CSV bytes.
   * `ExportService` coordinates job state transitions (`PENDING` $\to$ `PROCESSING` $\to$ `COMPLETED`).
   * `RecurringExpenseService` calculates date advances and coordinates subscription generation.
2. **Open/Closed Principle (OCP):**
   * Adding support for PDF or Excel statements requires writing one new `PDFExportFormatter` subclass implementing `ExportFormatter`. The `ExportService` remains completely untouched.
3. **Liskov Substitution Principle (LSP):**
   * Any `ExportFormatter` implementation returns `(file_bytes, mime_type)` conforming strictly to the interface contract.
4. **Interface Segregation Principle (ISP):**
   * DTOs for recurring expense creation (`RecurringExpenseCreate`) are segregated from generated batch execution reports (`BatchProcessResult`).
5. **Dependency Inversion Principle (DIP):**
   * Background task handlers receive repositories and database sessions through dependency injection rather than tight static coupling.

---

## 4. ACID Invariants in Asynchronous Batch Processing

When processing hundreds of recurring subscription rules at midnight:
* **The Granular Transaction Boundary Rule:**
  Never run an entire batch of hundreds of subscriptions inside a single giant database transaction. If rule #87 fails (e.g. deleted custom category or database constraint), a monolithic transaction would abort rules #1 through #86!
* **Our Solution (Per-Item Atomicity):**
  Each recurring item creates a real expense and advances `next_due_date` within its own atomic `db.commit()`. If an individual rule fails, its specific transaction rolls back (`db.rollback()`), logs the error, and the batch runner continues safely to the next subscription.
