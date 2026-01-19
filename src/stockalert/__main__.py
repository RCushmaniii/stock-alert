"""
StockAlert entry point.

Usage:
    python -m stockalert          # Start the GUI application
    python -m stockalert --tray   # Start minimized to system tray
    python -m stockalert --help   # Show help
"""

from __future__ import annotations

import argparse
import sys
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
        "--version",
        action="version",
        version=f"%(prog)s {get_version()}",
    )
    return parser.parse_args()


def get_version() -> str:
    """Get application version."""
    from stockalert import __version__

    return __version__


def main() -> int:
    """Main entry point for StockAlert."""
    args = parse_args()

    # Set up logging early
    from stockalert.utils.logging_config import setup_logging

    setup_logging(debug=args.debug)

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
