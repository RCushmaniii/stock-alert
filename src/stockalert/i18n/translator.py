"""
Translation manager for StockAlert.

Provides JSON-based internationalization with runtime language switching.
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def _get_locales_dir() -> Path:
    """Get the locales directory, handling both development and frozen exe."""
    if getattr(sys, "frozen", False):
        # Running as frozen exe (cx_Freeze)
        exe_dir = Path(sys.executable).parent
        return exe_dir / "lib" / "stockalert" / "i18n" / "locales"
    else:
        # Running from source
        return Path(__file__).parent / "locales"

# Global translator instance for shorthand access
_translator: Translator | None = None


def set_translator(translator: Translator) -> None:
    """Set the global translator instance.

    Args:
        translator: Translator instance to use globally
    """
    global _translator
    _translator = translator


def _(key: str, **kwargs: Any) -> str:
    """Shorthand function to get translated string.

    Args:
        key: Translation key using dot notation (e.g., "alerts.high.title")
        **kwargs: Format arguments for string interpolation

    Returns:
        Translated string, or key if not found
    """
    if _translator is None:
        return key
    return _translator.get(key, **kwargs)


class Translator:
    """JSON-based translation manager.

    Loads translations from JSON files and provides lookup by dot-notation keys.
    Supports runtime language switching.
    """

    SUPPORTED_LANGUAGES = ["en", "es"]
    DEFAULT_LANGUAGE = "en"

    def __init__(
        self,
        locales_dir: Path | str | None = None,
        default_language: str = "en",
    ) -> None:
        """Initialize the translator.

        Args:
            locales_dir: Directory containing locale JSON files
            default_language: Default language code
        """
        if locales_dir is None:
            locales_dir = _get_locales_dir()
        self.locales_dir = Path(locales_dir)

        self._translations: dict[str, dict[str, Any]] = {}
        self._current_language = default_language
        self._fallback_language = "en"
        self._missing_keys: set[str] = set()  # Track missing keys to avoid duplicate warnings

        self._load_all_languages()
        self.set_language(default_language)

    def _load_all_languages(self) -> None:
        """Load all available language files."""
        for lang in self.SUPPORTED_LANGUAGES:
            self._load_language(lang)

    def _load_language(self, language: str) -> bool:
        """Load translations for a specific language.

        Args:
            language: Language code (e.g., "en", "es")

        Returns:
            True if loaded successfully
        """
        locale_file = self.locales_dir / f"{language}.json"
        if not locale_file.exists():
            logger.warning(f"Locale file not found: {locale_file}")
            return False

        try:
            with open(locale_file, encoding="utf-8") as f:
                self._translations[language] = json.load(f)
            logger.debug(f"Loaded translations for '{language}'")
            return True
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {locale_file}: {e}")
            return False
        except OSError as e:
            logger.error(f"Failed to read {locale_file}: {e}")
            return False

    def set_language(self, language: str) -> bool:
        """Set the current language.

        Args:
            language: Language code (e.g., "en", "es")

        Returns:
            True if language was set successfully
        """
        if language not in self._translations:
            if not self._load_language(language):
                logger.warning(
                    f"Language '{language}' not available, "
                    f"falling back to '{self._fallback_language}'"
                )
                return False

        self._current_language = language
        logger.info(f"Language set to '{language}'")
        return True

    @property
    def current_language(self) -> str:
        """Get current language code."""
        return self._current_language

    @property
    def available_languages(self) -> list[str]:
        """Get list of available language codes."""
        return list(self._translations.keys())

    def get(self, key: str, **kwargs: Any) -> str:
        """Get a translated string.

        Args:
            key: Translation key using dot notation (e.g., "alerts.high.title")
            **kwargs: Format arguments for string interpolation

        Returns:
            Translated string, or key if not found
        """
        # Try current language
        value = self._get_nested(self._current_language, key)

        # Fall back to default language
        if value is None and self._current_language != self._fallback_language:
            value = self._get_nested(self._fallback_language, key)

        if value is None:
            # Log warning only once per missing key to avoid log spam
            if key not in self._missing_keys:
                self._missing_keys.add(key)
                logger.warning(f"Missing translation key: '{key}' (language: {self._current_language})")
            return key

        # Apply string formatting if kwargs provided
        if kwargs:
            try:
                return value.format(**kwargs)
            except KeyError as e:
                logger.warning(f"Missing format key {e} in translation '{key}'")
                return value

        return value

    def _get_nested(self, language: str, key: str) -> str | None:
        """Get a nested value from translations.

        Args:
            language: Language code
            key: Dot-notation key (e.g., "alerts.high.title")

        Returns:
            Value as string, or None if not found
        """
        if language not in self._translations:
            return None

        parts = key.split(".")
        value: Any = self._translations[language]

        for part in parts:
            if isinstance(value, dict):
                value = value.get(part)
                if value is None:
                    return None
            else:
                return None

        return str(value) if value is not None else None

    def get_language_name(self, language: str | None = None) -> str:
        """Get display name for a language.

        Args:
            language: Language code, or None for current language

        Returns:
            Display name (e.g., "English", "Español")
        """
        lang = language or self._current_language
        return self.get(f"languages.{lang}")

    def reload(self) -> None:
        """Reload all translations from disk."""
        self._translations.clear()
        self._missing_keys.clear()
        self._load_all_languages()
        logger.info("Translations reloaded")

    @property
    def missing_keys(self) -> set[str]:
        """Get all translation keys that were requested but not found.

        Returns:
            Set of missing translation keys
        """
        return self._missing_keys.copy()

    def clear_missing_keys(self) -> None:
        """Clear the set of missing translation keys."""
        self._missing_keys.clear()
