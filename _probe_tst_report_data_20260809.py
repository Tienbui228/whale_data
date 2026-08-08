"""
_probe_tst_report_data_20260809.py
Extract A.5 ba-dao-ham table values + EVENTS summary + B-2 details from CASE_TST.xlsx.
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
from datetime import datetime, timezone
import openpyxl

CASE_DIR = Path(r"D:\Data back test\whale_data\docs\case_files")
SCRATCH  = Path(r"D:\Data back test\whale_data\scratch")

def log(s=""): print(s)
def sf(v, d=None):
    try: return float(v) if v not in (None,"",) else d
    except: return d

NOW = datetime.now(timezone.utc)
log("=" * 70)
log(f"TST REPORT DATA  |  {NOW.strftime('%Y-%m-%d %H:%M UTC')}")
log("=" * 70)

wb   = openpyxl.load_workbook(str(CASE_DIR / "CASE_TST.xlsx"), data_only=True)
ws_d = wb["DAILY"]

# Read headers
hdrs = [ws_d.cell(1, c).value for c in range(1, ws_d.max_column + 1)]
col  = {h: i+1 for i, h in enumerate(hdrs) if h}
log(f"  Columns: {len(hdrs)} headers found")

# Read all DAILY rows into a list of dicts
rows = []
for r in range(2, ws_d.max_row + 1):
    if ws_d.cell(r, col.get("date", 1)).value is None:
        continue
    row = {h: ws_d.cell(r, col[h]).value for h in col}
    rows.append(row)
log(f"  DAILY rows: {len(rows)}, {rows[0].get('date','?')} → {rows[-1].get('date','?')}")

# ── A.5 BA-ĐẠO-HÀM: mốc 7/14/21/28 ngày gần nhất ────────────────────────────
log("\n--- A.5 BA-ĐẠO-HÀM table (last 28d of DAILY) ---")

# Last 28 rows (all have data since LSR available from 06-27)
# Mốc: i = last row; 7d = last-6, 14d = last-13, 21d = last-20, 28d = last-27
def get_moc(offset, rows):
    """offset=0 → latest, offset=6 → 7d ago (= 7 rows back)"""
    idx = len(rows) - 1 - offset
    if idx < 0: return None
    return rows[idx]

# div_avg3: col in DAILY
log(f"\n  div_avg3 (col={col.get('div_avg3','?')}):")
for label, offset in [("7d",6), ("14d",13), ("21d",20), ("28d",27)]:
    r = get_moc(offset, rows)
    if r:
        da = sf(r.get("div_avg3"))
        dt = r.get("date","?")
        log(f"    {label} ({dt}): div_avg3={da}")
if rows:
    peak28 = max((sf(r.get("div_avg3")) for r in rows[-28:] if sf(r.get("div_avg3")) is not None), default=None)
    log(f"    Peak div_avg3 (last 28d): {peak28}")

log(f"\n  gLSR (col={col.get('gLSR','?')}):")
glsr_28 = [sf(r.get("gLSR")) for r in rows[-28:] if sf(r.get("gLSR")) is not None]
for label, offset in [("7d",6), ("14d",13), ("21d",20), ("28d",27)]:
    r = get_moc(offset, rows)
    if r:
        g = sf(r.get("gLSR"))
        dt = r.get("date","?")
        log(f"    {label} ({dt}): gLSR={g}")
if glsr_28:
    log(f"    min28d gLSR: {min(glsr_28):.4f}")
    log(f"    max28d gLSR: {max(glsr_28):.4f}")
# Check crossings
for r in rows[-28:]:
    g = sf(r.get("gLSR"))
    if g is None: continue

log(f"\n  vol_vs_med14 (col={col.get('vol_vs_med14','?')}):")
for label, offset in [("7d",6), ("14d",13), ("21d",20), ("28d",27)]:
    r = get_moc(offset, rows)
    if r:
        vm = sf(r.get("vol_vs_med14"))
        dt = r.get("date","?")
        log(f"    {label} ({dt}): vol_vs_med14={vm}")
# avg7 per moc
for label, n_rows in [("7d",7), ("14d",7), ("21d",7), ("28d",7)]:
    offsets = {"7d": 0, "14d": 7, "21d": 14, "28d": 21}
    start_idx = len(rows) - offsets[label] - n_rows
    end_idx   = len(rows) - offsets[label]
    window = rows[max(0,start_idx):end_idx]
    vms = [sf(r.get("vol_vs_med14")) for r in window if sf(r.get("vol_vs_med14")) is not None]
    avg = round(sum(vms)/len(vms), 3) if vms else None
    log(f"    avg7 ending {label} ago: {avg} (n={len(vms)})")

# ── B-2 flags detail ──────────────────────────────────────────────────────────
log("\n--- B-2 Flag Summary ---")
dist_wall = [r for r in rows if r.get("flag_dist_wall_day") in (True, "True", 1, "1")]
knife      = [r for r in rows if r.get("flag_knife_crowd") in (True, "True", 1, "1")]
decay      = [r for r in rows if r.get("flag_decay_day") in (True, "True", 1, "1")]
neg_div    = [r for r in rows if r.get("flag_neg_div") in (True, "True", 1, "1")]
hedge      = [r for r in rows if r.get("flag_hedge_struct") in (True, "True", 1, "1")]
log(f"  flag_dist_wall_day: {len(dist_wall)} / {len(rows)} = {len(dist_wall)/len(rows)*100:.1f}%")
log(f"  flag_knife_crowd:   {len(knife)}")
log(f"  flag_decay_day:     {len(decay)}")
log(f"  flag_neg_div:       {len(neg_div)}")
log(f"  flag_hedge_struct:  {len(hedge)}")

if knife:
    log(f"\n  knife_crowd rows:")
    for r in knife:
        log(f"    {r.get('date')}: ret={r.get('ret_1d')} gLSR={r.get('gLSR')} taker={r.get('taker_buy_pct')}")

# ── pos_r / gLSR trajectory (last 42d of LSR window) ─────────────────────────
log("\n--- LSR trajectory (last 42 days with data) ---")
lsr_rows_full = [r for r in rows if sf(r.get("pos_r")) is not None]
log(f"  Rows with pos_r data: {len(lsr_rows_full)}")
if lsr_rows_full:
    log(f"  Range: {lsr_rows_full[0].get('date')} → {lsr_rows_full[-1].get('date')}")
    log(f"  Selected rows:")
    for r in lsr_rows_full:
        pos = sf(r.get("pos_r")); acc = sf(r.get("acc_r")); g = sf(r.get("gLSR"))
        da = sf(r.get("div_avg3")); sl = sf(r.get("glsr_slope_5d"))
        gom_a = r.get("gom_A_screen")
        log(f"    {r.get('date')}: pos_r={pos} acc_r={acc} gLSR={g} div_avg3={da} slope={sl} GOM_A={gom_a}")

# ── EVENTS sheet ──────────────────────────────────────────────────────────────
log("\n--- EVENTS sheet ---")
ws_ev = wb["EVENTS"]
ev_count = 0
for r in range(1, ws_ev.max_row + 1):
    vals = [ws_ev.cell(r, c).value for c in range(1, ws_ev.max_column + 1)]
    if any(v for v in vals):
        log(f"  Row {r}: {vals[:5]}")
        ev_count += 1
log(f"  Total event rows: {ev_count}")

# ── Funding deep dive: funding window stats ────────────────────────────────────
log("\n--- Funding stats (from DAILY, fn=6 days) ---")
fund_rows_ok = [r for r in rows if sf(r.get("fn")) is not None and sf(r.get("fn")) >= 6]
log(f"  Rows with fn>=6: {len(fund_rows_ok)}")
if fund_rows_ok:
    f_avgs = [sf(r.get("f_avg")) for r in fund_rows_ok if sf(r.get("f_avg")) is not None]
    neg_days = [r for r in fund_rows_ok if sf(r.get("f_avg")) is not None and sf(r.get("f_avg")) < 0]
    log(f"  Mean f_avg (when fn>=6): {round(sum(f_avgs)/len(f_avgs),6) if f_avgs else 'N/A'}")
    log(f"  Negative f_avg days: {len(neg_days)}")
    log(f"\n  Recent 7 days f_avg:")
    for r in fund_rows_ok[-7:]:
        log(f"    {r.get('date')}: f_avg={r.get('f_avg')} fn={r.get('fn')} pin_day={r.get('pin_day')}")

wb.close()

log(f"\n[REPORT DATA DONE]")
