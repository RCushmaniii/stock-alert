"""
Main application window for StockAlert.

PyQt6-based responsive GUI with header, footer, tabs, and theme support.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Callable

from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QCloseEvent, QDesktopServices, QIcon
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QStatusBar,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from stockalert.i18n.translator import _
from stockalert.ui.dialogs.profile_dialog import ProfileWidget
from stockalert.ui.dialogs.settings_dialog import SettingsWidget
from stockalert.ui.dialogs.ticker_dialog import TickerDialog

if TYPE_CHECKING:
    from stockalert.core.config import ConfigManager
    from stockalert.i18n.translator import Translator

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """Main application window with header, footer, tabs, and theme support."""

    CONTENT_MAX_WIDTH = 1200
    CONTENT_PADDING = 40

    def __init__(
        self,
        config_manager: ConfigManager,
        translator: Translator,
        on_settings_changed: Callable[[], None] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        """Initialize the main window.

        Args:
            config_manager: Configuration manager instance
            translator: Translator for i18n
            on_settings_changed: Callback when settings are saved
            parent: Parent widget
        """
        super().__init__(parent)
        self.config_manager = config_manager
        self.translator = translator
        self.on_settings_changed = on_settings_changed
        self._current_theme = "dark"

        self._setup_ui()
        self._load_data()
        self._apply_theme(self._current_theme)

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        self.setWindowTitle(_("app.name"))

        # Full screen by default
        self.showMaximized()

        # Load icon
        icon_path = Path(__file__).parent.parent.parent.parent / "stock_alert.ico"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

        # Main central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Header
        self._create_header(main_layout)

        # Content area with scroll
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setObjectName("contentScrollArea")

        # Content container (centered with max-width)
        content_container = QWidget()
        content_container.setObjectName("contentContainer")
        content_layout = QVBoxLayout(content_container)
        content_layout.setContentsMargins(
            self.CONTENT_PADDING,
            self.CONTENT_PADDING,
            self.CONTENT_PADDING,
            self.CONTENT_PADDING,
        )
        content_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)

        # Inner content with max width
        inner_content = QWidget()
        inner_content.setObjectName("innerContent")
        inner_content.setMaximumWidth(self.CONTENT_MAX_WIDTH)
        inner_content.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        inner_layout = QVBoxLayout(inner_content)
        inner_layout.setContentsMargins(0, 0, 0, 0)

        # Tab widget
        self.tabs = QTabWidget()
        self.tabs.setObjectName("mainTabs")
        inner_layout.addWidget(self.tabs)

        # Profile tab
        self.profile_widget = ProfileWidget(
            config_manager=self.config_manager,
            translator=self.translator,
            on_save=self._on_settings_saved,
        )
        self.tabs.addTab(self.profile_widget, _("tabs.profile"))

        # Settings tab
        self.settings_widget = SettingsWidget(
            config_manager=self.config_manager,
            translator=self.translator,
            on_save=self._on_settings_saved,
        )
        self.tabs.addTab(self.settings_widget, _("tabs.settings"))

        # Tickers tab
        self.tickers_widget = self._create_tickers_tab()
        self.tabs.addTab(self.tickers_widget, _("tabs.tickers"))

        # Help tab
        self.help_widget = self._create_help_tab()
        self.tabs.addTab(self.help_widget, _("tabs.help"))

        content_layout.addWidget(inner_content)
        scroll_area.setWidget(content_container)
        main_layout.addWidget(scroll_area, 1)

        # Footer
        self._create_footer(main_layout)

        # Status bar
        self.status_bar = QStatusBar()
        self.status_bar.setObjectName("statusBar")
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage(_("status.ready"))

    def _create_header(self, parent_layout: QVBoxLayout) -> None:
        """Create the header with logo, theme switcher, and language switcher."""
        header = QFrame()
        header.setObjectName("header")
        header.setFixedHeight(70)

        # Outer layout for full-width background
        header_outer = QHBoxLayout(header)
        header_outer.setContentsMargins(0, 0, 0, 0)
        header_outer.setSpacing(0)

        # Add stretch to center the inner content
        header_outer.addStretch()

        # Inner container with max-width matching content
        header_inner = QWidget()
        header_inner.setObjectName("headerInner")
        header_inner.setFixedWidth(self.CONTENT_MAX_WIDTH)
        header_layout = QHBoxLayout(header_inner)
        header_layout.setContentsMargins(0, 0, 0, 0)

        # Logo / App name
        logo_label = QLabel("AI StockAlert")
        logo_label.setObjectName("headerLogo")
        header_layout.addWidget(logo_label)

        header_layout.addStretch()

        # Language switcher - EN | ES style
        self.lang_en_btn = QPushButton("EN")
        self.lang_en_btn.setObjectName("langButton")
        self.lang_en_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.lang_en_btn.setCheckable(True)
        self.lang_en_btn.clicked.connect(lambda: self._set_language("en"))
        header_layout.addWidget(self.lang_en_btn)

        lang_separator = QLabel("|")
        lang_separator.setObjectName("langSeparator")
        header_layout.addWidget(lang_separator)

        self.lang_es_btn = QPushButton("ES")
        self.lang_es_btn.setObjectName("langButton")
        self.lang_es_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.lang_es_btn.setCheckable(True)
        self.lang_es_btn.clicked.connect(lambda: self._set_language("es"))
        header_layout.addWidget(self.lang_es_btn)

        # Set initial language state
        current_lang = self.config_manager.get("settings.language", "en")
        self._update_lang_buttons(current_lang)

        # Spacer
        header_layout.addSpacing(24)

        # Theme switcher - Sun/Moon icon button
        self.theme_btn = QPushButton()
        self.theme_btn.setObjectName("themeButton")
        self.theme_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.theme_btn.setFixedSize(40, 40)
        self.theme_btn.clicked.connect(self._toggle_theme)
        self._update_theme_icon()
        header_layout.addWidget(self.theme_btn)

        header_outer.addWidget(header_inner)
        header_outer.addStretch()

        parent_layout.addWidget(header)

    def _create_footer(self, parent_layout: QVBoxLayout) -> None:
        """Create the footer with links."""
        footer = QFrame()
        footer.setObjectName("footer")
        footer.setFixedHeight(50)

        # Outer layout for full-width background
        footer_outer = QHBoxLayout(footer)
        footer_outer.setContentsMargins(0, 0, 0, 0)
        footer_outer.setSpacing(0)

        # Add stretch to center the inner content
        footer_outer.addStretch()

        # Inner container with max-width matching content
        footer_inner = QWidget()
        footer_inner.setObjectName("footerInner")
        footer_inner.setFixedWidth(self.CONTENT_MAX_WIDTH)
        footer_layout = QHBoxLayout(footer_inner)
        footer_layout.setContentsMargins(0, 0, 0, 0)

        # Copyright
        self.copyright_label = QLabel(_("about.copyright"))
        self.copyright_label.setObjectName("footerText")
        footer_layout.addWidget(self.copyright_label)

        footer_layout.addStretch()

        # Links
        self.website_btn = QPushButton(_("footer.website"))
        self.website_btn.setObjectName("footerLink")
        self.website_btn.setFlat(True)
        self.website_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.website_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://rcsoftware.com")))
        footer_layout.addWidget(self.website_btn)

        separator1 = QLabel("|")
        separator1.setObjectName("footerSeparator")
        footer_layout.addWidget(separator1)

        self.privacy_btn = QPushButton(_("footer.privacy"))
        self.privacy_btn.setObjectName("footerLink")
        self.privacy_btn.setFlat(True)
        self.privacy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.privacy_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://rcsoftware.com/privacy")))
        footer_layout.addWidget(self.privacy_btn)

        separator2 = QLabel("|")
        separator2.setObjectName("footerSeparator")
        footer_layout.addWidget(separator2)

        self.terms_btn = QPushButton(_("footer.terms"))
        self.terms_btn.setObjectName("footerLink")
        self.terms_btn.setFlat(True)
        self.terms_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.terms_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://rcsoftware.com/terms")))
        footer_layout.addWidget(self.terms_btn)

        footer_outer.addWidget(footer_inner)
        footer_outer.addStretch()

        parent_layout.addWidget(footer)

    def _create_tickers_tab(self) -> QWidget:
        """Create the tickers management tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(20)

        # Title
        title = QLabel(_("tickers.title"))
        title.setObjectName("sectionTitle")
        layout.addWidget(title)

        # Ticker table
        self.ticker_table = QTableWidget()
        self.ticker_table.setObjectName("tickerTable")
        self.ticker_table.setColumnCount(6)
        self.ticker_table.setHorizontalHeaderLabels([
            _("tickers.symbol"),
            _("tickers.name"),
            _("tickers.high_threshold"),
            _("tickers.low_threshold"),
            _("tickers.last_price"),
            _("tickers.enabled"),
        ])
        self.ticker_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.ticker_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.ticker_table.setAlternatingRowColors(True)
        self.ticker_table.setMinimumHeight(300)

        # Make columns stretch
        header = self.ticker_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)

        layout.addWidget(self.ticker_table)

        # Button row
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)

        self.add_button = QPushButton(_("tickers.add"))
        self.add_button.setObjectName("primaryButton")
        self.add_button.clicked.connect(self._on_add_ticker)
        button_layout.addWidget(self.add_button)

        self.edit_button = QPushButton(_("tickers.edit"))
        self.edit_button.setObjectName("secondaryButton")
        self.edit_button.clicked.connect(self._on_edit_ticker)
        button_layout.addWidget(self.edit_button)

        self.delete_button = QPushButton(_("tickers.delete"))
        self.delete_button.setObjectName("dangerButton")
        self.delete_button.clicked.connect(self._on_delete_ticker)
        button_layout.addWidget(self.delete_button)

        self.toggle_button = QPushButton(_("tickers.toggle"))
        self.toggle_button.setObjectName("secondaryButton")
        self.toggle_button.clicked.connect(self._on_toggle_ticker)
        button_layout.addWidget(self.toggle_button)

        button_layout.addStretch()
        layout.addLayout(button_layout)

        return widget

    def _create_help_tab(self) -> QWidget:
        """Create the help tab with instructions and tips."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(24)

        # Title
        title = QLabel(_("help.title"))
        title.setObjectName("sectionTitle")
        layout.addWidget(title)

        # Getting Started section
        getting_started = QLabel(_("help.getting_started"))
        getting_started.setObjectName("helpSectionTitle")
        layout.addWidget(getting_started)

        getting_started_content = QLabel(_("help.getting_started_content"))
        getting_started_content.setWordWrap(True)
        getting_started_content.setObjectName("helpContent")
        layout.addWidget(getting_started_content)

        # Settings Tips section
        settings_tips = QLabel(_("help.settings_tips"))
        settings_tips.setObjectName("helpSectionTitle")
        layout.addWidget(settings_tips)

        settings_tips_content = QLabel(_("help.settings_tips_content"))
        settings_tips_content.setWordWrap(True)
        settings_tips_content.setObjectName("helpContent")
        layout.addWidget(settings_tips_content)

        # Managing Tickers section
        tickers_help = QLabel(_("help.tickers_title"))
        tickers_help.setObjectName("helpSectionTitle")
        layout.addWidget(tickers_help)

        tickers_content = QLabel(_("help.tickers_content"))
        tickers_content.setWordWrap(True)
        tickers_content.setObjectName("helpContent")
        layout.addWidget(tickers_content)

        # Alerts section
        alerts_help = QLabel(_("help.alerts_title"))
        alerts_help.setObjectName("helpSectionTitle")
        layout.addWidget(alerts_help)

        alerts_content = QLabel(_("help.alerts_content"))
        alerts_content.setWordWrap(True)
        alerts_content.setObjectName("helpContent")
        layout.addWidget(alerts_content)

        layout.addStretch()
        return widget

    def _apply_theme(self, theme: str) -> None:
        """Apply the specified theme."""
        self._current_theme = theme
        style_path = Path(__file__).parent / "styles" / "theme.qss"
        if style_path.exists():
            with open(style_path, encoding="utf-8") as f:
                base_style = f.read()

            # Apply theme-specific variables
            if theme == "light":
                themed_style = base_style.replace("/* THEME_MODE: dark */", "/* THEME_MODE: light */")
                # Light theme colors
                themed_style = self._get_light_theme()
            else:
                themed_style = self._get_dark_theme()

            self.setStyleSheet(themed_style)

    def _get_dark_theme(self) -> str:
        """Get dark theme stylesheet using CushLabs brand colors."""
        return """
