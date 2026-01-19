"""
Unit tests for Finnhub API provider.

Tests the FinnhubProvider class with mocked API responses.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from stockalert.api.finnhub import FinnhubProvider
from stockalert.api.base import ProviderError


class TestFinnhubProvider:
    """Tests for FinnhubProvider class."""

    @pytest.fixture
    def mock_client(self) -> MagicMock:
        """Provide a mocked Finnhub client."""
        client = MagicMock()
        client.quote.return_value = {
            "c": 175.50,  # Current price
            "d": 2.25,    # Change
            "dp": 1.30,   # Percent change
            "h": 176.00,  # High
            "l": 173.00,  # Low
            "o": 174.00,  # Open
            "pc": 173.25, # Previous close
            "t": 1704067200,
        }
        client.symbol_lookup.return_value = {
            "count": 1,
            "result": [
                {
                    "description": "Apple Inc.",
                    "displaySymbol": "AAPL",
                    "symbol": "AAPL",
                    "type": "Common Stock",
                }
            ],
        }
        return client

    @pytest.fixture
    def provider(self, mock_client: MagicMock) -> FinnhubProvider:
        """Provide a FinnhubProvider with mocked client."""
        with patch("finnhub.Client", return_value=mock_client):
            provider = FinnhubProvider(api_key="test_key")
        provider._client = mock_client
        return provider

    def test_provider_initialization(self) -> None:
        """Should initialize with API key."""
        with patch("finnhub.Client") as mock_class:
            provider = FinnhubProvider(api_key="test_key")
            mock_class.assert_called_once_with(api_key="test_key")

    def test_provider_without_api_key(self) -> None:
        """Should initialize without API key (demo mode)."""
        provider = FinnhubProvider(api_key="")
        assert provider._client is None

    def test_get_price(self, provider: FinnhubProvider) -> None:
        """Should return current price from quote."""
        price = provider.get_price("AAPL")
        assert price == 175.50

    def test_get_price_invalid_symbol(
        self, provider: FinnhubProvider, mock_client: MagicMock
    ) -> None:
        """Should return None for invalid symbol."""
        mock_client.quote.return_value = {"c": 0, "d": 0, "dp": 0, "h": 0, "l": 0, "o": 0, "pc": 0}

        price = provider.get_price("INVALID")
        assert price is None

    def test_get_quote(self, provider: FinnhubProvider) -> None:
        """Should return full quote data."""
        quote = provider.get_quote("AAPL")

        assert quote is not None
        assert quote["c"] == 175.50
        assert quote["h"] == 176.00
        assert quote["l"] == 173.00

    def test_validate_symbol_valid(self, provider: FinnhubProvider) -> None:
        """Should return True for valid symbol."""
        assert provider.validate_symbol("AAPL")

    def test_validate_symbol_invalid(
        self, provider: FinnhubProvider, mock_client: MagicMock
    ) -> None:
        """Should return False for invalid symbol."""
        mock_client.symbol_lookup.return_value = {"count": 0, "result": []}

        assert not provider.validate_symbol("INVALID123")

    def test_validate_symbol_case_insensitive(
        self, provider: FinnhubProvider, mock_client: MagicMock
    ) -> None:
        """Should handle case-insensitive symbol matching."""
        assert provider.validate_symbol("aapl")
        mock_client.symbol_lookup.assert_called_with("AAPL")

    def test_search_symbols(self, provider: FinnhubProvider) -> None:
        """Should return search results."""
        results = provider.search_symbols("Apple")

        assert len(results) == 1
        assert results[0]["symbol"] == "AAPL"
        assert results[0]["description"] == "Apple Inc."

    def test_search_symbols_no_results(
        self, provider: FinnhubProvider, mock_client: MagicMock
    ) -> None:
        """Should return empty list for no matches."""
        mock_client.symbol_lookup.return_value = {"count": 0, "result": []}

        results = provider.search_symbols("ZZZZZZZ")
        assert results == []

    def test_provider_properties(self, provider: FinnhubProvider) -> None:
        """Should have correct property values."""
        assert provider.name == "Finnhub"
        assert provider.rate_limit == 60

    def test_no_api_key_raises_on_request(self) -> None:
        """Should raise ProviderError when making request without API key."""
        provider = FinnhubProvider(api_key="")

        with pytest.raises(ProviderError, match="API key not configured"):
            provider._ensure_client()

    def test_rate_limiting_integration(
        self, provider: FinnhubProvider, mock_client: MagicMock
    ) -> None:
        """Should use rate limiter for requests."""
        # Make several requests
        for _ in range(5):
            provider.get_price("AAPL")

        # All requests should have been made
        assert mock_client.quote.call_count == 5

    def test_tokens_available_property(self, provider: FinnhubProvider) -> None:
        """Should report available rate limiter tokens."""
        initial_tokens = provider.tokens_available

        provider.get_price("AAPL")

        # Should have used one token
        assert provider.tokens_available < initial_tokens
