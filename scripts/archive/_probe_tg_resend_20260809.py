"""Re-run report for 2026-08-08, check TG message length, send with truncation if needed."""
import sys, subprocess, json, urllib.request, urllib.parse, os
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, "scripts")
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from run_gom_daily import format_tg_report, tg_send

REPO        = Path(".")
STORE       = REPO / "data" / "export"
SYM         = REPO / "data" / "config" / "freshwatch_symbols.txt"
target_date = "2026-08-08"
run_date    = "2026-08-09"
run_utc     = "01:25"   # original cron time

result = subprocess.run(
    [sys.executable, "scripts/gom_scan.py",
     "--daily", "--store", str(STORE),
     "--date", target_date,
     "--fw-filter", str(SYM)],
    capture_output=True, text=True, encoding="utf-8", errors="replace"
)
stdout = result.stdout

report = format_tg_report(stdout, target_date, run_utc, run_date)
length = len(report)
print(f"Report length: {length} chars (TG limit 4096)")

TG_LIMIT = 4096
if length > TG_LIMIT:
    # Truncate at last newline before limit, append notice
    cut = report[:TG_LIMIT - 60].rfind("\n")
    report_send = report[:cut] + "\n[truncated — full in gom_daily.log]"
    print(f"TRUNCATED to {len(report_send)} chars")
else:
    report_send = report

print("--- REPORT ---")
print(report_send)
print("--------------")

ok = tg_send(report_send)
print(f"tg_send={'OK' if ok else 'FAIL'}")
