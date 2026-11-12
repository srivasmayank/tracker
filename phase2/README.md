# Phase 2: Splitwise Multi-User Engine & Debt Simplification (Python Backend Guide)

> **Welcome to Phase 2!**  
> In Phase 1, we built personal expense tracking. In **Phase 2**, we transform the backend into a collaborative **Splitwise engine** where groups of friends can split expenses dynamically and settle debts with mathematical optimization.

---

## 1. What Changes Were Made From Phase 1 to Phase 2?

### A. New Files Added:
1. **Database Models (`app/models/`):**
   - `group.py`: Defines the `Group` entity (name, description, creator) and `GroupMember` junction entity (tracking who belongs to which group and their role: ADMIN vs MEMBER).
   - `group_expense.py`: Defines the `GroupExpense` header (who paid, category, amount, split type) and `ExpenseSplit` rows (how much each individual participant owes).
   - `settlement.py`: Defines the `Settlement` entity recording direct repayments between members (e.g., "Bob paid Alice \$50.00").
2. **Schemas & Data Transfer Objects (`app/schemas/`):**
   - `group.py`: `GroupCreate`, `GroupResponse`, `GroupMemberAdd`.
   - `group_expense.py`: `GroupExpenseCreate`, `ExpenseSplitInput`, `SplitType` enum (`EQUAL`, `EXACT`, `PERCENTAGE`, `SHARES`).
   - `settlement.py`: `SettlementCreate`, `DebtItem`, `MemberBalance`, `GroupBalancesResponse`.
3. **Repository Layer (`app/repositories/`):**
   - `group_repository.py`: Manages group creation, member additions, and membership verification.
   - `group_expense_repository.py`: Executes atomic persistence of the expense header along with all participant split rows.
   - `settlement_repository.py`: Records settlement transactions and queries group repayment history.
4. **Service & Algorithm Layer (`app/services/`):**
   - `split_strategies.py`: Implements the **Strategy Pattern** for dynamic split calculations.
   - `debt_simplifier.py`: Implements the **Greedy Bipartite Matching Algorithm** using Min-Max Heaps.
   - `group_service.py`: Orchestrates group lifecycle and invitations.
   - `group_expense_service.py`: Validates membership, runs the split strategy, and persists the split expense.
   - `settlement_service.py`: Validates debts and calculates group balance analytics.
5. **Presentation Layer (`app/api/v1/`):**
   - `groups.py`: Exposes REST endpoints for creating groups, inviting members, adding group expenses, querying member balances, and settling debts.
6. **Automated Tests:**
   - `tests/test_groups.py`: 5 comprehensive integration tests covering penny allocation, exact splits, percentage validation, and debt simplification workflows.

### B. Existing Files Modified:
- `app/api/v1/router.py`: Mounted the `/groups` router into the API.
- `app/core/dependencies.py`: Registered dependency injection providers for the new group repositories and services.
- `app/models/__init__.py`, `app/schemas/__init__.py`, `app/repositories/__init__.py`: Exported the new entities.

---

## 2. Why Were These Changes Made? (Deep Pedagogical Dive)

### A. The Strategy Pattern for Dynamic Splitting (`split_strategies.py`)
In real life, people split expenses in different ways:
- **Equal:** Split equally among 3 roommates.
- **Exact:** Alice pays \$30, Bob pays \$20, Charlie pays \$50.
- **Percentage:** 50% / 25% / 25%.
- **Shares:** 2 parts to 1 part (e.g. couples sharing a room).

#### Why Not Use a Giant `if/elif` Block?
If we put all calculation logic in one function:
```python
if split_type == "EQUAL":
    ...
elif split_type == "PERCENTAGE":
    ...
```
Every time a product manager asks for a new split type (e.g. "By Adjustment" or "By Hourly Usage"), we would have to modify the existing function, risking bugs in existing calculations. This violates the **Open/Closed Principle (OCP)**.

#### The Solution: The Strategy Pattern
We define an abstract base class `SplitStrategy`:
```python
class SplitStrategy(ABC):
    @abstractmethod
    def calculate_splits(self, total_amount: Decimal, split_inputs: List[ExpenseSplitInput]) -> List[ExpenseSplit]:
        pass
```
Then we create independent strategy classes: `EqualSplitStrategy`, `ExactSplitStrategy`, `PercentageSplitStrategy`, `SharesSplitStrategy`. A `SplitStrategyFactory` returns the requested strategy. Adding a 5th strategy requires writing a new class without touching existing ones!

