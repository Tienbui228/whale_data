#!/usr/bin/env python3
"""GUA Gate backfill: fill cols 51-52 (vol_spot_ext_usd + spot_ext_venue) from Gate API."""
import sys, io, urllib.request, json, math
from datetime import datetime, timezone
from pathlib import Path
import openpyxl

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

XLSX = Path(r"D:\Data back test\whale_data\docs\case_files\CASE_GUA.xlsx")

# Fetch Gate klines 07-01 → 08-18
frm = int(datetime(2026, 7, 1, tzinfo=timezone.utc).timestamp())
to  = int(datetime(2026, 8, 19, tzinfo=timezone.utc).timestamp())
url = f"https://api.gateio.ws/api/v4/spot/candlesticks?currency_pair=GUA_USDT&interval=1d&from={frm}&to={to}"
resp = json.load(urllib.request.urlopen(url, timeout=30))
# Format Gate v4: [ts, quote_vol_USDT, close, high, low, open, base_vol_GUA, complete]

# Build map: date_str → quote_vol_usd
gate_vol = {}
for c in resp:
    ts, qv, cl, hi, lo, op, bv, complete = c
    d = datetime.fromtimestamp(int(ts), tz=timezone.utc).strftime("%Y-%m-%d")
    gate_vol[d] = float(qv)

print(f"[Gate] fetched {len(gate_vol)} days, first={min(gate_vol)} last={max(gate_vol)}")

# Open workbook write-mode
wb = openpyxl.load_workbook(str(XLSX), data_only=False)
ws = wb["DAILY"]
max_row = ws.max_row
max_col_before = ws.max_column
print(f"[xlsx] max_row={max_row} max_col={max_col_before} (before)")

# Add section header row 1 col 51-52 (extend HAI-CHAN-KHO section)
ws.cell(1, 51).value = "SPOT-EXT (venue ngoài Binance, L-52 canonical)"
# Add col header row 2 col 51-52 per schema v2.1
ws.cell(2, 51).value = "vol_spot_ext_usd"
ws.cell(2, 52).value = "spot_ext_venue"

# Fill data 2026-07-01 → 2026-08-17 (max row = 241)
n_filled = 0
n_missing = 0
for r in range(3, max_row + 1):
    date_v = ws.cell(r, 1).value
    if not date_v: continue
    dstr = str(date_v)[:10]
    if not (dstr >= "2026-07-01" and dstr <= "2026-08-18"): continue
    v = gate_vol.get(dstr)
    if v is None:
        n_missing += 1
        continue
    ws.cell(r, 51).value = round(v, 2)
    ws.cell(r, 52).value = "gate"
    n_filled += 1

print(f"[fill] {n_filled} rows filled, {n_missing} missing (no Gate data)")
print(f"[xlsx] max_col now: {ws.max_column} (after add col 51-52)")

# Guard L-50: write-after-guard verify
# Simple guard: max_col must be >= 52 after edit
assert ws.max_column >= 52, f"Guard fail: max_col={ws.max_column} <52"

wb.save(str(XLSX))
print(f"[save] {XLSX.name}")

# Verify: re-open + spot-check
wb2 = openpyxl.load_workbook(str(XLSX), data_only=True, read_only=True)
ws2 = wb2["DAILY"]
print(f"\n[verify] Spot-check 5 rows (07-01, 07-15, 08-01, 08-08, 08-17):")
for target in ["2026-07-01","2026-07-15","2026-08-01","2026-08-08","2026-08-17"]:
    for r in range(3, ws2.max_row + 1):
        d = str(ws2.cell(r, 1).value)[:10]
        if d == target:
            v51 = ws2.cell(r, 51).value
            v52 = ws2.cell(r, 52).value
            v35 = ws2.cell(r, 35).value
            print(f"  {target}  col51={v51}  col52={v52}  col35(alpha)={str(v35)[:40] if v35 else None}")
            break
wb2.close()
