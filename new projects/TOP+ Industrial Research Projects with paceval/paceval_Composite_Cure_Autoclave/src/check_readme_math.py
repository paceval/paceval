#!/usr/bin/env python3
"""Required archive-wide Markdown math/links preflight, even when called from src."""
from pathlib import Path
import subprocess
import sys
root=Path(__file__).resolve().parents[1]
script=root/'scripts'/'check_markdown.py'
subprocess.run([sys.executable,str(script),*(sys.argv[1:] if len(sys.argv)>1 else [str(root)])],check=True)
