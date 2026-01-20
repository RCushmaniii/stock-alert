"""
Alert and notification management for StockAlert.

Handles sending notifications via multiple channels:
- Windows toast notifications
- SMS (via Twilio)
- WhatsApp (via Twilio)
- Email (future)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from winotify import Notification, audio

if TYPE_CHECKING:
    from stockalert.i18n.translator import Translator

logger = logging.getLogger(__name__)


@dataclass
class AlertSettings:
    """Configuration for alert channels."""

    windows_enabled: bool = True
    windows_audio: bool = True
    sms_enabled: bool = False
    whatsapp_enabled: bool = False
    email_enabled: bool = False
    phone_number: str = ""
    email_address: str = ""


class AlertManager:
    """Manages stock price alerts and multi-channel notifications."""

    APP_ID = "StockAlert"

    def __init__(
        self,
        icon_path: Path | None = None,
        translator: Translator | None = None,
        settings: AlertSettings | None = None,
    ) -> None:
        """Initialize the alert manager.

        Args:
            icon_path: Path to notification icon file
            translator: Translator for localized messages
            settings: Alert channel settings
        """
        self.icon_path = str(icon_path) if icon_path else None
        self.translator = translator
        self.settings = settings or AlertSettings()
        self._notifications_enabled = True
        self._twilio_service = None

        # Initialize Twilio if SMS or WhatsApp enabled
        if self.settings.sms_enabled or self.settings.whatsapp_enabled:
            self._init_twilio()

    def _init_twilio(self) -> None:
        """Initialize Twilio service for SMS/WhatsApp."""
        try:
            from stockalert.core.twilio_service import TwilioService
            self._twilio_service = TwilioService()
            if self._twilio_service.is_configured:
                logger.info("Twilio service initialized for SMS/WhatsApp alerts")
            else:
                logger.warning("Twilio not configured - SMS/WhatsApp alerts disabled")
        except Exception as e:
            logger.error(f"Failed to initialize Twilio service: {e}")
            self._twilio_service = None

    def update_settings(self, settings: AlertSettings) -> None:
        """Update alert settings.

        Args:
            settings: New alert settings
        """
        self.settings = settings

        # Initialize Twilio if needed
        if (settings.sms_enabled or settings.whatsapp_enabled) and not self._twilio_service:
            self._init_twilio()

    def set_notifications_enabled(self, enabled: bool) -> None:
        """Enable or disable all notifications."""
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

        self._send_all_channels(title=title, message=message, symbol=symbol)

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

        self._send_all_channels(title=title, message=message, symbol=symbol)

    def send_info(self, title: str, message: str) -> None:
        """Send an informational notification.

        Args:
            title: Notification title
            message: Notification message
        """
        if not self._notifications_enabled:
            return

        # Info messages only go to Windows notifications
        self._send_windows_notification(title=title, message=message)

    def _send_all_channels(
        self,
        title: str,
        message: str,
        symbol: str | None = None,
    ) -> None:
        """Send notification to all enabled channels.

        Args:
            title: Notification title
            message: Notification message
            symbol: Optional stock symbol for action button
        """
        # Windows notification
        if self.settings.windows_enabled:
            self._send_windows_notification(title, message, symbol)

        # SMS notification
        if self.settings.sms_enabled and self.settings.phone_number:
            self._send_sms(title, message)

        # WhatsApp notification
        if self.settings.whatsapp_enabled and self.settings.phone_number:
            self._send_whatsapp(title, message)

        # Email notification (future implementation)
        if self.settings.email_enabled and self.settings.email_address:
            self._send_email(title, message)

    def _send_windows_notification(
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

            # Set audio based on settings
            if self.settings.windows_audio:
                toast.set_audio(audio.Default, loop=False)
            else:
                toast.set_audio(audio.Silent, loop=False)

            # Add action button to view chart
            if symbol:
                chart_url = f"https://finance.yahoo.com/quote/{symbol}"
                action_label = self._get_text("alerts.view_chart")
                toast.add_actions(label=action_label, launch=chart_url)

            toast.show()
            logger.debug(f"Windows notification sent: {title}")

        except Exception as e:
            logger.exception(f"Failed to send Windows notification: {e}")

    def _send_sms(self, title: str, message: str) -> None:
        """Send SMS notification via Twilio.

        Args:
            title: Alert title
            message: Alert message
        """
        if not self._twilio_service or not self._twilio_service.sms_available:
            logger.warning("SMS not available")
            return

        try:
            # Combine title and message for SMS
            sms_text = f"{title}\n{message}"
            success = self._twilio_service.send_sms(
                to_number=self.settings.phone_number,
                message=sms_text,
            )
            if success:
                logger.debug(f"SMS sent: {title}")
            else:
                logger.warning("SMS send returned False")
        except Exception as e:
            logger.exception(f"Failed to send SMS: {e}")

    def _send_whatsapp(self, title: str, message: str) -> None:
        """Send WhatsApp notification via Twilio.

        Args:
            title: Alert title
            message: Alert message
        """
        if not self._twilio_service or not self._twilio_service.whatsapp_available:
            logger.warning("WhatsApp not available")
            return

        try:
            # Combine title and message for WhatsApp
            whatsapp_text = f"*{title}*\n{message}"
            success = self._twilio_service.send_whatsapp(
                to_number=self.settings.phone_number,
                message=whatsapp_text,
            )
            if success:
                logger.debug(f"WhatsApp sent: {title}")
            else:
                logger.warning("WhatsApp send returned False")
        except Exception as e:
            logger.exception(f"Failed to send WhatsApp: {e}")

    def _send_email(self, title: str, message: str) -> None:
        """Send email notification (future implementation).

        Args:
            title: Alert title
            message: Alert message
        """
        # TODO: Implement email notifications
        logger.debug("Email notifications not yet implemented")
