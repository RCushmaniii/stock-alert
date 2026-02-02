"""
Phone number validation and formatting utilities.

Uses Google's libphonenumber via the phonenumbers library for accurate
international phone number parsing, validation, and formatting.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum

import phonenumbers
from phonenumbers import NumberParseException, PhoneNumberType, carrier, geocoder

logger = logging.getLogger(__name__)


class PhoneValidationError(Enum):
    """Phone number validation error types."""

    EMPTY = "empty"
    INVALID_FORMAT = "invalid_format"
    TOO_SHORT = "too_short"
    TOO_LONG = "too_long"
    INVALID_COUNTRY = "invalid_country"
    NOT_A_NUMBER = "not_a_number"


@dataclass
class PhoneValidationResult:
    """Result of phone number validation."""

    valid: bool
    formatted: str | None  # E.164 format if valid
    formatted_display: str | None  # Human-readable format
    country_code: str | None  # ISO country code (e.g., "US", "MX")
    country_name: str | None  # Country name
    number_type: str | None  # "mobile", "fixed_line", "voip", etc.
    carrier_name: str | None  # Carrier if detectable
    error: PhoneValidationError | None
    error_message: str | None

    @property
    def is_mobile(self) -> bool:
        """Check if this is a mobile number."""
        return self.number_type in ("mobile", "fixed_line_or_mobile")


def validate_phone_number(
    number: str,
    default_region: str = "US",
) -> PhoneValidationResult:
    """Validate and parse a phone number.

    Args:
        number: Phone number in any reasonable format
        default_region: Default ISO country code if not specified in number

    Returns:
        PhoneValidationResult with validation details
    """
    if not number or not number.strip():
        return PhoneValidationResult(
            valid=False,
            formatted=None,
            formatted_display=None,
            country_code=None,
            country_name=None,
            number_type=None,
            carrier_name=None,
            error=PhoneValidationError.EMPTY,
            error_message="Phone number is required",
        )

    # Clean the input
    cleaned = number.strip()

    # Special handling for Mexican mobile numbers with "1" prefix
    # Mexico reformed numbering but WhatsApp still needs +521 for mobiles
    # The phonenumbers library rejects +521 as "too long", so we handle it specially
    mexico_mobile_match = None
    if cleaned.startswith("+521") and len(cleaned) == 14:
        # This is likely a valid Mexican mobile: +521 + 10 digits
        # Store it and validate without the "1"
        mexico_mobile_match = cleaned
        cleaned = "+52" + cleaned[4:]  # Remove the "1" for validation

    try:
        # Parse the phone number
        parsed = phonenumbers.parse(cleaned, default_region)

        # Validate the number
        if not phonenumbers.is_valid_number(parsed):
            # Try to give more specific error
            if not phonenumbers.is_possible_number(parsed):
                possible_length = phonenumbers.is_possible_number_with_reason(parsed)
                if possible_length == phonenumbers.ValidationResult.TOO_SHORT:
                    return PhoneValidationResult(
                        valid=False,
                        formatted=None,
                        formatted_display=None,
                        country_code=None,
                        country_name=None,
                        number_type=None,
                        carrier_name=None,
                        error=PhoneValidationError.TOO_SHORT,
                        error_message="Phone number is too short",
                    )
                elif possible_length == phonenumbers.ValidationResult.TOO_LONG:
                    return PhoneValidationResult(
                        valid=False,
                        formatted=None,
                        formatted_display=None,
                        country_code=None,
                        country_name=None,
                        number_type=None,
                        carrier_name=None,
                        error=PhoneValidationError.TOO_LONG,
                        error_message="Phone number is too long",
                    )

            return PhoneValidationResult(
                valid=False,
                formatted=None,
                formatted_display=None,
                country_code=None,
                country_name=None,
                number_type=None,
                carrier_name=None,
                error=PhoneValidationError.INVALID_FORMAT,
                error_message="Invalid phone number format",
            )

        # Get formatted versions
        e164 = phonenumbers.format_number(
            parsed, phonenumbers.PhoneNumberFormat.E164
        )
        international = phonenumbers.format_number(
            parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL
        )

        # Restore Mexican mobile "1" prefix if it was provided
        if mexico_mobile_match:
            e164 = mexico_mobile_match
            international = "+52 1 " + international[4:]  # Add "1" back for display

        # Get country info
        country_code = phonenumbers.region_code_for_number(parsed)
        country_name = geocoder.country_name_for_number(parsed, "en")

        # Get number type
        num_type = phonenumbers.number_type(parsed)
        type_names = {
            PhoneNumberType.MOBILE: "mobile",
            PhoneNumberType.FIXED_LINE: "fixed_line",
            PhoneNumberType.FIXED_LINE_OR_MOBILE: "fixed_line_or_mobile",
            PhoneNumberType.TOLL_FREE: "toll_free",
            PhoneNumberType.PREMIUM_RATE: "premium_rate",
            PhoneNumberType.SHARED_COST: "shared_cost",
            PhoneNumberType.VOIP: "voip",
            PhoneNumberType.PERSONAL_NUMBER: "personal",
            PhoneNumberType.PAGER: "pager",
            PhoneNumberType.UAN: "uan",
            PhoneNumberType.VOICEMAIL: "voicemail",
            PhoneNumberType.UNKNOWN: "unknown",
        }
        number_type = type_names.get(num_type, "unknown")

        # Try to get carrier (may not always be available)
        carrier_name = None
        try:
            carrier_name = carrier.name_for_number(parsed, "en") or None
        except Exception:
            pass

        return PhoneValidationResult(
            valid=True,
            formatted=e164,
            formatted_display=international,
            country_code=country_code,
            country_name=country_name,
            number_type=number_type,
            carrier_name=carrier_name,
            error=None,
            error_message=None,
        )

    except NumberParseException as e:
        error_type = PhoneValidationError.INVALID_FORMAT
        error_msg = "Invalid phone number format"

        if e.error_type == NumberParseException.INVALID_COUNTRY_CODE:
            error_type = PhoneValidationError.INVALID_COUNTRY
            error_msg = "Invalid or missing country code. Use format: +1234567890"
        elif e.error_type == NumberParseException.NOT_A_NUMBER:
            error_type = PhoneValidationError.NOT_A_NUMBER
            error_msg = "This doesn't appear to be a phone number"
        elif e.error_type == NumberParseException.TOO_SHORT_AFTER_IDD:
            error_type = PhoneValidationError.TOO_SHORT
            error_msg = "Phone number is too short"
        elif e.error_type == NumberParseException.TOO_LONG:
            error_type = PhoneValidationError.TOO_LONG
            error_msg = "Phone number is too long"

        return PhoneValidationResult(
            valid=False,
            formatted=None,
            formatted_display=None,
            country_code=None,
            country_name=None,
            number_type=None,
            carrier_name=None,
            error=error_type,
            error_message=error_msg,
        )


def format_for_whatsapp(number: str, default_region: str = "US") -> str | None:
    """Format a phone number for WhatsApp API.

    WhatsApp has specific formatting requirements:
    - Must be E.164 format
    - For Mexico (+52), mobile numbers need the "1" prefix after country code

    Args:
        number: Phone number in any format
        default_region: Default region if not specified

    Returns:
        Properly formatted number for WhatsApp, or None if invalid
    """
    result = validate_phone_number(number, default_region)
    if not result.valid or not result.formatted:
        return None

    # WhatsApp uses E.164 format
    formatted = result.formatted

    # Special handling for Mexico mobile numbers
    # WhatsApp requires +521 prefix for Mexican mobile numbers
    if result.country_code == "MX" and result.is_mobile:
        # Check if it already has the "1" after +52
        if formatted.startswith("+52") and not formatted.startswith("+521"):
            # Insert the "1" after +52
            formatted = "+521" + formatted[3:]
            logger.debug(f"Formatted Mexico mobile for WhatsApp: {formatted}")

    return formatted


def format_for_sms(number: str, default_region: str = "US") -> str | None:
    """Format a phone number for SMS.

    Args:
        number: Phone number in any format
        default_region: Default region if not specified

    Returns:
        E.164 formatted number, or None if invalid
    """
    result = validate_phone_number(number, default_region)
    if not result.valid:
        return None
    return result.formatted


def get_validation_hint(country_code: str | None = None) -> str:
    """Get a hint for phone number format.

    Args:
        country_code: Optional ISO country code

    Returns:
        Example format string
    """
    examples = {
        "US": "+1 (555) 123-4567",
        "MX": "+52 33 1234 5678",
        "GB": "+44 7911 123456",
        "ES": "+34 612 345 678",
        "DE": "+49 151 12345678",
        "FR": "+33 6 12 34 56 78",
        "BR": "+55 11 91234-5678",
    }

    if country_code and country_code in examples:
        return f"Example: {examples[country_code]}"

    return "Include country code, e.g., +1 555 123 4567"
