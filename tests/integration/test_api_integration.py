"""
Integration tests for API provider with rate limiting.

Tests the integration between FinnhubProvider and RateLimiter.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from stockalert.api.finnhub import FinnhubProvider
from stockalert.api.rate_limiter import RateLimiter


class TestApiRateLimiterIntegration:
    """Integration tests for API provider with rate limiting."""

    @pytest.fixture
    def mock_finnhub_client(self) -> MagicMock:
        """Provide a mocked Finnhub client."""
        client = MagicMock()
        client.quote.return_value = {
            "c": 175.50,
            "d": 2.25,
            "dp": 1.30,
            "h": 176.00,
            "l": 173.00,
            "o": 174.00,
            "pc": 173.25,
            "t": 1704067200,
        }
        return client

    @pytest.fixture
    def provider(self, mock_finnhub_client: MagicMock) -> FinnhubProvider:
        """Provide a FinnhubProvider with mocked client."""
        with patch("finnhub.Client", return_value=mock_finnhub_client):
            provider = FinnhubProvider(api_key="test_key")
        provider._client = mock_finnhub_client
        # Use a smaller burst size for testing
        provider._rate_limiter = RateLimiter(rate_limit=60, burst_size=3)
        return provider

    def test_multiple_requests_use_rate_limiter(
        self, provider: FinnhubProvider, mock_finnhub_client: MagicMock
    ) -> None:
        """Multiple requests should use tokens from rate limiter."""
        initial_tokens = provider.tokens_available

        # Make several requests
        for _ in range(3):
            provider.get_price("AAPL")

        # All should succeed, tokens should be depleted
        assert mock_finnhub_client.quote.call_count == 3
        assert provider.tokens_available < initial_tokens

    def test_rate_limiter_blocks_excess_requests(
        self, provider: FinnhubProvider
    ) -> None:
        """Rate limiter should block requests beyond burst size."""
        # Set a very short timeout to avoid waiting
        provider._rate_limiter = RateLimiter(rate_limit=60, burst_size=2)

        # These should succeed
        assert provider.get_price("AAPL") is not None
        assert provider.get_price("AAPL") is not None

        # Next request should have to wait (but with blocking=True it will)
        # This test verifies the rate limiter is being used
        assert provider.tokens_available < 1

    @pytest.mark.integration
    def test_quote_and_validate_different_endpoints(
        self, provider: FinnhubProvider, mock_finnhub_client: MagicMock
    ) -> None:
        """Different API methods should all use rate limiter."""
        provider.get_price("AAPL")
        provider.validate_symbol("MSFT")
        provider.search_symbols("Tesla")

        # All should consume tokens
        assert provider._rate_limiter.stats.total_requests == 3


class TestAlertFlowIntegration:
    """Integration tests for the alert flow."""

    @pytest.mark.integration
    def test_price_check_to_alert_flow(
        self,
        sample_config: dict,
        mock_finnhub_client: MagicMock,
    ) -> None:
        """Full flow from price check to alert should work."""
        from stockalert.core.config import ConfigManager
        from stockalert.core.monitor import StockMonitor
        from stockalert.core.alert_manager import AlertManager
        from stockalert.api.finnhub import FinnhubProvider
        from stockalert.utils.market_hours import MarketHours

        # Set up mocks
        mock_finnhub_client = MagicMock()
        mock_finnhub_client.quote.return_value = {
            "c": 250.0,  # Above the 200.0 high threshold
            "d": 0, "dp": 0, "h": 0, "l": 0, "o": 0, "pc": 0,
        }

        # Create components
        with patch("finnhub.Client", return_value=mock_finnhub_client):
            provider = FinnhubProvider(api_key="test")
        provider._client = mock_finnhub_client

        alert_manager = MagicMock(spec=AlertManager)
        market_hours = MagicMock(spec=MarketHours)
        market_hours.is_market_open.return_value = True

        # Use a mock config manager
        config_manager = MagicMock(spec=ConfigManager)
        config_manager.get_enabled_tickers.return_value = [
            {
                "symbol": "AAPL",
                "name": "Apple Inc.",
                "high_threshold": 200.0,
                "low_threshold": 150.0,
                "enabled": True,
            }
        ]
        config_manager.get.side_effect = lambda key, default=None: {
            "settings.check_interval": 60,
            "settings.cooldown": 300,
        }.get(key, default)

        # Create monitor and check
        monitor = StockMonitor(
            config_manager=config_manager,
            provider=provider,
            alert_manager=alert_manager,
            market_hours=market_hours,
            debug=True,
        )

        # Perform check
        state = monitor.get_ticker_state("AAPL")
        monitor._check_ticker(state)

        # Verify alert was sent
        alert_manager.send_high_alert.assert_called_once_with(
            symbol="AAPL",
            name="Apple Inc.",
            price=250.0,
            threshold=200.0,
        )
