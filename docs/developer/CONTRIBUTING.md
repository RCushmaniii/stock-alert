# Contributing to StockAlert

Thank you for your interest in contributing to StockAlert! This document provides guidelines for contributing to the project.

## Development Setup

### Prerequisites

- Python 3.10 or higher
- Windows 10/11 (required for winotify)
- Git
- A Finnhub API key (free at finnhub.io)

### Setting Up the Development Environment

1. **Clone the repository**
   ```bash
   git clone https://github.com/rcushman/stockalert.git
   cd stockalert
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -e ".[dev]"
   ```

4. **Set up pre-commit hooks**
   ```bash
   pre-commit install
   ```

5. **Configure your API key**
   ```bash
   copy .env.example .env
   # Edit .env and add your FINNHUB_API_KEY
   ```

6. **Run the application**
   ```bash
   python -m stockalert
   ```

## Code Standards

### Style Guide

We use **ruff** for linting and formatting:

```bash
# Check for issues
ruff check src/

# Auto-fix issues
ruff check src/ --fix

# Format code
ruff format src/
```

### Type Hints

All code must have complete type annotations:

```python
def fetch_price(symbol: str, timeout: float = 5.0) -> float | None:
    """Fetch current stock price."""
    ...
```

Run **mypy** to verify:
```bash
mypy src/
```

### Docstrings

Use Google-style docstrings for all public APIs:

```python
def calculate_threshold(
    price: float,
    percentage: float,
    direction: str = "high",
) -> float:
    """Calculate a price threshold based on percentage.

    Args:
        price: Base price for calculation
        percentage: Percentage above/below price
        direction: "high" or "low"

    Returns:
        Calculated threshold price

    Raises:
        ValueError: If direction is not "high" or "low"
    """
```

### Naming Conventions

- **Classes**: `PascalCase`
- **Functions/Methods**: `snake_case`
- **Constants**: `UPPER_SNAKE_CASE`
- **Private members**: `_leading_underscore`
- **Translation keys**: `category.subcategory.name`

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/stockalert --cov-report=html

# Run specific test file
pytest tests/unit/test_config.py

# Run tests matching pattern
pytest -k "test_rate"

# Run only unit tests
pytest tests/unit/

# Run GUI tests (requires display)
pytest tests/gui/ -m gui

# Skip slow tests
pytest -m "not slow"
```

### Writing Tests

1. **Place tests in the appropriate directory:**
   - `tests/unit/` - Unit tests
   - `tests/integration/` - Integration tests
   - `tests/gui/` - GUI tests

2. **Use descriptive test names:**
   ```python
   def test_rate_limiter_blocks_excess_requests():
       ...
   ```

3. **Use fixtures from conftest.py:**
   ```python
   def test_config_loading(temp_config_file, sample_config):
       manager = ConfigManager(temp_config_file)
       assert manager.get("settings.language") == "en"
   ```

4. **Mark special tests:**
   ```python
   @pytest.mark.slow
   def test_full_monitoring_cycle():
       ...

   @pytest.mark.gui
   def test_main_window_rendering():
       ...
   ```

### Coverage Requirements

- Minimum 80% code coverage
- All new features must include tests
- All bug fixes should include regression tests

## Pull Request Process

### Before Submitting

1. **Ensure all tests pass:**
   ```bash
   pytest
   ```

2. **Run linting:**
   ```bash
   ruff check src/
   ```

3. **Run type checking:**
   ```bash
   mypy src/
   ```

4. **Update documentation** if needed

5. **Add translations** for any new user-facing strings

### PR Guidelines

1. **Create a descriptive branch name:**
   - `feature/add-widget-xyz`
   - `fix/rate-limiter-deadlock`
   - `docs/update-api-guide`

2. **Write a clear PR description:**
   - What changes are included
   - Why the changes are needed
   - How to test the changes

3. **Keep PRs focused:**
   - One feature or fix per PR
   - Split large changes into smaller PRs

4. **Respond to review feedback** promptly

## Adding Features

### Adding a New Setting

1. Update the config schema in `core/config.py`
2. Add default value in `DEFAULT_CONFIG`
3. Add UI controls in `ui/dialogs/settings_dialog.py`
4. Add translation keys to both `en.json` and `es.json`
5. Add tests for the new setting

### Adding a New Translation String

1. Add to `src/stockalert/i18n/locales/en.json`:
   ```json
   { "category": { "new_key": "English text" } }
   ```

2. Add to `src/stockalert/i18n/locales/es.json`:
   ```json
   { "category": { "new_key": "Texto en español" } }
   ```

3. Use in code:
   ```python
   from stockalert.i18n import _
   message = _("category.new_key")
   ```

### Adding a New API Provider

1. Create `api/new_provider.py` implementing `BaseProvider`
2. Implement required methods:
   - `get_price(symbol) -> float | None`
   - `validate_symbol(symbol) -> bool`
   - `get_quote(symbol) -> dict | None`
3. Add provider option in config schema
4. Register in provider factory
5. Add tests for the new provider

## Reporting Issues

### Bug Reports

Include:
- StockAlert version
- Windows version
- Steps to reproduce
- Expected vs actual behavior
- Log output if available

### Feature Requests

Include:
- Clear description of the feature
- Use case / why it's needed
- Possible implementation approach (optional)

## Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Focus on the code, not the person
- Help newcomers learn

## Questions?

- GitHub Issues: For bugs and feature requests
- Email: dev@rcsoftware.com

Thank you for contributing to StockAlert!
