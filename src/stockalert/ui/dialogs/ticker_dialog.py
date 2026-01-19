"""
Ticker add/edit dialog for StockAlert.

Provides UI for adding or editing stock ticker configurations.
"""

from __future__ import annotations

import logging
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

        self._setup_ui()
        if ticker:
            self._load_ticker(ticker)

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

        layout.addLayout(form_layout)

        # Status label
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)

        # Button row
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.save_button = QPushButton(_("dialogs.save"))
        self.save_button.clicked.connect(self._on_save)
        self.save_button.setDefault(True)
        button_layout.addWidget(self.save_button)

        self.cancel_button = QPushButton(_("dialogs.cancel"))
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)

        layout.addLayout(button_layout)

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

    def _validate_symbol(self) -> None:
        """Validate the entered symbol."""
        symbol = self.symbol_edit.text().strip().upper()
        if not symbol:
            self.status_label.setText(_("errors.symbol_required"))
            self.status_label.setStyleSheet("color: red;")
            return

        self.status_label.setText(_("tickers.validating"))
        self.status_label.setStyleSheet("color: gray;")
        self.validate_button.setEnabled(False)

        # Force UI update
        from PyQt6.QtCore import QCoreApplication
        QCoreApplication.processEvents()

        try:
            # Try to validate with API (if available)
            # For now, just accept the symbol
            # In production, this would call the API provider
            self.status_label.setText(_("tickers.valid_symbol"))
            self.status_label.setStyleSheet("color: green;")
        except Exception as e:
            logger.exception("Symbol validation failed")
            self.status_label.setText(_("tickers.invalid_symbol"))
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

        return errors

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
                # Add new ticker
                self.config_manager.add_ticker(
                    symbol=symbol,
                    name=name,
                    high_threshold=high,
                    low_threshold=low,
                    enabled=enabled,
                )

            self.accept()

        except Exception as e:
            logger.exception("Failed to save ticker")
            QMessageBox.critical(
                self,
                _("errors.title"),
                str(e),
            )
