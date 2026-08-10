"""
_task_gua_8_register_20260810.py
G-8: Register GUA in CASE_INDEX.xlsx INDEX sheet.
Append row. KHÔNG điền verdict — tầng HUMAN.
machine: local
date: 2026-08-10
"""
import sys, io, openpyxl
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
from datetime import datetime, timezone

ROOT     = Path(r"D:\Data back test\whale_data")
CASE_IDX = ROOT / "docs" / "case_files" / "CASE_INDEX.xlsx"
DATE_TAG = "20260810"

def log(s=""): print(s)
NOW = datetime.now(timezone.utc)
log(f"G-8 REGISTER GUAUSDT  |  {NOW.strftime('%Y-%m-%d %H:%M UTC')}")

wb = openpyxl.load_workbook(CASE_IDX)
sh = wb["INDEX"]

# Current last row
existing = list(sh.iter_rows(values_only=True))
n_before = len(existing)
log(f"  INDEX rows before: {n_before}")

# Check if GUA already registered
for r in existing:
    if r and any("GUA" == str(v).strip().upper() for v in r if v):
        log(f"  GUA already registered — skipping")
        sys.exit(0)

# Append GUA row (matching column structure from existing rows)
# Cols: [filename, symbol, status, verdict, watch_status, date, col6, notes, col8, alpha_id, notes2]
new_row = [
    "CASE_GUA.xlsx",
    "GUA",
    "ACTIVE",
    "crowd-trap; div_avg3=0.41 BEAR; gLSR=2.87 VERY BULL; 0 GOM-A; OI calib $5.4M; ATH $1.70 -97.7%; pump TODAY +54.92%",
    "WATCH (án mới, pump in-progress → DỪNG chờ đọc)",
    "2026-08-10",
    None,
    "snap2 ≥15:50 UTC; G-4 on-chain CẦN OPERATOR; G-5 snap1 BID-HEAVY 1.25",
    None,
    "ALPHA_483",
    "SUPERFORTUNE; BSC onboard 2025-12-21; ATH $1.70 May25; 231 DAILY rows; contract=0xa5c8e151...",
]
sh.append(new_row)
n_after = n_before + 1

wb.save(CASE_IDX)
log(f"  GUA registered at row {n_after}")
log(f"  INDEX rows after: {n_after}")

# Verify
wb2 = openpyxl.load_workbook(CASE_IDX, data_only=True)
sh2 = wb2["INDEX"]
rows2 = list(sh2.iter_rows(values_only=True))
last = rows2[-1]
log(f"  Verify last row: {list(last)[:4]}")
log(f"  → filename={last[0]}, symbol={last[1]}, status={last[2]}")

log(f"\n[G-8 DONE]")
log(f"  CASE_GUA.xlsx registered in CASE_INDEX at row {n_after}")
log(f"  Verdict: KHÔNG điền — tầng HUMAN (CLAUDE.md §TẦNG HUMAN §3)")
