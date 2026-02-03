"""
Main application window for StockAlert.

PyQt6-based responsive GUI with header, footer, tabs, and theme support.
"""

from __future__ import annotations

import logging
import sys
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING

from PyQt6.QtCore import QMetaObject, QPoint, Qt, QTimer, QUrl, Q_ARG, pyqtSlot
from PyQt6.QtGui import QCloseEvent, QDesktopServices, QIcon, QPixmap
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
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
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from stockalert.core.paths import get_bundled_assets_dir
from stockalert.i18n.translator import _
from stockalert.ui.dialogs.profile_dialog import ProfileWidget
from stockalert.ui.dialogs.settings_dialog import SettingsWidget
from stockalert.ui.dialogs.ticker_dialog import TickerDialog
from stockalert.ui.widgets.news_widget import NewsWidget

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
        self._logo_cache: dict[str, QPixmap] = {}
        self._logo_cache_order: list[str] = []  # Track insertion order for LRU eviction
        self._logo_cache_max_size = 50  # Max logos to cache (prevents memory leak)
        self._network_manager = QNetworkAccessManager(self)
        self._network_manager.finished.connect(self._on_logo_loaded)
        self._pending_logos: dict[str, tuple[int, str]] = {}  # url -> (row, symbol)

        self._setup_ui()
        self._load_data()
        self._apply_theme(self._current_theme)
        self._restore_window_geometry()
        # Ensure all UI text matches current language (widgets may have been
        # created with stale translations if translator was set after import)
        self.retranslate_ui()

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        self.setWindowTitle(_("app.name"))

        # Always use programmatic orange branded icon for consistency
        self.setWindowIcon(self._create_app_icon())
        logger.info("Set window icon (programmatic orange)")

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

        # News tab
        self.news_widget = NewsWidget(
            config_manager=self.config_manager,
            translator=self.translator,
        )
        self.tabs.addTab(self.news_widget, _("tabs.news"))

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
        self.website_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://ai-stock-alert-website.netlify.app/")))
        footer_layout.addWidget(self.website_btn)

        separator1 = QLabel("|")
        separator1.setObjectName("footerSeparator")
        footer_layout.addWidget(separator1)

        self.privacy_btn = QPushButton(_("footer.privacy"))
        self.privacy_btn.setObjectName("footerLink")
        self.privacy_btn.setFlat(True)
        self.privacy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.privacy_btn.clicked.connect(self._open_privacy_link)
        footer_layout.addWidget(self.privacy_btn)

        separator2 = QLabel("|")
        separator2.setObjectName("footerSeparator")
        footer_layout.addWidget(separator2)

        self.terms_btn = QPushButton(_("footer.terms"))
        self.terms_btn.setObjectName("footerLink")
        self.terms_btn.setFlat(True)
        self.terms_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.terms_btn.clicked.connect(self._open_terms_link)
        footer_layout.addWidget(self.terms_btn)

        footer_outer.addWidget(footer_inner)
        footer_outer.addStretch()

        parent_layout.addWidget(footer)

    def _create_tickers_tab(self) -> QWidget:
        """Create the tickers management tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(20)

        # Title and button row
        header_layout = QHBoxLayout()

        self.tickers_title = QLabel(_("tickers.title"))
        self.tickers_title.setObjectName("sectionTitle")
        header_layout.addWidget(self.tickers_title)

        # Ticker count indicator (free tier limit)
        self.ticker_count_label = QLabel()
        self.ticker_count_label.setObjectName("tickerCountLabel")
        self.ticker_count_label.setStyleSheet("color: #888888; font-size: 12px; margin-left: 12px;")
        header_layout.addWidget(self.ticker_count_label)

        header_layout.addStretch()

        # Buttons at top right - all action buttons use orange styling
        self.add_button = QPushButton(_("tickers.add"))
        self.add_button.setObjectName("actionButton")
        self.add_button.clicked.connect(self._on_add_ticker)
        header_layout.addWidget(self.add_button)

        self.edit_button = QPushButton(_("tickers.edit"))
        self.edit_button.setObjectName("actionButton")
        self.edit_button.clicked.connect(self._on_edit_ticker)
        header_layout.addWidget(self.edit_button)

        self.delete_button = QPushButton(_("tickers.delete"))
        self.delete_button.setObjectName("dangerButton")
        self.delete_button.clicked.connect(self._on_delete_ticker)
        header_layout.addWidget(self.delete_button)

        self.toggle_button = QPushButton(_("tickers.toggle"))
        self.toggle_button.setObjectName("actionButton")
        self.toggle_button.clicked.connect(self._on_toggle_ticker)
        header_layout.addWidget(self.toggle_button)

        self.refresh_profiles_button = QPushButton(_("tickers.refresh_profiles"))
        self.refresh_profiles_button.setObjectName("actionButton")
        self.refresh_profiles_button.clicked.connect(self._on_refresh_profiles)
        header_layout.addWidget(self.refresh_profiles_button)

        layout.addLayout(header_layout)

        # Ticker table with checkbox column
        self.ticker_table = QTableWidget()
        self.ticker_table.setObjectName("tickerTable")
        self.ticker_table.setColumnCount(10)

        self.ticker_table.setHorizontalHeaderLabels([
            "",  # Checkbox column
            "",  # Logo column
            _("tickers.symbol"),
            _("tickers.name"),
            _("tickers.industry"),
            _("tickers.market_cap"),
            _("tickers.high_threshold"),
            _("tickers.low_threshold"),
            _("tickers.last_price"),
            _("tickers.enabled"),
        ])

        # Set up header
        header = self.ticker_table.horizontalHeader()
        if header is not None:
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)  # Checkbox
            self.ticker_table.setColumnWidth(0, 50)
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)  # Logo
            self.ticker_table.setColumnWidth(1, 45)
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Symbol
            header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)  # Name
            header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Industry
            header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)  # Market Cap
            header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)  # High
            header.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)  # Low
            header.setSectionResizeMode(8, QHeaderView.ResizeMode.ResizeToContents)  # Price
            header.setSectionResizeMode(9, QHeaderView.ResizeMode.ResizeToContents)  # Enabled

            # Set the first column header to have a clickable select all indicator
            header_item = self.ticker_table.horizontalHeaderItem(0)
            if header_item is not None:
                header_item.setText("☐")

            # Create a clickable header for select all
            header.sectionClicked.connect(self._on_header_clicked)

        # Disable row selection - only use checkboxes
        self.ticker_table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.ticker_table.setAlternatingRowColors(True)
        self.ticker_table.setMinimumHeight(300)
        vertical_header = self.ticker_table.verticalHeader()
        if vertical_header is not None:
            vertical_header.setDefaultSectionSize(40)
            vertical_header.setVisible(False)

        layout.addWidget(self.ticker_table)

        # Initial button state (disabled until selection)
        self._update_action_buttons()

        return widget

    def _on_header_clicked(self, logical_index: int) -> None:
        """Handle header click - toggle select all for first column."""
        if logical_index == 0:
            # Toggle all checkboxes
            all_checked = True
            if self.ticker_table.rowCount() > 0:
                for row in range(self.ticker_table.rowCount()):
                    checkbox_widget = self.ticker_table.cellWidget(row, 0)
                    if checkbox_widget:
                        checkbox = checkbox_widget.findChild(QCheckBox)
                        if checkbox and not checkbox.isChecked():
                            all_checked = False
                            break
            else:
                all_checked = False

            new_state = not all_checked

            for row in range(self.ticker_table.rowCount()):
                checkbox_widget = self.ticker_table.cellWidget(row, 0)
                if checkbox_widget:
                    checkbox = checkbox_widget.findChild(QCheckBox)
                    if checkbox:
                        checkbox.setChecked(new_state)

            # Update header text to show state
            self._update_select_all_header()

    def _update_select_all_header(self) -> None:
        """Update the select all header text based on selection state."""
        header_item = self.ticker_table.horizontalHeaderItem(0)
        if self.ticker_table.rowCount() == 0:
            if header_item is not None:
                header_item.setText("☐")
            return

        all_checked = True
        for row in range(self.ticker_table.rowCount()):
            checkbox_widget = self.ticker_table.cellWidget(row, 0)
            if checkbox_widget:
                checkbox = checkbox_widget.findChild(QCheckBox)
                if checkbox and not checkbox.isChecked():
                    all_checked = False
                    break

        # Use filled or empty box character
        if header_item is not None:
            header_item.setText("☑" if all_checked else "☐")

    def _on_select_all_changed(self, state: int) -> None:
        """Handle select all checkbox state change."""
        is_checked = state == Qt.CheckState.Checked.value
        for row in range(self.ticker_table.rowCount()):
            checkbox_widget = self.ticker_table.cellWidget(row, 0)
            if checkbox_widget:
                checkbox = checkbox_widget.findChild(QCheckBox)
                if checkbox:
                    checkbox.setChecked(is_checked)

    def _get_selected_symbols(self) -> list[str]:
        """Get all selected ticker symbols (via checkboxes)."""
        selected = []
        for row in range(self.ticker_table.rowCount()):
            checkbox_widget = self.ticker_table.cellWidget(row, 0)
            if checkbox_widget:
                checkbox = checkbox_widget.findChild(QCheckBox)
                if checkbox and checkbox.isChecked():
                    item = self.ticker_table.item(row, 2)  # Column 2 is symbol
                    if item:
                        selected.append(item.text())
        return selected

    def _update_action_buttons(self) -> None:
        """Update action button states based on checkbox selection."""
        selected = self._get_selected_symbols()
        count = len(selected)

        # Edit: only enabled when exactly 1 selected
        self.edit_button.setEnabled(count == 1)

        # Delete and Toggle: enabled when 1 or more selected
        self.delete_button.setEnabled(count >= 1)
        self.toggle_button.setEnabled(count >= 1)

    def _on_checkbox_changed(self) -> None:
        """Handle individual checkbox state change."""
        self._update_action_buttons()
        self._update_select_all_header()

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

        # Background Service section
        service_help = QLabel(_("help.service_title"))
        service_help.setObjectName("helpSectionTitle")
        layout.addWidget(service_help)

        service_content = QLabel(_("help.service_content"))
        service_content.setWordWrap(True)
        service_content.setObjectName("helpContent")
        layout.addWidget(service_content)

        layout.addStretch()
        return widget

    def _apply_theme(self, theme: str) -> None:
        """Apply the specified theme."""
        self._current_theme = theme
        # Handle frozen exe vs development
        if getattr(sys, "frozen", False):
            if hasattr(sys, "_MEIPASS"):
                # PyInstaller bundles data in _MEIPASS
                style_path = Path(sys._MEIPASS) / "stockalert" / "ui" / "styles" / "theme.qss"
            else:
                # cx_Freeze puts data in lib/ subdirectory
                style_path = Path(sys.executable).parent / "lib" / "stockalert" / "ui" / "styles" / "theme.qss"
        else:
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
        """Get dark theme stylesheet using CushLabs brand colors and Segoe UI Variable."""
        return """
