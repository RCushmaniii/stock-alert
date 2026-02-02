"""
Headless monitoring service for StockAlert.

This module provides a standalone monitoring process that runs independently
of the GUI. It can be run directly, as a Windows Service, or via Task Scheduler.

Usage:
    python -m stockalert.service          # Run in foreground
    python -m stockalert.service --install # Install as Windows Service
    python -m stockalert.service --remove  # Remove Windows Service
"""

from __future__ import annotations

import argparse
import logging
import os
import signal
import sys
import time
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING, Any

from stockalert.core.alert_manager import AlertManager, AlertSettings
from stockalert.core.api_key_manager import provision_stockalert_api_key
from stockalert.core.config import ConfigManager
from stockalert.core.monitor import StockMonitor
from stockalert.core.paths import get_app_dir, get_bundled_assets_dir, get_config_path, migrate_config_if_needed
from stockalert.i18n.translator import Translator, set_translator
from stockalert.utils.logging_config import setup_logging
from stockalert.utils.market_hours import MarketHours

if TYPE_CHECKING:
    from stockalert.api.base import BaseProvider

logger = logging.getLogger(__name__)


class StockAlertService:
    """Headless stock monitoring service."""

    SERVICE_NAME = "StockAlertService"
    SERVICE_DISPLAY_NAME = "StockAlert Monitoring Service"
    SERVICE_DESCRIPTION = "Monitors stock prices and sends alerts via Windows notifications, WhatsApp, and email."

    def __init__(self, config_path: Path | None = None, debug: bool = False) -> None:
        """Initialize the service.

        Args:
            config_path: Path to configuration file
            debug: Enable debug mode (skip market hours)
        """
        self.debug = debug
        self._running = False
        self._config_mtime: float = 0

        # Determine application directory (where exe/assets are)
        self.app_dir = get_app_dir()

        # Migrate config from old location if needed (handles upgrades)
        migrate_config_if_needed()

        # Initialize configuration (stored in AppData for persistence)
        self.config_path = config_path or get_config_path()
        self.config_manager = ConfigManager(self.config_path)

        # Auto-provision WhatsApp backend API key (transparent to user)
        provision_stockalert_api_key()

        # Initialize translator
        language = self.config_manager.get("settings.language", "en")
        self.translator = Translator(
            locales_dir=Path(__file__).parent / "i18n" / "locales"
        )
        self.translator.set_language(language)
        set_translator(self.translator)

        # Components
        self.monitor: StockMonitor | None = None
        self.alert_manager: AlertManager | None = None
        self.market_hours = MarketHours()

        logger.info(
            f"StockAlert Service initialized (config: {self.config_path})"
        )

    def _load_env(self) -> None:
        """Load environment variables from .env file."""
        from dotenv import load_dotenv

        env_path = self.app_dir / ".env"
        if env_path.exists():
            load_dotenv(env_path)
            logger.debug(f"Loaded environment from {env_path}")

    def _setup_api_provider(self) -> BaseProvider:
        """Set up the stock data API provider."""
        from stockalert.api.finnhub import FinnhubProvider
        from stockalert.core.api_key_manager import get_api_key

        # Try to get API key from secure storage first
        api_key = get_api_key()

        if not api_key:
            # Fallback to environment variable
            self._load_env()
            api_key = os.environ.get("FINNHUB_API_KEY", "")

        if not api_key:
            logger.warning("FINNHUB_API_KEY not set, using demo mode")

        return FinnhubProvider(api_key=api_key)

    def _setup_alert_manager(self) -> AlertManager:
        """Set up the alert manager with current settings."""
        settings = self.config_manager.settings
        alerts_config = settings.get("alerts", {})
        profile = self.config_manager.get("profile", {})

        alert_settings = AlertSettings(
            windows_enabled=alerts_config.get("windows_enabled", True),
            windows_audio=alerts_config.get("windows_audio", True),
            sms_enabled=alerts_config.get("sms_enabled", False),
            whatsapp_enabled=alerts_config.get("whatsapp_enabled", False),
            email_enabled=alerts_config.get("email_enabled", False),
            phone_number=profile.get("cell", ""),
            email_address=profile.get("email", ""),
        )

        # Icon is bundled with the app (in _MEIPASS for PyInstaller)
        icon_path = get_bundled_assets_dir() / "stock_alert.ico"
        return AlertManager(
            icon_path=icon_path if icon_path.exists() else None,
            translator=self.translator,
            settings=alert_settings,
        )

    def _setup_monitoring(self) -> None:
        """Set up stock monitoring components."""
        provider = self._setup_api_provider()
        self.alert_manager = self._setup_alert_manager()

        self.monitor = StockMonitor(
            config_manager=self.config_manager,
            provider=provider,
            alert_manager=self.alert_manager,
            market_hours=self.market_hours,
            debug=self.debug,
        )

    def _check_config_changes(self) -> bool:
        """Check if config file has been modified.

        Returns:
            True if config was reloaded
        """
        try:
            current_mtime = self.config_path.stat().st_mtime
            if current_mtime > self._config_mtime:
                self._config_mtime = current_mtime
                return True
        except OSError:
            pass
        return False

    def _reload_config(self) -> None:
        """Reload configuration and update components."""
        logger.info("Configuration file changed, reloading...")
        self.config_manager.reload()

        # Update language
        new_language = self.config_manager.get("settings.language", "en")
        if new_language != self.translator.current_language:
            self.translator.set_language(new_language)

        # Update alert settings
        if self.alert_manager:
            settings = self.config_manager.settings
            alerts_config = settings.get("alerts", {})
            profile = self.config_manager.get("profile", {})

            new_settings = AlertSettings(
                windows_enabled=alerts_config.get("windows_enabled", True),
                windows_audio=alerts_config.get("windows_audio", True),
                sms_enabled=alerts_config.get("sms_enabled", False),
                whatsapp_enabled=alerts_config.get("whatsapp_enabled", False),
                email_enabled=alerts_config.get("email_enabled", False),
                phone_number=profile.get("cell", ""),
                email_address=profile.get("email", ""),
            )
            self.alert_manager.update_settings(new_settings)

        # Reload tickers
        if self.monitor:
            self.monitor.reload_tickers()

        logger.info("Configuration reloaded successfully")

    def start(self) -> None:
        """Start the monitoring service."""
        if self._running:
            logger.warning("Service already running")
            return

        logger.info("Starting StockAlert monitoring service...")
        self._running = True

        # Set up components
        self._setup_monitoring()

        # Record initial config mtime
        try:
            self._config_mtime = self.config_path.stat().st_mtime
        except OSError:
            self._config_mtime = 0

        # Start monitoring
        if self.monitor:
            self.monitor.start()

        # Send startup notification
        if self.alert_manager:
            ticker_count = self.monitor.ticker_count if self.monitor else 0
            status = self.market_hours.get_market_status_message()
            self.alert_manager.send_info(
                title=self.translator.get("alerts.started.title"),
                message=self.translator.get(
                    "alerts.started.message",
                    count=ticker_count,
                    status=status,
                ),
            )

        logger.info(
            f"Service started, monitoring {self.monitor.ticker_count if self.monitor else 0} tickers"
        )

    def stop(self) -> None:
        """Stop the monitoring service."""
        if not self._running:
            return

        logger.info("Stopping StockAlert monitoring service...")
        self._running = False

        if self.monitor:
            self.monitor.stop()

        logger.info("Service stopped")

    def run_forever(self) -> None:
        """Run the service until stopped.

        This is the main loop for foreground execution.
        Checks for config changes and handles graceful shutdown.
        """
        self.start()

        # Config check interval (seconds) - check once per minute
        config_check_interval = 60

        try:
            while self._running:
                # Check for config changes
                if self._check_config_changes():
                    self._reload_config()

                time.sleep(config_check_interval)

        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
        finally:
            self.stop()

    @property
    def is_running(self) -> bool:
        """Check if service is running."""
        return self._running


