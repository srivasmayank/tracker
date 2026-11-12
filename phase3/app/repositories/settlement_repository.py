from typing import List
from sqlalchemy.orm import Session, joinedload
from app.models.settlement import Settlement
from app.repositories.base import BaseRepository


class SettlementRepository(BaseRepository[Settlement]):
    """Data access repository for Settlement repayment transactions."""

    def __init__(self, db: Session):
        super().__init__(Settlement, db)

    def record_settlement(self, settlement: Settlement) -> Settlement:
        """Atomically record and commit a repayment between two group members."""
        self.db.add(settlement)
        self.db.commit()
        self.db.refresh(settlement)
        return self.get_by_id_eager(settlement.id)

    def get_by_id_eager(self, settlement_id: int) -> Settlement:
        """Fetch settlement with payer and payee eagerly loaded."""
        return (
            self.db.query(Settlement)
            .options(
                joinedload(Settlement.payer),
                joinedload(Settlement.payee)
            )
            .filter(Settlement.id == settlement_id)
            .first()
        )

    def list_by_group(self, group_id: int) -> List[Settlement]:
        """Fetch all settlements recorded in a group."""
        return (
            self.db.query(Settlement)
            .options(
                joinedload(Settlement.payer),
                joinedload(Settlement.payee)
            )
            .filter(Settlement.group_id == group_id)
            .order_by(Settlement.settled_at.desc())
            .all()
        )

