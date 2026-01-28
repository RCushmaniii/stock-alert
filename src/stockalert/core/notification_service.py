"""
Notification service for StockAlert.

Sends WhatsApp notifications via the StockAlert backend API.
This is the production approach - users don't need their own Twilio credentials.
"""

from __future__ import annotations

import logging

import requests

logger = logging.getLogger(__name__)

# Production API endpoint
API_URL = "https://stockalert-api.vercel.app/api/send_whatsapp"


class NotificationService:
    """Service for sending notifications via the StockAlert backend API."""

    def __init__(self) -> None:
        """Initialize notification service."""
        self._api_url = API_URL
        logger.info("Notification service initialized")

    @property
    def is_configured(self) -> bool:
        """Check if the notification service is configured."""
        return bool(self._api_url)

    @property
    def whatsapp_available(self) -> bool:
        """Check if WhatsApp notifications are available."""
        return self.is_configured

    def send_whatsapp(
        self,
        to_number: str,
        message: str,
        country_code: str | None = None,
    ) -> tuple[bool, str]:
        """Send a WhatsApp message via the backend API.

        Args:
            to_number: Recipient phone number
            message: Message text to send
            country_code: Optional country code (e.g., "1", "52", "34")

        Returns:
            Tuple of (success, message) - message is error if failed, SID if success
        """
        if not self._api_url:
            logger.error("API URL not configured")
            return False, "API URL not configured"

        if not to_number:
            logger.warning("Cannot send WhatsApp - no recipient number provided")
            return False, "No phone number provided"

        try:
            headers = {
                "Content-Type": "application/json",
            }

            payload = {
                "phone": to_number,
                "message": message,
            }

            if country_code:
                payload["country_code"] = country_code

            logger.info(f"Sending WhatsApp to {to_number} via {self._api_url}")

            response = requests.post(
                self._api_url,
                headers=headers,
                json=payload,
                timeout=30,
            )

            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    sid = result.get("message_sid", "")
                    logger.info(f"WhatsApp sent: SID={sid}")
                    return True, sid
                else:
                    error = result.get("error", "Unknown error")
                    logger.error(f"WhatsApp failed: {error}")
                    return False, error
            else:
                error = f"API error {response.status_code}: {response.text}"
                logger.error(error)
                return False, error

        except requests.RequestException as e:
            error = f"Request failed: {e}"
            logger.error(error)
            return False, error

    def send_stock_alert(
        self,
        to_number: str,
        symbol: str,
        price: float,
        threshold: float,
        alert_type: str,
        country_code: str | None = None,
    ) -> tuple[bool, str]:
        """Send a stock price alert via WhatsApp using approved template.

        Args:
            to_number: Recipient phone number
            symbol: Stock ticker symbol
            price: Current stock price
            threshold: Alert threshold that was crossed
            alert_type: Type of alert ("high" or "low")
            country_code: Optional country code

        Returns:
            Tuple of (success, message)
        """
        if not self._api_url:
            return False, "API URL not configured"

        if not to_number:
            return False, "No phone number provided"

        direction = "above" if alert_type == "high" else "below"

        try:
            headers = {"Content-Type": "application/json"}

            # Use template_data for business-initiated messages
            payload = {
                "phone": to_number,
                "template_data": {
                    "symbol": symbol,
                    "price": f"{price:.2f}",
                    "threshold": f"{threshold:.2f}",
                    "direction": direction,
                },
            }

            if country_code:
                payload["country_code"] = country_code

            logger.info(f"Sending stock alert for {symbol} to {to_number}")

            response = requests.post(
                self._api_url,
                headers=headers,
                json=payload,
                timeout=30,
            )

            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    sid = result.get("message_sid", "")
                    logger.info(f"Stock alert sent: SID={sid}")
                    return True, sid
                else:
                    error = result.get("error", "Unknown error")
                    logger.error(f"Stock alert failed: {error}")
                    return False, error
            else:
                error = f"API error {response.status_code}: {response.text}"
                logger.error(error)
                return False, error

        except requests.RequestException as e:
            error = f"Request failed: {e}"
            logger.error(error)
            return False, error


# Singleton instance
_notification_service: NotificationService | None = None


def get_notification_service() -> NotificationService:
    """Get the global notification service instance."""
    global _notification_service
    if _notification_service is None:
        _notification_service = NotificationService()
    return _notification_service
