from abc import ABC, abstractmethod
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Dict
from fastapi import HTTPException, status
from app.schemas.group_expense import SplitType, ExpenseSplitInput
from app.models.group_expense import ExpenseSplit


class SplitStrategy(ABC):
    """
    Abstract Strategy Interface for expense splitting algorithms.
    Adheres to Open/Closed Principle (OCP): New splitting rules extend this class
    without altering existing expense creation pipeline logic.
    """

    @abstractmethod
    def calculate_splits(
        self,
        total_amount: Decimal,
        split_inputs: List[ExpenseSplitInput]
    ) -> List[ExpenseSplit]:
        """
        Calculates and returns concrete ExpenseSplit records.
        Guarantees Invariant: sum(split.owed_amount) == total_amount.
        """
        pass


class EqualSplitStrategy(SplitStrategy):
    """
    Splits total amount equally among all participants.
    Resolves fractional pennies by distributing leftover cents to participants
    ensuring sum(splits) exactly equals total_amount down to 2 decimal places.
    """

    def calculate_splits(
        self,
        total_amount: Decimal,
        split_inputs: List[ExpenseSplitInput]
    ) -> List[ExpenseSplit]:
        count = len(split_inputs)
        if count == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one participant must be included in the split."
            )

        # Convert to cents to eliminate floating-point issues
        total_cents = int(total_amount * 100)
        base_cents = total_cents // count
        remainder_cents = total_cents % count

        splits = []
        for i, item in enumerate(split_inputs):
            # Allocate an extra cent to first `remainder_cents` participants
            cents = base_cents + (1 if i < remainder_cents else 0)
            owed = Decimal(cents) / Decimal(100)
            splits.append(
                ExpenseSplit(
                    user_id=item.user_id,
                    owed_amount=owed,
                    percentage=None,
                    shares=None
                )
            )
        return splits


class ExactSplitStrategy(SplitStrategy):
    """
    Validates and assigns exact specified currency amounts.
    Enforces strict mathematical invariant: sum(owed_amounts) == total_amount.
    """

    def calculate_splits(
        self,
        total_amount: Decimal,
        split_inputs: List[ExpenseSplitInput]
    ) -> List[ExpenseSplit]:
        if not split_inputs:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Split details with exact amounts are required."
            )

        splits = []
        total_sum = Decimal("0.00")

        for item in split_inputs:
            if item.owed_amount is None or item.owed_amount <= Decimal("0.00"):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"User {item.user_id} must have a positive owed amount for exact split."
                )
            total_sum += item.owed_amount
            splits.append(
                ExpenseSplit(
                    user_id=item.user_id,
                    owed_amount=item.owed_amount,
                    percentage=None,
                    shares=None
                )
            )

        if total_sum != total_amount:
            diff = total_amount - total_sum
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Sum of split amounts ({total_sum}) does not equal total expense ({total_amount}). Difference: {diff}"
            )

        return splits


class PercentageSplitStrategy(SplitStrategy):
    """
    Splits total amount by specified percentages.
    Enforces sum(percentages) == 100.00% and resolves penny rounding differences.
    """

    def calculate_splits(
        self,
        total_amount: Decimal,
        split_inputs: List[ExpenseSplitInput]
    ) -> List[ExpenseSplit]:
        if not split_inputs:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Split details with percentages are required."
            )

        total_pct = Decimal("0.00")
        for item in split_inputs:
            if item.percentage is None or item.percentage <= Decimal("0.00"):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"User {item.user_id} must have a positive percentage."
                )
            total_pct += item.percentage

        if total_pct != Decimal("100.00"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Sum of split percentages must equal 100.00%. Current sum: {total_pct}%"
            )

        splits = []
        computed_sum = Decimal("0.00")
        cent = Decimal("0.01")

        for item in split_inputs:
            # Round to 2 decimal places using half-up arithmetic
            raw_owed = (total_amount * item.percentage) / Decimal("100.00")
            owed = raw_owed.quantize(cent, rounding=ROUND_HALF_UP)
            computed_sum += owed
            splits.append(
                ExpenseSplit(
                    user_id=item.user_id,
                    owed_amount=owed,
                    percentage=item.percentage,
                    shares=None
                )
            )

        # Allocate any 1-cent discrepancy caused by independent roundings
        discrepancy = total_amount - computed_sum
        if discrepancy != Decimal("0.00") and len(splits) > 0:
            splits[0].owed_amount += discrepancy

        return splits


class SharesSplitStrategy(SplitStrategy):
    """
    Splits total amount proportionally by integer shares (e.g. 2 shares vs 1 share).
    """

    def calculate_splits(
        self,
        total_amount: Decimal,
        split_inputs: List[ExpenseSplitInput]
    ) -> List[ExpenseSplit]:
        if not split_inputs:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Split details with shares are required."
            )

        total_shares = sum(item.shares or 0 for item in split_inputs)
        if total_shares <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Total shares must be greater than zero."
            )

        total_cents = int(total_amount * 100)
        splits = []
        allocated_cents = 0

        for item in split_inputs:
            if item.shares is None or item.shares <= 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"User {item.user_id} must have at least 1 share."
                )
            user_cents = (total_cents * item.shares) // total_shares
            allocated_cents += user_cents
            splits.append(
                ExpenseSplit(
                    user_id=item.user_id,
                    owed_amount=Decimal(user_cents) / Decimal(100),
                    percentage=None,
                    shares=item.shares
                )
            )

        # Leftover cents from integer division go to first participant
        leftover = total_cents - allocated_cents
        if leftover > 0 and len(splits) > 0:
            splits[0].owed_amount += Decimal(leftover) / Decimal(100)

        return splits


class SplitStrategyFactory:
    """
    Factory creating the appropriate strategy based on the SplitType enum.
    """
    _strategies: Dict[SplitType, SplitStrategy] = {
        SplitType.EQUAL: EqualSplitStrategy(),
        SplitType.EXACT: ExactSplitStrategy(),
        SplitType.PERCENTAGE: PercentageSplitStrategy(),
        SplitType.SHARES: SharesSplitStrategy(),
    }

    @classmethod
    def get_strategy(cls, split_type: SplitType) -> SplitStrategy:
        strategy = cls._strategies.get(split_type)
        if not strategy:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported split strategy type: {split_type}"
            )
        return strategy

