"""
Windows Service wrapper for StockAlert.

Provides functionality to install, remove, start, and stop
StockAlert as a Windows Service using pywin32.
"""

from __future__ import annotations

import logging
import os
import subprocess
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

# Service configuration
SERVICE_NAME = "StockAlertService"
SERVICE_DISPLAY_NAME = "StockAlert Monitoring Service"
SERVICE_DESCRIPTION = (
    "Monitors stock prices and sends alerts via Windows notifications, "
    "WhatsApp, and email. Configure via the StockAlert GUI application."
)


def _get_python_executable() -> str:
    """Get the path to the Python executable."""
    return sys.executable


def _get_service_script() -> str:
    """Get the path to the service script."""
    if getattr(sys, "frozen", False):
        # Running as compiled exe
        return str(Path(sys.executable).parent / "stockalert-service.exe")
    else:
        # Running from source
        return str(Path(__file__).resolve().parent.parent / "service.py")


def _run_command(args: list[str], check: bool = True) -> subprocess.CompletedProcess:
    """Run a command and return the result."""
    logger.debug(f"Running command: {' '.join(args)}")
    result = subprocess.run(
        args,
        capture_output=True,
        text=True,
    )
    if check and result.returncode != 0:
        logger.error(f"Command failed: {result.stderr}")
    return result


def is_admin() -> bool:
    """Check if running with administrator privileges."""
    try:
        import ctypes
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False


def get_service_status() -> str | None:
    """Get the current status of the Windows Service.

    Returns:
        Service status string ('running', 'stopped', 'pending', etc.)
        or None if service is not installed.
    """
    try:
        result = _run_command(
            ["sc", "query", SERVICE_NAME],
            check=False,
        )
        if result.returncode != 0:
            return None

        # Parse the output
        output = result.stdout.lower()
        if "running" in output:
            return "running"
        elif "stopped" in output:
            return "stopped"
        elif "start_pending" in output:
            return "starting"
        elif "stop_pending" in output:
            return "stopping"
        else:
            return "unknown"

    except Exception as e:
        logger.error(f"Failed to get service status: {e}")
        return None


def is_service_installed() -> bool:
    """Check if the Windows Service is installed."""
    return get_service_status() is not None


def install_service() -> int:
    """Install StockAlert as a Windows Service.

    Returns:
        0 on success, 1 on failure.
    """
    if not is_admin():
        logger.error("Administrator privileges required to install service")
        print("ERROR: Administrator privileges required.")
        print("Please run this command from an elevated command prompt.")
        return 1

    if is_service_installed():
        logger.warning("Service is already installed")
        print(f"Service '{SERVICE_NAME}' is already installed.")
        return 0

    try:
        # Determine the command to run
        if getattr(sys, "frozen", False):
            # Running as compiled exe - use the service exe directly
            bin_path = _get_service_script()
        else:
            # Running from source - use pythonw.exe to run without console
            python_exe = _get_python_executable()
            pythonw_exe = python_exe.replace("python.exe", "pythonw.exe")
            if not Path(pythonw_exe).exists():
                pythonw_exe = python_exe
            service_script = _get_service_script()
            bin_path = f'"{pythonw_exe}" "{service_script}"'

        # Create the service using sc command
        result = _run_command(
            [
                "sc", "create", SERVICE_NAME,
                f"binPath={bin_path}",
                f"DisplayName={SERVICE_DISPLAY_NAME}",
                "start=auto",  # Auto-start on boot
            ],
            check=False,
        )

        if result.returncode != 0:
            logger.error(f"Failed to create service: {result.stderr}")
            print(f"ERROR: Failed to create service: {result.stderr}")
            return 1

        # Set the service description
        _run_command(
            ["sc", "description", SERVICE_NAME, SERVICE_DESCRIPTION],
            check=False,
        )

        # Configure service recovery (restart on failure)
        _run_command(
            [
                "sc", "failure", SERVICE_NAME,
                "reset=86400",  # Reset failure count after 1 day
                "actions=restart/60000/restart/60000/restart/60000",  # Restart after 1 min
            ],
            check=False,
        )

        logger.info(f"Service '{SERVICE_NAME}' installed successfully")
        print(f"Service '{SERVICE_NAME}' installed successfully.")
        print("The service will start automatically on system boot.")
        print(f"To start now, run: python -m stockalert.service --start")
        return 0

    except Exception as e:
        logger.exception(f"Failed to install service: {e}")
        print(f"ERROR: Failed to install service: {e}")
        return 1