def create_signal_handler(service: StockAlertService) -> Callable[[int, Any], None]:
    """Create a signal handler for graceful shutdown."""
    def handler(signum: int, frame: Any) -> None:
        logger.info(f"Received signal {signum}, shutting down...")
        service.stop()
        sys.exit(0)
    return handler


def run_foreground(config_path: Path | None = None, debug: bool = False) -> int:
    """Run the service in foreground mode.

    Uses Global Mutex for single-instance guarantee and Named Pipe for IPC.

    Args:
        config_path: Path to configuration file
        debug: Enable debug mode

    Returns:
        Exit code
    """
    from stockalert.core.ipc import ServiceMutex, NamedPipeServer

    # 1. Try to acquire the Global Mutex (single instance check)
    mutex = ServiceMutex()
    if not mutex.acquire():
        logger.warning("Another service instance is already running (mutex held). Exiting.")
        print("StockAlert service is already running.")
        return 1

    logger.info(f"Service starting (PID: {os.getpid()})")

    service: StockAlertService | None = None
    pipe_server: NamedPipeServer | None = None

    try:
        # 2. Create the service
        service = StockAlertService(config_path=config_path, debug=debug)

        # 3. Define command handler for IPC (simple string-based protocol)
        def handle_command(command: str) -> str:
            """Handle commands from the Frontend. Returns response string."""
            import json

            if command == "PING":
                return "PONG"

            elif command == "STATUS":
                status = {
                    "pid": os.getpid(),
                    "running": service.is_running if service else False,
                    "ticker_count": service.monitor.ticker_count if service and service.monitor else 0,
                }
                return json.dumps(status)

            elif command == "RELOAD_SETTINGS":
                if service:
                    service._reload_config()
                return "SUCCESS: Settings reloaded"

            elif command == "STOP":
                if service:
                    service.stop()
                return "SUCCESS: Stopping"

            else:
                return f"UNKNOWN: {command}"

        # 4. Start the Named Pipe server for IPC
        pipe_server = NamedPipeServer(on_command=handle_command)
        pipe_server.start()

        # 5. Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, create_signal_handler(service))
        signal.signal(signal.SIGTERM, create_signal_handler(service))

        # 6. Run the monitoring service
        service.run_forever()
        return 0

    finally:
        # Clean up
        if pipe_server:
            pipe_server.stop()
        mutex.release()
        logger.info("Service cleanup complete")


