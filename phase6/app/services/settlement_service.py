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
from app.services.fx_service import FXService, default_fx_service


class SettlementService:
    """
    Business logic layer for debt settlements with ACID concurrency controls:
    1. Idempotency Key validation and response replay.
    2. Pessimistic row-locking (SELECT ... FOR UPDATE) on the Group aggregate.
    3. Multi-currency settlement conversion to Group base currency.
    4. Real-time balance invariants preventing concurrent over-settlements.
    """

    def __init__(
        self,
        group_repo: GroupRepository,
        group_expense_repo: GroupExpenseRepository,
        settlement_repo: SettlementRepository,
        idempotency_service: IdempotencyService,
        fx_service: Optional[FXService] = None
    ):
        self.group_repo = group_repo
        self.group_expense_repo = group_expense_repo
        self.settlement_repo = settlement_repo
        self.idempotency_service = idempotency_service
        self.fx_service = fx_service or default_fx_service

    def record_settlement(
        self,
        group_id: int,
        payer_id: int,
        data: SettlementCreate,
        idempotency_key: Optional[str] = None
    ) -> Union[Settlement, Dict[str, Any]]:
        """
        Records a repayment with full concurrency protection and multi-currency support.
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

            # 4. Multi-Currency Normalization to Base Currency
            group_base_curr = getattr(locked_group, "currency", "USD") or "USD"
            settle_curr = (data.currency or group_base_curr).upper().strip()

            if settle_curr != group_base_curr:
                base_amt, rate = self.fx_service.convert(data.amount, settle_curr, group_base_curr)
            else:
                base_amt = data.amount
                rate = Decimal("1.000000")

            # 5. Check real-time balance invariant in Base Currency
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
                    detail=f"You do not owe any money in this group (Current net balance: +{group_base_curr} {payer_net:.2f})."
                )

            # Prevent over-settling more than the outstanding debt
            outstanding_debt = abs(payer_net)
            if base_amt > outstanding_debt:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Settlement amount ({group_base_curr} {base_amt:.2f}) exceeds total outstanding debt ({group_base_curr} {outstanding_debt:.2f})."
                )

            # 6. Record settlement transaction with frozen exchange rate
            settlement = Settlement(
                group_id=group_id,
                payer_id=payer_id,
                payee_id=data.payee_id,
                amount=data.amount,
                currency=settle_curr,
                exchange_rate=rate,
                base_amount=base_amt,
                notes=data.notes.strip() if data.notes else None
            )
            created_settlement = self.settlement_repo.record_settlement(settlement)

            # 7. Barrier 3: Increment OCC Version on group aggregate
            self.group_repo.increment_version_occ(locked_group)

            # 8. Cache response in Idempotency Store
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
        Computes member net balances and simplified debt transactions for the group in its base currency.
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
        group_currency = getattr(group, "currency", "USD") or "USD"

        net_balances, member_balances, total_spending = DebtSimplifier.calculate_member_balances(
            members=users,
            expenses=expenses,
            settlements=settlements
        )

        simplified_debts = DebtSimplifier.simplify_debts(
            net_balances=net_balances,
            members=users,
            currency=group_currency
        )

        return GroupBalancesResponse(
            group_id=group_id,
            currency=group_currency,
            total_spending=total_spending,
            members=member_balances,
            simplified_debts=simplified_debts
        )
