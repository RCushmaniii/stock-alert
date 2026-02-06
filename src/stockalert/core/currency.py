"""
Currency formatting and conversion utilities.

Handles display of prices in USD or MXN based on user preference.
All internal values are stored in USD; this module handles display conversion.
"""

from __future__ import annotations

import logging
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from stockalert.core.config import ConfigManager

logger = logging.getLogger(__name__)


class Currency(Enum):
    """Supported currencies."""

    USD = "USD"
    MXN = "MXN"


# Currency display settings
CURRENCY_SYMBOLS = {
    Currency.USD: "$",
    Currency.MXN: "MX$",
}

CURRENCY_NAMES = {
    Currency.USD: "US Dollar",
    Currency.MXN: "Mexican Peso",
}


class CurrencyFormatter:
    """Handles currency conversion and formatting for display."""

    def __init__(self, config_manager: ConfigManager) -> None:
        """Initialize the currency formatter.

        Args:
            config_manager: Configuration manager instance
        """
        self._config = config_manager
        self._exchange_rate: float | None = None

    @property
    def current_currency(self) -> Currency:
        """Get the currently selected display currency."""
        currency_str = self._config.get("settings.currency", "USD")
        try:
            return Currency(currency_str)
        except ValueError:
            return Currency.USD

    @property
    def symbol(self) -> str:
        """Get the symbol for the current currency."""
        return CURRENCY_SYMBOLS.get(self.current_currency, "$")

    def set_exchange_rate(self, rate: float | None) -> None:
        """Update the cached exchange rate.

        Args:
            rate: USD to MXN exchange rate, or None if unavailable
        """
        self._exchange_rate = rate
        if rate:
            logger.debug(f"Currency formatter updated with rate: {rate:.4f}")

    def convert(self, usd_amount: float) -> float:
        """Convert USD amount to display currency.

        Args:
            usd_amount: Amount in USD

        Returns:
            Amount in the user's selected currency
        """
        if self.current_currency == Currency.USD:
            return usd_amount

        if self._exchange_rate is None:
            logger.warning("No exchange rate available, displaying in USD")
            return usd_amount

        return usd_amount * self._exchange_rate

    def format_price(self, usd_amount: float, decimals: int = 2) -> str:
        """Format a USD price for display in user's currency.

        Args:
            usd_amount: Price in USD
            decimals: Number of decimal places

        Returns:
            Formatted price string with currency symbol
        """
        converted = self.convert(usd_amount)
        symbol = self.symbol

        # Format with thousand separators
        if decimals == 0:
            return f"{symbol}{converted:,.0f}"
        elif decimals == 1:
            return f"{symbol}{converted:,.1f}"
        else:
            return f"{symbol}{converted:,.2f}"

    def format_threshold(self, usd_amount: float) -> str:
        """Format a threshold value for display.

        Args:
            usd_amount: Threshold in USD

        Returns:
            Formatted threshold string
        """
        return self.format_price(usd_amount, decimals=2)

    def format_market_cap(self, usd_millions: float) -> str:
        """Format market cap for display.

        Args:
            usd_millions: Market cap in millions of USD

        Returns:
            Formatted market cap string (e.g., "$2.5T", "MX$50B")
        """
        converted = self.convert(usd_millions)
        symbol = self.symbol

        if converted >= 1_000_000:  # Trillions
            return f"{symbol}{converted / 1_000_000:.1f}T"
        elif converted >= 1_000:  # Billions
            return f"{symbol}{converted / 1_000:.1f}B"
        else:  # Millions
            return f"{symbol}{converted:.0f}M"

    def parse_user_input(self, user_input: str) -> float | None:
        """Parse a user-entered price and convert to USD.

        Args:
            user_input: User-entered price string (may include currency symbol)

        Returns:
            Price in USD, or None if parsing fails
        """
        # Remove currency symbols and whitespace
        cleaned = user_input.strip()
        for sym in CURRENCY_SYMBOLS.values():
            cleaned = cleaned.replace(sym, "")
        cleaned = cleaned.replace(",", "").replace(" ", "")

        try:
            value = float(cleaned)
        except ValueError:
            return None

        # If user is viewing in MXN, convert their input back to USD
        if self.current_currency == Currency.MXN and self._exchange_rate:
            return value / self._exchange_rate

        return value

    def get_rate_info(self) -> str:
        """Get a human-readable exchange rate info string.

        Returns:
            Info string like "1 USD = 17.50 MXN" or "Rate unavailable"
        """
        if self._exchange_rate is None:
            return "Exchange rate unavailable"
        return f"1 USD = {self._exchange_rate:.2f} MXN"


# Module-level formatter instance (set by app.py)
_formatter: CurrencyFormatter | None = None


def get_formatter() -> CurrencyFormatter | None:
    """Get the global currency formatter instance."""
    return _formatter


def set_formatter(formatter: CurrencyFormatter) -> None:
    """Set the global currency formatter instance."""
    global _formatter
    _formatter = formatter


def format_price(usd_amount: float, decimals: int = 2) -> str:
    """Convenience function to format a price using the global formatter.

    Args:
        usd_amount: Price in USD
        decimals: Number of decimal places

    Returns:
        Formatted price string, or USD format if no formatter available
    """
    if _formatter is None:
        return f"${usd_amount:,.{decimals}f}"
    return _formatter.format_price(usd_amount, decimals)
