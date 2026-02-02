"""
News widget for displaying company and market news.

Fetches and displays news from Finnhub API.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING, Any

from PyQt6.QtCore import Qt, QThread, QUrl, pyqtSignal
from PyQt6.QtGui import QDesktopServices, QMouseEvent, QPixmap
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest
from PyQt6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from stockalert.i18n.translator import _

if TYPE_CHECKING:
    from stockalert.core.config import ConfigManager
    from stockalert.i18n.translator import Translator

logger = logging.getLogger(__name__)


class NewsFetcher(QThread):
    """Background thread for fetching news."""

    news_ready = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(
        self,
        api_key: str,
        symbols: list[str] | None = None,
        category: str = "general",
    ) -> None:
        super().__init__()
        self.api_key = api_key
        self.symbols = symbols
        self.category = category

    def run(self) -> None:
        """Fetch news in background."""
        try:
            from stockalert.api.finnhub import FinnhubProvider

            provider = FinnhubProvider(api_key=self.api_key)
            all_news = []

            if self.symbols:
                # Fetch company-specific news
                today = datetime.now()
                week_ago = today - timedelta(days=7)
                from_date = week_ago.strftime("%Y-%m-%d")
                to_date = today.strftime("%Y-%m-%d")

                for symbol in self.symbols[:5]:  # Limit to 5 to conserve API calls
                    news = provider.get_company_news(symbol, from_date, to_date)
                    for article in news[:3]:  # Top 3 per symbol
                        article["_symbol"] = symbol
                        all_news.append(article)
            else:
                # Fetch general market news
                all_news = provider.get_market_news(self.category)[:15]

            # Sort by datetime (newest first)
            all_news.sort(key=lambda x: x.get("datetime", 0), reverse=True)

            self.news_ready.emit(all_news)

        except Exception as e:
            logger.exception("Failed to fetch news")
            self.error.emit(str(e))


class NewsCard(QFrame):
    """Individual news article card."""

    def __init__(
        self,
        article: dict[str, Any],
        show_symbol_badge: bool = True,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.article = article
        self.show_symbol_badge = show_symbol_badge
        self.setObjectName("newsCard")
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Set up the card UI."""
        self.setFrameStyle(QFrame.Shape.StyledPanel)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        # Thumbnail placeholder
        self.thumbnail = QLabel()
        self.thumbnail.setFixedSize(80, 80)
        self.thumbnail.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.thumbnail.setObjectName("newsThumbnail")
        self.thumbnail.setText("📰")
        layout.addWidget(self.thumbnail)

        # Content area
        content_layout = QVBoxLayout()
        content_layout.setSpacing(4)

        # Symbol badge (if company news and badge enabled)
        symbol = self.article.get("_symbol")
        if symbol and self.show_symbol_badge:
            badge = QLabel(symbol)
            badge.setObjectName("symbolBadge")
            badge.setStyleSheet("""
                background-color: #FF6A3D;
                color: #000000;
                padding: 2px 8px;
                border-radius: 4px;
                font-size: 11px;
                font-weight: bold;
            """)
            badge.setFixedWidth(badge.sizeHint().width())
            content_layout.addWidget(badge)

        # Headline
        headline = self.article.get("headline", "No headline")
        headline_label = QLabel(headline)
        headline_label.setObjectName("newsHeadline")
        headline_label.setWordWrap(True)
        content_layout.addWidget(headline_label)

        # Summary (truncated)
        summary = self.article.get("summary", "")
        if len(summary) > 150:
            summary = summary[:150] + "..."
        if summary:
            summary_label = QLabel(summary)
            summary_label.setObjectName("newsSummary")
            summary_label.setWordWrap(True)
            content_layout.addWidget(summary_label)

        # Meta row (source + time)
        meta_layout = QHBoxLayout()
        meta_layout.setSpacing(16)

        source = self.article.get("source", "Unknown")
        source_label = QLabel(f"📰 {source}")
        source_label.setObjectName("newsMeta")
        meta_layout.addWidget(source_label)

        timestamp = self.article.get("datetime", 0)
        if timestamp:
            dt = datetime.fromtimestamp(timestamp)
            time_str = dt.strftime("%b %d, %I:%M %p")
            time_label = QLabel(f"🕐 {time_str}")
            time_label.setObjectName("newsMeta")
            meta_layout.addWidget(time_label)

        meta_layout.addStretch()
        content_layout.addLayout(meta_layout)

        layout.addLayout(content_layout, 1)
        # Card styling (including hover) is handled by theme in main_window.py

    def mousePressEvent(self, event: QMouseEvent | None) -> None:
        """Open article in browser on click."""
        url = self.article.get("url")
        if url:
            QDesktopServices.openUrl(QUrl(url))
        super().mousePressEvent(event)


