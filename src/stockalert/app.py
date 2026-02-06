"""
Main application orchestrator for StockAlert.

This module coordinates all application components:
- Configuration management
- PyQt6 GUI
- System tray integration

ARCHITECTURE NOTE:
The GUI is a PURE FRONTEND. It does NOT do any stock monitoring itself.
All monitoring is done by the background service (service.py).
The GUI communicates with the service via IPC (Named Pipes).
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication, QDialog

from stockalert.core.api_key_manager import provision_stockalert_api_key
from stockalert.core.config import ConfigManager
from stockalert.core.ipc import is_service_running, get_service_status, send_reload_config, GUIPipeServer
from stockalert.core.paths import get_app_dir, get_bundled_assets_dir, get_config_path, migrate_config_if_needed
from stockalert.core.windows_service import get_background_process_status, start_background_process
from stockalert.i18n.translator import Translator, set_translator
from stockalert.ui.main_window import MainWindow
from stockalert.ui.tray_icon import TrayIcon
from stockalert.utils.market_hours import MarketHours

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class StockAlertApp:
    """Main application class coordinating all components.

    IMPORTANT: This GUI is a PURE FRONTEND. It does NOT do any stock monitoring.
    All monitoring is delegated to the background service (service.py).
    """

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

        # Initialize UI components (created later during run)
        self.qt_app: QApplication | None = None
        self.main_window: MainWindow | None = None
        self.tray_icon: TrayIcon | None = None
        self.market_hours = MarketHours()

        # Service status polling timer
        self._status_timer: QTimer | None = None

        # GUI IPC server for handling SHOW_WINDOW from second instances
        self._gui_pipe_server: GUIPipeServer | None = None

        logger.info(
            "StockAlert GUI initialized",
            extra={
                "config_path": str(self.config_path),
                "start_minimized": start_minimized,
                "debug": debug,
            },
        )


    def _ensure_service_running(self) -> bool:
        """Ensure the background service is running.

        The service runs automatically - users don't need to configure this.
        This is the "it just works" approach.

        Returns:
            True if service is running (or was started successfully)
        """
        # Check if service is already running
        if is_service_running():
            logger.info("Background service is already running")
            return True

        # Auto-start the background service
        logger.info("Auto-starting background service...")
        pid = start_background_process()
        if pid > 0:
            logger.info(f"Background service started (PID: {pid})")
            return True
        else:
            logger.error("Failed to start background service")
            return False

    def _update_service_status(self) -> None:
        """Update tray icon with current service status."""
        try:
            status = get_service_status()
            running = status.get("running", False)
            ticker_count = status.get("ticker_count", 0)

            if self.tray_icon:
                self.tray_icon.set_monitoring_state(running)
                self.tray_icon.set_ticker_count(ticker_count)

                # Update market status
                market_status = self.market_hours.get_market_status_message()
                self.tray_icon.set_market_status(market_status)

        except Exception as e:
            logger.debug(f"Error updating service status: {e}")

    def _create_app_icon(self) -> QIcon:
        """Load the branded app icon from the .ico file.

        Falls back to a programmatic orange icon if the .ico file is missing.
        """
        from PyQt6.QtCore import Qt, QSize
        from PyQt6.QtGui import QPixmap, QPainter, QColor, QPen

        ico_path = get_bundled_assets_dir() / "stock_alert.ico"
        if ico_path.exists():
            icon = QIcon(str(ico_path))
            sizes = icon.availableSizes()
            if not icon.isNull() and len(sizes) > 0:
                logger.info(f"Loaded app icon from {ico_path}, sizes={sizes}")
                return icon

            # Fallback: load as QPixmap at specific sizes
            logger.info("QIcon(path) returned no sizes, loading via QPixmap")
            icon = QIcon()
            for size in [16, 32, 48, 64, 128, 256]:
                pixmap = QPixmap(str(ico_path))
                if not pixmap.isNull():
                    scaled = pixmap.scaled(
                        QSize(size, size),
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation,
                    )
                    icon.addPixmap(scaled)
            if not icon.isNull():
                logger.info(f"Loaded app icon via QPixmap scaling, sizes={icon.availableSizes()}")
                return icon
            logger.warning("QPixmap also failed to load .ico")

        # Fallback: programmatic orange icon
        logger.info("Using fallback programmatic icon")
        icon = QIcon()
        for size in [16, 24, 32, 48, 64, 128, 256]:
            pixmap = QPixmap(size, size)
            pixmap.fill(QColor("#FF6A3D"))
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            scale = size / 64.0
            pen_width = max(1, int(4 * scale))
            painter.setPen(QPen(Qt.GlobalColor.white, pen_width))
            x1, y1 = int(12 * scale), int(48 * scale)
            x2, y2 = int(28 * scale), int(24 * scale)
            x3, y3 = int(52 * scale), int(40 * scale)
            painter.drawLine(x1, y1, x2, y2)
            painter.drawLine(x2, y2, x3, y3)
            painter.end()
            icon.addPixmap(pixmap)
        return icon

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
        """Handle settings changes from the UI.

        This reloads local config for UI updates and tells the
        background service to reload its config via IPC.
        """
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

        # Tell the background service to reload its config via IPC
        if is_service_running():
            logger.info("Sending RELOAD_SETTINGS command to background service")
            success = send_reload_config()
            if success:
                logger.info("Background service acknowledged config reload")
            else:
                logger.warning("Failed to send reload command to service")

        # Update service status display
        self._update_service_status()

    def _on_toggle_monitoring(self, enabled: bool) -> None:
        """Handle monitoring toggle from tray menu.

        NOTE: The GUI doesn't do monitoring. This just starts/stops the service.
        """
        if enabled:
            self._start_service()
        else:
            self._stop_service()

    def _on_quit(self) -> None:
        """Handle application quit.

        NOTE: Quitting the GUI does NOT stop the background service.
        The service continues monitoring independently.
        """
        logger.info("GUI quit requested (service continues running)")
        if self._status_timer:
            self._status_timer.stop()
        if self.qt_app:
            self.qt_app.quit()

    def _start_service(self) -> None:
        """Start the background monitoring service."""
        if is_service_running():
            logger.info("Service already running")
            self._update_service_status()
            return

        logger.info("Starting background service from GUI")
        pid = start_background_process()
        if pid > 0:
            logger.info(f"Background service started (PID: {pid})")
        else:
            logger.error("Failed to start background service")

        # Update status after a brief delay to let service start
        QTimer.singleShot(1000, self._update_service_status)

    def _stop_service(self) -> None:
        """Stop the background monitoring service."""
        from stockalert.core.ipc import send_stop_service

        if not is_service_running():
            logger.info("Service not running")
            self._update_service_status()
            return

        logger.info("Sending STOP command to background service")
        success = send_stop_service()
        if success:
            logger.info("Service acknowledged stop command")
        else:
            logger.warning("Failed to send stop command to service")

        # Update status after a brief delay
        QTimer.singleShot(1000, self._update_service_status)

    def _handle_gui_command(self, command: str) -> str:
        """Handle IPC commands sent to the GUI (e.g., SHOW_WINDOW).

        Called from background thread, so must use thread-safe Qt invocation.

        Args:
            command: Command string received via IPC.

        Returns:
            Response string.
        """
        logger.info(f"GUI IPC received command: {command}")
        if command == "SHOW_WINDOW":
            # Must invoke on main thread - QTimer.singleShot doesn't work from background thread
            from PyQt6.QtCore import QMetaObject, Qt, Q_ARG
            if self.main_window:
                QMetaObject.invokeMethod(
                    self.main_window,
                    "_show_from_ipc",
                    Qt.ConnectionType.QueuedConnection
                )
            return "SUCCESS"
        elif command == "PING":
            return "PONG"
        else:
            return f"UNKNOWN: {command}"

    def run(self) -> int:
        """Run the application.

        Returns:
            Exit code (0 for success).
        """
        # Start GUI IPC server for handling SHOW_WINDOW from second instances
        self._gui_pipe_server = GUIPipeServer(on_command=self._handle_gui_command)
        self._gui_pipe_server.start()

        # Create Qt application
        self.qt_app = QApplication(sys.argv)

        # Apply custom style for properly sized spinbox/combobox arrows
        # from stockalert.ui.styles.proxy_style import StockAlertStyle
        # self._app_style = StockAlertStyle("Fusion")
        # self.qt_app.setStyle(self._app_style)
        self.qt_app.setStyle("Fusion")

        # Import translator for localized app properties
        from stockalert.i18n.translator import _

        # These fix the "Python" text in the taskbar right-click menu
        # Use translated strings so taskbar right-click shows correct language
        app_name = _("app.name")
        app_desc = _("app.description")
        logger.info(f"Setting app name='{app_name}', displayName='{app_desc}'")
        self.qt_app.setApplicationName(app_name)
        self.qt_app.setApplicationDisplayName(app_desc)
        self.qt_app.setApplicationVersion("4.0.0")
        self.qt_app.setOrganizationName("CushLabs")
        self.qt_app.setOrganizationDomain("cushlabs.ai")
        self.qt_app.setQuitOnLastWindowClosed(False)

        # Set application-wide icon from .ico file (affects taskbar)
        self.qt_app.setWindowIcon(self._create_app_icon())
        logger.info("Set taskbar icon from .ico file")

        # Set up UI (no monitoring setup - that's done by the service)
        self._setup_ui()

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

        # Start service status polling timer (updates tray icon every 5 seconds)
        self._status_timer = QTimer()
        self._status_timer.timeout.connect(self._update_service_status)
        self._status_timer.start(5000)  # 5 second interval

        # Initial status update
        self._update_service_status()

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
                # Auto-start service if in background mode and not already running
                self._ensure_service_running()
            else:
                logger.warning("Service not started - API key not configured")
                # Only prompt if onboarding was already completed (returning user without key)
                if onboarding_completed:
                    self._prompt_for_api_key()

            # Update status display
            self._update_service_status()
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
