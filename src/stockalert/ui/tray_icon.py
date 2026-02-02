"""
System tray icon for StockAlert.

Provides system tray integration using PyQt6's QSystemTrayIcon.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QIcon, QCursor, QPixmap, QPainter, QColor, QPen
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
        # Pass main_window as parent to ensure proper ownership
        super().__init__(main_window)
        self.main_window = main_window
        self.translator = translator
        self.on_quit = on_quit
        self.on_toggle_monitoring = on_toggle_monitoring

        self._monitoring_enabled = True
        self._ticker_count = 0

        # 1. Force programmatic branded icon that cannot be 'missing'
        logger.info("Creating programmatic branded icon for system tray")
        self.setIcon(self._create_branded_icon())
        self.setToolTip("StockAlert")

        # 2. Create menu with explicit ownership
        self._create_menu()

        # 3. Explicit activation handling
        self.activated.connect(self._on_activated)
        
        # 4. Make visible
        self.setVisible(True)
        self.show()  # Explicitly call show() as well
        
        # Debug: Check if system tray is available
        if self.isSystemTrayAvailable():
            logger.info("System tray IS available on this system")
        else:
            logger.warning("System tray is NOT available on this system!")
        
        if self.isVisible():
            logger.info("Tray icon reports it IS visible")
        else:
            logger.warning("Tray icon reports it is NOT visible!")
            
        logger.info("System tray icon initialized")

    def _create_branded_icon(self) -> QIcon:
        """Create a branded orange circle icon programmatically."""
        # Create 16x16 pixmap (standard tray icon size) with SOLID background
        pixmap = QPixmap(16, 16)
        pixmap.fill(QColor("#FF6A3D"))  # Solid orange - no transparency
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw White "S" shape for StockAlert
        painter.setPen(QPen(Qt.GlobalColor.white, 2))
        painter.drawLine(4, 12, 8, 6)
        painter.drawLine(8, 6, 12, 10)
        
        painter.end()
        
        icon = QIcon(pixmap)
        logger.info(f"Created icon, isNull={icon.isNull()}, sizes={icon.availableSizes()}")
        return icon

    def _create_menu(self) -> None:
        """Create the context menu with explicit ownership."""
        # Don't pass parent here - we'll set context menu explicitly
        self.menu = QMenu()

        # Show/Hide window
        self.show_action = self.menu.addAction(_("tray.menu.show"))
        self.show_action.triggered.connect(self._toggle_window)

        self.menu.addSeparator()

        # Monitoring status (disabled, just for display)
        self.status_action = self.menu.addAction("")
        self.status_action.setEnabled(False)

        # Market status (disabled, just for display)
        self.market_action = self.menu.addAction("")
        self.market_action.setEnabled(False)

        self.menu.addSeparator()

        # Toggle monitoring
        self.monitor_action = self.menu.addAction(_("tray.menu.stop_monitoring"))
        self.monitor_action.triggered.connect(self._toggle_monitoring)

        # Reload config
        self.reload_action = self.menu.addAction(_("tray.menu.reload_config"))
        self.reload_action.triggered.connect(self._reload_config)

        self.menu.addSeparator()

        # Exit
        self.exit_action = self.menu.addAction(_("tray.menu.exit"))
        self.exit_action.triggered.connect(self._on_exit)

        # Crucial: Set the context menu explicitly
        self.setContextMenu(self.menu)
        self._update_status_text()

    def _toggle_window(self) -> None:
        """Toggle main window visibility."""
        if self.main_window.isVisible():
            self.main_window.hide()
            self.show_action.setText(_("tray.menu.show"))
        else:
            self.main_window.showMaximized()
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
        elif reason == QSystemTrayIcon.ActivationReason.Trigger:
            # Single click - show window
            if not self.main_window.isVisible():
                self._toggle_window()
        elif reason == QSystemTrayIcon.ActivationReason.Context:
            # On Windows, explicitly popup the context menu at cursor position
            if self.contextMenu():
                self.contextMenu().popup(QCursor.pos())

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
