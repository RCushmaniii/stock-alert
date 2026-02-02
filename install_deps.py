"""Install missing dependencies."""
import subprocess
import sys
from pathlib import Path

# Get venv pip path
project_root = Path(__file__).parent
pip_path = project_root / "venv" / "Scripts" / "pip.exe"

print(f"Installing windows-toasts using {pip_path}...")
result = subprocess.run([str(pip_path), "install", "windows-toasts"], capture_output=True, text=True)
print(result.stdout)
if result.stderr:
    print(result.stderr)
print(f"Return code: {result.returncode}")
