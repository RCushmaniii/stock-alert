"""
Logging configuration for StockAlert.

Sets up structured logging with console and optional file handlers.
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path


def setup_logging(
    debug: bool = False,
    log_file: Path | str | None = None,
) -> None:
    """Set up application logging.

    Args:
        debug: If True, set log level to DEBUG
        log_file: Optional path to log file
    """
    # Determine log level
    level_str = os.environ.get("LOG_LEVEL", "DEBUG" if debug else "INFO")
    level = getattr(logging, level_str.upper(), logging.INFO)

    # Create formatter
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Remove existing handlers
    root_logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File handler (optional)
    log_file_path = log_file or os.environ.get("LOG_FILE")
    if log_file_path:
        file_handler = logging.FileHandler(log_file_path, encoding="utf-8")
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    # Reduce noise from third-party libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("finnhub").setLevel(logging.WARNING)

    logging.debug(f"Logging configured: level={level_str}, file={log_file_path}")
