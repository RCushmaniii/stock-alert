"""
GUI tests for the main window.

Uses pytest-qt for PyQt6 widget testing.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest

# Skip all tests in this module if PyQt6 is not available
pytest.importorskip("PyQt6")

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication

if TYPE_CHECKING:
    from pytestqt.qtbot import QtBot


@pytest.fixture
def mock_config_manager() -> MagicMock:
    """Provide a mocked ConfigManager."""
    config = MagicMock()
    config.get_tickers.return_value = [
        {
            "symbol": "AAPL",
            "name": "Apple Inc.",
            "high_threshold": 200.0,
            "low_threshold": 150.0,
            "enabled": True,
        },
        {
            "symbol": "MSFT",
            "name": "Microsoft Corp.",
            "high_threshold": 450.0,
            "low_threshold": 350.0,
            "enabled": False,
        },
    ]
    config.settings = {
        "check_interval": 60,
        "cooldown": 300,
        "notifications_enabled": True,
        "language": "en",
    }
    config.get.side_effect = lambda key, default=None: {
        "settings.check_interval": 60,
        "settings.cooldown": 300,
        "settings.notifications_enabled": True,
        "settings.language": "en",
    }.get(key, default)
    return config


@pytest.fixture
def mock_translator() -> MagicMock:
    """Provide a mocked Translator."""
    translator = MagicMock()
    translator.get.side_effect = lambda key, **kwargs: key
    translator.current_language = "en"
    return translator


@pytest.mark.gui
class TestMainWindow:
    """GUI tests for MainWindow."""

    def test_window_creation(
        self,
        qtbot: QtBot,
        mock_config_manager: MagicMock,
        mock_translator: MagicMock,
    ) -> None:
        """Window should be created with correct properties."""
        from stockalert.ui.main_window import MainWindow

        window = MainWindow(
            config_manager=mock_config_manager,
            translator=mock_translator,
        )
        qtbot.addWidget(window)

        assert window.windowTitle() == "app.name"
        assert window.minimumWidth() == 800
        assert window.minimumHeight() == 600

    def test_tab_widget_exists(
        self,
        qtbot: QtBot,
        mock_config_manager: MagicMock,
        mock_translator: MagicMock,
    ) -> None:
        """Window should have tab widget with correct tabs."""
        from stockalert.ui.main_window import MainWindow

        window = MainWindow(
            config_manager=mock_config_manager,
            translator=mock_translator,
        )
        qtbot.addWidget(window)

        assert window.tabs is not None
        assert window.tabs.count() == 2

    def test_ticker_table_populated(
        self,
        qtbot: QtBot,
        mock_config_manager: MagicMock,
        mock_translator: MagicMock,
    ) -> None:
        """Ticker table should be populated with config data."""
        from stockalert.ui.main_window import MainWindow

        window = MainWindow(
            config_manager=mock_config_manager,
            translator=mock_translator,
        )
        qtbot.addWidget(window)

        assert window.ticker_table.rowCount() == 2
        assert window.ticker_table.item(0, 0).text() == "AAPL"
        assert window.ticker_table.item(1, 0).text() == "MSFT"

    def test_ticker_enabled_display(
        self,
        qtbot: QtBot,
        mock_config_manager: MagicMock,
        mock_translator: MagicMock,
    ) -> None:
        """Enabled status should display correctly."""
        from stockalert.ui.main_window import MainWindow

        window = MainWindow(
            config_manager=mock_config_manager,
            translator=mock_translator,
        )
        qtbot.addWidget(window)

        # AAPL is enabled
        assert window.ticker_table.item(0, 5).text() == "✓"
        # MSFT is disabled
        assert window.ticker_table.item(1, 5).text() == "✗"

    def test_update_ticker_price(
        self,
        qtbot: QtBot,
        mock_config_manager: MagicMock,
        mock_translator: MagicMock,
    ) -> None:
        """Should update displayed price for ticker."""
        from stockalert.ui.main_window import MainWindow

        window = MainWindow(
            config_manager=mock_config_manager,
            translator=mock_translator,
        )
        qtbot.addWidget(window)

        # Initially "--"
        assert window.ticker_table.item(0, 4).text() == "--"

        # Update price
        window.update_ticker_price("AAPL", 175.50)
        assert window.ticker_table.item(0, 4).text() == "$175.50"

    def test_update_ticker_price_none(
        self,
        qtbot: QtBot,
        mock_config_manager: MagicMock,
        mock_translator: MagicMock,
    ) -> None:
        """Should handle None price gracefully."""
        from stockalert.ui.main_window import MainWindow

        window = MainWindow(
            config_manager=mock_config_manager,
            translator=mock_translator,
        )
        qtbot.addWidget(window)

        window.update_ticker_price("AAPL", None)
        assert window.ticker_table.item(0, 4).text() == "--"

    def test_buttons_exist(
        self,
        qtbot: QtBot,
        mock_config_manager: MagicMock,
        mock_translator: MagicMock,
    ) -> None:
        """All ticker management buttons should exist."""
        from stockalert.ui.main_window import MainWindow

        window = MainWindow(
            config_manager=mock_config_manager,
            translator=mock_translator,
        )
        qtbot.addWidget(window)

        assert window.add_button is not None
        assert window.edit_button is not None
        assert window.delete_button is not None
        assert window.toggle_button is not None


@pytest.mark.gui
class TestTickerDialog:
    """GUI tests for TickerDialog."""

    def test_dialog_creation_add_mode(
        self,
        qtbot: QtBot,
        mock_config_manager: MagicMock,
        mock_translator: MagicMock,
    ) -> None:
        """Dialog should open in add mode."""
        from stockalert.ui.dialogs.ticker_dialog import TickerDialog

        dialog = TickerDialog(
            config_manager=mock_config_manager,
            translator=mock_translator,
        )
        qtbot.addWidget(dialog)

        assert dialog.windowTitle() == "tickers.add"
        assert dialog.symbol_edit.isEnabled()
        assert dialog.validate_button.isEnabled()

    def test_dialog_creation_edit_mode(
        self,
        qtbot: QtBot,
        mock_config_manager: MagicMock,
        mock_translator: MagicMock,
    ) -> None:
        """Dialog should open in edit mode with existing data."""
        from stockalert.ui.dialogs.ticker_dialog import TickerDialog

        ticker = {
            "symbol": "AAPL",
            "name": "Apple Inc.",
            "high_threshold": 200.0,
            "low_threshold": 150.0,
            "enabled": True,
        }

        dialog = TickerDialog(
            config_manager=mock_config_manager,
            translator=mock_translator,
            ticker=ticker,
        )
        qtbot.addWidget(dialog)

        assert dialog.windowTitle() == "tickers.edit"
        assert not dialog.symbol_edit.isEnabled()
        assert dialog.symbol_edit.text() == "AAPL"
        assert dialog.name_edit.text() == "Apple Inc."
        assert dialog.high_spin.value() == 200.0
        assert dialog.low_spin.value() == 150.0

    def test_symbol_uppercase(
        self,
        qtbot: QtBot,
        mock_config_manager: MagicMock,
        mock_translator: MagicMock,
    ) -> None:
        """Symbol input should be automatically uppercased."""
        from stockalert.ui.dialogs.ticker_dialog import TickerDialog

        dialog = TickerDialog(
            config_manager=mock_config_manager,
            translator=mock_translator,
        )
        qtbot.addWidget(dialog)

        qtbot.keyClicks(dialog.symbol_edit, "aapl")
        assert dialog.symbol_edit.text() == "AAPL"

    def test_validation_empty_symbol(
        self,
        qtbot: QtBot,
        mock_config_manager: MagicMock,
        mock_translator: MagicMock,
    ) -> None:
        """Validation should fail for empty symbol."""
        from stockalert.ui.dialogs.ticker_dialog import TickerDialog

        dialog = TickerDialog(
            config_manager=mock_config_manager,
            translator=mock_translator,
        )
        qtbot.addWidget(dialog)

        errors = dialog._validate_form()
        assert len(errors) > 0

    def test_validation_high_less_than_low(
        self,
        qtbot: QtBot,
        mock_config_manager: MagicMock,
        mock_translator: MagicMock,
    ) -> None:
        """Validation should fail when high < low."""
        from stockalert.ui.dialogs.ticker_dialog import TickerDialog

        dialog = TickerDialog(
            config_manager=mock_config_manager,
            translator=mock_translator,
        )
        qtbot.addWidget(dialog)

        dialog.symbol_edit.setText("TEST")
        dialog.high_spin.setValue(100.0)
        dialog.low_spin.setValue(200.0)

        errors = dialog._validate_form()
        assert any("high" in e.lower() or "greater" in e.lower() for e in errors)
