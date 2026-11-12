# Phase 6: Multi-Currency & Real-Time Foreign Exchange (FX) Engine (Python Backend Guide)

> **Welcome to Phase 6!**  
> In Phase 1 through 5, we built personal expenses, Splitwise groups, concurrency control, sliding-window rate limiting, and background workers.
> In **Phase 6**, we tackle cross-border financial engineering: **Multi-Currency Transactions**, the **Adapter Pattern for FX Providers**, **Currency Triangulation**, **Historical Rate Snapshot Freezing**, and **Base-Currency Normalized Debt Simplification**.

---

## 1. What Changes Were Made From Phase 5 to Phase 6?

### A. New Files Added:
1. **Foreign Exchange Service Layer (`app/services/fx_service.py`):**
   - Implements the **Adapter Pattern**:
     - `ExchangeRateProvider`: Abstract interface for exchange rate data providers.
     - `FallbackStaticFXAdapter`: Zero-network-dependency benchmark provider supporting triangulation across USD, EUR, GBP, INR, CAD, AUD, JPY, CHF, SGD, AED.
     - `CachedFXProvider`: In-memory TTL caching decorator preventing redundant computations.
     - `FXService`: Domain service providing high-precision `convert()` and `get_exchange_rate()` using exact Python `Decimal` arithmetic.
2. **FX Presentation Layer (`app/api/v1/fx.py`):**
   - `GET /api/v1/fx/currencies`: Supported currency codes.
   - `GET /api/v1/fx/rates?base=USD`: Real-time benchmark exchange rates.
   - `GET /api/v1/fx/convert?amount=100&from_currency=EUR&to_currency=USD`: Live currency conversion endpoint.
3. **Automated Multi-Currency Tests (`tests/test_multi_currency.py`):**
   - 3 integration tests covering:
     - Mathematical triangulation accuracy (EUR $\rightarrow$ INR through USD vehicle currency).
     - In-memory cache hits and TTL eviction.
     - Creating EUR group expenses in a USD group with rate freezing.
     - Cross-currency settlement and debt resolution down to $0.00.

### B. Existing Files Modified:
- `app/models/group.py`: Added `currency = Column(String(3), default="USD")` (base accounting currency).
- `app/models/group_expense.py`: Added `currency`, `exchange_rate` (frozen at creation), and `base_amount` (`amount * exchange_rate`).
- `app/models/settlement.py`: Added `currency`, `exchange_rate`, and `base_amount`.
- `app/models/expense.py`: Added `currency` for personal expenses.
- `app/schemas/` (`group.py`, `group_expense.py`, `settlement.py`, `expense.py`): Added `currency` parameters and response fields.
- `app/services/debt_simplifier.py`: Upgraded `calculate_member_balances()` to normalize all expenses and participant splits into the group's base currency using the frozen exchange rate snapshots.
- `app/services/group_expense_service.py` & `settlement_service.py`: Injected `FXService` to perform automated conversions whenever expense/settlement currency differs from the group base currency.
- `app/api/v1/router.py`: Mounted the `/fx` router into the API.

---

## 2. Why Were These Changes Made? (Deep Pedagogical Dive)

### A. The Adapter Pattern for Foreign Exchange (`fx_service.py`)
In real production systems, you might fetch exchange rates from:
- The European Central Bank (ECB)
- Open Exchange Rates
- Fixer.io or Wise
Every API has different JSON responses, authentication headers, and network failure modes.

#### How the Adapter Pattern Protects Our App:
We define an abstract interface:
```python
class ExchangeRateProvider(ABC):
    @abstractmethod
    def get_rates(self, base_currency: str) -> Dict[str, Decimal]:
        pass
```
Our `GroupExpenseService` and `SettlementService` only know about `ExchangeRateProvider`. They have **zero knowledge** of whether rates came from an offline table, Redis, or an external bank API!
- Switching from a test provider to a live banking API requires writing **one new adapter class** without modifying a single line of financial calculation code.

---

