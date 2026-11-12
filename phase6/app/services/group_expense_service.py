from decimal import Decimal
from typing import List, Optional, Union, Dict, Any
from fastapi import HTTPException, status
from app.models.group_expense import GroupExpense
from app.schemas.group_expense import GroupExpenseCreate, GroupExpenseResponse, ExpenseSplitInput, SplitType
from app.repositories.group_repository import GroupRepository
from app.repositories.group_expense_repository import GroupExpenseRepository
from app.repositories.category_repository import CategoryRepository
from app.services.split_strategies import SplitStrategyFactory
from app.services.idempotency_service import IdempotencyService
from app.services.fx_service import FXService, default_fx_service


class GroupExpenseService:
    """
    Business logic layer orchestrating group expense splitting and persistence
    with ACID concurrency, multi-currency conversion, and idempotency protections.
    """

    def __init__(
        self,
        group_repo: GroupRepository,
        group_expense_repo: GroupExpenseRepository,
        category_repo: CategoryRepository,
        idempotency_service: IdempotencyService,
        fx_service: Optional[FXService] = None
    ):
        self.group_repo = group_repo
        self.group_expense_repo = group_expense_repo
        self.category_repo = category_repo
        self.idempotency_service = idempotency_service
        self.fx_service = fx_service or default_fx_service

    def create_group_expense(
        self,
        group_id: int,
        requester_id: int,
        data: GroupExpenseCreate,
        idempotency_key: Optional[str] = None
    ) -> Union[GroupExpense, Dict[str, Any]]:
        """
        Creates a shared group expense, calculates split distribution using the Strategy Pattern,
        and atomically commits everything in a single transaction.
        Replays cached response if idempotency key was previously completed.
        """
        request_path = f"/api/v1/groups/{group_id}/expenses"

        # 1. Idempotency Gate
        cached_response = self.idempotency_service.check_or_reserve(
            key=idempotency_key,
            user_id=requester_id,
            request_path=request_path,
            payload=data.model_dump()
        )
        if cached_response is not None:
            return cached_response

        try:
            # 2. Acquire Pessimistic Row Lock on Group Aggregate
            locked_group = self.group_repo.get_group_for_update(group_id)
            if not locked_group:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Group not found."
                )

            # 3. Verify requester is a group member
            if not self.group_repo.is_member(group_id, requester_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You must be a member of this group to add an expense."
                )

            # 4. Determine payer (defaults to requester if not specified)
            paid_by = data.paid_by_user_id or requester_id
            if not self.group_repo.is_member(group_id, paid_by):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="The user marked as payer must belong to the group."
                )

            # 5. Verify category
            category = self.category_repo.get_user_category_by_id(data.category_id, requester_id)
            if not category:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Category not found."
                )

            # 6. Resolve split participant inputs
            group_member_ids = set(self.group_repo.get_member_user_ids(group_id))
            split_inputs: List[ExpenseSplitInput] = data.splits or []

            if data.split_type == SplitType.EQUAL and not split_inputs:
                split_inputs = [ExpenseSplitInput(user_id=uid) for uid in group_member_ids]

            if not split_inputs:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="At least one participant is required to split the expense."
                )

            for s in split_inputs:
                if s.user_id not in group_member_ids:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Participant user {s.user_id} is not a member of this group."
                    )

            # 7. Execute Strategy Pattern for split calculation
            strategy = SplitStrategyFactory.get_strategy(data.split_type)
            calculated_splits = strategy.calculate_splits(
                total_amount=data.amount,
                split_inputs=split_inputs
            )

            # 8. Multi-Currency Normalization & Exchange Rate Freezing
            group_base_curr = getattr(locked_group, "currency", "USD") or "USD"
            expense_curr = (data.currency or group_base_curr).upper().strip()

            if expense_curr != group_base_curr:
                base_amt, rate = self.fx_service.convert(data.amount, expense_curr, group_base_curr)
            else:
                base_amt = data.amount
                rate = Decimal("1.000000")

            # 9. Instantiate GroupExpense model with frozen exchange rate
            expense = GroupExpense(
                group_id=group_id,
                paid_by_user_id=paid_by,
                category_id=data.category_id,
                amount=data.amount,
                currency=expense_curr,
                exchange_rate=rate,
                base_amount=base_amt,
                description=data.description.strip(),
                split_type=data.split_type.value,
                expense_date=data.expense_date
            )

            # 10. Atomic persistence of header + all splits
            created_expense = self.group_expense_repo.create_atomic_group_expense(expense, calculated_splits)

            # 10. Increment OCC version
            self.group_repo.increment_version_occ(locked_group)

            # 11. Cache response in Idempotency Store
            if idempotency_key:
                expense_dto = GroupExpenseResponse.model_validate(created_expense).model_dump()
                self.idempotency_service.mark_completed(
                    key=idempotency_key,
                    user_id=requester_id,
                    response_code=201,
                    response_data=expense_dto
                )

            return created_expense
        except Exception:
            if idempotency_key:
                self.idempotency_service.mark_failed(key=idempotency_key, user_id=requester_id)
            raise

    def list_group_expenses(self, group_id: int, user_id: int) -> List[GroupExpense]:
        """Fetch all shared expenses within a group."""
        if not self.group_repo.is_member(group_id, user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not a member of this group."
            )
        return self.group_expense_repo.list_by_group(group_id)
