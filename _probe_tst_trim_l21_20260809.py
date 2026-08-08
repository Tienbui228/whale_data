"""
_probe_tst_trim_l21_20260809.py
L-21: remove 2026-08-08 partial candle from perp+spot CSVs.
Today = 08/08, 08/08 candle not closed → DAILY stops at 07/08.
"""
import sys, io, csv
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path

SCRATCH  = Path(r"D:\Data back test\whale_data\scratch")
DATE_TAG = "20260809"
TRIM_DATE = "2026-08-08"

def log(s=""): print(s)

def trim_csv(path):
    with open(path, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    fields = list(rows[0].keys()) if rows else []
    before = len(rows)
    rows = [r for r in rows if r.get("date") != TRIM_DATE]
    after = len(rows)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    log(f"  {path.name}: {before} → {after} rows (removed {before-after} rows = {TRIM_DATE})")
    if rows:
        log(f"    Last date: {rows[-1].get('date','?')} close={rows[-1].get('c','?')}")

log("L-21 trim: remove 2026-08-08 partial candle")
for fname in [f"tst_perp_{DATE_TAG}.csv", f"tst_spot_{DATE_TAG}.csv"]:
    trim_csv(SCRATCH / fname)

# Also trim LSR (08/08 only has partial data — first record at 00:00 UTC)
lsr_path = SCRATCH / f"tst_lsr_raw_{DATE_TAG}.csv"
with open(lsr_path, encoding="utf-8") as f:
    rows = list(csv.DictReader(f))
fields = list(rows[0].keys())
trimmed = [r for r in rows if r.get("date") != TRIM_DATE]
with open(lsr_path, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=fields)
    w.writeheader()
    w.writerows(trimmed)
log(f"  tst_lsr_raw_{DATE_TAG}.csv: {len(rows)} → {len(trimmed)} (removed 08/08 partial)")

log(f"\nL-21 done. DAILY will stop at 2026-08-07 (closed candle).")
