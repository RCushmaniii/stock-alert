# StockAlert Debug Log

## Session: 2026-01-31

### Issues Being Tracked

---

## Issue 1: Language Not Persisting on Restart

### Symptoms

- User sets language to English via header button (EN)
- Clicks "Save Settings"
- App switches to Spanish unexpectedly
- On restart, app loads in wrong language

### Root Causes Identified

1. **Settings combo box triggering change during load**
   - `_load_settings()` sets combo index
   - Signal was connected, triggering `_on_language_combo_changed()`
   - This overwrote the saved language

2. **Circular callback issue**
   - Header button calls `_set_language()` → saves language → calls `on_settings_changed`
   - `on_settings_changed` calls `config_manager.reload()`
   - Reload could read stale file before write completed

3. **Two places to change language not synced**
   - Header EN/ES buttons (immediate save)
   - Settings tab combo box (was saving on "Save Settings" click)
   - These could overwrite each other

### Fixes Applied

| File                         | Change                                                                                   | Status     |
| ---------------------------- | ---------------------------------------------------------------------------------------- | ---------- |
| `settings_dialog.py:593-599` | Added `blockSignals(True/False)` around combo setCurrentIndex during load                | ✅ Applied |
| `settings_dialog.py:529-540` | Changed `_on_language_combo_changed` to save immediately and NOT call `on_save` callback | ✅ Applied |
| `main_window.py:1901-1918`   | Removed `on_settings_changed` callback from `_set_language` to prevent reload            | ✅ Applied |
| `settings_dialog.py:637-638` | Removed language save from `_on_save_clicked` (now saved immediately on change)          | ✅ Applied |

### Code Flow After Fix

```
Header EN button clicked:
  → _set_language("en")
    → translator.set_language("en")
    → config_manager.set("settings.language", "en") [SAVES TO FILE]
    → _update_lang_buttons("en")
    → retranslate_ui()
    → Sync settings_widget.language_combo (with blockSignals)
    → settings_widget.retranslate_ui()
    [NO on_settings_changed callback - prevents reload]

Settings combo changed:
  → _on_language_combo_changed(index)
    → translator.set_language(language)
    → config_manager.set("settings.language", language) [SAVES TO FILE]
    → retranslate_ui()
    [NO on_save callback - prevents reload]

App startup:
  → ConfigManager loads config.json
  → app.py reads settings.language from config
  → translator.set_language(language)
  → MainWindow created
    → _update_lang_buttons(current_lang)
  → SettingsWidget created
    → _load_settings()
      → blockSignals(True)
      → language_combo.setCurrentIndex(index)
      → blockSignals(False)
    → _connect_change_signals() [AFTER load, so no trigger]
```

---

## Issue 2: Service Status Shows "Stopped" After Starting

### Symptoms

- User clicks "Start Service"
- Green message "Background service started" appears
- But status indicator still shows "Stopped"
- IPC ping returns None

### Root Cause Identified

**WaitNamedPipe returns None on SUCCESS, not True**

```python
# BROKEN CODE (ipc.py:194)
if not win32pipe.WaitNamedPipe(PIPE_NAME, timeout_ms):
    return None  # This ALWAYS returned None because WaitNamedPipe returns None on success!
```

### Fix Applied

| File             | Change                                                                                             | Status     |
| ---------------- | -------------------------------------------------------------------------------------------------- | ---------- |
| `ipc.py:192-202` | Changed to try/except pattern - WaitNamedPipe raises exception on failure, returns None on success | ✅ Applied |

### Verification

```python
# Test command that now works:
>>> from stockalert.core.ipc import send_command, is_service_running, get_service_status
>>> send_command('PING')
'PONG'  # Was returning None before fix
>>> is_service_running()
True
>>> get_service_status()
{'pid': 90512, 'running': True, 'ticker_count': 8}
```

---

## Issue 3: GUI Kills Background Service on Startup

### Symptoms

- Background service running (PID visible)
- User opens GUI
- GUI kills the service instead of connecting to it
- Log shows: "Found existing background service (PID: X), stopping it..."

### Root Cause

`app.py:_cleanup_existing_service()` was designed for development (run latest code) but breaks production flow.

### Fix Applied

| File             | Change                                                                            | Status     |
| ---------------- | --------------------------------------------------------------------------------- | ---------- |
| `app.py:60-68`   | Removed `_cleanup_existing_service()` call, now just logs that service is running | ✅ Applied |
| `app.py:104-121` | Deleted `_cleanup_existing_service()` method entirely                             | ✅ Applied |
| `app.py:26`      | Removed unused `stop_background_process` import                                   | ✅ Applied |

---

## Issue 4: Service Status Update Timing

### Symptoms

- After clicking Start/Stop, status doesn't update immediately
- Need to wait for pipe server to initialize

### Fix Applied

| File                         | Change                                                                              | Status     |
| ---------------------------- | ----------------------------------------------------------------------------------- | ---------- |
| `settings_dialog.py:770-771` | Added `QTimer.singleShot(1500, self._update_service_status)` after successful start | ✅ Applied |
| `settings_dialog.py:791-792` | Added `QTimer.singleShot(1000, self._update_service_status)` after successful stop  | ✅ Applied |

---

## Issue 5: Settings Tab Not Retranslating on Startup

### Symptoms