---

### B. The "Penny Allocation" Problem in Equal Splits
When splitting \$100.00 among 3 people:
$$100.00 / 3 = 33.333333...$$
If we simply round to \$33.33:
$$33.33 \times 3 = 99.99$$
**One cent has vanished into thin air!** Over thousands of expenses, the accounting ledger would be out of balance.

#### How Our Algorithm Solves This:
In `EqualSplitStrategy`:
1. Calculate base share: $\lfloor 100.00 / 3 \rfloor = 33.33$.
2. Calculate remainder cents: $100.00 - (33.33 \times 3) = 0.01$.
3. Allocate the extra penny to the first participant!
   - Person 1: **\$33.34**
   - Person 2: **\$33.33**
   - Person 3: **\$33.33**
   - Total = **\$100.00 exactly**.

---

### C. The Debt Simplification Algorithm (`debt_simplifier.py`)
Without simplification, a trip of 5 friends can result in a messy web of $5 \times 4 / 2 = 10$ confusing pairwise debts:
- Bob owes Alice \$20
- Alice owes Charlie \$20
- Charlie owes Bob \$10...

Instead of forcing people to make 10 separate bank transfers, our algorithm uses a **Greedy Bipartite Matching Min-Max Heap**:
1. First, calculate each person's **Net Balance**:
   $$\text{Net} = \text{Total Paid} - \text{Total Owed} + \text{Settlements Paid} - \text{Settlements Received}$$
   Note that the sum of all net balances in any closed group is always strictly **zero** ($\sum \text{Net} = 0$).
2. Separate members into two priority heaps:
   - **Debtors** (people who owe money, net < 0).
   - **Creditors** (people who should receive money, net > 0).
3. In each step, match the largest debtor with the largest creditor:
   - Settle the minimum of what the debtor owes and what the creditor is owed.
   - Reinsert any remaining balance into the heap.
4. **Result:** Reduces up to $O(N^2)$ transactions to at most **$N-1$ optimal transfers**!

---

## 3. Benefits & Covered Gaps

| Capability | Phase 1 Foundation | Phase 2 Splitwise Engine |
| :--- | :--- | :--- |
| **Tenancy** | Single-user private ledger | Multi-user collaborative group ledgers |
| **Splitting** | Not supported | Equal, Exact, Percentage, and Shares |
| **Rounding** | N/A | Penny-perfect remainder allocation |
| **Settlement** | N/A | Greedy Heap Debt Simplification ($O(N^2) \rightarrow O(N)$) |
| **ACID Integrity** | Single-table commit | Multi-row atomic split persistence |

---

## 4. What Gaps Still Remained for Phase 3?

Despite these features, Phase 2 still has severe **concurrency vulnerabilities**:
1. **The Double-Click Race Condition:**  
   If Alice double-clicks "Submit Expense", two HTTP requests hit the server within 2 milliseconds. Both create duplicate expense rows in the database, doubling everyone's debt!
2. **The Over-Settlement Race Condition:**  
   If Bob owes \$50 and rapidly clicks "Settle Up" twice, two \$50 settlement rows are committed. Bob has now overpaid by \$50, turning Alice into an unintentional debtor!
3. **No Network Retry Idempotency:**  
   If a mobile app sends a payment and the connection drops before receiving the response, the app retries. The server cannot distinguish a retry from a second charge.

These critical financial race conditions are solved in **Phase 3** using Pessimistic Row Locking (`SELECT ... FOR UPDATE`) and Idempotency Keys!

---

## 5. How to Run and Test Phase 2 Standalone

```powershell
# 1. Navigate to phase2 directory
cd phase2

# 2. Run all Phase 2 tests (14 tests)
$env:PYTHONPATH="c:\Users\PC\Downloads\tracer\phase2"
..\venv\Scripts\pytest tests -v

# 3. Start the server
..\venv\Scripts\uvicorn app.main:app --reload --port 8000
```
