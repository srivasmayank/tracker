import json
import hashlib
from typing import Any, Optional, Dict
from fastapi import HTTPException, status
from app.repositories.idempotency_repository import IdempotencyRepository


class IdempotencyService:
    """
    Business logic layer for request deduplication and response caching.
    Adheres to the IETF Idempotency-Key specification.
    """

    def __init__(self, idempotency_repo: IdempotencyRepository):
        self.idempotency_repo = idempotency_repo

    @staticmethod
    def compute_payload_hash(payload: Any) -> str:
        """Computes a deterministic SHA-256 fingerprint of the request payload."""
        if payload is None:
            raw = ""
        elif isinstance(payload, str):
            raw = payload
        else:
            # Sort keys to ensure deterministic ordering regardless of dictionary iteration order
            raw = json.dumps(payload, sort_keys=True, default=str)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def check_or_reserve(
        self,
        key: Optional[str],
        user_id: int,
        request_path: str,
        payload: Any
    ) -> Optional[Dict[str, Any]]:
        """
        Guards transaction entry:
        - If key is None: Idempotency not requested, proceed with normal execution.
        - If key is fresh: Atomically creates record in 'PROCESSING' state and proceeds.
        - If key is 'PROCESSING': Raises HTTP 409 Conflict (in-flight concurrent duplicate).
        - If key is 'COMPLETED': Replays cached response without running business logic.
        """
        if not key or not key.strip():
            return None

        clean_key = key.strip()
        payload_hash = self.compute_payload_hash(payload)

        record, is_new = self.idempotency_repo.try_create_lock(
            key=clean_key,
            user_id=user_id,
            request_path=request_path,
            request_hash=payload_hash
        )

        if is_new:
            # Successfully acquired the in-flight processing lock
            return None

        # Existing record found
        if record.status == "PROCESSING":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A request with this idempotency key is currently processing. Please retry shortly."
            )

        if record.status == "COMPLETED":
            # Security verification: Ensure the caller didn't reuse the key with a different payload
            if record.request_hash != payload_hash:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Idempotency key has already been used with a different request payload."
                )

            # Replay cached response
            try:
                cached_data = json.loads(record.response_body) if record.response_body else {}
                return cached_data
            except Exception:
                return {}

        return None

    def mark_completed(
        self,
        key: Optional[str],
        user_id: int,
        response_code: int,
        response_data: Any
    ) -> None:
        """Caches the serialized response and transitions state to COMPLETED."""
        if not key or not key.strip():
            return

        body_str = json.dumps(response_data, default=str)
        self.idempotency_repo.mark_completed(
            key=key.strip(),
            user_id=user_id,
            response_code=response_code,
            response_body=body_str
        )

    def mark_failed(self, key: Optional[str], user_id: int) -> None:
        """Transitions state to FAILED upon unhandled exception to unblock retries."""
        if not key or not key.strip():
            return
        self.idempotency_repo.mark_failed(key=key.strip(), user_id=user_id)