/* AI StockAlert - Dark Theme (CushLabs Brand) */
/* Primary: #FF6A3D (Cush Orange) */
/* Grays: 900=#0A0A0A, 800=#141414, 700=#1A1A1A, 600=#2A2A2A, 400=#666666, 300=#888888, 200=#AAAAAA */
/* Typography: Segoe UI Variable (Native Windows) */

* {
    font-family: "Segoe UI Variable Text", "Segoe UI", sans-serif;
    font-size: 14px;
}

QMainWindow, QWidget {
    background-color: #0A0A0A;
    color: #AAAAAA;
}

/* Display/Hero text uses Segoe UI Variable Display with Bold weight */
#headerLogo {
    font-family: "Segoe UI Variable Display", "Segoe UI", sans-serif;
    font-weight: 700;
}

/* Section Headers use Semibold weight */
#sectionTitle, QGroupBox::title, #mainTabs QTabBar::tab {
    font-family: "Segoe UI Variable Display", "Segoe UI", sans-serif;
    font-weight: 600;
}

/* Header */
#header {
    background-color: #000000;
    border-bottom: 1px solid #2A2A2A;
}

#headerLogo {
    font-size: 32px;
    font-weight: 700;
    color: #FF6A3D;
    background-color: transparent;
}

#headerLabel {
    font-size: 13px;
    color: #666666;
    background-color: transparent;
}

#headerInner {
    background-color: transparent;
}

/* Language Switcher - EN | ES style */
#langButton {
    background-color: transparent;
    border: none;
    color: #666666;
    font-size: 14px;
    font-weight: normal;
    padding: 4px 2px;
    min-width: 24px;
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
    padding: 0 2px;
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

