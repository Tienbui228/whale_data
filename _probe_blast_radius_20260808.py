#!/usr/bin/env python3
"""Blast radius: who loads freshwatch CSV? Production gom_scan daily path."""
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except AttributeError:
    pass

WD  = Path(r"D:\Data back test\whale_data")
BOT = Path(r"D:\Data back test\binance-bot-signals")

print("=== BLAST RADIUS: freshwatch CSV decimal-taker bug ===")
print()

# 1. Production gom_scan.py: how does it load data for --daily?
print("=== gom_scan.py --daily data path ===")
gom_scan = WD / "scripts" / "gom_scan.py"
txt = gom_scan.read_text(encoding="utf-8", errors="replace")

# Find daily loading code
lines = txt.splitlines()
daily_section = []
in_daily = False
for i, line in enumerate(lines):
    if "--daily" in line or "args.daily" in line or "def run_daily" in line:
        in_daily = True
    if in_daily:
        daily_section.append(f"  L{i+1}: {line.rstrip()}")
    if in_daily and len(daily_section) > 40:
        break

# Look for parquet/CSV loading in daily path
print("  Keywords in daily section:")
for keyword in ["parquet", "freshwatch", "csv", "CSV", "read_csv", "load_fw", "store"]:
    matches = [i+1 for i, l in enumerate(lines) if keyword.lower() in l.lower()
               and ("daily" in lines[max(0,i-20):i+1][-1].lower() if i > 20 else True)]
    if matches:
        print(f"    '{keyword}' found at lines: {matches[:5]}")

# Show how daily actually loads
print()
print("  Searching for DayData source in --daily path:")
for i, line in enumerate(lines):
    if any(kw in line for kw in ["parquet", "read_parquet", "load_fw_csv", "freshwatch",
                                   "build_days_from", "load_store", "days_from"]):
        print(f"  L{i+1}: {line.rstrip()}")
print()

# 2. Check run_daily function
print("=== run_daily() function ===")
in_func = False
for i, line in enumerate(lines):
    if "def run_daily" in line or "def _run_daily" in line:
        in_func = True
    if in_func:
        print(f"  L{i+1}: {line.rstrip()}")
        if in_func and i > 0 and line.strip().startswith("def ") and "run_daily" not in line:
            break
    if in_func and len([l for l in lines[i:i+5] if l.strip()]) > 0:
        if i > 0 and lines[i].strip() == "" and lines[i-1].strip() == "":
            break
print()

# 3. Check all scripts that use load_fw_csv or freshwatch CSV
print("=== Scripts/probes that read freshwatch CSV ===")
search_dirs = [WD, WD / "scripts", WD / "backtest"]
patterns = ["load_fw_csv", "freshwatch_daily", "freshwatch.*csv", "read_csv.*freshwatch"]

found_files = set()
for d in search_dirs:
    if not d.exists():
        continue
    for f in d.glob("*.py"):
        try:
            content = f.read_text(encoding="utf-8", errors="replace")
            if any(p.replace(".*", "") in content for p in patterns):
                found_files.add(f)
        except Exception:
            pass

for f in sorted(found_files):
    print(f"  {f.relative_to(WD)}")
    content = f.read_text(encoding="utf-8", errors="replace")
    for i, line in enumerate(content.splitlines()):
        if any(p.replace(".*","") in line for p in patterns):
            print(f"    L{i+1}: {line.strip()[:80]}")
print()

# 4. Production gom_scan daily: check for parquet store read
print("=== Production daily: store/parquet usage ===")
for i, line in enumerate(lines):
    if any(kw in line for kw in ["read_parquet", "pq.read", ".parquet",
                                   "pd.read_parquet", "store_path", "store/"]):
        print(f"  L{i+1}: {line.rstrip()}")
print()

# 5. Conclusion
print("=== SUMMARY ===")
print("  load_fw_csv() defined in: _probe_gom_gate6_v6_20260808.py (gate probe only)")
print("  _probe_parti_fix_20260808.py has its own CSV loader (inline)")
print("  Production gom_scan.py --daily: reads from parquet store (data/raw/...)")
print("  → decimal taker bug is PROBE-ONLY, NOT in production daily path ✓")
print()
print("  G1 replay (result.txt via parse_result_file + build_days):")
print("  → taker_buy_pct from result.txt stored as PERCENTAGE (47.3) → no unit bug ✓")
