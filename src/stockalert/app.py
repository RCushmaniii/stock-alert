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
from PyQt6.QtWidgets import QApplication, QDialog

from stockalert.core.alert_manager import AlertManager, AlertSettings
from stockalert.core.api_key_manager import provision_stockalert_api_key
from stockalert.core.config import ConfigManager
from stockalert.core.monitor import StockMonitor
from stockalert.core.paths import get_app_dir, get_bundled_assets_dir, get_config_path, migrate_config_if_needed
from stockalert.core.windows_service import get_background_process_status
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

        # Check for existing background service
        # In production: connect to it (don't stop it)
        # In development: optionally stop it to run latest code
        self._background_service_running = False
        status = get_background_process_status()
        if status.get("running"):
            self._background_service_running = True
            pid = status.get("pid")
            logger.info(f"Found existing background service (PID: {pid}), will connect to it")

        # Determine application directory (where exe/assets are)
        self.app_dir = get_app_dir()

        # Set working directory
        os.chdir(self.app_dir)

        # Migrate config from old location if needed (handles upgrades)
        migrate_config_if_needed()

        # Initialize configuration (stored in AppData for persistence)
        self.config_path = config_path or get_config_path()
        self.config_manager = ConfigManager(self.config_path)

        # Auto-provision WhatsApp backend API key (transparent to user)
        provision_stockalert_api_key()

        # Initialize translator (locales_dir auto-detected by Translator)
        language = self.config_manager.get("settings.language", "en")
        logger.info(f"Config language value: '{language}'")
        self.translator = Translator()
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


    def _setup_api_provider(self) -> BaseProvider:
        """Set up the stock data API provider."""
        from stockalert.api.finnhub import FinnhubProvider
        from stockalert.core.api_key_manager import get_api_key

        # Try to get API key from secure storage first
        api_key = get_api_key()

        if not api_key:
            # Fallback to environment variable
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

        # Icon is bundled with the app (in _MEIPASS for PyInstaller)
        icon_path = get_bundled_assets_dir() / "stock_alert.ico"
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

    def _create_app_icon(self) -> QIcon:
        """Create a branded app icon programmatically."""
        from PyQt6.QtCore import Qt
        from PyQt6.QtGui import QPixmap, QPainter, QColor, QPen, QIcon
        
        # Create 64x64 pixmap with solid orange background
        pixmap = QPixmap(64, 64)
        pixmap.fill(QColor("#FF6A3D"))
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw white trend line
        painter.setPen(QPen(Qt.GlobalColor.white, 4))
        painter.drawLine(12, 48, 28, 24)
        painter.drawLine(28, 24, 52, 40)
        
        painter.end()
        return QIcon(pixmap)

    def _setup_ui(self) -> None:
        """Set up the PyQt6 user interface."""
        self.main_window = MainWindow(
            config_manager=self.config_manager,
            translator=self.translator,
            on_settings_changed=self._on_settings_changed,
        )

        # Icon is bundled with the app (in _MEIPASS for PyInstaller)
        icon_path = get_bundled_assets_dir() / "stock_alert.ico"
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
        """Start stock price monitoring.

        Will skip if background service is already running to prevent duplicates.
        """
        if self._is_monitoring:
            return

        # Check if background service is already running
        from stockalert.core.windows_service import get_background_process_status
        bg_status = get_background_process_status()
        if bg_status.get("running"):
            pid = bg_status.get("pid", "?")
            logger.info(f"Background service already running (PID: {pid}), skipping embedded monitoring")
            # Update tray to show monitoring is active (via background service)
            if self.tray_icon:
                self.tray_icon.set_monitoring_state(True)
            return

        if not self.monitor:
            self._setup_monitoring()

        logger.info("Starting stock monitoring (embedded mode)")
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
        # These fix the "Python" text in the taskbar right-click menu
        self.qt_app.setApplicationName("StockAlert")
        self.qt_app.setApplicationDisplayName("StockAlert")
        self.qt_app.setApplicationVersion("3.0.0")
        self.qt_app.setOrganizationName("CushLabs")
        self.qt_app.setOrganizationDomain("cushlabs.ai")
        self.qt_app.setQuitOnLastWindowClosed(False)
        
        # Set application-wide icon (affects taskbar)
        # Use programmatic icon to ensure consistent orange branding
        self.qt_app.setWindowIcon(self._create_app_icon())
        logger.info("Set taskbar icon (programmatic orange)")

        # Set up components FIRST (before any dialogs)
        self._setup_monitoring()
        self._setup_ui()

        # Explicitly brand the main window (Windows sometimes ignores global app icon)
        if self.main_window:
            self.main_window.setWindowIcon(self._create_app_icon())
            logger.info("Set main window icon explicitly")

        # Show window or minimize to tray
        if self.start_minimized:
            if self.tray_icon:
                self.tray_icon.show()
            logger.info("Started minimized to system tray")
        else:
            if self.main_window:
                self.main_window.showMaximized()
                self.main_window.raise_()
                self.main_window.activateWindow()
            if self.tray_icon:
                self.tray_icon.show()

        # Now check for startup warnings/prompts (after UI is visible)
        # Use timer to show dialogs after window is fully displayed
        QTimer.singleShot(300, self._show_startup_dialogs)

        # Run event loop
        return int(self.qt_app.exec())

    def _show_startup_dialogs(self) -> None:
        """Show any startup dialogs after window is displayed."""
        try:
            # Check if config was recovered from corruption
            if self.config_manager.was_recovered:
                self._show_config_recovery_warning()

            # Check if this is a first-time user (show onboarding regardless of API key)
            onboarding_completed = self.config_manager.get("app.onboarding_completed", False)
            if not onboarding_completed:
                logger.info("First-time user detected, showing onboarding dialog")
                self._show_onboarding_dialog()

            # Check for API key
            api_key_valid = self._validate_api_key_on_startup()

            if api_key_valid:
                # Start monitoring now that we know key is valid
                self.start_monitoring()
            else:
                logger.warning("Monitoring not started - API key not configured")
                # Only prompt if onboarding was already completed (returning user without key)
                if onboarding_completed:
                    self._prompt_for_api_key()
        except Exception as e:
            logger.exception(f"Error in startup dialogs: {e}")

    def _validate_api_key_on_startup(self) -> bool:
        """Validate API key on startup.

        Returns:
            True if API key is valid, False otherwise
        """
        try:
            from stockalert.core.api_key_manager import get_api_key, has_api_key

            if not has_api_key():
                logger.warning("No API key configured")
                return False

            api_key = get_api_key()
            if not api_key:
                return False

            # Key exists - assume it's valid (don't test on startup to avoid delays)
            logger.info("API key found")
            return True

        except Exception as e:
            logger.exception(f"Error checking API key: {e}")
            return False

    def _show_config_recovery_warning(self) -> None:
        """Show warning dialog that config was recovered from corruption."""
        from PyQt6.QtWidgets import QMessageBox

        QMessageBox.warning(
            self.main_window,
            "Configuration Recovered",
            "Your configuration file was corrupted and has been reset to defaults.\n\n"
            "A backup of the corrupted file was saved.\n\n"
            "Please re-enter your settings and API key.",
        )

    def _show_onboarding_dialog(self) -> None:
        """Show onboarding dialog for first-time users."""
        try:
            from stockalert.ui.dialogs.onboarding_dialog import OnboardingDialog

            dialog = OnboardingDialog(self.main_window)
            result = dialog.exec()

            # Mark onboarding as completed regardless of button clicked
            self.config_manager.set("app.onboarding_completed", True, save=True)

            if result == QDialog.DialogCode.Accepted and self.main_window:
                # User clicked "Get Started" - go to Profile tab first
                if hasattr(self.main_window, 'tabs'):
                    self.main_window.tabs.setCurrentIndex(0)  # Profile tab
        except Exception as e:
            logger.exception(f"Error showing onboarding dialog: {e}")

    def _prompt_for_api_key(self) -> None:
        """Prompt user to enter API key (for returning users without key)."""
        try:
            from PyQt6.QtWidgets import QMessageBox
            from stockalert.i18n.translator import _

            result = QMessageBox.information(
                self.main_window,
                _("onboarding.step2_title"),
                _("onboarding.step2_desc") + "\n\n" +
                "Click OK to open Settings and enter your key.",
                QMessageBox.StandardButton.Ok,
            )

            if result == QMessageBox.StandardButton.Ok and self.main_window:
                # Switch to settings tab
                if hasattr(self.main_window, 'tabs'):
                    self.main_window.tabs.setCurrentIndex(1)  # Settings tab
        except Exception as e:
            logger.exception(f"Error in API key prompt: {e}")
