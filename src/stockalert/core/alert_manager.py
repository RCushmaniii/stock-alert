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
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

from windows_toasts import Toast, WindowsToaster

if TYPE_CHECKING:
    from stockalert.core.notification_service import NotificationService
    from stockalert.core.twilio_service import TwilioService
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


@dataclass
class PendingNotification:
    """A notification waiting to be retried."""

    title: str
    message: str
    symbol: str | None = None
    retry_count: int = 0
    next_retry_time: float = field(default_factory=time.time)
    max_retries: int = 3


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
        self._twilio_service: TwilioService | None = None
        self._notification_service: NotificationService | None = None

        # Notification retry queue
        self._retry_queue: list[PendingNotification] = []
        self._retry_lock = threading.Lock()
        self._retry_thread: threading.Thread | None = None
        self._retry_running = False

        # Initialize notification services if SMS or WhatsApp enabled
        if self.settings.sms_enabled or self.settings.whatsapp_enabled:
            self._init_notification_services()

        # Start retry thread
        self._start_retry_thread()

    def _start_retry_thread(self) -> None:
        """Start the background retry thread."""
        if self._retry_thread and self._retry_thread.is_alive():
            return

        self._retry_running = True
        self._retry_thread = threading.Thread(target=self._retry_loop, daemon=True)
        self._retry_thread.start()

    def _stop_retry_thread(self) -> None:
        """Stop the background retry thread."""
        self._retry_running = False
        if self._retry_thread:
            self._retry_thread.join(timeout=2.0)

    def _retry_loop(self) -> None:
        """Background loop to retry failed notifications."""
        while self._retry_running:
            try:
                self._process_retry_queue()
            except Exception as e:
                logger.exception(f"Error in retry loop: {e}")
            time.sleep(5)  # Check every 5 seconds

    def _process_retry_queue(self) -> None:
        """Process pending notifications in the retry queue."""
        current_time = time.time()

        with self._retry_lock:
            # Find notifications ready to retry
            ready = [n for n in self._retry_queue if n.next_retry_time <= current_time]

            for notification in ready:
                self._retry_queue.remove(notification)

                # Attempt to send
                success = self._try_send_windows_notification(
                    notification.title,
                    notification.message,
                    notification.symbol,
                )

                if not success and notification.retry_count < notification.max_retries:
                    # Exponential backoff: 10s, 30s, 90s
                    delay = 10 * (3 ** notification.retry_count)
                    notification.retry_count += 1
                    notification.next_retry_time = current_time + delay
                    self._retry_queue.append(notification)
                    logger.debug(
                        f"Notification retry {notification.retry_count} scheduled "
                        f"in {delay}s: {notification.title}"
                    )
                elif not success:
                    logger.warning(
                        f"Notification dropped after {notification.max_retries} retries: "
                        f"{notification.title}"
                    )

    def _queue_for_retry(self, title: str, message: str, symbol: str | None = None) -> None:
        """Queue a failed notification for retry.

        Args:
            title: Notification title
            message: Notification message
            symbol: Optional stock symbol
        """
        with self._retry_lock:
            # Limit queue size to prevent memory issues
            if len(self._retry_queue) >= 20:
                logger.warning("Retry queue full, dropping oldest notification")
                self._retry_queue.pop(0)

            notification = PendingNotification(
                title=title,
                message=message,
                symbol=symbol,
                next_retry_time=time.time() + 10,  # First retry in 10 seconds
            )
            self._retry_queue.append(notification)
            logger.debug(f"Notification queued for retry: {title}")

    def _init_notification_services(self) -> None:
        """Initialize notification services for SMS/WhatsApp."""
        # Try backend API first (production mode)
        try:
            from stockalert.core.notification_service import NotificationService
            self._notification_service = NotificationService()
            if self._notification_service.is_configured:
                logger.info("Backend notification service initialized for WhatsApp alerts")
        except Exception as e:
            logger.debug(f"Backend notification service not available: {e}")
            self._notification_service = None

        # Fall back to direct Twilio (development mode)
        if not self._notification_service or not self._notification_service.is_configured:
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

        # Initialize notification services if needed
        if (settings.sms_enabled or settings.whatsapp_enabled):
            if not self._notification_service and not self._twilio_service:
                self._init_notification_services()

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
        name: str,  # noqa: ARG002 - reserved for future use
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

        # Get translated strings
        app_title = self._get_text("alerts.app_title")
        crossed = self._get_text("alerts.crossed_above")
        current = self._get_text("alerts.current")
        thresh = self._get_text("alerts.threshold")

        # Clean, concise format for both Windows and WhatsApp
        windows_message = f"{symbol} {crossed}\n{current} ${price:.2f}  {thresh} ${threshold:.2f}"
        whatsapp_message = (
            f"*{app_title}*\n"
            f"{symbol} {crossed}\n"
            f"{current} ${price:.2f}  ${threshold:.2f}"
        )

        self._send_all_channels(
            title=app_title,
            message=windows_message,
            symbol=symbol,
            whatsapp_message=whatsapp_message,
        )

    def send_low_alert(
        self,
        symbol: str,
        name: str,  # noqa: ARG002 - reserved for future use
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

        # Get translated strings
        app_title = self._get_text("alerts.app_title")
        crossed = self._get_text("alerts.crossed_below")
        current = self._get_text("alerts.current")
        thresh = self._get_text("alerts.threshold")

        # Clean, concise format for both Windows and WhatsApp
        windows_message = f"{symbol} {crossed}\n{current} ${price:.2f}  {thresh} ${threshold:.2f}"
        whatsapp_message = (
            f"*{app_title}*\n"
            f"{symbol} {crossed}\n"
            f"{current} ${price:.2f}  ${threshold:.2f}"
        )

        self._send_all_channels(
            title=app_title,
            message=windows_message,
            symbol=symbol,
            whatsapp_message=whatsapp_message,
        )

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

    def send_system_notification(self, title: str, message: str) -> None:
        """Send a system notification (always sent, ignores enabled flag).

        Used for critical system messages like auto-disabled tickers,
        config recovery, etc.

        Args:
            title: Notification title
            message: Notification message
        """
        # System notifications always go through, regardless of enabled flag
        self._send_windows_notification(title=title, message=message)

    def _send_all_channels(
        self,
        title: str,
        message: str,
        symbol: str | None = None,
        whatsapp_message: str | None = None,
    ) -> None:
        """Send notification to all enabled channels.

        Args:
            title: Notification title
            message: Notification message
            symbol: Optional stock symbol for action button
            whatsapp_message: Optional custom WhatsApp message format
        """
        # Windows notification
        if self.settings.windows_enabled:
            self._send_windows_notification(title, message, symbol)

        # SMS notification
        if self.settings.sms_enabled and self.settings.phone_number:
            self._send_sms(title, message)

        # WhatsApp notification
        if self.settings.whatsapp_enabled and self.settings.phone_number:
            self._send_whatsapp(whatsapp_message or f"*{title}*\n{message}")

        # Email notification (future implementation)
        if self.settings.email_enabled and self.settings.email_address:
            self._send_email(title, message)

    def _send_windows_notification(
        self,
        title: str,
        message: str,
        symbol: str | None = None,
    ) -> None:
        """Send a Windows toast notification with retry on failure.

        Args:
            title: Notification title
            message: Notification message
            symbol: Optional stock symbol for action button
        """
        success = self._try_send_windows_notification(title, message, symbol)

        if not success:
            # Queue for retry
            self._queue_for_retry(title, message, symbol)

    def _try_send_windows_notification(
        self,
        title: str,
        message: str,
        symbol: str | None = None,
    ) -> bool:
        """Attempt to send a Windows toast notification.

        Args:
            title: Notification title
            message: Notification message
            symbol: Optional stock symbol for action button

        Returns:
            True if sent successfully, False otherwise
        """
        try:
            toaster = WindowsToaster(self.APP_ID)
            toast = Toast()
            toast.text_fields = [title, message]

            # Add action button to view chart
            if symbol:
                chart_url = f"https://finance.yahoo.com/quote/{symbol}"
                toast.launch_action = chart_url

            toaster.show_toast(toast)
            logger.debug(f"Windows notification sent: {title}")
            return True

        except Exception as e:
            logger.warning(f"Failed to send Windows notification: {e}")
            return False

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

    def _send_whatsapp(self, message: str) -> None:
        """Send WhatsApp notification via backend API or direct Twilio.

        Args:
            message: Formatted message to send
        """
        # Try backend API first (production mode)
        if self._notification_service and self._notification_service.is_configured:
            try:
                success, result = self._notification_service.send_whatsapp(
                    to_number=self.settings.phone_number,
                    message=message,
                )
                if success:
                    logger.debug(f"WhatsApp sent via backend API: {result}")
                    return
                else:
                    logger.warning(f"Backend API send failed: {result}")
            except Exception as e:
                logger.warning(f"Backend API failed, trying direct Twilio: {e}")

        # Fall back to direct Twilio (development mode)
        if not self._twilio_service or not self._twilio_service.whatsapp_available:
            logger.warning("WhatsApp not available")
            return

        try:
            success = self._twilio_service.send_whatsapp(
                to_number=self.settings.phone_number,
                message=message,
            )
            if success:
                logger.debug("WhatsApp sent via Twilio")
            else:
                logger.warning("Twilio send returned False")
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

    def test_windows_notification(self) -> tuple[bool, str]:
        """Send a test Windows notification.

        Returns:
            Tuple of (success, message)
        """
        try:
            toaster = WindowsToaster(self.APP_ID)
            toast = Toast()
            toast.text_fields = [
                "StockAlert Test",
                "This is a test notification. If you see this, Windows notifications are working!",
            ]
            toaster.show_toast(toast)
            logger.info("Test Windows notification sent")
            return True, "Test notification sent successfully"

        except Exception as e:
            logger.exception(f"Failed to send test notification: {e}")
            return False, str(e)

    def test_whatsapp(self, phone_number: str) -> tuple[bool, str]:
        """Send a test WhatsApp message.

        Args:
            phone_number: Phone number to send test to

        Returns:
            Tuple of (success, message)
        """
        if not phone_number:
            return False, "Phone number not configured"

        test_message = (
            "*StockAlert Test*\n"
            "This is a test message. If you receive this, WhatsApp alerts are working!"
        )

        # Try backend API first (production mode)
        if not self._notification_service:
            self._init_notification_services()

        if self._notification_service and self._notification_service.is_configured:
            try:
                logger.info(f"Testing WhatsApp via backend API to {phone_number}")
                success, result = self._notification_service.send_whatsapp(
                    to_number=phone_number,
                    message=test_message,
                )
                if success:
                    logger.info(f"Test WhatsApp sent via backend API to {phone_number}")
                    return True, "Test message sent successfully"
                else:
                    # Return the actual error from the backend
                    logger.warning(f"Backend API test failed: {result}")
                    return False, result
            except Exception as e:
                logger.warning(f"Backend API test exception: {e}")
                return False, str(e)

        # Fall back to direct Twilio (development mode)
        if not self._twilio_service:
            return False, "WhatsApp not available - backend API not configured"

        if not self._twilio_service.whatsapp_available:
            return False, "WhatsApp not available - check Twilio configuration"

        try:
            success = self._twilio_service.send_whatsapp(
                to_number=phone_number,
                message=test_message,
            )
            if success:
                logger.info(f"Test WhatsApp sent via Twilio to {phone_number}")
                return True, "Test message sent successfully"
            else:
                return False, "Failed to send message - check Twilio logs"

        except Exception as e:
            logger.exception(f"Failed to send test WhatsApp: {e}")
            return False, str(e)
