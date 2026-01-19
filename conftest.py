"""
Pytest configuration and shared fixtures for StockAlert v3.0.

This file is automatically loaded by pytest and provides:
- Common fixtures for testing
- Mock configurations
- Test utilities
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any, Generator
from unittest.mock import MagicMock, patch

import pytest

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

if TYPE_CHECKING:
    from pytest_mock import MockerFixture


# =============================================================================
# Configuration Fixtures
# =============================================================================


@pytest.fixture
def sample_config() -> dict[str, Any]:
    """Provide a valid sample configuration for testing."""
    return {
        "settings": {
            "check_interval": 60,
            "cooldown": 300,
            "notifications_enabled": True,
            "language": "en",
            "api": {
                "provider": "finnhub",
                "rate_limit": 60,
            },
        },
        "tickers": [
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
                "enabled": True,
            },
            {
                "symbol": "GOOGL",
                "name": "Alphabet Inc.",
                "high_threshold": 180.0,
                "low_threshold": 140.0,
                "enabled": False,
            },
        ],
    }


@pytest.fixture
def minimal_config() -> dict[str, Any]:
    """Provide a minimal valid configuration."""
    return {
        "settings": {
            "check_interval": 60,
            "cooldown": 300,
            "notifications_enabled": True,
        },
        "tickers": [],
    }


@pytest.fixture
def temp_config_file(tmp_path: Path, sample_config: dict[str, Any]) -> Path:
    """Create a temporary config file for testing."""
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(sample_config, indent=2))
    return config_path


# =============================================================================
# API Fixtures
# =============================================================================


@pytest.fixture
def mock_finnhub_client(mocker: MockerFixture) -> MagicMock:
    """Provide a mocked Finnhub client."""
    mock_client = MagicMock()

    # Mock quote response
    mock_client.quote.return_value = {
        "c": 175.50,  # Current price
        "d": 2.25,  # Change
        "dp": 1.30,  # Percent change
        "h": 176.00,  # High
        "l": 173.00,  # Low
        "o": 174.00,  # Open
        "pc": 173.25,  # Previous close
        "t": 1704067200,  # Timestamp
    }

    # Mock symbol lookup
    mock_client.symbol_lookup.return_value = {
        "count": 1,
        "result": [
            {
                "description": "Apple Inc.",
                "displaySymbol": "AAPL",
                "symbol": "AAPL",
                "type": "Common Stock",
            }
        ],
    }

    return mock_client


@pytest.fixture
def mock_finnhub(mocker: MockerFixture, mock_finnhub_client: MagicMock) -> MagicMock:
    """Patch finnhub.Client to return mock client."""
    return mocker.patch("finnhub.Client", return_value=mock_finnhub_client)


# =============================================================================
# Rate Limiter Fixtures
# =============================================================================


@pytest.fixture
def mock_rate_limiter() -> MagicMock:
    """Provide a mocked rate limiter that always allows requests."""
    limiter = MagicMock()
    limiter.acquire.return_value = True
    limiter.tokens = 60
    limiter.max_tokens = 60
    return limiter


# =============================================================================
# Market Hours Fixtures
# =============================================================================


@pytest.fixture
def mock_market_open(mocker: MockerFixture) -> MagicMock:
    """Mock market as currently open."""
    mock = mocker.patch("stockalert.utils.market_hours.MarketHours.is_market_open")
    mock.return_value = True
    return mock


@pytest.fixture
def mock_market_closed(mocker: MockerFixture) -> MagicMock:
    """Mock market as currently closed."""
    mock = mocker.patch("stockalert.utils.market_hours.MarketHours.is_market_open")
    mock.return_value = False
    return mock


# =============================================================================
# Notification Fixtures
# =============================================================================


@pytest.fixture
def mock_notification(mocker: MockerFixture) -> MagicMock:
    """Mock Windows toast notifications."""
    return mocker.patch("winotify.Notification")


# =============================================================================
# Translation Fixtures
# =============================================================================


@pytest.fixture
def en_translations() -> dict[str, Any]:
    """Provide English translation strings for testing."""
    return {
        "app": {
            "name": "StockAlert",
            "version": "3.0.0",
        },
        "alerts": {
            "high": {
                "title": "{symbol} High Alert",
                "message": "{name} reached ${price:.2f} (threshold: ${threshold:.2f})",
            },
            "low": {
                "title": "{symbol} Low Alert",
                "message": "{name} dropped to ${price:.2f} (threshold: ${threshold:.2f})",
            },
        },
        "settings": {
            "title": "Settings",
            "check_interval": "Check Interval (seconds)",
            "cooldown": "Cooldown Period (seconds)",
            "notifications": "Enable Notifications",
            "language": "Language",
        },
        "tickers": {
            "title": "Stock Tickers",
            "add": "Add Ticker",
            "edit": "Edit Ticker",
            "delete": "Delete Ticker",
            "symbol": "Symbol",
            "name": "Name",
            "high_threshold": "High Threshold",
            "low_threshold": "Low Threshold",
            "enabled": "Enabled",
        },
        "dialogs": {
            "save": "Save",
            "cancel": "Cancel",
            "confirm": "Confirm",
            "yes": "Yes",
            "no": "No",
        },
        "errors": {
            "invalid_symbol": "Invalid stock symbol",
            "api_error": "API error: {message}",
            "config_load_error": "Failed to load configuration",
        },
    }


@pytest.fixture
def mock_translator(mocker: MockerFixture, en_translations: dict[str, Any]) -> MagicMock:
    """Mock translator with English strings."""

    def get_string(key: str, **kwargs: Any) -> str:
        parts = key.split(".")
        value = en_translations
        for part in parts:
            if isinstance(value, dict):
                value = value.get(part, key)
            else:
                return key
        if isinstance(value, str):
            return value.format(**kwargs) if kwargs else value
        return key

    mock = mocker.patch("stockalert.i18n.translator._")
    mock.side_effect = get_string
    return mock


# =============================================================================
# Environment Fixtures
# =============================================================================


@pytest.fixture
def mock_env_vars(monkeypatch: pytest.MonkeyPatch) -> dict[str, str]:
    """Set up test environment variables."""
    env_vars = {
        "FINNHUB_API_KEY": "test_api_key_12345",
        "LOG_LEVEL": "DEBUG",
        "DEBUG_MODE": "1",
    }
    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)
    return env_vars


@pytest.fixture
def clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Remove StockAlert-related environment variables."""
    for key in ["FINNHUB_API_KEY", "LOG_LEVEL", "DEBUG_MODE", "LOG_FILE"]:
        monkeypatch.delenv(key, raising=False)


