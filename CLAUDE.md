# StockAlert v3.0 - AI Assistant Guidelines

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
│   └── config.py         # Configuration management
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

### Build MSI
```bash
pip install -e ".[build]"
python setup.py bdist_msi
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
| `FINNHUB_API_KEY` | Yes | Finnhub API key |
| `LOG_LEVEL` | No | Logging level (default: INFO) |
| `DEBUG_MODE` | No | Enable debug features |

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

2. **Rate Limiting**: Finnhub free tier allows 60 calls/minute. With many stocks, check intervals automatically adjust.

3. **Thread Safety**: UI updates must happen on the main thread. Use Qt signals for cross-thread communication.

4. **Windows Only**: This app uses Windows-specific features (winotify, system tray). It will not run on Linux/macOS.

5. **Bilingual**: All user-facing text must have entries in both `en.json` and `es.json`.
