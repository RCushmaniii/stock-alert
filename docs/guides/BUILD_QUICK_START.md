# Quick Start: Building the Installer

## TL;DR — Three Commands

```bash
# 1. Kill any running instance
taskkill //F //IM StockAlert.exe

# 2. Build the frozen executable (cx_Freeze)
python setup_msi.py build_exe

# 3. Package into installer (Inno Setup)
"$LOCALAPPDATA/Programs/Inno Setup 6/ISCC.exe" installer.iss
```

**Output:** `dist/StockAlert-<version>-Setup.exe`

## What You Need

- Python 3.12 with project venv activated
- [Inno Setup 6](https://jrsoftware.org/isdownload.php) installed (goes to `%LOCALAPPDATA%\Programs\Inno Setup 6\`)
- All runtime dependencies installed (`pip install -e ".[dev]"`)

## What Gets Built

| Stage | Command | Output |
|-------|---------|--------|
| 1. Frozen exe | `python setup_msi.py build_exe` | `build/exe.win-amd64-3.12/StockAlert.exe` |
| 2. Installer | `ISCC.exe installer.iss` | `dist/StockAlert-<version>-Setup.exe` |

## Common Issues

| Problem | Fix |
|---------|-----|
| "Permission denied" / files locked | Kill running `StockAlert.exe` first |
| Missing module at runtime | Add to `packages` or `includes` in `setup_msi.py` |
| Inno Setup not found | It installs to `%LOCALAPPDATA%`, not `%PROGRAMFILES%` |
| Locale/assets missing at runtime | Check `include_files` in `setup_msi.py` |

## Full Documentation

See [BUILD_INSTALLER.md](BUILD_INSTALLER.md) for the detailed guide.
