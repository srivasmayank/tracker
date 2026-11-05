from typing import List
from fastapi import HTTPException, status
from app.models.settlement import Settlement
from app.schemas.settlement import SettlementCreate, GroupBalancesResponse
from app.repositories.group_repository import GroupRepository
from app.repositories.group_expense_repository import GroupExpenseRepository
from app.repositories.settlement_repository import SettlementRepository
from app.services.debt_simplifier import DebtSimplifier


class SettlementService:
    """
    Business logic layer for debt settlements and balance resolutions.
    """

    def __init__(
        self,
        group_repo: GroupRepository,
        group_expense_repo: GroupExpenseRepository,
        settlement_repo: SettlementRepository
    ):
        self.group_repo = group_repo
        self.group_expense_repo = group_expense_repo
        self.settlement_repo = settlement_repo

    def record_settlement(
        self,
        group_id: int,
        payer_id: int,
        data: SettlementCreate
    ) -> Settlement:
        """
        Records a direct repayment from the authenticated requester (payer) to the payee.
        """
        # 1. Verify payer is member of group
        if not self.group_repo.is_member(group_id, payer_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You must be a member of this group to record a settlement."
            )

        # 2. Verify payee is distinct and also a member
        if payer_id == data.payee_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Payer and payee cannot be the same user."
            )

        if not self.group_repo.is_member(group_id, data.payee_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Payee must be an active member of this group."
            )

        # 3. Create Settlement
        settlement = Settlement(
            group_id=group_id,
            payer_id=payer_id,
            payee_id=data.payee_id,
            amount=data.amount,
            notes=data.notes.strip() if data.notes else None
        )
        return self.settlement_repo.record_settlement(settlement)

    def list_group_settlements(self, group_id: int, user_id: int) -> List[Settlement]:
        """Fetch all settlements in the group."""
        if not self.group_repo.is_member(group_id, user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not a member of this group."
            )
        return self.settlement_repo.list_by_group(group_id)

    def get_group_balances(self, group_id: int, user_id: int) -> GroupBalancesResponse:
        """
        Computes member net balances and simplified debt transactions for the group.
        """
        # 1. Verify membership and retrieve group details
        group = self.group_repo.get_group_with_members(group_id)
        if not group:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Group not found."
            )

        member_ids = [m.user_id for m in group.members]
        if user_id not in member_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not a member of this group."
            )

        users = [m.user for m in group.members if m.user]

        # 2. Fetch expenses and settlements
        expenses = self.group_expense_repo.list_by_group(group_id)
        settlements = self.settlement_repo.list_by_group(group_id)

        # 3. Calculate net balances
        net_balances, member_balances, total_spending = DebtSimplifier.calculate_member_balances(
            members=users,
            expenses=expenses,
            settlements=settlements
        )

        # 4. Run Debt Minimization / Simplification Graph Algorithm
        simplified_debts = DebtSimplifier.simplify_debts(
            net_balances=net_balances,
            members=users
        )

        return GroupBalancesResponse(
            group_id=group_id,
            total_spending=total_spending,
            members=member_balances,
            simplified_debts=simplified_debts
        )