class NewsWidget(QWidget):
    """Widget displaying news feed."""

    def __init__(
        self,
        config_manager: ConfigManager,
        translator: Translator,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.config_manager = config_manager
        self.translator = translator
        self._fetcher: NewsFetcher | None = None
        self._network_manager = QNetworkAccessManager(self)
        self._network_manager.finished.connect(self._on_thumbnail_loaded)
        self._pending_thumbnails: dict[str, NewsCard] = {}

        self._setup_ui()
        self._load_news()

    def _setup_ui(self) -> None:
        """Set up the widget UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        # Header with filter - all items vertically centered
        header_layout = QHBoxLayout()
        header_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        header_layout.setSpacing(12)

        # Dynamic title that updates based on filter
        self.title_label = QLabel(_("news.title") + " - " + _("news.my_stocks"))
        self.title_label.setObjectName("sectionTitle")
        header_layout.addWidget(self.title_label, alignment=Qt.AlignmentFlag.AlignVCenter)

        header_layout.addStretch()

        # News type filter styled as orange button with arrow
        self.filter_combo = QComboBox()
        self.filter_combo.addItem(_("news.my_stocks"), "stocks")
        self.filter_combo.addItem(_("news.general"), "general")
        self.filter_combo.addItem(_("news.crypto"), "crypto")
        self.filter_combo.addItem(_("news.forex"), "forex")
        self.filter_combo.addItem(_("news.mergers"), "merger")
        self.filter_combo.currentIndexChanged.connect(self._on_filter_changed)
        self.filter_combo.setObjectName("newsFilterCombo")
        self.filter_combo.setFixedHeight(40)
        self.filter_combo.setMinimumWidth(140)

        # Get path to chevron SVG asset
        assets_dir = Path(__file__).parent.parent / "assets"
        chevron_path = (assets_dir / "chevron-down.svg").as_posix()

        self.filter_combo.setStyleSheet(f"""
            QComboBox#newsFilterCombo {{
                background-color: #FF6A3D;
                color: #FFFFFF;
                border: none;
                border-radius: 6px;
                padding: 0px 36px 0px 16px;
                min-width: 140px;
                font-size: 13px;
                font-weight: 600;
            }}
            QComboBox#newsFilterCombo:hover {{
                background-color: #FF8560;
            }}
            QComboBox#newsFilterCombo::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: center right;
                width: 30px;
                border: none;
            }}
            QComboBox#newsFilterCombo::down-arrow {{
                image: url({chevron_path});
                width: 14px;
                height: 8px;
            }}
            QComboBox#newsFilterCombo QAbstractItemView {{
                background-color: #1E1E1E;
                color: #FFFFFF;
                selection-background-color: #FF6A3D;
                selection-color: #FFFFFF;
                border: 1px solid #444444;
                border-radius: 4px;
                outline: none;
                padding: 4px;
            }}
            QComboBox#newsFilterCombo QAbstractItemView::item {{
                padding: 8px 12px;
                min-height: 24px;
                color: #FFFFFF;
            }}
            QComboBox#newsFilterCombo QAbstractItemView::item:hover {{
                background-color: #FF6A3D;
                color: #FFFFFF;
            }}
            QComboBox#newsFilterCombo QAbstractItemView::item:selected {{
                background-color: #FF6A3D;
                color: #FFFFFF;
            }}
        """)
        header_layout.addWidget(self.filter_combo, alignment=Qt.AlignmentFlag.AlignVCenter)

        # Refresh button - same height as combo for alignment
        self.refresh_btn = QPushButton(_("news.refresh"))
        self.refresh_btn.setObjectName("actionButton")
        self.refresh_btn.setFixedHeight(40)
        self.refresh_btn.clicked.connect(self._load_news)
        self.refresh_btn.setStyleSheet("""
            QPushButton#actionButton {
                background-color: #FF6A3D;
                color: #FFFFFF;
                border: none;
                border-radius: 6px;
                padding: 0px 20px;
                font-size: 13px;
                font-weight: 600;
            }
            QPushButton#actionButton:hover {
                background-color: #FF8560;
            }
        """)
        header_layout.addWidget(self.refresh_btn, alignment=Qt.AlignmentFlag.AlignVCenter)

        layout.addLayout(header_layout)

        # Loading/status label
        self.status_label = QLabel(_("news.loading"))
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("color: #888888; padding: 20px;")
        layout.addWidget(self.status_label)

        # Scrollable news feed
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setObjectName("newsScrollArea")

        self.news_container = QWidget()
        self.news_layout = QVBoxLayout(self.news_container)
        self.news_layout.setSpacing(12)
        self.news_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.scroll_area.setWidget(self.news_container)
        layout.addWidget(self.scroll_area, 1)

    def _on_filter_changed(self, index: int) -> None:  # noqa: ARG002
        """Handle filter change."""
        # Update title based on selection
        filter_text = self.filter_combo.currentText()
        self.title_label.setText(_("news.title") + " - " + filter_text)
        self._load_news()

    def _load_news(self) -> None:
        """Load news from API."""
        # Clear existing news
        while self.news_layout.count():
            item = self.news_layout.takeAt(0)
            if item is not None:
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()

        self.status_label.setText(_("news.loading"))
        self.status_label.show()
        self.refresh_btn.setEnabled(False)

        # Get API key from secure storage
        from stockalert.core.api_key_manager import get_api_key
        api_key = get_api_key()

        if not api_key:
            self.status_label.setText(_("errors.no_api_key"))
            self.refresh_btn.setEnabled(True)
            return

        # Determine what to fetch
        filter_value = self.filter_combo.currentData()
        self._current_filter = filter_value
        self._ticker_names: dict[str, str] = {}

        if filter_value == "stocks":
            # Fetch news for monitored stocks
            tickers = self.config_manager.get_tickers()
            symbols = []
            for t in tickers:
                if t.get("enabled", True):
                    symbol = t["symbol"]
                    symbols.append(symbol)
                    self._ticker_names[symbol] = t.get("name", symbol)
            if not symbols:
                self.status_label.setText(_("news.no_stocks"))
                self.refresh_btn.setEnabled(True)
                return
            self._fetcher = NewsFetcher(api_key, symbols=symbols)
        else:
            # Fetch general news
            self._fetcher = NewsFetcher(api_key, category=filter_value)

        self._fetcher.news_ready.connect(self._on_news_ready)
        self._fetcher.error.connect(self._on_news_error)
        self._fetcher.start()

    def _on_news_ready(self, articles: list[dict[str, Any]]) -> None:
        """Handle news loaded."""
        self.status_label.hide()
        self.refresh_btn.setEnabled(True)

        if not articles:
            self.status_label.setText(_("news.no_news"))
            self.status_label.show()
            return

        # Group by ticker if viewing "My Stocks"
        if self._current_filter == "stocks":
            self._display_grouped_news(articles)
        else:
            self._display_flat_news(articles)

        # Add spacer at end
        self.news_layout.addStretch()

        # Scroll to top AFTER content is added
        # Process events to ensure layout is complete, then scroll
        from PyQt6.QtWidgets import QApplication
        QApplication.processEvents()
        scrollbar = self.scroll_area.verticalScrollBar()
        if scrollbar is not None:
            scrollbar.setValue(0)

        # Also schedule a delayed scroll as backup
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(100, self._scroll_to_top)

    def _scroll_to_top(self) -> None:
        """Scroll the news feed to the top."""
        scrollbar = self.scroll_area.verticalScrollBar()
        if scrollbar is not None:
            scrollbar.setValue(0)

    def _display_flat_news(self, articles: list[dict[str, Any]]) -> None:
        """Display news in a flat list."""
        for article in articles:
            card = NewsCard(article)
            self.news_layout.addWidget(card)

            image_url = article.get("image")
            if image_url:
                self._load_thumbnail(image_url, card)

    def _display_grouped_news(self, articles: list[dict[str, Any]]) -> None:
        """Display news grouped by ticker symbol."""
        # Group articles by symbol
        grouped: dict[str, list[dict[str, Any]]] = {}
        for article in articles:
            symbol = article.get("_symbol", "Other")
            if symbol not in grouped:
                grouped[symbol] = []
            grouped[symbol].append(article)

        # Display each group with a header
        for symbol in grouped:
            # Create section header
            company_name = self._ticker_names.get(symbol, symbol)
            header = QLabel(f"{symbol} - {company_name}")
            header.setObjectName("symbolHeader")
            self.news_layout.addWidget(header)

            # Add articles for this group
            for article in grouped[symbol][:5]:  # Limit to 5 per stock
                card = NewsCard(article, show_symbol_badge=False)
                self.news_layout.addWidget(card)

                image_url = article.get("image")
                if image_url:
                    self._load_thumbnail(image_url, card)

    def _on_news_error(self, error: str) -> None:
        """Handle news fetch error."""
        self.status_label.setText(f"Error: {error}")
        self.status_label.show()
        self.refresh_btn.setEnabled(True)

    def _load_thumbnail(self, url: str, card: NewsCard) -> None:
        """Load thumbnail image asynchronously."""
        self._pending_thumbnails[url] = card
        request = QNetworkRequest(QUrl(url))
        self._network_manager.get(request)

    def _on_thumbnail_loaded(self, reply: QNetworkReply) -> None:
        """Handle thumbnail download."""
        url = reply.url().toString()

        if url in self._pending_thumbnails:
            card = self._pending_thumbnails.pop(url)

            if reply.error() == QNetworkReply.NetworkError.NoError:
                data = reply.readAll()
                pixmap = QPixmap()
                pixmap.loadFromData(data)

                if not pixmap.isNull():
                    scaled = pixmap.scaled(
                        80, 80,
                        Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                        Qt.TransformationMode.SmoothTransformation,
                    )
                    # Crop to square
                    if scaled.width() > 80:
                        x = (scaled.width() - 80) // 2
                        scaled = scaled.copy(x, 0, 80, 80)
                    if scaled.height() > 80:
                        y = (scaled.height() - 80) // 2
                        scaled = scaled.copy(0, y, 80, 80)

                    card.thumbnail.setPixmap(scaled)
                    card.thumbnail.setStyleSheet("""
                        border-radius: 8px;
                    """)

        reply.deleteLater()

    def retranslate_ui(self) -> None:
        """Update UI text after language change."""
        # Update filter combo items
        self.filter_combo.setItemText(0, _("news.my_stocks"))
        self.filter_combo.setItemText(1, _("news.general"))
        self.filter_combo.setItemText(2, _("news.crypto"))
        self.filter_combo.setItemText(3, _("news.forex"))
        self.filter_combo.setItemText(4, _("news.mergers"))

        # Update title based on current selection
        filter_text = self.filter_combo.currentText()
        self.title_label.setText(_("news.title") + " - " + filter_text)

        # Update refresh button
        self.refresh_btn.setText(_("news.refresh"))
