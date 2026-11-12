from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


class Settlement(Base):
    """
    Settlement transaction recording a direct repayment between two group members.
    Reduces the payer's liability and the payee's credit balance within the group.
    """
    __tablename__ = "settlements"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    group_id = Column(Integer, ForeignKey("groups.id", ondelete="CASCADE"), nullable=False, index=True)
    payer_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    payee_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(3), default="USD", nullable=False)
    exchange_rate = Column(Numeric(14, 6), default=1.0, nullable=False)
    base_amount = Column(Numeric(12, 2), nullable=True)
    notes = Column(String(255), nullable=True)
    settled_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    group = relationship("Group", back_populates="settlements")
    payer = relationship("User", foreign_keys=[payer_id])
    payee = relationship("User", foreign_keys=[payee_id])

    def __repr__(self) -> str:
        return f"<Settlement(id={self.id}, group_id={self.group_id}, payer={self.payer_id} -> payee={self.payee_id}, amount={self.amount})>"