def remove_service() -> int:
    """Remove the StockAlert Windows Service.

    Returns:
        0 on success, 1 on failure.
    """
    if not is_admin():
        logger.error("Administrator privileges required to remove service")
        print("ERROR: Administrator privileges required.")
        print("Please run this command from an elevated command prompt.")
        return 1

    if not is_service_installed():
        logger.warning("Service is not installed")
        print(f"Service '{SERVICE_NAME}' is not installed.")
        return 0

    try:
        # Stop the service first if running
        status = get_service_status()
        if status == "running":
            print("Stopping service...")
            stop_service()

        # Delete the service
        result = _run_command(
            ["sc", "delete", SERVICE_NAME],
            check=False,
        )

        if result.returncode != 0:
            logger.error(f"Failed to delete service: {result.stderr}")
            print(f"ERROR: Failed to delete service: {result.stderr}")
            return 1

        logger.info(f"Service '{SERVICE_NAME}' removed successfully")
        print(f"Service '{SERVICE_NAME}' removed successfully.")
        return 0

    except Exception as e:
        logger.exception(f"Failed to remove service: {e}")
        print(f"ERROR: Failed to remove service: {e}")
        return 1


def start_service() -> int:
    """Start the StockAlert Windows Service.

    Returns:
        0 on success, 1 on failure.
    """
    if not is_service_installed():
        logger.error("Service is not installed")
        print(f"ERROR: Service '{SERVICE_NAME}' is not installed.")
        print("Run: python -m stockalert.service --install")
        return 1

    status = get_service_status()
    if status == "running":
        logger.info("Service is already running")
        print(f"Service '{SERVICE_NAME}' is already running.")
        return 0

    try:
        result = _run_command(
            ["sc", "start", SERVICE_NAME],
            check=False,
        )

        if result.returncode != 0:
            logger.error(f"Failed to start service: {result.stderr}")
            print(f"ERROR: Failed to start service: {result.stderr}")
            return 1

        logger.info(f"Service '{SERVICE_NAME}' started")
        print(f"Service '{SERVICE_NAME}' started successfully.")
        return 0

    except Exception as e:
        logger.exception(f"Failed to start service: {e}")
        print(f"ERROR: Failed to start service: {e}")
        return 1


def stop_service() -> int:
    """Stop the StockAlert Windows Service.

    Returns:
        0 on success, 1 on failure.
    """
    if not is_service_installed():
        logger.error("Service is not installed")
        print(f"ERROR: Service '{SERVICE_NAME}' is not installed.")
        return 1

    status = get_service_status()
    if status == "stopped":
        logger.info("Service is already stopped")
        print(f"Service '{SERVICE_NAME}' is already stopped.")
        return 0

    try:
        result = _run_command(
            ["sc", "stop", SERVICE_NAME],
            check=False,
        )

        if result.returncode != 0:
            logger.error(f"Failed to stop service: {result.stderr}")
            print(f"ERROR: Failed to stop service: {result.stderr}")
            return 1

        logger.info(f"Service '{SERVICE_NAME}' stopped")
        print(f"Service '{SERVICE_NAME}' stopped successfully.")
        return 0

    except Exception as e:
        logger.exception(f"Failed to stop service: {e}")
        print(f"ERROR: Failed to stop service: {e}")
        return 1


