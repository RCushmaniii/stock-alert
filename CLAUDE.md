# StockAlert v3.0 - AI Assistant Guidelines

> **IMPORTANT: DO NOT ASSIGN DEVELOPER WORK TO THE USER!**
> The user is the project manager, NOT a developer. If you need to:
> - Update code (frontend, backend, Vercel, etc.) → DO IT YOURSELF
> - Push to git → DO IT YOURSELF
> - Deploy to Vercel → Push to git, it auto-deploys from `backend/` folder
> - Install a package or tool → ASK the user to install it
>
> NEVER say "copy this code and paste it" or "update this in Vercel dashboard".
> Just make the changes and push them.

> **IMPORTANT: Be a PROACTIVE Product Advisor!**
> Don't just implement what's asked - think like a product designer:
> - **Simplify UX**: If a feature adds complexity users don't need, suggest removing it
> - **"It Just Works"**: Modern apps don't ask users to configure things that should be automatic
> - **Fewer Choices = Better**: Don't expose settings users shouldn't need to think about
> - **Challenge Requirements**: If something seems over-engineered, say so and propose simpler alternatives
> - **Think Like a User**: Would your mom understand this UI? If not, simplify it
>
> Examples of good advice:
> - "Do users really need a Start/Stop button, or should the service just always run?"
> - "This setting adds complexity - can we just pick a sensible default?"
> - "Instead of 3 options, what if we just did the right thing automatically?"

> **IMPORTANT: Read [`docs/LESSONS_LEARNED.md`](docs/LESSONS_LEARNED.md) before making changes!**
> It contains critical information about build processes, common pitfalls, and solutions to problems encountered during development.

## Quick Reference (from Lessons Learned)

### Build Commands
```bash
# Kill running app first (use // for Windows flags in Git Bash)
taskkill //F //IM StockAlert.exe

# Build (use setup_msi.py, NOT cx_Freeze directly)
python setup_msi.py build_exe

# Launch for testing
"./build/exe.win-amd64-3.12/StockAlert.exe" &
```

### Inno Setup Location (for creating installers)
```
%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe
```
**NOT** in Program Files - it's in the user's AppData folder!

### Key Gotchas
- **Config Location**: Stored in `%APPDATA%\StockAlert\config.json` (persists across rebuilds!)
- **Rate Limiter**: Must be a singleton shared across all FinnhubProvider instances
- **Startup Dialogs**: Must show AFTER UI is created, via QTimer.singleShot()
- **API Key Storage**: Keyring fails in frozen exe; uses config.json fallback
- **Translations**: Always update BOTH en.json AND es.json
- **Currency Display**: All prices stored in USD internally; `CurrencyFormatter` handles display conversion
- **Exchange Rate API**: Key embedded in app (`exchange_rate.py`), cached 1 hour

---

## WhatsApp/SMS Backend (Vercel)

### Vercel Project
- **Project URL**: https://vercel.com/rcushmaniii-projects/stockalert-api
- **API Endpoint**: `https://stockalert-api.vercel.app/api/send_whatsapp` (UNDERSCORE, not hyphen!)
- **Source Code**: `backend/api/send_whatsapp.py` (auto-deploys on git push)

### Vercel Deployment (CLI Required)
- The `backend/` folder is NOT auto-deployed via Git
- **To deploy**: `cd backend && vercel --prod`
- Vercel CLI must be installed and authenticated
- Project: `rcushmaniii-projects/stockalert-api`
- Production URL: `https://stockalert-api.vercel.app`

### Twilio WhatsApp Configuration
- **Account SID**: (stored in Vercel environment variables)
- **WhatsApp Number**: (stored in Vercel environment variables)
- **Template SID**: `HX138b713346901520a4a6d48e21ec3e68` (ai_stock_price_alert_02)
- **Template Variables**:
  - `1`: Ticker symbol (e.g., "AAPL")
  - `2`: Current price (e.g., "182.50")
  - `3`: Direction ("above" or "below")
  - `4`: Threshold price (e.g., "180.00")

### IMPORTANT: Templates Required!
WhatsApp Business numbers CANNOT send freeform messages. You MUST use `template_data`, not `message`. Freeform only works if user messaged you in last 24 hours.

### API Request Format
```json
POST /api/send_whatsapp
{
  "phone": "+5213315590572",
  "template_data": {"1": "AAPL", "2": "182.50", "3": "above", "4": "180.00"}
}
```
**Note**: Endpoint is `send_whatsapp` (underscore), NOT `send-whatsapp` (hyphen)!

