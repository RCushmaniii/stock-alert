# Building the StockAlert Installer

The installer is built in two stages: first cx_Freeze bundles the Python app into a standalone `.exe`, then Inno Setup wraps that into a professional Windows installer.

## Prerequisites

- **Python 3.12** with project virtual environment activated
- **Inno Setup 6** — installs to `%LOCALAPPDATA%\Programs\Inno Setup 6\` (NOT Program Files)
- All runtime dependencies installed (`pip install -e ".[dev]"`)

## Stage 1: Build the Frozen Executable (cx_Freeze)

```bash
# Kill any running instance first
taskkill //F //IM StockAlert.exe

# Build
python setup_msi.py build_exe
```

**Output:** `build/exe.win-amd64-3.12/StockAlert.exe`

### What cx_Freeze Does

`setup_msi.py` uses cx_Freeze to freeze the Python application into a standalone directory containing:

- **StockAlert.exe** — the main application (`Win32GUI` base, no console window)
- **Python runtime** — embedded Python 3.12 interpreter
- **All dependencies** — PyQt6, finnhub, winotify/WinRT, pywin32, keyring, phonenumbers, twilio, Pillow, pytz, etc.
- **Bundled assets:**
  - Locale files (`en.json`, `es.json`) → `lib/stockalert/i18n/locales/`
  - QSS stylesheets → `lib/stockalert/ui/styles/`
  - SVG assets → `lib/stockalert/ui/assets/`
  - `stock_alert.ico`, `stock_trend.svg`
  - `config.example.json`
  - User docs, EULA, privacy policy, third-party licenses
  - `install_startup.ps1`
  - pywin32 DLLs (copied to both root and `lib/` for compatibility)

### Key Configuration in `setup_msi.py`

| Section | Purpose |
|---------|---------|
| `APP_VERSION` | Version string — update this for each release |
| `packages` | Top-level packages for cx_Freeze to bundle |
| `includes` | Specific modules that aren't auto-detected (WinRT, win32 modules, keyring backends) |
| `excludes` | Dev/test packages to leave out (pytest, tkinter, PyQt5) |
| `include_files` | Extra files copied into the build (icons, locales, docs, pywin32 DLLs) |
| `zip_exclude_packages` | Packages that must NOT be zipped (PyQt6 needs DLLs accessible, pytz needs data files) |

### Adding a New Dependency

If the frozen app crashes with a missing module:

1. Add the package name to `packages` (for top-level packages) or `includes` (for specific modules)
2. If the package has data files that aren't `.py`, add them to `include_files`
3. If the package has DLLs, they may need to be in `zip_exclude_packages`

## Stage 2: Create the Installer (Inno Setup)

```bash
"$LOCALAPPDATA/Programs/Inno Setup 6/ISCC.exe" installer.iss
```

**Output:** `dist/StockAlert-<version>-Setup.exe`

### What Inno Setup Does

`installer.iss` takes the entire `build/exe.win-amd64-3.12/` directory and packages it into a single `.exe` installer with:

- **LZMA2 ultra compression** — keeps the installer small
- **No admin required** — `PrivilegesRequired=lowest` (user can elevate if they want Program Files)
- **English and Spanish** install language support
- **User-selectable options:**
  - Desktop shortcut (default: on)
  - Start Menu shortcut (default: on)
  - Auto-start with Windows (default: on) — uses startup folder shortcut with `--tray` flag
- **Post-install:** option to launch the app immediately
- **Uninstall:** cleans up config, logs, and startup shortcuts (both current and legacy names)

### Key Configuration in `installer.iss`

| Setting | Purpose |
|---------|---------|
| `MyAppVersion` | Must match `APP_VERSION` in `setup_msi.py` |
| `AppId` | Unique GUID — do NOT change after first release (used for upgrades) |
| `DefaultDirName` | Install location (`{autopf}\AI StockAlert`) |
| `OutputBaseFilename` | Installer filename pattern |
| `PrivilegesRequired` | `lowest` = no admin needed |

### Installer Tasks Breakdown

| Task | What It Creates |
|------|----------------|
| Desktop shortcut | `{autodesktop}\AI StockAlert.lnk` → `StockAlert.exe` |
| Start Menu | `{group}\AI StockAlert.lnk` → `StockAlert.exe` (always created) |
| Auto-start | `{userstartup}\AI StockAlert.lnk` → `StockAlert.exe --tray` |

## Full Build Pipeline

```bash
# 1. Kill running app
taskkill //F //IM StockAlert.exe

# 2. Build frozen exe
python setup_msi.py build_exe

# 3. (Optional) Test the frozen exe before packaging
"./build/exe.win-amd64-3.12/StockAlert.exe" &

# 4. Package into installer
"$LOCALAPPDATA/Programs/Inno Setup 6/ISCC.exe" installer.iss

# Output: dist/StockAlert-<version>-Setup.exe
```

## Version Bumping

When releasing a new version, update the version string in **both** files:

1. `setup_msi.py` → `APP_VERSION = "x.y.z"`
2. `installer.iss` → `#define MyAppVersion "x.y.z"`

## Troubleshooting

### "Permission denied" or files locked during build

The previous `StockAlert.exe` is still running. Kill it first:

```bash
taskkill //F //IM StockAlert.exe
```

### Missing module at runtime (frozen exe crashes)

Add the module to `setup_msi.py`:
- Top-level package → `packages` list
- Specific submodule → `includes` list
- Data files → `include_files` list

### pywin32 modules fail in frozen build

pywin32 requires `pywintypes312.dll` to be pre-loaded. The build already handles this by copying the DLL to both root and `lib/` directories, and `ipc.py` pre-loads it with `ctypes.WinDLL()` before importing any win32 modules.

### Locale files not found at runtime

Locale JSON files must be at `lib/stockalert/i18n/locales/` in the build output. Check the `include_files` section of `setup_msi.py` — the locale loop should be copying them there.

### Inno Setup not found

Inno Setup installs to `%LOCALAPPDATA%\Programs\Inno Setup 6\`, **not** Program Files. Verify it's there:

```bash
ls "$LOCALAPPDATA/Programs/Inno Setup 6/ISCC.exe"
```

### Installer is too large

Check `excludes` in `setup_msi.py` — make sure test frameworks, tkinter, and other unnecessary packages are excluded.

## File Reference

| File | Purpose |
|------|---------|
| `setup_msi.py` | cx_Freeze configuration — builds the frozen exe |
| `installer.iss` | Inno Setup script — creates the installer |
| `stock_alert.ico` | Application icon (embedded in exe and installer) |
| `install_startup.ps1` | PowerShell script for auto-start setup (bundled in installer) |
| `config.example.json` | Example configuration (bundled in installer) |

## Note on `setup_msi.py` Naming

Despite the filename, the primary use is `python setup_msi.py build_exe` (cx_Freeze frozen build). The file also contains `bdist_msi` options for building a raw MSI, but the actual distribution installer is created by Inno Setup — not the cx_Freeze MSI builder.
