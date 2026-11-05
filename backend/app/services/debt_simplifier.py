import heapq
from decimal import Decimal
from typing import List, Dict, Tuple
from app.models.group_expense import GroupExpense
from app.models.settlement import Settlement
from app.models.user import User
from app.schemas.settlement import DebtItem, MemberBalance, GroupBalancesResponse


class DebtSimplifier:
    """
    Core algorithmic engine for calculating member net balances and
    minimizing pairwise debts using a Greedy Bipartite Matching algorithm.
    """

    @staticmethod
    def calculate_member_balances(
        members: List[User],
        expenses: List[GroupExpense],
        settlements: List[Settlement]
    ) -> Tuple[Dict[int, Decimal], List[MemberBalance], Decimal]:
        """
        Calculates individual net balances for all group members:
        Net = (Total Paid For Expenses - Total Owed In Splits) + (Settlements Paid - Settlements Received)
        """
        user_map: Dict[int, User] = {m.id: m for m in members}
        total_paid: Dict[int, Decimal] = {m.id: Decimal("0.00") for m in members}
        total_owed: Dict[int, Decimal] = {m.id: Decimal("0.00") for m in members}
        total_group_spending = Decimal("0.00")

        # 1. Tally Expenses & Splits
        for exp in expenses:
            total_group_spending += exp.amount
            if exp.paid_by_user_id in total_paid:
                total_paid[exp.paid_by_user_id] += exp.amount

            for split in exp.splits:
                if split.user_id in total_owed:
                    total_owed[split.user_id] += split.owed_amount

        # 2. Tally Direct Settlements
        settlements_paid: Dict[int, Decimal] = {m.id: Decimal("0.00") for m in members}
        settlements_received: Dict[int, Decimal] = {m.id: Decimal("0.00") for m in members}

        for s in settlements:
            if s.payer_id in settlements_paid:
                settlements_paid[s.payer_id] += s.amount
            if s.payee_id in settlements_received:
                settlements_received[s.payee_id] += s.amount

        # 3. Calculate Net Balances
        net_balances: Dict[int, Decimal] = {}
        member_balances: List[MemberBalance] = []

        for m in members:
            uid = m.id
            net = (total_paid[uid] - total_owed[uid]) + (settlements_paid[uid] - settlements_received[uid])
            net_balances[uid] = net

            member_balances.append(
                MemberBalance(
                    user_id=uid,
                    full_name=m.full_name,
                    email=m.email,
                    net_balance=net,
                    total_paid=total_paid[uid],
                    total_owed=total_owed[uid]
                )
            )

        return net_balances, member_balances, total_group_spending

    @staticmethod
    def simplify_debts(
        net_balances: Dict[int, Decimal],
        members: List[User]
    ) -> List[DebtItem]:
        """
        Greedy bipartite matching using two heaps (Min-Debtor and Max-Creditor).
        Reduces O(N^2) pairwise debts to at most N-1 transactions.
        """
        user_map = {m.id: m.full_name for m in members}

        # Max-heaps stored with negative values because Python heapq is a min-heap
        # Creditors: positive net balance (stored as (-amount, user_id))
        # Debtors: negative net balance (stored as (-abs(net), user_id))
        creditor_heap = []
        debtor_heap = []

        epsilon = Decimal("0.001")  # Ignore sub-cent precision dust

        for uid, balance in net_balances.items():
            if balance > epsilon:
                heapq.heappush(creditor_heap, (-float(balance), uid))
            elif balance < -epsilon:
                heapq.heappush(debtor_heap, (-float(abs(balance)), uid))

        simplified_debts: List[DebtItem] = []

        while debtor_heap and creditor_heap:
            neg_debt_amt, debtor_id = heapq.heappop(debtor_heap)
            neg_credit_amt, creditor_id = heapq.heappop(creditor_heap)

            debt_amt = Decimal(str(-neg_debt_amt)).quantize(Decimal("0.01"))
            credit_amt = Decimal(str(-neg_credit_amt)).quantize(Decimal("0.01"))

            settle_amount = min(debt_amt, credit_amt)

            simplified_debts.append(
                DebtItem(
                    debtor_id=debtor_id,
                    debtor_name=user_map.get(debtor_id, f"User {debtor_id}"),
                    creditor_id=creditor_id,
                    creditor_name=user_map.get(creditor_id, f"User {creditor_id}"),
                    amount=settle_amount
                )
            )

            remaining_debt = debt_amt - settle_amount
            remaining_credit = credit_amt - settle_amount

            if remaining_debt > epsilon:
                heapq.heappush(debtor_heap, (-float(remaining_debt), debtor_id))

            if remaining_credit > epsilon:
                heapq.heappush(creditor_heap, (-float(remaining_credit), creditor_id))

        return simplified_debts