/* AI StockAlert - Dark Theme (CushLabs Brand) */
/* Primary: #FF6A3D (Cush Orange) */
/* Grays: 900=#0A0A0A, 800=#141414, 700=#1A1A1A, 600=#2A2A2A, 400=#666666, 300=#888888, 200=#AAAAAA */

* {
    font-family: "Source Serif 4", "Georgia", serif;
}

QMainWindow, QWidget {
    background-color: #0A0A0A;
    color: #AAAAAA;
}

/* Headings use Space Grotesk */
#headerLogo, #sectionTitle, QGroupBox::title, #mainTabs QTabBar::tab {
    font-family: "Space Grotesk", "Segoe UI", sans-serif;
}

/* Header */
#header {
    background-color: #000000;
    border-bottom: 1px solid #2A2A2A;
}

#headerLogo {
    font-size: 24px;
    font-weight: bold;
    color: #FF6A3D;
    background-color: transparent;
}

#headerLabel {
    font-size: 14px;
    color: #666666;
    background-color: transparent;
}

#headerInner, #footerInner {
    background-color: transparent;
}

/* Language Switcher - EN | ES style */
#langButton {
    background-color: transparent;
    border: none;
    color: #666666;
    font-size: 14px;
    font-weight: normal;
    padding: 8px 12px;
    min-width: 40px;
}

