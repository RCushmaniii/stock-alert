"""
cx_Freeze setup script for creating StockAlert v3.0 MSI installer.

Usage:
    python setup_msi.py build_exe
    python setup_msi.py bdist_msi

This will create an MSI installer in the dist/ directory.
"""

import os
import sys
from pathlib import Path

# Increase recursion limit for cx_Freeze analyzing PyQt6
sys.setrecursionlimit(5000)

# Fix DLL search path for PyQt6 before importing cx_Freeze
if sys.platform == "win32":
    # Point to PyQt6's Qt binaries, not Conda's Qt5
    pyqt6_path = Path(sys.prefix) / "Lib" / "site-packages" / "PyQt6" / "Qt6" / "bin"
    if pyqt6_path.exists():
        os.environ["PATH"] = str(pyqt6_path) + ";" + os.environ.get("PATH", "")
        os.add_dll_directory(str(pyqt6_path))

from cx_Freeze import Executable, setup

# Application metadata
APP_NAME = "AI StockAlert"
APP_VERSION = "4.0.0"
APP_DESCRIPTION = "AI StockAlert: Stock price monitoring with Windows notifications"
APP_AUTHOR = "Robert Cushman"
APP_COMPANY = "CUSHLABS.AI"
APP_COPYRIGHT = "Copyright 2024-2026 CUSHLABS.AI"

# Find package data files
src_dir = Path("src/stockalert")
locale_files = list((src_dir / "i18n/locales").glob("*.json"))
style_files = list((src_dir / "ui/styles").glob("*.qss"))
asset_files = list((src_dir / "ui/assets").glob("*.svg"))

# Find pywin32 DLLs that need to be bundled
venv_site_packages = Path("venv/Lib/site-packages")
pywin32_dlls = []
pywin32_system32 = venv_site_packages / "pywin32_system32"
if pywin32_system32.exists():
    for dll in pywin32_system32.glob("*.dll"):
        pywin32_dlls.append((str(dll), dll.name))
        # Also put in lib/ where extensions (win32api.pyd) live
        pywin32_dlls.append((str(dll), f"lib/{dll.name}"))

# Build include_files list
include_files = [
    # Application icon
    ("stock_alert.ico", "stock_alert.ico"),
    # Configuration example
    ("config.example.json", "config.example.json"),
    # Documentation
    ("docs/user/USER_GUIDE_EN.md", "docs/USER_GUIDE.md"),
    ("docs/user/USER_GUIDE_ES.md", "docs/USER_GUIDE_ES.md"),
    ("docs/legal/EULA.md", "docs/EULA.md"),
    ("docs/legal/PRIVACY_POLICY.md", "docs/PRIVACY_POLICY.md"),
    ("docs/legal/THIRD_PARTY_LICENSES.md", "docs/THIRD_PARTY_LICENSES.md"),
    ("README.md", "README.md"),
    # Startup script
    ("install_startup.ps1", "install_startup.ps1"),
]

# Add pywin32 DLLs
include_files.extend(pywin32_dlls)

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

# Add asset files
for asset_file in asset_files:
    include_files.append(
        (str(asset_file), f"lib/stockalert/ui/assets/{asset_file.name}")
    )

# Dependencies to include
build_exe_options = {
    "packages": [
        # Core packages - let cx_Freeze discover submodules
        "stockalert",
        # PyQt6 must be explicitly included
        "PyQt6",
        "PyQt6.QtCore",
        "PyQt6.QtGui", 
        "PyQt6.QtWidgets",
        # Third-party packages
        "finnhub",
        "dotenv",
        "windows_toasts",
        "requests",
        "PIL",
        "pytz",
        "twilio",
        "keyring",
        "phonenumbers",
        # WinRT for Windows notifications (include all subpackages)
        "winrt",
        # pywin32 for IPC (Named Pipes, Mutex)
        "win32api",
        "win32event",
        "win32file",
        "win32pipe",
    ],
    "includes": [
        # Explicitly include modules that might not be auto-detected
        "PyQt6.QtCore",
        "PyQt6.QtGui",
        "PyQt6.QtWidgets",
        "PyQt6.QtNetwork",
        # WinRT modules for windows-toasts notifications
        "winrt",
        "winrt.windows.foundation",
        "winrt.windows.foundation.collections",
        "winrt.windows.data.xml.dom",
        "winrt.windows.ui.notifications",
        # Win32 modules for keyring and IPC
        "win32timezone",
        "win32api",
        "win32event",
        "win32file",
        "win32pipe",
        "win32cred",
        "win32ctypes",
        "win32ctypes.core",
        "pywintypes",
        "keyring.backends",
        "keyring.backends.Windows",
    ],
    "include_files": include_files,
    "excludes": [
        "test",
        "unittest",
        "pytest",
        "pytest_qt",
        "tkinter",
        "FreeSimpleGUI",
        "yfinance",
        "pystray",
        # Exclude Conda's Qt5 to avoid conflicts
        "PyQt5",
        "pyqt",
    ],
    "optimize": 2,
    "include_msvcr": True,
    # Path to source
    "path": ["src"] + sys.path,
    # Don't zip PyQt6 - it needs DLLs accessible
    "zip_include_packages": ["*"],
    "zip_exclude_packages": ["PyQt6"],
}

# MSI-specific options
bdist_msi_options = {
    "upgrade_code": "{12345678-1234-1234-1234-123456789012}",
    "add_to_path": False,
    "initial_target_dir": r"[ProgramFilesFolder]\StockAlert",
    "install_icon": "stock_alert.ico",
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
        shortcut_dir="DesktopFolder",  # Desktop shortcut
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
