"""
StockAlert entry point.

Usage:
    python -m stockalert          # Start the GUI application
    python -m stockalert --tray   # Start minimized to system tray
    python -m stockalert --help   # Show help
"""

from __future__ import annotations

import atexit
import ctypes
import os
import sys
import tempfile

# Set Windows App User Model ID so taskbar shows our icon, not Python's
# This MUST be done before any Qt imports
if sys.platform == "win32":
    try:
        # Use unique App ID - this tells Windows this is NOT generic python.exe
        # Increment version to force Windows to refresh cached icon
        myappid = 'CushLabs.AIStockAlert.GUI.4.0'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except Exception:
        pass

# Fix DLL search path on Windows to avoid conflicts with Git's OpenSSL
if sys.platform == "win32":
    import contextlib
    from pathlib import Path as _Path

    # Add Anaconda's DLL directories before other paths
    base_prefix = _Path(sys.base_prefix)
    dll_paths = [
        base_prefix / "Library" / "bin",
        base_prefix / "DLLs",
        base_prefix,
    ]
    # Prepend to PATH environment variable
    current_path = os.environ.get("PATH", "")
    new_paths = [str(p) for p in dll_paths if p.exists()]
    os.environ["PATH"] = ";".join(new_paths) + ";" + current_path
    # Also use add_dll_directory for Python 3.8+
    for dll_path in new_paths:
        with contextlib.suppress(OSError, AttributeError):
            os.add_dll_directory(dll_path)

import argparse
from pathlib import Path


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        prog="stockalert",
        description="Stock price monitoring with Windows notifications",
    )
    parser.add_argument(
        "--tray",
        action="store_true",
        help="Start minimized to system tray",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Path to configuration file",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode",
    )
    parser.add_argument(
        "--service",
        action="store_true",
        help="Run as background monitoring service (no GUI)",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {get_version()}",
    )
    return parser.parse_args()


def get_version() -> str:
    """Get application version."""
    from stockalert import __version__

    return __version__


class InstanceLock:
    """Prevents multiple instances of the application from running.

    Uses a lock file with exclusive access on Windows.
    """

    def __init__(self, app_name: str = "StockAlert") -> None:
        """Initialize instance lock.

        Args:
            app_name: Application name for the lock file
        """
        self._app_name = app_name
        self._lock_file = None
        self._lock_path = Path(tempfile.gettempdir()) / f"{app_name}.lock"

    def acquire(self) -> bool:
        """Attempt to acquire the instance lock.

        Returns:
            True if lock acquired, False if another instance is running
        """
        try:
            # On Windows, opening with exclusive access prevents other processes
            if sys.platform == "win32":
                import msvcrt

                self._lock_file = open(self._lock_path, "w")
                msvcrt.locking(self._lock_file.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                # On Unix, use fcntl
                import fcntl

                self._lock_file = open(self._lock_path, "w")
                fcntl.flock(self._lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)

            # Write PID to lock file for debugging
            self._lock_file.write(str(os.getpid()))
            self._lock_file.flush()

            # Register cleanup on exit
            atexit.register(self.release)

            return True

        except (OSError, IOError):
            # Lock already held by another process
            if self._lock_file:
                self._lock_file.close()
                self._lock_file = None
            return False

    def release(self) -> None:
        """Release the instance lock."""
        if self._lock_file:
            try:
                if sys.platform == "win32":
                    import msvcrt

                    msvcrt.locking(self._lock_file.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    import fcntl

                    fcntl.flock(self._lock_file.fileno(), fcntl.LOCK_UN)

                self._lock_file.close()
                self._lock_path.unlink(missing_ok=True)
            except (OSError, IOError):
                pass
            finally:
                self._lock_file = None


def main() -> int:
    """Main entry point for StockAlert."""
    args = parse_args()

    # If --service flag is passed, run as headless monitoring service
    if args.service:
        from stockalert.service import run_foreground
        return run_foreground(config_path=args.config, debug=args.debug)

    # Check for existing GUI instance (separate from service)
    instance_lock = InstanceLock("StockAlertGUI")
    if not instance_lock.acquire():
        # Another instance is running - show message and exit
        print("StockAlert is already running.", file=sys.stderr)
        print("Check your system tray for the existing instance.", file=sys.stderr)

        # Try to show a GUI message if possible
        try:
            from PyQt6.QtWidgets import QApplication, QMessageBox

            temp_app = QApplication(sys.argv)
            QMessageBox.warning(
                None,
                "StockAlert Already Running",
                "Another instance of StockAlert is already running.\n\n"
                "Check your system tray for the existing instance.",
            )
            temp_app.quit()
        except Exception:
            pass  # Silently fail if GUI not available

        return 1

    # Set up logging early - write to file for debugging
    from pathlib import Path

    from stockalert.utils.logging_config import setup_logging

    # Log to file in same directory as executable (or project root in dev)
    if getattr(sys, "frozen", False):
        log_path = Path(sys.executable).parent / "stockalert.log"
    else:
        log_path = Path(__file__).parent.parent.parent / "stockalert.log"

    setup_logging(debug=args.debug, log_file=log_path)

    # Import app after logging is set up
    from stockalert.app import StockAlertApp

    # Create and run application
    app = StockAlertApp(
        config_path=args.config,
        start_minimized=args.tray,
        debug=args.debug,
    )

    return app.run()


if __name__ == "__main__":
    sys.exit(main())
