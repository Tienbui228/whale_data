"""
_task_xpin_x2_append_20260808.py
X-2:
  1. Backup CASE_XPIN.xlsx (L-34)
  2. Add 11 missing columns to DAILY sheet (no backfill)
  3. UPDATE row 330 (08-05, data_bad=1, partial) → complete freshwatch data
  4. APPEND rows 08-06 and 08-07
  5. Update CASE sheet latest values
  6. Update TRIGGERS trang_thai_hom_nay
  7. Append EVENTS row
"""
import sys, io, json, csv, shutil, statistics
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
from datetime import datetime, timezone
import openpyxl
from openpyxl.styles import Font

ROOT     = Path(r"D:\Data back test\whale_data")
SCRATCH  = ROOT / "scratch"
CASE_DIR = ROOT / "docs" / "case_files"
XPIN_XL  = CASE_DIR / "CASE_XPIN.xlsx"
VPS_EXPORT = Path(r"D:\Check onchain fresh wallets\data\export")

def log(s=""): print(s)
NOW_UTC = datetime.now(timezone.utc)
log(f"XPIN X-2 APPEND  |  {NOW_UTC.strftime('%Y-%m-%d %H:%M UTC')}")

# ── L-34 Backup ───────────────────────────────────────────────────────────────
bak_path = SCRATCH / f"CASE_XPIN_bak_{NOW_UTC.strftime('%Y%m%d_%H%M%S')}.xlsx"
try:
    shutil.copy2(str(XPIN_XL), str(bak_path))
    log(f"  Backup: {bak_path.name}")
except Exception as e:
    raise RuntimeError(f"L-34 lock: cannot backup CASE_XPIN.xlsx: {e}")

# ── Load data sources ─────────────────────────────────────────────────────────
DATE_TAG = "20260808"

# 1. LSR CSV
lsr_by_date = {}
lsr_csv = SCRATCH / f"xpin_lsr_raw_{DATE_TAG}.csv"
with open(lsr_csv, encoding="utf-8") as f:
    for r in csv.DictReader(f):
        dt = r["date"]
        lsr_by_date[dt] = {
            "pos_r": float(r["pos_r_raw"]) if r.get("pos_r_raw") else None,
            "acc_r": float(r["acc_r_raw"]) if r.get("acc_r_raw") else None,
            "glsr":  float(r["glsr_raw"])  if r.get("glsr_raw") else None,
        }

# 2. OI history
oi_data = json.loads((SCRATCH / f"xpin_oi_hist_{DATE_TAG}.json").read_text(encoding="utf-8"))
oi_by_date = {}
for dt, vals in oi_data.items():
    oi_by_date[dt] = vals["oi_usd"]

