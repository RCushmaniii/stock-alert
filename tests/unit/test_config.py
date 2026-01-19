"""
Unit tests for configuration management.

Tests the ConfigManager class.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from stockalert.core.config import ConfigError, ConfigManager


class TestConfigManager:
    """Tests for ConfigManager class."""

    def test_load_existing_config(self, temp_config_file: Path) -> None:
        """Should load an existing config file."""
        manager = ConfigManager(temp_config_file)
        assert manager.get("settings.check_interval") == 60
        assert len(manager.get_tickers()) == 3

    def test_create_default_config(self, tmp_path: Path) -> None:
        """Should create default config if file doesn't exist."""
        config_path = tmp_path / "new_config.json"
        manager = ConfigManager(config_path)

        assert config_path.exists()
        assert manager.get("settings.check_interval") is not None

    def test_get_with_dot_notation(self, temp_config_file: Path) -> None:
        """Should support dot notation for nested keys."""
        manager = ConfigManager(temp_config_file)

        # Top level
        assert manager.get("settings") is not None

        # Nested
        assert manager.get("settings.check_interval") == 60
        assert manager.get("settings.api.provider") == "finnhub"

    def test_get_with_default(self, temp_config_file: Path) -> None:
        """Should return default for missing keys."""
        manager = ConfigManager(temp_config_file)

        assert manager.get("nonexistent") is None
        assert manager.get("nonexistent", "default") == "default"
        assert manager.get("settings.nonexistent", 123) == 123

    def test_set_and_save(self, temp_config_file: Path) -> None:
        """Should set values and persist to file."""
        manager = ConfigManager(temp_config_file)

        manager.set("settings.check_interval", 120)
        assert manager.get("settings.check_interval") == 120

        # Verify saved to file
        with open(temp_config_file) as f:
            saved = json.load(f)
        assert saved["settings"]["check_interval"] == 120

    def test_set_without_save(self, temp_config_file: Path) -> None:
        """Should set value without saving when save=False."""
        manager = ConfigManager(temp_config_file)

        manager.set("settings.check_interval", 999, save=False)
        assert manager.get("settings.check_interval") == 999

        # Verify NOT saved to file
        with open(temp_config_file) as f:
            saved = json.load(f)
        assert saved["settings"]["check_interval"] == 60  # Original value

    def test_get_tickers(self, temp_config_file: Path) -> None:
        """Should return all tickers."""
        manager = ConfigManager(temp_config_file)
        tickers = manager.get_tickers()

        assert len(tickers) == 3
        assert tickers[0]["symbol"] == "AAPL"

    def test_get_enabled_tickers(self, temp_config_file: Path) -> None:
        """Should return only enabled tickers."""
        manager = ConfigManager(temp_config_file)
        enabled = manager.get_enabled_tickers()

        # GOOGL is disabled in sample_config
        assert len(enabled) == 2
        symbols = [t["symbol"] for t in enabled]
        assert "AAPL" in symbols
        assert "MSFT" in symbols
        assert "GOOGL" not in symbols

    def test_add_ticker(self, temp_config_file: Path) -> None:
        """Should add a new ticker."""
        manager = ConfigManager(temp_config_file)

        manager.add_ticker(
            symbol="TSLA",
            name="Tesla Inc.",
            high_threshold=300.0,
            low_threshold=200.0,
        )

        tickers = manager.get_tickers()
        assert len(tickers) == 4
        assert any(t["symbol"] == "TSLA" for t in tickers)

    def test_add_duplicate_ticker_raises(self, temp_config_file: Path) -> None:
        """Should raise error when adding duplicate symbol."""
        manager = ConfigManager(temp_config_file)

        with pytest.raises(ConfigError, match="already exists"):
            manager.add_ticker(
                symbol="AAPL",
                name="Duplicate",
                high_threshold=100.0,
                low_threshold=50.0,
            )

    def test_update_ticker(self, temp_config_file: Path) -> None:
        """Should update an existing ticker."""
        manager = ConfigManager(temp_config_file)

        manager.update_ticker("AAPL", high_threshold=250.0, name="Apple Updated")

        tickers = manager.get_tickers()
        aapl = next(t for t in tickers if t["symbol"] == "AAPL")
        assert aapl["high_threshold"] == 250.0
        assert aapl["name"] == "Apple Updated"

    def test_update_nonexistent_ticker_raises(self, temp_config_file: Path) -> None:
        """Should raise error when updating non-existent ticker."""
        manager = ConfigManager(temp_config_file)

        with pytest.raises(ConfigError, match="not found"):
            manager.update_ticker("FAKE", high_threshold=100.0)

    def test_delete_ticker(self, temp_config_file: Path) -> None:
        """Should delete an existing ticker."""
        manager = ConfigManager(temp_config_file)

        manager.delete_ticker("MSFT")

        tickers = manager.get_tickers()
        assert len(tickers) == 2
        assert not any(t["symbol"] == "MSFT" for t in tickers)

    def test_delete_nonexistent_ticker_raises(self, temp_config_file: Path) -> None:
        """Should raise error when deleting non-existent ticker."""
        manager = ConfigManager(temp_config_file)

        with pytest.raises(ConfigError, match="not found"):
            manager.delete_ticker("FAKE")

    def test_toggle_ticker(self, temp_config_file: Path) -> None:
        """Should toggle ticker enabled state."""
        manager = ConfigManager(temp_config_file)

        # AAPL starts enabled
        assert manager.toggle_ticker("AAPL") is False
        assert manager.toggle_ticker("AAPL") is True

    def test_reload_config(self, temp_config_file: Path) -> None:
        """Should reload config from file."""
        manager = ConfigManager(temp_config_file)

        # Modify file directly
        with open(temp_config_file) as f:
            data = json.load(f)
        data["settings"]["check_interval"] = 999
        with open(temp_config_file, "w") as f:
            json.dump(data, f)

        # Manager still has old value
        assert manager.get("settings.check_interval") == 60

        # After reload, should have new value
        manager.reload()
        assert manager.get("settings.check_interval") == 999

    def test_invalid_json_raises(self, tmp_path: Path) -> None:
        """Should raise error for invalid JSON."""
        config_path = tmp_path / "invalid.json"
        config_path.write_text("{ invalid json }")

        with pytest.raises(ConfigError, match="Invalid JSON"):
            ConfigManager(config_path)

    def test_missing_settings_raises(self, tmp_path: Path) -> None:
        """Should raise error for config missing settings."""
        config_path = tmp_path / "missing.json"
        config_path.write_text('{"tickers": []}')

        with pytest.raises(ConfigError, match="Missing"):
            ConfigManager(config_path)

    def test_settings_property(self, temp_config_file: Path) -> None:
        """Settings property should return copy of settings."""
        manager = ConfigManager(temp_config_file)
        settings = manager.settings

        # Modifying returned dict shouldn't affect manager
        settings["check_interval"] = 999
        assert manager.get("settings.check_interval") == 60

    def test_to_dict(self, temp_config_file: Path) -> None:
        """to_dict should return full config copy."""
        manager = ConfigManager(temp_config_file)
        data = manager.to_dict()

        assert "settings" in data
        assert "tickers" in data
        assert data["settings"]["check_interval"] == 60