#footerInner {
    background-color: transparent;
}

#footerText {
    font-size: 13px;
    color: #FF6A3D;
    background-color: transparent;
}

#footerLink {
    font-size: 13px;
    color: #FF6A3D;
    background-color: transparent;
    border: none;
    padding: 5px 10px;
}

#footerLink:hover {
    color: #FF8A5D;
    text-decoration: underline;
    background-color: transparent;
}

#footerSeparator {
    color: #FF6A3D;
    margin: 0 5px;
    background-color: transparent;
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
    font-size: 24px;
    font-weight: 600;
    color: #FFFFFF;
    margin-bottom: 10px;
}

#helpSectionTitle {
    font-size: 20px;
    font-weight: 600;
    color: #FF6A3D;
    margin-top: 16px;
    margin-bottom: 8px;
}

#helpContent {
    font-size: 14px;
    font-weight: 400;
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

#tickerTable QTableCornerButton::section {
    background-color: #1A1A1A;
    border: none;
    border-bottom: 1px solid #2A2A2A;
}

#tickerTable QWidget {
    background-color: transparent;
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

/* Action buttons (smaller orange buttons for service control, etc.) */
#actionButton, QPushButton[objectName="actionButton"] {
    background-color: #FF6A3D;
    color: #000000;
    border: none;
    border-radius: 6px;
    padding: 8px 16px;
    font-size: 13px;
    font-weight: 600;
    min-width: 100px;
}

#actionButton:hover, QPushButton[objectName="actionButton"]:hover {
    background-color: #FF8A5D;
}

#actionButton:pressed, QPushButton[objectName="actionButton"]:pressed {
    background-color: #E55A2D;
}

#actionButton:disabled, QPushButton[objectName="actionButton"]:disabled {
    background-color: #4A4A4A;
    color: #888888;
}

#dangerButton {
    background-color: #DC3545;
    color: #FFFFFF;
    border: none;
    border-radius: 6px;
    padding: 8px 16px;
    font-size: 13px;
    font-weight: 600;
    min-width: 100px;
}

#dangerButton:hover {
    background-color: #C82333;
}

#dangerButton:pressed {
    background-color: #A71D2A;
}

/* Captions/Labels - 12px muted grey */
#helpLabel {
    color: #666666;
    font-size: 13px;
    font-weight: 400;
    margin-bottom: 12px;
}

/* Form Elements - Body text 14-16px */
QLabel {
    font-size: 14px;
    font-weight: 400;
    color: #AAAAAA;
}

QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
    background-color: #1A1A1A;
    border: 1px solid #2A2A2A;
    border-radius: 6px;
    padding: 12px 14px;
    font-size: 14px;
    font-weight: 400;
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
    border-radius: 0px;
    border: 2px solid #2A2A2A;
    background-color: #1A1A1A;
}

QCheckBox::indicator:checked {
    background-color: #FF6A3D;
    border-color: #FF6A3D;
}

/* Ticker table checkboxes - square shape */
#tickerCheckbox {
    spacing: 0px;
    margin: 0px;
    padding: 0px;
}

#tickerCheckbox::indicator {
    width: 20px;
    height: 20px;
    min-width: 20px;
    min-height: 20px;
    max-width: 20px;
    max-height: 20px;
    border-radius: 0px;
    border: 2px solid #555555;
    background-color: #1A1A1A;
}

#tickerCheckbox::indicator:checked {
    background-color: #FF6A3D;
    border-color: #FF6A3D;
    image: none;
}

#tickerCheckbox::indicator:hover {
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

#modeRadio {
    font-weight: bold;
    font-size: 14px;
    color: #FFFFFF;
    min-height: 24px;
    spacing: 8px;
}

#modeRadio::indicator {
    width: 18px;
    height: 18px;
    min-width: 18px;
    min-height: 18px;
    border-radius: 9px;
    border: 2px solid #555555;
    background-color: #1A1A1A;
}

#modeRadio::indicator:hover {
    border-color: #FF6A3D;
}

#modeRadio::indicator:checked {
    background-color: #FF6A3D;
    border-color: #FF6A3D;
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

/* News Widget */
#newsCard {
    background-color: #1E1E1E;
    border: 1px solid #3A3A3A;
    border-radius: 12px;
}

#newsCard:hover {
    border-color: #FF6A3D;
    background-color: #282828;
}

#newsThumbnail {
    background-color: #2A2A2A;
    border: 1px solid #3A3A3A;
    border-radius: 8px;
    font-size: 28px;
}

/* Ensure news card content has no background */
#newsCard QLabel {
    background: transparent;
}

#newsCard QWidget {
    background: transparent;
}

#newsScrollArea {
    background: transparent;
    border: none;
}

#newsScrollArea QWidget {
    background: transparent;
}

#newsHeadline {
    font-weight: bold;
    font-size: 14px;
    color: #FFFFFF;
    background: transparent;
}

#newsSummary {
    color: #B0B0B0;
    font-size: 12px;
    background: transparent;
}

#newsMeta {
    color: #888888;
    font-size: 11px;
    background: transparent;
}

#newsFilterCombo {
    background-color: #2A2A2A;
    color: #FFFFFF;
    border: 1px solid #444444;
    border-radius: 6px;
    padding: 8px 14px;
    padding-right: 40px;
    min-width: 130px;
    font-size: 13px;
}

#newsFilterCombo:hover {
    border-color: #FF6A3D;
}

#newsFilterCombo::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: center right;
    width: 36px;
    border: none;
    background-color: #FF6A3D;
    border-top-right-radius: 5px;
    border-bottom-right-radius: 5px;
}

#newsFilterCombo::down-arrow {
    image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTQiIGhlaWdodD0iOCIgdmlld0JveD0iMCAwIDE0IDgiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PHBhdGggZD0iTTEgMUw3IDdMMTMgMSIgc3Ryb2tlPSJ3aGl0ZSIgc3Ryb2tlLXdpZHRoPSIyLjUiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCIvPjwvc3ZnPg==);
    width: 14px;
    height: 8px;
}

#newsFilterCombo:hover::drop-down {
    background-color: #FF8560;
}

#newsFilterCombo QAbstractItemView {
    background-color: #1E1E1E;
    color: #FFFFFF;
    selection-background-color: #FF6A3D;
    selection-color: #FFFFFF;
    border: 1px solid #444444;
    outline: none;
}

