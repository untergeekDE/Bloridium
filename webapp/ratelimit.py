"""Small in-process sliding-window rate limiter for upload requests.

Gunicorn runs several worker processes, so this is a per-worker limit. The
service uses two workers and documents the resulting ceiling; a shared
store would be overkill for a small public converter.

The limiter only keeps timestamps in memory. Client addresses are never
written to disk by this module.
"""

from __future__ import annotations

import math
import threading
import time


class SlidingWindowLimiter:
    """Allow at most `limit` events per key in the last `window_s` seconds."""

    def __init__(self, limit: int, window_s: float, max_keys: int = 4096):
        if limit < 1:
            raise ValueError("limit must be >= 1")
        if window_s <= 0:
            raise ValueError("window_s must be > 0")
        self.limit = limit
        self.window_s = window_s
        self.max_keys = max_keys
        self._hits: dict[str, list[float]] = {}
        self._lock = threading.Lock()

    def allow(self, key: str, now: float | None = None) -> tuple[bool, int]:
        """Return (allowed, retry_after_seconds).

        `now` is injectable for tests; production uses a monotonic clock.
        """
        now = time.monotonic() if now is None else now
        cutoff = now - self.window_s
        with self._lock:
            hits = self._hits.get(key)
            if hits is None:
                hits = []
                self._hits[key] = hits
            else:
                hits[:] = [t for t in hits if t > cutoff]

            if len(hits) >= self.limit:
                retry_after = max(1, math.ceil(hits[0] + self.window_s - now))
                return False, retry_after

            hits.append(now)
            if len(self._hits) > self.max_keys:
                self._prune(cutoff)
            return True, 0

    def _prune(self, cutoff: float) -> None:
        """Drop idle keys so a spray of source addresses cannot grow forever."""
        for key in [k for k, hits in self._hits.items()
                    if not hits or hits[-1] <= cutoff]:
            del self._hits[key]
