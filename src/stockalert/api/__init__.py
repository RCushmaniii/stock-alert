"""
Stock data API providers for StockAlert.

This package contains:
- base: Abstract provider interface
- finnhub: Finnhub API client
- rate_limiter: Token bucket rate limiting
"""

from __future__ import annotations

from stockalert.api.base import BaseProvider, ProviderError
from stockalert.api.finnhub import FinnhubProvider
from stockalert.api.rate_limiter import RateLimiter, RateLimitError

__all__ = [
    "BaseProvider",
    "FinnhubProvider",
    "ProviderError",
    "RateLimitError",
    "RateLimiter",
]
