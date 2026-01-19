"""
PyQt6 user interface for StockAlert.

This package contains:
- main_window: Main application window
- tray_icon: System tray integration
- dialogs/: Modal dialogs
- widgets/: Reusable widgets
- styles/: Qt stylesheets
"""

from __future__ import annotations

from stockalert.ui.main_window import MainWindow
from stockalert.ui.tray_icon import TrayIcon

__all__ = [
    "MainWindow",
    "TrayIcon",
]
