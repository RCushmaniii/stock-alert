"""
Unit tests for the rate limiter.

Tests the token bucket algorithm implementation.
"""

from __future__ import annotations

import time
from unittest.mock import patch

import pytest

from stockalert.api.rate_limiter import RateLimiter, RateLimitError


class TestRateLimiter:
    """Tests for RateLimiter class."""

    def test_initial_tokens(self) -> None:
        """Rate limiter should start with max tokens."""
        limiter = RateLimiter(rate_limit=60, burst_size=10)
        assert limiter.tokens == 10

    def test_acquire_decrements_tokens(self) -> None:
        """Acquiring a token should decrement the count."""
        limiter = RateLimiter(rate_limit=60, burst_size=10)
        initial = limiter.tokens

        assert limiter.acquire(blocking=False)
        assert limiter.tokens < initial

    def test_acquire_multiple_tokens(self) -> None:
        """Should be able to acquire multiple tokens up to burst size."""
        limiter = RateLimiter(rate_limit=60, burst_size=5)

        for _ in range(5):
            assert limiter.acquire(blocking=False)

        # Next acquisition should fail without waiting
        with pytest.raises(RateLimitError):
            limiter.acquire(blocking=False)

    def test_try_acquire_non_blocking(self) -> None:
        """try_acquire should return False instead of raising."""
        limiter = RateLimiter(rate_limit=60, burst_size=1)

        # First should succeed
        assert limiter.try_acquire()

        # Second should fail gracefully
        assert not limiter.try_acquire()

    def test_tokens_refill_over_time(self) -> None:
        """Tokens should refill based on elapsed time."""
        limiter = RateLimiter(rate_limit=60, burst_size=10)

        # Use all tokens
        for _ in range(10):
            limiter.acquire(blocking=False)

        assert limiter.tokens < 1

        # Wait a bit for tokens to refill naturally
        time.sleep(0.2)
        tokens_after = limiter.tokens
        assert tokens_after >= 0.1  # Some tokens should have refilled

    def test_tokens_cap_at_max(self) -> None:
        """Tokens should not exceed max_tokens."""
        limiter = RateLimiter(rate_limit=60, burst_size=5)

        # Tokens should be at max initially
        assert limiter.tokens == 5  # Capped at burst_size

        # Use one token
        limiter.acquire(blocking=False)
        assert limiter.tokens < 5

        # Reset should restore to max
        limiter.reset()
        assert limiter.tokens == 5

    def test_acquire_with_timeout(self) -> None:
        """Acquire with timeout should return False when timeout expires."""
        limiter = RateLimiter(rate_limit=60, burst_size=1)

        # Use the one token
        limiter.acquire(blocking=False)

        # Next acquire with short timeout should fail
        result = limiter.acquire(blocking=True, timeout=0.01)
        assert not result

    def test_rate_limit_error_contains_wait_time(self) -> None:
        """RateLimitError should contain estimated wait time."""
        limiter = RateLimiter(rate_limit=60, burst_size=1)

        limiter.acquire(blocking=False)

        with pytest.raises(RateLimitError) as exc_info:
            limiter.acquire(blocking=False)

        assert exc_info.value.wait_time > 0

    def test_reset_restores_tokens(self) -> None:
        """Reset should restore tokens to max."""
        limiter = RateLimiter(rate_limit=60, burst_size=10)

        # Use some tokens
        for _ in range(5):
            limiter.acquire(blocking=False)

        limiter.reset()
        assert limiter.tokens == 10

    def test_stats_tracking(self) -> None:
        """Stats should track requests and blocks."""
        limiter = RateLimiter(rate_limit=60, burst_size=2)

        # Make requests
        limiter.acquire(blocking=False)
        limiter.acquire(blocking=False)

        assert limiter.stats.total_requests == 2
        assert limiter.stats.requests_blocked == 0

        # Try to exceed limit
        try:
            limiter.acquire(blocking=False)
        except RateLimitError:
            pass

        assert limiter.stats.requests_blocked == 1

    def test_different_rate_limits(self) -> None:
        """Should handle different rate limit configurations."""
        # High rate limit
        fast_limiter = RateLimiter(rate_limit=600, burst_size=50)
        assert fast_limiter.refill_rate == 10.0  # 600/60 = 10 per second

        # Low rate limit
        slow_limiter = RateLimiter(rate_limit=30, burst_size=5)
        assert slow_limiter.refill_rate == 0.5  # 30/60 = 0.5 per second
