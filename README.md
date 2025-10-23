# 📈 StockAlert

> A professional Windows desktop application for real-time multi-stock price monitoring with intelligent alerting and visual configuration management.

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-Personal-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows%2010%2F11-lightgrey.svg)](https://www.microsoft.com/windows)

## ✨ Features

### Core Functionality
- 📊 **Multi-Stock Monitoring** - Track unlimited stocks simultaneously with individual thresholds
- 🔔 **Smart Notifications** - Windows Toast alerts with clickable actions to view charts
- ⚙️ **Visual Configuration** - User-friendly GUI editor for managing stocks and settings
- 🎯 **Per-Stock Thresholds** - Independent high/low price alerts for each ticker
- ⏱️ **Configurable Intervals** - Customize check frequency and cooldown periods
- 🔄 **Real-Time Data** - Live price feeds from Yahoo Finance API

### Advanced Features
- 🛡️ **Intelligent Cooldowns** - Per-stock alert throttling to prevent notification spam
- ✅ **Symbol Validation** - Real-time ticker verification before adding stocks
- 🎨 **Modern UI** - Clean, professional interface built with FreeSimpleGUI
- 💾 **JSON Configuration** - Human-readable settings file for easy backup/sharing
- 🔌 **Modular Architecture** - Clean separation of concerns following SOLID principles
- 🚨 **Graceful Error Handling** - Automatic retry logic for network failures

## 🚀 Quick Start

### Prerequisites

- **Operating System:** Windows 10 or later
- **Python:** 3.8 or higher
- **Internet Connection:** Required for real-time stock data

### Installation

1. **Clone the repository:**
   ```powershell
   git clone <repository-url>
   cd aa-stock-alert
   ```

2. **Create and activate virtual environment:**
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

3. **Install dependencies:**
   ```powershell
   pip install -r requirements.txt
   ```

4. **Create configuration file:**
   ```powershell
   Copy-Item config.example.json config.json
   ```

### Usage

#### 1. Configure Your Stocks (GUI Method - Recommended)

```powershell
python config_editor.py
```

**Settings Tab:**
- Set check interval (seconds between price checks)
- Configure cooldown period (seconds between alerts)
- Enable/disable notifications

**Tickers Tab:**
- Click **Add Ticker** to add a new stock
- Enter symbol (e.g., AAPL, MSFT, TSLA)
- Click **Validate** to verify the symbol exists
- Set high and low price thresholds
- Click **Save**

#### 2. Run the Stock Monitor

```powershell
python stock_alert.py
```

The application will:
- Load configuration from `config.json`
- Monitor all enabled stocks at your specified interval
- Send Windows Toast notifications when thresholds are breached
- Display real-time price updates in the console
- Continue until you press `Ctrl+C`

## 📊 Example Output

```
🚀 Starting StockAlert - Phase 2
📊 Monitoring 4 stock(s)
⏱️  Check interval: 60s
⏳ Cooldown period: 300s
============================================================

  • AAPL (Apple Inc.)
    High: $190.00 | Low: $180.00
  • MSFT (Microsoft Corp.)
    High: $410.00 | Low: $375.00
  • SPY (SPDR S&P 500 ETF)
    High: $580.00 | Low: $560.00
  • TSLA (Tesla Inc.)
    High: $250.00 | Low: $230.00

============================================================

[2025-10-23 13:03:40] AAPL: $185.50
[2025-10-23 13:03:40] MSFT: $415.25
🔔 [MSFT] Alert sent: MSFT reached $415.25 (threshold: $410.00)
[2025-10-23 13:03:40] SPY: $575.80
[2025-10-23 13:03:40] TSLA: $245.60

## ⚙️ Configuration

### Configuration File (`config.json`)

All settings are stored in `config.json` for easy management:

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

### Global Settings

| Parameter | Description | Default | Range |
|-----------|-------------|---------|-------|
| `check_interval` | Seconds between price checks | `60` | 10-3600 |
| `cooldown` | Seconds between alerts per stock | `300` | 60-86400 |
| `notifications_enabled` | Enable/disable toast notifications | `true` | true/false |

### Per-Stock Settings

| Parameter | Description | Required |
|-----------|-------------|----------|
| `symbol` | Stock ticker (e.g., AAPL, MSFT) | ✅ Yes |
| `name` | Display name | ❌ No (auto-fetched) |
| `high_threshold` | Upper price alert | ✅ Yes |
| `low_threshold` | Lower price alert | ✅ Yes |
| `enabled` | Monitor this stock | ❌ No (default: true) |

## 🧪 Testing

### Quick Alert Test

1. **Find current price** on [Yahoo Finance](https://finance.yahoo.com)
2. **Open config editor:** `python config_editor.py`
3. **Add test ticker** with tight thresholds:
   - Symbol: `AAPL` (or any active stock)
   - High: Current price + $0.50
   - Low: Current price - $0.50
4. **Run monitor:** `python stock_alert.py`
5. **Wait 1-2 check intervals** for alert

### Verify Features

- ✅ **Multi-stock:** Add 3+ tickers, verify all are monitored
- ✅ **Alerts:** Confirm toast notifications appear
- ✅ **Cooldown:** Verify alerts don't spam (check console messages)
- ✅ **Enable/Disable:** Toggle stocks on/off without deleting
- ✅ **Validation:** Try invalid symbol (e.g., "INVALID123")
- ✅ **Persistence:** Restart app, verify config loads correctly

## 🛠️ Troubleshooting

### No notifications appearing?

**Check Windows Settings:**
1. Open Settings → System → Notifications
2. Ensure notifications are enabled
3. Verify "Stock Alert" app has permission

**Verify Configuration:**
- Check `notifications_enabled: true` in `config.json`
- Ensure thresholds are set correctly (high > low)
- Confirm price has actually crossed threshold
- Check cooldown hasn't blocked alert (see console)

### Config editor won't launch?

**Missing FreeSimpleGUI:**
```powershell
pip install FreeSimpleGUI
```

**Alternative:** Use Tkinter version:
```powershell
python config_editor_tkinter.py
```

### "No data available" error?

- ✅ Check internet connection
- ✅ Verify ticker symbol on [Yahoo Finance](https://finance.yahoo.com)
- ✅ Try again (API can be slow)
- ✅ Check if market is open (prices update less frequently after-hours)

### Symbol validation fails?

- Use official ticker symbols (e.g., `AAPL` not `Apple`)
- Try searching on Yahoo Finance first
- Some international stocks may not be available

### App crashes on startup?

**Check config.json syntax:**
```powershell
python -m json.tool config.json
```

**Reset to defaults:**
```powershell
Copy-Item config.example.json config.json -Force
```

## 📋 Project Structure

```
aa-stock-alert/
├── stock_alert.py           # Main monitoring application
├── config_editor.py         # GUI configuration tool (FreeSimpleGUI)
├── config_editor_tkinter.py # Alternative GUI (Tkinter)
├── config.json              # User configuration (gitignored)
├── config.example.json      # Configuration template
├── requirements.txt         # Python dependencies
├── stock_alert.ico          # Notification icon
├── README.md               # This file
├── .gitignore              # Git ignore rules
├── utils/
│   ├── __init__.py         # Package marker
│   └── data_provider.py    # Yahoo Finance API wrapper
└── docs/
    ├── prd.md              # Product requirements
    ├── project-plan.md     # Development roadmap
    └── PHASE2_COMPLETE.md  # Phase 2 completion notes
```

## 🏗️ Architecture

### Design Principles

- **Single Responsibility Principle (SRP)** - Each module has one clear purpose
- **Separation of Concerns (SoC)** - UI, business logic, and data access are isolated
- **DRY (Don't Repeat Yourself)** - Shared logic abstracted into reusable components
- **Graceful Error Handling** - All operations anticipate and handle failures

### Key Components

**`StockAlert`** - Main orchestrator
- Loads configuration from JSON
- Manages multiple `StockMonitor` instances
- Coordinates monitoring loop

**`StockMonitor`** - Per-stock logic
- Tracks individual stock state
- Manages cooldown timers
- Sends notifications

**`DataProvider`** - API abstraction
- Wraps Yahoo Finance API
- Validates ticker symbols
- Handles network errors

**`ConfigEditor`** - GUI interface
- Visual configuration management
- Real-time symbol validation
- JSON persistence

## 🎯 Development Status

### ✅ Phase 1 (Complete)
- Single-stock monitoring
- Basic notifications
- Console output
- Error handling

### ✅ Phase 2 (Complete)
- Multi-stock monitoring
- JSON configuration
- GUI config editor
- Per-stock thresholds
- Modular architecture

### 🔜 Future Enhancements
- Historical price logging
- Email/SMS alerts
- Portfolio tracking
- Percentage-based thresholds
- After-hours monitoring toggle
- Web dashboard

## 📝 Technical Notes

### Logging

**Current:** Console output only (no file logging)
- Price checks displayed in real-time
- Alerts logged to console
- Errors printed with context
- Zero disk space used

**Rationale:** File logging avoided to prevent bloat from frequent price checks. Console output sufficient for debugging and monitoring.

### Data Source

**Yahoo Finance API** via `yfinance` library
- Free, no API key required
- Real-time and historical data
- Supports stocks, ETFs, indices
- Rate limits handled gracefully

### Platform

**Windows 10/11 only**
- Uses `winotify` for native toast notifications
- PowerShell commands in documentation
- Could be adapted for macOS/Linux with different notification libraries

## 🤝 Contributing

This is a personal portfolio project demonstrating:
- Clean code architecture
- SOLID principles
- Modern Python development practices
- User-friendly GUI design
- Real-world API integration

Feedback and suggestions welcome!

## 📄 License

Personal project - All rights reserved.

## 🙏 Acknowledgments

- **yfinance** - Yahoo Finance API wrapper
- **FreeSimpleGUI** - Free, open-source GUI framework
- **winotify** - Windows toast notifications

---

**Built with ❤️ for personal stock monitoring and portfolio demonstration**
