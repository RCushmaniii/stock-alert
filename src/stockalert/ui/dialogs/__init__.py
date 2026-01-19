"""
Dialog windows for StockAlert.

This package contains:
- settings_dialog: Settings configuration
- ticker_dialog: Add/edit ticker
"""

from __future__ import annotations

from stockalert.ui.dialogs.settings_dialog import SettingsWidget
from stockalert.ui.dialogs.ticker_dialog import TickerDialog

__all__ = [
    "SettingsWidget",
    "TickerDialog",
]
