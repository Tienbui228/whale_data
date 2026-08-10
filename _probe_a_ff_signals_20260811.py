"""A: Per-day FF A1-A5 signal trace — corrupt full-rebuild vs incremental replay.

Reconstructs what gom_scan computed for FF for each day in 2026-07-01→2026-08-09.
Shows exactly which condition killed the Aug-01 chain.

data-source: VPS freshwatch_daily_2026-07.csv + 2026-08.csv (canonical)
machine: VPS via SSH
date-range: 2026-07-01 → 2026-08-09
code-commit: see git log
"""
from __future__ import annotations
import sys, io, csv, subprocess, json, math
from pathlib import Path
from collections import deque

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

VPS = "root@5.223.67.21"
SYM = "FFUSDT"
BASE = "FF"
DATE_FROM = "2026-07-01"
DATE_TO   = "2026-08-09"

def is_null(v): return v is None or str(v).strip() in ("", "nan", "None", "N/A")
def sf(v, default=None):
    try: return float(v)
    except: return default

# ── Fetch freshwatch rows for FF ──────────────────────────────────────────────
def fetch_csv(month):
    path = f"/root/Data_back_test/whale_data/data/export/freshwatch_daily_{month}.csv"
    r = subprocess.run(["ssh", VPS, f"cat {path}"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0: return []
    return [row for row in csv.DictReader(r.stdout.splitlines())
            if row.get("symbol") == SYM]

rows = []
for mo in ["2026-07", "2026-08"]:
    rows.extend(fetch_csv(mo))
rows.sort(key=lambda r: r.get("date",""))
rows = [r for r in rows if DATE_FROM <= r.get("date","") <= DATE_TO]
print(f"Fetched {len(rows)} FF rows: {rows[0]['date']} → {rows[-1]['date']}")

# ── Signal computation (mirrors gom_scan.py A1-A5) ───────────────────────────
# A1: _div_ratio = avg3(lsr_pos_r) / avg3(lsr_acc_r) ≥ 1.5
# A2: vol_quote ≥ threshold (skip in this trace, mark as ?)
# A3: lsr_global(i) / lsr_global(i-5) ≤ 1.15 (slope downward/flat)
# A4: oi_usd vs med14 (not in CSV directly — derived; mark as ?)
# A5: oi_cycle_pos 30d rolling (relative rank of oi in 30d window)

# Threshold
DIV_THRESH    = 1.5
SLOPE_THRESH  = 1.15
SLOPE_WINDOW  = 5

# Rolling windows
pos_buf = deque(maxlen=10)   # avg3 uses last 3
acc_buf = deque(maxlen=10)
gsr_buf = deque(maxlen=40)   # need 5d back for A3
oi_buf  = deque(maxlen=32)   # 30d for A5

def avg3(buf):
    if len(buf) < 3: return None
    vals = [v for v in list(buf)[-3:] if v is not None]
    return sum(vals)/len(vals) if vals else None

all_oi = []  # for A5 30d cycle pos

header = (f"{'date':<12} {'pos_r':>7} {'acc_r':>7} {'gLSR':>7} {'oi_usd':>14}"
          f" {'div_avg3':>9} {'A1':>4} {'slope5':>8} {'A3':>4} {'A5':>6}")
print(f"\n{header}")
print("-" * 100)

signals_by_date = {}
for i, row in enumerate(rows):
    d = row.get("date","")
    pos_r  = sf(row.get("lsr_pos_r"))
    acc_r  = sf(row.get("lsr_acc_r"))
    gLSR   = sf(row.get("lsr_global_r"))
    oi_usd = sf(row.get("oi_usd"))

    pos_buf.append(pos_r)
    acc_buf.append(acc_r)
    gsr_buf.append(gLSR)
    oi_buf.append(oi_usd)

    # A1
    div_p = avg3(pos_buf)
    div_a = avg3(acc_buf)
    if div_p is not None and div_a and div_a > 0:
        div_avg3 = div_p / div_a
        a1 = div_avg3 >= DIV_THRESH
    else:
        div_avg3 = None
        a1 = False

    # A3: slope5 = gLSR[i] / gLSR[i-5]
    gsr_list = list(gsr_buf)
    if gLSR is not None and len(gsr_list) > SLOPE_WINDOW:
        prev_gsr = gsr_list[-(SLOPE_WINDOW+1)]
        if prev_gsr and prev_gsr > 0:
            slope5 = gLSR / prev_gsr
            a3 = slope5 <= SLOPE_THRESH
        else:
            slope5 = None; a3 = False
    else:
        slope5 = None; a3 = False

    # A5: oi_cycle_pos — relative rank of oi in 30d window
    oi_list = [v for v in oi_buf if v is not None]
    if len(oi_list) >= 10 and oi_usd is not None:
        oi_min = min(oi_list)
        oi_max = max(oi_list)
        if oi_max > oi_min:
            oi_cycle_pos = (oi_usd - oi_min) / (oi_max - oi_min)
        else:
            oi_cycle_pos = 0.5
        a5 = oi_cycle_pos <= 0.5   # "in lower half of 30d range"
    else:
        oi_cycle_pos = None
        a5 = False

    signals_by_date[d] = {
        "pos_r": pos_r, "acc_r": acc_r, "gLSR": gLSR, "oi_usd": oi_usd,
        "div_avg3": div_avg3, "a1": a1, "slope5": slope5, "a3": a3,
        "oi_cycle_pos": oi_cycle_pos, "a5": a5,
        "a1_and_a3": a1 and a3,
    }

    # Format
    pos_s    = f"{pos_r:.3f}" if pos_r else "NULL"
    acc_s    = f"{acc_r:.3f}" if acc_r else "NULL"
    gsr_s    = f"{gLSR:.4f}" if gLSR else "NULL"
    oi_s     = f"${oi_usd/1e6:.2f}M" if oi_usd else "NULL"
    div_s    = f"{div_avg3:.3f}" if div_avg3 else "N/A"
    a1_s     = "✓" if a1 else "✗"
    slope_s  = f"{slope5:.4f}" if slope5 else "N/A"
    a3_s     = "✓" if a3 else "✗"
    cyc_s    = f"{oi_cycle_pos:.2f}" if oi_cycle_pos is not None else "N/A"
    flag     = " ◄ GOM FIRE" if (a1 and a3) else ""
    print(f"{d:<12} {pos_s:>7} {acc_s:>7} {gsr_s:>7} {oi_s:>14}"
          f" {div_s:>9} {a1_s:>4} {slope_s:>8} {a3_s:>4} {cyc_s:>6}{flag}")

# ── Focus: around 08-01 ──────────────────────────────────────────────────────
print(f"\n=== FOCUS: 2026-08-01 (start of FF chain) ===")
d = "2026-08-01"
sig = signals_by_date.get(d, {})
print(f"  pos_r     = {sig.get('pos_r')}")
print(f"  acc_r     = {sig.get('acc_r')}")
print(f"  gLSR      = {sig.get('gLSR')}")
print(f"  div_avg3  = {sig.get('div_avg3')} (thresh {DIV_THRESH})")
print(f"  A1        = {sig.get('a1')} ({'PASS' if sig.get('a1') else 'FAIL'})")
print(f"  slope5    = {sig.get('slope5')} (thresh ≤{SLOPE_THRESH})")
print(f"  A3        = {sig.get('a3')} ({'PASS' if sig.get('a3') else 'FAIL'})")
print(f"  oi_cycle  = {sig.get('oi_cycle_pos')}")
print(f"  A5        = {sig.get('a5')}")

# ── Identify: which days does A1∧A3 fire? ─────────────────────────────────────
fire_days = [d for d, s in signals_by_date.items() if s.get("a1") and s.get("a3")]
print(f"\n=== DAYS WHERE A1∧A3 BOTH PASS (necessary for GOM open): {len(fire_days)} ===")
for d in fire_days:
    sig = signals_by_date[d]
    print(f"  {d}  div={sig['div_avg3']:.3f}  slope={sig['slope5']:.4f}")

# ── A3 boundary sensitivity: slope values near 1.15 ──────────────────────────
print(f"\n=== A3 BOUNDARY ANALYSIS (slope5 near {SLOPE_THRESH}±0.05) ===")
for d, sig in sorted(signals_by_date.items()):
    slope = sig.get("slope5")
    if slope is not None and 1.10 <= slope <= 1.20:
        gLSR = sig.get("gLSR")
        print(f"  {d}  slope={slope:.5f}  gLSR={gLSR}  A3={'PASS' if slope<=SLOPE_THRESH else 'FAIL'}  margin={SLOPE_THRESH-slope:+.5f}")

# ── Compare: what happened in full-rebuild vs incremental ─────────────────────
print(f"\n=== ROOT CAUSE SUMMARY ===")
# The corrupt run used full-rebuild which recomputed all signals from scratch
# The key: was the full-rebuild using a different start date for the rolling window?
# gsr_buf fills from the BEGINNING of the data — if full-rebuild starts from an earlier
# date, the gsr_buf at 08-01 may have different historical values → different slope5

print(f"Probe computes signals from {DATE_FROM} → {DATE_TO}")
print(f"Full-rebuild would start from data store beginning (may differ)")
print(f"The slope5 at 08-01 depends on gLSR 5 days prior = 2026-07-27")
d_prior = "2026-07-27"
d_target = "2026-08-01"
sig_prior = signals_by_date.get(d_prior, {})
sig_target = signals_by_date.get(d_target, {})
print(f"  gLSR(07-27) = {sig_prior.get('gLSR')} [5d prior to 08-01]")
print(f"  gLSR(08-01) = {sig_target.get('gLSR')}")
if sig_prior.get('gLSR') and sig_target.get('gLSR'):
    slope_calc = sig_target['gLSR'] / sig_prior['gLSR']
    print(f"  slope = {slope_calc:.6f}  vs threshold {SLOPE_THRESH}")
    print(f"  margin = {SLOPE_THRESH - slope_calc:+.6f}")
    print(f"  {'PASS (below threshold)' if slope_calc <= SLOPE_THRESH else 'FAIL (above threshold)'}")

# Check if 07-24/25/26 missing (the gap) affects window
gap_dates = ["2026-07-24", "2026-07-25", "2026-07-26"]
print(f"\nGAP DATES (missing from freshwatch): {gap_dates}")
for gd in gap_dates:
    print(f"  {gd}: {'IN signals_by_date' if gd in signals_by_date else 'ABSENT'}")

print(f"\nIMPACT: The 5d slope window for 08-01 looks back to the 5th PRESENT row,")
print(f"not to a calendar date. Missing dates shift which actual date is used.")
print(f"Full-rebuild starting from a different DATE_FROM may fill buffer differently.")
