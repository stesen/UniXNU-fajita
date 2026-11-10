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
  "offline-legacy-register=1",
  "offline-legacy-phase=4",
  "offline-legacy-gop=1",
  "offline-legacy-pm=1",
  "offline-legacy-validate=1",
  "offline-legacy-transfer=1",
  "offline-legacy-cpu-present=1",
  "offline-legacy-unit-scale=2",
  "fajita-display-logical=2048x2732",
  "fajita-fb-wc=1",
  "fajita-fb-src-cached=1",
  "sheng-fb-diff=1",
  "sheng-vsync=60",
  "sheng-banner=0",
]'''

text = PATH.read_text()
pattern = re.compile(r"kernel_args = \[.*?\n\]", re.S)
if not pattern.search(text):
    raise SystemExit("kernel_args block not found")
text = pattern.sub(MINIMAL, text, count=1)
text = text.replace("panic_screen = true", "panic_screen = false")
PATH.write_text(text)
print(f"trimmed kernel_args in {PATH}")
