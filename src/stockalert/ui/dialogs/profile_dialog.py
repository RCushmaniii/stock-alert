"""
Profile widget for StockAlert.

Provides UI for editing user profile information.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Callable

from PyQt6.QtCore import Qt
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
        profile_group = QGroupBox(_("profile.title"))
        form_layout = QFormLayout(profile_group)
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

        # Cell/Phone
        self.cell_input = QLineEdit()
        self.cell_input.setPlaceholderText(_("profile.cell_placeholder"))
        self.cell_label = QLabel(_("profile.cell"))
        form_layout.addRow(self.cell_label, self.cell_input)

        self.cell_help = QLabel(_("profile.cell_help"))
        self.cell_help.setObjectName("helpLabel")
        form_layout.addRow("", self.cell_help)

        layout.addWidget(profile_group)

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

    def _on_save_clicked(self) -> None:
        """Handle save button click."""
        try:
            # Get values
            name = self.name_input.text().strip()
            email = self.email_input.text().strip()
            cell = self.cell_input.text().strip()

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

        # Update parent group box
        parent_group = self.name_input.parent()
        if isinstance(parent_group, QGroupBox):
            parent_group.setTitle(_("profile.title"))
