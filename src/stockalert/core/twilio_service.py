"""
Twilio SMS and WhatsApp notification service for StockAlert.

Sends notifications via Vercel backend API to avoid bundling Twilio credentials
in the desktop app.
"""

from __future__ import annotations

import json
import logging
import urllib.request
import urllib.error
from typing import Any

from stockalert.core.api_key_manager import get_stockalert_api_key, has_stockalert_api_key
from stockalert.core.phone_utils import format_for_sms, format_for_whatsapp

logger = logging.getLogger(__name__)

# Vercel backend API URL
VERCEL_API_URL = "https://stockalert-api.vercel.app/api/send_whatsapp"


class TwilioService:
    """Service for sending SMS and WhatsApp notifications via Vercel backend."""

    def __init__(self) -> None:
        """Initialize Twilio service."""
        self._api_key: str | None = None
        self._load_credentials()

    def _load_credentials(self) -> None:
        """Load API key from secure credential storage."""
        # Load API key from Windows Credential Manager / config file
        self._api_key = get_stockalert_api_key()

        if self._api_key:
            logger.info("StockAlert API key configured (from secure storage)")
        else:
            logger.warning("StockAlert API key not configured - WhatsApp alerts will not work")

    @property
    def is_configured(self) -> bool:
        """Check if service is properly configured with API key."""
        return self._api_key is not None and len(self._api_key.strip()) > 0

    def reload_credentials(self) -> None:
        """Reload credentials from secure storage (call after user enters new key)."""
        self._load_credentials()

    @property
    def sms_available(self) -> bool:
        """Check if SMS is available."""
        return True

    @property
    def whatsapp_available(self) -> bool:
        """Check if WhatsApp is available."""
        return True

    def _call_api(self, endpoint: str, data: dict[str, Any]) -> dict[str, Any]:
        """Call the Vercel backend API.

        Args:
            endpoint: API endpoint URL
            data: Request payload

        Returns:
            Response data as dict
        """
        try:
            headers = {
                "Content-Type": "application/json",
            }
            if self._api_key:
                headers["X-API-Key"] = self._api_key

            request = urllib.request.Request(
                endpoint,
                data=json.dumps(data).encode("utf-8"),
                headers=headers,
                method="POST",
            )

            with urllib.request.urlopen(request, timeout=30) as response:
                return json.loads(response.read().decode("utf-8"))

        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8") if e.fp else str(e)
            logger.error(f"API error {e.code}: {error_body}")
            return {"success": False, "error": f"HTTP {e.code}: {error_body}"}
        except urllib.error.URLError as e:
            logger.error(f"Network error: {e.reason}")
            return {"success": False, "error": f"Network error: {e.reason}"}
        except Exception as e:
            logger.error(f"API call failed: {e}")
            return {"success": False, "error": str(e)}

    def send_sms(self, to_number: str, message: str) -> bool:
        """Send an SMS message.

        Args:
            to_number: Recipient phone number (any format, will be validated)
            message: Message text to send

        Returns:
            True if message was sent successfully, False otherwise
        """
        if not to_number:
            logger.warning("Cannot send SMS - no recipient number provided")
            return False

        try:
            formatted = format_for_sms(to_number)
            if not formatted:
                logger.error(f"Invalid phone number for SMS: {to_number}")
                return False

            # Use WhatsApp endpoint for now (can add SMS endpoint later)
            result = self._call_api(VERCEL_API_URL, {
                "phone": formatted,
                "message": message,
            })

            if result.get("success"):
                logger.info(f"SMS sent successfully via API")
                return True
            else:
                logger.error(f"SMS failed: {result.get('error')}")
                return False

        except Exception as e:
            logger.error(f"Failed to send SMS: {e}")
            return False

    def send_whatsapp(
        self,
        to_number: str,
        message: str,
        use_template: bool = True,
        template_variables: dict | None = None,
    ) -> bool:
        """Send a WhatsApp message via Vercel backend.

        Args:
            to_number: Recipient phone number (any format, will be validated)
            message: Message text (used as fallback or for template variables)
            use_template: If True, use approved WhatsApp template
            template_variables: Optional dict of variables for the template

        Returns:
            True if message was sent successfully, False otherwise
        """
        if not to_number:
            logger.warning("Cannot send WhatsApp - no recipient number provided")
            return False

        try:
            formatted = format_for_whatsapp(to_number)
            if not formatted:
                logger.error(f"Invalid phone number for WhatsApp: {to_number}")
                return False

            logger.info(f"Sending WhatsApp to {formatted} via Vercel API")

            # Build request payload
            payload: dict[str, Any] = {
                "phone": formatted,
            }

            if use_template and template_variables:
                payload["template_data"] = template_variables
            else:
                payload["message"] = message

            result = self._call_api(VERCEL_API_URL, payload)

            if result.get("success"):
                msg_sid = result.get("message_sid", "unknown")
                msg_status = result.get("status", "unknown")
                error_code = result.get("error_code")
                error_msg = result.get("error_message")

                if error_code or error_msg:
                    logger.warning(
                        f"WhatsApp sent but has errors - SID: {msg_sid}, "
                        f"Status: {msg_status}, ErrorCode: {error_code}, ErrorMsg: {error_msg}"
                    )
                else:
                    logger.info(
                        f"WhatsApp message sent successfully - SID: {msg_sid}, Status: {msg_status}"
                    )
                return True
            else:
                logger.error(
                    f"WhatsApp failed: {result.get('error')} "
                    f"(type: {result.get('error_type', 'unknown')})"
                )
                return False

        except Exception as e:
            logger.error(f"Failed to send WhatsApp message: {e}")
            return False

    def send_optin_message(self, to_number: str, stock_count: int) -> bool:
        """Send a WhatsApp opt-in message to request user consent.

        Args:
            to_number: Recipient phone number (any format, will be validated)
            stock_count: Number of stocks currently being monitored

        Returns:
            True if message was sent successfully, False otherwise
        """
        if not to_number:
            logger.warning("Cannot send opt-in - no recipient number provided")
            return False

        try:
            formatted = format_for_whatsapp(to_number)
            if not formatted:
                logger.error(f"Invalid phone number for opt-in: {to_number}")
                return False

            logger.info(f"Sending WhatsApp opt-in to {formatted}")

            # Build request payload for opt-in template
            payload: dict[str, Any] = {
                "phone": formatted,
                "template_type": "optin",
                "template_data": {
                    "1": str(stock_count),
                },
            }

            result = self._call_api(VERCEL_API_URL, payload)

            if result.get("success"):
                msg_sid = result.get("message_sid", "unknown")
                logger.info(f"Opt-in message sent successfully - SID: {msg_sid}")
                return True
            else:
                logger.error(f"Opt-in message failed: {result.get('error')}")
                return False

        except Exception as e:
            logger.error(f"Failed to send opt-in message: {e}")
            return False
