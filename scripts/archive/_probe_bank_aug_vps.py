# -*- coding: utf-8 -*-
"""VPS-side: grep BANK freshwatch data 01-05/08 from export files."""
import subprocess, os, glob

EXPORT_DIRS = [
    "/root/Data_back_test/whale_data/exports",
    "/root/Data_back_test/whale_data/data/exports",
    "/root/Data_back_test/whale_data/data/raw/freshwatch",
    "/root/freshwatch_exports",
]

def p(s):
    print(s)

p("=== BANK freshwatch search ===")

# Find export files
found_dirs = []
for d in EXPORT_DIRS:
    if os.path.isdir(d):
        p(f"DIR EXISTS: {d}")
        files = glob.glob(f"{d}/*.csv") + glob.glob(f"{d}/*.parquet")
        p(f"  files: {files[:10]}")
        found_dirs.append(d)
    else:
        p(f"DIR MISSING: {d}")

# Try to find freshwatch exports anywhere under /root
p("\nSearching for freshwatch CSVs under /root:")
try:
    r = subprocess.run(["find", "/root", "-name", "*.csv", "-newer", "/tmp"],
                       capture_output=True, text=True, timeout=10)
    p(r.stdout[:2000])
except Exception as e:
    p(f"find error: {e}")

# Try find by pattern
p("\nSearching for export files by name pattern:")
try:
    r2 = subprocess.run(["find", "/root", "-name", "*export*", "-o", "-name", "*freshwatch*",
                         "-o", "-name", "*daily*202608*"],
                        capture_output=True, text=True, timeout=10)
    p(r2.stdout[:3000])
except Exception as e:
    p(f"find2 error: {e}")
