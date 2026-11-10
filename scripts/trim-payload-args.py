#!/usr/bin/env python3
"""Trim [payload] kernel_args in a board.toml copy for the console-only bring-up.

The console profile kernel has no UFS / PMGR / graphics / HID integration, so the
payload validation refuses the full argument set. Keep only the arguments the
console kernel understands.
"""
import re
import sys
from pathlib import Path

PATH = Path(sys.argv[1] if len(sys.argv) > 1 else "board.toml")
MINIMAL = '''kernel_args = [
  "-v",
  "debug=0x14e",
  "cpus=8",
  "armcpu-timer-intid=19",
  "pcpu=0xf0",
  "fajita-wdog=3",
]'''

text = PATH.read_text()
pattern = re.compile(r"kernel_args = \[.*?\n\]", re.S)
if not pattern.search(text):
    raise SystemExit("kernel_args block not found")
text = pattern.sub(MINIMAL, text, count=1)
text = text.replace("panic_screen = true", "panic_screen = false")
PATH.write_text(text)
print(f"trimmed kernel_args in {PATH}")
