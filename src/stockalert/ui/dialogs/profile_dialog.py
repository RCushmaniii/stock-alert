"""
Profile widget for StockAlert.

Provides UI for editing user profile information.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import TYPE_CHECKING

from PyQt6.QtWidgets import (
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from stockalert.core.phone_utils import validate_phone_number, get_validation_hint
from stockalert.i18n.translator import _

if TYPE_CHECKING:
    from stockalert.core.config import ConfigManager
    from stockalert.i18n.translator import Translator

logger = logging.getLogger(__name__)


class ProfileWidget(QWidget):
    """Widget for editing user profile."""

    def __init__(
        self,
        config_manager: ConfigManager,
        translator: Translator,
        on_save: Callable[[], None] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        """Initialize the profile widget.

        Args:
            config_manager: Configuration manager instance
            translator: Translator for i18n
            on_save: Callback when profile is saved
            parent: Parent widget
        """
        super().__init__(parent)
        self.config_manager = config_manager
        self.translator = translator
        self.on_save = on_save

        self._setup_ui()
        self._load_profile()

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        layout.setSpacing(24)

        # Profile group
        self.profile_group = QGroupBox(_("profile.title"))
        form_layout = QFormLayout(self.profile_group)
        form_layout.setVerticalSpacing(16)
        form_layout.setHorizontalSpacing(20)
        form_layout.setContentsMargins(24, 32, 24, 24)

        # Name
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText(_("profile.name_placeholder"))
        self.name_label = QLabel(_("profile.name"))
        form_layout.addRow(self.name_label, self.name_input)

        self.name_help = QLabel(_("profile.name_help"))
        self.name_help.setObjectName("helpLabel")
        form_layout.addRow("", self.name_help)

        # Email
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText(_("profile.email_placeholder"))
        self.email_label = QLabel(_("profile.email"))
        form_layout.addRow(self.email_label, self.email_input)

        self.email_help = QLabel(_("profile.email_help"))
        self.email_help.setObjectName("helpLabel")
        form_layout.addRow("", self.email_help)

        # Cell/Phone with validation
        cell_container = QWidget()
        cell_layout = QVBoxLayout(cell_container)
        cell_layout.setContentsMargins(0, 0, 0, 0)
        cell_layout.setSpacing(4)

        self.cell_input = QLineEdit()
        self.cell_input.setPlaceholderText(_("profile.cell_placeholder"))
        self.cell_input.textChanged.connect(self._on_phone_changed)
        cell_layout.addWidget(self.cell_input)

        # Phone validation status label
        self.phone_validation_label = QLabel("")
        self.phone_validation_label.setObjectName("validationLabel")
        self.phone_validation_label.setWordWrap(True)
        cell_layout.addWidget(self.phone_validation_label)

        self.cell_label = QLabel(_("profile.cell"))
        form_layout.addRow(self.cell_label, cell_container)

        self.cell_help = QLabel(_("profile.cell_help"))
        self.cell_help.setObjectName("helpLabel")
        form_layout.addRow("", self.cell_help)

        layout.addWidget(self.profile_group)

        # Status label
        self.status_label = QLabel("")
        layout.addWidget(self.status_label)

        # Button row
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.save_button = QPushButton(_("profile.save"))
        self.save_button.setObjectName("primaryButton")
        self.save_button.clicked.connect(self._on_save_clicked)
        button_layout.addWidget(self.save_button)

        layout.addLayout(button_layout)
        layout.addStretch()

    def _load_profile(self) -> None:
        """Load profile from configuration."""
        profile = self.config_manager.get("profile", {})

        self.name_input.setText(profile.get("name", ""))
        self.email_input.setText(profile.get("email", ""))
        self.cell_input.setText(profile.get("cell", ""))

        # Validate loaded phone number
        self._on_phone_changed(profile.get("cell", ""))

    def _on_phone_changed(self, text: str) -> None:
        """Handle phone number input changes with real-time validation."""
        if not text.strip():
            self.phone_validation_label.setText("")
            return

        result = validate_phone_number(text)
        if result.valid:
            # Simple user-friendly message: ✓ Country
            display = f"✓ {result.country_name}" if result.country_name else "✓ Valid"
            self.phone_validation_label.setText(display)
            self.phone_validation_label.setStyleSheet("color: #22c55e;")
        else:
            self.phone_validation_label.setText(result.error_message or _("profile.invalid_phone"))
            self.phone_validation_label.setStyleSheet("color: #ef4444;")

    def _validate_phone_number(self, phone: str) -> tuple[bool, str]:
        """Validate phone number using phonenumbers library.

        Args:
            phone: Phone number to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not phone:
            return True, ""  # Empty is okay

        result = validate_phone_number(phone)
        if result.valid:
            return True, ""
        return False, result.error_message or "Invalid phone number format"

    def _on_save_clicked(self) -> None:
        """Handle save button click."""
        try:
            # Get values
            name = self.name_input.text().strip()
            email = self.email_input.text().strip()
            cell = self.cell_input.text().strip()

            # Validate phone number
            is_valid, error_msg = self._validate_phone_number(cell)
            if not is_valid:
                self.status_label.setText(error_msg)
                self.status_label.setStyleSheet("color: #ef4444;")
                QMessageBox.warning(
                    self,
                    "Invalid Phone Number",
                    error_msg + "\n\nPlease enter a valid phone number in international format.\n"
                    "Example: +1 555 123 4567",
                )
                return

            # Update configuration
            self.config_manager.set("profile.name", name, save=False)
            self.config_manager.set("profile.email", email, save=False)
            self.config_manager.set("profile.cell", cell, save=True)

            # Update status
            self.status_label.setText(_("profile.saved"))
            self.status_label.setStyleSheet("color: #22c55e;")

            # Trigger callback
            if self.on_save:
                self.on_save()

        except Exception as e:
            logger.exception("Failed to save profile")
            self.status_label.setText(_("profile.save_error"))
            self.status_label.setStyleSheet("color: #ef4444;")
            QMessageBox.critical(
                self,
                _("errors.title"),
                str(e),
            )

    def retranslate_ui(self) -> None:
        """Update UI text after language change."""
        # Update labels
        self.name_label.setText(_("profile.name"))
        self.name_input.setPlaceholderText(_("profile.name_placeholder"))
        self.name_help.setText(_("profile.name_help"))

        self.email_label.setText(_("profile.email"))
        self.email_input.setPlaceholderText(_("profile.email_placeholder"))
        self.email_help.setText(_("profile.email_help"))

        self.cell_label.setText(_("profile.cell"))
        self.cell_input.setPlaceholderText(_("profile.cell_placeholder"))
        self.cell_help.setText(_("profile.cell_help"))

        self.save_button.setText(_("profile.save"))

        # Update group box title
        self.profile_group.setTitle(_("profile.title"))
