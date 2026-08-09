"""
_probe_xpin_x3_a5_20260808.py
X-3: A.5 ba-đạo-hàm table + TRIGGER-CHECK table for XPIN.
"""
import sys, io, csv, statistics
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
from datetime import datetime, timezone

ROOT    = Path(r"D:\Data back test\whale_data")
SCRATCH = ROOT / "scratch"
VPS_EXPORT = Path(r"D:\Check onchain fresh wallets\data\export")

def log(s=""): print(s)
NOW_UTC = datetime.now(timezone.utc)
log(f"XPIN X-3 A.5 + TRIGGER-CHECK  |  {NOW_UTC.strftime('%Y-%m-%d %H:%M UTC')}")

SYM = "XPINUSDT"

def safe_float(v, default=None):
    try: return float(v) if v not in (None,"","nan","NaN","None") else default
    except: return default

# ── Load all freshwatch data ────────────────────────────────────────────────────
FW_FILES = [
    SCRATCH / "freshwatch_daily_2026-06.csv",
    SCRATCH / "freshwatch_daily_2026-07.csv",
    VPS_EXPORT / "freshwatch_daily_2026-08.csv",
]

hist = {}  # date → {px_avg, vol, glsr, div_raw, div_avg3, ...}

for fw_path in FW_FILES:
    if not fw_path.exists(): continue
    with open(fw_path, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r.get("symbol","").upper() != SYM: continue
            dt = r.get("date","")
            if not dt: continue
            pos_r = safe_float(r.get("lsr_pos_r"))
            acc_r = safe_float(r.get("lsr_acc_r"))
            glsr  = safe_float(r.get("lsr_global_r"))
            div   = round(pos_r/acc_r, 4) if pos_r and acc_r and acc_r>0 else None
            hist[dt] = {
                "px_avg": safe_float(r.get("px_avg")),
                "vol":    safe_float(r.get("vol_quote")),
                "glsr":   glsr,
                "pos_r":  pos_r,
                "acc_r":  acc_r,
                "div_raw": div,
                "f_avg":  safe_float(r.get("funding_avg")),
                "f_min":  safe_float(r.get("funding_min")),
                "oi_usd": safe_float(r.get("oi_usd")),
                "taker":  safe_float(r.get("taker_buy_pct")),
            }

all_dates = sorted(hist.keys())
log(f"  History: {len(all_dates)} dates, {all_dates[0] if all_dates else '?'} → {all_dates[-1] if all_dates else '?'}")

# ── Compute rolling div_avg3 and vol_vs_med14 ─────────────────────────────────
def get_div_avg3(target_dt):
    idx = all_dates.index(target_dt) if target_dt in all_dates else -1
    if idx < 0: return None
    window = all_dates[max(0, idx-2):idx+1]
    divs = [hist[d]["div_raw"] for d in window if hist[d].get("div_raw") is not None]
    return round(statistics.mean(divs), 4) if divs else None

def get_vol_vs_med14(target_dt):
    idx = all_dates.index(target_dt) if target_dt in all_dates else -1
    if idx < 0: return None
    window = all_dates[max(0, idx-13):idx+1]
    vols = [hist[d]["vol"] for d in window if hist[d].get("vol") is not None]
    cur_vol = hist[target_dt].get("vol")
    if not cur_vol or len(vols) < 7: return None
    med = statistics.median(vols)
    return round(cur_vol / med, 3) if med > 0 else None

def get_glsr(target_dt):
    return hist.get(target_dt, {}).get("glsr")

def get_div_raw(target_dt):
    return hist.get(target_dt, {}).get("div_raw")

def find_date_n_days_before(target_dt, n):
    idx = all_dates.index(target_dt) if target_dt in all_dates else -1
    if idx < n: return None
    return all_dates[idx - n]

# Target date
TARGET = "2026-08-07"
if TARGET not in all_dates:
    log(f"  ERROR: {TARGET} not in history"); sys.exit(1)

# ── A.5 table ──────────────────────────────────────────────────────────────────
log("\n=== A.5 BA-ĐẠO-HÀM ===")

mocs = {
    "28d": find_date_n_days_before(TARGET, 28),
    "21d": find_date_n_days_before(TARGET, 21),
    "14d": find_date_n_days_before(TARGET, 14),
    "7d":  find_date_n_days_before(TARGET, 7),
    "today (08-07)": TARGET,
}

log(f"\n  Mốc dates: {mocs}")
log()
log(f"  {'Mốc':<18} {'div_avg3':>9} {'gLSR':>7} {'vol_vs_m14':>11} {'div_raw':>8} {'pos_r':>7} {'acc_r':>7}")
log(f"  {'-'*18} {'-'*9} {'-'*7} {'-'*11} {'-'*8} {'-'*7} {'-'*7}")

a5_data = {}
for label, dt in mocs.items():
    if not dt:
        log(f"  {label:<18} {'N/A':>9} {'N/A':>7} {'N/A':>11} {'N/A':>8} {'N/A':>7} {'N/A':>7}")
        a5_data[label] = None
        continue
    d3   = get_div_avg3(dt)
    gls  = get_glsr(dt)
    vvm  = get_vol_vs_med14(dt)
    dr   = get_div_raw(dt)
    pr   = hist.get(dt, {}).get("pos_r")
    ar   = hist.get(dt, {}).get("acc_r")
    a5_data[label] = {"div_avg3": d3, "glsr": gls, "vol_vs_m14": vvm, "div_raw": dr, "pos_r": pr, "acc_r": ar, "date": dt}
    log(f"  {label:<18} {str(d3 or 'N/A'):>9} {str(gls or 'N/A'):>7} {str(vvm or 'N/A'):>11} {str(dr or 'N/A'):>8} {str(pr or 'N/A'):>7} {str(ar or 'N/A'):>7}")

# %chg from 28d (peak detection)
log(f"\n  %CHG từ 28d:")
ref = a5_data.get("28d")
cur = a5_data.get("today (08-07)")
if ref and cur:
    for k in ("div_avg3", "glsr", "vol_vs_m14", "div_raw", "pos_r", "acc_r"):
        r_v = ref.get(k) if ref else None
        c_v = cur.get(k) if cur else None
        if r_v and c_v and r_v != 0:
            chg = (c_v - r_v)/abs(r_v)*100
            log(f"    {k}: {r_v} → {c_v}  ({chg:+.1f}%)")
        else:
            log(f"    {k}: N/A")

# ── TRIGGER-CHECK ──────────────────────────────────────────────────────────────
log("\n=== TRIGGER-CHECK ===")
log("(số cạnh ngưỡng — KHÔNG verdict)")

# Current values as of 08-07
cur_glsr  = hist[TARGET]["glsr"]        # 2.5211
cur_div   = hist[TARGET]["div_raw"]     # 0.8542
cur_da3   = get_div_avg3(TARGET)        # div_avg3
cur_oi    = hist[TARGET]["oi_usd"]      # 13,000,982
cur_f_avg = hist[TARGET]["f_avg"]       # 0.000108
cur_f_min = hist[TARGET]["f_min"]       # 5e-5
cur_px    = hist[TARGET]["px_avg"]      # 0.001739

# T1: NEXT_IGNITION_SETUP: gLSR<1.2 AND div>1.5 AND stable_PIN>=7d AND OI build
t1_cond1 = f"gLSR={cur_glsr:.4f} (threshold <1.2, gap: {cur_glsr-1.2:+.4f}, need -{(cur_glsr-1.2)/cur_glsr*100:.1f}%)"
t1_cond2 = f"div_raw={cur_div:.4f} (threshold >1.5, gap: {1.5-cur_div:+.4f}, need +{(1.5-cur_div)/cur_div*100:.1f}%)"
t1_cond3 = f"PIN stable: f_avg={cur_f_avg:.6f} (threshold <=5.5e-5=0.000055; gap: +{(cur_f_avg-5.5e-5)*1e6:.1f}μ above floor)"
t1_cond4 = f"OI build: oi={cur_oi/1e6:.2f}M (floor=8.56M; +20%_target=10.27M; already above but not rapid-5d)"

log(f"\nT1 NEXT_IGNITION_SETUP (0/4 met):")
log(f"  C1: {t1_cond1}")
log(f"  C2: {t1_cond2}")
log(f"  C3: {t1_cond3}")
log(f"  C4: {t1_cond4}")

# T2: DIV_RECOVERY: div_raw > 1.5 sustained >=3d
log(f"\nT2 DIV_RECOVERY (div_raw>1.5 × ≥3d):")
log(f"  div_raw now: {cur_div:.4f}, threshold 1.5, gap: {1.5-cur_div:+.4f} (+{(1.5-cur_div)/cur_div*100:.1f}%)")
div_hist = [(d, hist[d]["div_raw"]) for d in all_dates[-10:] if hist[d].get("div_raw")]
log(f"  Last 10 div_raw: {[(d,v) for d,v in div_hist[-5:]]}")

# T3: gLSR_RESET: gLSR<1.2 sustained >=3d
log(f"\nT3 gLSR_RESET (gLSR<1.2 × ≥3d):")
log(f"  gLSR now: {cur_glsr:.4f}, threshold 1.2, gap: {cur_glsr-1.2:+.4f} (need -{(cur_glsr-1.2)/cur_glsr*100:.1f}% drop from here)")
glsr_hist = [(d, hist[d]["glsr"]) for d in all_dates[-7:] if hist[d].get("glsr")]
log(f"  Last 7 gLSR: {[(d, round(v,4)) for d,v in glsr_hist]}")

# T4: FUND_RESTABLE: f_avg<=5.5e-5 AND f_min=5e-5 >=7 intervals liên tiếp
# Calculate consecutive pin-eligible days
pin_streak = 0
for dt in reversed(all_dates):
    r = hist.get(dt, {})
    fa = r.get("f_avg")
    fm = r.get("f_min")
    if fa is not None and fm is not None:
        if fa <= 5.5e-5 and abs(fm - 5e-5) < 1e-7:
            pin_streak += 1
        else:
            break
log(f"\nT4 FUND_RESTABLE (f_avg<=5.5e-5 AND f_min=5e-5 ×≥7d):")
log(f"  f_avg 08-07: {cur_f_avg:.6f} (threshold 5.5e-5=0.0000550; gap: {(cur_f_avg-5.5e-5)*1e6:+.1f}μ)")
log(f"  f_min 08-07: {cur_f_min:.6f} (at floor ✓)")
log(f"  Current PIN streak (all-at-floor): {pin_streak} days")

# T5: OI_BUILD: OI increase >20% from floor $8.56M in 5d
oi_floor_30d = 8562000
oi_target = oi_floor_30d * 1.20
recent_oi_5d = [(d, hist[d]["oi_usd"]) for d in all_dates[-5:] if hist[d].get("oi_usd")]
oi_5d_min = min(v for _, v in recent_oi_5d) if recent_oi_5d else None
oi_5d_max = max(v for _, v in recent_oi_5d) if recent_oi_5d else None
oi_5d_pct = (oi_5d_max - oi_5d_min) / oi_5d_min * 100 if oi_5d_min else None

log(f"\nT5 OI_BUILD (OI >20% from floor ${oi_floor_30d/1e6:.2f}M in 5d):")
log(f"  OI now: ${cur_oi/1e6:.3f}M, floor: ${oi_floor_30d/1e6:.3f}M, target: ${oi_target/1e6:.3f}M")
log(f"  OI last 5d: {[(d, round(v/1e6,3)) for d,v in recent_oi_5d]}")
log(f"  5d OI swing: min=${oi_5d_min/1e6:.3f}M → max=${oi_5d_max/1e6:.3f}M ({oi_5d_pct:+.1f}%)" if oi_5d_pct else "  5d OI swing: N/A")

# T6: BITMART_VOL_VERIFY: Pending operator
log(f"\nT6 BITMART_VOL_VERIFY:")
log(f"  PENDING OPERATOR — requires live check of BitMart order book vs volume")

# ── Additional context: pin_history ──────────────────────────────────────────
log(f"\n=== PIN STREAK HISTORY (last 14d) ===")
log(f"  {'date':<12} {'f_avg':>10} {'f_min':>10} {'pin?':>6}")
for dt in all_dates[-14:]:
    r = hist.get(dt, {})
    fa = r.get("f_avg")
    fm = r.get("f_min")
    is_pin = "✓" if (fa and fa<=5.5e-5 and fm and abs(fm-5e-5)<1e-7) else "✗"
    log(f"  {dt:<12} {str(round(fa,6) if fa else 'N/A'):>10} {str(round(fm,6) if fm else 'N/A'):>10} {is_pin:>6}")

log("\n[X-3 DONE]")
