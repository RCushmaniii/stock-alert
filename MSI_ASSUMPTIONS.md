# 📋 MSI Installer - Assumptions & First-Run Behavior

## What Gets Installed

The MSI installer includes:

### Executables
- ✅ **StockAlert.exe** - Main monitoring application (with console window)
- ✅ **StockAlertConfig.exe** - Configuration GUI (no console window)

### Files
- ✅ **config.example.json** - Template with 2 example stocks (AAPL, MSFT)
- ✅ **stock_alert.ico** - Application icon
- ✅ **README.md** - Full documentation

### What's NOT Included
- ❌ **config.json** - User-specific configuration (created on first run)

## First-Run Behavior

### Scenario 1: User Runs StockAlert.exe First (Most Common)

**What Happens:**
1. App checks if `config.json` exists
2. If not found, automatically copies `config.example.json` → `config.json`
3. Displays message: "📋 No config.json found. Creating from config.example.json..."
4. Starts monitoring with example stocks (AAPL, MSFT)

**User Experience:**
- ✅ App works immediately out of the box
- ✅ Users see real stock monitoring with AAPL and MSFT
- ✅ Console shows helpful message about customization
- ✅ Users can later customize via StockAlertConfig.exe

### Scenario 2: User Runs StockAlertConfig.exe First

**What Happens:**
1. Config editor opens
2. User can create their own configuration from scratch
3. Saves to `config.json`
4. User then runs StockAlert.exe to start monitoring

**User Experience:**
- ✅ Full control over initial configuration
- ✅ No example stocks if user doesn't want them
- ✅ More intentional setup process

## Example Stocks Included

The `config.example.json` contains:

```json
{
  "settings": {
    "check_interval": 60,
    "cooldown": 300,
    "notifications_enabled": true
  },
  "tickers": [
    {
      "symbol": "AAPL",
      "name": "Apple Inc.",
      "high_threshold": 190.0,
      "low_threshold": 180.0,
      "enabled": true
    },
    {
      "symbol": "MSFT",
      "name": "Microsoft Corp.",
      "high_threshold": 410.0,
      "low_threshold": 375.0,
      "enabled": true
    }
  ]
}
```

### Important Notes:
- ⚠️ **Thresholds are examples** - Users should update them to current market prices
- ⚠️ **Prices may be outdated** - AAPL/MSFT prices change over time
- 💡 **Users should customize** - These are just starting points

## Installation Location

```
C:\Program Files\StockAlert\
├── StockAlert.exe
├── StockAlertConfig.exe
├── config.example.json
├── stock_alert.ico
├── README.md
└── [Python runtime and dependencies]
```

After first run:
```
C:\Program Files\StockAlert\
├── config.json              ← Created on first run
├── config.example.json
├── StockAlert.exe
├── StockAlertConfig.exe
└── ...
```

## Start Menu Shortcuts

Two shortcuts are created in the Start Menu:

1. **StockAlert** → Runs `StockAlert.exe` (monitoring app)
2. **StockAlert Configuration** → Runs `StockAlertConfig.exe` (config GUI)

## Console Window Behavior

### StockAlert.exe
- **Console window visible** (`base="Console"` in setup.py)
- Shows real-time price updates
- Displays alert messages
- Useful for debugging

**To hide console:** Change `base="Win32GUI"` in `setup.py` line 63

### StockAlertConfig.exe
- **No console window** (`base="Win32GUI"`)
- Pure GUI application
- Professional appearance

## Permissions & Security

### Installation
- Requires **Administrator privileges** (installs to Program Files)
- Standard Windows installer security

### Runtime
- **No admin required** to run the apps
- Reads/writes `config.json` in installation directory
- May require permissions if Program Files is write-protected

**Recommendation:** Consider installing to `[LocalAppDataFolder]` for per-user installs without admin.

## Network Requirements

### First Run
- ✅ **Internet required** - Validates AAPL/MSFT symbols
- ✅ **Fetches real-time prices** from Yahoo Finance API

### Offline Behavior
- ❌ App will fail to fetch prices
- ⚠️ Shows error messages in console
- 🔄 Retries automatically (up to 3 times per stock)

## Upgrade Behavior

### Installing Over Previous Version
- Uses `upgrade_code` in `setup.py` to detect previous installations
- **Preserves `config.json`** - User settings are kept
- Updates executables and dependencies
- Overwrites `config.example.json` with new version

### Uninstall
- Removes all files **except user-created data**
- `config.json` may be preserved (depends on Windows installer behavior)
- Removes Start Menu shortcuts
- Removes registry entries

## Key Assumptions Summary

| Assumption | Reality | Impact |
|------------|---------|--------|
| **Config file exists on first run** | ❌ No, auto-created | ✅ App works immediately |
| **Example stocks included** | ✅ Yes (AAPL, MSFT) | ✅ Users see it working |
| **Thresholds are current** | ⚠️ May be outdated | ⚠️ Users should update |
| **Internet available** | ✅ Required | ❌ Offline won't work |
| **Admin for install** | ✅ Required | Standard for Program Files |
| **Admin for runtime** | ❌ Not required | ✅ Runs as normal user |
| **Console visible** | ✅ Yes (StockAlert.exe) | ✅ Users see output |
| **Config preserved on upgrade** | ✅ Yes | ✅ Settings kept |
| **Auto-starts with Windows** | ❌ No | ✅ User controls when to run |
| **Runs in background** | ❌ No | ⚠️ Console must stay open |
| **Runs 24/7** | ❌ Not recommended | ⚠️ Only useful during market hours |

## Runtime Behavior & Resource Usage

### How It Runs
- **NOT a background service** - Runs as a visible console application
- **NOT auto-start** - Must be manually launched each time
- **Console must stay open** - Closing the window stops monitoring
- **No system tray** - Cannot minimize to tray (current version)

### Resource Usage
- **Memory:** ~50-100 MB (Python runtime + dependencies)
- **CPU:** Minimal - only active during price checks (default: every 60 seconds)
- **Network:** Brief API calls to Yahoo Finance every check interval
- **Disk:** No logging to disk (console output only)

### When to Run
**Recommended:** Only during market hours
- **US Regular Hours:** 9:30 AM - 4:00 PM ET (Mon-Fri)
- **Pre-market:** 4:00 AM - 9:30 AM ET (optional)
- **After-hours:** 4:00 PM - 8:00 PM ET (optional)

**Not recommended:** Nights, weekends, holidays (markets closed, prices don't change)

### Typical Usage Pattern
1. User starts their trading day
2. Launches StockAlert.exe from Start Menu
3. Monitors throughout the day
4. Closes console window when done (or at market close)
5. Repeat next trading day

## Recommendations for Users

### After Installation:

1. **Run StockAlertConfig.exe** to customize stocks
2. **Update thresholds** to current market prices
3. **Add your own stocks** of interest
4. **Test notifications** with tight thresholds
5. **Adjust check interval** based on your needs

### For Best Experience:

- ✅ Keep `config.example.json` as backup
- ✅ Use realistic thresholds (check current prices first)
- ✅ Start with 2-3 stocks, add more later
- ✅ Only run during market hours to save resources
- ✅ Use Task Scheduler for automatic market-hours startup (optional)

---

**Last Updated:** October 2025  
**Version:** 2.0.0