def main() -> int:
    """Main entry point for the service."""
    parser = argparse.ArgumentParser(
        description="StockAlert Monitoring Service",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python -m stockalert.service              # Run in foreground
    python -m stockalert.service --debug      # Run with debug mode
    python -m stockalert.service --install    # Install as Windows Service
    python -m stockalert.service --remove     # Remove Windows Service
    python -m stockalert.service --start      # Start Windows Service
    python -m stockalert.service --stop       # Stop Windows Service
        """,
    )
    parser.add_argument(
        "--config",
        type=Path,
        help="Path to configuration file",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode (skip market hours checks)",
    )
    parser.add_argument(
        "--install",
        action="store_true",
        help="Install as Windows Service",
    )
    parser.add_argument(
        "--remove",
        action="store_true",
        help="Remove Windows Service",
    )
    parser.add_argument(
        "--start",
        action="store_true",
        help="Start the Windows Service",
    )
    parser.add_argument(
        "--stop",
        action="store_true",
        help="Stop the Windows Service",
    )

    args = parser.parse_args()

    # Set up logging
    setup_logging(debug=args.debug, log_file="stockalert_service.log")

    # Handle Windows Service commands
    if args.install:
        from stockalert.core.windows_service import install_service
        return install_service()
    elif args.remove:
        from stockalert.core.windows_service import remove_service
        return remove_service()
    elif args.start:
        from stockalert.core.windows_service import start_service
        return start_service()
    elif args.stop:
        from stockalert.core.windows_service import stop_service
        return stop_service()

    # Run in foreground
    return run_foreground(config_path=args.config, debug=args.debug)


if __name__ == "__main__":
    sys.exit(main())