### Desktop App Integration
- `src/stockalert/core/twilio_service.py` calls the Vercel API
- Does NOT use Twilio SDK directly (avoids bundling credentials in exe)
- Phone numbers are validated via `phone_utils.py` using `phonenumbers` library

### API Key Authentication (Internal)
The WhatsApp backend requires an API key for authentication. This is **completely invisible to users**:
- The API key is **embedded in the app** (XOR-obfuscated in `api_key_manager.py`)
- On startup, `provision_stockalert_api_key()` auto-stores it in Windows Credential Manager
- Users just toggle "Enable WhatsApp" - no key entry required
- The key is set in Vercel as `API_KEY` environment variable
- **DO NOT** expose this key to users or ask them to configure it

### Mexican Phone Numbers
Mexican mobile numbers are special:
- Standard format: `+52` + 10 digits (e.g., `+523315590572`)
- WhatsApp format: `+521` + 10 digits (e.g., `+5213315590572`) - needs the "1" prefix
- The `phonenumbers` library may reject +521 as "too long" - we handle this specially in `phone_utils.py`

---

## Project Overview

StockAlert is a commercial-grade Windows desktop application for real-time stock price monitoring with customizable alerts. It runs in the system tray, monitors stock prices during market hours, and sends Windows toast notifications when price thresholds are breached.

## Architecture

```
src/stockalert/
├── __init__.py           # Package version and exports
├── __main__.py           # Entry point (python -m stockalert)
├── app.py                # Main application orchestrator
├── core/                 # Business logic
│   ├── monitor.py        # Stock price monitoring
│   ├── alert_manager.py  # Notification handling
│   ├── config.py         # Configuration management
│   └── paths.py          # Persistent path management (AppData)
├── api/                  # External API integration
│   ├── base.py           # Abstract provider interface
│   ├── finnhub.py        # Finnhub API client
│   └── rate_limiter.py   # Token bucket rate limiting
├── ui/                   # PyQt6 user interface
│   ├── main_window.py    # Main application window
│   ├── tray_icon.py      # System tray integration
│   ├── dialogs/          # Modal dialogs
│   └── widgets/          # Reusable widgets
├── i18n/                 # Internationalization
│   ├── translator.py     # Translation manager
│   └── locales/          # Language files (en.json, es.json)
└── utils/                # Utilities
    ├── market_hours.py   # Market hours detection
    └── logging_config.py # Logging setup
```

## Code Standards

### Type Hints
- All functions must have complete type annotations
- Use `from __future__ import annotations` in all modules
- Run `mypy src/` to verify - must pass with zero errors

### Docstrings
- All public classes and functions need docstrings
- Use Google-style docstrings:
```python
def fetch_price(symbol: str, timeout: float = 5.0) -> float | None:
    """Fetch current stock price from Finnhub API.

    Args:
        symbol: Stock ticker symbol (e.g., "AAPL")
        timeout: Request timeout in seconds

    Returns:
        Current stock price, or None if unavailable

    Raises:
        RateLimitError: If API rate limit exceeded
    """
```

### Naming Conventions
- Classes: `PascalCase`
- Functions/methods: `snake_case`
- Constants: `UPPER_SNAKE_CASE`
- Private members: `_leading_underscore`
- Translation keys: `category.subcategory.name` (e.g., `alerts.high.title`)

### Error Handling
- Never use bare `except:`
- Log exceptions with `logger.exception()` for stack traces
- Use custom exceptions for domain-specific errors
- Always clean up resources (use context managers)

## Key Components

### Rate Limiter (`api/rate_limiter.py`)
Token bucket algorithm for Finnhub's 60 calls/minute limit:
- Allows bursts up to 10 calls
- Refills at 1 token/second
- Use `await limiter.acquire()` before each API call

### Translator (`i18n/translator.py`)
Simple JSON-based translation system:
- Load with `translator.set_language("es")`
- Get strings with `_("alerts.high.title")` shorthand
- Supports runtime language switching

### Config Manager (`core/config.py`)
JSON configuration with validation:
- Schema validation on load
- Migration support for older configs
- Thread-safe read/write operations

## Common Tasks

### Adding a New Translation String
1. Add to `src/stockalert/i18n/locales/en.json`:
   ```json
   { "category": { "new_key": "English text" } }
   ```
2. Add to `src/stockalert/i18n/locales/es.json`:
   ```json
   { "category": { "new_key": "Spanish text" } }
   ```
