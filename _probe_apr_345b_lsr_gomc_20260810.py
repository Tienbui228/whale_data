"""
_probe_apr_345b_lsr_gomc_20260810.py
A-345b fix: Read LSR from freshwatch CSVs + re-run div_avg3/gLSR/GOM-C.
"""
import sys, io, csv
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
from datetime import datetime, timezone
from collections import defaultdict

ROOT    = Path(r"D:\Data back test\whale_data")
SCRATCH = ROOT / "scratch"
DATE_TAG = "20260810"
SYM = "APRUSDT"
SYM_LOWER = "apr"

def log(s=""): print(s)
NOW = datetime.now(timezone.utc)
log(f"A-345b LSR+GOMC FIX  |  {NOW.strftime('%Y-%m-%d %H:%M UTC')}")

def safe_float(v, d=None):
    try: return float(v) if v not in (None, "", "None") else d
    except: return d

# ── Load perp CSV ──────────────────────────────────────────────────────────
perp_rows = []
with open(SCRATCH / f"{SYM_LOWER}_perp_{DATE_TAG}.csv", encoding="utf-8") as f:
    for r in csv.DictReader(f): perp_rows.append(r)
all_dates = [r["date"] for r in perp_rows]
N = len(all_dates)
ret_all = [safe_float(r["ret_1d"]) for r in perp_rows]
taker_all = [safe_float(r["taker_pct"]) for r in perp_rows]

# ── Load funding ───────────────────────────────────────────────────────────
fund_by_day = defaultdict(list)
with open(SCRATCH / f"{SYM_LOWER}_funding_{DATE_TAG}.csv", encoding="utf-8") as f:
    for r in csv.DictReader(f):
        d = r.get("date",""); rate = safe_float(r.get("fundingRate"))
        if d and rate is not None: fund_by_day[d].append(rate)
f_avg_by_d = {d: sum(v)/len(v) for d,v in fund_by_day.items()}
f_avg_all = [f_avg_by_d.get(d) for d in all_dates]