#langButton:hover {
    color: #AAAAAA;
    background-color: transparent;
}

#langButton:checked {
    color: #FFFFFF;
    font-weight: bold;
    background-color: transparent;
}

#langSeparator {
    color: #666666;
    font-size: 14px;
    padding: 0 4px;
    background-color: transparent;
}

/* Theme Button - Sun/Moon */
#themeButton {
    background-color: #1A1A1A;
    border: 1px solid #2A2A2A;
    border-radius: 20px;
    font-size: 20px;
    color: #AAAAAA;
}

#themeButton:hover {
    background-color: #2A2A2A;
    border-color: #FF6A3D;
}

/* Footer */
#footer {
    background-color: #000000;
    border-top: 1px solid #2A2A2A;
}

#footerText {
    font-size: 13px;
    color: #666666;
}

#footerLink {
    font-size: 13px;
    color: #FF6A3D;
    background: transparent;
    border: none;
    padding: 5px 10px;
}

#footerLink:hover {
    color: #FF8A5D;
    text-decoration: underline;
}

#footerSeparator {
    color: #2A2A2A;
    margin: 0 5px;
}

/* Content Area */
#contentScrollArea {
    background-color: #0A0A0A;
    border: none;
}

#contentContainer {
    background-color: #0A0A0A;
}