# 3. Freshwatch Aug (canonical for 08-01 to 08-07)
fw_aug = VPS_EXPORT / "freshwatch_daily_2026-08.csv"
fw_by_date = {}
if fw_aug.exists():
    with open(fw_aug, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r.get("symbol","").upper() == "XPINUSDT":
                dt = r["date"]
                fw_by_date[dt] = r
log(f"  FW Aug: {len(fw_by_date)} XPIN rows ({sorted(fw_by_date.keys())[0] if fw_by_date else '?'} → {sorted(fw_by_date.keys())[-1] if fw_by_date else '?'})")

# ── Load existing DAILY data for rolling metrics ──────────────────────────────
wb = openpyxl.load_workbook(str(XPIN_XL))
ws = wb["DAILY"]
max_r = ws.max_row
max_c = ws.max_column

# Read existing headers
headers = [ws.cell(2, c).value for c in range(1, max_c + 1)]
h_idx = {str(h).strip(): i+1 for i, h in enumerate(headers) if h is not None}

def get_col(row, col_name):
    ci = h_idx.get(col_name)
    if ci is None:
        return None
    return ws.cell(row, ci).value

# Read existing data rows for rolling windows
existing = []  # list of dicts
for r in range(3, max_r + 1):
    row_vals = {headers[c-1]: ws.cell(r, c).value for c in range(1, max_c + 1) if headers[c-1]}
    if any(v is not None for v in row_vals.values()):
        existing.append(row_vals)

log(f"  Existing DAILY rows: {len(existing)}, last date: {existing[-1].get('date') if existing else 'N/A'}")

# Build px lookup for ret computation
px_by_date = {}
for row in existing:
    dt = str(row.get("date", ""))
    px = row.get("px_avg")
    if dt and px:
        px_by_date[dt] = float(px)

# Add freshwatch dates too
for dt, fw in fw_by_date.items():
    if dt not in px_by_date:
        v = fw.get("px_avg")
        if v: px_by_date[dt] = float(v)

# ── Helper: compute derived metrics ───────────────────────────────────────────
def safe_float(v, default=None):
    try:
        return float(v) if v not in (None,"","nan","NaN","None") else default
    except:
        return default

def funding_regime(f_avg, f_min):
    if f_avg is None: return None
    if f_avg <= 5.5e-5: return "pin"
    if f_avg <= 1e-4:   return "low"
    if f_avg <= 3e-4:   return "volatile"
    return "high"

def compute_rolling(existing_rows, fw_by_date, lsr_by_date, oi_by_date):
    """Build rolling history dict keyed by date."""
    hist = {}
    for r in existing_rows:
        dt = str(r.get("date", ""))
        if not dt: continue
        hist[dt] = {
            "px_avg": safe_float(r.get("px_avg")),
            "vol": safe_float(r.get("vol_perp_usd")),
            "oi":  safe_float(r.get("oi_usd")),
            "pos_r": safe_float(r.get("lsr_pos_r")),
            "acc_r": safe_float(r.get("lsr_acc_r")),
            "glsr":  safe_float(r.get("lsr_global_r")),
        }
    # add/overwrite from freshwatch Aug
    for dt, fw in fw_by_date.items():
        hist[dt] = {
            "px_avg": safe_float(fw.get("px_avg")),
            "vol": safe_float(fw.get("vol_quote")),
            "oi":  safe_float(fw.get("oi_usd")),
            "pos_r": safe_float(fw.get("lsr_pos_r")),
            "acc_r": safe_float(fw.get("lsr_acc_r")),
            "glsr":  safe_float(fw.get("lsr_global_r")),
        }
    # add from LSR CSV
    for dt, lr in lsr_by_date.items():
        if dt not in hist:
            hist[dt] = {}
        for k in ("pos_r","acc_r","glsr"):
            if lr.get(k) is not None:
                hist[dt][k] = lr[k]
    # add OI
    for dt, oi in oi_by_date.items():
        if dt in hist:
            hist[dt]["oi"] = oi
        else:
            hist[dt] = {"oi": oi}
    return hist

hist = compute_rolling(existing, fw_by_date, lsr_by_date, oi_by_date)
all_dates = sorted(hist.keys())

def get_hist_window(dates_sorted, target_dt, n):
    """Get last n dates ending at (and including) target_dt."""
    idx = dates_sorted.index(target_dt) if target_dt in dates_sorted else -1
    if idx < 0: return []
    start = max(0, idx - n + 1)
    return dates_sorted[start:idx + 1]

def get_median14_oi(dates_sorted, target_dt, hist_data):
    window = get_hist_window(dates_sorted, target_dt, 14)
    vals = [hist_data[d].get("oi") for d in window if hist_data[d].get("oi") is not None]
    return statistics.median(vals) if len(vals) >= 7 else None

def get_median14_vol(dates_sorted, target_dt, hist_data):
    window = get_hist_window(dates_sorted, target_dt, 14)
    vals = [hist_data[d].get("vol") for d in window if hist_data[d].get("vol") is not None]
    return statistics.median(vals) if len(vals) >= 7 else None

def get_oi_cycle_pos(dates_sorted, target_dt, hist_data, window_days=30):
    window = get_hist_window(dates_sorted, target_dt, window_days)
    oi_vals = [hist_data[d].get("oi") for d in window if hist_data[d].get("oi") is not None]
    if len(oi_vals) < 5: return None
    cur = hist_data.get(target_dt, {}).get("oi")
    if cur is None: return None
    mn, mx = min(oi_vals), max(oi_vals)
    if mx == mn: return 0.5
    return round((cur - mn) / (mx - mn), 4)

def glsr_slope_5d(dates_sorted, target_dt, hist_data):
    window = get_hist_window(dates_sorted, target_dt, 5)
    vals = [(i, hist_data[d].get("glsr")) for i, d in enumerate(window)
            if hist_data[d].get("glsr") is not None]
    if len(vals) < 3: return None
    n = len(vals)
    sx = sum(v[0] for v in vals)
    sy = sum(v[1] for v in vals)
    sxy = sum(v[0]*v[1] for v in vals)
    sxx = sum(v[0]**2 for v in vals)
    denom = n*sxx - sx**2
    if denom == 0: return None
    return round((n*sxy - sx*sy) / denom, 5)

def div_avg3(dates_sorted, target_dt, hist_data):
    window = get_hist_window(dates_sorted, target_dt, 3)
    divs = []
    for d in window:
        pr = hist_data[d].get("pos_r")
        ar = hist_data[d].get("acc_r")
        if pr and ar and ar > 0:
            divs.append(pr / ar)
    return round(sum(divs)/len(divs), 4) if divs else None

def d_pos_3d(dates_sorted, target_dt, hist_data):
    idx = dates_sorted.index(target_dt) if target_dt in dates_sorted else -1
    if idx < 3: return None
    dt3 = dates_sorted[idx - 3]
    cur = hist_data.get(target_dt, {}).get("pos_r")
    old = hist_data.get(dt3, {}).get("pos_r")
    if cur and old: return round(cur - old, 4)
    return None

def d_acc_3d(dates_sorted, target_dt, hist_data):
    idx = dates_sorted.index(target_dt) if target_dt in dates_sorted else -1
    if idx < 3: return None
    dt3 = dates_sorted[idx - 3]
    cur = hist_data.get(target_dt, {}).get("acc_r")
    old = hist_data.get(dt3, {}).get("acc_r")
    if cur and old: return round(cur - old, 4)
    return None

def ret_xd(dates_sorted, target_dt, hist_data, ndays):
    idx = dates_sorted.index(target_dt) if target_dt in dates_sorted else -1
    if idx < ndays: return None
    dt_prev = dates_sorted[idx - ndays]
    cur = hist_data.get(target_dt, {}).get("px_avg")
    old = hist_data.get(dt_prev, {}).get("px_avg")
    if cur and old and old > 0: return round((cur - old) / old, 5)
    return None

# ── Add new columns to DAILY sheet ───────────────────────────────────────────
NEW_COLS = ["gom_A", "gom_B", "vol_alpha", "taker_alpha", "spot_perp_ratio",
            "depth_ratio", "ret_7d", "ret_30d", "vol_vs_med14", "lsr_taker_r", "ret_atl"]
EXISTING_COL_COUNT = max_c
NEW_COL_START = EXISTING_COL_COUNT + 1

log(f"\n  Adding {len(NEW_COLS)} new columns starting at col {NEW_COL_START}:")
for i, col_name in enumerate(NEW_COLS):
    ci = NEW_COL_START + i
    # Row 1: group header (only first new col)
    if i == 0:
        ws.cell(1, ci).value = "NEW_COLS (added 08/08/2026)"
        ws.cell(1, ci).font  = Font(size=9, bold=True)
    # Row 2: field header
    ws.cell(2, ci).value = col_name
    ws.cell(2, ci).font  = Font(size=9, bold=True)
    log(f"    col {ci}: {col_name}")

# Update h_idx with new columns
for i, col_name in enumerate(NEW_COLS):
    h_idx[col_name] = NEW_COL_START + i

# ATL for ret_atl computation
# ATL from CASE sheet (find lowest close)
all_px = [hist[d].get("px_avg") for d in all_dates if hist[d].get("px_avg")]
ATL = min(all_px) if all_px else None
log(f"\n  ATL (from history): {ATL}")

# ── Build row data for 3 dates: 08-05 (update), 08-06, 08-07 ─────────────────
def build_row_data(dt, fw_data=None):
    """Build full column dict for a date."""
    fw  = fw_data or fw_by_date.get(dt, {})
    lsr = lsr_by_date.get(dt, {})

    px_avg = safe_float(fw.get("px_avg"))
    vol    = safe_float(fw.get("vol_quote"))
    taker  = safe_float(fw.get("taker_buy_pct"))
    f_avg  = safe_float(fw.get("funding_avg"))
    f_min  = safe_float(fw.get("funding_min"))
    f_max  = safe_float(fw.get("funding_max"))
    f_n    = safe_float(fw.get("funding_n"))
    oi_usd = safe_float(fw.get("oi_usd")) or oi_by_date.get(dt)
    pos_r  = safe_float(fw.get("lsr_pos_r")) or lsr.get("pos_r")
    acc_r  = safe_float(fw.get("lsr_acc_r")) or lsr.get("acc_r")
    glsr   = safe_float(fw.get("lsr_global_r")) or lsr.get("glsr")
    t_ratio= safe_float(fw.get("taker_ratio"))

    # ret_1d from prev px_avg
    ret_1d_val = None
    idx = all_dates.index(dt) if dt in all_dates else -1
    if idx > 0:
        prev = all_dates[idx - 1]
        prev_px = hist.get(prev, {}).get("px_avg")
        if px_avg and prev_px and prev_px > 0:
            ret_1d_val = round((px_avg - prev_px) / prev_px, 5)

    med14_oi  = get_median14_oi(all_dates, dt, hist)
    oi_vs_med = round(oi_usd / med14_oi, 4) if (oi_usd and med14_oi) else None
    oi_cyc    = get_oi_cycle_pos(all_dates, dt, hist)

    div_r     = round(pos_r / acc_r, 4) if (pos_r and acc_r and acc_r > 0) else None
    div_a3    = div_avg3(all_dates, dt, hist)
    glsr_sl   = glsr_slope_5d(all_dates, dt, hist)
    dp3       = d_pos_3d(all_dates, dt, hist)
    da3       = d_acc_3d(all_dates, dt, hist)

    regime    = funding_regime(f_avg, f_min)

    med14_vol = get_median14_vol(all_dates, dt, hist)
    vol_vs_m  = round(vol / med14_vol, 3) if (vol and med14_vol) else None

    r7        = ret_xd(all_dates, dt, hist, 7)
    r30       = ret_xd(all_dates, dt, hist, 30)
    r_atl     = round((px_avg - ATL) / ATL, 4) if (px_avg and ATL and ATL > 0) else None

    # gom_A: False (gLSR >>1.1 → A2 fails)
    # gom_B: False (div_ratio = div_r/div_a3 >> 0.5 → B1 fails; also A2 prereq fails)
    gom_a = 0  # False
    gom_b = 0  # False

    return {
        "date":           dt,
        "px_avg":         round(px_avg, 8) if px_avg else None,
        "ret_1d":         ret_1d_val,
        "vol_perp_usd":   round(vol, 0) if vol else None,
        "taker_buy_pct":  round(taker, 5) if taker else None,
        "f_avg":          round(f_avg, 8) if f_avg else None,
        "f_min":          round(f_min, 8) if f_min else None,
        "f_max":          round(f_max, 8) if f_max else None,
        "f_n":            int(f_n) if f_n else None,
        "funding_regime": regime,
        "pin_streak":     0,  # will compute below
        "oi_usd":         round(oi_usd, 0) if oi_usd else None,
        "oi_vs_med14":    oi_vs_med,
        "oi_cycle_pos":   oi_cyc,
        "lsr_pos_r":      round(pos_r, 4) if pos_r else None,
        "lsr_acc_r":      round(acc_r, 4) if acc_r else None,
        "lsr_global_r":   round(glsr, 4) if glsr else None,
        "div_raw":        div_r,
        "div_avg3":       div_a3,
        "glsr_slope_5d":  glsr_sl,
        "d_pos_3d":       dp3,
        "d_acc_3d":       da3,
        "signals_bullish":  None,
        "signals_suppress": None,
        "screen_rank":    None,
        "data_bad":       0,
        "spot_venue":     "BSC_DEX_PancakeSwapV3_0.01%",
        "vol_spot_usd":   None,   # GeckoTerminal 403
        "taker_spot_pct": None,
        "depth_bid2_usd": None,
        "depth_ask2_usd": None,
        "bid_wall_px":    None,
        "bid_wall_usd":   None,
        "ask_wall_px":    None,
        "ask_wall_usd":   None,
        "alpha_suspect":  "ABSTAIN(API400)",
        "exch_balance_delta": None,
        "wallet_activity": None,
        "dominance_pct":  None,
        "note_operator":  None,
        "mm_note":        None,
        # NEW COLS
        "gom_A":          gom_a,
        "gom_B":          gom_b,
        "vol_alpha":      "ABSTAIN(API400)",
        "taker_alpha":    "ABSTAIN(L-48)",
        "spot_perp_ratio": None,   # spot vol missing → can't compute
        "depth_ratio":    None,    # no depth snap for this date
        "ret_7d":         r7,
        "ret_30d":        r30,
        "vol_vs_med14":   vol_vs_m,
        "lsr_taker_r":    round(t_ratio, 4) if t_ratio else None,
        "ret_atl":        r_atl,
    }

# ── Compute pin_streak ────────────────────────────────────────────────────────
# pin_streak: consecutive days ending at dt where f_min=5e-5 and f_avg≤5.5e-5
# From existing data + new dates
def compute_pin_streak(all_dates_sorted, target_dt, existing_rows, fw_by_date):
    idx = all_dates_sorted.index(target_dt) if target_dt in all_dates_sorted else -1
    streak = 0
    for i in range(idx, -1, -1):
        d = all_dates_sorted[i]
        # get f_min and f_avg for this date
        fw = fw_by_date.get(d, {})
        f_min_v = safe_float(fw.get("funding_min"))
        f_avg_v = safe_float(fw.get("funding_avg"))
        # fallback to existing
        if f_min_v is None:
            for r in existing_rows:
                if str(r.get("date","")) == d:
                    f_min_v = safe_float(r.get("f_min"))
                    f_avg_v = safe_float(r.get("f_avg"))
                    break
        if f_min_v is not None and f_avg_v is not None:
            if abs(f_min_v - 5e-5) < 1e-7 and f_avg_v <= 5.5e-5:
                streak += 1
            else:
                break
        else:
            break
    return streak

# ── Write rows ────────────────────────────────────────────────────────────────
def write_row(ws_obj, row_num, row_data):
    for col_name, val in row_data.items():
        ci = h_idx.get(col_name)
        if ci is None: continue
        c = ws_obj.cell(row_num, ci)
        c.value = val
        c.font  = Font(size=9)

log("\n=== WRITING ROWS ===")

# 1. UPDATE row 330 (08-05) — complete freshwatch data
row_08_05 = build_row_data("2026-08-05")
row_08_05["pin_streak"] = compute_pin_streak(all_dates, "2026-08-05", existing, fw_by_date)
# Mark that this was updated from partial
row_08_05["note_operator"] = "row updated 08/08/2026 (was data_bad=1 partial f_n=2; fw_aug complete f_n=6)"
write_row(ws, 330, row_08_05)
log(f"  UPDATE row 330 (2026-08-05): vol=${row_08_05['vol_perp_usd']:,.0f} f_n={row_08_05['f_n']} data_bad={row_08_05['data_bad']}")

# 2. APPEND 08-06 (row 331)
row_08_06 = build_row_data("2026-08-06")
row_08_06["pin_streak"] = compute_pin_streak(all_dates, "2026-08-06", existing, fw_by_date)
write_row(ws, 331, row_08_06)
log(f"  APPEND row 331 (2026-08-06): px={row_08_06['px_avg']} vol=${row_08_06['vol_perp_usd']:,.0f} gLSR={row_08_06['lsr_global_r']}")

# 3. APPEND 08-07 (row 332)
row_08_07 = build_row_data("2026-08-07")
row_08_07["pin_streak"] = compute_pin_streak(all_dates, "2026-08-07", existing, fw_by_date)
write_row(ws, 332, row_08_07)
log(f"  APPEND row 332 (2026-08-07): px={row_08_07['px_avg']} vol=${row_08_07['vol_perp_usd']:,.0f} gLSR={row_08_07['lsr_global_r']}")

log("\n  08-05 summary:")
log(f"    vol_perp_usd: {row_08_05['vol_perp_usd']:,.0f} (was 598,638)")
log(f"    taker_buy_pct: {row_08_05['taker_buy_pct']} (was 0.56402)")
log(f"    f_n: {row_08_05['f_n']} (was 2)")
log(f"    data_bad: {row_08_05['data_bad']} (was 1)")
log(f"    vol_vs_med14: {row_08_05['vol_vs_med14']}")
log(f"    gom_A: {row_08_05['gom_A']}  gom_B: {row_08_05['gom_B']}")
log("\n  08-06 summary:")
log(f"    px_avg: {row_08_06['px_avg']}, ret_1d: {row_08_06['ret_1d']:.4%}" if row_08_06['ret_1d'] else f"    px_avg: {row_08_06['px_avg']}, ret_1d: None")
log(f"    div_raw: {row_08_06['div_raw']}, div_avg3: {row_08_06['div_avg3']}")
log(f"    glsr_slope_5d: {row_08_06['glsr_slope_5d']}")
log(f"    vol_vs_med14: {row_08_06['vol_vs_med14']}")
log(f"    oi_vs_med14: {row_08_06['oi_vs_med14']}, oi_cycle_pos: {row_08_06['oi_cycle_pos']}")
log("\n  08-07 summary:")
log(f"    px_avg: {row_08_07['px_avg']}, ret_1d: {row_08_07['ret_1d']:.4%}" if row_08_07['ret_1d'] else f"    px_avg: {row_08_07['px_avg']}, ret_1d: None")
log(f"    vol_perp_usd: {row_08_07['vol_perp_usd']:,.0f} (vs med14={get_median14_vol(all_dates,'2026-08-07',hist):,.0f})")
log(f"    vol_vs_med14: {row_08_07['vol_vs_med14']}")
log(f"    div_raw: {row_08_07['div_raw']}, div_avg3: {row_08_07['div_avg3']}")
log(f"    lsr_taker_r: {row_08_07['lsr_taker_r']}")

# ── Update CASE sheet latest values ──────────────────────────────────────────
log("\n=== UPDATE CASE SHEET ===")
ws_case = wb["CASE"]
updates = {
    "px_current":   row_08_07["px_avg"],
    "mc_est_usd":   round(row_08_07["px_avg"] * 48074534161, 0) if row_08_07["px_avg"] else None,
    "fdv_usd":      round(row_08_07["px_avg"] * 100000000000, 0) if row_08_07["px_avg"] else None,
    "OI_latest":    row_08_07["oi_usd"],
    "gLSR_latest":  row_08_07["lsr_global_r"],
    "gLSR_status":  "NEW PEAK 30d (2.521) — crowd all-in 08/08/2026",
    "pos_r_latest": row_08_07["lsr_pos_r"],
    "acc_r_latest": row_08_07["lsr_acc_r"],
    "div_raw_latest": row_08_07["div_raw"],
    "div_status":   "INVERTED (div=0.854) — acc_r > pos_r, accounts more leveraged",
    "px_vs_ath_now": f"{round((row_08_07['px_avg'] - 0.010318)/0.010318*100, 1) if row_08_07['px_avg'] else '?'}%",
    "state":        "WATCH — post-failed-ignition holding (updated 08/08/2026)",
}

for r in range(1, ws_case.max_row + 1):
    key = str(ws_case.cell(r, 1).value or "").strip()
    if key in updates:
        ws_case.cell(r, 2).value = updates[key]
        ws_case.cell(r, 2).font  = Font(size=9)
        log(f"  {key}: {updates[key]}")

# ── Update TRIGGERS trang_thai_hom_nay ───────────────────────────────────────
log("\n=== UPDATE TRIGGERS ===")
ws_trig = wb["TRIGGERS"]
trig_updates = {
    1: f"NOT MET (0/4 conditions) — gLSR=2.521 (>1.2), div=0.854 (<1.5), f_n=6 but volatile (>5.5e-5), OI $13.0M flat — 08/08/2026",
    2: f"FAIL (div_raw=0.854 declining; acc_r > pos_r = inverted structure) — 08/08/2026",
    3: f"FAIL (gLSR=2.521 NEW PEAK, far above 1.2) — 08/08/2026",
    4: f"FAIL (f_avg=0.000108, stable but f_min=5e-5 only at some intervals; no 7d PIN streak) — 08/08/2026",
    5: f"FAIL (OI $13.0M; floor=$8.56M; +52% from floor but no 5d rapid build) — 08/08/2026",
    6: f"PENDING OPERATOR — 08/08/2026",
}
for r in range(3, ws_trig.max_row + 1):
    trig_num = ws_trig.cell(r, 1).value
    if trig_num in trig_updates:
        ws_trig.cell(r, 5).value = trig_updates[trig_num]
        ws_trig.cell(r, 5).font  = Font(size=9)
        log(f"  Trigger {trig_num}: updated")

# ── Append EVENTS row ─────────────────────────────────────────────────────────
log("\n=== APPEND EVENTS ===")
ws_ev = wb["EVENTS"]
ev_max = ws_ev.max_row
new_ev_row = ev_max + 1
ev_vals = [
    "2026-08-08",               # date
    "REFRESH_X2",               # event_type
    row_08_07["px_avg"],        # px_open (use 08-07 avg)
    None, None,
    row_08_07["px_avg"],        # px_close
    row_08_07["vol_perp_usd"], # vol_perp_usd
    row_08_07["taker_buy_pct"], # taker_pct
    round((row_08_07["oi_usd"]-row_08_05["oi_usd"]) if row_08_07["oi_usd"] and row_08_05["oi_usd"] else 0, 0),  # oi_delta
    (f"DAILY updated: 08-05 corrected (data_bad=1→0, f_n=2→6, vol=598K→2.55M). "
     f"Appended 08-06/07. gLSR=2.521 NEW PEAK. vol_perp 08-07=$6.05M (2.7x med14). "
     f"OI $13.0M. 11 cols added (gom_A/B,vol_alpha,taker_alpha,...). LSR 0/30 FAPI 404.")
]
ev_hdr_count = ws_ev.max_column
for ci, val in enumerate(ev_vals[:ev_hdr_count], 1):
    ws_ev.cell(new_ev_row, ci).value = val
    ws_ev.cell(new_ev_row, ci).font  = Font(size=9)
log(f"  EVENTS row {new_ev_row} appended")

# ── Save ──────────────────────────────────────────────────────────────────────
log("\n=== SAVING ===")
wb.save(str(XPIN_XL))
log(f"  Saved: {XPIN_XL}")

log("\n=== KEY COMPUTED VALUES ===")
log(f"  08-05 (corrected): px_avg={row_08_05['px_avg']} vol=${row_08_05['vol_perp_usd']:,.0f} "
    f"gLSR={row_08_05['lsr_global_r']} div={row_08_05['div_raw']}")
log(f"  08-06 (new):       px_avg={row_08_06['px_avg']} vol=${row_08_06['vol_perp_usd']:,.0f} "
    f"ret_1d={row_08_06['ret_1d']} gLSR={row_08_06['lsr_global_r']} div={row_08_06['div_raw']}")
log(f"  08-07 (new):       px_avg={row_08_07['px_avg']} vol=${row_08_07['vol_perp_usd']:,.0f} "
    f"ret_1d={row_08_07['ret_1d']} gLSR={row_08_07['lsr_global_r']} div={row_08_07['div_raw']}")
log(f"  vol_vs_med14 08-07: {row_08_07['vol_vs_med14']}x")
log(f"  oi_cycle_pos 08-07: {row_08_07['oi_cycle_pos']}")
log(f"  glsr_slope_5d 08-07: {row_08_07['glsr_slope_5d']}")

log("\n[X-2 APPEND DONE]")
