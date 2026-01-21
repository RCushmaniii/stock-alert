# 📦 Building MSI Installer for StockAlert

This guide walks you through creating a Windows MSI installer for the StockAlert application.

## 🎯 Overview

The MSI installer packages StockAlert into a professional Windows installation package that:
- ✅ Installs to Program Files
- ✅ Creates Start Menu shortcuts
- ✅ Includes all dependencies
- ✅ Provides standard Windows uninstall
- ✅ Includes both the monitor and configuration GUI

## 📋 Prerequisites

### Required Software
- **Python 3.8+** installed on Windows
- **Virtual environment** set up for the project
- **Internet connection** for downloading build dependencies

### Required Python Packages
The build process requires these packages (automatically installed by build script):
- **cx-Freeze 6.15.14** - Creates MSI installers for Windows
- **PyInstaller 6.3.0** - Alternative executable builder (optional)

## 🚀 Quick Build (Automated)

### Option 1: Using PowerShell Script (Recommended)

```powershell
# Run the automated build script
.\build_msi.ps1
```

This script will:
1. ✅ Activate virtual environment (if needed)
2. ✅ Install build dependencies
3. ✅ Clean previous builds
4. ✅ Build the MSI installer
5. ✅ Display the output location

### Option 2: Manual Build

```powershell
# 1. Activate virtual environment
.\venv\Scripts\Activate.ps1

# 2. Install build dependencies
pip install -r requirements-build.txt

# 3. Clean previous builds (optional)
Remove-Item -Recurse -Force .\build, .\dist -ErrorAction SilentlyContinue

# 4. Build MSI
python setup.py bdist_msi
```

## 📂 Output Location

After a successful build, you'll find:

```
dist/
└── StockAlert-2.0.0-win64.msi    # Your installer (name may vary)
```

The MSI file is typically 40-60 MB and includes:
- StockAlert.exe (main monitoring application)
- StockAlertConfig.exe (configuration GUI)
- All Python dependencies bundled
- Icon and example configuration

## 🔧 Customizing the Build

### Modify Version or Metadata

Edit `setup.py`:

```python
APP_NAME = "StockAlert"
APP_VERSION = "2.0.0"          # Change version here
APP_DESCRIPTION = "..."         # Change description
APP_AUTHOR = "Robert Cushman"   # Change author
```

### Change Installation Directory

Edit `setup.py` → `bdist_msi_options`:

```python
"initial_target_dir": r"[ProgramFilesFolder]\StockAlert",  # Default
# or
"initial_target_dir": r"[LocalAppDataFolder]\StockAlert",  # Per-user install
```

### Add/Remove Files

Edit `setup.py` → `build_exe_options` → `include_files`:

```python
"include_files": [
    ("stock_alert.ico", "stock_alert.ico"),
    ("config.example.json", "config.example.json"),
    ("README.md", "README.md"),
    # Add more files here
],
```

### Hide Console Window

To hide the console for the main app, edit `setup.py`:

```python
Executable(
    script="stock_alert.py",
    base="Win32GUI",  # Changed from "Console"
    # ...
)
```

**Note:** This will hide all console output. Only use for production builds.

## 🧪 Testing the MSI

### 1. Install the MSI

```powershell
# Double-click the MSI file or run:
msiexec /i "dist\StockAlert-2.0.0-win64.msi"
```

### 2. Verify Installation

- ✅ Check Start Menu for "StockAlert" shortcuts
- ✅ Navigate to `C:\Program Files\StockAlert`
- ✅ Run StockAlertConfig.exe to configure
- ✅ Run StockAlert.exe to start monitoring

### 3. Test Uninstall

```powershell
# Via Control Panel
control appwiz.cpl

# Or via Settings
ms-settings:appsfeatures
```

Find "StockAlert" and uninstall.

## 🐛 Troubleshooting

### Build Fails: "Module not found"

**Cause:** Missing dependency in `setup.py`

**Solution:** Add the missing package to `build_exe_options["packages"]`:

```python
"packages": [
    "yfinance",
    "winotify",
    "your_missing_module",  # Add here
],
```

### MSI Install Fails: "Another version is already installed"

**Cause:** Previous version not uninstalled

**Solution:**
1. Uninstall old version via Control Panel
2. Or change `upgrade_code` in `setup.py` (forces new install)

### Application Won't Start After Install

**Cause:** Missing runtime files or dependencies

**Solution:**
1. Check `include_files` in `setup.py`
2. Ensure `stock_alert.ico` and `config.example.json` are included
3. Test on a clean Windows VM

### MSI is Too Large (>100 MB)

**Cause:** Including unnecessary packages

**Solution:** Add exclusions in `setup.py`:

```python
"excludes": [
    "tkinter",
    "test",
    "unittest",
    "pytest",
    "numpy",  # If not needed
    "pandas",  # If not needed
],
```

### "Permission Denied" During Build

**Cause:** Previous build files locked

**Solution:**
```powershell
# Close all running instances
taskkill /F /IM StockAlert.exe /T
taskkill /F /IM StockAlertConfig.exe /T

# Clean and rebuild
Remove-Item -Recurse -Force .\build, .\dist
python setup.py bdist_msi
```

## 📊 Build Options Reference

### cx_Freeze Build Options

| Option | Description | Example |
|--------|-------------|---------|
| `packages` | Python packages to include | `["yfinance", "requests"]` |
| `includes` | Specific modules to include | `["utils.data_provider"]` |
| `excludes` | Packages to exclude | `["tkinter", "test"]` |
| `include_files` | Data files to bundle | `[("icon.ico", "icon.ico")]` |
| `optimize` | Python optimization level (0-2) | `2` |

### MSI Options

| Option | Description | Example |
|--------|-------------|---------|
| `upgrade_code` | GUID for upgrades | `{12345678-...}` |
| `initial_target_dir` | Install location | `[ProgramFilesFolder]\App` |
| `install_icon` | Installer icon | `"app.ico"` |
| `add_to_path` | Add to system PATH | `False` |

## 🔐 Code Signing (Optional)

For production distribution, sign your MSI:

```powershell
# Requires a code signing certificate
signtool sign /f "certificate.pfx" /p "password" /t "http://timestamp.digicert.com" "dist\StockAlert-2.0.0-win64.msi"
```

## 📝 Best Practices

1. **Version Numbering** - Use semantic versioning (MAJOR.MINOR.PATCH)
2. **Testing** - Always test on a clean Windows VM before distribution
3. **Documentation** - Include README.md in the installer
4. **Upgrade Code** - Keep the same `upgrade_code` for all versions to enable upgrades
5. **File Size** - Minimize by excluding unnecessary packages
6. **Icon** - Use a professional icon for better user experience

## 🎯 Distribution Checklist

Before distributing your MSI:

- [ ] Version number updated in `setup.py`
- [ ] Tested on clean Windows 10/11 system
- [ ] Install/uninstall works correctly
- [ ] Start Menu shortcuts created
- [ ] Application runs without errors
- [ ] Configuration GUI works
- [ ] README.md included
- [ ] Icon displays correctly
- [ ] MSI file size is reasonable (<100 MB)
- [ ] (Optional) Code signed for production

## 📚 Additional Resources

- [cx_Freeze Documentation](https://cx-freeze.readthedocs.io/)
- [MSI Installer Guide](https://docs.microsoft.com/en-us/windows/win32/msi/)
- [Windows Code Signing](https://docs.microsoft.com/en-us/windows/win32/seccrypto/cryptography-tools)

---

**Need help?** Check the troubleshooting section or review the `setup.py` configuration.
