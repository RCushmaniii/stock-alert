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

# Shared rate limiter singleton - all FinnhubProvider instances share the same
# rate limiter since they all use the same API key with a global rate limit
_shared_rate_limiter: RateLimiter | None = None
_provider_instance_count: int = 0


def _get_shared_rate_limiter() -> RateLimiter:
    """Get or create the shared rate limiter singleton."""
    global _shared_rate_limiter
    if _shared_rate_limiter is None:
        logger.info("Creating shared rate limiter singleton")
        _shared_rate_limiter = RateLimiter(
            rate_limit=60,  # Free tier limit
            burst_size=10,  # Allow short bursts
        )
    return _shared_rate_limiter


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
        global _provider_instance_count
        _provider_instance_count += 1

        self._api_key = api_key
        self._client: finnhub.Client | None = None
        # Use shared rate limiter so all instances respect the global API rate limit
        self._rate_limiter = _get_shared_rate_limiter()

        if api_key:
            self._client = finnhub.Client(api_key=api_key)
            logger.info(
                f"Finnhub provider #{_provider_instance_count} initialized, "
                f"rate limiter tokens: {self._rate_limiter.tokens:.1f}"
            )
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
        func_name = getattr(func, "__name__", str(func))
        logger.debug(f"Making request: {func_name}, tokens before: {self._rate_limiter.tokens:.1f}")

        # Acquire rate limit token
        if not self._rate_limiter.acquire(blocking=True, timeout=30.0):
            logger.warning(f"Rate limit timeout for {func_name}")
            raise RateLimitError(30.0)

        logger.debug(f"Token acquired for {func_name}, tokens after: {self._rate_limiter.tokens:.1f}")

        try:
            result = func(*args, **kwargs)
            logger.debug(f"Request {func_name} succeeded")
            return result
        except finnhub.FinnhubAPIException as e:
            logger.error(f"Finnhub API error in {func_name}: {e}")
            raise ProviderError(f"API error: {e}") from e
        except Exception as e:
            logger.exception(f"Unexpected error in {func_name}: {e}")
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
                return dict(quote)  # Explicit cast to satisfy mypy
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

    def get_market_news(self, category: str = "general") -> list[dict[str, Any]]:
        """Get latest market news.

        Args:
            category: News category - general, forex, crypto, or merger

        Returns:
            List of news articles with:
                - category: News category
                - datetime: Published time (UNIX timestamp)
                - headline: News headline
                - id: News ID
                - image: Thumbnail image URL
                - related: Related stocks mentioned
                - source: News source
                - summary: News summary
                - url: URL to original article
        """
        try:
            client = self._ensure_client()
            news = self._make_request(client.general_news, category)
            return list(news) if news else []

        except ProviderError:
            return []

    def get_company_news(
        self, symbol: str, from_date: str, to_date: str
    ) -> list[dict[str, Any]]:
        """Get company news articles.

        Args:
            symbol: Stock ticker symbol
            from_date: Start date in YYYY-MM-DD format
            to_date: End date in YYYY-MM-DD format

        Returns:
            List of news articles with:
                - category: News category
                - datetime: Published time (UNIX timestamp)
                - headline: News headline
                - id: News ID
                - image: Thumbnail image URL
                - related: Related stocks mentioned
                - source: News source
                - summary: News summary
                - url: URL to original article
        """
        try:
            client = self._ensure_client()
            news = self._make_request(
                client.company_news, symbol.upper(), _from=from_date, to=to_date
            )
            return list(news) if news else []

        except ProviderError:
            return []

    def get_company_profile(self, symbol: str) -> dict[str, Any] | None:
        """Get company profile data.

        Args:
            symbol: Stock ticker symbol

        Returns:
            Dictionary with company profile:
                - country: Country of headquarters
                - currency: Currency used in filings
                - exchange: Listed exchange
                - finnhubIndustry: Industry classification
                - ipo: IPO date
                - logo: Logo image URL
                - marketCapitalization: Market cap in millions
                - name: Company name
                - phone: Company phone
                - shareOutstanding: Shares outstanding in millions
                - ticker: Ticker symbol
                - weburl: Company website
            Returns None if unavailable
        """
        try:
            client = self._ensure_client()
            profile = self._make_request(client.company_profile2, symbol=symbol.upper())

            if profile and profile.get("name"):
                return dict(profile)  # Explicit cast to satisfy mypy
            return None

        except ProviderError:
            return None

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
