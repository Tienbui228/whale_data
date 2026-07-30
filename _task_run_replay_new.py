#!/usr/bin/env python3
"""Chạy suite gốc replay.py tại D:\Data back test\binance-bot-signals\ (canonical sau B5)."""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import subprocess
from pathlib import Path

REPO = Path(r"D:\Data back test\binance-bot-signals")
CASE_DIR = REPO / "docs" / "case study"
REPLAY = REPO / "replay.py"

print(f"repo:     {REPO}")
print(f"case_dir: {CASE_DIR}")
print(f"replay:   {REPLAY}")
print(f"case dir exists: {CASE_DIR.is_dir()}")
print(f"replay exists:   {REPLAY.is_file()}")
print()

result_files = sorted(CASE_DIR.glob("*_result.txt"))
print(f"case files found ({len(result_files)}):")
for f in result_files:
    print(f"  {f.name}")
print()

r = subprocess.run(
    [sys.executable, str(REPLAY), str(CASE_DIR)],
    capture_output=True, text=True,
    cwd=str(REPO),
    encoding="utf-8", errors="replace"
)
print("=== STDOUT ===")
print(r.stdout)
if r.stderr:
    print("=== STDERR ===")
    print(r.stderr[:2000])
print(f"exit code: {r.returncode}")
