"""
Twilio SMS and WhatsApp notification service for StockAlert.

Handles sending SMS and WhatsApp messages via Twilio API.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)


class TwilioService:
    """Service for sending SMS and WhatsApp notifications via Twilio."""

    def __init__(self) -> None:
        """Initialize Twilio service with credentials from environment."""
        self._client = None
        self._account_sid: str | None = None
        self._auth_token: str | None = None
        self._from_number: str | None = None
        self._whatsapp_number: str | None = None

        self._load_credentials()

    def _load_credentials(self) -> None:
        """Load Twilio credentials from environment variables."""
        from dotenv import load_dotenv

        # Load .env from project root
        app_dir = Path(__file__).resolve().parent.parent.parent.parent
        load_dotenv(app_dir / ".env")

        # Support both TWILIO and TWILLIO spellings
        self._account_sid = os.environ.get("TWILIO_SID") or os.environ.get("TWILLIO_SID")
        self._auth_token = os.environ.get("TWILIO_AUTH_TOKEN") or os.environ.get("TWILLIO_AUTH_TOKEN")
        self._from_number = os.environ.get("TWILIO_FROM_NUMBER") or os.environ.get("TWILLIO_FROM_NUMBER")
        self._whatsapp_number = os.environ.get("TWILIO_WHATSAPP_NUMBER") or os.environ.get("TWILLIO_WHATSAPP_NUMBER")

        if self._account_sid and self._auth_token:
            try:
                from twilio.rest import Client
                self._client = Client(self._account_sid, self._auth_token)
                logger.info("Twilio service initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Twilio client: {e}")
                self._client = None
        else:
            logger.warning("Twilio credentials not configured - SMS/WhatsApp alerts disabled")

    @property
    def is_configured(self) -> bool:
        """Check if Twilio is properly configured."""
        return self._client is not None

    @property
    def sms_available(self) -> bool:
        """Check if SMS is available (requires from_number)."""
        return self.is_configured and bool(self._from_number)

    @property
    def whatsapp_available(self) -> bool:
        """Check if WhatsApp is available."""
        return self.is_configured and bool(self._whatsapp_number)

    def send_sms(self, to_number: str, message: str) -> bool:
        """Send an SMS message.

        Args:
            to_number: Recipient phone number (E.164 format, e.g., +15551234567)
            message: Message text to send

        Returns:
            True if message was sent successfully, False otherwise
        """
        if not self.sms_available:
            logger.warning("SMS not available - missing Twilio from_number")
            return False

        if not to_number:
            logger.warning("Cannot send SMS - no recipient number provided")
            return False

        try:
            # Ensure number is in E.164 format
            to_number = self._format_phone_number(to_number)

            message_obj = self._client.messages.create(
                body=message,
                from_=self._from_number,
                to=to_number,
            )

            logger.info(f"SMS sent successfully: SID={message_obj.sid}")
            return True

        except Exception as e:
            logger.error(f"Failed to send SMS: {e}")
            return False

    def send_whatsapp(self, to_number: str, message: str) -> bool:
        """Send a WhatsApp message.

        Args:
            to_number: Recipient phone number (E.164 format, e.g., +15551234567)
            message: Message text to send

        Returns:
            True if message was sent successfully, False otherwise
        """
        if not self.whatsapp_available:
            logger.warning("WhatsApp not available - missing Twilio WhatsApp number")
            return False

        if not to_number:
            logger.warning("Cannot send WhatsApp - no recipient number provided")
            return False

        try:
            # Ensure number is in E.164 format
            to_number = self._format_phone_number(to_number)

            # WhatsApp uses whatsapp: prefix
            from_whatsapp = f"whatsapp:{self._whatsapp_number}"
            to_whatsapp = f"whatsapp:{to_number}"

            message_obj = self._client.messages.create(
                body=message,
                from_=from_whatsapp,
                to=to_whatsapp,
            )

            logger.info(f"WhatsApp message sent successfully: SID={message_obj.sid}")
            return True

        except Exception as e:
            logger.error(f"Failed to send WhatsApp message: {e}")
            return False

    def _format_phone_number(self, number: str) -> str:
        """Format phone number to E.164 format.

        Args:
            number: Phone number in various formats

        Returns:
            Phone number in E.164 format (e.g., +15551234567)
        """
        # Remove common formatting characters
        cleaned = "".join(c for c in number if c.isdigit() or c == "+")

        # Add + prefix if missing
        if not cleaned.startswith("+"):
            # Assume US number if 10 digits
            if len(cleaned) == 10:
                cleaned = "+1" + cleaned
            elif len(cleaned) == 11 and cleaned.startswith("1"):
                cleaned = "+" + cleaned
            else:
                cleaned = "+" + cleaned

        return cleaned
