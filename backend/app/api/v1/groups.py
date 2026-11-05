from typing import List
from fastapi import APIRouter, Depends, status
from app.models.user import User
from app.schemas.group import GroupCreate, GroupResponse, GroupMemberAdd, GroupMemberResponse
from app.schemas.group_expense import GroupExpenseCreate, GroupExpenseResponse
from app.schemas.settlement import SettlementCreate, SettlementResponse, GroupBalancesResponse
from app.services.group_service import GroupService
from app.services.group_expense_service import GroupExpenseService
from app.services.settlement_service import SettlementService
from app.core.dependencies import (
    get_group_service,
    get_group_expense_service,
    get_settlement_service,
    get_current_user
)

router = APIRouter(prefix="/groups", tags=["Groups & Splitwise"])


@router.post("", response_model=GroupResponse, status_code=status.HTTP_201_CREATED)
def create_group(
    group_in: GroupCreate,
    current_user: User = Depends(get_current_user),
    group_service: GroupService = Depends(get_group_service)
):
    """Create a new group ledger and assign current user as ADMIN."""
    return group_service.create_group(creator_id=current_user.id, data=group_in)


@router.get("", response_model=List[GroupResponse])
def list_groups(
    current_user: User = Depends(get_current_user),
    group_service: GroupService = Depends(get_group_service)
):
    """List all groups the authenticated user is currently a member of."""
    return group_service.get_user_groups(user_id=current_user.id)


@router.get("/{group_id}", response_model=GroupResponse)
def get_group_details(
    group_id: int,
    current_user: User = Depends(get_current_user),
    group_service: GroupService = Depends(get_group_service)
):
    """Retrieve group details including active members."""
    return group_service.get_group_details(group_id=group_id, user_id=current_user.id)


@router.post("/{group_id}/members", response_model=GroupMemberResponse, status_code=status.HTTP_201_CREATED)
def add_group_member(
    group_id: int,
    member_in: GroupMemberAdd,
    current_user: User = Depends(get_current_user),
    group_service: GroupService = Depends(get_group_service)
):
    """Invite/Add an existing registered user to the group by email."""
    return group_service.add_member_by_email(
        group_id=group_id,
        requester_id=current_user.id,
        data=member_in
    )


@router.post("/{group_id}/expenses", response_model=GroupExpenseResponse, status_code=status.HTTP_201_CREATED)
def create_group_expense(
    group_id: int,
    expense_in: GroupExpenseCreate,
    current_user: User = Depends(get_current_user),
    group_expense_service: GroupExpenseService = Depends(get_group_expense_service)
):
    """
    Record a shared group expense with dynamic splitting strategy (EQUAL, EXACT, PERCENTAGE, SHARES).
    Atomically writes header and individual participant splits in one ACID transaction.
    """
    return group_expense_service.create_group_expense(
        group_id=group_id,
        requester_id=current_user.id,
        data=expense_in
    )


@router.get("/{group_id}/expenses", response_model=List[GroupExpenseResponse])
def list_group_expenses(
    group_id: int,
    current_user: User = Depends(get_current_user),
    group_expense_service: GroupExpenseService = Depends(get_group_expense_service)
):
    """List all shared expenses recorded for this group."""
    return group_expense_service.list_group_expenses(group_id=group_id, user_id=current_user.id)


@router.get("/{group_id}/balances", response_model=GroupBalancesResponse)
def get_group_balances(
    group_id: int,
    current_user: User = Depends(get_current_user),
    settlement_service: SettlementService = Depends(get_settlement_service)
):
    """
    Computes total group spending, member net balances, and runs the
    Greedy Debt Minimization algorithm to generate simplified 'who owes whom' settlements.
    """
    return settlement_service.get_group_balances(group_id=group_id, user_id=current_user.id)


@router.post("/{group_id}/settle", response_model=SettlementResponse, status_code=status.HTTP_201_CREATED)
def record_settlement(
    group_id: int,
    settlement_in: SettlementCreate,
    current_user: User = Depends(get_current_user),
    settlement_service: SettlementService = Depends(get_settlement_service)
):
    """
    Record a direct repayment from the authenticated user to a fellow creditor.
    Immediately updates the net debt balance.
    """
    return settlement_service.record_settlement(
        group_id=group_id,
        payer_id=current_user.id,
        data=settlement_in
    )


@router.get("/{group_id}/settlements", response_model=List[SettlementResponse])
def list_group_settlements(
    group_id: int,
    current_user: User = Depends(get_current_user),
    settlement_service: SettlementService = Depends(get_settlement_service)
):
    """List historical settlements recorded in this group."""
    return settlement_service.list_group_settlements(group_id=group_id, user_id=current_user.id)

