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
APP_DATA_FOLDER = "StockAlert"


def get_app_data_dir() -> Path:
    """Get the application data directory for StockAlert.

    Returns:
        Path to %APPDATA%/StockAlert (created if doesn't exist)
    """
    if sys.platform == "win32":
        app_data = Path(os.environ.get("APPDATA", ""))
        if app_data.exists():
            stockalert_dir = app_data / APP_DATA_FOLDER
        else:
            # Fallback to user home
            stockalert_dir = Path.home() / ".stockalert"
    else:
        stockalert_dir = Path.home() / ".stockalert"

    stockalert_dir.mkdir(parents=True, exist_ok=True)
    return stockalert_dir


def get_pid_file_path() -> Path:
    """Get the path to the PID file.

    Returns:
        Path to the PID file in the app data directory.
    """
    return get_app_data_dir() / "stockalert.pid"
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
        # Running as compiled exe - use main exe with --service flag
        return sys.executable
    else:
        # Running from source
        return str(Path(__file__).resolve().parent.parent / "service.py")


def _run_command(args: list[str], check: bool = True) -> subprocess.CompletedProcess:
    """Run a command and return the result."""
    logger.debug(f"Running command: {' '.join(args)}")
    # Use CREATE_NO_WINDOW to prevent console window flashing on Windows
    creationflags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
    result = subprocess.run(
        args,
        capture_output=True,
        text=True,
        creationflags=creationflags,
    )
    if check and result.returncode != 0:
        logger.error(f"Command failed: {result.stderr}")
    return result


