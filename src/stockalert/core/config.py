"""
Configuration management for StockAlert.

Handles loading, saving, and validating JSON configuration files.
Supports schema validation and migration from older config versions.
"""

from __future__ import annotations

import json
import logging
import shutil
import threading
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


# Default configuration structure
DEFAULT_CONFIG: dict[str, Any] = {
    "version": "3.0.0",
    "settings": {
        "check_interval": 60,
        "cooldown": 300,
        "notifications_enabled": True,
        "language": "en",
        "service_mode": "background",  # Default to background service
        "alerts": {
            "windows_enabled": True,
            "windows_audio": True,
            "sms_enabled": False,
            "whatsapp_enabled": False,
            "email_enabled": False,
        },
        "api": {
            "provider": "finnhub",
            "rate_limit": 60,
        },
    },
    "profile": {
        "name": "",
        "email": "",
        "cell": "",
    },
    "tickers": [],
}


class ConfigError(Exception):
    """Configuration-related error."""

    pass


class ConfigManager:
    """Thread-safe configuration manager for JSON config files."""

    def __init__(self, config_path: Path | str) -> None:
        """Initialize configuration manager.

        Args:
            config_path: Path to the JSON configuration file.
        """
        self.config_path = Path(config_path)
        self._config: dict[str, Any] = {}
        self._lock = threading.RLock()

        self._load()

    def _load(self) -> None:
        """Load configuration from file."""
        with self._lock:
            if not self.config_path.exists():
                # Try to copy from example
                example_path = self.config_path.parent / "config.example.json"
                if example_path.exists():
                    shutil.copy(example_path, self.config_path)
                    logger.info(f"Created config from example: {self.config_path}")
                else:
                    # Create default config
                    self._config = DEFAULT_CONFIG.copy()
                    self._save()
                    logger.info(f"Created default config: {self.config_path}")
                    return

            try:
                with open(self.config_path, encoding="utf-8") as f:
                    self._config = json.load(f)
                self._migrate()
                self._validate()
                logger.info(f"Loaded configuration from {self.config_path}")
            except json.JSONDecodeError as e:
                raise ConfigError(f"Invalid JSON in config file: {e}") from e
            except OSError as e:
                raise ConfigError(f"Failed to read config file: {e}") from e

    def _migrate(self) -> None:
        """Migrate older config versions to current format."""
        with self._lock:
            config_version = self._config.get("version", "2.0.0")

            if config_version < "3.0.0":
                # Migrate from v2.x
                logger.info(f"Migrating config from v{config_version} to v3.0.0")

                # Add new fields with defaults
                if "language" not in self._config.get("settings", {}):
                    self._config.setdefault("settings", {})["language"] = "en"

                if "api" not in self._config.get("settings", {}):
                    self._config.setdefault("settings", {})["api"] = {
                        "provider": "finnhub",
                        "rate_limit": 60,
                    }

                self._config["version"] = "3.0.0"
                self._save()

    def _validate(self) -> None:
        """Validate configuration structure."""
        with self._lock:
            # Check required sections
            if "settings" not in self._config:
                raise ConfigError("Missing 'settings' section in config")
            if "tickers" not in self._config:
                raise ConfigError("Missing 'tickers' section in config")

            settings = self._config["settings"]
            required_settings = ["check_interval", "cooldown", "notifications_enabled"]
            for field in required_settings:
                if field not in settings:
                    raise ConfigError(f"Missing required setting: {field}")

            # Validate ticker entries
            for i, ticker in enumerate(self._config["tickers"]):
                required_fields = ["symbol", "high_threshold", "low_threshold"]
                for field in required_fields:
                    if field not in ticker:
                        raise ConfigError(
                            f"Ticker {i} missing required field: {field}"
                        )

    def _save(self) -> None:
        """Save configuration to file."""
        with self._lock:
            try:
                with open(self.config_path, "w", encoding="utf-8") as f:
                    json.dump(self._config, f, indent=2)
                logger.debug(f"Saved configuration to {self.config_path}")
            except OSError as e:
                raise ConfigError(f"Failed to save config file: {e}") from e

    def reload(self) -> None:
        """Reload configuration from file."""
        self._load()

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value using dot notation.

        Args:
            key: Configuration key using dot notation (e.g., "settings.language")
            default: Default value if key doesn't exist

        Returns:
            Configuration value or default
        """
        with self._lock:
            parts = key.split(".")
            value: Any = self._config
            for part in parts:
                if isinstance(value, dict):
                    value = value.get(part)
                    if value is None:
                        return default
                else:
                    return default
            return value

    def set(self, key: str, value: Any, save: bool = True) -> None:
        """Set a configuration value using dot notation.

        Args:
            key: Configuration key using dot notation
            value: Value to set
            save: If True, save to file immediately
        """
        with self._lock:
            parts = key.split(".")
            target = self._config
            for part in parts[:-1]:
                if part not in target:
                    target[part] = {}
                target = target[part]
            target[parts[-1]] = value

            if save:
                self._save()

    def get_tickers(self) -> list[dict[str, Any]]:
        """Get list of configured tickers.

        Returns:
            List of ticker configurations
        """
        with self._lock:
            return self._config.get("tickers", []).copy()

    def get_enabled_tickers(self) -> list[dict[str, Any]]:
        """Get list of enabled tickers.

        Returns:
            List of enabled ticker configurations
        """
        with self._lock:
            return [t for t in self.get_tickers() if t.get("enabled", True)]

    def add_ticker(
        self,
        symbol: str,
        name: str,
        high_threshold: float,
        low_threshold: float,
        enabled: bool = True,
    ) -> None:
        """Add a new ticker to configuration.

        Args:
            symbol: Stock ticker symbol
            name: Display name
            high_threshold: High price threshold
            low_threshold: Low price threshold
            enabled: Whether monitoring is enabled

        Raises:
            ConfigError: If ticker already exists
        """
        with self._lock:
            symbol = symbol.upper()
            if any(t["symbol"] == symbol for t in self._config["tickers"]):
                raise ConfigError(f"Ticker {symbol} already exists")

            self._config["tickers"].append(
                {
                    "symbol": symbol,
                    "name": name,
                    "high_threshold": high_threshold,
                    "low_threshold": low_threshold,
                    "enabled": enabled,
                }
            )
            self._save()

    def update_ticker(self, symbol: str, **kwargs: Any) -> None:
        """Update an existing ticker.

        Args:
            symbol: Stock ticker symbol to update
            **kwargs: Fields to update

        Raises:
            ConfigError: If ticker doesn't exist
        """
        with self._lock:
            symbol = symbol.upper()
            for ticker in self._config["tickers"]:
                if ticker["symbol"] == symbol:
                    ticker.update(kwargs)
                    self._save()
                    return
            raise ConfigError(f"Ticker {symbol} not found")

    def delete_ticker(self, symbol: str) -> None:
        """Delete a ticker from configuration.

        Args:
            symbol: Stock ticker symbol to delete

        Raises:
            ConfigError: If ticker doesn't exist
        """
        with self._lock:
            symbol = symbol.upper()
            original_length = len(self._config["tickers"])
            self._config["tickers"] = [
                t for t in self._config["tickers"] if t["symbol"] != symbol
            ]
            if len(self._config["tickers"]) == original_length:
                raise ConfigError(f"Ticker {symbol} not found")
            self._save()

    def toggle_ticker(self, symbol: str) -> bool:
        """Toggle a ticker's enabled state.

        Args:
            symbol: Stock ticker symbol to toggle

        Returns:
            New enabled state

        Raises:
            ConfigError: If ticker doesn't exist
        """
        with self._lock:
            symbol = symbol.upper()
            for ticker in self._config["tickers"]:
                if ticker["symbol"] == symbol:
                    ticker["enabled"] = not ticker.get("enabled", True)
                    self._save()
                    return ticker["enabled"]
            raise ConfigError(f"Ticker {symbol} not found")

    @property
    def settings(self) -> dict[str, Any]:
        """Get settings section."""
        with self._lock:
            return self._config.get("settings", {}).copy()

    def to_dict(self) -> dict[str, Any]:
        """Get full configuration as dictionary."""
        with self._lock:
            return self._config.copy()
