"""
Internationalization (i18n) for StockAlert.

This package provides:
- translator: Translation manager
- locales/: Language files (JSON)

Supported languages:
- English (en)
- Spanish (es)
"""

from __future__ import annotations

from stockalert.i18n.translator import Translator, _, set_translator

__all__ = [
    "Translator",
    "_",
    "set_translator",
]
