import time
import threading
from abc import ABC, abstractmethod
from typing import Dict, List, Tuple, Callable, Optional
from fastapi import Request, Response, HTTPException, status
from app.core.config import settings


class RateLimiterStorage(ABC):
    """
    Abstract storage contract for rate limiter algorithms.
    Adheres to the Open/Closed Principle (OCP) and Liskov Substitution Principle (LSP):
    allows swapping between InMemory and Redis backends without changing route guards.
    """

    @abstractmethod
    def record_and_check(
        self,
        key: str,
        limit: int,
        window_seconds: int
    ) -> Tuple[bool, int, int, int]:
        """
        Atomically records an arrival timestamp and evaluates the rate limit.
        Returns:
            is_allowed (bool): Whether the request is permitted.
            remaining (int): Available quota remaining in the window.
            reset_time (int): Unix epoch timestamp when quota refreshes.
            retry_after (int): Seconds client must wait if throttled.
        """
        pass

    @abstractmethod
    def clear(self) -> None:
        """Flushes rate limiter state (useful for test isolation)."""
        pass


class InMemorySlidingWindowStorage(RateLimiterStorage):
    """
    Thread-safe, Sliding Window Log rate limiter.
    Tracks precise floating-point request timestamps per key.
    Eliminates boundary traffic spikes inherent to fixed-window counters.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._logs: Dict[str, List[float]] = {}

    def record_and_check(
        self,
        key: str,
        limit: int,
        window_seconds: int
    ) -> Tuple[bool, int, int, int]:
        now = time.time()
        window_start = now - window_seconds

        with self._lock:
            timestamps = self._logs.get(key, [])
            # Evict timestamps outside the rolling window
            valid_timestamps = [t for t in timestamps if t > window_start]

            reset_time = int(valid_timestamps[0] + window_seconds) if valid_timestamps else int(now + window_seconds)

            if len(valid_timestamps) < limit:
                # Request is allowed: record timestamp and grant access
                valid_timestamps.append(now)
                self._logs[key] = valid_timestamps
                remaining = limit - len(valid_timestamps)
                return True, remaining, reset_time, 0
            else:
                # Quota exceeded: deny request
                self._logs[key] = valid_timestamps
                oldest = valid_timestamps[0]
                retry_after = max(1, int(oldest + window_seconds - now) + 1)
                return False, 0, reset_time, retry_after

    def clear(self) -> None:
        with self._lock:
            self._logs.clear()


# Default singleton storage instance (Thread-safe memory store)
default_rate_limit_storage = InMemorySlidingWindowStorage()


def get_client_ip(request: Request) -> str:
    """Extracts client IP address respecting X-Forwarded-For reverse proxy headers."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "127.0.0.1"


class RateLimiter:
    """
    FastAPI dependency guard enforcing rate limiting on routes.
    Emits standard IETF rate-limit response headers:
    X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset, and Retry-After.
    """

    def __init__(
        self,
        limit: int,
        window_seconds: int,
        key_func: Callable[[Request], str] = get_client_ip,
        storage: Optional[RateLimiterStorage] = None,
        scope: str = "default"
    ):
        self.limit = limit
        self.window_seconds = window_seconds
        self.key_func = key_func
        self.storage = storage or default_rate_limit_storage
        self.scope = scope

    async def __call__(self, request: Request, response: Response) -> None:
        if not settings.RATE_LIMITING_ENABLED:
            return

        subject = self.key_func(request)
        rate_key = f"{self.scope}:{subject}"

        is_allowed, remaining, reset_time, retry_after = self.storage.record_and_check(
            key=rate_key,
            limit=self.limit,
            window_seconds=self.window_seconds
        )

        headers = {
            "X-RateLimit-Limit": str(self.limit),
            "X-RateLimit-Remaining": str(remaining),
            "X-RateLimit-Reset": str(reset_time),
        }

        # Store on request.state so middleware can preserve headers across exceptions
        request.state.rate_limit_headers = headers

        # Attach informational rate limit headers to response
        for k, v in headers.items():
            response.headers[k] = v

        if not is_allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Maximum {self.limit} requests per {self.window_seconds}s. Try again in {retry_after} seconds.",
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(self.limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(reset_time),
                }
            )
