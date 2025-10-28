"""
cx_Freeze setup script for creating StockAlert MSI installer.

Usage:
    python setup.py bdist_msi

This will create an MSI installer in the dist/ directory.
"""

import sys
from cx_Freeze import setup, Executable

# Application metadata
APP_NAME = "StockAlert"
APP_VERSION = "2.1.0"
APP_DESCRIPTION = "Background stock monitoring with automatic market hours detection"
APP_AUTHOR = "Robert Cushman"
APP_COMPANY = "RC Software"

# Dependencies to include
build_exe_options = {
    "packages": [
        "yfinance",
        "winotify",
        "requests",
        "PIL",
        "FreeSimpleGUI",
        "json",
        "datetime",
        "time",
        "os",
        "sys",
        "pytz",
        "pystray",
        "threading",
    ],
    "includes": [
        "utils.data_provider",
        "utils.market_hours",
    ],
    "include_files": [
        ("stock_alert.ico", "stock_alert.ico"),
        ("config.example.json", "config.example.json"),
        ("README.txt", "README.txt"),
        ("USER_GUIDE.md", "USER_GUIDE.md"),
        ("README.md", "README.md"),
        ("install_startup.ps1", "install_startup.ps1"),
    ],
    "excludes": [
        "test",
        "unittest",
        "pytest",
    ],
    "optimize": 2,
}

# MSI-specific options
bdist_msi_options = {
    "upgrade_code": "{12345678-1234-1234-1234-123456789012}",  # Generate unique GUID
    "add_to_path": False,
    "initial_target_dir": r"[ProgramFilesFolder]\StockAlert",
    "install_icon": "stock_alert.ico",
}

# Define executables
executables = [
    Executable(
        script="stock_alert_tray.py",
        base="Win32GUI",  # Background tray app - no console window
        target_name="StockAlert.exe",
        icon="stock_alert.ico",
        shortcut_name="StockAlert",
        shortcut_dir="ProgramMenuFolder",
    ),
    Executable(
        script="config_editor.py",
        base="Win32GUI",  # GUI application - no console window
        target_name="StockAlertConfig.exe",
        icon="stock_alert.ico",
        shortcut_name="StockAlert Configuration",
        shortcut_dir="ProgramMenuFolder",
    ),
    Executable(
        script="stock_alert.py",
        base="Console",  # Console version (for debugging/advanced users)
        target_name="StockAlertConsole.exe",
        icon="stock_alert.ico",
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
