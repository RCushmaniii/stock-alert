"""
Settings widget for StockAlert.

Provides UI for editing global application settings.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from stockalert.core.api_key_manager import (
    get_api_key,
    set_api_key,
    test_api_key,
)
from stockalert.core.paths import get_bundled_assets_dir
from stockalert.core.service_controller import ServiceController, ServiceStatus
from stockalert.core.tier_limits import get_max_tickers, get_min_check_interval
from stockalert.i18n.translator import _

if TYPE_CHECKING:
    from stockalert.core.config import ConfigManager
    from stockalert.core.service_controller import ServiceState
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
        self._dirty = False  # Track unsaved changes
        self._original_values: dict = {}  # Track original values for change detection

        # Service controller
        self.service_controller = ServiceController(on_status_changed=self._on_service_status_changed)

        # Status update timer
        self._status_timer = QTimer(self)
        self._status_timer.timeout.connect(self._update_service_status)
        self._status_timer.start(5000)  # Update every 5 seconds

        self._setup_ui()
        self._load_settings()
        self._connect_change_signals()
        self._dirty = False  # Reset after initial load
        self._update_service_status()

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        layout.setSpacing(24)

        # Provider section
        self.api_group = QGroupBox(_("settings.provider_title"))
        api_layout = QFormLayout(self.api_group)
        api_layout.setVerticalSpacing(12)
        api_layout.setHorizontalSpacing(20)
        api_layout.setContentsMargins(24, 24, 24, 24)

        # Provider name (read-only)
        self.provider_name_label = QLabel(_("settings.provider_name") + ":")
        self.provider_label = QLabel("Finnhub")
        self.provider_label.setStyleSheet("font-weight: bold;")
        api_layout.addRow(self.provider_name_label, self.provider_label)

        # API Key input with paste button
        api_key_container = QWidget()
        api_key_layout = QHBoxLayout(api_key_container)
        api_key_layout.setContentsMargins(0, 0, 0, 0)
        api_key_layout.setSpacing(8)

        self.api_key_edit = QLineEdit()
        self.api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_edit.setPlaceholderText(_("settings.api_key_placeholder"))
        self.api_key_edit.setMinimumWidth(250)
        api_key_layout.addWidget(self.api_key_edit)

        self.paste_key_btn = QPushButton(_("settings.paste"))
        self.paste_key_btn.setObjectName("primaryButton")  # Orange - primary action
        self.paste_key_btn.setFixedWidth(100)
        self.paste_key_btn.clicked.connect(self._on_paste_api_key)
        api_key_layout.addWidget(self.paste_key_btn)

        self.test_key_btn = QPushButton(_("settings.test_connection"))
        self.test_key_btn.setObjectName("secondaryButton")  # Gray - secondary action
        self.test_key_btn.setFixedWidth(100)
        self.test_key_btn.clicked.connect(self._on_test_api_key)
        api_key_layout.addWidget(self.test_key_btn)

        self.api_key_label = QLabel(_("settings.api_key") + ":")
        api_layout.addRow(self.api_key_label, api_key_container)

        # API key help text with link
        self.api_help = QLabel(_("settings.api_key_help"))
        self.api_help.setObjectName("helpLabel")
        self.api_help.setOpenExternalLinks(True)
        self.api_help.setWordWrap(True)
        api_layout.addRow("", self.api_help)

        # Connection status
        self.api_status_label = QLabel("")
        self.api_status_label.setObjectName("apiStatusLabel")
        api_layout.addRow("", self.api_status_label)

        # License/Tier (populated after successful connection test)
        self.license_row_label = QLabel(_("settings.license") + ":")
        self.license_label = QLabel("")
        self.license_label.setStyleSheet("font-weight: bold; color: #00AA00;")
        api_layout.addRow(self.license_row_label, self.license_label)

        layout.addWidget(self.api_group)

        # Settings group
        self.settings_group = QGroupBox(_("settings.title"))
        form_layout = QFormLayout(self.settings_group)
        form_layout.setVerticalSpacing(16)
        form_layout.setHorizontalSpacing(20)
        form_layout.setContentsMargins(24, 32, 24, 24)

        # Tier Limits - hidden initially, shown after test connection
        self.tier_limits_row_label = QLabel(_("settings.tier_limits") + ":")
        self.tier_limits_label = QLabel("")
        self.tier_limits_label.setObjectName("helpLabel")
        self.tier_limits_label.setWordWrap(True)
        form_layout.addRow(self.tier_limits_row_label, self.tier_limits_label)
        # Hide initially - will show after successful test connection
        self.tier_limits_row_label.setVisible(False)
        self.tier_limits_label.setVisible(False)

        # Check interval with unit selector
        min_interval = get_min_check_interval()
        self.check_interval_label = QLabel(_("settings.check_interval"))
        self.check_interval_label.setStyleSheet("color: white; font-size: 14px; font-weight: bold;")

        interval_container = QWidget()
        interval_layout = QHBoxLayout(interval_container)
        interval_layout.setContentsMargins(0, 8, 0, 8)
        interval_layout.setSpacing(16)

        # Spinbox with hidden buttons - we'll add our own
        self.check_interval_spin = QSpinBox()
        self.check_interval_spin.setMinimumWidth(80)
        self.check_interval_spin.setMinimumHeight(40)
        self.check_interval_spin.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
        self.check_interval_spin.setStyleSheet("""
            QSpinBox {
                padding: 8px 12px;
                font-size: 14px;
                background-color: #2d2d2d;
                color: white;
                border: 1px solid #555;
                border-radius: 4px;
            }
        """)
        interval_layout.addWidget(self.check_interval_spin)

        # Custom up/down buttons with chevrons
        arrow_container = QWidget()
        arrow_layout = QVBoxLayout(arrow_container)
        arrow_layout.setContentsMargins(0, 0, 0, 0)
        arrow_layout.setSpacing(2)

        self.interval_up_btn = QPushButton("+")
        self.interval_up_btn.setFixedSize(28, 19)
        self.interval_up_btn.setStyleSheet("""
            QPushButton {
                background-color: #3d3d3d;
                color: white;
                border: 1px solid #555;
                border-radius: 3px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #5d5d5d; }
            QPushButton:pressed { background-color: #FF6A3D; }
        """)
        self.interval_up_btn.clicked.connect(lambda: self.check_interval_spin.stepUp())
        arrow_layout.addWidget(self.interval_up_btn)

        self.interval_down_btn = QPushButton("-")
        self.interval_down_btn.setFixedSize(28, 19)
        self.interval_down_btn.setStyleSheet("""
            QPushButton {
                background-color: #3d3d3d;
                color: white;
                border: 1px solid #555;
                border-radius: 3px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #5d5d5d; }
            QPushButton:pressed { background-color: #FF6A3D; }
        """)
        self.interval_down_btn.clicked.connect(lambda: self.check_interval_spin.stepDown())
        arrow_layout.addWidget(self.interval_down_btn)

        interval_layout.addWidget(arrow_container)

        # Unit selector (seconds, minutes, hours)
        self.interval_unit_combo = QComboBox()
        self.interval_unit_combo.addItem(_("settings.unit_seconds"), "seconds")
        self.interval_unit_combo.addItem(_("settings.unit_minutes"), "minutes")
        self.interval_unit_combo.addItem(_("settings.unit_hours"), "hours")
        self.interval_unit_combo.setMinimumWidth(110)
        self.interval_unit_combo.setMinimumHeight(40)
        self.interval_unit_combo.setStyleSheet("""
            QComboBox {
                padding: 8px 12px;
                font-size: 14px;
                background-color: #2d2d2d;
                color: white;
                border: 1px solid #555;
                border-radius: 4px;
            }
            QComboBox::drop-down {
                width: 0px;
                border: none;
            }
            QComboBox QAbstractItemView {
                background-color: #2d2d2d;
                color: white;
                selection-background-color: #FF6A3D;
                border: 1px solid #555;
            }
        """)
        self.interval_unit_combo.currentIndexChanged.connect(self._on_interval_unit_changed)
        interval_layout.addWidget(self.interval_unit_combo)

        # Dropdown button with chevron
        self.combo_dropdown_btn = QPushButton("v")
        self.combo_dropdown_btn.setFixedSize(28, 40)
        self.combo_dropdown_btn.setStyleSheet("""
            QPushButton {
                background-color: #3d3d3d;
                color: white;
                border: 1px solid #555;
                border-radius: 3px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #5d5d5d; }
            QPushButton:pressed { background-color: #FF6A3D; }
        """)
        self.combo_dropdown_btn.clicked.connect(lambda: self.interval_unit_combo.showPopup())
        interval_layout.addWidget(self.combo_dropdown_btn)

        interval_layout.addStretch()

        # Store min interval for validation
        self._min_interval_seconds = min_interval
        self._update_interval_range()

        form_layout.addRow(self.check_interval_label, interval_container)

        self.check_interval_help = QLabel(_("settings.check_interval_help"))
        self.check_interval_help.setObjectName("helpLabel")
        form_layout.addRow("", self.check_interval_help)

        # Cooldown - hidden, using default 300s
        self.cooldown_spin = QSpinBox()
        self.cooldown_spin.setRange(60, 7200)
        self.cooldown_spin.setValue(300)  # Default 5 minutes
        self.cooldown_spin.setVisible(False)

        layout.addWidget(self.settings_group)

        # Alert Settings group
        self.alerts_group = QGroupBox(_("settings.alerts_title"))
        alerts_layout = QFormLayout(self.alerts_group)
        alerts_layout.setVerticalSpacing(16)
        alerts_layout.setHorizontalSpacing(20)
        alerts_layout.setContentsMargins(24, 32, 24, 24)

        # Windows notifications with test button
        windows_container = QWidget()
        windows_layout = QHBoxLayout(windows_container)
        windows_layout.setContentsMargins(0, 0, 0, 0)
        windows_layout.setSpacing(16)
        self.windows_alerts_check = QCheckBox(_("settings.alerts_windows"))
        self.windows_alerts_check.stateChanged.connect(self._on_windows_alerts_changed)
        windows_layout.addWidget(self.windows_alerts_check)
        self.test_windows_btn = QPushButton(_("settings.test"))
        self.test_windows_btn.setObjectName("secondaryButton")
        self.test_windows_btn.setFixedWidth(80)
        self.test_windows_btn.clicked.connect(self._on_test_windows)
        windows_layout.addWidget(self.test_windows_btn)
        windows_layout.addStretch()
        alerts_layout.addRow("", windows_container)

        # Windows audio option (indented)
        audio_container = QWidget()
        audio_layout = QHBoxLayout(audio_container)
        audio_layout.setContentsMargins(24, 0, 0, 0)
        self.windows_audio_check = QCheckBox(_("settings.alerts_windows_audio"))
        audio_layout.addWidget(self.windows_audio_check)
        audio_layout.addStretch()
        alerts_layout.addRow("", audio_container)

        # SMS alerts (hidden - requires purchased Twilio number)
        # self.sms_alerts_check = QCheckBox(_("settings.alerts_sms"))
        # alerts_layout.addRow("", self.sms_alerts_check)
        # self.sms_alerts_help = QLabel(_("settings.alerts_sms_help"))
        # self.sms_alerts_help.setObjectName("helpLabel")
        # alerts_layout.addRow("", self.sms_alerts_help)

        # WhatsApp alerts with test button
        whatsapp_container = QWidget()
        whatsapp_layout = QHBoxLayout(whatsapp_container)
        whatsapp_layout.setContentsMargins(0, 0, 0, 0)
        whatsapp_layout.setSpacing(16)
        self.whatsapp_alerts_check = QCheckBox(_("settings.alerts_whatsapp"))
        self.whatsapp_alerts_check.stateChanged.connect(self._on_whatsapp_alerts_changed)
        whatsapp_layout.addWidget(self.whatsapp_alerts_check)
        self.test_whatsapp_btn = QPushButton(_("settings.test"))
        self.test_whatsapp_btn.setObjectName("secondaryButton")
        self.test_whatsapp_btn.setFixedWidth(80)
        self.test_whatsapp_btn.clicked.connect(self._on_test_whatsapp)
        whatsapp_layout.addWidget(self.test_whatsapp_btn)
        whatsapp_layout.addStretch()
        alerts_layout.addRow("", whatsapp_container)

        # WhatsApp status/help label - shows phone requirement
        self.whatsapp_status_label = QLabel("")
        self.whatsapp_status_label.setObjectName("helpLabel")
        alerts_layout.addRow("", self.whatsapp_status_label)

        # Email alerts (hidden for now)
        # self.email_alerts_check = QCheckBox(_("settings.alerts_email"))
        # alerts_layout.addRow("", self.email_alerts_check)
        # self.email_alerts_help = QLabel(_("settings.alerts_email_help"))
        # self.email_alerts_help.setObjectName("helpLabel")
        # alerts_layout.addRow("", self.email_alerts_help)

        layout.addWidget(self.alerts_group)

        # Background Service group (simplified - service always runs automatically)
        self.service_group = QGroupBox(_("settings.service_title"))
        service_main_layout = QVBoxLayout(self.service_group)
        service_main_layout.setSpacing(16)
        service_main_layout.setContentsMargins(24, 24, 24, 24)

        # Status row with indicator
        status_row = QHBoxLayout()
        self.service_status_label = QLabel(_("settings.service_status"))
        status_row.addWidget(self.service_status_label)

        self.service_status_indicator = QLabel("")
        self.service_status_indicator.setStyleSheet("font-size: 16px; color: gray;")
        status_row.addWidget(self.service_status_indicator)

        self.service_status_value = QLabel("")
        self.service_status_value.setObjectName("serviceStatus")
        status_row.addWidget(self.service_status_value)
        status_row.addStretch()
        service_main_layout.addLayout(status_row)

        # Help text explaining automatic behavior
        self.service_help = QLabel(_("settings.service_auto_help"))
        self.service_help.setObjectName("helpLabel")
        self.service_help.setWordWrap(True)
        service_main_layout.addWidget(self.service_help)

        # Autostart checkbox
        self.autostart_check = QCheckBox(_("settings.autostart"))
        self.autostart_check.setToolTip(_("settings.autostart_help"))
        self.autostart_check.stateChanged.connect(self._on_autostart_changed)
        service_main_layout.addWidget(self.autostart_check)

        service_main_layout.addStretch()
        layout.addWidget(self.service_group)

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

    def _on_whatsapp_alerts_changed(self, state: int) -> None:
        """Handle WhatsApp alerts checkbox change."""
        enabled = state == Qt.CheckState.Checked.value

        if enabled:
            # Check if phone number is configured
            profile = self.config_manager.get("profile", {})
            phone = profile.get("cell", "").strip()

            if not phone:
                # No phone number - disable and show message
                self.whatsapp_alerts_check.blockSignals(True)
                self.whatsapp_alerts_check.setChecked(False)
                self.whatsapp_alerts_check.blockSignals(False)
                self.whatsapp_status_label.setText(_("settings.alerts_whatsapp_requires_phone"))
                self.whatsapp_status_label.setStyleSheet("color: #00AA00; font-weight: bold;")
                self.test_whatsapp_btn.setEnabled(False)
            else:
                # Phone configured - allow enabling
                self.whatsapp_status_label.setText("")
                self.test_whatsapp_btn.setEnabled(True)
        else:
            self.whatsapp_status_label.setText("")
            self.test_whatsapp_btn.setEnabled(False)

    def _has_phone_number(self) -> bool:
        """Check if phone number is configured in profile."""
        profile = self.config_manager.get("profile", {})
        phone = profile.get("cell", "").strip()
        return bool(phone)

    def _on_interval_unit_changed(self, _index: int) -> None:
        """Handle interval unit change."""
        self._update_interval_range()

    def _update_interval_range(self) -> None:
        """Update spinbox range based on selected unit."""
        unit = self.interval_unit_combo.currentData()
        min_sec = self._min_interval_seconds

        if unit == "seconds":
            self.check_interval_spin.setRange(min_sec, 3600)
            self.check_interval_spin.setSingleStep(10)
        elif unit == "minutes":
            min_min = max(1, (min_sec + 59) // 60)  # Round up
            self.check_interval_spin.setRange(min_min, 60)
            self.check_interval_spin.setSingleStep(1)
        elif unit == "hours":
            self.check_interval_spin.setRange(1, 24)
            self.check_interval_spin.setSingleStep(1)

    def _get_interval_seconds(self) -> int:
        """Get current interval in seconds."""
        value = self.check_interval_spin.value()
        unit = self.interval_unit_combo.currentData()

        if unit == "minutes":
            return value * 60
        elif unit == "hours":
            return value * 3600
        return value

    def _set_interval_from_seconds(self, seconds: int) -> None:
        """Set interval spinbox and unit from seconds value."""
        # Choose the best unit for display
        if seconds >= 3600 and seconds % 3600 == 0:
            # Exact hours
            self.interval_unit_combo.setCurrentIndex(2)  # hours
            self._update_interval_range()
            self.check_interval_spin.setValue(seconds // 3600)
        elif seconds >= 60 and seconds % 60 == 0:
            # Exact minutes
            self.interval_unit_combo.setCurrentIndex(1)  # minutes
            self._update_interval_range()
            self.check_interval_spin.setValue(seconds // 60)
        else:
            # Seconds
            self.interval_unit_combo.setCurrentIndex(0)  # seconds
            self._update_interval_range()
            self.check_interval_spin.setValue(seconds)

    def _mark_dirty(self) -> None:
        """Mark settings as having unsaved changes."""
        self._dirty = True

    def has_unsaved_changes(self) -> bool:
        """Check if there are unsaved changes."""
        return self._dirty

    def _connect_change_signals(self) -> None:
        """Connect widget signals to mark dirty on change."""
        self.check_interval_spin.valueChanged.connect(self._mark_dirty)
        self.interval_unit_combo.currentIndexChanged.connect(self._mark_dirty)
        self.windows_alerts_check.stateChanged.connect(self._mark_dirty)
        self.windows_audio_check.stateChanged.connect(self._mark_dirty)
        self.whatsapp_alerts_check.stateChanged.connect(self._mark_dirty)

    def _load_settings(self) -> None:
        """Load settings from configuration."""
        settings = self.config_manager.settings
        alerts = settings.get("alerts", {})

        # Store original values for change detection
        self._original_values = {
            "check_interval": settings.get("check_interval", 600),
            "windows_enabled": alerts.get("windows_enabled", True),
            "windows_audio": alerts.get("windows_audio", True),
            "whatsapp_enabled": alerts.get("whatsapp_enabled", False),
        }

        # Load API key (masked)
        api_key = get_api_key()
        if api_key:
            self.api_key_edit.setText(api_key)
            self.api_status_label.setText("OK - " + _("settings.api_key_configured"))
            self.api_status_label.setStyleSheet("color: #00AA00;")
            self.license_label.setText("")
        else:
            self.api_status_label.setText(_("settings.api_key_not_set"))
            self.api_status_label.setStyleSheet("color: #FF6A3D;")
            self.license_label.setText("")

        # Load check interval (in seconds, enforce minimum)
        min_interval = get_min_check_interval()
        interval_seconds = settings.get("check_interval", min_interval)
        interval_seconds = max(interval_seconds, min_interval)
        self._set_interval_from_seconds(interval_seconds)

        self.cooldown_spin.setValue(settings.get("cooldown", 300))

        # Load alert settings
        self.windows_alerts_check.setChecked(alerts.get("windows_enabled", True))
        self.windows_audio_check.setChecked(alerts.get("windows_audio", True))
        self.windows_audio_check.setEnabled(alerts.get("windows_enabled", True))

        # WhatsApp - check if phone number is configured
        has_phone = self._has_phone_number()
        whatsapp_enabled = alerts.get("whatsapp_enabled", False) and has_phone
        self.whatsapp_alerts_check.setChecked(whatsapp_enabled)
        self.test_whatsapp_btn.setEnabled(whatsapp_enabled)

        if not has_phone:
            self.whatsapp_alerts_check.setEnabled(True)
            self.whatsapp_status_label.setText("")
        else:
            self.whatsapp_status_label.setText("")

        # Load autostart state (block signals to prevent triggering change handler)
        from stockalert.core.windows_service import is_autostart_enabled
        self.autostart_check.blockSignals(True)
        self.autostart_check.setChecked(is_autostart_enabled())
        self.autostart_check.blockSignals(False)

    def _on_save_clicked(self) -> None:
        """Handle save button click."""
        try:
            changes = []  # Track what changed

            # Compare against original values loaded at startup (not current config)
            orig = self._original_values

            # Save API key through BOTH systems to ensure it persists
            api_key = self.api_key_edit.text().strip()
            old_api_key = get_api_key() or ""
            if api_key and api_key != old_api_key:
                set_api_key(api_key)
                self.config_manager.set("api_key", api_key, save=False)
                changes.append("API Key: Updated")

            # Get check interval in seconds (converted from displayed unit)
            check_interval = self._get_interval_seconds()
            old_interval = orig.get("check_interval", 600)
            if check_interval != old_interval:
                changes.append(f"Check Interval: {self._format_interval(old_interval)} -> {self._format_interval(check_interval)}")

            # Use default cooldown (hidden from UI)
            cooldown = self.cooldown_spin.value()

            # Get alert settings
            windows_enabled = self.windows_alerts_check.isChecked()
            old_windows = orig.get("windows_enabled", True)
            if windows_enabled != old_windows:
                changes.append(f"Windows Notifications: {'Enabled' if windows_enabled else 'Disabled'}")

            windows_audio = self.windows_audio_check.isChecked()
            old_audio = orig.get("windows_audio", True)
            if windows_audio != old_audio:
                changes.append(f"Notification Sound: {'Enabled' if windows_audio else 'Disabled'}")

            whatsapp_enabled = self.whatsapp_alerts_check.isChecked()
            old_whatsapp = orig.get("whatsapp_enabled", False)
            if whatsapp_enabled != old_whatsapp:
                changes.append(f"WhatsApp Alerts: {'Enabled' if whatsapp_enabled else 'Disabled'}")

            # Update configuration
            self.config_manager.set("settings.check_interval", check_interval, save=False)
            self.config_manager.set("settings.cooldown", cooldown, save=False)
            self.config_manager.set("settings.alerts.windows_enabled", windows_enabled, save=False)
            self.config_manager.set("settings.alerts.windows_audio", windows_audio, save=False)
            self.config_manager.set("settings.alerts.whatsapp_enabled", whatsapp_enabled, save=True)

            # Update status label
            self.status_label.setText(_("settings.saved"))
            self.status_label.setStyleSheet("color: green;")
            self._dirty = False

            # Update original values to new saved values (for future change detection)
            self._original_values = {
                "check_interval": check_interval,
                "windows_enabled": windows_enabled,
                "windows_audio": windows_audio,
                "whatsapp_enabled": whatsapp_enabled,
            }

            # Show dialog with changes
            if changes:
                changes_text = "\n".join(f"  - {c}" for c in changes)
                QMessageBox.information(
                    self,
                    "AI StockAlert - Settings Saved",
                    f"Settings saved successfully!\n\nChanges:\n{changes_text}",
                )
            else:
                QMessageBox.information(
                    self,
                    "AI StockAlert - Settings Saved",
                    "Settings saved successfully!\n\nNo changes detected.",
                )

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

    def _format_interval(self, seconds: int) -> str:
        """Format interval in human-readable form."""
        if seconds >= 3600 and seconds % 3600 == 0:
            hours = seconds // 3600
            return f"{hours} hour{'s' if hours > 1 else ''}"
        elif seconds >= 60 and seconds % 60 == 0:
            minutes = seconds // 60
            return f"{minutes} minute{'s' if minutes > 1 else ''}"
        else:
            return f"{seconds} seconds"

    def retranslate_ui(self) -> None:
        """Update UI text after language change."""
        # Update group box titles
        self.api_group.setTitle(_("settings.provider_title"))
        self.settings_group.setTitle(_("settings.title"))
        self.alerts_group.setTitle(_("settings.alerts_title"))
        self.service_group.setTitle(_("settings.service_title"))

        # Provider section
        self.provider_name_label.setText(_("settings.provider_name") + ":")
        self.api_key_label.setText(_("settings.api_key") + ":")
        self.api_key_edit.setPlaceholderText(_("settings.api_key_placeholder"))
        self.paste_key_btn.setText(_("settings.paste"))
        self.test_key_btn.setText(_("settings.test_connection"))
        self.api_help.setText(_("settings.api_key_help"))
        self.license_row_label.setText(_("settings.license") + ":")
        self.tier_limits_row_label.setText(_("settings.tier_limits") + ":")

        # Settings section
        self.check_interval_label.setText(_("settings.check_interval"))
        self.check_interval_help.setText(_("settings.check_interval_help"))
        # Update interval unit combo
        self.interval_unit_combo.setItemText(0, _("settings.unit_seconds"))
        self.interval_unit_combo.setItemText(1, _("settings.unit_minutes"))
        self.interval_unit_combo.setItemText(2, _("settings.unit_hours"))

        # Alert settings
        self.windows_alerts_check.setText(_("settings.alerts_windows"))
        self.windows_audio_check.setText(_("settings.alerts_windows_audio"))
        self.test_windows_btn.setText(_("settings.test"))
        self.whatsapp_alerts_check.setText(_("settings.alerts_whatsapp"))
        self.test_whatsapp_btn.setText(_("settings.test"))

        self.save_button.setText(_("settings.save"))

        # Service settings
        self.service_status_label.setText(_("settings.service_status"))
        self.service_help.setText(_("settings.service_auto_help"))
        self.autostart_check.setText(_("settings.autostart"))
        self.autostart_check.setToolTip(_("settings.autostart_help"))

    def _on_service_status_changed(self, state: ServiceState) -> None:  # noqa: ARG002
        """Handle service status change callback."""
        self._update_service_status()

    def _update_service_status(self) -> None:
        """Update the service status display."""
        state = self.service_controller.get_state()
        status_text = self.service_controller.get_status_display()

        self.service_status_value.setText(status_text)

        # Update status indicator color and text color
        if state.status == ServiceStatus.RUNNING:
            # Green indicator and text for running
            self.service_status_indicator.setText("")
            self.service_status_indicator.setStyleSheet("font-size: 16px; color: #00CC00;")
            self.service_status_value.setStyleSheet("color: #00CC00; font-weight: bold;")
        elif state.status == ServiceStatus.STOPPED:
            # Red indicator for stopped
            self.service_status_indicator.setText("")
            self.service_status_indicator.setStyleSheet("font-size: 16px; color: #CC0000;")
            self.service_status_value.setStyleSheet("color: gray;")
        else:
            # Orange indicator for transitioning/unknown
            self.service_status_indicator.setText("")
            self.service_status_indicator.setStyleSheet("font-size: 16px; color: #FF9900;")
            self.service_status_value.setStyleSheet("color: orange;")

    def _on_autostart_changed(self, state: int) -> None:
        """Handle autostart checkbox change."""
        from stockalert.core.windows_service import enable_autostart, disable_autostart
        
        enabled = state == Qt.CheckState.Checked.value
        if enabled:
            success, message = enable_autostart()
        else:
            success, message = disable_autostart()
        
        if success:
            self.status_label.setText(message)
            self.status_label.setStyleSheet("color: green;")
        else:
            self.status_label.setText(message)
            self.status_label.setStyleSheet("color: red;")
            # Revert checkbox state on failure
            self.autostart_check.blockSignals(True)
            self.autostart_check.setChecked(not enabled)
            self.autostart_check.blockSignals(False)

    def _on_paste_api_key(self) -> None:
        """Paste API key from clipboard."""
        clipboard = QApplication.clipboard()
        if clipboard is None:
            return
        text = clipboard.text()
        if text:
            self.api_key_edit.setText(text.strip())
            self.api_status_label.setText(_("settings.api_key_pasted"))
            self.api_status_label.setStyleSheet("color: #888888;")

    def _on_test_api_key(self) -> None:
        """Test the API key connection."""
        api_key = self.api_key_edit.text().strip()

        if not api_key:
            self.api_status_label.setText(_("settings.api_key_empty"))
            self.api_status_label.setStyleSheet("color: #FF6A3D;")
            return

        # Show testing status
        self.api_status_label.setText(_("settings.testing_connection"))
        self.api_status_label.setStyleSheet("color: #888888;")
        self.test_key_btn.setEnabled(False)

        # Force UI update
        QApplication.processEvents()

        # Test the key
        success, message = test_api_key(api_key)

        if success:
            # Auto-save the API key on successful test
            set_api_key(api_key)
            self.api_status_label.setText("✓ Connected successfully (saved)")
            self.api_status_label.setStyleSheet("color: #00AA00;")
            # Update license field to show Free tier
            self.license_label.setText(_("settings.license_free"))
            # Show tier limits after successful connection
            max_tickers = get_max_tickers()
            min_interval = get_min_check_interval()
            tier_text = _("settings.tier_limits_free").format(
                max_tickers=max_tickers, min_interval=min_interval
            )
            self.tier_limits_label.setText(tier_text)
            self.tier_limits_row_label.setVisible(True)
            self.tier_limits_label.setVisible(True)
        else:
            self.api_status_label.setText("✗ " + message)
            self.api_status_label.setStyleSheet("color: #FF0000;")
            # Clear license on failure
            self.license_label.setText("")
            # Hide tier limits on failure
            self.tier_limits_row_label.setVisible(False)
            self.tier_limits_label.setVisible(False)

        self.test_key_btn.setEnabled(True)

    def _on_test_windows(self) -> None:
        """Test Windows notification using Windows-Toasts library."""
        # Show info dialog FIRST - notification will be sent after user clicks OK
        result = QMessageBox.information(
            self,
            "AI StockAlert - Windows Test",
            "A test notification will be sent after you click OK.\n\n"
            "Check your Windows notification area (bottom-right corner).\n\n"
            "If you don't see it, check that Focus Assist / Do Not Disturb is off.",
            QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel,
        )

        if result != QMessageBox.StandardButton.Ok:
            return

        self.test_windows_btn.setEnabled(False)
        self.status_label.setText(_("settings.testing_windows"))
        self.status_label.setStyleSheet("color: #888888;")
        QApplication.processEvents()

        # Small delay so user can see the notification area
        QTimer.singleShot(500, self._send_test_windows_notification)

    def _send_test_windows_notification(self) -> None:
        """Actually send the Windows test notification."""
        try:
            from windows_toasts import Toast, WindowsToaster

            toaster = WindowsToaster("AI StockAlert")
            toast = Toast()
            toast.text_fields = [
                "StockAlert Test",
                "This is a test notification. If you see this, Windows notifications are working!",
            ]

            # Check if audio is enabled
            play_audio = self.windows_audio_check.isChecked()
            if not play_audio:
                from windows_toasts import ToastAudio
                toast.audio = ToastAudio(silent=True)

            toaster.show_toast(toast)

            self.status_label.setText("OK - " + _("settings.test_windows_success"))
            self.status_label.setStyleSheet("color: #00AA00; font-weight: bold;")

        except Exception as e:
            logger.exception("Failed to test Windows notification")
            self.status_label.setText(f"Error: {e}")
            self.status_label.setStyleSheet("color: #FF0000; font-weight: bold;")
            QMessageBox.critical(self, "Windows Test Error", str(e))

        self.test_windows_btn.setEnabled(True)

    def _on_test_whatsapp(self) -> None:
        """Test WhatsApp notification."""
        from pathlib import Path

        from stockalert.core.alert_manager import AlertManager, AlertSettings

        # Get phone number from profile
        profile = self.config_manager.get("profile", {})
        phone_number = profile.get("cell", "")

        if not phone_number:
            QMessageBox.warning(
                self,
                _("settings.test_whatsapp_title"),
                _("settings.test_whatsapp_no_phone"),
            )
            return

        self.test_whatsapp_btn.setEnabled(False)
        self.status_label.setText(_("settings.testing_whatsapp"))
        self.status_label.setStyleSheet("color: #888888;")
        QApplication.processEvents()

        try:
            # Create temporary AlertManager for testing
            # Icon is bundled with the app (in _MEIPASS for PyInstaller)
            icon_path = get_bundled_assets_dir() / "stock_alert.ico"
            settings = AlertSettings(
                whatsapp_enabled=True,
                phone_number=phone_number,
            )
            alert_manager = AlertManager(
                icon_path=icon_path if icon_path.exists() else None,
                settings=settings,
            )

            success, message = alert_manager.test_whatsapp(phone_number)

            if success:
                self.status_label.setText("✓ " + _("settings.test_whatsapp_success"))
                self.status_label.setStyleSheet("color: #00AA00; font-weight: bold;")
                QMessageBox.information(
                    self,
                    "WhatsApp Test",
                    f"Test message sent to {phone_number}!\n\nCheck your WhatsApp for the message.",
                )
            else:
                self.status_label.setText("✗ " + message)
                self.status_label.setStyleSheet("color: #FF0000; font-weight: bold;")
                # Provide helpful error message
                if "not configured" in message.lower() or "401" in message.lower() or "unauthorized" in message.lower():
                    QMessageBox.warning(
                        self,
                        "WhatsApp Test Failed",
                        "WhatsApp API key is not configured or invalid.\n\n"
                        "To enable WhatsApp alerts:\n"
                        "1. Enter your StockAlert API key in the field above\n"
                        "2. Click Save to store it securely\n"
                        "3. Try the test again\n\n"
                        "Contact support if you need an API key.",
                    )
                else:
                    QMessageBox.warning(self, "WhatsApp Test Failed", message)

        except Exception as e:
            logger.exception("Failed to test WhatsApp")
            self.status_label.setText(f"✗ {e}")
            self.status_label.setStyleSheet("color: #FF0000; font-weight: bold;")
            error_msg = str(e)
            # Check for common Twilio sandbox errors
            if "21608" in error_msg or "not a valid" in error_msg.lower():
                QMessageBox.warning(
                    self,
                    "WhatsApp Sandbox",
                    "Your phone number hasn't joined the Twilio Sandbox.\n\n"
                    "To join:\n"
                    "1. Open WhatsApp\n"
                    "2. Send a message to +1 415 523 8886\n"
                    "3. Type: join <your-sandbox-code>\n\n"
                    "Find your sandbox code at:\n"
                    "console.twilio.com > Messaging > Try it out > Send a WhatsApp message",
                )
            else:
                QMessageBox.critical(self, "WhatsApp Test Error", error_msg)

        self.test_whatsapp_btn.setEnabled(True)
