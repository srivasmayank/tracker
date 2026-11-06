from decimal import Decimal
from typing import List, Optional, Union, Dict, Any
from fastapi import HTTPException, status
from app.models.settlement import Settlement
from app.schemas.settlement import SettlementCreate, SettlementResponse, GroupBalancesResponse
from app.repositories.group_repository import GroupRepository
from app.repositories.group_expense_repository import GroupExpenseRepository
from app.repositories.settlement_repository import SettlementRepository
from app.services.debt_simplifier import DebtSimplifier
from app.services.idempotency_service import IdempotencyService


class SettlementService:
    """
    Business logic layer for debt settlements with ACID concurrency controls:
    1. Idempotency Key validation and response replay.
    2. Pessimistic row-locking (SELECT ... FOR UPDATE) on the Group aggregate.
    3. Real-time balance invariants preventing concurrent over-settlements.
    """

    def __init__(
        self,
        group_repo: GroupRepository,
        group_expense_repo: GroupExpenseRepository,
        settlement_repo: SettlementRepository,
        idempotency_service: IdempotencyService
    ):
        self.group_repo = group_repo
        self.group_expense_repo = group_expense_repo
        self.settlement_repo = settlement_repo
        self.idempotency_service = idempotency_service

    def record_settlement(
        self,
        group_id: int,
        payer_id: int,
        data: SettlementCreate,
        idempotency_key: Optional[str] = None
    ) -> Union[Settlement, Dict[str, Any]]:
        """
        Records a repayment with full concurrency protection.
        If idempotency_key is provided and was already completed, replays the cached response.
        """
        request_path = f"/api/v1/groups/{group_id}/settle"

        # 1. Barrier 1: Check Idempotency Gate
        cached_response = self.idempotency_service.check_or_reserve(
            key=idempotency_key,
            user_id=payer_id,
            request_path=request_path,
            payload=data.model_dump()
        )
        if cached_response is not None:
            return cached_response

        try:
            # 2. Barrier 2: Pessimistic Engine Lock (SELECT ... FOR UPDATE)
            # In MySQL InnoDB, this acquires an exclusive lock on the Group row.
            # Any concurrent settle or expense request on this group will wait.
            locked_group = self.group_repo.get_group_for_update(group_id)
            if not locked_group:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Group not found."
                )

            # 3. Verify membership
            if not self.group_repo.is_member(group_id, payer_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You must be a member of this group to record a settlement."
                )

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

            # 4. Check real-time balance invariant while holding the lock
            # Verify debtor does not overpay if settling
            group_details = self.group_repo.get_group_with_members(group_id)
            users = [m.user for m in group_details.members if m.user]
            expenses = self.group_expense_repo.list_by_group(group_id)
            current_settlements = self.settlement_repo.list_by_group(group_id)

            net_balances, _, _ = DebtSimplifier.calculate_member_balances(
                members=users,
                expenses=expenses,
                settlements=current_settlements
            )

            payer_net = net_balances.get(payer_id, Decimal("0.00"))
            # If payer is a net creditor (net >= 0), they owe nothing to the group
            if payer_net >= Decimal("0.00"):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"You do not owe any money in this group (Current net balance: +${payer_net:.2f})."
                )

            # Prevent over-settling more than the outstanding debt
            outstanding_debt = abs(payer_net)
            if data.amount > outstanding_debt:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Settlement amount (${data.amount:.2f}) exceeds total outstanding debt (${outstanding_debt:.2f})."
                )

            # 5. Record settlement transaction
            settlement = Settlement(
                group_id=group_id,
                payer_id=payer_id,
                payee_id=data.payee_id,
                amount=data.amount,
                notes=data.notes.strip() if data.notes else None
            )
            created_settlement = self.settlement_repo.record_settlement(settlement)

            # 6. Barrier 3: Increment OCC Version on group aggregate
            self.group_repo.increment_version_occ(locked_group)

            # 7. Cache response in Idempotency Store
            if idempotency_key:
                settlement_dto = SettlementResponse.model_validate(created_settlement).model_dump()
                self.idempotency_service.mark_completed(
                    key=idempotency_key,
                    user_id=payer_id,
                    response_code=201,
                    response_data=settlement_dto
                )

            return created_settlement
        except Exception:
            # Release lock in case of failure so user can retry
            if idempotency_key:
                self.idempotency_service.mark_failed(key=idempotency_key, user_id=payer_id)
            raise

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
        expenses = self.group_expense_repo.list_by_group(group_id)
        settlements = self.settlement_repo.list_by_group(group_id)

        net_balances, member_balances, total_spending = DebtSimplifier.calculate_member_balances(
            members=users,
            expenses=expenses,
            settlements=settlements
        )

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
