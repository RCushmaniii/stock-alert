# StockAlert v3.0 Architecture

## Overview

StockAlert is a Windows desktop application built with Python and PyQt6 for monitoring stock prices and sending Windows toast notifications when price thresholds are breached.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        User Interface                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ MainWindow   │  │  TrayIcon    │  │      Dialogs         │  │
│  │  (PyQt6)     │  │  (PyQt6)     │  │  (Settings/Ticker)   │  │
│  └──────┬───────┘  └──────┬───────┘  └──────────┬───────────┘  │
└─────────┼─────────────────┼─────────────────────┼───────────────┘
          │                 │                     │
          └─────────────────┼─────────────────────┘
                            │
┌───────────────────────────┼─────────────────────────────────────┐
│                    Application Layer                            │
│  ┌────────────────────────┴────────────────────────────────┐   │
│  │                    StockAlertApp                         │   │
│  │              (Main orchestrator - app.py)                │   │
│  └───────────────────────────┬──────────────────────────────┘   │
└──────────────────────────────┼──────────────────────────────────┘
                               │
┌──────────────────────────────┼──────────────────────────────────┐
│                      Core Business Logic                        │
│  ┌─────────────┐  ┌──────────┴───────┐  ┌────────────────────┐ │
│  │ConfigManager│  │  StockMonitor    │  │   AlertManager     │ │
│  │(config.py)  │  │  (monitor.py)    │  │ (alert_manager.py) │ │
│  └─────────────┘  └────────┬─────────┘  └────────────────────┘ │
└────────────────────────────┼────────────────────────────────────┘
                             │
┌────────────────────────────┼────────────────────────────────────┐
│                      API Integration                            │
│  ┌──────────────────┐  ┌───┴───────────┐  ┌──────────────────┐ │
│  │   BaseProvider   │  │FinnhubProvider│  │   RateLimiter    │ │
│  │    (base.py)     │  │ (finnhub.py)  │  │(rate_limiter.py) │ │
│  └──────────────────┘  └───────────────┘  └──────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │   Finnhub API   │
                    │  (External)     │
                    └─────────────────┘
```

## Component Details

### Entry Point (`__main__.py`)

- Parses command line arguments
- Sets up logging
- Creates and runs `StockAlertApp`

### Application Orchestrator (`app.py`)

**Class: `StockAlertApp`**

Coordinates all components:
- Creates Qt application
- Initializes configuration
- Sets up API provider
- Creates UI components
- Manages monitoring lifecycle

### Core Components (`core/`)

#### ConfigManager (`config.py`)
- Thread-safe JSON configuration management
- Schema validation and migration
- Dot-notation access (e.g., `get("settings.language")`)
- Ticker CRUD operations

#### StockMonitor (`monitor.py`)
- Background monitoring thread
- Market hours awareness
- Threshold checking logic
- Cooldown management
- Statistics tracking

#### AlertManager (`alert_manager.py`)
- Windows toast notifications (winotify)
- Localized alert messages
- "View Chart" action buttons

### API Layer (`api/`)

#### BaseProvider (`base.py`)
- Abstract interface for data providers
- Defines `get_price()`, `validate_symbol()`, `get_quote()`

#### FinnhubProvider (`finnhub.py`)
- Finnhub API client wrapper
- Rate-limited requests
- Symbol validation and search

#### RateLimiter (`rate_limiter.py`)
- Token bucket algorithm
- 60 calls/minute limit
- Burst capacity of 10
- Blocking and non-blocking modes

### UI Layer (`ui/`)

#### MainWindow (`main_window.py`)
- PyQt6 QMainWindow
- Tabs: Settings, Tickers
- Responsive design (min 800x600)

#### TrayIcon (`tray_icon.py`)
- QSystemTrayIcon wrapper
- Context menu with monitoring controls
- Double-click to show/hide window

#### Dialogs (`dialogs/`)
- `SettingsWidget`: Global settings form
- `TickerDialog`: Add/edit ticker modal

### Internationalization (`i18n/`)

#### Translator (`translator.py`)
- JSON-based translations
- Dot-notation keys
- Runtime language switching
- Shorthand `_()` function

#### Locales (`locales/`)
- `en.json`: English strings (~80 keys)
- `es.json`: Spanish strings (~80 keys)

### Utilities (`utils/`)

#### MarketHours (`market_hours.py`)
- US market hours (9:30 AM - 4:00 PM ET)
- Holiday calendar (2024-2027)
- `is_market_open()`, `seconds_until_market_open()`

#### Logging (`logging_config.py`)
- Configurable log levels
- Console and file handlers
- Environment variable support

## Data Flow

### Price Check Flow

```
1. StockMonitor._monitoring_loop()
   │
   ├─ Check market hours (MarketHours.is_market_open())
   │  └─ If closed, sleep until market opens
   │
   ├─ For each enabled ticker:
   │  │
   │  ├─ FinnhubProvider.get_price(symbol)
   │  │  │
   │  │  ├─ RateLimiter.acquire() - wait for token
   │  │  │
   │  │  └─ finnhub.Client.quote(symbol)
   │  │
   │  ├─ Update TickerState.last_price
   │  │
   │  └─ StockMonitor._check_thresholds()
   │     │
   │     ├─ Check cooldown period
   │     │
   │     ├─ Compare price to thresholds
   │     │
   │     └─ AlertManager.send_high_alert() or send_low_alert()
   │        │
   │        └─ winotify.Notification.show()
   │
   └─ Sleep for check_interval seconds