#innerContent {
    background-color: transparent;
}

/* Tabs */
#mainTabs {
    font-size: 16px;
}

#mainTabs::pane {
    border: 1px solid #2A2A2A;
    background-color: #141414;
    border-radius: 8px;
    padding: 20px;
}

#mainTabs QTabBar::tab {
    background-color: transparent;
    color: #666666;
    padding: 12px 24px;
    margin-right: 5px;
    border-bottom: 3px solid transparent;
    font-size: 16px;
    font-weight: 500;
}

#mainTabs QTabBar::tab:selected {
    color: #FFFFFF;
    border-bottom: 3px solid #FF6A3D;
}

#mainTabs QTabBar::tab:hover:!selected {
    color: #AAAAAA;
}

/* Section Titles */
#sectionTitle {
    font-size: 22px;
    font-weight: bold;
    color: #FFFFFF;
    margin-bottom: 10px;
}

#helpSectionTitle {
    font-size: 18px;
    font-weight: bold;
    color: #FF6A3D;
    margin-top: 16px;
    margin-bottom: 8px;
}

#helpContent {
    font-size: 14px;
    color: #AAAAAA;
    line-height: 1.6;
    padding-left: 8px;
}

/* Tables */
#tickerTable {
    background-color: #141414;
    alternate-background-color: #1A1A1A;
    gridline-color: #2A2A2A;
    border: 1px solid #2A2A2A;
    border-radius: 8px;
    font-size: 15px;
}

#tickerTable::item {
    padding: 12px 8px;
    color: #AAAAAA;
}

#tickerTable::item:selected {
    background-color: #2A2A2A;
    color: #FFFFFF;
}

#tickerTable QHeaderView::section {
    background-color: #1A1A1A;
    color: #666666;
    padding: 14px 8px;
    border: none;
    border-bottom: 1px solid #2A2A2A;
    font-weight: bold;
    font-size: 14px;
    text-transform: uppercase;
}

/* Buttons */
#primaryButton, QPushButton[objectName="primaryButton"] {
    background-color: #FF6A3D;
    color: #000000;
    border: none;
    border-radius: 8px;
    padding: 12px 24px;
    font-size: 15px;
    font-weight: 600;
    min-width: 120px;
}

#primaryButton:hover, QPushButton[objectName="primaryButton"]:hover {
    background-color: #FF8A5D;
}

#primaryButton:pressed, QPushButton[objectName="primaryButton"]:pressed {
    background-color: #E55A2D;
}

#secondaryButton {
    background-color: transparent;
    color: #AAAAAA;
    border: 1px solid #FF6A3D;
    border-radius: 8px;
    padding: 12px 24px;
    font-size: 15px;
    font-weight: 600;
    min-width: 120px;
}

#secondaryButton:hover {
    background-color: rgba(255, 106, 61, 0.1);
    border-color: #FF8A5D;
    color: #FFFFFF;
}

#dangerButton {
    background-color: transparent;
    color: #f4212e;
    border: 1px solid #661111;
    border-radius: 8px;
    padding: 12px 24px;
    font-size: 15px;
    font-weight: 600;
    min-width: 120px;
}

#dangerButton:hover {
    background-color: rgba(244, 33, 46, 0.1);
    border-color: #f4212e;
}

/* Help Labels */
#helpLabel {
    color: #666666;
    font-size: 12px;
    margin-bottom: 12px;
}

/* Form Elements */
QLabel {
    font-size: 15px;
    color: #AAAAAA;
}

QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
    background-color: #1A1A1A;
    border: 1px solid #2A2A2A;
    border-radius: 6px;
    padding: 12px 14px;
    font-size: 15px;
    color: #AAAAAA;
    margin-bottom: 8px;
}

QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {
    border-color: #FF6A3D;
}

QComboBox QAbstractItemView {
    background-color: #1A1A1A;
    border: 1px solid #2A2A2A;
    selection-background-color: #FF6A3D;
    selection-color: #000000;
}

QCheckBox {
    font-size: 15px;
    spacing: 10px;
    margin: 12px 0;
}

QCheckBox::indicator {
    width: 22px;
    height: 22px;
    border-radius: 4px;
    border: 2px solid #2A2A2A;
    background-color: #1A1A1A;
}

QCheckBox::indicator:checked {
    background-color: #FF6A3D;
    border-color: #FF6A3D;
}

/* Radio Buttons */
QRadioButton {
    font-size: 14px;
    spacing: 6px;
    color: #AAAAAA;
}

QRadioButton::indicator {
    width: 18px;
    height: 18px;
    border-radius: 9px;
    border: 2px solid #2A2A2A;
    background-color: #1A1A1A;
}

QRadioButton::indicator:hover {
    border-color: #FF6A3D;
}

QRadioButton::indicator:checked {
    background-color: #FF6A3D;
    border-color: #FF6A3D;
}

#unitRadio {
    padding: 6px 12px;
    background-color: #1A1A1A;
    border: 1px solid #2A2A2A;
    border-radius: 4px;
}

#unitRadio:checked {
    background-color: #2A2A2A;
    border-color: #FF6A3D;
    color: #FFFFFF;
}

/* Form Rows */
QFormLayout {
    vertical-spacing: 20px;
}

/* Group Box */
QGroupBox {
    font-size: 18px;
    font-weight: bold;
    border: 1px solid #2A2A2A;
    border-radius: 8px;
    margin-top: 24px;
    padding: 24px 20px;
    background-color: #141414;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 20px;
    padding: 0 10px;
    color: #FFFFFF;
}

/* Status Bar */
#statusBar {
    background-color: #000000;
    border-top: 1px solid #2A2A2A;
    font-size: 13px;
    color: #666666;
    padding: 5px 20px;
}

/* Scrollbars */
QScrollBar:vertical {
    background-color: #141414;
    width: 12px;
    border-radius: 6px;
}

QScrollBar::handle:vertical {
    background-color: #2A2A2A;
    border-radius: 6px;
    min-height: 40px;
}

QScrollBar::handle:vertical:hover {
    background-color: #666666;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

/* Message Box */
QMessageBox {
    background-color: #141414;
}

QMessageBox QLabel {
    color: #AAAAAA;
    font-size: 15px;
}

/* Dialog */
QDialog {
    background-color: #141414;
}
"""

    def _get_light_theme(self) -> str:
        """Get light theme stylesheet using CushLabs brand colors."""
        return """
/* AI StockAlert - Light Theme (CushLabs Brand) */
/* Primary: #FF6A3D (Cush Orange) */
/* Light backgrounds with dark text */

* {
    font-family: "Source Serif 4", "Georgia", serif;
}

QMainWindow, QWidget {
    background-color: #FFFFFF;
    color: #000000;
}

/* Headings use Space Grotesk */
#headerLogo, #sectionTitle, QGroupBox::title, #mainTabs QTabBar::tab {
    font-family: "Space Grotesk", "Segoe UI", sans-serif;
}

/* Header */
#header {
    background-color: #FAFAFA;
    border-bottom: 1px solid #E5E5E5;
}

#headerLogo {
    font-size: 24px;
    font-weight: bold;
    color: #FF6A3D;
    background-color: transparent;
}

#headerLabel {
    font-size: 14px;
    color: #666666;
    background-color: transparent;
}

#headerInner, #footerInner {
    background-color: transparent;
}

/* Language Switcher - EN | ES style */
#langButton {
    background-color: transparent;
    border: none;
    color: #666666;
    font-size: 14px;
    font-weight: normal;
    padding: 8px 12px;
    min-width: 40px;
}

#langButton:hover {
    color: #000000;
    background-color: transparent;
}

#langButton:checked {
    color: #000000;
    font-weight: bold;
    background-color: transparent;
}

#langSeparator {
    color: #999999;
    font-size: 14px;
    padding: 0 4px;
    background-color: transparent;
}

/* Theme Button - Sun/Moon */
#themeButton {
    background-color: #FFFFFF;
    border: 1px solid #E5E5E5;
    border-radius: 20px;
    font-size: 20px;
    color: #000000;
}

#themeButton:hover {
    background-color: #F5F5F5;
    border-color: #FF6A3D;
}

/* Footer */
#footer {
    background-color: #FAFAFA;
    border-top: 1px solid #E5E5E5;
}

#footerText {
    font-size: 13px;
    color: #666666;
}

#footerLink {
    font-size: 13px;
    color: #FF6A3D;
    background: transparent;
    border: none;
    padding: 5px 10px;
}