#newsFilterCombo QAbstractItemView::item {
    padding: 8px 12px;
    min-height: 24px;
}

#newsFilterCombo QAbstractItemView::item:hover {
    background-color: #FF6A3D;
    color: #FFFFFF;
}

#symbolHeader {
    color: #FF6A3D;
    font-weight: bold;
    font-size: 15px;
}

/* Mode Cards for Service Settings */
#modeCard {
    background-color: #1A1A1A;
    border: 2px solid #3A3A3A;
    border-radius: 8px;
}

#modeCard:hover {
    border-color: #FF6A3D;
}
"""

    def _get_light_theme(self) -> str:
        """Get light theme stylesheet using CushLabs brand colors and Segoe UI Variable."""
        return """
/* AI StockAlert - Light Theme (CushLabs Brand) */
/* Primary: #FF6A3D (Cush Orange) */
/* Typography: Segoe UI Variable (Native Windows) */

* {
    font-family: "Segoe UI Variable Text", "Segoe UI", sans-serif;
    font-size: 14px;
}

QMainWindow, QWidget {
    background-color: #FAF8F5;
    color: #000000;
}

/* Display/Hero text uses Segoe UI Variable Display with Bold weight */
#headerLogo {
    font-family: "Segoe UI Variable Display", "Segoe UI", sans-serif;
    font-weight: 700;
}

/* Section Headers use Semibold weight */
#sectionTitle, QGroupBox::title, #mainTabs QTabBar::tab {
    font-family: "Segoe UI Variable Display", "Segoe UI", sans-serif;
    font-weight: 600;
}

/* Header */
#header {
    background-color: #F5F3EE;
    border-bottom: 1px solid #E5E5E5;
}

#headerLogo {
    font-size: 32px;
    font-weight: 700;
    color: #FF6A3D;
    background-color: transparent;
}

#headerLabel {
    font-size: 13px;
    color: #666666;
    background-color: transparent;
}

#headerInner {
    background-color: transparent;
}

/* Language Switcher - EN | ES style */
#langButton {
    background-color: transparent;
    border: none;
    color: #666666;
    font-size: 14px;
    font-weight: normal;
    padding: 4px 2px;
    min-width: 24px;
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
    padding: 0 2px;
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
    background-color: #F5F3EE;
    border-top: 1px solid #E8E4DD;
}

#footerInner {
    background-color: transparent;
}

#footerText {
    font-size: 13px;
    color: #FF6A3D;
    background-color: transparent;
}

#footerLink {
    font-size: 13px;
    color: #FF6A3D;
    background-color: transparent;
    border: none;
    padding: 5px 10px;
}

#footerLink:hover {
    color: #E55A2D;
    text-decoration: underline;
    background-color: transparent;
}

#footerSeparator {
    color: #FF6A3D;
    margin: 0 5px;
    background-color: transparent;
}

/* Content Area - Light sand background */
#contentScrollArea {
    background-color: #FAF8F5;
    border: none;
}

#contentContainer {
    background-color: #FAF8F5;
}

#innerContent {
    background-color: transparent;
}

/* Tabs */
#mainTabs {
    font-size: 16px;
}

#mainTabs::pane {
    border: 1px solid #E8E4DD;
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
    font-size: 24px;
    font-weight: 600;
    color: #000000;
    margin-bottom: 10px;
}

#helpSectionTitle {
    font-size: 20px;
    font-weight: 600;
    color: #FF6A3D;
    margin-top: 16px;
    margin-bottom: 8px;
}

#helpContent {
    font-size: 14px;
    font-weight: 400;
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

#tickerTable QTableCornerButton::section {
    background-color: #FAFAFA;
    border: none;
    border-bottom: 1px solid #E5E5E5;
}

#tickerTable QWidget {
    background-color: transparent;
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

/* Action buttons (smaller orange buttons for service control, etc.) */
#actionButton, QPushButton[objectName="actionButton"] {
    background-color: #FF6A3D;
    color: #FFFFFF;
    border: none;
    border-radius: 6px;
    padding: 8px 16px;
    font-size: 13px;
    font-weight: 600;
    min-width: 100px;
}

#actionButton:hover, QPushButton[objectName="actionButton"]:hover {
    background-color: #E55A2D;
}

#actionButton:pressed, QPushButton[objectName="actionButton"]:pressed {
    background-color: #CC4A1D;
}

#actionButton:disabled, QPushButton[objectName="actionButton"]:disabled {
    background-color: #E5E5E5;
    color: #999999;
}

#dangerButton {
    background-color: #DC3545;
    color: #FFFFFF;
    border: none;
    border-radius: 6px;
    padding: 8px 16px;
    font-size: 13px;
    font-weight: 600;
    min-width: 100px;
}

#dangerButton:hover {
    background-color: #C82333;
}

#dangerButton:pressed {
    background-color: #A71D2A;
}

/* Captions/Labels - 12px muted grey */
#helpLabel {
    color: #666666;
    font-size: 13px;
    font-weight: 400;
    margin-bottom: 12px;
}

/* Form Elements - Body text 14-16px */
QLabel {
    font-size: 14px;
    font-weight: 400;
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
    border-radius: 0px;
    border: 2px solid #E5E5E5;
    background-color: #FFFFFF;
}

QCheckBox::indicator:checked {
    background-color: #FF6A3D;
    border-color: #FF6A3D;
}

/* Ticker table checkboxes - square shape */
#tickerCheckbox {
    spacing: 0px;
    margin: 0px;
    padding: 0px;
}

#tickerCheckbox::indicator {
    width: 20px;
    height: 20px;
    min-width: 20px;
    min-height: 20px;
    max-width: 20px;
    max-height: 20px;
    border-radius: 0px;
    border: 2px solid #CCCCCC;
    background-color: #FFFFFF;
}

#tickerCheckbox::indicator:checked {
    background-color: #FF6A3D;
    border-color: #FF6A3D;
    image: none;
}

#tickerCheckbox::indicator:hover {
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

#modeRadio {
    font-weight: bold;
    font-size: 14px;
    color: #000000;
    min-height: 24px;
    spacing: 8px;
}

#modeRadio::indicator {
    width: 18px;
    height: 18px;
    min-width: 18px;
    min-height: 18px;
    border-radius: 9px;
    border: 2px solid #CCCCCC;
    background-color: #FFFFFF;
}

#modeRadio::indicator:hover {
    border-color: #FF6A3D;
}

