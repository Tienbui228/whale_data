"""[1] Kiểm tra store raw AIN daily — perp klines cuối ngày nào."""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
import os

ROOT = Path(r"D:\Data back test\whale_data")

print("=== [1] STORE RAW AIN DAILY — cuối ngày nào? ===\n")

# Check possible store paths for perp/fapi klines
candidates = [
    ROOT / "data" / "raw" / "fapi_klines_1d",
    ROOT / "data" / "raw" / "perp_klines_1d",
    ROOT / "data" / "raw" / "klines_1d",
    ROOT / "data" / "raw",
    ROOT / "data",
]

for p in candidates:
    if p.exists() and p.is_dir():
        print(f"EXISTS: {p}")
        # List subdirs/files
        children = sorted(p.iterdir())[:20]
        for c in children:
            print(f"  {c.name}{'/' if c.is_dir() else ''}")
    else:
        print(f"ABSENT: {p}")

# Specifically search for AIN files anywhere in data/
print("\n--- Search for AIN*.parquet/csv/json in data/ ---")
data_dir = ROOT / "data"
if data_dir.exists():
    for f in sorted(data_dir.rglob("*AIN*")):
        stat = f.stat()
        from datetime import datetime
        mtime = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
        print(f"  {f.relative_to(ROOT)}  mtime={mtime}  size={stat.st_size}")
    for f in sorted(data_dir.rglob("*ain*")):
        stat = f.stat()
        mtime = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
        print(f"  {f.relative_to(ROOT)}  mtime={mtime}  size={stat.st_size}")
else:
    print("  data/ not found")

# Check scratch for AIN CSVs (these are what build_case used)
print("\n--- scratch/ AIN files ---")
scratch = ROOT / "scratch"
if scratch.exists():
    for f in sorted(scratch.glob("ain*")):
        stat = f.stat()
        mtime = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
        print(f"  {f.name}  mtime={mtime}  size={stat.st_size}")
        # If CSV, print last date
        if f.suffix == ".csv":
            try:
                lines = f.read_text(encoding="utf-8", errors="replace").strip().split("\n")
                if lines:
                    print(f"    first: {lines[0][:80]}")
                    print(f"    last:  {lines[-1][:80]}")
                    print(f"    rows:  {len(lines)}")
            except Exception as e:
                print(f"    read error: {e}")
else:
    print("  scratch/ not found")