### B. Currency Triangulation Algorithm
Direct exchange rates between exotic pairs (e.g. Japanese Yen to Indian Rupee) are rarely published directly by central banks. International financial markets use **currency triangulation** through a reference vehicle currency (typically USD):

$$\text{Rate}(A \rightarrow B) = \frac{\text{Rate}(\text{USD} \rightarrow B)}{\text{Rate}(\text{USD} \rightarrow A)}$$

**Concrete Example:**
- $1 \text{ USD} = 0.92 \text{ EUR}$
- $1 \text{ USD} = 84.50 \text{ INR}$
- $\text{Rate}(\text{EUR} \rightarrow \text{INR}) = \frac{84.50}{0.92} \approx 91.847826 \text{ INR/EUR}$

In `app/services/fx_service.py`, this computation uses `Decimal` with `ROUND_HALF_UP` precision to prevent floating-point rounding decay.

---

### C. The ACID Financial Immutability Rule (Historical Rate Freezing)
> [!IMPORTANT]
> **Why we NEVER recalculate past debts using current exchange rates:**
> Suppose Alice pays **€100.00** for dinner in Paris in January when €1 = \$1.05.
> Bob's share is \$52.50 USD.
> In November, the Euro surges to €1 = \$1.20.
> If the system dynamically calculated Bob's debt using today's rate:
> - Bob's debt for the January dinner would suddenly jump from \$52.50 to \$60.00!
> - Bob would owe \$7.50 more without having bought anything new!
> 
> **The Accounting Solution:**
> On the day the expense is created, the system **freezes** the exchange rate directly on the `GroupExpense` table:
> - `amount`: `100.00`
> - `currency`: `EUR`
> - `exchange_rate`: `1.086957`
> - `base_amount`: `108.70`
> 
> Future currency fluctuations will affect *future* purchases, but will **never** alter historical accounting ledgers!

---

### D. Multi-Currency Debt Simplification
How does the Min-Max Greedy Heap simplify debts when people spend in 5 different currencies?
1. Every expense and split is converted into the **Group's Base Currency** using its frozen rate snapshot.
2. Net balances are tallied in Base Currency ($ \sum \text{Net} = 0 $).
3. The greedy algorithm yields simplified debts in Base Currency.
4. When settling up, Bob can pay in the Base Currency OR convert the payment to his local currency at the live settlement rate!

---

## 3. The Complete 6-Phase Evolution Matrix

| Milestone | Key Challenge Solved | Key Design Pattern / Principle |
| :--- | :--- | :--- |
| **Phase 1** | Personal Expense CRUD | Clean Layered Architecture, BaseRepository, Decimal(12,2) Precision |
| **Phase 2** | Splitwise Multi-User Engine | Strategy Pattern (Dynamic Splitting), Min-Max Greedy Heap Debt Simplification |
| **Phase 3** | Concurrency & Race Conditions | Pessimistic Row Locking (`SELECT ... FOR UPDATE`), OCC Versioning, IETF Idempotency Gate |
| **Phase 4** | API Security & DoS Defense | Sliding Window Log Rate Limiter, IETF Response Headers (`X-RateLimit-*`, `Retry-After`) |
| **Phase 5** | Heavy I/O & Automation | Asynchronous `202 Accepted` Polling, BackgroundTasks, Month-End Date Clamping |
| **Phase 6** | International Multi-Currency | Adapter Pattern FX Providers, Triangulation Math, Historical Rate Snapshot Freezing |

---

## 4. How to Run and Test Phase 6 Standalone

```powershell
# 1. Navigate to phase6 directory
cd phase6

# 2. Run all Phase 6 tests (29 tests)
$env:PYTHONPATH="c:\Users\PC\Downloads\tracer\phase6"
..\venv\Scripts\pytest tests -v

# 3. Start the server
..\venv\Scripts\uvicorn app.main:app --reload --port 8000
```
- Interactive Swagger Docs: [http://localhost:8000/api/v1/docs](http://localhost:8000/api/v1/docs)
- Test conversion endpoint: `GET /api/v1/fx/convert?amount=100&from_currency=EUR&to_currency=USD`
