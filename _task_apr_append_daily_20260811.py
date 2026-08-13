"""
_task_apr_append_daily_20260811.py
Append 3 new rows (Aug 10-12) to CASE_APR.xlsx DAILY.
Reads from scratch/apr_p1_newrows_20260811.json.
machine: local
"""
import sys, io, json, openpyxl
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path

ROOT    = Path(r"D:\Data back test\whale_data")
SCRATCH = ROOT / "scratch"
CASE    = ROOT / "docs" / "case_files" / "CASE_APR.xlsx"

def log(s=""): print(s, flush=True)

# Load new rows
rows_file = SCRATCH / "apr_p1_newrows_20260811.json"
with open(rows_file, encoding="utf-8") as f:
    data = json.load(f)

need_dates   = data["need_dates"]
new_rows     = data["new_rows"]
existing_cnt = data["existing_count"]

log(f"Append task: {len(new_rows)} rows → CASE_APR.xlsx DAILY")
log(f"Dates: {need_dates}")
log(f"Existing DAILY data rows before: {existing_cnt}")

wb = openpyxl.load_workbook(CASE)
sh = wb["DAILY"]

# Verify last existing row date
all_rows = list(sh.iter_rows(values_only=True))
last_data_row = all_rows[-1]
log(f"Last existing row date: {last_data_row[0]}")

# Check for duplicates before appending
existing_dates = set()
for r in all_rows[2:]:  # skip 2 header rows
    if r[0]:
        existing_dates.add(str(r[0]))

appended = 0
for row50 in new_rows:
    d_str = str(row50[0])
    if d_str in existing_dates:
        log(f"  SKIP {d_str} — already exists")
        continue
    sh.append(row50)
    appended += 1
    log(f"  APPENDED {d_str}: c={row50[5]} ret={row50[16]:.3f}% vol=${row50[6]:,.0f}")

wb.save(CASE)
log(f"\nSaved. Appended {appended} rows.")

# Verify
wb2 = openpyxl.load_workbook(CASE, data_only=True, read_only=True)
sh2 = wb2["DAILY"]
rows2 = list(sh2.iter_rows(values_only=True))
log(f"Total rows after (incl 2 header): {len(rows2)}")
log(f"Data rows after: {len(rows2) - 2}")
log(f"Last 3 dates: {[r[0] for r in rows2[-3:]]}")
wb2.close()

log(f"\n[APPEND DONE]")
