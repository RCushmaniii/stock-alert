# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for StockAlert.

Build with: pyinstaller stockalert.spec
"""

import sys
from pathlib import Path

block_cipher = None

# Project paths
project_root = Path(SPECPATH)
src_path = project_root / 'src'
icon_path = project_root / 'stock_alert.ico'

# Data files to include
datas = [
    # Include translation files
    (str(src_path / 'stockalert' / 'i18n' / 'locales'), 'stockalert/i18n/locales'),
    # Include style files
    (str(src_path / 'stockalert' / 'ui' / 'styles'), 'stockalert/ui/styles'),
    # Include icon
    (str(icon_path), '.'),
]

# Hidden imports that PyInstaller might miss
hiddenimports = [
    'stockalert',
    'stockalert.app',
    'stockalert.core',
    'stockalert.core.config',
    'stockalert.core.monitor',
    'stockalert.core.alert_manager',
    'stockalert.core.ipc',
    'stockalert.core.windows_service',
    'stockalert.core.service_controller',
    'stockalert.core.api_key_manager',
    'stockalert.core.twilio_service',
    'stockalert.api',
    'stockalert.api.finnhub',
    'stockalert.ui',
    'stockalert.ui.main_window',
    'stockalert.ui.tray_icon',
    'stockalert.ui.dialogs',
    'stockalert.i18n',
    'stockalert.i18n.translator',
    'stockalert.utils',
    'stockalert.utils.market_hours',
    'win32api',
    'win32con',
    'win32file',
    'win32pipe',
    'win32event',
    'winerror',
    'pywintypes',
    'keyring',
    'keyring.backends',
    'keyring.backends.Windows',
    'phonenumbers',
    'dotenv',
    'finnhub',
]

a = Analysis(
    [str(src_path / 'stockalert' / '__main__.py')],
    pathex=[str(src_path)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['PyQt5', 'tkinter', 'pytest', 'unittest', 'test'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='StockAlert',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # No console window (GUI app)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(icon_path) if icon_path.exists() else None,
)
