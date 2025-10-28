# 🚀 Quick Start: Building MSI Installer

## TL;DR - Build in 3 Steps

```powershell
# 1. Ensure you're in the project directory
cd aa-stock-alert

# 2. Run the automated build script
.\build_msi.ps1

# 3. Find your MSI in the dist/ folder
```

## What Gets Installed

The MSI installer includes:
- ✅ **StockAlert.exe** - Main monitoring application
- ✅ **StockAlertConfig.exe** - Configuration GUI
- ✅ **All dependencies** - No Python installation required
- ✅ **Start Menu shortcuts** - Easy access from Windows Start
- ✅ **Example config** - Ready to customize

## Required Packages

The build process uses:
- **cx-Freeze 6.15.14** - Creates the MSI installer
- **PyInstaller 6.3.0** - Alternative packaging tool (optional)

These are automatically installed by `build_msi.ps1`.

## Manual Build (If Script Fails)

```powershell
# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Install build dependencies
pip install -r requirements-build.txt

# Build MSI
python setup.py bdist_msi
```

## Output

```
dist/
└── StockAlert-2.0.0-win64.msi    (~40-60 MB)
```

## Customization

Edit `setup.py` to change:
- **Version number** - `APP_VERSION = "2.0.0"`
- **Install location** - `initial_target_dir`
- **Included files** - `include_files` list
- **Console visibility** - `base="Console"` or `base="Win32GUI"`

## Full Documentation

See [docs/BUILD_MSI.md](docs/BUILD_MSI.md) for:
- Detailed troubleshooting
- Advanced customization
- Testing procedures
- Distribution checklist

## Common Issues

### "Module not found" during build
→ Add missing package to `setup.py` → `packages` list

### MSI won't install
→ Uninstall previous version first

### Build files locked
→ Close all running instances of StockAlert

---

**Ready to build?** Run `.\build_msi.ps1` and you're done! 🎉
