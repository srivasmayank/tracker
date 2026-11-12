# Phase 6: Multi-Currency & Real-Time Foreign Exchange (FX) Engine
## Architectural Design & Pedagogical Engineering Guide

---

## 1. Executive Summary & Problem Context

In distributed global teams, travel groups, and cross-border transactions, expenses are almost never denominated in a single homogenous currency. 
When four colleagues travel across Europe, the UK, and North America:
1. **Alice** pays `€120.00 EUR` for a group train ticket.
2. **Bob** pays `£85.00 GBP` for a shared working space.
3. **Charlie** pays `$150.00 USD` for dinner.
4. The group has its base accounting currency set to **USD ($)**.

A naive system fails here in multiple catastrophic ways:
- **Floating-point rounding decay:** `120.00 / 0.92 = 130.4347826...` Using floating point (`float`) results in discrepancies where cents disappear or phantom debts arise.
- **Dynamic Rate Drift:** If exchange rates fluctuate daily, calculating past debts dynamically would cause a user's debt to fluctuate every morning without any new transactions occurring.
- **Triangulation Complexity:** No direct exchange rate is posted between arbitrary currency pairs (e.g., Thai Baht to Norwegian Krone).

Phase 6 resolves this cleanly with an enterprise **Adapter Pattern**, **Currency Triangulation Engine**, **Historical Rate Snapshot Freezing**, and **Base-Currency Normalized Debt Simplification**.

---

## 2. High-Level Design (HLD)

### 2.1 Multi-Currency Flow & Architecture

```mermaid
sequenceDiagram
    autonumber
    actor Alice as User (Alice)
    participant API as FastAPI Router (/groups/{id}/expenses)
    participant GroupSvc as GroupExpenseService
    participant FX as FXService (Adapter + Cache)
    participant DB as MySQL (InnoDB)

    Alice->>API: POST /groups/1/expenses {amount: 120.00, currency: "EUR", split: EQUAL}
    API->>GroupSvc: create_group_expense(group_id=1, payload)
    GroupSvc->>DB: Fetch Group (base_currency = "USD")
    GroupSvc->>FX: get_conversion_rate(from_curr="EUR", to_curr="USD")
    FX-->>GroupSvc: rate = Decimal("1.085000")
    Note over GroupSvc: base_amount = 120.00 * 1.085000 = $130.20 USD<br/>Split $130.20 equally with penny allocation!
    GroupSvc->>DB: ATOMIC INSERT GroupExpense (amount=120.00, currency='EUR', exchange_rate=1.085000, base_amount=130.20)
    GroupSvc->>DB: ATOMIC INSERT ExpenseSplits (split_amount in base currency)
    DB-->>GroupSvc: Commit Transaction
    GroupSvc-->>API: GroupExpenseResponse
    API-->>Alice: HTTP 201 Created
```

---

## 3. Low-Level Design (LLD): Principles & Patterns

### 3.1 The Adapter Pattern for Exchange Rate Providers
In real-world production, foreign exchange rate APIs have different auth schemes, endpoint contracts, and reliability guarantees.
The system defines an abstract contract:

```python
class ExchangeRateProvider(ABC):
    @abstractmethod
    def get_rates(self, base_currency: str) -> Dict[str, Decimal]:
        """Fetch all exchange rates relative to the requested base currency."""
        pass

    @abstractmethod
    def get_rate(self, from_curr: str, to_curr: str) -> Decimal:
        """Fetch or triangulate exchange rate between two currencies."""
        pass
```

We implement:
1. **`FallbackStaticFXAdapter`**: An ultra-reliable offline provider with realistic central-bank benchmark rates for USD, EUR, GBP, INR, CAD, AUD, JPY, CHF, SGD.
2. **`CachedFXProvider`**: A decorator that wraps any provider with in-memory caching and configurable Time-To-Live (TTL), reducing external network latency from 250ms to 0.05ms.

### 3.2 Currency Triangulation Algorithm
Given standard rates against reference currency (USD):
$$\text{Rate}(\text{EUR} \rightarrow \text{INR}) = \frac{\text{Rate}(\text{USD} \rightarrow \text{INR})}{\text{Rate}(\text{USD} \rightarrow \text{EUR})}$$

All computations use Python's `Decimal` with `ROUND_HALF_UP` precision to prevent floating-point anomalies.

### 3.3 Historical Rate Freezing (Financial Immutability)
In accounting, historical transactions are **immutable**.
When an expense is recorded:
- `amount`: Original nominal amount entered by user (e.g. `120.00`).
- `currency`: 3-letter currency code (e.g. `EUR`).
- `exchange_rate`: The precise conversion rate at the moment of creation (e.g. `1.085000`).
- `base_amount`: The value in the group's base currency (e.g. `130.20`).

Future exchange rate swings affect **future** expenses, but **never** retroactively alter historical balances.

---

## 4. Multi-Currency Debt Simplification

The Min-Max Greedy Heap algorithm simplifies debts seamlessly across currencies:
1. Every expense's net contribution to a member is normalized to the **Group Base Currency**.
2. Net balances are summed in Base Currency ($ \sum \text{Balance} = 0 $).
3. The greedy algorithm yields optimal base-currency settlement transactions.
4. When settling up, the user can pay in base currency or convert at the live settlement rate.

---

## 5. Verification & Testing Strategy

1. **Unit Tests:** Triangulation mathematics, Decimal precision, caching TTL.
2. **Integration Tests:** Group creation with custom base currency (`EUR`, `GBP`, `USD`), cross-currency expense creation with rate freezing, multi-currency debt simplification, and multi-currency settlement.
3. **Frontend Integration:** Currency pickers, live conversion previews, and group base-currency balance reporting.
