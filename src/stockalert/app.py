"""
Main application orchestrator for StockAlert.

This module coordinates all application components:
- Configuration management
- PyQt6 GUI
- Stock monitoring
- System tray integration
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication

from stockalert.core.alert_manager import AlertManager, AlertSettings
from stockalert.core.config import ConfigManager
from stockalert.core.monitor import StockMonitor
from stockalert.core.windows_service import (
    get_background_process_status,
    stop_background_process,
)
from stockalert.i18n.translator import Translator, set_translator
from stockalert.ui.main_window import MainWindow
from stockalert.ui.tray_icon import TrayIcon
from stockalert.utils.market_hours import MarketHours

if TYPE_CHECKING:
    from stockalert.api.base import BaseProvider

logger = logging.getLogger(__name__)


class StockAlertApp:
    """Main application class coordinating all components."""

    def __init__(
        self,
        config_path: Path | None = None,
        start_minimized: bool = False,
        debug: bool = False,
    ) -> None:
        """Initialize the StockAlert application.

        Args:
            config_path: Path to configuration file. If None, uses default location.
            start_minimized: If True, start minimized to system tray.
            debug: If True, enable debug mode (verbose logging, skip market hours).
        """
        self.debug = debug
        self.start_minimized = start_minimized

        # Clean up any existing background service before starting
        # This ensures we're running the latest code after updates
        self._cleanup_existing_service()

        # Determine application directory
        if getattr(sys, "frozen", False):
            self.app_dir = Path(sys.executable).parent
        else:
            # Resolve to absolute path first, then traverse up from src/stockalert/app.py
            self.app_dir = Path(__file__).resolve().parent.parent.parent

        # Set working directory
        os.chdir(self.app_dir)

        # Initialize configuration
        self.config_path = config_path or self.app_dir / "config.json"
        self.config_manager = ConfigManager(self.config_path)

        # Initialize translator
        language = self.config_manager.get("settings.language", "en")
        self.translator = Translator(
            locales_dir=Path(__file__).parent / "i18n" / "locales"
        )
        self.translator.set_language(language)
        set_translator(self.translator)

        # Initialize components (created later during run)
        self.qt_app: QApplication | None = None
        self.main_window: MainWindow | None = None
        self.tray_icon: TrayIcon | None = None
        self.monitor: StockMonitor | None = None
        self.alert_manager: AlertManager | None = None
        self.market_hours = MarketHours()

        # Monitoring state
        self._monitoring_timer: QTimer | None = None
        self._is_monitoring = False

        logger.info(
            "StockAlert initialized",
            extra={
                "config_path": str(self.config_path),
                "start_minimized": start_minimized,
                "debug": debug,
            },
        )

    def _cleanup_existing_service(self) -> None:
        """Stop any existing background service before starting.

        This ensures we're running the latest code after updates or
        during development when code changes.
        """
        status = get_background_process_status()
        if status.get("running"):
            pid = status.get("pid")
            logger.info(f"Found existing background service (PID: {pid}), stopping it...")
            result = stop_background_process()
            if result == 0:
                logger.info("Successfully stopped existing background service")
            else:
                logger.warning("Failed to stop existing background service")
        else:
            logger.debug("No existing background service found")

    def _setup_api_provider(self) -> BaseProvider:
        """Set up the stock data API provider."""
        from stockalert.api.finnhub import FinnhubProvider

        api_key = os.environ.get("FINNHUB_API_KEY", "")
        if not api_key:
            # Try loading from .env in project root
            from dotenv import load_dotenv

            env_path = self.app_dir / ".env"
            load_dotenv(env_path)
            api_key = os.environ.get("FINNHUB_API_KEY", "")

        if not api_key:
            logger.warning("FINNHUB_API_KEY not set, using demo mode")

        return FinnhubProvider(api_key=api_key)

    def _setup_monitoring(self) -> None:
        """Set up stock monitoring components."""
        provider = self._setup_api_provider()

        icon_path = self.app_dir / "stock_alert.ico"
        alert_settings = self._load_alert_settings()
        self.alert_manager = AlertManager(
            icon_path=icon_path if icon_path.exists() else None,
            translator=self.translator,
            settings=alert_settings,
        )

        self.monitor = StockMonitor(
            config_manager=self.config_manager,
            provider=provider,
            alert_manager=self.alert_manager,
            market_hours=self.market_hours,
            debug=self.debug,
        )

    def _load_alert_settings(self) -> AlertSettings:
        """Load alert settings from configuration."""
        settings = self.config_manager.settings
        alerts_config = settings.get("alerts", {})
        profile = self.config_manager.get("profile", {})

        return AlertSettings(
            windows_enabled=alerts_config.get("windows_enabled", True),
            windows_audio=alerts_config.get("windows_audio", True),
            sms_enabled=alerts_config.get("sms_enabled", False),
            whatsapp_enabled=alerts_config.get("whatsapp_enabled", False),
            email_enabled=alerts_config.get("email_enabled", False),
            phone_number=profile.get("cell", ""),
            email_address=profile.get("email", ""),
        )

    def _setup_ui(self) -> None:
        """Set up the PyQt6 user interface."""
        self.main_window = MainWindow(
            config_manager=self.config_manager,
            translator=self.translator,
            on_settings_changed=self._on_settings_changed,
        )

        icon_path = self.app_dir / "stock_alert.ico"
        self.tray_icon = TrayIcon(
            main_window=self.main_window,
            icon_path=icon_path if icon_path.exists() else None,
            translator=self.translator,
            on_quit=self._on_quit,
            on_toggle_monitoring=self._on_toggle_monitoring,
        )

    def _on_settings_changed(self) -> None:
        """Handle settings changes from the UI."""
        logger.info("Settings changed, reloading configuration")
        self.config_manager.reload()

        # Update language if changed
        new_language = self.config_manager.get("settings.language", "en")
        if new_language != self.translator.current_language:
            self.translator.set_language(new_language)
            if self.main_window:
                self.main_window.retranslate_ui()
            if self.tray_icon:
                self.tray_icon.update_menu()

        # Update alert settings
        if self.alert_manager:
            new_settings = self._load_alert_settings()
            self.alert_manager.update_settings(new_settings)

        # Restart monitoring with new settings
        if self._is_monitoring and self.monitor:
            self.monitor.reload_tickers()

    def _on_toggle_monitoring(self, enabled: bool) -> None:
        """Handle monitoring toggle from tray menu."""
        if enabled:
            self.start_monitoring()
        else:
            self.stop_monitoring()

    def _on_quit(self) -> None:
        """Handle application quit."""
        logger.info("Application quit requested")
        self.stop_monitoring()
        if self.qt_app:
            self.qt_app.quit()

    def start_monitoring(self) -> None:
        """Start stock price monitoring."""
        if self._is_monitoring:
            return

        if not self.monitor:
            self._setup_monitoring()

        logger.info("Starting stock monitoring")
        self._is_monitoring = True

        if self.monitor:
            self.monitor.start()

        if self.tray_icon:
            self.tray_icon.set_monitoring_state(True)

    def stop_monitoring(self) -> None:
        """Stop stock price monitoring."""
        if not self._is_monitoring:
            return

        logger.info("Stopping stock monitoring")
        self._is_monitoring = False

        if self.monitor:
            self.monitor.stop()

        if self.tray_icon:
            self.tray_icon.set_monitoring_state(False)

    def run(self) -> int:
        """Run the application.

        Returns:
            Exit code (0 for success).
        """
        # Create Qt application
        self.qt_app = QApplication(sys.argv)
        self.qt_app.setApplicationName("StockAlert")
        self.qt_app.setApplicationVersion("3.0.0")
        self.qt_app.setOrganizationName("RC Software")
        self.qt_app.setQuitOnLastWindowClosed(False)

        # Set up components
        self._setup_monitoring()
        self._setup_ui()

        # Start monitoring automatically
        self.start_monitoring()

        # Show window or minimize to tray
        if self.start_minimized:
            if self.tray_icon:
                self.tray_icon.show()
            logger.info("Started minimized to system tray")
        else:
            if self.main_window:
                self.main_window.showMaximized()
            if self.tray_icon:
                self.tray_icon.show()

        # Run event loop
        return self.qt_app.exec()