#footerLink:hover {
    color: #E55A2D;
    text-decoration: underline;
}

#footerSeparator {
    color: #CCCCCC;
    margin: 0 5px;
}

/* Content Area */
#contentScrollArea {
    background-color: #FFFFFF;
    border: none;
}

#contentContainer {
    background-color: #FFFFFF;
}

#innerContent {
    background-color: transparent;
}

/* Tabs */
#mainTabs {
    font-size: 16px;
}

#mainTabs::pane {
    border: 1px solid #E5E5E5;
    background-color: #FFFFFF;
    border-radius: 8px;
    padding: 20px;
}

#mainTabs QTabBar::tab {
    background-color: transparent;
    color: #666666;
    padding: 12px 24px;
    margin-right: 5px;
    border-bottom: 3px solid transparent;
    font-size: 16px;
    font-weight: 500;
}

#mainTabs QTabBar::tab:selected {
    color: #000000;
    border-bottom: 3px solid #FF6A3D;
}

#mainTabs QTabBar::tab:hover:!selected {
    color: #000000;
}

/* Section Titles */
#sectionTitle {
    font-size: 22px;
    font-weight: bold;
    color: #000000;
    margin-bottom: 10px;
}

#helpSectionTitle {
    font-size: 18px;
    font-weight: bold;
    color: #FF6A3D;
    margin-top: 16px;
    margin-bottom: 8px;
}

#helpContent {
    font-size: 14px;
    color: #333333;
    line-height: 1.6;
    padding-left: 8px;
}

/* Tables */
#tickerTable {
    background-color: #FFFFFF;
    alternate-background-color: #FAFAFA;
    gridline-color: #E5E5E5;
    border: 1px solid #E5E5E5;
    border-radius: 8px;
    font-size: 15px;
}

#tickerTable::item {
    padding: 12px 8px;
    color: #000000;
}

#tickerTable::item:selected {
    background-color: #FFF0EB;
    color: #000000;
}

#tickerTable QHeaderView::section {
    background-color: #FAFAFA;
    color: #666666;
    padding: 14px 8px;
    border: none;
    border-bottom: 1px solid #E5E5E5;
    font-weight: bold;
    font-size: 14px;
    text-transform: uppercase;
}

/* Buttons */
#primaryButton, QPushButton[objectName="primaryButton"] {
    background-color: #FF6A3D;
    color: #FFFFFF;
    border: none;
    border-radius: 8px;
    padding: 12px 24px;
    font-size: 15px;
    font-weight: 600;
    min-width: 120px;
}

#primaryButton:hover, QPushButton[objectName="primaryButton"]:hover {
    background-color: #E55A2D;
}

#primaryButton:pressed, QPushButton[objectName="primaryButton"]:pressed {
    background-color: #CC4A1D;
}

#secondaryButton {
    background-color: transparent;
    color: #000000;
    border: 1px solid #FF6A3D;
    border-radius: 8px;
    padding: 12px 24px;
    font-size: 15px;
    font-weight: 600;
    min-width: 120px;
}

#secondaryButton:hover {
    background-color: #FFF0EB;
    border-color: #E55A2D;
}

#dangerButton {
    background-color: transparent;
    color: #DC2626;
    border: 1px solid #FCA5A5;
    border-radius: 8px;
    padding: 12px 24px;
    font-size: 15px;
    font-weight: 600;
    min-width: 120px;
}

#dangerButton:hover {
    background-color: #FEF2F2;
    border-color: #DC2626;
}

/* Help Labels */
#helpLabel {
    color: #666666;
    font-size: 12px;
    margin-bottom: 12px;
}

/* Form Elements */
QLabel {
    font-size: 15px;
    color: #000000;
}

QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
    background-color: #FFFFFF;
    border: 1px solid #E5E5E5;
    border-radius: 6px;
    padding: 12px 14px;
    font-size: 15px;
    color: #000000;
    margin-bottom: 8px;
}

QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {
    border-color: #FF6A3D;
}

QComboBox QAbstractItemView {
    background-color: #FFFFFF;
    border: 1px solid #E5E5E5;
    selection-background-color: #FF6A3D;
    selection-color: #FFFFFF;
}

QCheckBox {
    font-size: 15px;
    spacing: 10px;
    margin: 12px 0;
}

QCheckBox::indicator {
    width: 22px;
    height: 22px;
    border-radius: 4px;
    border: 2px solid #E5E5E5;
    background-color: #FFFFFF;
}

QCheckBox::indicator:checked {
    background-color: #FF6A3D;
    border-color: #FF6A3D;
}

/* Radio Buttons */
QRadioButton {
    font-size: 14px;
    spacing: 6px;
    color: #000000;
}

