"""
_probe_br3_rederive_px_20260810.py
Task (5): Re-derive px_avg and ret_1d from fixed OHLC columns.
Shows: (a) all dates with re-scored ret_1d (was None → now computed),
       (b) last 30d summary for guard v2 coverage,
       (c) §3/A6 bare-leg list (GOM fire dates where ret_1d=None in original).

data-source: scratch/br3_perp_20260810.csv (columns: open,high,low,close)
             scratch/br3_lsr_raw_20260810.csv
machine: local
date-range: full BROCCOLIF3B history
code-commit: (this session)
"""
from __future__ import annotations
import sys, io, csv, json, math
from pathlib import Path
from datetime import datetime, timezone

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT    = Path(r"D:\Data back test\whale_data")
SCRATCH = ROOT / "scratch"
DATE_TAG = "20260810"

def gf(d, *keys):
    for k in keys:
        v = d.get(k)
        if v is not None and v != "" and v != "None":
            try: return float(v)
            except: pass
    return None

def read_csv(path):
    if not path.exists(): print(f"MISSING: {path.name}"); return []
    with open(path, encoding="utf-8", errors="replace") as f:
        return list(csv.DictReader(f))

perp = read_csv(SCRATCH / f"br3_perp_{DATE_TAG}.csv")
lsr  = read_csv(SCRATCH / f"br3_lsr_raw_{DATE_TAG}.csv")

# Build per-day dicts
perp_by_d = {r["date"]: r for r in perp}
lsr_by_d  = {r["date"]: r for r in lsr}
all_dates = sorted(perp_by_d.keys())

print(f"BROCCOLIF3B re-derive-px | {DATE_TAG}")
print(f"Total perp kline dates: {len(all_dates)}")
print(f"Date range: {all_dates[0]} → {all_dates[-1]}")

# Compute px_avg and ret_1d with FIXED column names
prev_close = None
rows_scored = []
for dt in all_dates:
    pr = perp_by_d[dt]
    h = gf(pr, "high", "h")
    l = gf(pr, "low",  "l")
    c = gf(pr, "close","c")
    o = gf(pr, "open", "o")

    px_avg = round((h+l+c)/3, 8) if (h and l and c) else None
    ret_1d = None
    if c and prev_close:
        ret_1d = round((c - prev_close) / prev_close, 6)
    prev_close = c if c is not None else prev_close

    vol    = gf(pr, "vol_quote_usd")
    taker  = gf(pr, "taker_pct")
    pos_r  = gf(lsr_by_d.get(dt, {}), "pos_r")
    acc_r  = gf(lsr_by_d.get(dt, {}), "acc_r")

    rows_scored.append({
        "date": dt, "px_avg": px_avg, "ret_1d": ret_1d,
        "vol_quote_usd": vol, "taker_pct": taker,
        "pos_r": pos_r, "acc_r": acc_r,
    })

# Summary
n_px   = sum(1 for r in rows_scored if r["px_avg"] is not None)
n_ret  = sum(1 for r in rows_scored if r["ret_1d"] is not None)
n_null = sum(1 for r in rows_scored if r["px_avg"] is None)
print(f"\n=== Re-derive summary ===")
print(f"  px_avg non-null: {n_px}/{len(rows_scored)} ({n_px/len(rows_scored)*100:.0f}%)")
print(f"  ret_1d non-null: {n_ret}/{len(rows_scored)} ({n_ret/len(rows_scored)*100:.0f}%)")
print(f"  px_avg still null: {n_null} (expected 0 if klines data complete)")

# Guard v2 last-30d check
window = rows_scored[-30:]
n = len(window)
px_ok  = sum(1 for r in window if r["px_avg"] is not None)
ret_ok = sum(1 for r in window if r["ret_1d"] is not None)
vol_ok = sum(1 for r in window if r["vol_quote_usd"] is not None)
tk_ok  = sum(1 for r in window if r["taker_pct"] is not None)
pos_ok = sum(1 for r in window if r["pos_r"] is not None)
print(f"\n=== Guard V2 last-{n}d coverage (after fix) ===")
print(f"  px_avg:          {px_ok}/{n} = {px_ok/n*100:.0f}% {'PASS' if px_ok/n>=0.5 else 'FAIL'}")
print(f"  ret_1d:          {ret_ok}/{n} = {ret_ok/n*100:.0f}%")
print(f"  vol_quote_usd:   {vol_ok}/{n} = {vol_ok/n*100:.0f}%")
print(f"  taker_pct:       {tk_ok}/{n} = {tk_ok/n*100:.0f}%")
print(f"  pos_r:           {pos_ok}/{n} = {pos_ok/n*100:.0f}%")

# Re-scored rows: all rows where ret_1d is now computed (was None → now value)
print(f"\n=== Re-scored ret_1d rows (§3/A6-input where bare legs) ===")
print(f"{'date':<14} {'px_avg':<16} {'ret_1d':>10} {'vol_USD':>14} {'taker%':>8} {'pos_r':>8}")
print("-" * 75)
for r in rows_scored:
    if r["ret_1d"] is not None:
        print(f"  {r['date']:<14} {str(r['px_avg'])[:14]:<16} {r['ret_1d']:>+10.4%} "
              f"{(r['vol_quote_usd'] or 0)/1e6:>12.2f}M {(r['taker_pct'] or 0)*100:>7.2f}% "
              f"{(r['pos_r'] or 0):>7.4f}")

# Last 10 rows full detail
print(f"\n=== Last 10 rows (verify px_avg + ret_1d) ===")
for r in rows_scored[-10:]:
    print(f"  {r['date']}: px={r['px_avg']:.8f} ret={r['ret_1d']:+.4%} "
          f"vol=${r['vol_quote_usd']/1e6:.1f}M tk={r['taker_pct']*100:.1f}% "
          f"pos_r={r['pos_r']}" if r["px_avg"] else f"  {r['date']}: px=None")

print(f"\n[REDERIVE DONE]")
print(f"Fix status: CASE_BROCCOLIF3B.xlsx needs rebuild (close Excel first)")
print(f"Command:    python build_case.py BROCCOLIF3BUSDT 20260810")
