"""
Core business logic for StockAlert.

This package contains:
- monitor: Stock price monitoring
- alert_manager: Notification handling
- config: Configuration management
"""

from __future__ import annotations

from stockalert.core.alert_manager import AlertManager
from stockalert.core.config import ConfigManager
from stockalert.core.monitor import StockMonitor

__all__ = [
    "AlertManager",
    "ConfigManager",
    "StockMonitor",
]