QRadioButton::indicator {
    width: 18px;
    height: 18px;
    border-radius: 9px;
    border: 2px solid #E5E5E5;
    background-color: #FFFFFF;
}

QRadioButton::indicator:hover {
    border-color: #FF6A3D;
}

QRadioButton::indicator:checked {
    background-color: #FF6A3D;
    border-color: #FF6A3D;
}

#unitRadio {
    padding: 6px 12px;
    background-color: #FFFFFF;
    border: 1px solid #E5E5E5;
    border-radius: 4px;
}

#unitRadio:checked {
    background-color: #FFF0EB;
    border-color: #FF6A3D;
    color: #000000;
}

/* Form Rows */
QFormLayout {
    vertical-spacing: 20px;
}

/* Group Box */
QGroupBox {
    font-size: 18px;
    font-weight: bold;
    border: 1px solid #E5E5E5;
    border-radius: 8px;
    margin-top: 24px;
    padding: 24px 20px;
    background-color: #FFFFFF;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 20px;
    padding: 0 10px;
    color: #000000;
}

/* Status Bar */
#statusBar {
    background-color: #FAFAFA;
    border-top: 1px solid #E5E5E5;
    font-size: 13px;
    color: #666666;
    padding: 5px 20px;
}

/* Scrollbars */
QScrollBar:vertical {
    background-color: #FAFAFA;
    width: 12px;
    border-radius: 6px;
}

QScrollBar::handle:vertical {
    background-color: #CCCCCC;
    border-radius: 6px;
    min-height: 40px;
}

