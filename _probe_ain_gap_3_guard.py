"""[3] Kiểm tra build_case.py có staleness guard không."""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path

ROOT = Path(r"D:\Data back test\whale_data")

print("=== [3] build_case.py staleness guard ===\n")

bc = ROOT / "build_case.py"
if not bc.exists():
    # Check backtest/
    bc = ROOT / "backtest" / "build_case.py"

if bc.exists():
    txt = bc.read_text(encoding="utf-8", errors="replace")
    lines = txt.split("\n")
    print(f"build_case.py: {bc} ({len(lines)} lines)")
    print("\n--- Staleness / date-check logic (search 'stale', 'gap', 'today', 'date', 'warn') ---")
    hits = []
    for i, line in enumerate(lines):
        if any(k in line.lower() for k in ["stale", "staleness", "days_ago", "today", "cutoff",
                                             "last_date", "date_gap", "warn", "raise", "guard",
                                             "missing", "data_ok"]):
            hits.append((i+1, line.rstrip()))
    if hits:
        for ln, l in hits:
            print(f"  L{ln}: {l}")
    else:
        print("  NO staleness guard found")

    # Also search for date range logic around the last row
    print("\n--- 'last' / 'max' date logic ---")
    for i, line in enumerate(lines):
        if any(k in line.lower() for k in ["last_date", "max_date", "end_date", "date_end",
                                             "df.tail", "iloc[-1]", "last row", "cutoff_date"]):
            print(f"  L{i+1}: {line.rstrip()}")
else:
    print(f"build_case.py NOT FOUND at expected paths")
    # Search
    for f in ROOT.rglob("build_case.py"):
        print(f"  found at: {f}")
