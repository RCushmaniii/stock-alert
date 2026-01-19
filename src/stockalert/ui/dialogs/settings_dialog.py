"""
Settings widget for StockAlert.

Provides UI for editing global application settings.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Callable

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from stockalert.i18n.translator import _

if TYPE_CHECKING:
    from stockalert.core.config import ConfigManager
    from stockalert.i18n.translator import Translator

logger = logging.getLogger(__name__)


class SettingsWidget(QWidget):
    """Widget for editing global settings."""

    def __init__(
        self,
        config_manager: ConfigManager,
        translator: Translator,
        on_save: Callable[[], None] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        """Initialize the settings widget.

        Args:
            config_manager: Configuration manager instance
            translator: Translator for i18n
            on_save: Callback when settings are saved
            parent: Parent widget
        """
        super().__init__(parent)
        self.config_manager = config_manager
        self.translator = translator
        self.on_save = on_save

        self._setup_ui()
        self._load_settings()

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        layout.setSpacing(24)

        # Settings group
        settings_group = QGroupBox(_("settings.title"))
        form_layout = QFormLayout(settings_group)
        form_layout.setVerticalSpacing(16)
        form_layout.setHorizontalSpacing(20)
        form_layout.setContentsMargins(24, 32, 24, 24)

        # Check interval with horizontal radio buttons
        self.check_interval_label = QLabel(_("settings.check_interval"))

        interval_container = QWidget()
        interval_layout = QHBoxLayout(interval_container)
        interval_layout.setContentsMargins(0, 0, 0, 0)
        interval_layout.setSpacing(12)

        self.check_interval_spin = QSpinBox()
        self.check_interval_spin.setRange(1, 999)
        self.check_interval_spin.setFixedWidth(80)
        interval_layout.addWidget(self.check_interval_spin)

        # Radio button group for time unit
        self.interval_unit_group = QButtonGroup(self)

        self.interval_sec_radio = QRadioButton("sec")
        self.interval_sec_radio.setObjectName("unitRadio")
        self.interval_unit_group.addButton(self.interval_sec_radio, 1)
        interval_layout.addWidget(self.interval_sec_radio)

        self.interval_min_radio = QRadioButton("min")
        self.interval_min_radio.setObjectName("unitRadio")
        self.interval_unit_group.addButton(self.interval_min_radio, 60)
        interval_layout.addWidget(self.interval_min_radio)

        self.interval_hrs_radio = QRadioButton("hrs")
        self.interval_hrs_radio.setObjectName("unitRadio")
        self.interval_unit_group.addButton(self.interval_hrs_radio, 3600)
        interval_layout.addWidget(self.interval_hrs_radio)

        interval_layout.addStretch()

        form_layout.addRow(self.check_interval_label, interval_container)

        self.check_interval_help = QLabel(_("settings.check_interval_help"))
        self.check_interval_help.setObjectName("helpLabel")
        form_layout.addRow("", self.check_interval_help)

        # Cooldown
        self.cooldown_spin = QSpinBox()
        self.cooldown_spin.setRange(60, 7200)
        self.cooldown_spin.setSuffix(" s")
        self.cooldown_label = QLabel(_("settings.cooldown"))
        form_layout.addRow(self.cooldown_label, self.cooldown_spin)

        self.cooldown_help = QLabel(_("settings.cooldown_help"))
        self.cooldown_help.setObjectName("helpLabel")
        form_layout.addRow("", self.cooldown_help)

        layout.addWidget(settings_group)

        # Alert Settings group
        alerts_group = QGroupBox(_("settings.alerts_title"))
        alerts_layout = QFormLayout(alerts_group)
        alerts_layout.setVerticalSpacing(16)
        alerts_layout.setHorizontalSpacing(20)
        alerts_layout.setContentsMargins(24, 32, 24, 24)

        # Windows notifications
        self.windows_alerts_check = QCheckBox(_("settings.alerts_windows"))
        self.windows_alerts_check.stateChanged.connect(self._on_windows_alerts_changed)
        alerts_layout.addRow("", self.windows_alerts_check)

        # Windows audio option (indented)
        audio_container = QWidget()
        audio_layout = QHBoxLayout(audio_container)
        audio_layout.setContentsMargins(24, 0, 0, 0)
        self.windows_audio_check = QCheckBox(_("settings.alerts_windows_audio"))
        audio_layout.addWidget(self.windows_audio_check)
        audio_layout.addStretch()
        alerts_layout.addRow("", audio_container)

        # Email alerts
        self.email_alerts_check = QCheckBox(_("settings.alerts_email"))
        alerts_layout.addRow("", self.email_alerts_check)

        self.email_alerts_help = QLabel(_("settings.alerts_email_help"))
        self.email_alerts_help.setObjectName("helpLabel")
        alerts_layout.addRow("", self.email_alerts_help)

        # WhatsApp alerts
        self.whatsapp_alerts_check = QCheckBox(_("settings.alerts_whatsapp"))
        alerts_layout.addRow("", self.whatsapp_alerts_check)

        self.whatsapp_alerts_help = QLabel(_("settings.alerts_whatsapp_help"))
        self.whatsapp_alerts_help.setObjectName("helpLabel")
        alerts_layout.addRow("", self.whatsapp_alerts_help)

        layout.addWidget(alerts_group)

        # Language Settings group
        lang_group = QGroupBox(_("settings.language_title"))
        lang_layout = QFormLayout(lang_group)
        lang_layout.setVerticalSpacing(16)
        lang_layout.setHorizontalSpacing(20)
        lang_layout.setContentsMargins(24, 32, 24, 24)

        # Language
        self.language_combo = QComboBox()
        self.language_combo.addItem("English", "en")
        self.language_combo.addItem("Español", "es")
        self.language_label = QLabel(_("settings.language"))
        lang_layout.addRow(self.language_label, self.language_combo)

        self.language_help = QLabel(_("settings.language_help"))
        self.language_help.setObjectName("helpLabel")
        lang_layout.addRow("", self.language_help)

        layout.addWidget(lang_group)

        # Status label
        self.status_label = QLabel("")
        layout.addWidget(self.status_label)

        # Button row
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.save_button = QPushButton(_("settings.save"))
        self.save_button.setObjectName("primaryButton")
        self.save_button.clicked.connect(self._on_save_clicked)
        button_layout.addWidget(self.save_button)

        layout.addLayout(button_layout)
        layout.addStretch()

    def _on_windows_alerts_changed(self, state: int) -> None:
        """Handle Windows alerts checkbox change."""
        enabled = state == Qt.CheckState.Checked.value
        self.windows_audio_check.setEnabled(enabled)
        if not enabled:
            self.windows_audio_check.setChecked(False)

    def _load_settings(self) -> None:
        """Load settings from configuration."""
        settings = self.config_manager.settings

        # Load check interval and determine best unit
        interval_seconds = settings.get("check_interval", 60)
        if interval_seconds >= 3600 and interval_seconds % 3600 == 0:
            self.check_interval_spin.setValue(interval_seconds // 3600)
            self.interval_hrs_radio.setChecked(True)
        elif interval_seconds >= 60 and interval_seconds % 60 == 0:
            self.check_interval_spin.setValue(interval_seconds // 60)
            self.interval_min_radio.setChecked(True)
        else:
            self.check_interval_spin.setValue(interval_seconds)
            self.interval_sec_radio.setChecked(True)

        self.cooldown_spin.setValue(settings.get("cooldown", 300))

        # Load alert settings
        alerts = settings.get("alerts", {})
        self.windows_alerts_check.setChecked(alerts.get("windows_enabled", True))
        self.windows_audio_check.setChecked(alerts.get("windows_audio", True))
        self.windows_audio_check.setEnabled(alerts.get("windows_enabled", True))
        self.email_alerts_check.setChecked(alerts.get("email_enabled", False))
        self.whatsapp_alerts_check.setChecked(alerts.get("whatsapp_enabled", False))

        # Set language combo
        current_lang = settings.get("language", "en")
        index = self.language_combo.findData(current_lang)
        if index >= 0:
            self.language_combo.setCurrentIndex(index)

    def _on_save_clicked(self) -> None:
        """Handle save button click."""
        try:
            # Get check interval in seconds
            interval_value = self.check_interval_spin.value()
            unit_multiplier = self.interval_unit_group.checkedId()
            if unit_multiplier < 1:
                unit_multiplier = 1  # Default to seconds
            check_interval = interval_value * unit_multiplier

            cooldown = self.cooldown_spin.value()
            language = self.language_combo.currentData()

            # Get alert settings
            windows_enabled = self.windows_alerts_check.isChecked()
            windows_audio = self.windows_audio_check.isChecked()
            email_enabled = self.email_alerts_check.isChecked()
            whatsapp_enabled = self.whatsapp_alerts_check.isChecked()

            # Update configuration
            self.config_manager.set("settings.check_interval", check_interval, save=False)
            self.config_manager.set("settings.cooldown", cooldown, save=False)
            self.config_manager.set("settings.alerts.windows_enabled", windows_enabled, save=False)
            self.config_manager.set("settings.alerts.windows_audio", windows_audio, save=False)
            self.config_manager.set("settings.alerts.email_enabled", email_enabled, save=False)
            self.config_manager.set("settings.alerts.whatsapp_enabled", whatsapp_enabled, save=False)
            self.config_manager.set("settings.language", language, save=True)

            # Update status
            self.status_label.setText(_("settings.saved"))
            self.status_label.setStyleSheet("color: green;")

            # Trigger callback
            if self.on_save:
                self.on_save()

        except Exception as e:
            logger.exception("Failed to save settings")
            self.status_label.setText(_("settings.save_error"))
            self.status_label.setStyleSheet("color: red;")
            QMessageBox.critical(
                self,
                _("errors.title"),
                str(e),
            )

    def retranslate_ui(self) -> None:
        """Update UI text after language change."""
        # Update labels
        self.check_interval_label.setText(_("settings.check_interval"))
        self.check_interval_help.setText(_("settings.check_interval_help"))
        self.cooldown_label.setText(_("settings.cooldown"))
        self.cooldown_help.setText(_("settings.cooldown_help"))

        # Alert settings
        self.windows_alerts_check.setText(_("settings.alerts_windows"))
        self.windows_audio_check.setText(_("settings.alerts_windows_audio"))
        self.email_alerts_check.setText(_("settings.alerts_email"))
        self.email_alerts_help.setText(_("settings.alerts_email_help"))
        self.whatsapp_alerts_check.setText(_("settings.alerts_whatsapp"))
        self.whatsapp_alerts_help.setText(_("settings.alerts_whatsapp_help"))

        self.language_label.setText(_("settings.language"))
        self.language_help.setText(_("settings.language_help"))
        self.save_button.setText(_("settings.save"))