QScrollBar::handle:vertical:hover {
    background-color: #888888;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

/* Message Box */
QMessageBox {
    background-color: #FFFFFF;
}

QMessageBox QLabel {
    color: #000000;
    font-size: 15px;
}

/* Dialog */
QDialog {
    background-color: #FFFFFF;
}
"""

    def _update_lang_buttons(self, current_lang: str) -> None:
        """Update language button styles to show current selection."""
        self.lang_en_btn.setChecked(current_lang == "en")
        self.lang_es_btn.setChecked(current_lang == "es")

    def _set_language(self, language: str) -> None:
        """Set the application language."""
        self.translator.set_language(language)
        self.config_manager.set("settings.language", language)
        self._update_lang_buttons(language)
        self.retranslate_ui()
        if self.on_settings_changed:
            self.on_settings_changed()

    def _toggle_theme(self) -> None:
        """Toggle between dark and light themes."""
        new_theme = "light" if self._current_theme == "dark" else "dark"
        self._apply_theme(new_theme)
        self._update_theme_icon()
        self.config_manager.set("settings.theme", new_theme)

    def _update_theme_icon(self) -> None:
        """Update the theme button icon based on current theme."""
        if self._current_theme == "dark":
            # Sun icon (switch to light)
            self.theme_btn.setText("☀")
            self.theme_btn.setToolTip(_("theme.light"))
        else:
            # Moon icon (switch to dark)
            self.theme_btn.setText("🌙")
            self.theme_btn.setToolTip(_("theme.dark"))

    def _load_data(self) -> None:
        """Load data into the UI."""
        self._refresh_ticker_table()

    def _refresh_ticker_table(self) -> None:
        """Refresh the ticker table with current data."""
        tickers = self.config_manager.get_tickers()
        self.ticker_table.setRowCount(len(tickers))

        for row, ticker in enumerate(tickers):
            # Symbol
            symbol_item = QTableWidgetItem(ticker.get("symbol", ""))
            symbol_item.setFlags(symbol_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.ticker_table.setItem(row, 0, symbol_item)

            # Name
            name_item = QTableWidgetItem(ticker.get("name", ""))
            name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.ticker_table.setItem(row, 1, name_item)

            # High threshold
            high = ticker.get("high_threshold", 0)
            high_item = QTableWidgetItem(f"${high:.2f}")
            high_item.setFlags(high_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            high_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.ticker_table.setItem(row, 2, high_item)

            # Low threshold
            low = ticker.get("low_threshold", 0)
            low_item = QTableWidgetItem(f"${low:.2f}")
            low_item.setFlags(low_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            low_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.ticker_table.setItem(row, 3, low_item)

            # Last price (placeholder)
            price_item = QTableWidgetItem("--")
            price_item.setFlags(price_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            price_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.ticker_table.setItem(row, 4, price_item)

            # Enabled
            enabled = ticker.get("enabled", True)
            enabled_item = QTableWidgetItem("✓" if enabled else "✗")
            enabled_item.setFlags(enabled_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            enabled_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.ticker_table.setItem(row, 5, enabled_item)

    def _get_selected_row(self) -> int:
        """Get the currently selected row index, or -1 if none."""
        selection = self.ticker_table.selectedItems()
        if selection:
            return selection[0].row()
        return -1

    def _get_selected_symbol(self) -> str | None:
        """Get the symbol of the selected row."""
        row = self._get_selected_row()
        if row >= 0:
            item = self.ticker_table.item(row, 0)
            if item:
                return item.text()
        return None

    def _on_add_ticker(self) -> None:
        """Handle add ticker button."""
        dialog = TickerDialog(
            config_manager=self.config_manager,
            translator=self.translator,
            parent=self,
        )
        if dialog.exec():
            self._refresh_ticker_table()
            if self.on_settings_changed:
                self.on_settings_changed()

    def _on_edit_ticker(self) -> None:
        """Handle edit ticker button."""
        symbol = self._get_selected_symbol()
        if not symbol:
            QMessageBox.warning(
                self,
                _("errors.title"),
                _("tickers.no_selection"),
            )
            return

        # Find ticker data
        tickers = self.config_manager.get_tickers()
        ticker_data = next((t for t in tickers if t["symbol"] == symbol), None)
        if not ticker_data:
            return

        dialog = TickerDialog(
            config_manager=self.config_manager,
            translator=self.translator,
            ticker=ticker_data,
            parent=self,
        )
        if dialog.exec():
            self._refresh_ticker_table()
            if self.on_settings_changed:
                self.on_settings_changed()

    def _on_delete_ticker(self) -> None:
        """Handle delete ticker button."""
        symbol = self._get_selected_symbol()
        if not symbol:
            QMessageBox.warning(
                self,
                _("errors.title"),
                _("tickers.no_selection"),
            )
            return

        result = QMessageBox.question(
            self,
            _("dialogs.confirm"),
            _("tickers.delete_confirm", symbol=symbol),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if result == QMessageBox.StandardButton.Yes:
            self.config_manager.delete_ticker(symbol)
            self._refresh_ticker_table()
            self.status_bar.showMessage(_("tickers.delete_success"))
            if self.on_settings_changed:
                self.on_settings_changed()

    def _on_toggle_ticker(self) -> None:
        """Handle toggle ticker button."""
        symbol = self._get_selected_symbol()
        if not symbol:
            QMessageBox.warning(
                self,
                _("errors.title"),
                _("tickers.no_selection"),
            )
            return

        self.config_manager.toggle_ticker(symbol)
        self._refresh_ticker_table()
        if self.on_settings_changed:
            self.on_settings_changed()

    def _on_settings_saved(self) -> None:
        """Handle settings saved event."""
        self.status_bar.showMessage(_("settings.saved"))
        if self.on_settings_changed:
            self.on_settings_changed()

    def retranslate_ui(self) -> None:
        """Update UI text after language change."""
        self.setWindowTitle(_("app.name"))
        self.tabs.setTabText(0, _("tabs.profile"))
        self.tabs.setTabText(1, _("tabs.settings"))
        self.tabs.setTabText(2, _("tabs.tickers"))
        self.tabs.setTabText(3, _("tabs.help"))
        self.profile_widget.retranslate_ui()
        self.settings_widget.retranslate_ui()

        # Recreate help tab to update content
        self.tabs.removeTab(3)
        self.help_widget = self._create_help_tab()
        self.tabs.insertTab(3, self.help_widget, _("tabs.help"))

        # Update theme button tooltip
        self._update_theme_icon()

        # Update footer
        self.copyright_label.setText(_("about.copyright"))
        self.website_btn.setText(_("footer.website"))
        self.privacy_btn.setText(_("footer.privacy"))
        self.terms_btn.setText(_("footer.terms"))

        # Update ticker table headers
        self.ticker_table.setHorizontalHeaderLabels([
            _("tickers.symbol"),
            _("tickers.name"),
            _("tickers.high_threshold"),
            _("tickers.low_threshold"),
            _("tickers.last_price"),
            _("tickers.enabled"),
        ])

        # Update buttons
        self.add_button.setText(_("tickers.add"))
        self.edit_button.setText(_("tickers.edit"))
        self.delete_button.setText(_("tickers.delete"))
        self.toggle_button.setText(_("tickers.toggle"))

    def update_ticker_price(self, symbol: str, price: float | None) -> None:
        """Update the displayed price for a ticker.

        Args:
            symbol: Ticker symbol
            price: Current price, or None if unavailable
        """
        for row in range(self.ticker_table.rowCount()):
            item = self.ticker_table.item(row, 0)
            if item and item.text() == symbol:
                price_item = self.ticker_table.item(row, 4)
                if price_item:
                    if price is not None:
                        price_item.setText(f"${price:.2f}")
                    else:
                        price_item.setText("--")
                break

    def closeEvent(self, event: QCloseEvent) -> None:
        """Handle window close - minimize to tray instead of quitting."""
        event.ignore()
        self.hide()
