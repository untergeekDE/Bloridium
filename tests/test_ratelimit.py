"""Tests for the per-client upload rate limiter."""

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "webapp"))

from ratelimit import SlidingWindowLimiter  # noqa: E402


def test_allows_up_to_limit_then_blocks():
    limiter = SlidingWindowLimiter(limit=2, window_s=60)
    assert limiter.allow("a", now=0) == (True, 0)
    assert limiter.allow("a", now=1) == (True, 0)
    allowed, retry_after = limiter.allow("a", now=2)
    assert allowed is False
    assert retry_after == 58  # oldest hit at t=0 expires at t=60


def test_window_expires():
    limiter = SlidingWindowLimiter(limit=1, window_s=10)
    assert limiter.allow("a", now=0) == (True, 0)
    assert limiter.allow("a", now=5)[0] is False
    assert limiter.allow("a", now=10) == (True, 0)


def test_clients_are_independent():
    limiter = SlidingWindowLimiter(limit=1, window_s=60)
    assert limiter.allow("a", now=0)[0] is True
    assert limiter.allow("a", now=1)[0] is False
    assert limiter.allow("b", now=1)[0] is True


def test_retry_after_is_at_least_one_second():
    limiter = SlidingWindowLimiter(limit=1, window_s=10)
    limiter.allow("a", now=0)
    allowed, retry_after = limiter.allow("a", now=9.5)
    assert allowed is False
    assert retry_after == 1
