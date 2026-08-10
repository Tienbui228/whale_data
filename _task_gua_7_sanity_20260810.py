"""
_task_gua_7_sanity_20260810.py
G-7: Sanity 5 items for GUAUSDT.
S1: DAILY row count. S2: date continuity. S3: GOM-A/B flag count.
S4: taker_buy_pct range [40,60]. S5: f_avg sign+range (last 14d).
machine: local
date: 2026-08-10
"""
import sys, io, openpyxl
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
from datetime import datetime, timezone, timedelta

ROOT    = Path(r"D:\Data back test\whale_data")
CASE_GUA = ROOT / "docs" / "case_files" / "CASE_GUA.xlsx"
DATE_TAG = "20260810"

def log(s=""): print(s)
NOW = datetime.now(timezone.utc)
log(f"G-7 SANITY GUAUSDT  |  {NOW.strftime('%Y-%m-%d %H:%M UTC')}")

wb = openpyxl.load_workbook(CASE_GUA, data_only=True)
sh = wb["DAILY"]
rows = list(sh.iter_rows(values_only=True))
hdr1 = rows[1]
actual_data = [r for r in rows[2:] if any(v is not None for v in r)]

col_map = {str(h or "").lower().strip(): i for i, h in enumerate(hdr1)}
def gcol_exact(row, key):
    kl = key.lower().strip()
    if kl in col_map:
        return row[col_map[kl]]
    # substring fallback
    for ck, ci in col_map.items():
        if kl in ck:
            return row[ci]
    return None

def sf(v):
    try: return float(v) if v not in (None,"","None") else None
    except: return None

PASS = 0; FAIL = 0

def check(label, ok, detail=""):
    global PASS, FAIL
    if ok: PASS += 1; s = "PASS"
    else:  FAIL += 1; s = "FAIL"
    log(f"  [{s}] {label}{(' — ' + detail) if detail else ''}")

log(f"\n  DAILY rows loaded: {len(actual_data)}")
log()

# ── S1: Row count ≥200 ───────────────────────────────────────────────────────
n = len(actual_data)
check("S1 DAILY row count ≥200", n >= 200, f"n={n}")

# ── S2: Date continuity (no gap > 2 calendar days) ───────────────────────────
dates = []
for r in actual_data:
    v = gcol_exact(r, "date")
    try: dates.append(str(v)[:10])
    except: pass
dates = sorted(set(d for d in dates if d and d >= "2025-01-01"))
gaps = []
for i in range(1, len(dates)):
    d0 = datetime.strptime(dates[i-1], "%Y-%m-%d")
    d1 = datetime.strptime(dates[i], "%Y-%m-%d")
    diff = (d1 - d0).days
    if diff > 3:  # allow weekends + 1
        gaps.append(f"{dates[i-1]}→{dates[i]} ({diff}d)")
check("S2 Date continuity (no gap >3d)", len(gaps) == 0,
      f"gaps: {gaps[:3]}" if gaps else f"range {dates[0]}→{dates[-1]}, n={len(dates)}")

# ── S3: GOM-A/B flag count (expect 0 for GUAUSDT based on build output) ────────
gom_a = sum(1 for r in actual_data if str(gcol_exact(r,"gom_a_screen") or "").lower() == "true")
gom_b = sum(1 for r in actual_data if str(gcol_exact(r,"gom_b_screen") or "").lower() == "true")
check("S3 GOM-A fires=0 (expected cold)", gom_a == 0, f"GOM-A={gom_a}, GOM-B={gom_b}")

# ── S4: taker_buy_pct range [35,65] ──────────────────────────────────────────
takers = [sf(gcol_exact(r,"taker_buy_pct (k[10]/k[7])")) for r in actual_data]
takers_v = [v for v in takers if v is not None]
out_range = [v for v in takers_v if not (35 <= v <= 65)]
check("S4 taker_buy_pct in [35,65]", len(out_range) == 0,
      f"out-range: {len(out_range)}/{len(takers_v)}, outliers: {sorted(out_range)[:5]}" if out_range else
      f"range [{min(takers_v):.1f},{max(takers_v):.1f}], n={len(takers_v)}")

# ── S5: f_avg last 14d sign+magnitude ────────────────────────────────────────
f_avgs = [sf(gcol_exact(r,"f_avg")) for r in actual_data]
f_valid = [(dates[i], f_avgs[i]) for i in range(len(f_avgs)) if f_avgs[i] is not None]
f_last14 = f_valid[-14:] if len(f_valid) >= 14 else f_valid
f_extreme = [(d,v) for d,v in f_last14 if abs(v) > 0.005]
f_neg = [(d,v) for d,v in f_last14 if v < -0.0002]
f_range_ok = len(f_extreme) == 0
log(f"  f_avg last 14d: n={len(f_last14)}, neg_days={len(f_neg)}, extreme(>0.5%)={len(f_extreme)}")
if f_last14:
    log(f"    last 3: " + " | ".join(f"{d}={v:.6f}" for d,v in f_last14[-3:]))
check("S5 f_avg last 14d no extreme (|f|>0.5%)", f_range_ok,
      f"extreme: {[(d,round(v,5)) for d,v in f_extreme[:3]]}" if f_extreme else "OK")

# ── Summary ──────────────────────────────────────────────────────────────────
log()
log(f"  SANITY: {PASS}/5 PASS, {FAIL}/5 FAIL")
if FAIL == 0:
    log(f"  → ALL PASS ✓ — G-8 can proceed")
else:
    log(f"  → {FAIL} FAIL — revisar antes de G-8")

log(f"\n[G-7 SANITY DONE]")
