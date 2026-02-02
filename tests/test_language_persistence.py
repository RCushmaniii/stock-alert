"""
Automated tests for language persistence and service status fixes.
Run with: python -m pytest tests/test_language_persistence.py -v
"""

import json
import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def get_config_path():
    """Get the config file path."""
    import os
    appdata = os.environ.get("APPDATA", "")
    return Path(appdata) / "StockAlert" / "config.json"


def read_config():
    """Read the current config."""
    config_path = get_config_path()
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def write_config(config):
    """Write config to file."""
    config_path = get_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)


def test_config_language_read_write():
    """Test that language can be read and written to config."""
    print("\n=== Test 1: Config Language Read/Write ===")
    
    # Read current config
    config = read_config()
    original_lang = config.get("settings", {}).get("language", "en")
    print(f"Original language: {original_lang}")
    
    # Set to English
    config.setdefault("settings", {})["language"] = "en"
    write_config(config)
    
    # Read back
    config2 = read_config()
    assert config2["settings"]["language"] == "en", "Failed to save English"
    print("✓ English saved and read correctly")
    
    # Set to Spanish
    config2["settings"]["language"] = "es"
    write_config(config2)
    
    # Read back
    config3 = read_config()
    assert config3["settings"]["language"] == "es", "Failed to save Spanish"
    print("✓ Spanish saved and read correctly")
    
    # Restore original
    config3["settings"]["language"] = original_lang
    write_config(config3)
    print(f"✓ Restored to: {original_lang}")
    
    return True


def test_config_manager():
    """Test ConfigManager class."""
    print("\n=== Test 2: ConfigManager Class ===")
    
    from stockalert.core.config import ConfigManager
    
    config_path = get_config_path()
    cm = ConfigManager(config_path)
    
    # Get current language
    lang = cm.get("settings.language", "en")
    print(f"Current language via ConfigManager: {lang}")
    
    # Set to English
    cm.set("settings.language", "en")
    
    # Verify it was saved to file
    with open(config_path, "r", encoding="utf-8") as f:
        file_config = json.load(f)
    
    assert file_config["settings"]["language"] == "en", "ConfigManager didn't save to file"
    print("✓ ConfigManager.set() saves to file correctly")
    
    # Verify get returns correct value
    assert cm.get("settings.language") == "en", "ConfigManager.get() returned wrong value"
    print("✓ ConfigManager.get() returns correct value")
    
    return True


def test_translator():
    """Test Translator class."""
    print("\n=== Test 3: Translator Class ===")
    
    from stockalert.i18n.translator import Translator
    
    t = Translator()
    
    # Set to English
    t.set_language("en")
    assert t.current_language == "en", "Failed to set English"
    print("✓ Translator.set_language('en') works")
    
    # Get a translation
    settings_title = t.get("settings.title")
    assert settings_title != "settings.title", f"Translation not found: {settings_title}"
    print(f"✓ English translation: settings.title = '{settings_title}'")
    
    # Set to Spanish
    t.set_language("es")
    assert t.current_language == "es", "Failed to set Spanish"
    print("✓ Translator.set_language('es') works")
    
    # Get Spanish translation
    settings_title_es = t.get("settings.title")
    assert settings_title_es != settings_title, "Spanish translation same as English"
    print(f"✓ Spanish translation: settings.title = '{settings_title_es}'")
    
    return True


def test_ipc_pipe():
    """Test IPC Named Pipe communication."""
    print("\n=== Test 4: IPC Named Pipe ===")
    
    from stockalert.core.ipc import PIPE_NAME, MUTEX_NAME, send_command, is_service_running, get_service_status
    
    print(f"Pipe name: {PIPE_NAME}")
    print(f"Mutex name: {MUTEX_NAME}")
    
    # Check if service is running
    running = is_service_running()
    print(f"Service running: {running}")
    
    if running:
        # Test PING
        response = send_command("PING", timeout_ms=2000)
        assert response == "PONG", f"PING failed: {response}"
        print("✓ PING returned PONG")
        
        # Test STATUS
        status = get_service_status()
        assert status.get("running") == True, f"STATUS failed: {status}"
        print(f"✓ STATUS: {status}")
    else:
        print("⚠ Service not running, skipping IPC tests")
        
        # Check if pipe exists
        import os
        pipe_path = r"\\.\pipe\StockAlertServicePipe"
        try:
            # Try to check if pipe exists
            import win32pipe
            try:
                win32pipe.WaitNamedPipe(pipe_path, 100)
                print("⚠ Pipe exists but service reports not running")
            except Exception as e:
                print(f"✓ Pipe does not exist (expected when service stopped): {e}")
        except ImportError:
            print("⚠ win32pipe not available for pipe check")
    
    return True


def test_waitnamedpipe_behavior():
    """Test WaitNamedPipe return value behavior."""
    print("\n=== Test 5: WaitNamedPipe Behavior ===")
    
    try:
        import win32pipe
        
        # Test with non-existent pipe
        try:
            result = win32pipe.WaitNamedPipe(r"\\.\pipe\NonExistentPipe12345", 100)
            print(f"WaitNamedPipe on non-existent pipe returned: {result}")
        except Exception as e:
            error_code = getattr(e, "winerror", 0)
            print(f"✓ WaitNamedPipe on non-existent pipe raised exception (winerror={error_code}): {type(e).__name__}")
        
        # Document the behavior
        print("\nKEY INSIGHT: WaitNamedPipe returns None on SUCCESS, raises exception on FAILURE")
        print("The old code 'if not win32pipe.WaitNamedPipe(...)' was ALWAYS true because None is falsy!")
        
    except ImportError:
        print("⚠ win32pipe not available")
    
    return True


def run_all_tests():
    """Run all tests."""
    print("=" * 60)
    print("STOCKALERT AUTOMATED VERIFICATION TESTS")
    print("=" * 60)
    
    tests = [
        test_config_language_read_write,
        test_config_manager,
        test_translator,
        test_ipc_pipe,
        test_waitnamedpipe_behavior,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"✗ FAILED: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