3. Use in code: `_("category.new_key")`

### Adding a New Setting
1. Update schema in `core/config.py`
2. Add default value in `DEFAULT_CONFIG`
3. Add UI controls in `ui/dialogs/settings_dialog.py`
4. Add translation keys for labels

### Adding a New API Provider
1. Create `api/new_provider.py` implementing `BaseProvider`
2. Implement required methods: `get_price()`, `validate_symbol()`
3. Add provider option in config schema
4. Register in provider factory

## Testing

### Run Tests
```bash
# All tests
pytest

# With coverage
pytest --cov=src/stockalert --cov-report=html

# Only unit tests
pytest tests/unit/

# Only GUI tests
pytest tests/gui/ -m gui

# Skip slow tests
pytest -m "not slow"
```

### Test Fixtures
Common fixtures in `conftest.py`:
- `mock_finnhub`: Mocked Finnhub client
- `sample_config`: Valid test configuration
- `qtbot`: PyQt6 test helper (from pytest-qt)

### GUI Testing
Use `pytest-qt` for widget testing:
```python
def test_add_ticker(qtbot, main_window):
    qtbot.addWidget(main_window)
    qtbot.mouseClick(main_window.add_button, Qt.LeftButton)
    assert main_window.ticker_dialog.isVisible()
```

## Build & Package

### Development Install
```bash
pip install -e ".[dev]"
pre-commit install
```

### Build Executable
```bash
# Kill any running instance first
taskkill //F //IM StockAlert.exe

# Build with cx_Freeze (via setup_msi.py)
python setup_msi.py build_exe

# Output: build/exe.win-amd64-3.12/StockAlert.exe
```

### Create Installer (Inno Setup)
```bash
# Inno Setup is in AppData, NOT Program Files!
"%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe" installer.iss

# Output: dist/StockAlert_Setup.exe
```

### Linting
```bash
# Check
ruff check src/

# Fix auto-fixable issues
ruff check src/ --fix

# Format
ruff format src/
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `FINNHUB_API_KEY` | Yes | Finnhub API key for stock data (user-provided) |
| `LOG_LEVEL` | No | Logging level (default: INFO) |
| `DEBUG_MODE` | No | Enable debug features |

**Note**: The Finnhub API key is stored in `%APPDATA%\StockAlert\config.json` after user enters it in Settings. No `.env` file is needed for production builds.

## Dependencies

### Runtime
- PyQt6: GUI framework
- finnhub-python: Stock data API
- python-dotenv: Environment variables
- winotify: Windows notifications
- pytz: Timezone handling
- Pillow: Image processing

### Development
- pytest, pytest-qt, pytest-cov: Testing
- ruff: Linting and formatting
- mypy: Type checking
- pre-commit: Git hooks

## Important Notes

1. **Market Hours**: The app only actively monitors during US market hours (9:30 AM - 4:00 PM ET, Mon-Fri, excluding holidays)

2. **Rate Limiting**: Finnhub free tier allows 60 calls/minute. The rate limiter MUST be a singleton shared across all FinnhubProvider instances (see `api/finnhub.py`).

3. **Thread Safety**: UI updates must happen on the main thread. Use Qt signals for cross-thread communication.

4. **Windows Only**: This app uses Windows-specific features (winotify, system tray). It will not run on Linux/macOS.

5. **Bilingual**: All user-facing text must have entries in both `en.json` and `es.json`.

6. **Startup Order**: Never show dialogs before UI is created. Use `QTimer.singleShot()` to delay startup dialogs.

7. **API Key Storage**: Keyring may fail in frozen exe; `api_key_manager.py` has config.json fallback.

8. **See Also**: [`docs/LESSONS_LEARNED.md`](docs/LESSONS_LEARNED.md) for detailed troubleshooting and patterns.

9. **WhatsApp via Vercel**: Desktop app does NOT call Twilio directly. It calls the Vercel backend API which handles Twilio. See "WhatsApp/SMS Backend" section above.

10. **Phone Validation**: Uses `phonenumbers` library in `core/phone_utils.py`. Mexican numbers with +521 prefix need special handling.

11. **WhatsApp API Key**: The backend authentication key is embedded in the app and auto-provisioned. Users never see or manage this key - they just enable WhatsApp alerts and it works.

12. **Vercel Deployment Protection**: If WhatsApp returns 401, check that Vercel Deployment Protection is disabled for the API project, or verify the embedded API key matches the Vercel `API_KEY` environment variable.
