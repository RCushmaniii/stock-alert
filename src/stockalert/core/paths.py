"""
Path utilities for StockAlert.

Provides consistent paths for application data that persists across
builds, reinstalls, and updates.
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

# Application identifiers
APP_NAME = "StockAlert"
APP_AUTHOR = "RC Software"


def get_app_data_dir() -> Path:
    """Get the application data directory for persistent storage.

    Uses %APPDATA%/StockAlert on Windows (e.g., C:/Users/Name/AppData/Roaming/StockAlert)
    This directory persists across application rebuilds and reinstalls.

    Returns:
        Path to the application data directory (created if needed)
    """
    # Use APPDATA environment variable on Windows
    appdata = os.environ.get("APPDATA")
    if appdata:
        data_dir = Path(appdata) / APP_NAME
    else:
        # Fallback to home directory
        data_dir = Path.home() / ".stockalert"

    # Create directory if it doesn't exist
    data_dir.mkdir(parents=True, exist_ok=True)

    return data_dir


def get_config_path() -> Path:
    """Get the path to the configuration file.

    The config file is stored in AppData so it persists across builds.

    Returns:
        Path to config.json
    """
    return get_app_data_dir() / "config.json"


def get_app_dir() -> Path:
    """Get the application installation directory.

    This is where the executable is located (for external files like .env).

    Returns:
        Path to the application directory
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    else:
        # Development: project root
        return Path(__file__).resolve().parent.parent.parent.parent


def get_bundled_assets_dir() -> Path:
    """Get the directory where bundled assets are located.

    For PyInstaller, this is sys._MEIPASS (where bundled files are extracted).
    For cx_Freeze, this is the exe directory.
    For development, this is the project root.

    Use this for finding bundled files like icons, translations, styles.

    Returns:
        Path to the bundled assets directory
    """
    if getattr(sys, "frozen", False):
        if hasattr(sys, "_MEIPASS"):
            # PyInstaller extracts bundled files to _MEIPASS
            return Path(sys._MEIPASS)
        else:
            # cx_Freeze puts files next to exe
            return Path(sys.executable).parent
    else:
        # Development: project root
        return Path(__file__).resolve().parent.parent.parent.parent


def migrate_config_if_needed() -> bool:
    """Migrate config from old location to AppData if needed.

    Checks for config.json in the app directory and copies it to AppData
    if no config exists there yet. This handles upgrades from older versions.

    Returns:
        True if migration occurred, False otherwise
    """
    app_dir = get_app_dir()
    old_config = app_dir / "config.json"
    new_config = get_config_path()

    # Only migrate if old exists and new doesn't
    if old_config.exists() and not new_config.exists():
        try:
            import shutil
            shutil.copy(old_config, new_config)
            logger.info(f"Migrated config from {old_config} to {new_config}")

            # Optionally rename old config to indicate it's been migrated
            backup_path = old_config.with_suffix(".migrated.json")
            old_config.rename(backup_path)
            logger.info(f"Renamed old config to {backup_path}")

            return True
        except Exception as e:
            logger.error(f"Failed to migrate config: {e}")

    return False
