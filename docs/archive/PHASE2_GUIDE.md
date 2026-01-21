# Phase 2 - Quick Start Guide

## 🎉 What's New in Phase 2

- ✅ **Multi-stock monitoring** - Track unlimited tickers simultaneously
- ✅ **JSON configuration** - All settings stored in `config.json`
- ✅ **Visual config editor** - Easy-to-use GUI for managing settings
- ✅ **Per-stock thresholds** - Individual high/low alerts for each ticker
- ✅ **Enable/disable tickers** - Toggle monitoring without deleting
- ✅ **Modular architecture** - Clean separation of concerns

---

## 📁 New Project Structure

```
/aa-stock-alert/
│
├── stock_alert.py           # Main app (Phase 2 - multi-stock)
├── config.json              # Your settings (gitignored)
├── config.example.json      # Template for config.json
├── config_editor.py         # PySimpleGUI editor (requires license)
├── config_editor_tkinter.py # Tkinter editor (FREE, built-in)
├── utils/
│   ├── __init__.py
│   └── data_provider.py     # yfinance wrapper
└── assets/
    └── icon.ico             # Optional notification icon
```

---

## 🚀 Getting Started

### Step 1: Create Your Config File

Copy the example config to create your own:

```powershell
Copy-Item config.example.json config.json
```

### Step 2: Edit Configuration (Choose One Method)

#### Option A: Use the Visual Editor (Recommended)

```powershell
python config_editor_tkinter.py
```

This opens a GUI where you can:
- Add/edit/delete stock tickers
- Set high and low thresholds
- Configure check intervals and cooldowns
- Enable/disable notifications

#### Option B: Edit JSON Manually

Open `config.json` in your editor and modify:

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
    }
  ]
}
```

### Step 3: Run the Stock Alert

```powershell
python stock_alert.py
```

---

## 📊 Configuration Reference

### Global Settings

| Setting | Type | Description | Example |
|---------|------|-------------|---------|
| `check_interval` | integer | Seconds between price checks | `60` (1 minute) |
| `cooldown` | integer | Seconds between repeated alerts | `300` (5 minutes) |
| `notifications_enabled` | boolean | Enable/disable toast notifications | `true` |

### Ticker Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `symbol` | string | ✅ Yes | Stock ticker (e.g., "AAPL") |
| `name` | string | No | Display name for alerts |
| `high_threshold` | float | ✅ Yes | Alert when price ≥ this value |
| `low_threshold` | float | ✅ Yes | Alert when price ≤ this value |
| `enabled` | boolean | No | Enable/disable monitoring (default: true) |

---

## 🎯 Usage Examples

### Example 1: Monitor Multiple Tech Stocks

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
      "name": "Apple",
      "high_threshold": 200.0,
      "low_threshold": 180.0,
      "enabled": true
    },
    {
      "symbol": "MSFT",
      "name": "Microsoft",
      "high_threshold": 420.0,
      "low_threshold": 380.0,
      "enabled": true
    },
    {
      "symbol": "NVDA",
      "name": "NVIDIA",
      "high_threshold": 900.0,
      "low_threshold": 800.0,
      "enabled": true
    }
  ]
}
```

### Example 2: Temporarily Disable a Stock

Set `"enabled": false` to stop monitoring without deleting:

```json
{
  "symbol": "TSLA",
  "name": "Tesla",
  "high_threshold": 250.0,
  "low_threshold": 200.0,
  "enabled": false
}
```

---

## 🔧 Config Editor Features

### Tkinter Editor (`config_editor_tkinter.py`)

**Settings Tab:**
- Adjust check interval
- Set cooldown period
- Toggle notifications on/off

**Tickers Tab:**
- View all tickers in a table
- Add new tickers with validation
- Edit existing tickers
- Delete tickers
- Toggle enabled status

**Symbol Validation:**
- Click "Validate" to check if a ticker symbol exists
- Prevents adding invalid symbols

---

## 🎨 GUI Editors Comparison

| Feature | Tkinter Editor | PySimpleGUI Editor |
|---------|---------------|-------------------|
| **Cost** | ✅ FREE | ⚠️ Requires license |
| **Installation** | ✅ Built-in | ❌ `pip install PySimpleGUI` |
| **Look** | Native Windows | Modern themed |
| **Functionality** | Full featured | Full featured |
| **Recommended** | ✅ Yes | Only if you have license |

---

## 🐛 Troubleshooting

### Config file not found
- Run the app once to auto-create from `config.example.json`
- Or manually copy: `Copy-Item config.example.json config.json`

### No stocks being monitored
- Check that at least one ticker has `"enabled": true`
- Verify your `config.json` syntax is valid JSON

### Validation fails for a symbol
- Ensure the symbol is correct (e.g., "AAPL" not "Apple")
- Check your internet connection
- Try the symbol on finance.yahoo.com

### Notifications not showing
- Set `"notifications_enabled": true` in settings
- Check Windows notification settings
- Ensure cooldown period has passed

---

## 💡 Tips

1. **Test with close thresholds** - Set thresholds near current price to test alerts quickly
2. **Use cooldown wisely** - Prevents alert spam during volatile periods
3. **Disable vs Delete** - Use `enabled: false` to temporarily stop monitoring
4. **Backup your config** - `config.json` contains all your settings
5. **Check interval** - Lower = more responsive, but more API calls

---

## 🔄 Migrating from Phase 1

Phase 1 used hardcoded values in `main()`. Phase 2 uses JSON config.

**Old Phase 1 code:**
```python
alert = StockAlert(
    symbol="AAPL",
    high_threshold=256.52,
    low_threshold=256.40,
    check_interval=60
)
```

**New Phase 2 equivalent:**
Add to `config.json`:
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
      "high_threshold": 256.52,
      "low_threshold": 256.40,
      "enabled": true
    }
  ]
}
```

Then just run: `python stock_alert.py`

---

## 📝 Next Steps

1. ✅ Create your `config.json`
2. ✅ Add your favorite stocks using the GUI editor
3. ✅ Set realistic thresholds based on current prices
4. ✅ Run `python stock_alert.py`
5. ✅ Monitor your stocks!

---

**Need help?** Check the main README.md or review the example config.
