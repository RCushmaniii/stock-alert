"""
Ticker add/edit dialog for StockAlert.

Provides UI for adding or editing stock ticker configurations.
"""

from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING, Any

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from stockalert.core.tier_limits import can_add_ticker, get_max_tickers
from stockalert.i18n.translator import _

if TYPE_CHECKING:
    from stockalert.core.config import ConfigManager
    from stockalert.i18n.translator import Translator

logger = logging.getLogger(__name__)


class TickerDialog(QDialog):
    """Dialog for adding or editing a ticker."""

    def __init__(
        self,
        config_manager: ConfigManager,
        translator: Translator,
        ticker: dict[str, Any] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        """Initialize the ticker dialog.

        Args:
            config_manager: Configuration manager instance
            translator: Translator for i18n
            ticker: Existing ticker data for editing, or None for new
            parent: Parent widget
        """
        super().__init__(parent)
        self.config_manager = config_manager
        self.translator = translator
        self.ticker = ticker
        self.is_edit = ticker is not None
        self._current_price: float | None = None
        self._company_profile: dict[str, Any] | None = None

        self._setup_ui()
        if ticker:
            self._load_ticker(ticker)
            # Fetch current price in edit mode
            self._refresh_price()

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        title = _("tickers.edit") if self.is_edit else _("tickers.add")
        self.setWindowTitle(title)
        self.setMinimumWidth(400)

        layout = QVBoxLayout(self)

        # Form
        form_layout = QFormLayout()

        # Symbol
        symbol_layout = QHBoxLayout()
        self.symbol_edit = QLineEdit()
        self.symbol_edit.setMaxLength(10)
        self.symbol_edit.textChanged.connect(self._on_symbol_changed)
        if self.is_edit:
            self.symbol_edit.setEnabled(False)
        symbol_layout.addWidget(self.symbol_edit)

        self.validate_button = QPushButton(_("tickers.validate"))
        self.validate_button.clicked.connect(self._validate_symbol)
        if self.is_edit:
            self.validate_button.setEnabled(False)
        symbol_layout.addWidget(self.validate_button)

        form_layout.addRow(_("tickers.symbol") + ":", symbol_layout)

        # Name
        self.name_edit = QLineEdit()
        form_layout.addRow(_("tickers.name") + ":", self.name_edit)

        # High threshold
        self.high_spin = QDoubleSpinBox()
        self.high_spin.setRange(0.01, 999999.99)
        self.high_spin.setDecimals(2)
        self.high_spin.setPrefix("$")
        form_layout.addRow(_("tickers.high_threshold") + ":", self.high_spin)

        # Low threshold
        self.low_spin = QDoubleSpinBox()
        self.low_spin.setRange(0.01, 999999.99)
        self.low_spin.setDecimals(2)
        self.low_spin.setPrefix("$")
        form_layout.addRow(_("tickers.low_threshold") + ":", self.low_spin)

        # Enabled
        self.enabled_check = QCheckBox()
        self.enabled_check.setChecked(True)
        form_layout.addRow(_("tickers.enabled") + ":", self.enabled_check)

        # Current price (shown for both add and edit)
        price_layout = QHBoxLayout()
        self.price_label = QLabel("--")
        self.price_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        price_layout.addWidget(self.price_label)
        price_layout.addStretch()
        form_layout.addRow(_("tickers.current_price") + ":", price_layout)

        layout.addLayout(form_layout)

        # Status label
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)

        # Button row
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        # Refresh button (edit mode only)
        if self.is_edit:
            self.refresh_button = QPushButton(_("tickers.refresh_price"))
            self.refresh_button.setObjectName("actionButton")
            self.refresh_button.clicked.connect(self._refresh_price)
            button_layout.addWidget(self.refresh_button)

        # Validate button styling (add mode)
        self.validate_button.setObjectName("actionButton")

        self.save_button = QPushButton(_("dialogs.save"))
        self.save_button.setObjectName("actionButton")
        self.save_button.clicked.connect(self._on_save)
        self.save_button.setDefault(True)
        button_layout.addWidget(self.save_button)

        self.cancel_button = QPushButton(_("dialogs.cancel"))
        self.cancel_button.setObjectName("cancelButton")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)

        layout.addLayout(button_layout)

        # Apply button styles
        self._apply_button_styles()

    def _apply_button_styles(self) -> None:
        """Apply consistent button styles."""
        action_style = """
            QPushButton#actionButton {
                background-color: #FF6A3D;
                color: #000000;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 13px;
                font-weight: 600;
                min-width: 80px;
            }
            QPushButton#actionButton:hover {
                background-color: #FF8560;
            }
            QPushButton#actionButton:pressed {
                background-color: #E55A2D;
            }
            QPushButton#actionButton:disabled {
                background-color: #666666;
                color: #999999;
            }
            QPushButton#cancelButton {
                background-color: #2A2A2A;
                color: #FFFFFF;
                border: 1px solid #444444;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 13px;
                font-weight: 600;
                min-width: 80px;
            }
            QPushButton#cancelButton:hover {
                background-color: #3A3A3A;
                border-color: #555555;
            }
            QPushButton#cancelButton:pressed {
                background-color: #1A1A1A;
            }
        """
        self.setStyleSheet(action_style)

    def _refresh_price(self) -> None:
        """Fetch and display the current market price."""
        if not self.is_edit or not self.ticker:
            return

        symbol = self.ticker.get("symbol", "")
        if not symbol:
            return

        self.price_label.setText("Loading...")

        # Force UI update
        from PyQt6.QtCore import QCoreApplication
        QCoreApplication.processEvents()

        try:
            from stockalert.api.finnhub import FinnhubProvider
            from stockalert.core.api_key_manager import get_api_key

            # Get API key from secure storage
            api_key = get_api_key()
            logger.info(f"Refreshing price for {symbol}, API key present: {bool(api_key)}")

            if api_key:
                provider = FinnhubProvider(api_key=api_key)
                logger.info(f"Rate limiter tokens: {provider.tokens_available:.1f}")
                price = provider.get_price(symbol)
                logger.info(f"Got price for {symbol}: {price}")
                if price is not None:
                    self._current_price = price
                    self.price_label.setText(f"${price:.2f}")
                    self.price_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #00AA00;")
                else:
                    self.price_label.setText("N/A (market closed?)")
                    self.price_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #888888;")
            else:
                self.price_label.setText("No API key")
                self.price_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #888888;")

        except Exception as e:
            logger.exception(f"Failed to fetch price for {symbol}")
            # Show actual error to help debug
            error_msg = str(e)[:30] if str(e) else "Unknown error"
            self.price_label.setText(f"Error: {error_msg}")
            self.price_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #FF0000;")

    def _load_ticker(self, ticker: dict[str, Any]) -> None:
        """Load ticker data into the form."""
        self.symbol_edit.setText(ticker.get("symbol", ""))
        self.name_edit.setText(ticker.get("name", ""))
        self.high_spin.setValue(ticker.get("high_threshold", 0.0))
        self.low_spin.setValue(ticker.get("low_threshold", 0.0))
        self.enabled_check.setChecked(ticker.get("enabled", True))

    def _on_symbol_changed(self, text: str) -> None:
        """Handle symbol text change - uppercase it."""
        cursor_pos = self.symbol_edit.cursorPosition()
        self.symbol_edit.setText(text.upper())
        self.symbol_edit.setCursorPosition(cursor_pos)

        # Clear validation status
        self.status_label.setText("")

    def _validate_symbol_format(self, symbol: str) -> tuple[bool, str]:
        """Validate stock symbol format before API lookup.

        Args:
            symbol: Stock symbol to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not symbol:
            return False, _("errors.symbol_required")

        # Length check: 1-5 characters for most US stocks, up to 6 for some
        if len(symbol) > 6:
            return False, "Symbol too long (max 6 characters)"

        # Format check: uppercase alphanumeric, may include . or - for special symbols
        # Examples: AAPL, BRK.A, BRK.B, BF-A, BF-B
        if not re.match(r"^[A-Z0-9][A-Z0-9.\-]{0,5}$", symbol):
            return False, "Invalid symbol format (use uppercase letters/numbers)"

        # Common typo patterns to warn about
        if symbol.isdigit():
            return False, "Symbol cannot be all numbers"

        if symbol.startswith(".") or symbol.startswith("-"):
            return False, "Symbol cannot start with . or -"

        return True, ""

    def _validate_symbol(self) -> None:
        """Validate the entered symbol and auto-fill company name."""
        symbol = self.symbol_edit.text().strip().upper()

        # Basic format validation first (before API call)
        is_valid, error_msg = self._validate_symbol_format(symbol)
        if not is_valid:
            self.status_label.setText(error_msg)
            self.status_label.setStyleSheet("color: red;")
            return

        self.status_label.setText(_("tickers.validating"))
        self.status_label.setStyleSheet("color: gray;")
        self.validate_button.setEnabled(False)

        # Force UI update
        from PyQt6.QtCore import QCoreApplication
        QCoreApplication.processEvents()

        try:
            # Try to validate with Finnhub API and get company name
            from stockalert.api.finnhub import FinnhubProvider
            from stockalert.core.api_key_manager import get_api_key

            # Get API key from secure storage
            api_key = get_api_key()

            if api_key:
                provider = FinnhubProvider(api_key=api_key)
                results = provider.search_symbols(symbol)

                # Find exact match
                company_name = None
                for result in results:
                    if result.get("symbol", "").upper() == symbol:
                        company_name = result.get("description", "")
                        break

                if company_name:
                    # Auto-fill company name if empty
                    if not self.name_edit.text().strip():
                        self.name_edit.setText(company_name)
                    self.status_label.setText(_("tickers.valid_symbol"))
                    self.status_label.setStyleSheet("color: green;")

                    # Fetch current price for valid symbol
                    price = provider.get_price(symbol)
                    if price is not None:
                        self._current_price = price
                        self.price_label.setText(f"${price:.2f}")
                        self.price_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #00AA00;")
                    else:
                        self.price_label.setText("N/A")
                        self.price_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #888888;")

                    # Fetch company profile for additional data
                    profile = provider.get_company_profile(symbol)
                    if profile:
                        self._company_profile = profile
                        logger.info(f"Fetched profile for {symbol}: {profile.get('name')}")
                else:
                    self.status_label.setText(_("tickers.invalid_symbol"))
                    self.status_label.setStyleSheet("color: red;")
                    self.price_label.setText("--")
                    self.price_label.setStyleSheet("font-size: 16px; font-weight: bold;")
            else:
                # No API key - accept symbol but warn
                self.status_label.setText(_("tickers.valid_symbol"))
                self.status_label.setStyleSheet("color: orange;")
                self.price_label.setText("No API key")
                self.price_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #888888;")

        except Exception as e:
            logger.exception("Symbol validation failed")
            error_msg = str(e)
            if "rate" in error_msg.lower() or "limit" in error_msg.lower():
                self.status_label.setText("Rate limit - wait a moment")
                self.status_label.setStyleSheet("color: orange;")
            elif "api" in error_msg.lower() or "key" in error_msg.lower():
                self.status_label.setText("API error - check key")
                self.status_label.setStyleSheet("color: red;")
            else:
                self.status_label.setText(f"Error: {error_msg[:40]}")
                self.status_label.setStyleSheet("color: red;")
        finally:
            self.validate_button.setEnabled(True)

    def _validate_form(self) -> list[str]:
        """Validate form inputs.

        Returns:
            List of error messages, empty if valid
        """
        errors = []

        symbol = self.symbol_edit.text().strip().upper()
        if not symbol:
            errors.append(_("errors.symbol_required"))

        high = self.high_spin.value()
        low = self.low_spin.value()

        if high <= 0 or low <= 0:
            errors.append(_("errors.threshold_positive"))
        elif high <= low:
            errors.append(_("errors.high_greater_low"))

        # Check for duplicate (only for new tickers)
        if not self.is_edit:
            tickers = self.config_manager.get_tickers()
            if any(t["symbol"] == symbol for t in tickers):
                errors.append(_("tickers.duplicate_symbol", symbol=symbol))

            # Check ticker limit for free tier
            if not can_add_ticker(len(tickers)):
                max_tickers = get_max_tickers()
                errors.append(_("tickers.limit_reached", limit=max_tickers))

        return errors

    def _check_threshold_sanity(self) -> str | None:
        """Check if thresholds are realistic compared to current price.

        Returns:
            Warning message if thresholds seem unrealistic, None otherwise
        """
        if self._current_price is None or self._current_price <= 0:
            return None

        high = self.high_spin.value()
        low = self.low_spin.value()
        price = self._current_price

        warnings = []

        # Warn if high threshold is more than 5x current price
        if high > price * 5:
            ratio = high / price
            warnings.append(
                f"High threshold (${high:.2f}) is {ratio:.1f}x the current price (${price:.2f})"
            )

        # Warn if low threshold is less than 20% of current price
        if low < price * 0.2:
            ratio = price / low
            warnings.append(
                f"Low threshold (${low:.2f}) is {ratio:.1f}x below the current price (${price:.2f})"
            )

        # Warn if thresholds are very close to current price (within 1%)
        if abs(high - price) / price < 0.01:
            warnings.append(
                f"High threshold (${high:.2f}) is within 1% of current price - may trigger immediately"
            )
        if abs(low - price) / price < 0.01:
            warnings.append(
                f"Low threshold (${low:.2f}) is within 1% of current price - may trigger immediately"
            )

        if warnings:
            return "\n".join(warnings) + "\n\nAre you sure you want to continue?"

        return None

    def _on_save(self) -> None:
        """Handle save button click."""
        errors = self._validate_form()
        if errors:
            QMessageBox.warning(
                self,
                _("validation.errors_title"),
                "\n".join(errors),
            )
            return

        # Check for unrealistic thresholds
        sanity_warning = self._check_threshold_sanity()
        if sanity_warning:
            result = QMessageBox.warning(
                self,
                "Threshold Warning",
                sanity_warning,
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if result != QMessageBox.StandardButton.Yes:
                return

        try:
            symbol = self.symbol_edit.text().strip().upper()
            name = self.name_edit.text().strip() or symbol
            high = self.high_spin.value()
            low = self.low_spin.value()
            enabled = self.enabled_check.isChecked()

            if self.is_edit:
                # Update existing ticker
                self.config_manager.update_ticker(
                    symbol,
                    name=name,
                    high_threshold=high,
                    low_threshold=low,
                    enabled=enabled,
                )
            else:
                # Add new ticker with profile data if available
                profile = self._company_profile or {}
                self.config_manager.add_ticker(
                    symbol=symbol,
                    name=name,
                    high_threshold=high,
                    low_threshold=low,
                    enabled=enabled,
                    logo=profile.get("logo", ""),
                    industry=profile.get("finnhubIndustry", ""),
                    market_cap=profile.get("marketCapitalization", 0.0),
                    exchange=profile.get("exchange", ""),
                    weburl=profile.get("weburl", ""),
                    ipo=profile.get("ipo", ""),
                    country=profile.get("country", ""),
                    shares_outstanding=profile.get("shareOutstanding", 0.0),
                )

            self.accept()

        except Exception as e:
            logger.exception("Failed to save ticker")
            QMessageBox.critical(
                self,
                _("errors.title"),
                str(e),
            )
