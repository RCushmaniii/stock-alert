# StockAlert - Lessons Learned & Technical Notes

This document captures important discoveries, gotchas, and solutions found during development. **Read this before making changes** to avoid repeating past mistakes.

---

## Table of Contents

1. [Build & Packaging](#build--packaging)
2. [API & Rate Limiting](#api--rate-limiting)
3. [Windows-Specific Issues](#windows-specific-issues)
4. [Single-Instance Application & IPC](#single-instance-application--ipc-critical) ⚠️ **READ THIS**
5. [PyQt6 UI Patterns](#pyqt6-ui-patterns)
6. [Configuration & Storage](#configuration--storage)
7. [Internationalization (i18n)](#internationalization-i18n)
8. [Testing & Demos](#testing--demos)
9. [Common Mistakes to Avoid](#common-mistakes-to-avoid)
10. [WhatsApp Backend & API Keys](#whatsapp-backend--api-keys)

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

### pywin32 DLL Loading in Frozen Builds

**Problem**: In cx_Freeze frozen builds, importing `win32api`, `win32pipe`, etc. fails with "DLL load failed while importing win32api: The specified procedure could not be found."

**Root Cause**: The `.pyd` modules (win32api.pyd, win32pipe.pyd) need `pywintypes312.dll` loaded first, but they can't find it in the frozen environment.

**Solution**: Pre-load the DLL using `ctypes.WinDLL()` BEFORE importing win32 modules:

```python
_HAS_PYWIN32 = False
try:
    import sys
    if getattr(sys, "frozen", False):
        import ctypes
        from pathlib import Path
        exe_dir = Path(sys.executable).parent
        dll_paths = [
            exe_dir / "pywintypes312.dll",
            exe_dir / "lib" / "pywintypes312.dll",
        ]
        for dll_path in dll_paths:
            if dll_path.exists():
                try:
                    ctypes.WinDLL(str(dll_path))
                    break
                except Exception:
                    pass

    import win32api
    import win32pipe
    # ... other win32 imports
    _HAS_PYWIN32 = True
except ImportError:
    pass
```

**Key File**: `src/stockalert/core/ipc.py` - This pattern is critical for IPC (Named Pipes, Mutex) functionality.

### Locale Files in Frozen Builds

**Problem**: Translator looks for locale files inside `library.zip` where they can't be directly accessed.

**Error in log**: `Locale file not found: C:\...\lib\library.zip\stockalert\i18n\locales\en.json`

**Root Cause**: The service explicitly passed `locales_dir=Path(__file__).parent / "i18n" / "locales"` to Translator. In frozen builds, `__file__` points inside `library.zip`.

**Solution**: Don't pass `locales_dir` - let Translator auto-detect using `_get_locales_dir()`:

```python
# WRONG - breaks in frozen builds
self.translator = Translator(
    locales_dir=Path(__file__).parent / "i18n" / "locales"
)

# CORRECT - auto-detects based on sys.frozen
self.translator = Translator()
```

The `Translator._get_locales_dir()` function already handles frozen builds correctly by returning `exe_dir / "lib" / "stockalert" / "i18n" / "locales"`.

---

## Single-Instance Application & IPC (CRITICAL)

This section documents the extensive struggles with implementing single-instance behavior and window activation. **This took days to get right.**

### The Problem

When a user clicks the app icon (Start Menu, desktop shortcut) while it's already running in the system tray:
- **Expected**: Existing window appears
- **Wrong behavior 1**: Error dialog "StockAlert is already running" (unfriendly)
- **Wrong behavior 2**: Nothing happens (confusing)
- **Wrong behavior 3**: Blank white window appears (broken)

### Architecture Overview

StockAlert has a **GUI/Service split architecture**:
- **GUI Process** (`StockAlert.exe`): PyQt6 window, can minimize to system tray
- **Service Process** (`StockAlert.exe --service`): Headless monitoring, Named Pipe server for IPC
- **Second Instance** (user clicks app again): Should tell GUI to show window, then exit

### Failed Approaches (Don't Do These)

#### ❌ Approach 1: Show Error Dialog
```python
# WRONG - Unfriendly UX
if not instance_lock.acquire():
    QMessageBox.warning(None, "Already Running",
        "Check your system tray for the existing instance.")
    return 1
```
**Problem**: Users don't know what a "system tray" is. They just want the window to appear.

#### ❌ Approach 2: Windows API FindWindow + ShowWindow
```python
# WRONG - Causes blank white window with Qt
user32 = ctypes.windll.user32
hwnd = user32.FindWindowW(None, "AI StockAlert...")
if hwnd:
    user32.ShowWindow(hwnd, SW_RESTORE)
    user32.SetForegroundWindow(hwnd)
```
**Problem**: Windows API's `ShowWindow()` on a Qt window that's hidden via `hide()` results in a **blank white window**. The Qt widgets don't render because Qt didn't properly prepare the window for display.

#### ❌ Approach 3: QTimer.singleShot from Background Thread
```python
# WRONG - QTimer.singleShot doesn't work from non-Qt threads
def _handle_ipc_command(self, command):
    if command == "SHOW_WINDOW":
        QTimer.singleShot(0, self._show_main_window)  # Silent failure!
```
**Problem**: `QTimer.singleShot()` called from a background thread (IPC server thread) silently fails. The callback never executes.

### ✅ The Correct Solution: IPC + QMetaObject.invokeMethod

**Step 1: Single-Instance Detection via Lock File**

In `__main__.py`:
```python
class InstanceLock:
    """Uses file locking for single-instance detection."""

    def acquire(self) -> bool:
        try:
            self._lock_file = open(self._lock_path, "w")
            msvcrt.locking(self._lock_file.fileno(), msvcrt.LK_NBLCK, 1)
            return True
        except (OSError, IOError):
            return False  # Another instance has the lock
```

**Step 2: GUI IPC Server (Named Pipe)**

In `core/ipc.py`:
```python
GUI_PIPE_NAME = "\\\\.\\pipe\\StockAlertGUIPipe"

class GUIPipeServer:
    """Listens for commands from second instances."""

    def __init__(self, on_command: Callable[[str], str]):
        self._on_command = on_command
        self._thread = threading.Thread(target=self._server_loop, daemon=True)

    def _server_loop(self):
        while self._running:
            # Create pipe, wait for connection, read command, send response
            h_pipe = win32pipe.CreateNamedPipe(GUI_PIPE_NAME, ...)
            win32pipe.ConnectNamedPipe(h_pipe, None)
            result, data = win32file.ReadFile(h_pipe, BUFFER_SIZE)
            response = self._on_command(data.decode("utf-8"))
            win32file.WriteFile(h_pipe, response.encode("utf-8"))
```

**Step 3: Thread-Safe Window Activation**

In `app.py` - **CRITICAL: Use QMetaObject.invokeMethod, NOT QTimer.singleShot**:
```python
def _handle_gui_command(self, command: str) -> str:
    """Called from background IPC thread."""
    if command == "SHOW_WINDOW":
        # QTimer.singleShot DOES NOT WORK from background thread!
        # Must use QMetaObject.invokeMethod with QueuedConnection
        from PyQt6.QtCore import QMetaObject, Qt
        QMetaObject.invokeMethod(
            self.main_window,
            "_show_from_ipc",
            Qt.ConnectionType.QueuedConnection
        )
        return "SUCCESS"
```

In `main_window.py` - **The slot must be decorated with @pyqtSlot()**:
```python
from PyQt6.QtCore import pyqtSlot

class MainWindow(QMainWindow):
    @pyqtSlot()
    def _show_from_ipc(self) -> None:
        """Qt slot - can be safely invoked from background thread."""
        self.showMaximized()
        self.raise_()
        self.activateWindow()
```

**Step 4: Second Instance Sends Command and Exits Silently**

In `__main__.py`:
```python
def _activate_existing_instance() -> bool:
    """Send IPC command to existing GUI to show window."""
    from stockalert.core.ipc import send_gui_command
    response = send_gui_command("SHOW_WINDOW", timeout_ms=2000)
    return response and "SUCCESS" in response

def main():
    instance_lock = InstanceLock("StockAlertGUI")
    if not instance_lock.acquire():
        _activate_existing_instance()
        return 0  # Exit silently (not an error!)
```

### Key Files for Single-Instance/IPC

| File | Purpose |
|------|---------|
| `src/stockalert/__main__.py` | Instance lock, `_activate_existing_instance()` |
| `src/stockalert/core/ipc.py` | `GUIPipeServer`, `send_gui_command()` |
| `src/stockalert/app.py` | `_handle_gui_command()`, starts GUIPipeServer |
| `src/stockalert/ui/main_window.py` | `_show_from_ipc()` slot |

### Debugging Tips

**Check if IPC is working:**
```bash
tail -f stockalert.log | grep -i "IPC\|SHOW_WINDOW"
```

**Expected log entries when second instance activates first:**
```
INFO | GUI pipe server started: \\.\pipe\StockAlertGUIPipe
INFO | GUI IPC received command: SHOW_WINDOW
INFO | Showing window via IPC request
```

**If window doesn't appear:**
1. Check "GUI pipe server started" appears in log
2. Check "GUI IPC received command: SHOW_WINDOW" appears
3. If command received but window doesn't show → check `_show_from_ipc` is decorated with `@pyqtSlot()`

### Why This Is So Hard

1. **Qt + Windows + Threads**: Qt has strict thread affinity for GUI operations
2. **Hidden vs Minimized**: A Qt window hidden with `hide()` is NOT the same as minimized - Windows API doesn't understand this
3. **Silent Failures**: `QTimer.singleShot` from wrong thread just silently does nothing
4. **Named Pipes**: pywin32 adds complexity (see pywin32 DLL loading section)

### Service Single-Instance (Mutex)

The background service uses a Windows Mutex (not file locking) for single-instance:

```python
# In core/ipc.py
MUTEX_NAME = "Local\\StockAlertServiceMutex"

class ServiceMutex:
    def acquire(self) -> bool:
        self._handle = win32event.CreateMutex(None, False, MUTEX_NAME)
        if win32api.GetLastError() == winerror.ERROR_ALREADY_EXISTS:
            return False  # Another service is running
        return True
```

This is separate from the GUI's `InstanceLock` - both can run simultaneously (GUI + Service), but not multiple GUIs or multiple services.

### Frontend → Backend Config Sync

When user saves settings in the GUI, the backend service needs to pick up changes:

**Method 1: Immediate IPC (preferred)**
```python
# In app.py _on_settings_changed()
if is_service_running():
    send_reload_config()  # Sends "RELOAD_SETTINGS" via Named Pipe
```

**Method 2: File watching (backup)**
```python
# In service.py run_forever()
while self._running:
    if self._check_config_changes():  # Checks mtime every 60 seconds
        self._reload_config()
```

The service's `_reload_config()` method:
- Reloads config from disk
- Updates language if changed
- Updates alert settings (WhatsApp enabled, etc.)
- Reloads ticker list

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
6. **Single-instance behavior**: Close window (goes to tray), click Start Menu icon → window should reappear (not error, not blank)

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

### 7. Using Windows API ShowWindow on Qt Hidden Windows

**What happened**: Used `FindWindow()` + `ShowWindow()` to bring existing window to front. Result: blank white window.

**Lesson**: Qt windows hidden with `hide()` cannot be shown with Windows API. Must use Qt methods (`showMaximized()`, etc.) via IPC.

### 8. Using QTimer.singleShot from Background Thread

**What happened**: IPC server received SHOW_WINDOW command, called `QTimer.singleShot(0, self._show_window)`. Nothing happened.

**Lesson**: `QTimer.singleShot()` silently fails when called from non-Qt thread. Use `QMetaObject.invokeMethod()` with `Qt.ConnectionType.QueuedConnection` instead.

### 9. Passing Path(__file__) in Frozen Builds

**What happened**: Service passed `locales_dir=Path(__file__).parent / "i18n/locales"` to Translator. Locale files not found.

**Lesson**: In cx_Freeze frozen builds, `__file__` points inside `library.zip`. Never use `Path(__file__)` for resource paths. Use functions that detect frozen state (like `_get_locales_dir()`).

### 10. Forgetting to Pre-load pywin32 DLLs

**What happened**: IPC using Named Pipes failed with "DLL load failed while importing win32api".

**Lesson**: In frozen builds, pywin32's `.pyd` files can't find `pywintypes312.dll`. Pre-load it with `ctypes.WinDLL()` before importing win32 modules.

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

## PyQt6 Table Column Management

### Adding Columns to QTableWidget

**Problem**: When adding a new column to an existing table, you must update ALL column index references throughout the code.

**Example**: Adding a "News" column (📰) after the Symbol column shifted all subsequent columns:

| Column | Before | After |
|--------|--------|-------|
| Checkbox | 0 | 0 |
| Logo | 1 | 1 |
| Symbol | 2 | 2 |
| **📰 News** | - | **3** (NEW) |
| Name | 3 | 4 |
| Industry | 4 | 5 |
| Market Cap | 5 | 6 |
| Low | 6 | 7 |
| High | 7 | 8 |
| Price | 8 | 9 |
| Enabled | 9 | 10 |

**Checklist when adding columns:**
1. Update `setColumnCount()`
2. Update header labels list
3. Update ALL `setItem()` and `setCellWidget()` calls
4. Update ALL column width settings (`setColumnWidth()`)
5. Update any `item().text()` or `cellWidget()` index references
6. Update `retranslate_ui()` if it sets headers

### Widget Tooltips (QToolTip Styling)

**Problem**: Default QToolTip can appear as a black rectangle with invisible text in dark themes.

**Solution**: Explicitly style QToolTip in the widget's stylesheet:

```python
checkbox_container.setStyleSheet("""
    QWidget { background: transparent; }
    QToolTip {
        background-color: #333333;
        color: #FFFFFF;
        border: 1px solid #555555;
        padding: 4px;
    }
""")
checkbox.setToolTip(_("tickers.news_enabled_help"))
```

**Important**: The QToolTip style must be on the widget that has the tooltip, or a parent container. It won't inherit from global app styles in all cases.

---

## WhatsApp Business API Quality

### Delivery vs API Success - CRITICAL

**Problem**: Twilio API can return `success: true` and a `message_sid` even when the message will NOT be delivered.

**Why this happens:**
- Twilio accepts the message into their queue (API success)
- Meta/WhatsApp later decides whether to deliver it
- Delivery depends on: template approval status, user quality rating, rate limits

**What to check when messages aren't delivered but API shows success:**

1. **Template status** in Twilio Console → Messaging → Content Templates
   - Must show "Approved" status
   - "Pending" templates won't deliver

2. **WhatsApp Business Quality Rating**
   - Check Twilio Console → Phone Numbers → WhatsApp Senders
   - Low quality = throttled or blocked delivery

3. **24-hour session window**
   - Templates can be sent anytime
   - Freeform messages ONLY work if user messaged you in last 24 hours

4. **Phone number format**
   - Must include country code (e.g., +1 for US, +52 for Mexico)
   - Mexican numbers need +521 prefix for WhatsApp (see phone_utils.py)

### Meta Quality Monitoring

WhatsApp Business messages include an info icon (ⓘ) that users can tap to:
- Mark as "Not interested"
- Report as spam
- Block the sender

**Impact of negative feedback:**
- Lowers your quality rating
- Can cause: slower delivery, silent failures, account restrictions
- No notification when this happens - messages just stop delivering

**Mitigation strategies:**
1. Use reasonable alert thresholds to minimize notification frequency
2. Implement cooldown periods (Settings) to prevent alert flooding
3. Warn users about WhatsApp quality in onboarding/help
4. Always have Windows notifications as backup

### Enhanced Logging for Debugging

Added detailed logging for WhatsApp delivery debugging:

```python
# In TwilioService
logger.info(
    f"WhatsApp message sent - SID: {msg_sid}, Status: {msg_status}, "
    f"Error Code: {error_code}, Error Message: {error_msg}"
)

# Backend response includes:
{
    'success': True,
    'message_sid': 'SMxxxxx',
    'status': 'queued',  # or 'sent', 'delivered', 'failed'
    'error_code': None,   # Twilio error code if any
    'error_message': None # Twilio error message if any
}
```

---

## Consolidated Notifications Pattern

### Problem

Sending individual notifications for each ticker that crosses a threshold creates notification spam, especially when multiple stocks move simultaneously.

### Solution

Collect all alerts during a check cycle, then send ONE consolidated notification:

```python
# In monitor.py
@dataclass
class PendingAlert:
    """A pending alert to be sent in consolidated notification."""
    symbol: str
    name: str
    price: float
    threshold: float
    alert_type: str  # "high" or "low"

def _check_all_tickers(self) -> None:
    """Check prices for all enabled tickers and send consolidated alerts."""
    pending_alerts: list[PendingAlert] = []

    for symbol, state in self._tickers.items():
        alert = self._check_ticker(state)
        if alert:
            pending_alerts.append(alert)

    # Send ONE notification for all alerts
    if pending_alerts:
        self._send_consolidated_alerts(pending_alerts)
```

### Alert Manager Consolidated Format

```python
# In alert_manager.py
def send_consolidated_alert(self, alerts: list) -> None:
    if len(alerts) == 1:
        # Single alert - traditional detailed format
        alert = alerts[0]
        title = f"{alert.symbol} {'High' if alert.alert_type == 'high' else 'Low'} Alert"
        message = f"{alert.name}: ${alert.price:.2f} (threshold: ${alert.threshold:.2f})"
    else:
        # Multiple alerts - consolidated summary
        title = f"{len(alerts)} Price Alerts"
        lines = []
        for alert in alerts:
            direction = "↑" if alert.alert_type == "high" else "↓"
            lines.append(f"{direction} {alert.symbol}: ${alert.price:.2f}")
        message = "\n".join(lines)

    self._send_windows_notification(title, message)
    if self._whatsapp_enabled:
        self._send_whatsapp_notification(alerts)
```

---

## Currency Switcher (USD/MXN)

### Architecture

The currency feature allows users to view prices in USD or Mexican Pesos (MXN):

- **Exchange Rate API**: Uses exchangerate-api.com free tier (1,500 requests/month)
- **Caching**: Rate cached for 1 hour to minimize API calls
- **Storage**: All values stored internally in USD (Option A pattern)
- **Display**: Converted on-the-fly using cached exchange rate

### Key Files

| File | Purpose |
|------|---------|
| `src/stockalert/api/exchange_rate.py` | API client with caching |
| `src/stockalert/core/currency.py` | CurrencyFormatter class |
| `src/stockalert/ui/main_window.py` | Currency toggle in header |

### Implementation Pattern

```python
# In main_window.py __init__
self.currency_formatter = CurrencyFormatter(config_manager)
set_global_formatter(self.currency_formatter)

# Set up exchange rate API key (embedded)
set_exchange_rate_api_key("your-api-key")

# Pre-fetch rate if currency is MXN
if config_manager.get("settings.currency", "USD") == "MXN":
    self._refresh_exchange_rate()
```

### CurrencyFormatter Usage

```python
from stockalert.core.currency import get_formatter

formatter = get_formatter()

# Format price (converts if MXN)
price_str = formatter.format_price(123.45)  # "$123.45" or "MX$2,469.00"

# Format market cap
cap_str = formatter.format_market_cap(50000)  # "$50.0B" or "MX$1.0T"

# Convert user input back to USD
usd_value = formatter.parse_user_input("2500")  # Returns USD equivalent
```

### Header Toggle Pattern

The currency toggle uses the same style as language buttons:

```python
# USD | MXN toggle (reuses langButton style)
self.currency_usd_btn = QPushButton("USD")
self.currency_usd_btn.setObjectName("langButton")
self.currency_usd_btn.clicked.connect(lambda: self._set_currency("USD"))

self.currency_mxn_btn = QPushButton("MXN")
self.currency_mxn_btn.setObjectName("langButton")
self.currency_mxn_btn.clicked.connect(lambda: self._set_currency("MXN"))
```

### API Budget Analysis

- Free tier: 1,500 requests/month
- Market hours: ~137 hours/month
- At 1 request/hour: ~137 requests/month (under 10% of limit)

---

## Onboarding Dialog

### Reset Flag for Testing

To trigger the onboarding dialog on next launch:

```json
// In config.json
{
  "onboarding_completed": false
}
```

Or programmatically:
```python
config_manager.set("onboarding_completed", False, save=True)
```

### Content Guidelines

Onboarding should be:
1. **Specific**: Step-by-step with exact URLs and button names
2. **Minimal**: Only essential setup steps (4 steps max)
3. **Honest**: Include warnings about limitations (e.g., WhatsApp quality issues)

Example structure:
- Step 1: Get Finnhub API key (with exact URL)
- Step 2: Configure Settings (paste key, test connection)
- Step 3: Set up Profile (for WhatsApp - phone with country code)
- Step 4: Add stocks to monitor

Include a warning tip about WhatsApp quality monitoring to set expectations.

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

## WhatsApp Opt-In Flow

### Why Opt-In Is Required

WhatsApp Business API requires **explicit user consent** before sending business-initiated messages. Without opt-in:
- Messages may be flagged as spam
- Meta may throttle or block delivery
- Account quality rating suffers

### Implementation

**1. Twilio Content Template**

Create an opt-in template in Twilio Console → Messaging → Content Templates:
- Template Name: `stock_alert_optin`
- Body: "AI StockAlert would like to send you price alerts when your stocks cross your set thresholds.\n\nCurrently, you're monitoring {{1}} stocks.\n\nWould you like to receive WhatsApp alerts?"
- Quick Reply buttons: "Yes, enable alerts" | "No thanks"

**2. Backend Support (`backend/api/send_whatsapp.py`)**

```python
OPTIN_TEMPLATE_SID = os.environ.get('TWILIO_OPTIN_SID', 'HXxxxx')

def send_whatsapp_message(to_number, message=None, template_data=None, template_type="alert"):
    if template_type == "optin":
        content_variables = json.dumps({
            "1": str(template_data.get("1") or template_data.get("stock_count", "0")),
        })
        template_sid = OPTIN_TEMPLATE_SID
```

**3. Desktop App (`core/twilio_service.py`)**

```python
def send_optin_message(self, to_number: str, stock_count: int) -> bool:
    payload = {
        "phone": formatted,
        "template_type": "optin",
        "template_data": {"1": str(stock_count)},
    }
    return self._call_api(VERCEL_API_URL, payload)
```

**4. Auto-Trigger on First Enable (`ui/dialogs/settings_dialog.py`)**

```python
def _on_save_clicked(self):
    whatsapp_newly_enabled = whatsapp_enabled and not old_whatsapp
    if whatsapp_newly_enabled:
        optin_sent = self.config_manager.get("whatsapp_optin_sent", False)
        if not optin_sent:
            self._send_whatsapp_optin()

def _send_whatsapp_optin(self):
    service = TwilioService()
    success = service.send_optin_message(phone_number, stock_count)
    if success:
        self.config_manager.set("whatsapp_optin_sent", True, save=True)
```

### Key Points

- Opt-in only sent **once** (tracked via `whatsapp_optin_sent` config flag)
- Triggered when user **enables and saves** WhatsApp settings (not on test button)
- Stock count dynamically inserted from current ticker list
- User taps "Yes, enable alerts" button to consent

### Testing Opt-In Flow

1. Set `whatsapp_enabled: false` in config.json
2. Remove `whatsapp_optin_sent` key if present
3. Launch app, enable WhatsApp in Settings, click Save
4. Check WhatsApp for opt-in message with Yes/No buttons

---

*Last updated: February 7, 2026*
