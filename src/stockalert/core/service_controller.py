"""
Service controller for StockAlert GUI.

Provides a clean interface for the GUI to control the background
monitoring service (either as a Windows Service or background process).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Callable

from stockalert.core.windows_service import (
    get_background_process_status,
    get_service_status,
    is_admin,
    is_service_installed,
    restart_service,
    start_background_process,
    start_service,
    stop_background_process,
    stop_service,
)

logger = logging.getLogger(__name__)


class ServiceMode(Enum):
    """Mode for running the monitoring service."""
    WINDOWS_SERVICE = "service"  # Run as Windows Service (requires admin to install)
    BACKGROUND_PROCESS = "process"  # Run as background process (no admin required)
    EMBEDDED = "embedded"  # Run embedded in GUI (legacy mode)


class ServiceStatus(Enum):
    """Status of the monitoring service."""
    RUNNING = "running"
    STOPPED = "stopped"
    STARTING = "starting"
    STOPPING = "stopping"
    NOT_INSTALLED = "not_installed"
    UNKNOWN = "unknown"


@dataclass
class ServiceState:
    """Current state of the service."""
    status: ServiceStatus
    mode: ServiceMode | None = None
    pid: int | None = None
    message: str = ""


class ServiceController:
    """Controller for managing the StockAlert monitoring service."""

    def __init__(self, on_status_changed: Callable[[ServiceState], None] | None = None) -> None:
        """Initialize the service controller.

        Args:
            on_status_changed: Callback when service status changes
        """
        self._on_status_changed = on_status_changed
        self._preferred_mode = ServiceMode.BACKGROUND_PROCESS

    @property
    def preferred_mode(self) -> ServiceMode:
        """Get the preferred service mode."""
        return self._preferred_mode

    @preferred_mode.setter
    def preferred_mode(self, mode: ServiceMode) -> None:
        """Set the preferred service mode."""
        self._preferred_mode = mode

    def get_state(self) -> ServiceState:
        """Get the current service state.

        Checks both Windows Service and background process.

        Returns:
            ServiceState with current status.
        """
        # First check Windows Service
        if is_service_installed():
            status_str = get_service_status()
            status_map = {
                "running": ServiceStatus.RUNNING,
                "stopped": ServiceStatus.STOPPED,
                "starting": ServiceStatus.STARTING,
                "stopping": ServiceStatus.STOPPING,
            }
            status = status_map.get(status_str, ServiceStatus.UNKNOWN)
            return ServiceState(
                status=status,
                mode=ServiceMode.WINDOWS_SERVICE,
                message=f"Windows Service: {status_str}",
            )

        # Check background process
        proc_status = get_background_process_status()
        if proc_status.get("running"):
            return ServiceState(
                status=ServiceStatus.RUNNING,
                mode=ServiceMode.BACKGROUND_PROCESS,
                pid=proc_status.get("pid"),
                message=f"Background process: PID {proc_status.get('pid')}",
            )

        return ServiceState(
            status=ServiceStatus.STOPPED,
            mode=None,
            message="Service not running",
        )

    def is_running(self) -> bool:
        """Check if the service is currently running."""
        state = self.get_state()
        return state.status == ServiceStatus.RUNNING

    def start(self, mode: ServiceMode | None = None) -> tuple[bool, str]:
        """Start the monitoring service.

        Args:
            mode: Mode to use (defaults to preferred_mode)

        Returns:
            Tuple of (success, message)
        """
        mode = mode or self._preferred_mode

        # Check if already running
        state = self.get_state()
        if state.status == ServiceStatus.RUNNING:
            return True, "Service is already running"

        logger.info(f"Starting service in {mode.value} mode")

        if mode == ServiceMode.WINDOWS_SERVICE:
            if not is_service_installed():
                return False, "Windows Service not installed. Run with --install first."
            result = start_service()
            success = result == 0
            message = "Service started" if success else "Failed to start service"

        elif mode == ServiceMode.BACKGROUND_PROCESS:
            pid = start_background_process()
            success = pid > 0
            message = f"Background process started (PID: {pid})" if success else "Failed to start process"

        else:
            return False, "Embedded mode should be controlled by the GUI directly"

        if success:
            new_state = self.get_state()
            if self._on_status_changed:
                self._on_status_changed(new_state)

        return success, message

    def stop(self) -> tuple[bool, str]:
        """Stop the monitoring service.

        Stops whichever mode is currently running.

        Returns:
            Tuple of (success, message)
        """
        state = self.get_state()

        if state.status != ServiceStatus.RUNNING:
            return True, "Service is not running"

        logger.info(f"Stopping service (mode: {state.mode})")

        if state.mode == ServiceMode.WINDOWS_SERVICE:
            result = stop_service()
            success = result == 0
            message = "Service stopped" if success else "Failed to stop service"

        elif state.mode == ServiceMode.BACKGROUND_PROCESS:
            result = stop_background_process()
            success = result == 0
            message = "Process stopped" if success else "Failed to stop process"

        else:
            return False, "Unknown service mode"

        if success:
            new_state = self.get_state()
            if self._on_status_changed:
                self._on_status_changed(new_state)

        return success, message

    def restart(self) -> tuple[bool, str]:
        """Restart the monitoring service.

        Returns:
            Tuple of (success, message)
        """
        state = self.get_state()

        if state.status != ServiceStatus.RUNNING:
            # Not running, just start
            return self.start()

        logger.info(f"Restarting service (mode: {state.mode})")

        if state.mode == ServiceMode.WINDOWS_SERVICE:
            result = restart_service()
            success = result == 0
            message = "Service restarted" if success else "Failed to restart service"

        elif state.mode == ServiceMode.BACKGROUND_PROCESS:
            # Stop then start
            stop_result = stop_background_process()
            if stop_result == 0:
                import time
                time.sleep(1)
                pid = start_background_process()
                success = pid > 0
                message = f"Process restarted (PID: {pid})" if success else "Failed to restart process"
            else:
                success = False
                message = "Failed to stop process for restart"

        else:
            return False, "Unknown service mode"

        if success:
            new_state = self.get_state()
            if self._on_status_changed:
                self._on_status_changed(new_state)

        return success, message

    def can_use_windows_service(self) -> bool:
        """Check if Windows Service mode is available.

        Returns:
            True if Windows Service is installed or user is admin.
        """
        return is_service_installed() or is_admin()

    def get_status_display(self) -> str:
        """Get a human-readable status string.

        Returns:
            Status string for display in UI.
        """
        state = self.get_state()

        status_text = {
            ServiceStatus.RUNNING: "Running",
            ServiceStatus.STOPPED: "Stopped",
            ServiceStatus.STARTING: "Starting...",
            ServiceStatus.STOPPING: "Stopping...",
            ServiceStatus.NOT_INSTALLED: "Not Installed",
            ServiceStatus.UNKNOWN: "Unknown",
        }

        text = status_text.get(state.status, "Unknown")

        if state.mode == ServiceMode.WINDOWS_SERVICE:
            text += " (Windows Service)"
        elif state.mode == ServiceMode.BACKGROUND_PROCESS and state.pid:
            text += f" (PID: {state.pid})"

        return text
