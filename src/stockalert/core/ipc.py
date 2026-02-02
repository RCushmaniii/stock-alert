"""
Inter-Process Communication (IPC) module for StockAlert.

Uses Windows Named Pipes (via pywin32) for reliable communication between
the Frontend (GUI) and Backend (Service).

Architecture:
- Backend creates a Mutex (single instance) + Named Pipe server
- Frontend connects to Named Pipe to communicate with Backend
"""

from __future__ import annotations

import json
import logging
import os
import threading
import time
from typing import Any, Callable

import win32api
import win32event
import win32file
import win32pipe
import winerror

logger = logging.getLogger(__name__)

# Named Pipe and Mutex names
# The pipe prefix \\.\pipe\ is mandatory on Windows
# Build the string to ensure correct escaping: \\.\pipe\name
PIPE_NAME = "\\\\" + "." + "\\" + "pipe" + "\\" + "StockAlertServicePipe"
# Local\ for current user session (no admin required)
MUTEX_NAME = "Local" + "\\" + "StockAlertServiceMutex"
BUFFER_SIZE = 4096


class ServiceMutex:
    """Global Mutex for ensuring single service instance using pywin32."""

    def __init__(self) -> None:
        self._handle = None

    def acquire(self) -> bool:
        """Try to acquire the mutex.

        Returns:
            True if acquired (we're the only instance),
            False if another instance holds it.
        """
        try:
            # Create a named mutex
            # If it already exists, GetLastError() returns ERROR_ALREADY_EXISTS
            self._handle = win32event.CreateMutex(None, False, MUTEX_NAME)
            last_error = win32api.GetLastError()

            if last_error == winerror.ERROR_ALREADY_EXISTS:
                # Another instance has the mutex
                logger.info(f"Mutex already exists: {MUTEX_NAME}")
                if self._handle:
                    win32api.CloseHandle(self._handle)
                    self._handle = None
                return False

            logger.info(f"Acquired service mutex: {MUTEX_NAME}")
            return True

        except Exception as e:
            logger.exception(f"Failed to acquire mutex: {e}")
            return False

    def release(self) -> None:
        """Release the mutex."""
        if self._handle:
            try:
                win32api.CloseHandle(self._handle)
                logger.info("Released service mutex")
            except Exception as e:
                logger.exception(f"Failed to release mutex: {e}")
            finally:
                self._handle = None


class NamedPipeServer:
    """Named Pipe server for the Backend service using pywin32."""

    def __init__(self, on_command: Callable[[str], str]) -> None:
        """Initialize the pipe server.

        Args:
            on_command: Callback to handle incoming commands. Takes command string, returns response string.
        """
        self._on_command = on_command
        self._running = False
        self._thread: threading.Thread | None = None

    def start(self) -> bool:
        """Start the pipe server in a background thread."""
        if self._running:
            return True

        self._running = True
        self._thread = threading.Thread(target=self._server_loop, daemon=True)
        self._thread.start()
        logger.info(f"Named pipe server started: {PIPE_NAME}")
        return True

    def stop(self) -> None:
        """Stop the pipe server."""
        self._running = False

        # Connect to our own pipe to unblock WaitForConnection
        try:
            handle = win32file.CreateFile(
                PIPE_NAME,
                win32file.GENERIC_READ | win32file.GENERIC_WRITE,
                0,
                None,
                win32file.OPEN_EXISTING,
                0,
                None,
            )
            win32file.CloseHandle(handle)
        except Exception:
            pass

        if self._thread:
            self._thread.join(timeout=2.0)
            self._thread = None

        logger.info("Named pipe server stopped")

    def _server_loop(self) -> None:
        """Main server loop - accepts connections and handles commands."""
        logger.info(f"IPC: Listening on {PIPE_NAME}")

        while self._running:
            h_pipe = None
            try:
                # 1. Create the Named Pipe Instance
                h_pipe = win32pipe.CreateNamedPipe(
                    PIPE_NAME,
                    win32pipe.PIPE_ACCESS_DUPLEX,
                    win32pipe.PIPE_TYPE_MESSAGE | win32pipe.PIPE_READMODE_MESSAGE | win32pipe.PIPE_WAIT,
                    win32pipe.PIPE_UNLIMITED_INSTANCES,
                    BUFFER_SIZE,
                    BUFFER_SIZE,
                    0,
                    None,
                )

                # 2. Block until a client connects
                win32pipe.ConnectNamedPipe(h_pipe, None)

                if not self._running:
                    break

                # 3. Read the command
                result, data = win32file.ReadFile(h_pipe, BUFFER_SIZE)
                command = data.decode("utf-8").strip()
                logger.debug(f"IPC: Received command '{command}'")

                # 4. Process the command
                response = self._on_command(command)

                # 5. Send Response
                win32file.WriteFile(h_pipe, response.encode("utf-8"))

            except Exception as e:
                if self._running:
                    logger.debug(f"IPC Error: {e}")
            finally:
                # 6. Close the handle to reset the pipe instance
                if h_pipe:
                    try:
                        win32pipe.DisconnectNamedPipe(h_pipe)
                        win32file.CloseHandle(h_pipe)
                    except Exception:
                        pass