def is_admin() -> bool:
    """Check if running with administrator privileges."""
    try:
        import ctypes
        return bool(ctypes.windll.shell32.IsUserAnAdmin() != 0)
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
        print("To start now, run: python -m stockalert.service --start")
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
        Process ID on success, -1 on failure, existing PID if already running.
    """
    # Check if already running to prevent duplicates
    status = get_background_process_status()
    if status.get("running"):
        existing_pid = status.get("pid", -1)
        logger.info(f"Background process already running (PID: {existing_pid})")
        print(f"StockAlert monitoring already running (PID: {existing_pid})")
        return existing_pid

    try:
        if getattr(sys, "frozen", False):
            # Running as compiled exe - use main exe with --service flag
            cmd = [_get_service_script(), "--service"]
            cwd = None
            env = None
            logger.info(f"Starting service (frozen): cmd={cmd}")
        else:
            # Running from source - use module invocation for correct imports
            # Use python.exe (not pythonw.exe) - CREATE_NO_WINDOW flag hides console
            python_exe = _get_python_executable()

            # Run as module: python -m stockalert.service
            cmd = [python_exe, "-m", "stockalert.service"]

            # Set working directory to src folder for correct module resolution
            src_dir = Path(__file__).resolve().parent.parent.parent
            cwd = str(src_dir)

            # Copy environment and ensure PYTHONPATH includes src
            env = os.environ.copy()

            logger.info(f"Starting service (source): cmd={cmd}, cwd={cwd}")

        # Start the process detached from this console
        if sys.platform == "win32":
            # Windows-specific: use CREATE_NO_WINDOW flag
            CREATE_NO_WINDOW = 0x08000000
            process = subprocess.Popen(
                cmd,
                cwd=cwd,
                env=env,
                creationflags=CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS,
                start_new_session=True,
            )
        else:
            process = subprocess.Popen(
                cmd,
                cwd=cwd,
                env=env,
                start_new_session=True,
            )

        logger.info(f"Background process started with PID {process.pid}")
        print(f"StockAlert monitoring started (PID: {process.pid})")

        # Save PID to file for later reference
        pid_file = get_pid_file_path()
        pid_file.write_text(str(process.pid))
        logger.info(f"PID file written: {pid_file}")

        # Give process a moment to start and check if it's still running
        import time
        time.sleep(0.5)

        # Verify process is actually running
        poll_result = process.poll()
        if poll_result is not None:
            logger.error(f"Service process exited immediately with code {poll_result}")
            print(f"ERROR: Service process exited with code {poll_result}")
            # Clean up PID file since process died
            if pid_file.exists():
                pid_file.unlink()
            return -1

        logger.info(f"Service process verified running (PID: {process.pid})")
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
    pid_file = get_pid_file_path()

    if not pid_file.exists():
        print("No background process found (PID file missing)")
        return 1

    try:
        pid = int(pid_file.read_text().strip())

        # Try to terminate the process
        if sys.platform == "win32":
            subprocess.run(
                ["taskkill", "/PID", str(pid), "/F"],
                check=False,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
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
    pid_file = get_pid_file_path()

    if not pid_file.exists():
        # Also check for any running StockAlert processes without PID file
        return _find_stockalert_process()

    try:
        pid = int(pid_file.read_text().strip())

        # Check if process is running AND is actually StockAlert
        if sys.platform == "win32":
            result = subprocess.run(
                ["tasklist", "/FI", f"PID eq {pid}", "/V", "/FO", "CSV"],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            # Check if it's a python/stockalert process
            output = result.stdout.lower()
            if str(pid) in output and ("python" in output or "stockalert" in output):
                return {"running": True, "pid": pid}
        else:
            try:
                os.kill(pid, 0)  # Check if process exists
                return {"running": True, "pid": pid}
            except ProcessLookupError:
                pass

        # PID file exists but process not running, clean up stale PID file
        logger.info(f"Cleaning up stale PID file (PID {pid} not running)")
        pid_file.unlink()

        # Check if there's another StockAlert process running
        return _find_stockalert_process()

    except (ValueError, OSError):
        return {"running": False}


def _find_stockalert_process() -> dict:
    """Find any running StockAlert background process.

    This is a fallback when PID file is missing/stale.

    Returns:
        Dictionary with 'running' bool and optional 'pid' int.
    """
    if sys.platform != "win32":
        return {"running": False}

    try:
        # Use WMIC to find pythonw processes running stockalert.service
        result = subprocess.run(
            ["wmic", "process", "where",
             "name='pythonw.exe' or name='StockAlert-Service.exe'",
             "get", "processid,commandline", "/format:csv"],
            capture_output=True,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )

        # Debug: log raw WMIC output
        logger.debug(f"WMIC output (returncode={result.returncode}): {repr(result.stdout)}")

        for line in result.stdout.splitlines():
            line_stripped = line.strip()
            if not line_stripped or line_stripped.startswith("Node"):
                continue  # Skip empty lines and header

            line_lower = line_stripped.lower()
            # Look specifically for "-m stockalert.service" module invocation
            # This avoids matching other scripts that just mention "stockalert"
            if "-m stockalert.service" in line_lower or "stockalert-service.exe" in line_lower:
                # Extract PID (last field in CSV)
                parts = line.strip().split(",")
                if parts and parts[-1].isdigit():
                    pid = int(parts[-1])
                    logger.info(f"Found orphan StockAlert service process: PID {pid}")
                    # Update PID file
                    pid_file = get_pid_file_path()
                    pid_file.write_text(str(pid))
                    return {"running": True, "pid": pid}

        return {"running": False}

    except Exception as e:
        logger.debug(f"Error finding StockAlert process: {e}")
        return {"running": False}


def get_startup_folder() -> Path:
    """Get the Windows Startup folder path.

    Returns:
        Path to the user's Startup folder
    """
    if sys.platform == "win32":
        startup = Path(os.environ.get("APPDATA", "")) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
        return startup
    return Path.home()


def is_autostart_enabled() -> bool:
    """Check if StockAlert is configured to start with Windows.

    Returns:
        True if autostart is enabled
    """
    startup_folder = get_startup_folder()
    shortcut_path = startup_folder / "StockAlert.lnk"
    return shortcut_path.exists()


def enable_autostart() -> tuple[bool, str]:
    """Enable StockAlert to start automatically with Windows.

    Creates a shortcut in the Windows Startup folder (no admin required).
    Uses VBS script for source installs to avoid showing console window.

    Returns:
        Tuple of (success, message)
    """
    try:
        startup_folder = get_startup_folder()
        if not startup_folder.exists():
            return False, f"Startup folder not found: {startup_folder}"

        shortcut_path = startup_folder / "StockAlert.lnk"

        # Get the path to the service
        if getattr(sys, "frozen", False):
            # Running as compiled exe - use the service exe directly
            target_path = Path(sys.executable).parent / "StockAlert-Service.exe"
            if not target_path.exists():
                target_path = Path(sys.executable)
            arguments = "--service"
            working_dir = str(target_path.parent)
        else:
            # Running from source - use VBS script to avoid console window
            vbs_path = _create_service_batch_file()
            target_path = Path("wscript.exe")
            arguments = f'"{vbs_path}"'
            working_dir = str(vbs_path.parent)

        # Create Windows shortcut using PowerShell (no admin required)
        ps_script = f'''
$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("{shortcut_path}")
$Shortcut.TargetPath = "{target_path}"
$Shortcut.Arguments = "{arguments}"
$Shortcut.WorkingDirectory = "{working_dir}"
$Shortcut.Description = "StockAlert Background Service"
$Shortcut.WindowStyle = 7
$Shortcut.Save()
'''
        result = subprocess.run(
            ["powershell", "-Command", ps_script],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0:
            logger.info(f"Created autostart shortcut at {shortcut_path}")
            return True, "StockAlert will now start automatically with Windows"
        else:
            logger.error(f"Failed to create shortcut: {result.stderr}")
            return False, f"Failed to create shortcut: {result.stderr}"

    except Exception as e:
        logger.exception(f"Error enabling autostart: {e}")
        return False, str(e)


def disable_autostart() -> tuple[bool, str]:
    """Disable StockAlert from starting automatically with Windows.

    Removes the shortcut from the Windows Startup folder.

    Returns:
        Tuple of (success, message)
    """
    try:
        startup_folder = get_startup_folder()
        shortcut_path = startup_folder / "StockAlert.lnk"

        if shortcut_path.exists():
            shortcut_path.unlink()
            logger.info(f"Removed autostart shortcut from {shortcut_path}")
            return True, "StockAlert will no longer start automatically with Windows"
        else:
            return True, "Autostart was not enabled"

    except Exception as e:
        logger.exception(f"Error disabling autostart: {e}")
        return False, str(e)


def _create_service_batch_file() -> Path:
    """Create a VBS script to run the service from source without console.

    Returns:
        Path to the VBS script
    """
    app_data = get_app_data_dir()
    vbs_path = app_data / "start_service.vbs"

    # Find pythonw.exe (no console) and source directory
    python_exe = sys.executable
    pythonw_exe = python_exe.replace("python.exe", "pythonw.exe")
    if not Path(pythonw_exe).exists():
        pythonw_exe = python_exe  # Fallback

    src_dir = Path(__file__).parent.parent.parent  # stockalert package root

    # Use VBS to run without any window at all
    vbs_content = f'''Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "{src_dir}"
WshShell.Run """{pythonw_exe}"" -m stockalert.service", 0, False
'''
    vbs_path.write_text(vbs_content)
    logger.info(f"Created service VBS script at {vbs_path}")
    return vbs_path
