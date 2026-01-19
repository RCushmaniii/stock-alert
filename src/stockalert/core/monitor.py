"""
Stock price monitoring for StockAlert.

Handles the monitoring loop, threshold checking, and coordination
with the API provider and alert manager.
"""

from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from stockalert.api.base import BaseProvider
    from stockalert.core.alert_manager import AlertManager
    from stockalert.core.config import ConfigManager
    from stockalert.utils.market_hours import MarketHours

logger = logging.getLogger(__name__)


@dataclass
class TickerState:
    """State tracking for a monitored ticker."""

    symbol: str
    name: str
    high_threshold: float
    low_threshold: float
    enabled: bool = True
    last_price: float | None = None
    last_alert_time: float | None = None
    consecutive_failures: int = 0


@dataclass
class MonitorStats:
    """Statistics for the monitoring session."""

    checks_performed: int = 0
    alerts_sent: int = 0
    api_errors: int = 0
    start_time: float = field(default_factory=time.time)

    @property
    def uptime_seconds(self) -> float:
        """Get monitoring uptime in seconds."""
        return time.time() - self.start_time


class StockMonitor:
    """Monitors stock prices and triggers alerts based on thresholds."""

    MAX_CONSECUTIVE_FAILURES = 5
    SLEEP_CHUNK_SECONDS = 60

    def __init__(
        self,
        config_manager: ConfigManager,
        provider: BaseProvider,
        alert_manager: AlertManager,
        market_hours: MarketHours,
        debug: bool = False,
    ) -> None:
        """Initialize the stock monitor.

        Args:
            config_manager: Configuration manager instance
            provider: Stock data API provider
            alert_manager: Alert/notification manager
            market_hours: Market hours utility
            debug: If True, skip market hours checks
        """
        self.config_manager = config_manager
        self.provider = provider
        self.alert_manager = alert_manager
        self.market_hours = market_hours
        self.debug = debug

        self._tickers: dict[str, TickerState] = {}
        self._running = False
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._stats = MonitorStats()

        self._load_tickers()

    def _load_tickers(self) -> None:
        """Load tickers from configuration."""
        self._tickers.clear()
        for ticker_config in self.config_manager.get_enabled_tickers():
            symbol = ticker_config["symbol"].upper()
            self._tickers[symbol] = TickerState(
                symbol=symbol,
                name=ticker_config.get("name", symbol),
                high_threshold=ticker_config["high_threshold"],
                low_threshold=ticker_config["low_threshold"],
                enabled=ticker_config.get("enabled", True),
            )
        logger.info(f"Loaded {len(self._tickers)} tickers for monitoring")

    def reload_tickers(self) -> None:
        """Reload tickers from configuration without stopping monitoring."""
        logger.info("Reloading tickers")
        old_tickers = set(self._tickers.keys())
        self._load_tickers()
        new_tickers = set(self._tickers.keys())

        added = new_tickers - old_tickers
        removed = old_tickers - new_tickers
        if added:
            logger.info(f"Added tickers: {added}")
        if removed:
            logger.info(f"Removed tickers: {removed}")

    def start(self) -> None:
        """Start the monitoring loop in a background thread."""
        if self._running:
            logger.warning("Monitor already running")
            return

        self._running = True
        self._stop_event.clear()
        self._stats = MonitorStats()

        self._thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self._thread.start()
        logger.info("Stock monitoring started")

    def stop(self) -> None:
        """Stop the monitoring loop."""
        if not self._running:
            return

        logger.info("Stopping stock monitoring")
        self._running = False
        self._stop_event.set()

        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5.0)

    def _monitoring_loop(self) -> None:
        """Main monitoring loop - runs in background thread."""
        while self._running and not self._stop_event.is_set():
            try:
                # Check market hours unless in debug mode
                if not self.debug and not self.market_hours.is_market_open():
                    self._wait_for_market_open()
                    continue

                # Check all tickers
                self._check_all_tickers()

                # Sleep for check interval
                check_interval = self.config_manager.get("settings.check_interval", 60)
                self._interruptible_sleep(check_interval)

            except Exception as e:
                logger.exception(f"Error in monitoring loop: {e}")
                self._stats.api_errors += 1
                self._interruptible_sleep(60)

    def _wait_for_market_open(self) -> None:
        """Wait until market opens."""
        seconds_until_open = self.market_hours.seconds_until_market_open()
        status = self.market_hours.get_market_status_message()
        logger.info(f"Market closed: {status}. Waiting {seconds_until_open // 3600}h")

        # Sleep in chunks to allow for clean shutdown
        self._interruptible_sleep(seconds_until_open)

    def _interruptible_sleep(self, seconds: float) -> None:
        """Sleep for specified duration, checking for stop events."""
        elapsed = 0.0
        while elapsed < seconds and self._running and not self._stop_event.is_set():
            chunk = min(self.SLEEP_CHUNK_SECONDS, seconds - elapsed)
            self._stop_event.wait(timeout=chunk)
            elapsed += chunk

    def _check_all_tickers(self) -> None:
        """Check prices for all enabled tickers."""
        for symbol, state in self._tickers.items():
            if not self._running or self._stop_event.is_set():
                break

            if not state.enabled:
                continue

            self._check_ticker(state)

    def _check_ticker(self, state: TickerState) -> None:
        """Check a single ticker's price against thresholds."""
        try:
            price = self.provider.get_price(state.symbol)
            self._stats.checks_performed += 1

            if price is None:
                state.consecutive_failures += 1
                if state.consecutive_failures >= self.MAX_CONSECUTIVE_FAILURES:
                    logger.warning(
                        f"[{state.symbol}] Failed to fetch price "
                        f"{self.MAX_CONSECUTIVE_FAILURES} consecutive times"
                    )
                    state.consecutive_failures = 0
                return

            # Reset failure counter on success
            state.consecutive_failures = 0
            state.last_price = price

            logger.debug(f"{state.symbol}: ${price:.2f}")

            # Check thresholds
            self._check_thresholds(state, price)

        except Exception as e:
            logger.exception(f"Error checking {state.symbol}: {e}")
            self._stats.api_errors += 1

    def _check_thresholds(self, state: TickerState, price: float) -> None:
        """Check if price crosses any thresholds."""
        cooldown = self.config_manager.get("settings.cooldown", 300)

        # Check if we're in cooldown period
        if state.last_alert_time is not None:
            time_since_alert = time.time() - state.last_alert_time
            if time_since_alert < cooldown:
                return

        # Check high threshold
        if price >= state.high_threshold:
            logger.info(
                f"{state.symbol} HIGH ALERT: ${price:.2f} >= ${state.high_threshold:.2f}"
            )
            self.alert_manager.send_high_alert(
                symbol=state.symbol,
                name=state.name,
                price=price,
                threshold=state.high_threshold,
            )
            state.last_alert_time = time.time()
            self._stats.alerts_sent += 1

        # Check low threshold
        elif price <= state.low_threshold:
            logger.info(
                f"{state.symbol} LOW ALERT: ${price:.2f} <= ${state.low_threshold:.2f}"
            )
            self.alert_manager.send_low_alert(
                symbol=state.symbol,
                name=state.name,
                price=price,
                threshold=state.low_threshold,
            )
            state.last_alert_time = time.time()
            self._stats.alerts_sent += 1

    @property
    def is_running(self) -> bool:
        """Check if monitoring is currently active."""
        return self._running

    @property
    def stats(self) -> MonitorStats:
        """Get monitoring statistics."""
        return self._stats

    @property
    def ticker_count(self) -> int:
        """Get number of monitored tickers."""
        return len(self._tickers)

    def get_ticker_state(self, symbol: str) -> TickerState | None:
        """Get state for a specific ticker."""
        return self._tickers.get(symbol.upper())

    def get_all_states(self) -> dict[str, TickerState]:
        """Get state for all tickers."""
        return self._tickers.copy()
