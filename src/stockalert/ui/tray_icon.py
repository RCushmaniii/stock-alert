"""
System tray icon for StockAlert.

Provides system tray integration using PyQt6's QSystemTrayIcon.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Callable

from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtWidgets import QMenu, QSystemTrayIcon

from stockalert.i18n.translator import _

if TYPE_CHECKING:
    from stockalert.i18n.translator import Translator
    from stockalert.ui.main_window import MainWindow

logger = logging.getLogger(__name__)


class TrayIcon(QSystemTrayIcon):
    """System tray icon with context menu."""

    def __init__(
        self,
        main_window: MainWindow,
        icon_path: Path | None = None,
        translator: Translator | None = None,
        on_quit: Callable[[], None] | None = None,
        on_toggle_monitoring: Callable[[bool], None] | None = None,
    ) -> None:
        """Initialize the system tray icon.

        Args:
            main_window: Main application window
            icon_path: Path to icon file
            translator: Translator for i18n
            on_quit: Callback when quit is selected
            on_toggle_monitoring: Callback when monitoring is toggled
        """
        super().__init__()
        self.main_window = main_window
        self.translator = translator
        self.on_quit = on_quit
        self.on_toggle_monitoring = on_toggle_monitoring

        self._monitoring_enabled = True
        self._ticker_count = 0

        # Set icon
        if icon_path and icon_path.exists():
            self.setIcon(QIcon(str(icon_path)))
        else:
            # Use a default icon
            self.setIcon(self._create_default_icon())

        self.setToolTip(_("tray.title"))

        # Create menu
        self._create_menu()

        # Connect signals
        self.activated.connect(self._on_activated)

    def _create_default_icon(self) -> QIcon:
        """Create a simple default icon."""
        from PyQt6.QtCore import Qt
        from PyQt6.QtGui import QPixmap

        pixmap = QPixmap(64, 64)
        pixmap.fill(Qt.GlobalColor.darkBlue)
        return QIcon(pixmap)

    def _create_menu(self) -> None:
        """Create the context menu."""
        self.menu = QMenu()

        # Show/Hide window
        self.show_action = QAction(_("tray.menu.show"), self.menu)
        self.show_action.triggered.connect(self._toggle_window)
        self.menu.addAction(self.show_action)

        self.menu.addSeparator()

        # Monitoring status (disabled, just for display)
        self.status_action = QAction("", self.menu)
        self.status_action.setEnabled(False)
        self.menu.addAction(self.status_action)

        # Market status (disabled, just for display)
        self.market_action = QAction("", self.menu)
        self.market_action.setEnabled(False)
        self.menu.addAction(self.market_action)

        self.menu.addSeparator()

        # Toggle monitoring
        self.monitor_action = QAction(_("tray.menu.stop_monitoring"), self.menu)
        self.monitor_action.triggered.connect(self._toggle_monitoring)
        self.menu.addAction(self.monitor_action)

        # Reload config
        self.reload_action = QAction(_("tray.menu.reload_config"), self.menu)
        self.reload_action.triggered.connect(self._reload_config)
        self.menu.addAction(self.reload_action)

        self.menu.addSeparator()

        # Exit
        self.exit_action = QAction(_("tray.menu.exit"), self.menu)
        self.exit_action.triggered.connect(self._on_exit)
        self.menu.addAction(self.exit_action)

        self.setContextMenu(self.menu)
        self._update_status_text()

    def _toggle_window(self) -> None:
        """Toggle main window visibility."""
        if self.main_window.isVisible():
            self.main_window.hide()
            self.show_action.setText(_("tray.menu.show"))
        else:
            self.main_window.show()
            self.main_window.raise_()
            self.main_window.activateWindow()
            self.show_action.setText(_("tray.menu.hide"))

    def _toggle_monitoring(self) -> None:
        """Toggle monitoring on/off."""
        self._monitoring_enabled = not self._monitoring_enabled
        self._update_status_text()

        if self.on_toggle_monitoring:
            self.on_toggle_monitoring(self._monitoring_enabled)

    def _reload_config(self) -> None:
        """Reload configuration."""
        if self.main_window.on_settings_changed:
            self.main_window.on_settings_changed()

    def _on_exit(self) -> None:
        """Handle exit request."""
        if self.on_quit:
            self.on_quit()

    def _on_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        """Handle tray icon activation."""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self._toggle_window()

    def _update_status_text(self) -> None:
        """Update the status text in the menu."""
        self.status_action.setText(
            _("tray.menu.monitoring", count=self._ticker_count)
        )

        if self._monitoring_enabled:
            self.monitor_action.setText(_("tray.menu.stop_monitoring"))
            self.setToolTip(_("tray.tooltip.monitoring", count=self._ticker_count))
        else:
            self.monitor_action.setText(_("tray.menu.start_monitoring"))
            self.setToolTip(_("tray.tooltip.paused"))

    def set_monitoring_state(self, enabled: bool) -> None:
        """Set the monitoring state.

        Args:
            enabled: Whether monitoring is enabled
        """
        self._monitoring_enabled = enabled
        self._update_status_text()

    def set_ticker_count(self, count: int) -> None:
        """Set the number of monitored tickers.

        Args:
            count: Number of tickers
        """
        self._ticker_count = count
        self._update_status_text()

    def set_market_status(self, status: str) -> None:
        """Set the market status message.

        Args:
            status: Market status message
        """
        # Truncate if too long
        if len(status) > 25:
            status = status[:22] + "..."
        self.market_action.setText(_("tray.menu.market_status", status=status))

    def update_menu(self) -> None:
        """Update menu text after language change."""
        self.setToolTip(_("tray.title"))
        self.show_action.setText(
            _("tray.menu.hide") if self.main_window.isVisible() else _("tray.menu.show")
        )
        self.reload_action.setText(_("tray.menu.reload_config"))
        self.exit_action.setText(_("tray.menu.exit"))
        self._update_status_text()