```

### Configuration Change Flow

```
1. User modifies settings in UI
   │
   ├─ SettingsWidget._on_save_clicked()
   │  │
   │  └─ ConfigManager.set() → writes config.json
   │
   ├─ MainWindow._on_settings_saved()
   │  │
   │  └─ Callback to StockAlertApp._on_settings_changed()
   │
   └─ StockAlertApp._on_settings_changed()
      │
      ├─ ConfigManager.reload()
      │
      ├─ Translator.set_language() if changed
      │
      └─ StockMonitor.reload_tickers()
```

## Threading Model

```
Main Thread (Qt Event Loop)
├─ PyQt6 UI rendering
├─ User interaction handling
├─ Signal/slot processing
│
└─ Background Thread (Daemon)
   └─ StockMonitor._monitoring_loop()
      ├─ API calls
      ├─ Threshold checking
      └─ Notification triggering (via winotify)
```

**Thread Safety Considerations:**
- ConfigManager uses RLock for thread-safe access
- RateLimiter uses Lock for token management
- UI updates must happen on main thread
- winotify is thread-safe for notifications

## File Structure

```
src/stockalert/
├── __init__.py         # Package version
├── __main__.py         # Entry point
├── app.py              # StockAlertApp orchestrator
│
├── core/
│   ├── __init__.py
│   ├── config.py       # ConfigManager
│   ├── monitor.py      # StockMonitor
│   └── alert_manager.py
│
├── api/
│   ├── __init__.py
│   ├── base.py         # BaseProvider ABC
│   ├── finnhub.py      # FinnhubProvider
│   └── rate_limiter.py # Token bucket
│
├── ui/
│   ├── __init__.py
│   ├── main_window.py  # MainWindow
│   ├── tray_icon.py    # TrayIcon
│   ├── dialogs/
│   │   ├── settings_dialog.py
│   │   └── ticker_dialog.py
│   ├── widgets/
│   └── styles/
│       └── theme.qss   # Qt stylesheet
│
├── i18n/
│   ├── __init__.py
│   ├── translator.py   # Translation manager
│   └── locales/
│       ├── en.json
│       └── es.json
│
└── utils/
    ├── __init__.py
    ├── market_hours.py
    └── logging_config.py
```

## Dependencies

### Runtime
- **PyQt6**: GUI framework
- **finnhub-python**: Stock data API
- **python-dotenv**: Environment variables
- **winotify**: Windows notifications
- **pytz**: Timezone handling
- **Pillow**: Image processing
- **requests**: HTTP client

### Development
- **pytest**: Testing
- **pytest-qt**: Qt testing
- **pytest-cov**: Coverage
- **ruff**: Linting
- **mypy**: Type checking
- **pre-commit**: Git hooks

## Configuration

### config.json Schema

```json
{
  "version": "3.0.0",
  "settings": {
    "check_interval": 60,
    "cooldown": 300,
    "notifications_enabled": true,
    "language": "en",
    "api": {
      "provider": "finnhub",
      "rate_limit": 60
    }
  },
  "tickers": [
    {
      "symbol": "AAPL",
      "name": "Apple Inc.",
      "high_threshold": 200.0,
      "low_threshold": 150.0,
      "enabled": true
    }
  ]
}
```

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `FINNHUB_API_KEY` | Yes | Finnhub API key |
| `LOG_LEVEL` | No | Logging level (default: INFO) |
| `LOG_FILE` | No | Log file path |
| `DEBUG_MODE` | No | Enable debug mode |

## Testing Strategy

### Unit Tests
- Test individual components in isolation
- Mock external dependencies
- High coverage of core logic

### Integration Tests
- Test component interactions
- Verify data flow
- Mock only external APIs

### GUI Tests
- Use pytest-qt for widget testing
- Test user interactions
- Verify responsive behavior
