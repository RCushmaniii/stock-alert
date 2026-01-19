"""
Finnhub API provider for stock data.

Implements the BaseProvider interface using the Finnhub API.
Free tier allows 60 API calls per minute.
"""

from __future__ import annotations

import logging
from typing import Any

import finnhub

from stockalert.api.base import BaseProvider, ProviderError
from stockalert.api.rate_limiter import RateLimiter, RateLimitError

logger = logging.getLogger(__name__)


class FinnhubProvider(BaseProvider):
    """Finnhub API provider for stock data.

    Attributes:
        RATE_LIMIT: API calls per minute (free tier)
        BURST_SIZE: Maximum burst size for rate limiter
    """

    RATE_LIMIT = 60  # Free tier limit
    BURST_SIZE = 10  # Allow short bursts

    def __init__(self, api_key: str) -> None:
        """Initialize Finnhub provider.

        Args:
            api_key: Finnhub API key
        """
        self._api_key = api_key
        self._client: finnhub.Client | None = None
        self._rate_limiter = RateLimiter(
            rate_limit=self.RATE_LIMIT,
            burst_size=self.BURST_SIZE,
        )

        if api_key:
            self._client = finnhub.Client(api_key=api_key)
            logger.info("Finnhub provider initialized")
        else:
            logger.warning("Finnhub API key not provided - running in demo mode")

    def _ensure_client(self) -> finnhub.Client:
        """Ensure client is initialized.

        Returns:
            Finnhub client instance

        Raises:
            ProviderError: If API key not configured
        """
        if self._client is None:
            raise ProviderError(
                "Finnhub API key not configured. "
                "Set FINNHUB_API_KEY environment variable."
            )
        return self._client

    def _make_request(self, func: Any, *args: Any, **kwargs: Any) -> Any:
        """Make a rate-limited API request.

        Args:
            func: API function to call
            *args: Positional arguments for function
            **kwargs: Keyword arguments for function

        Returns:
            API response

        Raises:
            ProviderError: If API call fails
            RateLimitError: If rate limit exceeded
        """
        # Acquire rate limit token
        if not self._rate_limiter.acquire(blocking=True, timeout=30.0):
            raise RateLimitError(30.0)

        try:
            return func(*args, **kwargs)
        except finnhub.FinnhubAPIException as e:
            logger.error(f"Finnhub API error: {e}")
            raise ProviderError(f"API error: {e}") from e
        except Exception as e:
            logger.exception(f"Unexpected error: {e}")
            raise ProviderError(f"Unexpected error: {e}") from e

    def get_price(self, symbol: str) -> float | None:
        """Get current stock price.

        Args:
            symbol: Stock ticker symbol (e.g., "AAPL")

        Returns:
            Current price as float, or None if unavailable
        """
        quote = self.get_quote(symbol)
        if quote and "c" in quote and quote["c"] > 0:
            return float(quote["c"])
        return None

    def get_quote(self, symbol: str) -> dict[str, float] | None:
        """Get full quote data for a symbol.

        Args:
            symbol: Stock ticker symbol

        Returns:
            Dictionary with quote data:
                - c: Current price
                - d: Change
                - dp: Percent change
                - h: High price of the day
                - l: Low price of the day
                - o: Open price of the day
                - pc: Previous close price
                - t: Timestamp
            Returns None if unavailable
        """
        try:
            client = self._ensure_client()
            quote = self._make_request(client.quote, symbol.upper())

            # Finnhub returns 0 for all values if symbol not found
            if quote and quote.get("c", 0) > 0:
                return quote
            return None

        except ProviderError:
            return None

    def validate_symbol(self, symbol: str) -> bool:
        """Validate if a stock symbol exists.

        Args:
            symbol: Stock ticker symbol to validate

        Returns:
            True if symbol is valid, False otherwise
        """
        try:
            client = self._ensure_client()
            result = self._make_request(client.symbol_lookup, symbol.upper())

            if result and result.get("count", 0) > 0:
                # Check if exact match exists
                for item in result.get("result", []):
                    if item.get("symbol", "").upper() == symbol.upper():
                        return True
                    if item.get("displaySymbol", "").upper() == symbol.upper():
                        return True
            return False

        except ProviderError:
            return False

    def search_symbols(self, query: str) -> list[dict[str, str]]:
        """Search for stock symbols.

        Args:
            query: Search query

        Returns:
            List of matching symbols with description
        """
        try:
            client = self._ensure_client()
            result = self._make_request(client.symbol_lookup, query)

            if result and result.get("count", 0) > 0:
                return [
                    {
                        "symbol": item.get("displaySymbol", item.get("symbol", "")),
                        "description": item.get("description", ""),
                        "type": item.get("type", ""),
                    }
                    for item in result.get("result", [])
                ]
            return []

        except ProviderError:
            return []

    @property
    def name(self) -> str:
        """Get provider name."""
        return "Finnhub"

    @property
    def rate_limit(self) -> int:
        """Get API rate limit (calls per minute)."""
        return self.RATE_LIMIT

    @property
    def tokens_available(self) -> float:
        """Get current rate limiter tokens."""
        return self._rate_limiter.tokens
