# StockAlert - Lessons Learned & Technical Notes

This document captures important discoveries, gotchas, and solutions found during development. **Read this before making changes** to avoid repeating past mistakes.

---

## Table of Contents

1. [Build & Packaging](#build--packaging)
2. [API & Rate Limiting](#api--rate-limiting)
3. [Windows-Specific Issues](#windows-specific-issues)
4. [PyQt6 UI Patterns](#pyqt6-ui-patterns)
5. [Configuration & Storage](#configuration--storage)
6. [Internationalization (i18n)](#internationalization-i18n)
7. [Testing & Demos](#testing--demos)
8. [Common Mistakes to Avoid](#common-mistakes-to-avoid)
9. [WhatsApp Backend & API Keys](#whatsapp-backend--api-keys)

---

## Build & Packaging

### Inno Setup Location

**CRITICAL**: Inno Setup is installed in the user's **personal AppData folder**, NOT in Program Files.

```
Location: %LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe
Example:  C:\Users\Robert Cushman\AppData\Local\Programs\Inno Setup 6\ISCC.exe
```

Do NOT look for it in:
- `C:\Program Files (x86)\Inno Setup 6\`
- `C:\Program Files\Inno Setup 6\`

### Build Commands

**Correct way to build:**
```bash
cd "C:\Users\Robert Cushman\.vscode\Projects\ai-stock-alert"
python setup_msi.py build_exe
```

**Wrong way (will fail):**
```bash
python -m cx_Freeze build_exe  # Error: 'executables' must be a list
```

### Killing Processes Before Rebuild

If the build fails with "build_exe directory cannot be cleaned", the app is still running.

**Use Windows-style flags in Git Bash:**
```bash
taskkill //F //IM StockAlert.exe
```

**NOT Unix-style flags:**
```bash
taskkill /f /im StockAlert.exe  # May not work in Git Bash
```

### Build Output Location

```
C:\Users\Robert Cushman\.vscode\Projects\ai-stock-alert\build\exe.win-amd64-3.12\
├── StockAlert.exe           # Main executable
├── lib\                     # Python libraries
│   └── stockalert\
│       └── i18n\locales\    # Translation files (en.json, es.json)
├── config.example.json      # Example configuration
└── stock_alert.ico          # Application icon
```

### Iteration Workflow

During development iterations, **do NOT create installers** - just rebuild and launch:

```bash
taskkill //F //IM StockAlert.exe
python setup_msi.py build_exe
"./build/exe.win-amd64-3.12/StockAlert.exe" &
```

Only create installers when explicitly requested for release/demo.

---

## API & Rate Limiting

### Finnhub Free Tier Limits

- **60 API calls per minute** (global across all requests)
- **Max 15 tickers** can be monitored
- **Minimum 90 second** check interval

### Shared Rate Limiter Pattern

**CRITICAL**: Multiple `FinnhubProvider` instances MUST share the same rate limiter.

**Problem**: Each ticker dialog creates a new FinnhubProvider. If each has its own rate limiter, they don't know about each other's API calls, causing rate limit errors.

**Solution**: Module-level singleton rate limiter in `api/finnhub.py`:

```python
# Shared rate limiter singleton
_shared_rate_limiter: RateLimiter | None = None

def _get_shared_rate_limiter() -> RateLimiter:
    global _shared_rate_limiter
    if _shared_rate_limiter is None:
        _shared_rate_limiter = RateLimiter(rate_limit=60, burst_size=10)
    return _shared_rate_limiter

class FinnhubProvider:
    def __init__(self, api_key: str):
        # Use shared rate limiter
        self._rate_limiter = _get_shared_rate_limiter()
```

### API Calls Per Operation

Know how many API calls each operation makes:

| Operation | API Calls |
|-----------|-----------|
| Test Connection | 1 (quote) |
| Validate Symbol | 1 (symbol_lookup) + 1 (quote) + 1 (company_profile) = 3 |
| Refresh Price | 1 (quote) |
| Edit Ticker Dialog | 1 (quote on open) |
| News Refresh | 1 per category |

---

## Windows-Specific Issues

### Keyring/Credential Storage

**Problem**: `keyring` library fails in frozen exe with "DLL load failed while importing win32api".

**Solution**: Implement fallback to config.json storage in `core/api_key_manager.py`:

```python
def _is_keyring_available() -> bool:
    """Check if keyring works before using it."""
    try:
        import keyring
        keyring.get_password("StockAlert_Test", "test")
        return True
    except Exception:
        return False

def get_api_key() -> str | None:
    # Try keyring first
    if _is_keyring_available():
        key = keyring.get_password(SERVICE_NAME, FINNHUB_KEY_NAME)
        if key:
            return key
    # Fall back to config file
    return _get_from_config()
```

### Console Window Flash

To prevent console window appearing on startup, ensure `base="Win32GUI"` in setup_msi.py:

```python
executables = [
    Executable(
        "src/stockalert/__main__.py",
        base="Win32GUI",  # CRITICAL: Prevents console window
        target_name="StockAlert.exe",
        icon="stock_alert.ico",
    )
]
```

---

## PyQt6 UI Patterns

### Dialogs Must Have Parent Window

**Problem**: Showing QMessageBox before UI is created causes app crash.

**Solution**: Always show dialogs AFTER the main window is created and visible:

```python
def run(self) -> int:
    # 1. Create Qt app
    self.qt_app = QApplication(sys.argv)

    # 2. Set up UI FIRST
    self._setup_ui()

    # 3. Show window
    self.main_window.showMaximized()

    # 4. THEN show dialogs via timer (after event loop starts)
    QTimer.singleShot(300, self._show_startup_dialogs)

    return self.qt_app.exec()
```

### Dynamic UI Elements (Show After Action)

For fields that should only appear after user action (e.g., tier limits after test connection):

```python
# In _setup_ui():
self.tier_limits_row_label = QLabel(_("settings.tier_limits") + ":")
self.tier_limits_label = QLabel("")
form_layout.addRow(self.tier_limits_row_label, self.tier_limits_label)
# Hide initially
self.tier_limits_row_label.setVisible(False)
self.tier_limits_label.setVisible(False)

# In _on_test_api_key() after success:
self.tier_limits_label.setText(tier_text)
self.tier_limits_row_label.setVisible(True)
self.tier_limits_label.setVisible(True)
```

### Card Layout Spacing

For card-style layouts (like service mode selection), use generous spacing:

```python
card = QFrame()
card.setMinimumWidth(250)
card.setMinimumHeight(120)
card_layout = QVBoxLayout(card)
card_layout.setSpacing(12)  # Vertical spacing between elements
card_layout.setContentsMargins(20, 20, 20, 20)  # Padding inside card

# Between cards:
cards_layout = QHBoxLayout()
cards_layout.setSpacing(24)  # Space between cards
cards_layout.addStretch()  # Don't stretch cards to fill width
```

### Force UI Update During Long Operations

When doing synchronous operations, force UI refresh:

```python
from PyQt6.QtWidgets import QApplication

def _on_test_api_key(self):
    self.status_label.setText("Testing...")
    QApplication.processEvents()  # Force UI update

    # ... do API call ...
```

---

## Configuration & Storage

### Persistent Config Location (AppData)

**CRITICAL**: Config is stored in AppData, NOT in the app directory. This ensures settings persist across rebuilds.

```
Location: %APPDATA%\StockAlert\config.json
Example:  C:\Users\Robert Cushman\AppData\Roaming\StockAlert\config.json
```

**Why AppData?**
- Survives application rebuilds (no more re-entering phone number!)
- Survives reinstalls (user data separate from app files)
- Standard Windows pattern for user data

**Migration**: On first run, the app checks for config in the old location (app directory) and migrates it to AppData automatically.

**Key Files**:
- `src/stockalert/core/paths.py` - Central path management
- Uses `get_config_path()` everywhere instead of hardcoded paths

### Auto-Save on Test Connection

**Insight**: Users expect API key to be saved when test connection succeeds, not just when clicking Save.

```python
def _on_test_api_key(self):
    success, message = test_api_key(api_key)
    if success:
        set_api_key(api_key)  # Auto-save immediately
        self.api_status_label.setText("✓ Connected successfully (saved)")
```

### ConfigManager vs Direct File Writes - CRITICAL

**Problem**: `api_key_manager.py` writes directly to `config.json`, but `ConfigManager` has its own in-memory cache. When `ConfigManager.set(..., save=True)` is called, it overwrites the file with its cache, **erasing the API key**.

**Symptoms**: API key works after test connection, but "No API key" appears after clicking Save Settings.

**Solution**: Reload ConfigManager from disk before saving to pick up external changes:

```python
def _on_save_clicked(self):
    # Save API key FIRST (writes directly to config.json)
    if api_key:
        set_api_key(api_key)

    # Reload config to pick up the api_key we just saved
    self.config_manager.reload()

    # Now set other values and save
    self.config_manager.set("settings.language", language, save=False)
    self.config_manager.set("settings.service_mode", mode, save=True)
```

**Root Cause Log Evidence**:
```
22:08:15 | API key stored in config file        ← Test connection saved key
22:08:21 | API key present: True                ← Works!
22:08:30 | Settings changed, reloading          ← User clicked Save
22:08:33 | API key present: False               ← KEY ERASED!
```

### Config File Location

Config is now stored in AppData for persistence (both dev and frozen):
```
C:\Users\<username>\AppData\Roaming\StockAlert\config.json
```

Assets (icons, locales) remain in the app directory:
```
C:\...\build\exe.win-amd64-3.12\stock_alert.ico
C:\...\build\exe.win-amd64-3.12\lib\stockalert\i18n\locales\
```

---

## Internationalization (i18n)

### Always Update Both Locale Files

Every new translation key MUST be added to BOTH:
- `src/stockalert/i18n/locales/en.json`
- `src/stockalert/i18n/locales/es.json`

### Translation Key Naming

Use dot notation: `category.subcategory.name`

```json
{
  "settings": {
    "tier_limits": "Tier Limits",
    "tier_limits_free": "Max {max_tickers} tickers, {min_interval}s minimum interval"
  }
}
```

### Parameterized Translations

Use format placeholders:

```python
tier_text = _("settings.tier_limits_free").format(
    max_tickers=max_tickers,
    min_interval=min_interval
)
```

---

## Testing & Demos

### Pre-Demo Checklist

Before any demo:
1. Do a fresh build
2. Test the entire happy path manually
3. **DO NOT** add new features or "edge case fixes" right before demo
4. Keep the working build as backup

### Regression Testing

After any change, test:
1. App launches without crash
2. API key test connection works
3. Can add/edit/delete tickers
4. Tier limits show after test connection (not before)
5. Background service start/stop works

---

## Common Mistakes to Avoid

### 1. Adding Untested Startup Checks Before Demo

**What happened**: Added config recovery warning dialog that crashed app because it ran before UI was created.

**Lesson**: Never add startup logic without thorough testing. Startup code is fragile.

### 2. Forgetting Inno Setup Location

**What happened**: Searched in Program Files, wasted time.

**Lesson**: It's in `%LOCALAPPDATA%\Programs\Inno Setup 6\`

### 3. Creating New Rate Limiters Per Instance

**What happened**: Each ticker dialog got fresh rate limiter, causing API failures.

**Lesson**: Use singleton pattern for shared resources like rate limiters.

### 4. Showing UI Elements Before Relevant Data Exists

**What happened**: Tier limits showed "Free tier: 15 tickers..." before user even tested connection.

**Lesson**: Hide dynamic fields until the action that populates them occurs.

### 5. Not Killing App Before Rebuild

**What happened**: Build failed with "directory cannot be cleaned".

**Lesson**: Always `taskkill //F //IM StockAlert.exe` before rebuild.

### 6. Using Unix Flags in Git Bash for Windows Commands

**What happened**: `taskkill /f /im` didn't work.

**Lesson**: Use `//F //IM` for Windows commands in Git Bash.

---

## WhatsApp Backend & API Keys

### Architecture Overview

The WhatsApp notification system uses a **three-tier architecture**:
1. **Desktop App** → 2. **Vercel Backend** → 3. **Twilio API**

The desktop app does NOT call Twilio directly. This keeps Twilio credentials out of the executable.

### API Key Management (Internal - NOT User-Facing)

**CRITICAL**: The WhatsApp API key is **embedded in the app** and **invisible to users**.

**How it works:**
1. The API key is XOR-obfuscated and embedded in `core/api_key_manager.py`
2. On app startup, `provision_stockalert_api_key()` auto-stores it in Windows Credential Manager
3. `TwilioService` reads the key from Credential Manager when sending alerts
4. Users just toggle "Enable WhatsApp" - no key configuration required

**Why this design:**
- Users only configure ONE key (Finnhub) - less friction
- WhatsApp API key is the app's identity, not user data
- Security: key is obfuscated, not plain text in the binary

**Updating the embedded key:**
```python
# In api_key_manager.py
# Generate new encoded key:
key = "your-new-api-key"
encoded = bytes(ord(c) ^ 0x5A for c in key)
print(repr(encoded))  # Use this as _EMBEDDED_KEY_DATA
```

**Vercel side:**
- Set `API_KEY` environment variable in Vercel project settings
- Deploy: `cd backend && vercel --prod`
- Test: request without key should return 401

### Common Issues

**401 Unauthorized from Vercel:**
1. Check `API_KEY` env var is set in Vercel (not empty)
2. Verify no trailing newline in the value
3. Ensure embedded key in app matches Vercel exactly
4. Redeploy after changing env vars: `vercel --prod --force`

**Key not provisioning:**
- Check `provision_stockalert_api_key()` is called in `app.py` and `service.py`
- Verify `_decode_embedded_key()` returns correct value
- Check Windows Credential Manager or config.json for stored key

---

## Quick Reference

### Build & Run (Development)
```bash
taskkill //F //IM StockAlert.exe
python setup_msi.py build_exe
"./build/exe.win-amd64-3.12/StockAlert.exe" &
```

### Create Installer (Release)
```bash
"%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe" installer.iss
```

### Key File Locations
| File | Purpose |
|------|---------|
| `%APPDATA%\StockAlert\config.json` | User settings (persists across builds!) |
| `setup_msi.py` | Build configuration |
| `installer.iss` | Inno Setup script |
| `src/stockalert/app.py` | Main application orchestrator |
| `src/stockalert/core/paths.py` | Central path management |
| `src/stockalert/core/api_key_manager.py` | API key storage |
| `src/stockalert/api/finnhub.py` | API client with rate limiting |
| `src/stockalert/ui/dialogs/settings_dialog.py` | Settings UI |
| `src/stockalert/i18n/locales/*.json` | Translations |

---

*Last updated: February 2026*
