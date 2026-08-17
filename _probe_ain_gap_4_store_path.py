"""[1b] Where does whale_collector store perp klines? Check module paths."""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
from datetime import datetime

ROOT = Path(r"D:\Data back test\whale_data")

print("=== [1b] whale_collector perp store paths ===\n")

# Check whale_collector module for storage paths
wc_config = ROOT / "whale_collector" / "config.py"
wc_paths  = ROOT / "whale_collector" / "storage" / "paths.py"
wc_storage = ROOT / "whale_collector" / "storage"

for p in [wc_config, wc_paths, wc_storage]:
    if p.exists():
        print(f"EXISTS: {p}")
        if p.is_file():
            txt = p.read_text(encoding="utf-8", errors="replace")
            for i, line in enumerate(txt.split("\n")):
                if any(k in line.lower() for k in ["raw", "store", "data_dir", "path", "dir",
                                                     "parquet", "partition", "ain", "perp", "kline"]):
                    print(f"  L{i+1}: {line.rstrip()}")
    else:
        print(f"ABSENT: {p}")

# Check backfill_30d.py for HOURLY_METRICS / _collect_symbol to understand what's stored
print("\n--- backfill_30d.py top-level config ---")
bf = ROOT / "scripts" / "backfill_30d.py"
if bf.exists():
    txt = bf.read_text(encoding="utf-8", errors="replace")
    lines = txt.split("\n")
    for i, line in enumerate(lines[:80]):
        if line.strip():
            print(f"  L{i+1}: {line.rstrip()}")

# Check case_daily.py — what does it do and what data source?
print("\n--- case_daily.py summary ---")
cd = ROOT / "scripts" / "case_daily.py"
if cd.exists():
    txt = cd.read_text(encoding="utf-8", errors="replace")
    lines = txt.split("\n")
    print(f"  lines: {len(lines)}")
    for i, line in enumerate(lines):
        if any(k in line.lower() for k in ["ain", "symbol", "csv", "parquet", "scratch",
                                            "stale", "date", "last", "build_case", "today"]):
            print(f"  L{i+1}: {line.rstrip()}")

# Search universe_master.csv for AIN
print("\n--- universe_master.csv AIN row ---")
um = ROOT / "data" / "config" / "universe_master.csv"
if not um.exists():
    um = ROOT / "data" / "universe_master.csv"
if um.exists():
    stat = um.stat()
    mtime = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
    print(f"  Found: {um} mtime={mtime}")
    lines = um.read_text(encoding="utf-8", errors="replace").strip().split("\n")
    print(f"  Total rows: {len(lines)}")
    print(f"  Header: {lines[0]}")
    ain_rows = [l for l in lines if "AINUSDT" in l]
    print(f"  AIN rows: {ain_rows}")
else:
    print(f"  universe_master.csv: NOT FOUND at {um}")
    for f in ROOT.rglob("universe_master.csv"):
        stat = f.stat()
        mtime = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
        print(f"  Found at: {f}  mtime={mtime}")
