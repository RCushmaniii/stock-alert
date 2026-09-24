"""
Unit tests for the stock monitor.

Tests the StockMonitor class.
"""

from __future__ import annotations

import time
from unittest.mock import MagicMock, patch

import pytest

from stockalert.core.monitor import StockMonitor, TickerState, MonitorStats


class TestTickerState:
    """Tests for TickerState dataclass."""

    def test_ticker_state_defaults(self) -> None:
        """Should have sensible defaults."""
        state = TickerState(
            symbol="AAPL",
            name="Apple Inc.",
            high_threshold=200.0,
            low_threshold=150.0,
        )

        assert state.enabled is True
        assert state.last_price is None
        assert state.last_alert_time is None
        assert state.consecutive_failures == 0


class TestMonitorStats:
    """Tests for MonitorStats dataclass."""

    def test_stats_defaults(self) -> None:
        """Should have zero defaults."""
        stats = MonitorStats()

        assert stats.checks_performed == 0
        assert stats.alerts_sent == 0
        assert stats.api_errors == 0

    def test_uptime_calculation(self) -> None:
        """Should calculate uptime correctly."""
        stats = MonitorStats()
        time.sleep(0.1)

        assert stats.uptime_seconds >= 0.1


class TestStockMonitor:
    """Tests for StockMonitor class."""

    @pytest.fixture
    def mock_config(self) -> MagicMock:
        """Provide a mocked ConfigManager."""
        config = MagicMock()
        config.get_enabled_tickers.return_value = [
            {
                "symbol": "AAPL",
                "name": "Apple Inc.",
                "high_threshold": 200.0,
                "low_threshold": 150.0,
                "enabled": True,
            },
            {
                "symbol": "MSFT",
                "name": "Microsoft Corp.",
                "high_threshold": 450.0,
                "low_threshold": 350.0,
                "enabled": True,
            },
        ]
        config.get.side_effect = lambda key, default=None: {
            "settings.check_interval": 60,
            "settings.cooldown": 300,
        }.get(key, default)
        return config

    @pytest.fixture
    def mock_provider(self) -> MagicMock:
        """Provide a mocked API provider."""
        provider = MagicMock()
        provider.get_price.return_value = 175.0
        return provider

    @pytest.fixture
    def mock_alert_manager(self) -> MagicMock:
        """Provide a mocked AlertManager."""
        return MagicMock()

    @pytest.fixture
    def mock_market_hours(self) -> MagicMock:
        """Provide a mocked MarketHours."""
        market = MagicMock()
        market.is_market_open.return_value = True
        return market

    @pytest.fixture
    def monitor(
        self,
        mock_config: MagicMock,
        mock_provider: MagicMock,
        mock_alert_manager: MagicMock,
        mock_market_hours: MagicMock,
    ) -> StockMonitor:
        """Provide a StockMonitor with mocked dependencies."""
        return StockMonitor(
            config_manager=mock_config,
            provider=mock_provider,
            alert_manager=mock_alert_manager,
            market_hours=mock_market_hours,
            debug=True,  # Skip market hours checks
        )

    def test_monitor_initialization(self, monitor: StockMonitor) -> None:
        """Should initialize with tickers from config."""
        assert monitor.ticker_count == 2
        assert "AAPL" in monitor._tickers
        assert "MSFT" in monitor._tickers

    def test_start_stop(self, monitor: StockMonitor) -> None:
        """Should start and stop monitoring."""
        monitor.start()
        assert monitor.is_running

        monitor.stop()
        assert not monitor.is_running

    def test_reload_tickers(
        self, monitor: StockMonitor, mock_config: MagicMock
    ) -> None:
        """Should reload tickers from config."""
        # Change config to return different tickers
        mock_config.get_enabled_tickers.return_value = [
            {
                "symbol": "GOOGL",
                "name": "Alphabet Inc.",
                "high_threshold": 180.0,
                "low_threshold": 140.0,
                "enabled": True,
            }
        ]

        monitor.reload_tickers()

        assert monitor.ticker_count == 1
        assert "GOOGL" in monitor._tickers
        assert "AAPL" not in monitor._tickers

    def test_get_ticker_state(self, monitor: StockMonitor) -> None:
        """Should return state for specific ticker."""
        state = monitor.get_ticker_state("AAPL")

        assert state is not None
        assert state.symbol == "AAPL"
        assert state.high_threshold == 200.0

    def test_get_ticker_state_not_found(self, monitor: StockMonitor) -> None:
        """Should return None for unknown ticker."""
        state = monitor.get_ticker_state("UNKNOWN")
        assert state is None

    def test_check_ticker_updates_price(
        self,
        monitor: StockMonitor,
        mock_provider: MagicMock,
    ) -> None:
        """Should update last_price after check."""
        state = monitor._tickers["AAPL"]
        assert state.last_price is None

        monitor._check_ticker(state)

        assert state.last_price == 175.0
        mock_provider.get_price.assert_called_with("AAPL")

    def test_check_ticker_high_alert(
        self,
        monitor: StockMonitor,
        mock_provider: MagicMock,
    ) -> None:
        """Should return a high PendingAlert when price exceeds threshold.

        _check_ticker RETURNS a PendingAlert; it does not notify. _check_all_tickers
        collects them and _send_consolidated_alerts does the sending, so several
        tickers crossing in one sweep become one notification instead of five.
        Asserting on alert_manager here (as this test used to) tests the old
        design and fails on the new one while alerting works fine.

        first_check_done is set first because the very first observation of a
        ticker never alerts - price-gap protection, so adding a stock already
        above its threshold does not fire immediately.
        """
        state = monitor._tickers["AAPL"]
        state.first_check_done = True
        mock_provider.get_price.return_value = 250.0  # Above 200 threshold

        alert = monitor._check_ticker(state)

        assert alert is not None
        assert alert.alert_type == "high"
        assert alert.symbol == "AAPL"
        assert alert.price == 250.0

    def test_check_ticker_low_alert(
        self,
        monitor: StockMonitor,
        mock_provider: MagicMock,
    ) -> None:
        """Should return a low PendingAlert when price falls below threshold."""
        state = monitor._tickers["AAPL"]
        state.first_check_done = True
        mock_provider.get_price.return_value = 100.0  # Below 150 threshold

        alert = monitor._check_ticker(state)

        assert alert is not None
        assert alert.alert_type == "low"
        assert alert.symbol == "AAPL"
        assert alert.price == 100.0

    def test_first_check_never_alerts(
        self,
        monitor: StockMonitor,
        mock_provider: MagicMock,
    ) -> None:
        """Price-gap protection: the first observation never alerts."""
        state = monitor._tickers["AAPL"]
        assert not state.first_check_done
        mock_provider.get_price.return_value = 250.0  # Well above threshold

        assert monitor._check_ticker(state) is None
        assert state.first_check_done

        # The second observation at the same price does alert.
        assert monitor._check_ticker(state) is not None

    def test_check_ticker_no_alert_in_range(
        self,
        monitor: StockMonitor,
        mock_provider: MagicMock,
        mock_alert_manager: MagicMock,
    ) -> None:
        """Should not trigger alert when price is in range."""
        mock_provider.get_price.return_value = 175.0  # Between 150 and 200

        state = monitor._tickers["AAPL"]
        monitor._check_ticker(state)

        mock_alert_manager.send_high_alert.assert_not_called()
        mock_alert_manager.send_low_alert.assert_not_called()

    def test_cooldown_prevents_repeated_alerts(
        self,
        monitor: StockMonitor,
        mock_provider: MagicMock,
    ) -> None:
        """Should not alert again inside the cooldown window.

        last_alert_time is stamped by _send_consolidated_alerts, not by
        _check_ticker, so this sets it the way the real dispatch path would.
        """
        state = monitor._tickers["AAPL"]
        state.first_check_done = True
        mock_provider.get_price.return_value = 250.0  # Above threshold

        # First crossing produces an alert
        assert monitor._check_ticker(state) is not None

        # Dispatch stamps the cooldown clock
        state.last_alert_time = time.time()

        # Second crossing inside the window produces nothing
        assert monitor._check_ticker(state) is None

        # Once the window has passed, it alerts again
        cooldown = monitor.config_manager.get("settings.cooldown", 300)
        state.last_alert_time = time.time() - (cooldown + 1)
        assert monitor._check_ticker(state) is not None

    def test_one_alert_per_symbol_per_trading_day(
        self,
        monitor: StockMonitor,
        mock_provider: MagicMock,
    ) -> None:
        """A price parked across its threshold alerts once a day, not every check.

        With a 2-hour interval and a 5-minute cooldown, ALB below its low
        threshold was re-sent on every check. Past the cooldown, the ledger
        still holds it back until the next trading day.
        """
        state = monitor._tickers["AAPL"]
        state.first_check_done = True
        mock_provider.get_price.return_value = 250.0  # Above threshold

        alert = monitor._check_ticker(state)
        assert alert is not None
        monitor._send_consolidated_alerts([alert])

        cooldown = monitor.config_manager.get("settings.cooldown", 300)
        state.last_alert_time = time.time() - (cooldown + 1)
        assert monitor._check_ticker(state) is None

        # The other ticker is unaffected
        msft = monitor._tickers["MSFT"]
        msft.first_check_done = True
        mock_provider.get_price.return_value = 500.0
        assert monitor._check_ticker(msft) is not None

    def test_consecutive_failures_tracking(
        self,
        monitor: StockMonitor,
        mock_provider: MagicMock,
    ) -> None:
        """Should track consecutive API failures."""
        mock_provider.get_price.return_value = None  # Simulated failure

        state = monitor._tickers["AAPL"]

        for _ in range(3):
            monitor._check_ticker(state)

        assert state.consecutive_failures == 3

    def test_success_resets_failures(
        self,
        monitor: StockMonitor,
        mock_provider: MagicMock,
    ) -> None:
        """Should reset failure count on success."""
        state = monitor._tickers["AAPL"]
        state.consecutive_failures = 5

        mock_provider.get_price.return_value = 175.0
        monitor._check_ticker(state)

        assert state.consecutive_failures == 0

    def test_stats_tracking(
        self,
        monitor: StockMonitor,
        mock_provider: MagicMock,
    ) -> None:
        """Should track monitoring statistics."""
        state = monitor._tickers["AAPL"]
        monitor._check_ticker(state)

        assert monitor.stats.checks_performed == 1
