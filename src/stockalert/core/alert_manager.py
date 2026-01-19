"""
Alert and notification management for StockAlert.

Handles sending Windows toast notifications for stock price alerts.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

from winotify import Notification, audio

if TYPE_CHECKING:
    from stockalert.i18n.translator import Translator

logger = logging.getLogger(__name__)


class AlertManager:
    """Manages stock price alerts and Windows notifications."""

    APP_ID = "StockAlert"

    def __init__(
        self,
        icon_path: Path | None = None,
        translator: Translator | None = None,
    ) -> None:
        """Initialize the alert manager.

        Args:
            icon_path: Path to notification icon file
            translator: Translator for localized messages
        """
        self.icon_path = str(icon_path) if icon_path else None
        self.translator = translator
        self._notifications_enabled = True

    def set_notifications_enabled(self, enabled: bool) -> None:
        """Enable or disable notifications."""
        self._notifications_enabled = enabled
        logger.info(f"Notifications {'enabled' if enabled else 'disabled'}")

    def _get_text(self, key: str, **kwargs: str | float) -> str:
        """Get translated text or fall back to key."""
        if self.translator:
            return self.translator.get(key, **kwargs)
        return key

    def send_high_alert(
        self,
        symbol: str,
        name: str,
        price: float,
        threshold: float,
    ) -> None:
        """Send a high threshold alert notification.

        Args:
            symbol: Stock ticker symbol
            name: Stock display name
            price: Current price that triggered alert
            threshold: Threshold that was crossed
        """
        if not self._notifications_enabled:
            return

        title = self._get_text("alerts.high.title", symbol=symbol)
        message = self._get_text(
            "alerts.high.message",
            name=name,
            price=price,
            threshold=threshold,
        )

        self._send_notification(
            title=title,
            message=message,
            symbol=symbol,
        )

    def send_low_alert(
        self,
        symbol: str,
        name: str,
        price: float,
        threshold: float,
    ) -> None:
        """Send a low threshold alert notification.

        Args:
            symbol: Stock ticker symbol
            name: Stock display name
            price: Current price that triggered alert
            threshold: Threshold that was crossed
        """
        if not self._notifications_enabled:
            return

        title = self._get_text("alerts.low.title", symbol=symbol)
        message = self._get_text(
            "alerts.low.message",
            name=name,
            price=price,
            threshold=threshold,
        )

        self._send_notification(
            title=title,
            message=message,
            symbol=symbol,
        )

    def send_info(self, title: str, message: str) -> None:
        """Send an informational notification.

        Args:
            title: Notification title
            message: Notification message
        """
        if not self._notifications_enabled:
            return

        self._send_notification(title=title, message=message)

    def _send_notification(
        self,
        title: str,
        message: str,
        symbol: str | None = None,
    ) -> None:
        """Send a Windows toast notification.

        Args:
            title: Notification title
            message: Notification message
            symbol: Optional stock symbol for action button
        """
        try:
            toast = Notification(
                app_id=self.APP_ID,
                title=title,
                msg=message,
                duration="long",
                icon=self.icon_path,
            )

            toast.set_audio(audio.Default, loop=False)

            # Add action button to view chart
            if symbol:
                chart_url = f"https://finance.yahoo.com/quote/{symbol}"
                action_label = self._get_text("alerts.view_chart")
                toast.add_actions(label=action_label, launch=chart_url)

            toast.show()
            logger.debug(f"Notification sent: {title}")

        except Exception as e:
            logger.exception(f"Failed to send notification: {e}")
