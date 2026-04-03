from __future__ import annotations

import time
from collections import defaultdict
from threading import Lock


class InMemoryRateLimiter:
    """Sliding-window rate limiter. Thread-safe, per-key (typically per-IP)."""

    def __init__(self, max_calls: int = 10, window_seconds: float = 60.0) -> None:
        self._max_calls = max_calls
        self._window = window_seconds
        self._calls: dict[str, list[float]] = defaultdict(list)
        self._lock = Lock()

    def is_allowed(self, key: str) -> bool:
        """Returns True if the key is within the rate limit, False if exceeded."""
        now = time.monotonic()
        cutoff = now - self._window
        with self._lock:
            self._calls[key] = [t for t in self._calls[key] if t > cutoff]
            if len(self._calls[key]) >= self._max_calls:
                return False
            self._calls[key].append(now)
            return True
