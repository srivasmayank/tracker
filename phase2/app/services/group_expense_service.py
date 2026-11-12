from typing import List
from fastapi import HTTPException, status
from app.models.group_expense import GroupExpense
from app.schemas.group_expense import GroupExpenseCreate, ExpenseSplitInput, SplitType
from app.repositories.group_repository import GroupRepository
from app.repositories.group_expense_repository import GroupExpenseRepository
from app.repositories.category_repository import CategoryRepository
from app.services.split_strategies import SplitStrategyFactory


class GroupExpenseService:
    """
    Business logic layer orchestrating group expense splitting and persistence.
    """

    def __init__(
        self,
        group_repo: GroupRepository,
        group_expense_repo: GroupExpenseRepository,
        category_repo: CategoryRepository
    ):
        self.group_repo = group_repo
        self.group_expense_repo = group_expense_repo
        self.category_repo = category_repo

    def create_group_expense(
        self,
        group_id: int,
        requester_id: int,
        data: GroupExpenseCreate
    ) -> GroupExpense:
        """
        Creates a shared group expense, calculates split distribution using the Strategy Pattern,
        and atomically commits everything in a single transaction.
        """
        # 1. Verify requester is a group member
        if not self.group_repo.is_member(group_id, requester_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You must be a member of this group to add an expense."
            )

        # 2. Determine payer (defaults to requester if not specified)
        paid_by = data.paid_by_user_id or requester_id
        if not self.group_repo.is_member(group_id, paid_by):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="The user marked as payer must belong to the group."
            )

        # 3. Verify category
        category = self.category_repo.get_user_category_by_id(data.category_id, requester_id)
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found."
            )

        # 4. Resolve split participant inputs
        group_member_ids = set(self.group_repo.get_member_user_ids(group_id))

        split_inputs: List[ExpenseSplitInput] = data.splits or []

        # If EQUAL split and no specific participants provided, default to all group members
        if data.split_type == SplitType.EQUAL and not split_inputs:
            split_inputs = [ExpenseSplitInput(user_id=uid) for uid in group_member_ids]

        if not split_inputs:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one participant is required to split the expense."
            )

        # Verify all split participant user_ids belong to the group
        for s in split_inputs:
            if s.user_id not in group_member_ids:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Participant user {s.user_id} is not a member of this group."
                )

        # 5. Execute Strategy Pattern for split calculation
        strategy = SplitStrategyFactory.get_strategy(data.split_type)
        calculated_splits = strategy.calculate_splits(
            total_amount=data.amount,
            split_inputs=split_inputs
        )

        # 6. Instantiate GroupExpense model
        expense = GroupExpense(
            group_id=group_id,
            paid_by_user_id=paid_by,
            category_id=data.category_id,
            amount=data.amount,
            description=data.description.strip(),
            split_type=data.split_type.value,
            expense_date=data.expense_date
        )

        # 7. Atomic persistence of header + all splits
        return self.group_expense_repo.create_atomic_group_expense(expense, calculated_splits)

    def list_group_expenses(self, group_id: int, user_id: int) -> List[GroupExpense]:
        """Fetch all shared expenses within a group."""
        if not self.group_repo.is_member(group_id, user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not a member of this group."
            )
        return self.group_expense_repo.list_by_group(group_id)

