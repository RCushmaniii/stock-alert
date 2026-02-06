# AI StockAlert

> AI StockAlert: Stock price monitoring with multi-channel alerts for Windows.

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-Proprietary-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows%2010%2F11-lightgrey.svg)](https://www.microsoft.com/windows)

**[Download for Windows](https://ai-stock-alert-website.netlify.app/)** | **[Live Demo](https://ai-stock-alert-website.netlify.app/)**

## Features

### Core Functionality
- **Multi-Stock Monitoring** - Track unlimited stocks with individual high/low thresholds
- **Multi-Channel Alerts** - Windows notifications, WhatsApp, and email (coming soon)
- **Background Service** - Continues monitoring even after closing the GUI
- **Bilingual Support** - Full English and Spanish interface
- **Professional GUI** - Modern PyQt6 interface with dark/light themes

### Background Service Architecture
- **24/7 Monitoring** - Service runs independently of the GUI
- **Auto-Reload Config** - Changes are picked up without restart
- **Graceful Shutdown** - Clean stop via GUI or command line
- **Market Hours Aware** - Only alerts during trading hours

### Alert Channels
- **Windows Toast Notifications** - Click to view stock chart
- **WhatsApp Alerts** - Via Twilio integration (requires account)
- **Email Alerts** - Coming soon

## Quick Start

### Prerequisites

- **OS:** Windows 10 or later
- **Python:** 3.10 or higher
- **API Key:** Free Finnhub API key ([Get one here](https://finnhub.io/))

### Installation

1. **Clone the repository:**
   ```powershell
   git clone https://github.com/RCushmaniii/stock-alert.git
   cd stock-alert
   ```

2. **Create and activate virtual environment:**
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

3. **Install dependencies:**
   ```powershell
   pip install -e ".[dev]"
   ```

4. **Configure API key:**
   ```powershell
   Copy-Item .env.example .env
   # Edit .env and add your FINNHUB_API_KEY
   ```

### Usage

#### Run the GUI Application
```powershell
cd src
python -m stockalert
```

#### Run the Background Service (Headless)
```powershell
cd src
python -m stockalert.service
```

The GUI provides:
- **Profile Tab** - Set your name, email, and phone for alerts
- **Settings Tab** - Configure check intervals, cooldown, alert channels
- **Tickers Tab** - Add/edit/delete stocks with price thresholds
- **Help Tab** - Tips and documentation

### Background Service

The background service allows monitoring to continue even when the GUI is closed:

1. Open the GUI and configure your tickers and settings
2. Go to **Settings > Background Service**
3. Select "Background Service" mode
4. Click **Start Service**
5. Close the GUI - monitoring continues!

**Command Line Options:**
```powershell
# Run in foreground (for debugging)
python -m stockalert.service --debug

# Install as Windows Service (requires admin)
python -m stockalert.service --install

# Control Windows Service
python -m stockalert.service --start
python -m stockalert.service --stop
python -m stockalert.service --remove
```

## Configuration

### Environment Variables (.env)

```env
FINNHUB_API_KEY=your_api_key_here

# For WhatsApp alerts (optional)
TWILIO_SID=your_twilio_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_WHATSAPP_NUMBER=+14155238886
```

### Configuration File (config.json)

```json
{
  "version": "3.0.0",
  "settings": {
    "check_interval": 60,
    "cooldown": 300,
    "language": "en",
    "service_mode": "background",
    "alerts": {
      "windows_enabled": true,
      "windows_audio": true,
      "whatsapp_enabled": false,
      "email_enabled": false
    }
  },
  "profile": {
    "name": "Your Name",
    "email": "your@email.com",
    "cell": "+15551234567"
  },
  "tickers": [
    {
      "symbol": "AAPL",
      "name": "Apple Inc.",
      "high_threshold": 200.0,
      "low_threshold": 180.0,
      "enabled": true
    }
  ]
}
```

## Architecture

```
src/stockalert/
├── __main__.py           # GUI entry point
├── app.py                # Main application orchestrator
├── service.py            # Background service entry point
├── core/
│   ├── config.py         # Configuration management
│   ├── monitor.py        # Stock price monitoring
│   ├── alert_manager.py  # Multi-channel alert dispatch
│   ├── twilio_service.py # WhatsApp/SMS integration
│   ├── service_controller.py  # Service control from GUI
│   └── windows_service.py     # Windows Service wrapper
├── api/
│   ├── finnhub.py        # Finnhub API client
│   └── rate_limiter.py   # API rate limiting
├── ui/
│   ├── main_window.py    # PyQt6 main window
│   ├── tray_icon.py      # System tray integration
│   └── dialogs/          # Settings, Profile, Ticker dialogs
├── i18n/
│   └── locales/          # en.json, es.json translations
└── utils/
    ├── market_hours.py   # NYSE trading hours
    └── logging_config.py # Structured logging
```

### Key Design Decisions

- **Background Service** - Monitoring decoupled from GUI for 24/7 operation
- **Config File Watching** - Service auto-reloads when settings change
- **Rate Limiting** - Token bucket algorithm respects Finnhub's 60 calls/min
- **Multi-Channel Alerts** - Plugin architecture for alert channels
- **Bilingual** - All UI strings externalized in JSON locale files

## Development

### Running Tests
```powershell
pytest tests/ -v
```

### Code Quality
```powershell
ruff check src/
mypy src/
```

### Building MSI Installer
```powershell
pip install -e ".[build]"
python setup.py bdist_msi
```

## Troubleshooting

### No alerts appearing?
1. Check Windows Settings > Notifications > StockAlert is enabled
2. Verify your Finnhub API key is set in `.env`
3. Confirm thresholds are set (price must cross threshold)
4. Check cooldown period hasn't blocked repeated alerts

### WhatsApp not working?
1. Ensure Twilio credentials are set in `.env`
2. You must first send "join <sandbox-keyword>" to Twilio's WhatsApp number
3. Check your phone number includes country code (e.g., +1)

### Service won't start?
1. Check if another instance is already running
2. View logs in `stockalert_service.log`
3. Try running with `--debug` flag

## Documentation

Detailed documentation is available in the `docs/` folder:

| Folder | Contents |
|--------|----------|
| `docs/guides/` | Build guides, MSI creation, code signing |
| `docs/developer/` | Architecture, API setup, contributing |
| `docs/user/` | User guides (English & Spanish) |
| `docs/legal/` | EULA, privacy policy, licenses |
| `docs/archive/` | Legacy v2.x documentation |

## License

Proprietary - CushLabs.ai. All rights reserved.

## Credits

- **Finnhub** - Stock market data API
- **PyQt6** - Cross-platform GUI framework
- **Twilio** - WhatsApp/SMS messaging
- **winotify** - Windows toast notifications

---

**Built by Robert Cushman | CushLabs.ai**
