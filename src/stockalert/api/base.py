"""
Abstract base class for stock data providers.

Defines the interface that all API providers must implement.
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class ProviderError(Exception):
    """Base exception for provider-related errors."""

    pass


class BaseProvider(ABC):
    """Abstract base class for stock data API providers."""

    @abstractmethod
    def get_price(self, symbol: str) -> float | None:
        """Get current stock price.

        Args:
            symbol: Stock ticker symbol (e.g., "AAPL")

        Returns:
            Current price as float, or None if unavailable

        Raises:
            ProviderError: If there's an API error
        """
        ...

    @abstractmethod
    def validate_symbol(self, symbol: str) -> bool:
        """Validate if a stock symbol exists.

        Args:
            symbol: Stock ticker symbol to validate

        Returns:
            True if symbol is valid, False otherwise
        """
        ...

    @abstractmethod
    def get_quote(self, symbol: str) -> dict[str, float] | None:
        """Get full quote data for a symbol.

        Args:
            symbol: Stock ticker symbol

        Returns:
            Dictionary with quote data (current, high, low, open, close, etc.)
            or None if unavailable
        """
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        """Get provider name."""
        ...

    @property
    @abstractmethod
    def rate_limit(self) -> int:
        """Get API rate limit (calls per minute)."""
        ...
