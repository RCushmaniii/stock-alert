"""
cx_Freeze setup script for creating StockAlert v3.0 MSI installer.

Usage:
    python setup.py bdist_msi

This will create an MSI installer in the dist/ directory.
"""

import sys
from pathlib import Path

from cx_Freeze import Executable, setup

# Application metadata
APP_NAME = "StockAlert"
APP_VERSION = "3.0.0"
APP_DESCRIPTION = "Commercial-grade stock price monitoring with Windows notifications"
APP_AUTHOR = "Robert Cushman"
APP_COMPANY = "RC Software"
APP_COPYRIGHT = "Copyright 2024-2025 RC Software"

# Find package data files
src_dir = Path("src/stockalert")
locale_files = list((src_dir / "i18n/locales").glob("*.json"))
style_files = list((src_dir / "ui/styles").glob("*.qss"))

# Build include_files list
include_files = [
    # Application icon
    ("stock_alert.ico", "stock_alert.ico"),
    # Configuration example
    ("config.example.json", "config.example.json"),
    # Environment template
    (".env.example", ".env.example"),
    # Documentation
    ("docs/user_guide/en/USER_GUIDE.md", "docs/USER_GUIDE.md"),
    ("docs/user_guide/es/USER_GUIDE.md", "docs/USER_GUIDE_ES.md"),
    ("docs/legal/EULA.md", "docs/EULA.md"),
    ("docs/legal/PRIVACY_POLICY.md", "docs/PRIVACY_POLICY.md"),
    ("docs/legal/THIRD_PARTY_LICENSES.md", "docs/THIRD_PARTY_LICENSES.md"),
    ("README.md", "README.md"),
    # Startup script
    ("install_startup.ps1", "install_startup.ps1"),
]

# Add locale files
for locale_file in locale_files:
    include_files.append(
        (str(locale_file), f"lib/stockalert/i18n/locales/{locale_file.name}")
    )

# Add style files
for style_file in style_files:
    include_files.append(
        (str(style_file), f"lib/stockalert/ui/styles/{style_file.name}")
    )

# Dependencies to include
build_exe_options = {
    "packages": [
        # Core packages
        "stockalert",
        "stockalert.core",
        "stockalert.api",
        "stockalert.ui",
        "stockalert.ui.dialogs",
        "stockalert.ui.widgets",
        "stockalert.i18n",
        "stockalert.utils",
        # Third-party packages
        "PyQt6",
        "PyQt6.QtCore",
        "PyQt6.QtGui",
        "PyQt6.QtWidgets",
        "finnhub",
        "dotenv",
        "winotify",
        "requests",
        "PIL",
        "pytz",
        # Standard library
        "json",
        "datetime",
        "time",
        "os",
        "sys",
        "threading",
        "logging",
        "pathlib",
    ],
    "includes": [
        "stockalert.core.config",
        "stockalert.core.monitor",
        "stockalert.core.alert_manager",
        "stockalert.api.base",
        "stockalert.api.finnhub",
        "stockalert.api.rate_limiter",
        "stockalert.ui.main_window",
        "stockalert.ui.tray_icon",
        "stockalert.ui.dialogs.settings_dialog",
        "stockalert.ui.dialogs.ticker_dialog",
        "stockalert.i18n.translator",
        "stockalert.utils.market_hours",
        "stockalert.utils.logging_config",
    ],
    "include_files": include_files,
    "excludes": [
        "test",
        "unittest",
        "pytest",
        "tkinter",
        "FreeSimpleGUI",
        "yfinance",  # Removed in v3.0
        "pystray",   # Replaced by QSystemTrayIcon
    ],
    "optimize": 2,
    "include_msvcr": True,
    # Path to source
    "path": ["src"] + sys.path,
}

# MSI-specific options
bdist_msi_options = {
    "upgrade_code": "{12345678-1234-1234-1234-123456789012}",
    "add_to_path": False,
    "initial_target_dir": r"[ProgramFilesFolder]\StockAlert",
    "install_icon": "stock_alert.ico",
    # Product metadata
    "data": {
        "Manufacturer": APP_COMPANY,
        "ProductName": APP_NAME,
        "ProductVersion": APP_VERSION,
    },
}

# Define executables
executables = [
    # Main application (GUI, runs in system tray)
    Executable(
        script="src/stockalert/__main__.py",
        base="Win32GUI",
        target_name="StockAlert.exe",
        icon="stock_alert.ico",
        shortcut_name="StockAlert",
        shortcut_dir="ProgramMenuFolder",
        copyright=APP_COPYRIGHT,
    ),
    # Console version for debugging
    Executable(
        script="src/stockalert/__main__.py",
        base="Console",
        target_name="StockAlertConsole.exe",
        icon="stock_alert.ico",
        copyright=APP_COPYRIGHT,
    ),
]

setup(
    name=APP_NAME,
    version=APP_VERSION,
    description=APP_DESCRIPTION,
    author=APP_AUTHOR,
    options={
        "build_exe": build_exe_options,
        "bdist_msi": bdist_msi_options,
    },
    executables=executables,
)
