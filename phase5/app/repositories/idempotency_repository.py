from typing import Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.models.idempotency import IdempotencyRecord
from app.repositories.base import BaseRepository


class IdempotencyRepository(BaseRepository[IdempotencyRecord]):
    """Data access repository for Idempotency tracking and response caching."""

    def __init__(self, db: Session):
        super().__init__(IdempotencyRecord, db)

    def get_by_key(self, key: str, user_id: int) -> Optional[IdempotencyRecord]:
        """Fetch idempotency record for a specific key and user."""
        return (
            self.db.query(IdempotencyRecord)
            .filter(IdempotencyRecord.key == key, IdempotencyRecord.user_id == user_id)
            .first()
        )

    def try_create_lock(
        self,
        key: str,
        user_id: int,
        request_path: str,
        request_hash: str
    ) -> Tuple[IdempotencyRecord, bool]:
        """
        Attempts to atomically reserve the idempotency key in status 'PROCESSING'.
        Returns (record, is_new):
        - If is_new == True: Lock successfully acquired for this new operation.
        - If is_new == False: Key already exists (either in-flight or completed).
        """
        record = IdempotencyRecord(
            key=key,
            user_id=user_id,
            request_path=request_path,
            request_hash=request_hash,
            status="PROCESSING"
        )
        try:
            self.db.add(record)
            self.db.commit()
            self.db.refresh(record)
            return record, True
        except IntegrityError:
            self.db.rollback()
            existing = self.get_by_key(key, user_id)
            return existing, False

    def mark_completed(self, key: str, user_id: int, response_code: int, response_body: str) -> None:
        """Atomically transitions status to 'COMPLETED' and caches the response payload."""
        record = self.get_by_key(key, user_id)
        if record:
            record.status = "COMPLETED"
            record.response_code = response_code
            record.response_body = response_body
            self.db.commit()

    def mark_failed(self, key: str, user_id: int) -> None:
        """Transitions status to 'FAILED' allowing client to retry after error."""
        record = self.get_by_key(key, user_id)
        if record:
            record.status = "FAILED"
            self.db.commit()

