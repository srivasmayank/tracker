from datetime import datetime, timezone, timedelta
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Index
from app.core.database import Base


class IdempotencyRecord(Base):
    """
    Idempotency persistence entity adhering to the IETF Idempotency-Key specification.
    Stores in-flight lock status and cached completed HTTP responses to guarantee
    exactly-once execution semantics for financial mutations.
    """
    __tablename__ = "idempotency_keys"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    key = Column(String(64), unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    request_path = Column(String(255), nullable=False)
    request_hash = Column(String(64), nullable=False)  # SHA-256 fingerprint of request payload
    response_code = Column(Integer, nullable=True)
    response_body = Column(Text, nullable=True)  # Serialized JSON response
    status = Column(String(20), default="PROCESSING", nullable=False)  # PROCESSING, COMPLETED, FAILED
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    expires_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc) + timedelta(hours=24),
        nullable=False,
        index=True
    )

    __table_args__ = (
        Index("idx_idempotency_key_user", "key", "user_id"),
    )

    def __repr__(self) -> str:
        return f"<IdempotencyRecord(key='{self.key}', status='{self.status}', user_id={self.user_id})>"