#modeRadio::indicator:checked {
    background-color: #FF6A3D;
    border-color: #FF6A3D;
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

/* News Widget - Light Theme */
#newsCard {
    background-color: #FFFFFF;
    border: 1px solid #D0D0D0;
    border-radius: 12px;
}

#newsCard:hover {
    border-color: #FF6A3D;
    background-color: #FFF8F5;
}

#newsThumbnail {
    background-color: #F0F0F0;
    border-radius: 8px;
    font-size: 32px;
}

#newsHeadline {
    font-weight: bold;
    font-size: 14px;
    color: #000000;
}

#newsSummary {
    color: #444444;
    font-size: 12px;
}

#newsMeta {
    color: #666666;
    font-size: 11px;
}

#newsFilterCombo {
    background-color: #FFFFFF;
    color: #000000;
    border: 1px solid #CCCCCC;
    border-radius: 6px;
    padding: 8px 14px;
    padding-right: 40px;
    min-width: 130px;
    font-size: 13px;
}

#newsFilterCombo:hover {
    border-color: #FF6A3D;
}

#newsFilterCombo::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: center right;
    width: 36px;
    border: none;
    background-color: #FF6A3D;
    border-top-right-radius: 5px;
    border-bottom-right-radius: 5px;
}

#newsFilterCombo::down-arrow {
    image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTQiIGhlaWdodD0iOCIgdmlld0JveD0iMCAwIDE0IDgiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PHBhdGggZD0iTTEgMUw3IDdMMTMgMSIgc3Ryb2tlPSJ3aGl0ZSIgc3Ryb2tlLXdpZHRoPSIyLjUiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCIvPjwvc3ZnPg==);
    width: 14px;
    height: 8px;
}

#newsFilterCombo:hover::drop-down {
    background-color: #FF8560;
}

#newsFilterCombo QAbstractItemView {
    background-color: #FFFFFF;
    color: #000000;
    selection-background-color: #FF6A3D;
    selection-color: #FFFFFF;
    border: 1px solid #CCCCCC;
}

#symbolHeader {
    color: #FF6A3D;
    font-weight: bold;
    font-size: 15px;
}

/* Mode Cards for Service Settings */
#modeCard {
    background-color: #FFFFFF;
    border: 2px solid #E5E5E5;
    border-radius: 8px;
}

