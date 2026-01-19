"""
Token bucket rate limiter for API calls.

Implements a token bucket algorithm to enforce rate limits
on API calls, allowing bursts while respecting overall limits.
"""

from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class RateLimitError(Exception):
    """Raised when rate limit is exceeded."""

    def __init__(self, wait_time: float) -> None:
        self.wait_time = wait_time
        super().__init__(f"Rate limit exceeded. Wait {wait_time:.1f} seconds.")


@dataclass
class RateLimiterStats:
    """Statistics for rate limiter usage."""

    total_requests: int = 0
    requests_blocked: int = 0
    total_wait_time: float = 0.0


class RateLimiter:
    """Token bucket rate limiter for API calls.

    The token bucket algorithm allows for burst traffic while maintaining
    an average rate limit. Tokens are added at a constant rate, and each
    request consumes one token.

    Attributes:
        max_tokens: Maximum number of tokens (burst capacity)
        refill_rate: Tokens added per second
        tokens: Current number of available tokens
    """

    def __init__(
        self,
        rate_limit: int = 60,
        burst_size: int = 10,
    ) -> None:
        """Initialize the rate limiter.

        Args:
            rate_limit: Maximum calls per minute
            burst_size: Maximum burst size (tokens)
        """
        self.max_tokens = burst_size
        self.refill_rate = rate_limit / 60.0  # Tokens per second
        self._tokens = float(burst_size)
        self._last_refill = time.monotonic()
        self._lock = threading.Lock()
        self._stats = RateLimiterStats()

    def _refill(self) -> None:
        """Refill tokens based on elapsed time."""
        now = time.monotonic()
        elapsed = now - self._last_refill
        tokens_to_add = elapsed * self.refill_rate
        self._tokens = min(self.max_tokens, self._tokens + tokens_to_add)
        self._last_refill = now

    def acquire(self, blocking: bool = True, timeout: float | None = None) -> bool:
        """Acquire a token for making an API call.

        Args:
            blocking: If True, block until token is available
            timeout: Maximum time to wait (seconds). None = wait forever.

        Returns:
            True if token was acquired, False if timeout expired

        Raises:
            RateLimitError: If not blocking and no tokens available
        """
        start_time = time.monotonic()
        wait_logged = False

        with self._lock:
            while True:
                self._refill()

                if self._tokens >= 1.0:
                    self._tokens -= 1.0
                    self._stats.total_requests += 1
                    return True

                if not blocking:
                    wait_time = (1.0 - self._tokens) / self.refill_rate
                    self._stats.requests_blocked += 1
                    raise RateLimitError(wait_time)

                # Check timeout
                if timeout is not None:
                    elapsed = time.monotonic() - start_time
                    if elapsed >= timeout:
                        self._stats.requests_blocked += 1
                        return False

                # Calculate wait time
                wait_time = (1.0 - self._tokens) / self.refill_rate
                if timeout is not None:
                    remaining = timeout - (time.monotonic() - start_time)
                    wait_time = min(wait_time, remaining)

                if not wait_logged:
                    logger.debug(f"Rate limit: waiting {wait_time:.2f}s for token")
                    wait_logged = True

                # Release lock while waiting
                self._lock.release()
                try:
                    time.sleep(wait_time)
                    self._stats.total_wait_time += wait_time
                finally:
                    self._lock.acquire()

    def try_acquire(self) -> bool:
        """Try to acquire a token without blocking.

        Returns:
            True if token was acquired, False if not available
        """
        try:
            return self.acquire(blocking=False)
        except RateLimitError:
            return False

    @property
    def tokens(self) -> float:
        """Get current number of available tokens."""
        with self._lock:
            self._refill()
            return self._tokens

    @property
    def stats(self) -> RateLimiterStats:
        """Get rate limiter statistics."""
        return self._stats

    def reset(self) -> None:
        """Reset the rate limiter to full capacity."""
        with self._lock:
            self._tokens = float(self.max_tokens)
            self._last_refill = time.monotonic()
            self._stats = RateLimiterStats()
