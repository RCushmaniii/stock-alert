"""
API Key Manager for StockAlert.

Handles secure storage and retrieval of API keys.
Uses Windows Credential Manager when available, falls back to config file.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

import requests

from stockalert.core.paths import get_config_path

logger = logging.getLogger(__name__)

# Credential storage constants
SERVICE_NAME = "StockAlert"
FINNHUB_KEY_NAME = "FinnhubApiKey"
STOCKALERT_KEY_NAME = "StockAlertApiKey"  # For WhatsApp backend authentication

# Flag to track if keyring works
_keyring_available: bool | None = None


def _get_config_path() -> Path:
    """Get the config file path (in AppData for persistence)."""
    return get_config_path()


def _get_from_config() -> str | None:
    """Get API key from config file."""
    try:
        config_path = _get_config_path()
        if config_path.exists():
            with open(config_path, encoding="utf-8") as f:
                config = json.load(f)
            return config.get("api_key")
    except Exception as e:
        logger.debug(f"Failed to get API key from config: {e}")
    return None


def _save_to_config(api_key: str) -> bool:
    """Save API key to config file."""
    try:
        config_path = _get_config_path()
        config = {}
        if config_path.exists():
            with open(config_path, encoding="utf-8") as f:
                config = json.load(f)
        config["api_key"] = api_key
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)
        logger.info("API key stored in config file")
        return True
    except Exception as e:
        logger.error(f"Failed to save API key to config: {e}")
        return False


def _is_keyring_available() -> bool:
    """Check if keyring is available and working."""
    global _keyring_available
    if _keyring_available is not None:
        return _keyring_available

    try:
        import keyring
        keyring.get_password("StockAlert_Test", "test")
        _keyring_available = True
    except Exception:
        _keyring_available = False

    return _keyring_available


def get_api_key() -> str | None:
    """Get the stored Finnhub API key."""
    if _is_keyring_available():
        try:
            import keyring
            key = keyring.get_password(SERVICE_NAME, FINNHUB_KEY_NAME)
            if key:
                return key
        except Exception as e:
            logger.debug(f"Keyring get failed: {e}")

    key = _get_from_config()
    if key:
        return key

    return _get_from_env()


def set_api_key(api_key: str) -> bool:
    """Store the Finnhub API key.

    Always saves to config file for background service access.
    Also tries keyring as additional secure storage.
    """
    # Always save to config file - this is the reliable storage
    # that works in both GUI and background service
    config_saved = _save_to_config(api_key)

    # Also try keyring as additional secure storage
    if _is_keyring_available():
        try:
            import keyring
            keyring.set_password(SERVICE_NAME, FINNHUB_KEY_NAME, api_key)
            logger.info("API key also stored in secure storage")
        except Exception as e:
            logger.debug(f"Keyring set failed (config fallback used): {e}")

    return config_saved


def delete_api_key() -> bool:
    """Delete the stored API key."""
    success = False

    if _is_keyring_available():
        try:
            import keyring
            keyring.delete_password(SERVICE_NAME, FINNHUB_KEY_NAME)
            success = True
        except Exception:
            pass

    try:
        config_path = _get_config_path()
        if config_path.exists():
            with open(config_path, encoding="utf-8") as f:
                config = json.load(f)
            if "api_key" in config:
                del config["api_key"]
                with open(config_path, "w", encoding="utf-8") as f:
                    json.dump(config, f, indent=2)
                success = True
    except Exception:
        pass

    return success


def test_api_key(api_key: str) -> tuple[bool, str]:
    """Test if an API key is valid."""
    if not api_key or not api_key.strip():
        return False, "API key is empty"

    try:
        url = f"https://finnhub.io/api/v1/quote?symbol=AAPL&token={api_key}"
        response = requests.get(url, timeout=10)

        if response.status_code == 200:
            data = response.json()
            if data.get("c", 0) > 0:
                return True, "Connected successfully (Finnhub Free Tier)"
            else:
                return True, "Connected (market may be closed)"
        elif response.status_code == 401:
            return False, "Invalid API key"
        elif response.status_code == 429:
            return True, "Rate limit hit - key is valid"
        else:
            return False, f"Unexpected response: {response.status_code}"

    except requests.exceptions.Timeout:
        return False, "Connection timeout"
    except requests.exceptions.ConnectionError:
        return False, "Cannot connect"
    except Exception as e:
        return False, f"Error: {e!s}"


def _get_from_env() -> str | None:
    """Get API key from .env file."""
    try:
        import os
        from dotenv import load_dotenv
        from stockalert.core.paths import get_app_dir

        possible_paths = [
            Path.cwd() / ".env",
            get_app_dir() / ".env",
        ]

        for env_path in possible_paths:
            if env_path.exists():
                load_dotenv(env_path)
                break

        return os.environ.get("FINNHUB_API_KEY")
    except Exception:
        return None


def has_api_key() -> bool:
    """Check if an API key is configured."""
    key = get_api_key()
    return key is not None and len(key.strip()) > 0


# ============================================================================
# StockAlert API Key (for WhatsApp backend authentication)
# This key is embedded in the app and auto-provisioned on startup.
# Users never see or manage this key - it's part of the app's identity.
# ============================================================================

# Embedded API key (obfuscated) - this is the app's backend authentication
# The key is XOR'd with a simple mask to avoid plain-text extraction
_EMBEDDED_KEY_DATA = b'95\x08\x12\x1c\x08\x17\x02\x15k0\x0e"6b(b\x0c)\x08\x19\x02)(.2\x1b\x1c4 0\x145\x0b\x0c\x1d6 +k9h)'
_KEY_MASK = 0x5A  # XOR mask

def _decode_embedded_key() -> str | None:
    """Decode the embedded API key."""
    if _EMBEDDED_KEY_DATA == b'PLACEHOLDER_KEY_DATA':
        # Key not yet configured - check environment for development
        import os
        return os.environ.get("STOCKALERT_API_KEY")
    try:
        decoded = bytes(b ^ _KEY_MASK for b in _EMBEDDED_KEY_DATA)
        return decoded.decode("utf-8")
    except Exception:
        return None


def provision_stockalert_api_key() -> bool:
    """Auto-provision the StockAlert API key on app startup.

    This is called automatically when the app starts. It checks if the key
    is already stored, and if not, provisions it from the embedded data.
    Users never interact with this - it happens transparently.

    Returns:
        True if key is available (either already stored or just provisioned)
    """
    # Check if already provisioned
    if has_stockalert_api_key():
        logger.debug("StockAlert API key already provisioned")
        return True

    # Get embedded key
    embedded_key = _decode_embedded_key()
    if not embedded_key:
        logger.warning("No embedded StockAlert API key available")
        return False

    # Provision to secure storage
    logger.info("Auto-provisioning StockAlert API key...")
    success = set_stockalert_api_key(embedded_key)
    if success:
        logger.info("StockAlert API key provisioned successfully")
    else:
        logger.error("Failed to provision StockAlert API key")
    return success


def get_stockalert_api_key() -> str | None:
    """Get the stored StockAlert API key (for WhatsApp backend)."""
    # Try keyring first
    if _is_keyring_available():
        try:
            import keyring
            key = keyring.get_password(SERVICE_NAME, STOCKALERT_KEY_NAME)
            if key:
                return key
        except Exception as e:
            logger.debug(f"Keyring get failed for StockAlert key: {e}")

    # Fallback to config file
    try:
        config_path = _get_config_path()
        if config_path.exists():
            with open(config_path, encoding="utf-8") as f:
                config = json.load(f)
            return config.get("stockalert_api_key")
    except Exception as e:
        logger.debug(f"Failed to get StockAlert API key from config: {e}")

    return None


def set_stockalert_api_key(api_key: str) -> bool:
    """Store the StockAlert API key (for WhatsApp backend).

    Always saves to config file for background service access.
    Also tries keyring as additional secure storage.
    """
    # Always save to config file - this is the reliable storage
    # that works in both GUI and background service
    config_saved = False
    try:
        config_path = _get_config_path()
        config = {}
        if config_path.exists():
            with open(config_path, encoding="utf-8") as f:
                config = json.load(f)
        config["stockalert_api_key"] = api_key
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)
        logger.info("StockAlert API key stored in config file")
        config_saved = True
    except Exception as e:
        logger.error(f"Failed to save StockAlert API key to config: {e}")

    # Also try keyring as additional secure storage
    if _is_keyring_available():
        try:
            import keyring
            keyring.set_password(SERVICE_NAME, STOCKALERT_KEY_NAME, api_key)
            logger.info("StockAlert API key also stored in secure storage")
        except Exception as e:
            logger.debug(f"Keyring set failed for StockAlert key (config fallback used): {e}")

    return config_saved


def delete_stockalert_api_key() -> bool:
    """Delete the stored StockAlert API key."""
    success = False

    if _is_keyring_available():
        try:
            import keyring
            keyring.delete_password(SERVICE_NAME, STOCKALERT_KEY_NAME)
            success = True
        except Exception:
            pass

    try:
        config_path = _get_config_path()
        if config_path.exists():
            with open(config_path, encoding="utf-8") as f:
                config = json.load(f)
            if "stockalert_api_key" in config:
                del config["stockalert_api_key"]
                with open(config_path, "w", encoding="utf-8") as f:
                    json.dump(config, f, indent=2)
                success = True
    except Exception:
        pass

    return success


def has_stockalert_api_key() -> bool:
    """Check if a StockAlert API key is configured."""
    key = get_stockalert_api_key()
    return key is not None and len(key.strip()) > 0
