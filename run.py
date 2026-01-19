#!/usr/bin/env python
"""Quick run script for development."""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from stockalert.__main__ import main

if __name__ == "__main__":
    sys.exit(main())