#modeCard:hover {
    border-color: #FF6A3D;
}
"""

    def _update_lang_buttons(self, current_lang: str) -> None:
        """Update language button styles to show current selection."""
        self.lang_en_btn.setChecked(current_lang == "en")
        self.lang_es_btn.setChecked(current_lang == "es")

    def _set_language(self, language: str) -> None:
        """Set the application language."""
        logger.info(f"Header button: changing language to '{language}'")
        self.translator.set_language(language)
        self.config_manager.set("settings.language", language, save=True)
        self._update_lang_buttons(language)
        self.retranslate_ui()
        # Also retranslate the settings widget if it exists
        if hasattr(self, 'settings_widget') and self.settings_widget:
            self.settings_widget.retranslate_ui()

    def _create_app_icon(self) -> QIcon:
        """Create a branded app icon programmatically with multiple sizes."""
        from PyQt6.QtCore import Qt
        from PyQt6.QtGui import QPixmap, QPainter, QColor, QPen

        icon = QIcon()

        # Create multiple sizes for Windows DPI scaling
        for size in [16, 24, 32, 48, 64, 128, 256]:
            pixmap = QPixmap(size, size)
            pixmap.fill(QColor("#FF6A3D"))  # Solid orange

            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)

            # Draw white trend line scaled to size
            scale = size / 64.0
            pen_width = max(1, int(4 * scale))
            painter.setPen(QPen(Qt.GlobalColor.white, pen_width))

            # Scaled line coordinates
            x1, y1 = int(12 * scale), int(48 * scale)
            x2, y2 = int(28 * scale), int(24 * scale)
            x3, y3 = int(52 * scale), int(40 * scale)
            painter.drawLine(x1, y1, x2, y2)
            painter.drawLine(x2, y2, x3, y3)

            painter.end()
            icon.addPixmap(pixmap)

        return icon

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

    def _truncate_text(self, text: str, max_length: int = 30) -> str:
        """Truncate text with ellipsis if too long.

        Args:
            text: Text to truncate
            max_length: Maximum length before truncation

        Returns:
            Original text or truncated with ellipsis
        """
        if len(text) <= max_length:
            return text
        return text[: max_length - 3] + "..."

    def _format_market_cap(self, market_cap: float) -> tuple[str, str]:
        """Format market cap value and return category.

        Args:
            market_cap: Market cap in millions

        Returns:
            Tuple of (formatted string, category)
        """
        if market_cap <= 0:
            return ("--", "")

        # market_cap is already in millions from Finnhub
        if market_cap >= 200000:  # $200B+
            return (f"${market_cap / 1000:.0f}B", "Mega")
        elif market_cap >= 10000:  # $10B+
            return (f"${market_cap / 1000:.1f}B", "Large")
        elif market_cap >= 2000:  # $2B+
            return (f"${market_cap / 1000:.1f}B", "Mid")
        elif market_cap >= 300:  # $300M+
            return (f"${market_cap:.0f}M", "Small")
        else:
            return (f"${market_cap:.0f}M", "Micro")

    def _load_logo(self, url: str, row: int, symbol: str) -> None:
        """Asynchronously load a company logo.

        Args:
            url: Logo image URL
            row: Table row to update
            symbol: Stock symbol for tracking
        """
        if not url:
            return

        # Check cache first
        if url in self._logo_cache:
            # Move to end of order list (most recently used)
            if url in self._logo_cache_order:
                self._logo_cache_order.remove(url)
                self._logo_cache_order.append(url)
            self._set_logo_cell(row, self._logo_cache[url], symbol)
            return

        # Track pending request
        self._pending_logos[url] = (row, symbol)

        # Start async download
        request = QNetworkRequest(QUrl(url))
        self._network_manager.get(request)

    def _on_logo_loaded(self, reply: QNetworkReply) -> None:
        """Handle logo download completion."""
        url = reply.url().toString()

        if url in self._pending_logos:
            row, symbol = self._pending_logos.pop(url)

            if reply.error() == QNetworkReply.NetworkError.NoError:
                data = reply.readAll()
                pixmap = QPixmap()
                pixmap.loadFromData(data)

                if not pixmap.isNull():
                    # Scale to fit cell
                    scaled = pixmap.scaled(
                        32, 32,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation
                    )
                    self._add_to_logo_cache(url, scaled)
                    self._set_logo_cell(row, scaled, symbol)

        reply.deleteLater()

    def _add_to_logo_cache(self, url: str, pixmap: QPixmap) -> None:
        """Add a logo to the cache with LRU eviction.

        Args:
            url: Logo URL (cache key)
            pixmap: Logo pixmap to cache
        """
        # If already in cache, move to end of order list (most recently used)
        if url in self._logo_cache:
            self._logo_cache_order.remove(url)
            self._logo_cache_order.append(url)
            return

        # Evict oldest entries if cache is full
        while len(self._logo_cache) >= self._logo_cache_max_size:
            if self._logo_cache_order:
                oldest_url = self._logo_cache_order.pop(0)
                self._logo_cache.pop(oldest_url, None)

        # Add to cache
        self._logo_cache[url] = pixmap
        self._logo_cache_order.append(url)

    def _set_logo_cell(self, row: int, pixmap: QPixmap, symbol: str = "") -> None:
        """Set the logo pixmap in a table cell - clickable to open chart."""
        if row >= self.ticker_table.rowCount():
            return

        # Get symbol from the row if not provided
        if not symbol:
            item = self.ticker_table.item(row, 2)
            symbol = item.text() if item else ""

        btn = QPushButton()
        btn.setIcon(QIcon(pixmap))
        btn.setIconSize(pixmap.size())
        btn.setFlat(True)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setToolTip(f"View {symbol} chart")
        btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                padding: 2px;
            }
            QPushButton:hover {
                background-color: #2A2A2A;
                border-radius: 4px;
            }
        """)
        btn.clicked.connect(lambda checked, s=symbol: self._open_chart(s))
        self.ticker_table.setCellWidget(row, 1, btn)

    def _open_chart(self, symbol: str) -> None:
        """Open stock chart in browser."""
        # Use TradingView chart URL
        chart_url = f"https://www.tradingview.com/chart/?symbol={symbol}"
        QDesktopServices.openUrl(QUrl(chart_url))

    def _get_website_lang_prefix(self) -> str:
        """Get the language prefix for website URLs."""
        lang = self.config_manager.get("settings.language", "en")
        return "es" if lang == "es" else "en"

    def _open_privacy_link(self) -> None:
        """Open privacy policy in browser with correct language."""
        lang = self._get_website_lang_prefix()
        url = f"https://ai-stock-alert-website.netlify.app/{lang}/privacy"
        QDesktopServices.openUrl(QUrl(url))

    def _open_terms_link(self) -> None:
        """Open terms of service in browser with correct language."""
        lang = self._get_website_lang_prefix()
        url = f"https://ai-stock-alert-website.netlify.app/{lang}/terms"
        QDesktopServices.openUrl(QUrl(url))

    def _load_data(self) -> None:
        """Load data into the UI."""
        self._refresh_ticker_table()

    def _refresh_ticker_table(self) -> None:
        """Refresh the ticker table with current data."""
        from stockalert.core.tier_limits import get_max_tickers

        tickers = self.config_manager.get_tickers()
        self.ticker_table.setRowCount(len(tickers))

        # Update ticker count label
        current_count = len(tickers)
        max_count = get_max_tickers()
        self.ticker_count_label.setText(_("tickers.ticker_count", current=current_count, max=max_count))

        # Change color based on limit proximity
        if current_count >= max_count:
            self.ticker_count_label.setStyleSheet("color: #FF6A3D; font-size: 12px; margin-left: 12px; font-weight: bold;")
        elif current_count >= max_count - 3:
            self.ticker_count_label.setStyleSheet("color: #FFAA00; font-size: 12px; margin-left: 12px;")
        else:
            self.ticker_count_label.setStyleSheet("color: #888888; font-size: 12px; margin-left: 12px;")

        for row, ticker in enumerate(tickers):
            # Column 0: Checkbox
            checkbox_widget = QWidget()
            checkbox_widget.setStyleSheet("background-color: transparent;")
            checkbox_layout = QHBoxLayout(checkbox_widget)
            checkbox_layout.setContentsMargins(0, 0, 0, 0)
            checkbox_layout.addStretch()
            checkbox = QCheckBox()
            checkbox.setObjectName("tickerCheckbox")
            checkbox.setFixedSize(18, 18)
            checkbox.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
            checkbox.setStyleSheet("""
                QCheckBox {
                    spacing: 0px;
                    background-color: transparent;
                }
                QCheckBox::indicator {
                    width: 16px;
                    height: 16px;
                    border: 2px solid #555555;
                    border-radius: 0px;
                    background-color: #1A1A1A;
                }
                QCheckBox::indicator:checked {
                    background-color: #FF6A3D;
                    border-color: #FF6A3D;
                }
                QCheckBox::indicator:hover {
                    border-color: #FF6A3D;
                }
            """)
            checkbox.stateChanged.connect(self._on_checkbox_changed)
            checkbox_layout.addWidget(checkbox)
            checkbox_layout.addStretch()
            self.ticker_table.setCellWidget(row, 0, checkbox_widget)

            # Column 1: Logo (async load) - clickable to open chart
            logo_url = ticker.get("logo", "")
            symbol = ticker.get("symbol", "")
            if logo_url:
                self._load_logo(logo_url, row, symbol)
            else:
                # Placeholder for missing logo - clickable to open chart
                placeholder = QPushButton("📈")
                placeholder.setFlat(True)
                placeholder.setCursor(Qt.CursorShape.PointingHandCursor)
                placeholder.setToolTip(f"View {symbol} chart")
                placeholder.setStyleSheet("""
                    QPushButton {
                        background-color: transparent;
                        font-size: 18px;
                        border: none;
                    }
                    QPushButton:hover {
                        background-color: #2A2A2A;
                        border-radius: 4px;
                    }
                """)
                placeholder.clicked.connect(lambda checked, s=symbol: self._open_chart(s))
                self.ticker_table.setCellWidget(row, 1, placeholder)

            # Column 2: Symbol
            symbol_item = QTableWidgetItem(symbol)
            symbol_item.setFlags(symbol_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.ticker_table.setItem(row, 2, symbol_item)

            # Column 3: Name (truncate long names, show full in tooltip)
            full_name = ticker.get("name", "")
            display_name = self._truncate_text(full_name, max_length=30)
            name_item = QTableWidgetItem(display_name)
            name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            if len(full_name) > 30:
                name_item.setToolTip(full_name)
            self.ticker_table.setItem(row, 3, name_item)

            # Column 4: Industry
            industry = ticker.get("industry", "")
            industry_item = QTableWidgetItem(industry if industry else "--")
            industry_item.setFlags(industry_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.ticker_table.setItem(row, 4, industry_item)

            # Column 5: Market Cap with category badge
            market_cap = ticker.get("market_cap", 0)
            cap_str, cap_category = self._format_market_cap(market_cap)
            if cap_category:
                cap_display = f"{cap_str} ({cap_category})"
            else:
                cap_display = cap_str
            cap_item = QTableWidgetItem(cap_display)
            cap_item.setFlags(cap_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            cap_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.ticker_table.setItem(row, 5, cap_item)

            # Column 6: High threshold
            high = ticker.get("high_threshold", 0)
            high_item = QTableWidgetItem(f"${high:.2f}")
            high_item.setFlags(high_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            high_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.ticker_table.setItem(row, 6, high_item)

            # Column 7: Low threshold
            low = ticker.get("low_threshold", 0)
            low_item = QTableWidgetItem(f"${low:.2f}")
            low_item.setFlags(low_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            low_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.ticker_table.setItem(row, 7, low_item)

            # Column 8: Last price (placeholder)
            price_item = QTableWidgetItem("--")
            price_item.setFlags(price_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            price_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.ticker_table.setItem(row, 8, price_item)

            # Column 9: Enabled
            enabled = ticker.get("enabled", True)
            enabled_item = QTableWidgetItem("✓" if enabled else "✗")
            enabled_item.setFlags(enabled_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            enabled_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.ticker_table.setItem(row, 9, enabled_item)

        # Update button states and header
        self._update_action_buttons()
        self._update_select_all_header()

        # Fetch prices asynchronously after table is populated
        QTimer.singleShot(100, self._fetch_ticker_prices)

    def _fetch_ticker_prices(self) -> None:
        """Fetch current prices for all tickers using QTimer for responsiveness."""
        from stockalert.api.finnhub import FinnhubProvider
        from stockalert.core.api_key_manager import get_api_key

        api_key = get_api_key()
        if not api_key:
            logger.warning("No API key, cannot fetch prices")
            return

        # Store state for sequential fetching
        self._price_fetch_provider = FinnhubProvider(api_key=api_key)
        self._price_fetch_symbols = [t.get("symbol", "") for t in self.config_manager.get_tickers() if t.get("symbol")]
        self._price_fetch_index = 0

        # Start fetching first price
        self._fetch_next_price()

    def _fetch_next_price(self) -> None:
        """Fetch the next ticker price in the queue."""
        if not hasattr(self, '_price_fetch_symbols') or self._price_fetch_index >= len(self._price_fetch_symbols):
            # Done fetching - clean up
            if hasattr(self, '_price_fetch_provider'):
                delattr(self, '_price_fetch_provider')
            if hasattr(self, '_price_fetch_symbols'):
                delattr(self, '_price_fetch_symbols')
            if hasattr(self, '_price_fetch_index'):
                delattr(self, '_price_fetch_index')
            return

        symbol = self._price_fetch_symbols[self._price_fetch_index]
        self._price_fetch_index += 1

        try:
            price = self._price_fetch_provider.get_price(symbol)
            if price is not None:
                self.update_ticker_price(symbol, price)
                logger.debug(f"Updated price for {symbol}: ${price:.2f}")
        except Exception as e:
            logger.debug(f"Failed to fetch price for {symbol}: {e}")

        # Schedule next fetch with small delay to keep UI responsive
        QTimer.singleShot(50, self._fetch_next_price)

    def _get_selected_row(self) -> int:
        """Get the currently selected row index, or -1 if none."""
        selection = self.ticker_table.selectedItems()
        if selection:
            return int(selection[0].row())
        return -1

    def _get_selected_symbol(self) -> str | None:
        """Get the symbol of the selected row."""
        row = self._get_selected_row()
        if row >= 0:
            item = self.ticker_table.item(row, 2)  # Column 2 is symbol
            if item:
                return str(item.text())
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
        selected = self._get_selected_symbols()
        if len(selected) != 1:
            QMessageBox.warning(
                self,
                _("errors.title"),
                _("tickers.no_selection"),
            )
            return

        symbol = selected[0]

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
        selected = self._get_selected_symbols()
        if not selected:
            QMessageBox.warning(
                self,
                _("errors.title"),
                _("tickers.no_selection"),
            )
            return

        # Confirmation message varies by count
        count = len(selected)
        if count == 1:
            confirm_msg = _("tickers.delete_confirm", symbol=selected[0])
        else:
            confirm_msg = _("tickers.delete_confirm_multiple", count=count)

        result = QMessageBox.question(
            self,
            _("dialogs.confirm"),
            confirm_msg,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if result == QMessageBox.StandardButton.Yes:
            for symbol in selected:
                self.config_manager.delete_ticker(symbol)
            self._refresh_ticker_table()
            self.status_bar.showMessage(_("tickers.delete_success"))
            if self.on_settings_changed:
                self.on_settings_changed()

    def _on_toggle_ticker(self) -> None:
        """Handle toggle ticker button."""
        selected = self._get_selected_symbols()
        if not selected:
            QMessageBox.warning(
                self,
                _("errors.title"),
                _("tickers.no_selection"),
            )
            return

        for symbol in selected:
            self.config_manager.toggle_ticker(symbol)
        self._refresh_ticker_table()
        if self.on_settings_changed:
            self.on_settings_changed()

    def _on_refresh_profiles(self) -> None:
        """Refresh company profile data for all tickers."""
        from stockalert.api.finnhub import FinnhubProvider
        from stockalert.core.api_key_manager import get_api_key

        # Get API key from secure storage
        api_key = get_api_key()

        if not api_key:
            QMessageBox.warning(
                self,
                _("errors.title"),
                _("errors.no_api_key"),
            )
            return

        try:
            provider = FinnhubProvider(api_key=api_key)
        except Exception:
            logger.exception("Failed to initialize Finnhub provider")
            QMessageBox.warning(
                self,
                _("errors.title"),
                _("errors.no_api_key"),
            )
            return

        # Disable button and show loading state
        self.refresh_profiles_button.setEnabled(False)
        self.refresh_profiles_button.setText(_("tickers.refreshing_profiles"))
        QApplication.processEvents()

        tickers = self.config_manager.get_tickers()
        updated_count = 0

        for ticker in tickers:
            symbol = ticker["symbol"]
            try:
                profile = provider.get_company_profile(symbol)
                if profile:
                    self.config_manager.update_ticker(
                        symbol,
                        logo=profile.get("logo", ""),
                        industry=profile.get("finnhubIndustry", ""),
                        market_cap=profile.get("marketCapitalization", 0.0),
                        exchange=profile.get("exchange", ""),
                        weburl=profile.get("weburl", ""),
                        ipo=profile.get("ipo", ""),
                        country=profile.get("country", ""),
                        shares_outstanding=profile.get("shareOutstanding", 0.0),
                    )
                    updated_count += 1
                    logger.info(f"Updated profile for {symbol}")
            except Exception as e:
                logger.warning(f"Failed to fetch profile for {symbol}: {e}")

        # Restore button state
        self.refresh_profiles_button.setEnabled(True)
        self.refresh_profiles_button.setText(_("tickers.refresh_profiles"))

        # Refresh table to show new data
        self._refresh_ticker_table()

        # Show success message
        self.status_bar.showMessage(
            _("tickers.profiles_refreshed", count=updated_count)
        )

    def _on_settings_saved(self) -> None:
        """Handle settings saved event."""
        self.status_bar.showMessage(_("settings.saved"))
        if self.on_settings_changed:
            self.on_settings_changed()

    def retranslate_ui(self) -> None:
        """Update UI text after language change."""
        self.setWindowTitle(_("app.name"))

        # Update tab labels - Profile, Settings, Tickers, News, Help
        self.tabs.setTabText(0, _("tabs.profile"))
        self.tabs.setTabText(1, _("tabs.settings"))
        self.tabs.setTabText(2, _("tabs.tickers"))
        self.tabs.setTabText(3, _("tabs.news"))
        self.tabs.setTabText(4, _("tabs.help"))

        # Update child widgets
        self.profile_widget.retranslate_ui()
        self.settings_widget.retranslate_ui()
        self.news_widget.retranslate_ui()

        # Recreate help tab to update content (it has static text blocks)
        self.tabs.removeTab(4)
        self.help_widget = self._create_help_tab()
        self.tabs.insertTab(4, self.help_widget, _("tabs.help"))

        # Update theme button tooltip
        self._update_theme_icon()

        # Update footer
        self.copyright_label.setText(_("about.copyright"))
        self.website_btn.setText(_("footer.website"))
        self.privacy_btn.setText(_("footer.privacy"))
        self.terms_btn.setText(_("footer.terms"))

        # Update tickers tab title
        self.tickers_title.setText(_("tickers.title"))

        # Update ticker table headers (10 columns)
        self.ticker_table.setHorizontalHeaderLabels([
            "",  # Checkbox column
            "",  # Logo column
            _("tickers.symbol"),
            _("tickers.name"),
            _("tickers.industry"),
            _("tickers.market_cap"),
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
        self.refresh_profiles_button.setText(_("tickers.refresh_profiles"))

        # Update status bar
        self.status_bar.showMessage(_("status.ready"))

    def update_ticker_price(self, symbol: str, price: float | None) -> None:
        """Update the displayed price for a ticker.

        Args:
            symbol: Ticker symbol
            price: Current price, or None if unavailable
        """
        for row in range(self.ticker_table.rowCount()):
            item = self.ticker_table.item(row, 2)  # Column 2 = Symbol
            if item and item.text() == symbol:
                price_item = self.ticker_table.item(row, 8)  # Column 8 = Last Price
                if price_item:
                    if price is not None:
                        price_item.setText(f"${price:.2f}")
                    else:
                        price_item.setText("--")
                break

    def closeEvent(self, event: QCloseEvent | None) -> None:
        """Handle window close - minimize to tray instead of quitting."""
        # Check for unsaved settings changes
        if hasattr(self, 'settings_widget') and self.settings_widget.has_unsaved_changes():
            reply = QMessageBox.question(
                self,
                _("dialogs.unsaved_changes_title"),
                _("dialogs.unsaved_changes_message"),
                QMessageBox.StandardButton.Save |
                QMessageBox.StandardButton.Discard |
                QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Save
            )

            if reply == QMessageBox.StandardButton.Save:
                self.settings_widget._on_save_clicked()
            elif reply == QMessageBox.StandardButton.Cancel:
                if event is not None:
                    event.ignore()
                return

        # Save window geometry before closing/hiding
        self._save_window_geometry()

        # When running from source (development), actually quit on close
        # When running as installed exe, minimize to tray
        if not getattr(sys, "frozen", False):
            # Development mode - actually quit
            if event is not None:
                event.accept()
            QApplication.instance().quit()
        else:
            # Production mode - hide to tray
            if event is not None:
                event.ignore()
            self.hide()

    def _save_window_geometry(self) -> None:
        """Save window position and size to config."""
        try:
            geometry = self.geometry()
            window_state = {
                "x": geometry.x(),
                "y": geometry.y(),
                "width": geometry.width(),
                "height": geometry.height(),
                "maximized": self.isMaximized(),
            }
            self.config_manager.set("window", window_state, save=True)
        except Exception as e:
            logger.debug(f"Failed to save window geometry: {e}")

    def _restore_window_geometry(self) -> None:
        """Restore window position and size from config."""
        try:
            window_state = self.config_manager.get("window", {})
            if not window_state:
                return

            x = window_state.get("x")
            y = window_state.get("y")
            width = window_state.get("width")
            height = window_state.get("height")
            maximized = window_state.get("maximized", False)

            # Validate values exist
            if None in (x, y, width, height):
                return

            # Ensure window is on a visible screen
            from PyQt6.QtGui import QGuiApplication

            screens = QGuiApplication.screens()
            if screens:
                # Check if saved position is on any screen
                point = QPoint(x + width // 2, y + height // 2)
                on_screen = any(
                    screen.geometry().contains(point) for screen in screens
                )

                if on_screen:
                    self.setGeometry(x, y, width, height)
                    if maximized:
                        self.showMaximized()
                    return

            # Position not on any screen, use default
            logger.debug("Saved window position not on visible screen, using default")

        except Exception as e:
            logger.debug(f"Failed to restore window geometry: {e}")
