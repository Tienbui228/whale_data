"""Run format_tg_report on VPS gom_scan output → print TG baseline v9."""
import sys, subprocess
from pathlib import Path
from datetime import datetime, timezone, timedelta

sys.path.insert(0, "scripts")
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from run_gom_daily import format_tg_report

REPO  = Path(".")
STORE = REPO / "data" / "export"
SYM   = REPO / "data" / "config" / "freshwatch_symbols.txt"

target_date = "2026-08-07"
run_date    = "2026-08-08"
run_utc     = "15:07"   # from the VPS run timestamp

result = subprocess.run(
    [sys.executable, "scripts/gom_scan.py",
     "--daily", "--store", str(STORE),
     "--date", target_date,
     "--fw-filter", str(SYM)],
    capture_output=True, text=True, encoding="utf-8", errors="replace"
)
stdout = result.stdout

report = format_tg_report(stdout, target_date, run_utc, run_date)
print("=" * 60)
print(report)
print("=" * 60)