# ── Load freshwatch LSR ────────────────────────────────────────────────────
log(f"\n=== Freshwatch LSR for APRUSDT ===")
lsr_by_d = {}
fw_count = 0
for fw_csv in sorted(SCRATCH.glob("freshwatch_daily_*.csv")):
    log(f"  Reading: {fw_csv.name}")
    with open(fw_csv, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        cols = reader.fieldnames or []
        log(f"    Columns: {cols[:20]}")
        for row in reader:
            sym = row.get("symbol","").upper()
            if sym != SYM: continue
            dt = row.get("date","")[:10]
            if not dt: continue
            # Try various column names for LSR
            pos_r = safe_float(row.get("lsr_pos_r") or row.get("pos_r"))
            acc_r = safe_float(row.get("lsr_acc_r") or row.get("acc_r"))
            glsr  = safe_float(row.get("lsr_global_r") or row.get("gLSR") or row.get("glsr"))
            if pos_r is not None or acc_r is not None:
                lsr_by_d[dt] = {"pos_r": pos_r, "acc_r": acc_r, "glsr": glsr}
                fw_count += 1

log(f"  APRUSDT LSR rows: {fw_count} dates")
if lsr_by_d:
    sorted_d = sorted(lsr_by_d.keys())
    log(f"  Date range: {sorted_d[0]} → {sorted_d[-1]}")
    log(f"  Sample (last 5):")
    for d in sorted_d[-5:]:
        v = lsr_by_d[d]
        log(f"    {d}: pos_r={v['pos_r']} acc_r={v['acc_r']} gLSR={v['glsr']}")

# Build arrays
pos_r_all = [safe_float(lsr_by_d.get(d,{}).get("pos_r")) for d in all_dates]
acc_r_all = [safe_float(lsr_by_d.get(d,{}).get("acc_r")) for d in all_dates]
glsr_all  = [safe_float(lsr_by_d.get(d,{}).get("glsr"))  for d in all_dates]

pos_r_count = sum(1 for v in pos_r_all if v is not None)
log(f"\n  pos_r non-null: {pos_r_count}/{N} dates")
log(f"  Recent pos_r (last 30d):")
for i in range(max(0,N-30), N):
    d = all_dates[i]; p = pos_r_all[i]; a = acc_r_all[i]; g = glsr_all[i]
    if any(v is not None for v in [p,a,g]):
        log(f"    {d}: pos_r={p} acc_r={a} gLSR={g}")

# ── div_avg3 ───────────────────────────────────────────────────────────────
div_avg3_all = [None] * N
for i in range(2, N):
    p3 = [v for v in pos_r_all[i-2:i+1] if v is not None]
    a3 = [v for v in acc_r_all[i-2:i+1] if v is not None]
    if len(p3) == 3 and len(a3) == 3:
        ap = sum(p3)/3; aa = sum(a3)/3
        div_avg3_all[i] = round(ap/aa, 4) if aa != 0 else None

div_vals = [(all_dates[i], div_avg3_all[i]) for i in range(N) if div_avg3_all[i] is not None]
log(f"\n=== div_avg3 ===")
log(f"  Non-null count: {len(div_vals)}")
if div_vals:
    vals = [v for _,v in div_vals]
    last_valid_div_d, last_valid_div = div_vals[-1]
    log(f"  Last valid: {last_valid_div_d} div_avg3={last_valid_div}")
    log(f"  min/max: {min(vals):.4f} / {max(vals):.4f}")
    log(f"  Recent (last 20 with data):")
    for d,v in div_vals[-20:]:
        flag = " ← HEDGE" if v <= 0.5 else (" ← GOM?" if v > 1.5 else "")
        log(f"    {d}: {v:.4f}{flag}")

# ── gLSR slope ─────────────────────────────────────────────────────────────
slope_all = [None] * N
for i in range(5, N):
    g = glsr_all[i]; gp = glsr_all[i-5]
    if g is not None and gp is not None and gp > 0:
        slope_all[i] = round(g/gp, 4)

glsr_vals = [(all_dates[i], glsr_all[i]) for i in range(N) if glsr_all[i] is not None]
log(f"\n=== gLSR ===")
if glsr_vals:
    last_glsr_d, last_glsr = glsr_vals[-1]
    log(f"  Last valid gLSR: {last_glsr_d} gLSR={last_glsr}")
    slope_last = next((slope_all[i] for i in range(N-1,-1,-1) if slope_all[i] is not None), None)
    log(f"  Last slope5d: {slope_last}")
    log(f"  Recent (last 10 with data):")
    for d,v in glsr_vals[-10:]:
        idx = all_dates.index(d)
        sl = slope_all[idx]
        log(f"    {d}: gLSR={v:.4f} slope5d={sl}")

# ── GOM-C rechấm WITH pos_r data ─────────────────────────────────────────
log(f"\n=== GOM-C RECHẤM (với LSR data) ===")
log(f"  Spec: C2=|f_avg|≤2e-4, C3=taker∈[40%,55%], d_pos=Δpos_r≥0")
NEUTRAL = 1e-4
GOMC_days = []

log(f"\n  Date         f_avg     C2      taker   C3    pos_r    d_pos  GOM-C")
log(f"  {'-'*70}")
for i in range(1, N):
    d = all_dates[i]
    f = f_avg_all[i]
    tk = taker_all[i]
    pos_r = pos_r_all[i]; pos_r_prev = pos_r_all[i-1]

    c2 = (abs(f) <= 2*NEUTRAL) if f is not None else None
    c3 = (40.0 <= tk <= 55.0) if tk is not None else None
    d_pos = None
    if pos_r is not None and pos_r_prev is not None:
        d_pos = (pos_r - pos_r_prev) >= 0

    gomc = (c2 == True) and (c3 == True) and (d_pos == True)
    if gomc:
        GOMC_days.append(d)

    if i >= N-20:
        f_s = f"{f:.6f}" if f is not None else "  N/A   "
        c2_s = "PASS" if c2 else ("FAIL" if c2==False else "N/A ")
        tk_s = f"{tk:.1f}" if tk is not None else "N/A "
        c3_s = "PASS" if c3 else ("FAIL" if c3==False else "N/A ")
        pos_s = f"{pos_r:.4f}" if pos_r is not None else "  N/A "
        dp_s = "Y" if d_pos==True else ("N" if d_pos==False else "?")
        g_s = "GOM-C ✓" if gomc else ""
        log(f"  {d}  {f_s}  {c2_s}  {tk_s:6s}  {c3_s}  {pos_s}  {dp_s}   {g_s}")

log(f"\n  GOM-C PROVISIONAL days: {len(GOMC_days)}")
if GOMC_days:
    for d in GOMC_days: log(f"    {d}")
else:
    log(f"    (none in dataset)")

# All historical GOM-C
all_gomc = []
for i in range(1, N):
    d = all_dates[i]; f = f_avg_all[i]; tk = taker_all[i]
    pos_r = pos_r_all[i]; pos_r_prev = pos_r_all[i-1]
    c2 = (abs(f) <= 2*NEUTRAL) if f is not None else None
    c3 = (40.0 <= tk <= 55.0) if tk is not None else None
    d_pos = None
    if pos_r is not None and pos_r_prev is not None:
        d_pos = (pos_r - pos_r_prev) >= 0
    if (c2 == True) and (c3 == True) and (d_pos == True):
        all_gomc.append(d)

log(f"\n  All GOM-C days (full history): {len(all_gomc)}")
for d in all_gomc: log(f"    {d}")

# ── Machine classification re-run ─────────────────────────────────────────
log(f"\n=== MACHINE CLASSIFICATION (updated) ===")
PIN_LO, PIN_HI = 4e-5, 6e-5
pin_streak_all = [0] * N
for i in range(N):
    f = f_avg_all[i]
    if f is not None and PIN_LO <= f <= PIN_HI:
        pin_streak_all[i] = (pin_streak_all[i-1]+1) if i > 0 else 1
    else:
        pin_streak_all[i] = 0
current_pin_streak = pin_streak_all[-1]
pin_days = sum(1 for v in pin_streak_all if v > 0)
pin_pct = pin_days/N*100

last_div = div_avg3_all[-1] if div_avg3_all else None
last_valid_div_v = next((div_avg3_all[i] for i in range(N-1,-1,-1) if div_avg3_all[i] is not None), None)
last_valid_div_age = next((N-1-i for i in range(N-1,-1,-1) if div_avg3_all[i] is not None), None)

log(f"  last valid div_avg3={last_valid_div_v} ({last_valid_div_age}d ago)")
log(f"  current pin_streak={current_pin_streak}, pin%={pin_pct:.1f}%")
log(f"  last gLSR={last_glsr if glsr_vals else 'N/A'}, slope5d={slope_last if glsr_vals else 'N/A'}")

if last_valid_div_v is not None and last_valid_div_age is not None and last_valid_div_age <= 10:
    if last_valid_div_v > 1.5 and current_pin_streak > 0:
        cls = "GOM-SIDE (div>1.5 + pin)"
    elif last_valid_div_v < 0.5 and current_pin_streak == 0:
        cls = "FARM-SIDE (div<0.5 + no pin)"
    else:
        cls = "ANALYSIS"
else:
    cls = "ANALYSIS (LSR stale or null)"

log(f"  → {cls}")
log(f"\n[A-345b DONE]")