def send_command(command: str, timeout_ms: int = 1000) -> str | None:
    """Send a command to the service and get the response.

    Args:
        command: Command string to send.
        timeout_ms: Timeout in milliseconds.

    Returns:
        Response string, or None if service not available.
    """
    try:
        # Wait for the pipe to be available
        # Note: WaitNamedPipe returns None on success, raises exception on failure
        try:
            win32pipe.WaitNamedPipe(PIPE_NAME, timeout_ms)
        except Exception as e:
            error_code = getattr(e, "winerror", 0)
            if error_code == 2:  # ERROR_FILE_NOT_FOUND - pipe doesn't exist
                return None
            # For other errors (like timeout), try to connect anyway
            logger.debug(f"WaitNamedPipe warning: {e}")

        # Open the Named Pipe
        handle = win32file.CreateFile(
            PIPE_NAME,
            win32file.GENERIC_READ | win32file.GENERIC_WRITE,
            0,
            None,
            win32file.OPEN_EXISTING,
            0,
            None,
        )

        try:
            # Set to message mode
            win32pipe.SetNamedPipeHandleState(
                handle,
                win32pipe.PIPE_READMODE_MESSAGE,
                None,
                None,
            )

            # Send Command
            win32file.WriteFile(handle, command.encode("utf-8"))

            # Read Response
            result, data = win32file.ReadFile(handle, BUFFER_SIZE)
            return data.decode("utf-8")

        finally:
            win32file.CloseHandle(handle)

    except Exception as e:
        # If the pipe is not found (2) or busy, service isn't running
        error_code = getattr(e, "winerror", 0)
        if error_code == 2:  # ERROR_FILE_NOT_FOUND
            return None
        logger.debug(f"IPC send_command error: {e}")
        return None


def is_service_running() -> bool:
    """Check if the background service is running by pinging its pipe.

    Returns:
        True if service is running and responsive.
    """
    response = send_command("PING", timeout_ms=500)
    return response == "PONG"


def get_service_status() -> dict[str, Any]:
    """Get detailed status from the service.

    Returns:
        Status dict with 'running', 'pid', etc.
    """
    response = send_command("STATUS", timeout_ms=500)
    if response:
        try:
            data = json.loads(response)
            data["running"] = True
            return data
        except json.JSONDecodeError:
            if response == "RUNNING":
                return {"running": True}
    return {"running": False}


def send_reload_config() -> bool:
    """Tell the service to reload its configuration.

    Returns:
        True if successful.
    """
    response = send_command("RELOAD_SETTINGS", timeout_ms=1000)
    return response is not None and "SUCCESS" in response


def send_stop_service() -> bool:
    """Tell the service to stop.

    Returns:
        True if successful.
    """
    response = send_command("STOP", timeout_ms=1000)
    return response is not None and "SUCCESS" in response
