"""[2] Kiểm tra freshwatch_symbols.txt — AIN có trong list không? mtime?"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
from datetime import datetime

ROOT = Path(r"D:\Data back test\whale_data")

print("=== [2] freshwatch_symbols.txt — AIN trong list? ===\n")

candidates = [
    ROOT / "data" / "config" / "freshwatch_symbols.txt",
    ROOT / "data" / "freshwatch_symbols.txt",
    ROOT / "freshwatch_symbols.txt",
    ROOT / "scripts" / "freshwatch_symbols.txt",
]

for p in candidates:
    if p.exists():
        stat = p.stat()
        mtime = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
        lines = p.read_text(encoding="utf-8", errors="replace").strip().split("\n")
        print(f"FOUND: {p}")
        print(f"  mtime: {mtime}")
        print(f"  lines: {len(lines)}")
        ain_lines = [l for l in lines if "AIN" in l.upper()]
        print(f"  AIN matches: {ain_lines}")
        print(f"  First 10: {lines[:10]}")
    else:
        print(f"ABSENT: {p}")

# Also check collect_daily.py for which symbol list it uses
print("\n--- collect_daily.py symbol source ---")
cd = ROOT / "scripts" / "collect_daily.py"
if cd.exists():
    txt = cd.read_text(encoding="utf-8", errors="replace")
    # Find symbol loading logic
    for i, line in enumerate(txt.split("\n")):
        if any(k in line.lower() for k in ["symbol", "ain", "freshwatch", "universe", "read_csv", "yaml", "config"]):
            print(f"  L{i+1}: {line.rstrip()}")
else:
    print(f"  ABSENT: {cd}")

# Check other collector scripts
print("\n--- Other collector/cron scripts that might cover perp klines ---")
for script in sorted((ROOT / "scripts").glob("*.py")):
    stat = script.stat()
    mtime = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d")
    print(f"  {script.name}  mtime={mtime}")