def restart_service() -> int:
    """Restart the StockAlert Windows Service.

    Returns:
        0 on success, 1 on failure.
    """
    stop_result = stop_service()
    if stop_result != 0 and get_service_status() != "stopped":
        return stop_result

    # Wait a moment for the service to fully stop
    import time
    time.sleep(2)

    return start_service()


# Alternative: Run as a background process (not a Windows Service)
# This is simpler and doesn't require admin privileges

def start_background_process() -> int:
    """Start StockAlert as a background process (not a Windows Service).

    This is an alternative for users who don't want to install a Windows Service.
    The process will run until the system restarts or it's manually stopped.

    Returns:
        Process ID on success, -1 on failure.
    """
    try:
        if getattr(sys, "frozen", False):
            # Running as compiled exe
            cmd = [_get_service_script()]
        else:
            # Running from source
            python_exe = _get_python_executable()
            pythonw_exe = python_exe.replace("python.exe", "pythonw.exe")
            if not Path(pythonw_exe).exists():
                pythonw_exe = python_exe
            service_script = _get_service_script()
            cmd = [pythonw_exe, service_script]

        # Start the process detached from this console
        if sys.platform == "win32":
            # Windows-specific: use CREATE_NO_WINDOW flag
            CREATE_NO_WINDOW = 0x08000000
            process = subprocess.Popen(
                cmd,
                creationflags=CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS,
                start_new_session=True,
            )
        else:
            process = subprocess.Popen(
                cmd,
                start_new_session=True,
            )

        logger.info(f"Background process started with PID {process.pid}")
        print(f"StockAlert monitoring started (PID: {process.pid})")

        # Save PID to file for later reference
        pid_file = Path(__file__).resolve().parent.parent.parent / "stockalert.pid"
        pid_file.write_text(str(process.pid))

        return process.pid

    except Exception as e:
        logger.exception(f"Failed to start background process: {e}")
        print(f"ERROR: Failed to start background process: {e}")
        return -1


def stop_background_process() -> int:
    """Stop the StockAlert background process.

    Returns:
        0 on success, 1 on failure.
    """
    pid_file = Path(__file__).resolve().parent.parent.parent / "stockalert.pid"

    if not pid_file.exists():
        print("No background process found (PID file missing)")
        return 1

    try:
        pid = int(pid_file.read_text().strip())

        # Try to terminate the process
        if sys.platform == "win32":
            subprocess.run(["taskkill", "/PID", str(pid), "/F"], check=False)
        else:
            os.kill(pid, 15)  # SIGTERM

        pid_file.unlink()
        print(f"Stopped background process (PID: {pid})")
        return 0

    except (ValueError, ProcessLookupError, PermissionError) as e:
        logger.error(f"Failed to stop background process: {e}")
        print(f"ERROR: Failed to stop background process: {e}")
        # Clean up stale PID file
        if pid_file.exists():
            pid_file.unlink()
        return 1


def get_background_process_status() -> dict:
    """Get the status of the background process.

    Returns:
        Dictionary with 'running' bool and optional 'pid' int.
    """
    pid_file = Path(__file__).resolve().parent.parent.parent / "stockalert.pid"

    if not pid_file.exists():
        return {"running": False}

    try:
        pid = int(pid_file.read_text().strip())

        # Check if process is running
        if sys.platform == "win32":
            result = subprocess.run(
                ["tasklist", "/FI", f"PID eq {pid}"],
                capture_output=True,
                text=True,
            )
            if str(pid) in result.stdout:
                return {"running": True, "pid": pid}
        else:
            try:
                os.kill(pid, 0)  # Check if process exists
                return {"running": True, "pid": pid}
            except ProcessLookupError:
                pass

        # Process not running, clean up stale PID file
        pid_file.unlink()
        return {"running": False}

    except (ValueError, OSError):
        return {"running": False}