# =============================================================================
# PyQt6 / GUI Fixtures
# =============================================================================


@pytest.fixture
def qapp(qapp_args: list[str]) -> Generator[Any, None, None]:
    """Provide QApplication instance for GUI tests.

    Note: This fixture is provided by pytest-qt when installed.
    This override ensures consistent setup across tests.
    """
    # pytest-qt provides this, but we can customize if needed
    pytest.importorskip("PyQt6")
    from PyQt6.QtWidgets import QApplication

    app = QApplication.instance()
    if app is None:
        app = QApplication(qapp_args or [])
    yield app


@pytest.fixture
def qapp_args() -> list[str]:
    """Arguments for QApplication."""
    return ["--platform", "offscreen"]


# =============================================================================
# Helper Functions
# =============================================================================


def assert_config_valid(config: dict[str, Any]) -> None:
    """Assert that a configuration dictionary is valid."""
    assert "settings" in config
    assert "tickers" in config
    assert isinstance(config["settings"], dict)
    assert isinstance(config["tickers"], list)
    assert "check_interval" in config["settings"]
    assert "cooldown" in config["settings"]
    assert "notifications_enabled" in config["settings"]


def create_mock_ticker(
    symbol: str = "TEST",
    name: str = "Test Corp",
    high: float = 100.0,
    low: float = 50.0,
    enabled: bool = True,
) -> dict[str, Any]:
    """Create a mock ticker configuration."""
    return {
        "symbol": symbol,
        "name": name,
        "high_threshold": high,
        "low_threshold": low,
        "enabled": enabled,
    }