- App loads with language set to English
- All tabs display in English EXCEPT Settings tab
- Settings tab shows Spanish text
- Switching language via header buttons fixes it temporarily

### Root Cause

The `_setup_ui()` method in widgets uses `_()` translation function during widget creation. If the translator's language was different when the module was first imported vs when the app actually runs, the text would be stale.

The `MainWindow.__init__()` was not calling `retranslate_ui()` after setup, so widgets kept their initial (potentially wrong) translations.

### Fix Applied

| File                   | Change                                             | Status     |
| ---------------------- | -------------------------------------------------- | ---------- |
| `main_window.py:88-90` | Added `retranslate_ui()` call at end of `__init__` | ✅ Applied |

```python
# Added at end of MainWindow.__init__:
self.retranslate_ui()  # Ensure all UI text matches current language
```

---

## Issue 6: Service Status Visual Indicator

### Request

User requested a visual indicator (green/red light) next to the service status label.

### Implementation

| File                         | Change                                                       | Status     |
| ---------------------------- | ------------------------------------------------------------ | ---------- |
| `settings_dialog.py:733-756` | Updated `_update_service_status()` to change indicator color | ✅ Applied |

- **Green (#00CC00)**: Service is running
- **Red (#CC0000)**: Service is stopped
- **Orange (#FF9900)**: Service is transitioning/unknown

---

## Issue 7: Service Start/Stop Not Prompting Save on Close

### Symptoms

- User stops or starts the background service
- Clicks X to close the app
- No "Unsaved Changes" dialog appears
- Service state change is lost

### Root Cause

The `_on_service_start()` and `_on_service_stop()` methods were not calling `_mark_dirty()` after successful operations, so the settings widget didn't know there were unsaved changes.

### Fix Applied

| File                         | Change                                                    | Status     |
| ---------------------------- | --------------------------------------------------------- | ---------- |
| `settings_dialog.py:781-782` | Added `self._mark_dirty()` after successful service start | ✅ Applied |
| `settings_dialog.py:804-805` | Added `self._mark_dirty()` after successful service stop  | ✅ Applied |

### Translations Verified

- `dialogs.unsaved_changes_title`: "Unsaved Changes" / "Cambios Sin Guardar"
- `dialogs.unsaved_changes_message`: Properly translated in both en.json and es.json

---

## Files Modified Summary

| File                                           | Lines Changed                               | Purpose                                   |
| ---------------------------------------------- | ------------------------------------------- | ----------------------------------------- |
| `src/stockalert/core/ipc.py`                   | 192-202                                     | Fix WaitNamedPipe success detection       |
| `src/stockalert/app.py`                        | 60-68, 104-121, 26                          | Remove service cleanup on GUI start       |
| `src/stockalert/ui/main_window.py`             | 1901-1918                                   | Fix language sync, remove reload callback |
| `src/stockalert/ui/dialogs/settings_dialog.py` | 529-540, 589-599, 637-638, 770-771, 791-792 | Fix language combo, service status timing |

---

## Automated Test Results (2026-01-31)

```
=== Test 1: Config Language Read/Write ===
✓ English saved and read correctly
✓ Spanish saved and read correctly

=== Test 2: ConfigManager Class ===
✓ ConfigManager.set() saves to file correctly
✓ ConfigManager.get() returns correct value

=== Test 3: Translator Class ===
✓ Translator.set_language('en') works
✓ Translator.set_language('es') works

=== Test 4: IPC Named Pipe ===
Service running: True
✓ PING returned PONG
✓ STATUS: {'pid': 100196, 'running': True, 'ticker_count': 8}

=== Test 5: WaitNamedPipe Behavior ===
✓ WaitNamedPipe on non-existent pipe raised exception (winerror=2)
KEY INSIGHT: WaitNamedPipe returns None on SUCCESS, raises exception on FAILURE

RESULTS: 5 passed, 0 failed
```

## Pending Verification

- [x] Config read/write works correctly
- [x] ConfigManager saves language to file
- [x] Translator switches languages correctly
- [x] IPC PING/STATUS works (service running)
- [x] WaitNamedPipe fix verified
- [ ] Language persists correctly across restart (needs manual test)
- [ ] Service status shows "Running" after Start Service (needs manual test)
- [ ] GUI connects to existing background service (needs manual test)
- [ ] Header EN/ES buttons sync with Settings combo (needs manual test)
- [ ] Save Settings doesn't change language unexpectedly (needs manual test)

---

## Test Commands

```powershell
# Check config language
type "C:\Users\Robert Cushman\AppData\Roaming\StockAlert\config.json" | findstr language

# Set config to English
python -c "import json; f=open(r'C:\Users\Robert Cushman\AppData\Roaming\StockAlert\config.json', 'r'); d=json.load(f); f.close(); d['settings']['language']='en'; f=open(r'C:\Users\Robert Cushman\AppData\Roaming\StockAlert\config.json', 'w'); json.dump(d, f, indent=2); f.close(); print('Done')"

# Test IPC
python -c "from stockalert.core.ipc import send_command, is_service_running; print('PING:', send_command('PING')); print('Running:', is_service_running())"

# Check for running service
wmic process where "name='python.exe' or name='pythonw.exe'" get processid,commandline /format:csv | findstr stockalert

# Check pipe exists
[System.IO.Directory]::GetFiles("\\.\pipe\") | Where-Object { $_ -like "*StockAlert*" }
```
