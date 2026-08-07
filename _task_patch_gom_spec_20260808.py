"""
_task_patch_gom_spec_20260808.py
Patch CASE_HEI.xlsx: Fix GOM-A/B per spec verbatim + add oi_cycle_pos + rows 07/08 + 08/08.

THU TU PER OPERATOR (muc 3 chay tren code muc 1 da va — KHONG song song):
  1. Load CSVs + fetch live data (07/08 fn=6, 08/08 closed, 08/08 LSR)
  2. Recompute tat ca rolling arrays voi dieu kien GOM chinh xac
  3. Re-score GOM-A+B cho toan bo window 09/07->08/08
  4. Cap nhat 07/08 row (fn gio = 6), append 08/08 row
  5. Save + L-32 verify
  6. In bang re-cham + full rows 27 cols
  7. Append EVENTS entry spec-drift
  8. In intraday 09/08 snapshot (khong ghi DAILY)

GOM-A per gom_detect_spec.md v1.4 §1 (operator CASE adaptation 08/08/2026):
  A1 = div_avg3 >= 1.5        # lsr_accum: nhien lieu tich luy
  A2 = avg5(gLSR) <= 1.1      # MUC nhien lieu toan thi — KHONG phai slope
  A3 = glsr_slope_5d <= 1.15  # CHIEU nhien lieu — nguong 1.15 KHONG phai 1.0
  A4 = d_pos_3d >= 0 OR pos_rerate(pos_r +0.25 vs avg5_pos_r, >=3d lien tuc)
  A5 = oi_cycle_pos <= 0.5    # OI trong vung tich luy — window 30d rolling
  GOM-A = A1 AND A2 AND A3 AND (A4 OR A5)

GOM-B per spec §1:
  B1 = div_avg3_low_streak >= 7  # hedge_structure >=7d: div_avg3 <= 0.5 lien tuc
  B2 = pin_streak >= 5           # funding_pinned >=5d
  B3 = taker_absorb_streak >= 7 AND range_7d <= 10%  # absorption
  B4 = NOT funding_neg_div       # NOT (f_avg<0 AND |ret_1d|<2%)
  GOM-B = B1 AND (B2 OR B3) AND B4
"""
import sys, io, json, csv, shutil
from pathlib import Path
from datetime import datetime, timezone
from collections import defaultdict
import urllib.request

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter

SCRATCH  = Path(r"D:\Data back test\whale_data\scratch")
CASE_DIR = Path(r"D:\Data back test\whale_data\docs\case_files")
XLSX     = CASE_DIR / "CASE_HEI.xlsx"
PIN_LO, PIN_HI = 4e-5, 6e-5

def log(s=""): print(s)
def safe_float(v, d=None):
    try:
        return float(v) if v not in (None, "", "None") else d
    except: return d
def fetch_json(url, timeout=25):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        return {"_error": str(e)}

NOW_UTC = datetime.now(timezone.utc)
log("=" * 70)
log(f"PATCH CASE_HEI GOM-A/B PER SPEC  |  {NOW_UTC.strftime('%Y-%m-%d %H:%M UTC')}")
log("=" * 70)

# ── 0. Backup ─────────────────────────────────────────────────────────────────
backup = SCRATCH / f"CASE_HEI_BACKUP_gom_patch_{NOW_UTC.strftime('%Y%m%d_%H%M')}.xlsx"
shutil.copy2(XLSX, backup)
log(f"  Backup: {backup}")

# ── 1. Load CSVs ──────────────────────────────────────────────────────────────
def load_csv(path):
    p = Path(path)
    if not p.exists():
        log(f"  WARN: CSV missing: {p}")
        return []
    with open(p, encoding="utf-8") as f:
        return list(csv.DictReader(f))

perp_rows = load_csv(SCRATCH / "hei_perp_full_20260808.csv")
spot_rows = load_csv(SCRATCH / "hei_spot_full_20260808.csv")
lsr_rows  = load_csv(SCRATCH / "hei_lsr_raw_20260808.csv")
log(f"  CSVs loaded: perp={len(perp_rows)}, spot={len(spot_rows)}, lsr={len(lsr_rows)}")

perp_by_d = {r["date"]: r for r in perp_rows}
spot_by_d = {r["date"]: r for r in spot_rows}
lsr_by_d  = {r["date"]: r for r in lsr_rows}

# ── 2. Fetch live data ─────────────────────────────────────────────────────────
log("\n--- FETCHING LIVE DATA ---")

log("  Funding rates (all history)...")
fund_raw = fetch_json("https://fapi.binance.com/fapi/v1/fundingRate?symbol=HEIUSDT&limit=1000")
fund_by_day = defaultdict(list)
if isinstance(fund_raw, list):
    for fr in fund_raw:
        ts = fr.get("fundingTime")
        if ts:
            dt = datetime.fromtimestamp(int(ts) / 1000, tz=timezone.utc).strftime("%Y-%m-%d")
            fund_by_day[dt].append(float(fr.get("fundingRate", 0)))
log(f"  Funding days={len(fund_by_day)}, 07/08={len(fund_by_day.get('2026-08-07',[]))}, "
    f"08/08={len(fund_by_day.get('2026-08-08',[]))}")

log("  OI hist 30d...")
oih_raw = fetch_json("https://fapi.binance.com/futures/data/openInterestHist"
                     "?symbol=HEIUSDT&period=1d&limit=30")
oi_by_d = {}
if isinstance(oih_raw, list):
    for o in oih_raw:
        ts = o.get("timestamp")
        if ts:
            dt = datetime.fromtimestamp(int(ts) / 1000, tz=timezone.utc).strftime("%Y-%m-%d")
            oi_by_d[dt] = {"oi_usd":   float(o.get("sumOpenInterestValue", 0)),
                            "oi_token": float(o.get("sumOpenInterest", 0))}
log(f"  OI hist days={len(oi_by_d)}, range={min(oi_by_d) if oi_by_d else '?'} -> {max(oi_by_d) if oi_by_d else '?'}")

def fetch_klines_day(date_str, is_perp=True):
    """Return dict with OHLCV + taker_pct for a single closed day."""
    from datetime import datetime, timezone
    y, m, d = int(date_str[:4]), int(date_str[5:7]), int(date_str[8:10])
    ts_s = int(datetime(y, m, d, 0, 0, 0, tzinfo=timezone.utc).timestamp() * 1000)
    ts_e = ts_s + 86_400_000
    if is_perp:
        url = (f"https://fapi.binance.com/fapi/v1/klines"
               f"?symbol=HEIUSDT&interval=1d&startTime={ts_s}&endTime={ts_e}&limit=2")
    else:
        url = (f"https://api.binance.com/api/v3/klines"
               f"?symbol=HEIUSDT&interval=1d&startTime={ts_s}&endTime={ts_e}&limit=2")
    raw = fetch_json(url)
    if isinstance(raw, list) and raw:
        k = raw[0]
        vol_q = float(k[7])
        taker_q = float(k[10])
        if is_perp:
            return {"o": float(k[1]), "h": float(k[2]), "l": float(k[3]), "c": float(k[4]),
                    "vol_quote_usd": vol_q,
                    "taker_pct": round(taker_q / vol_q * 100, 2) if vol_q else None,
                    "ret_1d": None}
        else:
            return {"vol_spot_usd": vol_q,
                    "taker_spot_pct": round(taker_q / vol_q * 100, 2) if vol_q else None}
    return {}

log("  Klines 07/08 perp+spot...")
perp_0807 = fetch_klines_day("2026-08-07", is_perp=True)
spot_0807_raw = fetch_klines_day("2026-08-07", is_perp=False)
if perp_0807:
    vol_p07 = perp_0807.get("vol_quote_usd") or 1
    vol_s07 = spot_0807_raw.get("vol_spot_usd") or 0
    spot_0807 = {**spot_0807_raw,
                 "spot_perp_ratio": round(vol_s07 / vol_p07, 3),
                 "l29_flag": "CLEAR" if vol_s07 / vol_p07 < 3 else "L29_ABSTAIN"}
else:
    spot_0807 = spot_0807_raw
log(f"  Perp 07/08: o={perp_0807.get('o')} c={perp_0807.get('c')} "
    f"vol=${perp_0807.get('vol_quote_usd', '?'):.0f}" if perp_0807.get('vol_quote_usd') else
    f"  Perp 07/08: {perp_0807}")

log("  Klines 08/08 perp+spot...")
perp_0808 = fetch_klines_day("2026-08-08", is_perp=True)
spot_0808_raw = fetch_klines_day("2026-08-08", is_perp=False)
if perp_0808:
    vol_p08 = perp_0808.get("vol_quote_usd") or 1
    vol_s08 = spot_0808_raw.get("vol_spot_usd") or 0
    spot_0808 = {**spot_0808_raw,
                 "spot_perp_ratio": round(vol_s08 / vol_p08, 3),
                 "l29_flag": "CLEAR" if vol_s08 / vol_p08 < 3 else "L29_ABSTAIN"}
    # ret_1d for 08/08 = close(08/08) / close(07/08) - 1
    c07 = perp_0807.get("c")
    c08 = perp_0808.get("c")
    if c07 and c08:
        perp_0808["ret_1d"] = round((c08 - c07) / c07 * 100, 4)
else:
    spot_0808 = spot_0808_raw
log(f"  Perp 08/08: o={perp_0808.get('o')} c={perp_0808.get('c')} "
    f"ret={perp_0808.get('ret_1d')}%")

log("  LSR 30d (pos_r + acc_r + gLSR + taker_lsr)...")
lsr_pos_raw  = fetch_json("https://fapi.binance.com/futures/data/topLongShortPositionRatio"
                           "?symbol=HEIUSDT&period=1d&limit=30")
lsr_acc_raw  = fetch_json("https://fapi.binance.com/futures/data/topLongShortAccountRatio"
                           "?symbol=HEIUSDT&period=1d&limit=30")
glsr_raw_f   = fetch_json("https://fapi.binance.com/futures/data/globalLongShortAccountRatio"
                           "?symbol=HEIUSDT&period=1d&limit=30")
taker_raw    = fetch_json("https://fapi.binance.com/futures/data/takerlongshortRatio"
                           "?symbol=HEIUSDT&period=1d&limit=30")

lsr_live = {}
def merge_lsr(raw, key_name, field):
    if isinstance(raw, list):
        for r in raw:
            ts = r.get("timestamp")
            if ts:
                dt = datetime.fromtimestamp(int(ts) / 1000, tz=timezone.utc).strftime("%Y-%m-%d")
                if dt not in lsr_live:
                    lsr_live[dt] = {}
                v = r.get(key_name)
                if v is not None:
                    lsr_live[dt][field] = float(v)

merge_lsr(lsr_pos_raw,  "longShortRatio", "pos_r_raw")
merge_lsr(lsr_acc_raw,  "longShortRatio", "acc_r_raw")
merge_lsr(glsr_raw_f,   "longShortRatio", "glsr_raw")
merge_lsr(taker_raw,    "buySellRatio",   "taker_lsr_raw")
log(f"  LSR live days={len(lsr_live)}, range={min(lsr_live) if lsr_live else '?'} -> {max(lsr_live) if lsr_live else '?'}")

# Override lsr_by_d with fresh 30d data
for dt, v in lsr_live.items():
    if dt not in lsr_by_d:
        lsr_by_d[dt] = {}
    lsr_by_d[dt].update(v)

# Inject all fetched data into lookup dicts
perp_by_d["2026-08-07"] = perp_0807
spot_by_d["2026-08-07"] = spot_0807

# 08/08: only inject if klines actually returned data (day is closed)
if perp_0808.get("o") is not None:
    perp_by_d["2026-08-08"] = perp_0808
    spot_by_d["2026-08-08"] = spot_0808
    MAX_DATE = "2026-08-08"
    log(f"  08/08 CLOSED — will append to DAILY")
else:
    MAX_DATE = "2026-08-07"
    log(f"  08/08 NOT CLOSED (no klines yet) — excluded from DAILY per operator spec")

# ── 3. Build date range 2025-02-13 → MAX_DATE ────────────────────────────────
all_dates = sorted(d for d in perp_by_d.keys() if d <= MAX_DATE)
log(f"\n  Date range: {all_dates[0]} → {all_dates[-1]} ({len(all_dates)} dates)")

# ── 4. Compute all rolling arrays ─────────────────────────────────────────────
vol_vals  = [safe_float(perp_by_d.get(d, {}).get("vol_quote_usd")) for d in all_dates]
h_vals    = [safe_float(perp_by_d.get(d, {}).get("h"))             for d in all_dates]
l_vals    = [safe_float(perp_by_d.get(d, {}).get("l"))             for d in all_dates]
oi_vals   = [oi_by_d.get(d, {}).get("oi_usd")                      for d in all_dates]
pos_r_all = [safe_float(lsr_by_d.get(d, {}).get("pos_r_raw"))      for d in all_dates]
acc_r_all = [safe_float(lsr_by_d.get(d, {}).get("acc_r_raw"))      for d in all_dates]
glsr_all  = [safe_float(lsr_by_d.get(d, {}).get("glsr_raw"))       for d in all_dates]

def rolling_med14(vals):
    out = [None] * len(vals)
    for i in range(14, len(vals)):
        w = [v for v in vals[i-14:i] if v is not None]
        if len(w) >= 7:
            s = sorted(w); n = len(s)
            out[i] = (s[n//2-1] + s[n//2]) / 2 if n % 2 == 0 else s[n//2]
    return out

vol_med14 = rolling_med14(vol_vals)
oi_med14  = rolling_med14(oi_vals)

N = len(all_dates)

# (a) div_raw = pos_r / acc_r  [CANONICAL: Phu luc A.1]
div_raw_all = [
    round(pos_r_all[i] / acc_r_all[i], 4)
    if (pos_r_all[i] and acc_r_all[i] and acc_r_all[i] != 0) else None
    for i in range(N)
]

# (b) div_avg3 = avg3(pos_r) / avg3(acc_r)  [CANONICAL: Phu luc A.2 — KHONG phai mean(div_raw)]
div_avg3_all = [None] * N
for i in range(2, N):
    p3 = [v for v in pos_r_all[i-2:i+1] if v is not None]
    a3 = [v for v in acc_r_all[i-2:i+1] if v is not None]
    if len(p3) == 3 and len(a3) == 3:
        ap = sum(p3) / 3; aa = sum(a3) / 3
        div_avg3_all[i] = round(ap / aa, 4) if aa != 0 else None

# (c) glsr_slope_5d = gLSR(t) / gLSR(t-5)  [CANONICAL: Phu luc A.3 — ratio KHONG phai %chg]
slope_all = [None] * N
for i in range(5, N):
    g = glsr_all[i]; gp = glsr_all[i-5]
    if g is not None and gp is not None and gp > 0:
        slope_all[i] = round(g / gp, 4)

# (d) avg5_glsr = rolling 5-day average of gLSR  [GOM-A A2]
avg5_glsr = [None] * N
for i in range(4, N):
    w = [v for v in glsr_all[i-4:i+1] if v is not None]
    if len(w) >= 3:
        avg5_glsr[i] = round(sum(w) / len(w), 4)

# (e) avg5_pos_r = rolling 5-day avg of pos_r  [for pos_rerate check in A4]
avg5_pos_r = [None] * N
for i in range(4, N):
    w = [v for v in pos_r_all[i-4:i+1] if v is not None]
    if len(w) >= 3:
        avg5_pos_r[i] = round(sum(w) / len(w), 4)

# (f) pos_rerate_streak: consecutive days where pos_r > avg5_pos_r + 0.25  [GOM-A A4]
pos_rerate_streak = [0] * N
for i in range(N):
    p = pos_r_all[i]; a5 = avg5_pos_r[i]
    if p is not None and a5 is not None and p > a5 + 0.25:
        pos_rerate_streak[i] = (pos_rerate_streak[i-1] + 1) if i > 0 else 1
    else:
        pos_rerate_streak[i] = 0

# (g) oi_cycle_pos = (oi_usd - min_30d) / (max_30d - min_30d)  [GOM-A A5, rolling 30d]
oi_cycle_pos_all = [None] * N
for i in range(29, N):
    w = [v for v in oi_vals[i-29:i+1] if v is not None]
    cur = oi_vals[i]
    if len(w) >= 10 and cur is not None:
        mn = min(w); mx = max(w)
        if mx > mn:
            oi_cycle_pos_all[i] = round((cur - mn) / (mx - mn), 4)

# (h) div_avg3_low_streak: consecutive days div_avg3 <= 0.5  [GOM-B B1]
div_avg3_low_streak = [0] * N
for i in range(N):
    if div_avg3_all[i] is not None and div_avg3_all[i] <= 0.5:
        div_avg3_low_streak[i] = (div_avg3_low_streak[i-1] + 1) if i > 0 else 1
    else:
        div_avg3_low_streak[i] = 0

# (i) taker_absorb_streak: consecutive days taker in [44%, 50.5%]  [GOM-B B3]
taker_vals = [safe_float(perp_by_d.get(d, {}).get("taker_pct")) for d in all_dates]
taker_absorb_streak = [0] * N
for i in range(N):
    t = taker_vals[i]
    if t is not None and 44.0 <= t <= 50.5:
        taker_absorb_streak[i] = (taker_absorb_streak[i-1] + 1) if i > 0 else 1
    else:
        taker_absorb_streak[i] = 0

# (j) range_7d: (max_high_7d - min_low_7d) / min_low_7d * 100  [GOM-B B3]
range_7d = [None] * N
for i in range(6, N):
    h7 = [v for v in h_vals[i-6:i+1] if v is not None]
    l7 = [v for v in l_vals[i-6:i+1] if v is not None]
    if h7 and l7:
        mx = max(h7); mn = min(l7)
        if mn > 0:
            range_7d[i] = round((mx - mn) / mn * 100, 2)

log(f"  Rolling arrays built:")
log(f"    div_raw non-null:     {sum(1 for v in div_raw_all if v is not None)}")
log(f"    div_avg3 non-null:    {sum(1 for v in div_avg3_all if v is not None)}")
log(f"    slope non-null:       {sum(1 for v in slope_all if v is not None)}")
log(f"    avg5_glsr non-null:   {sum(1 for v in avg5_glsr if v is not None)}")
log(f"    oi_cycle_pos non-null:{sum(1 for v in oi_cycle_pos_all if v is not None)}")

# ── 5. Build DAILY rows ────────────────────────────────────────────────────────
DAILY_HEADERS = [
    "date", "px_avg", "o", "h", "l", "c", "vol_perp_usd", "taker_buy_pct",
    "f_avg", "f_min", "f_max", "fn", "oi_usd", "oi_token", "data_ok", "low_conf",
    "ret_1d", "pin_streak", "pin_day", "oi_vs_med14", "vol_vs_med14",
    "div_raw", "div_avg3", "glsr_slope_5d", "d_pos_3d", "d_acc_3d",
    "pos_r", "acc_r", "gLSR", "taker_lsr",
    "vol_spot_usd", "taker_spot_pct", "spot_perp_ratio", "l29_flag",
    "vol_alpha", "taker_alpha", "on_chain_source",
    "gom_A_screen", "gom_B_screen", "gom_note",
    "data_source_perp", "data_source_lsr",
    "oi_cycle_pos",  # col 43 — new
]
assert len(DAILY_HEADERS) == 43, f"Expected 43, got {len(DAILY_HEADERS)}"

daily_data = []
pin_streak = 0

for i, dt in enumerate(all_dates):
    pr = perp_by_d.get(dt, {})
    sr = spot_by_d.get(dt, {})
    ls = lsr_by_d.get(dt, {})
    fd = fund_by_day.get(dt, [])
    oi = oi_by_d.get(dt, {})

    o  = safe_float(pr.get("o"))
    h  = safe_float(pr.get("h"))
    l  = safe_float(pr.get("l"))
    c  = safe_float(pr.get("c"))
    px_avg = round((h + l + c) / 3, 8) if (h and l and c) else None
    vol_p  = safe_float(pr.get("vol_quote_usd"))
    taker  = safe_float(pr.get("taker_pct"))
    ret_1d = safe_float(pr.get("ret_1d"))

    # For 2025/2026 data ret_1d from CSV: compute from close-to-close if available
    if ret_1d is None and i > 0:
        c_prev = safe_float(perp_by_d.get(all_dates[i-1], {}).get("c"))
        if c and c_prev and c_prev > 0:
            ret_1d = round((c - c_prev) / c_prev * 100, 4)

    fn    = len(fd)
    f_avg = round(sum(fd) / fn, 8) if fn > 0 else None
    f_min = round(min(fd), 8)      if fn > 0 else None
    f_max = round(max(fd), 8)      if fn > 0 else None
    data_ok  = fn >= 6 if fn > 0 else None
    low_conf = fn < 6  if fn > 0 else True

    oi_usd   = oi.get("oi_usd")
    oi_token = oi.get("oi_token")

    pin_day = all(PIN_LO <= f <= PIN_HI for f in fd) and fn >= 6 if fn > 0 else None
    if pin_day is True:
        pin_streak += 1
    elif pin_day is False:
        pin_streak = 0
    else:
        pin_streak = 0

    oi_vs_m  = round(oi_usd  / oi_med14[i], 3) if (oi_usd  and oi_med14[i])  else None
    vol_vs_m = round(vol_p   / vol_med14[i], 2) if (vol_p   and vol_med14[i]) else None

    pos_r = pos_r_all[i]
    acc_r = acc_r_all[i]
    glsr  = glsr_all[i]
    tkls  = safe_float(ls.get("taker_lsr_raw"))

    d_pos = None; d_acc = None
    if i >= 3:
        pp = pos_r_all[i-3]; ap = acc_r_all[i-3]
        if pos_r and pp and pp > 0: d_pos = round((pos_r - pp) / pp * 100, 2)
        if acc_r and ap and ap > 0: d_acc = round((acc_r - ap) / ap * 100, 2)

    vol_s = safe_float(sr.get("vol_spot_usd"))
    tk_s  = safe_float(sr.get("taker_spot_pct"))
    spr   = safe_float(sr.get("spot_perp_ratio"))
    l29   = sr.get("l29_flag", "") or ""

    # ── GOM-A per gom_detect_spec v1.4 §1 (operator CASE adaptation 08/08/2026) ──
    # A1 = div_avg3 >= 1.5  [lsr_accum: nhien lieu tich luy]
    A1 = (div_avg3_all[i] is not None and div_avg3_all[i] >= 1.5)
    # A2 = avg5(gLSR) <= 1.1  [MUC nhien lieu toan thi — KHONG phai slope]
    A2 = (avg5_glsr[i] is not None and avg5_glsr[i] <= 1.1)
    # A3 = glsr_slope_5d <= 1.15  [CHIEU nhien lieu — nguong 1.15, KHONG phai 1.0]
    A3 = (slope_all[i] is not None and slope_all[i] <= 1.15)
    # A4 = d_pos_3d >= 0 OR pos_rerate(pos_r +0.25 vs avg5_pos_r, >=3d lien tuc)
    A4 = ((d_pos is not None and d_pos >= 0) or pos_rerate_streak[i] >= 3)
    # A5 = oi_cycle_pos <= 0.5  [OI trong vung tich luy — window 30d rolling]
    A5 = (oi_cycle_pos_all[i] is not None and oi_cycle_pos_all[i] <= 0.5)
    gom_a = A1 and A2 and A3 and (A4 or A5)

    # ── GOM-B per spec §1 ──────────────────────────────────────────────────────
    # B1 = div_avg3 <= 0.5 lien tuc >=7d  [hedge_structure >=7d]
    B1 = (div_avg3_low_streak[i] >= 7)
    # B2 = pin_streak >= 5  [funding_pinned]
    B2 = (pin_streak >= 5)
    # B3 = taker [44, 50.5]% >=7d lien tuc + range 7d <= 10%  [absorption]
    B3 = (taker_absorb_streak[i] >= 7 and range_7d[i] is not None and range_7d[i] <= 10.0)
    # B4 = NOT funding_neg_div  (f_avg<0 AND |ret_1d|<2% = "neg funding trong thi truong phang")
    funding_neg_div = (f_avg is not None and f_avg < 0 and
                       ret_1d is not None and abs(ret_1d) < 2.0)
    B4 = not funding_neg_div
    gom_b = B1 and (B2 or B3) and B4

    gom_note = ""
    if gom_a or gom_b:
        parts = []
        if gom_a:
            parts.append(
                f"A(A1={A1},A2-avg5gLSR={round(avg5_glsr[i],3) if avg5_glsr[i] else '?'},"
                f"A3-slope={round(slope_all[i],3) if slope_all[i] else '?'},"
                f"A4={A4},A5-oicp={round(oi_cycle_pos_all[i],3) if oi_cycle_pos_all[i] else '?'})"
            )
        if gom_b:
            parts.append(f"B(B1_streak={div_avg3_low_streak[i]},B2_pin={pin_streak},"
                         f"B3={B3},B4={B4})")
        gom_note = " | ".join(parts) + " — spec v1.4 ky 08/08"

    row = {
        "date": dt, "px_avg": px_avg,
        "o": o, "h": h, "l": l, "c": c,
        "vol_perp_usd": vol_p, "taker_buy_pct": taker,
        "f_avg": f_avg, "f_min": f_min, "f_max": f_max,
        "fn": fn if fn > 0 else None,
        "oi_usd": oi_usd, "oi_token": oi_token,
        "data_ok": data_ok, "low_conf": low_conf,
        "ret_1d": ret_1d,
        "pin_streak": pin_streak, "pin_day": pin_day,
        "oi_vs_med14": oi_vs_m, "vol_vs_med14": vol_vs_m,
        "div_raw": div_raw_all[i], "div_avg3": div_avg3_all[i],
        "glsr_slope_5d": slope_all[i],
        "d_pos_3d": d_pos, "d_acc_3d": d_acc,
        "pos_r": pos_r, "acc_r": acc_r, "gLSR": glsr, "taker_lsr": tkls,
        "vol_spot_usd": vol_s, "taker_spot_pct": tk_s,
        "spot_perp_ratio": spr, "l29_flag": l29,
        "vol_alpha": "ABSTAIN(no_alpha_id)", "taker_alpha": "BANNED(k9==k5)",
        "on_chain_source": "ABSTAIN(Nansen_LOCKED)",
        "gom_A_screen": "TRUE" if gom_a else "false",
        "gom_B_screen": "TRUE" if gom_b else "false",
        "gom_note": gom_note,
        "data_source_perp": "fapi_klines_1d",
        "data_source_lsr": "fapi_LSR_30d" if ls else "MISSING(>30d)",
        "oi_cycle_pos": oi_cycle_pos_all[i],
        # stash condition values for re-cham table (not written to sheet)
        "_A1": A1, "_A2": A2, "_A3": A3, "_A4": A4, "_A5": A5,
        "_avg5_glsr": avg5_glsr[i], "_slope": slope_all[i],
        "_div_avg3": div_avg3_all[i], "_d_pos3d": d_pos,
        "_pos_rerate": pos_rerate_streak[i],
        "_oicp": oi_cycle_pos_all[i],
        "_B1": B1, "_B2": B2, "_B3": B3, "_B4": B4,
        "_B1_streak": div_avg3_low_streak[i],
    }
    daily_data.append(row)

log(f"\n  DAILY rows built: {len(daily_data)}")
log(f"  GOM-A fires: {sum(1 for r in daily_data if r['gom_A_screen']=='TRUE')}")
log(f"  GOM-A dates: {[r['date'] for r in daily_data if r['gom_A_screen']=='TRUE']}")
log(f"  GOM-B fires: {sum(1 for r in daily_data if r['gom_B_screen']=='TRUE')}")
log(f"  GOM-B dates: {[r['date'] for r in daily_data if r['gom_B_screen']=='TRUE']}")

# ── 6. Re-cham table for 09/07 → 08/08 ──────────────────────────────────────
log(f"\n{'='*80}")
log(f"RE-CHAM GOM-A+B: 2026-07-09 → 2026-08-08 (hien rows co >=1 cua A1-A3 pass)")
log(f"{'='*80}")
log(f"{'Date':12} {'A1':5} {'A2':5} {'A3':5} {'A4':5} {'A5':5} "
    f"{'GOM-A':6} {'B1':5} {'B2':5} {'B3':5} {'B4':5} {'GOM-B':6} "
    f"{'div_a3':7} {'avg5g':6} {'slope':6} {'oicp':6} {'d_pos3':7}")
log("-" * 110)

window_rows = [r for r in daily_data if "2026-07-09" <= r["date"] <= "2026-08-08"]
for r in window_rows:
    A1v = r["_A1"]; A2v = r["_A2"]; A3v = r["_A3"]
    if not (A1v or A2v or A3v):
        continue  # skip rows where none of A1-A3 pass
    log(f"{r['date']:12} "
        f"{'✓' if A1v else '✗':5} {'✓' if A2v else '✗':5} {'✓' if A3v else '✗':5} "
        f"{'✓' if r['_A4'] else '✗':5} {'✓' if r['_A5'] else '✗':5} "
        f"{'TRUE' if r['gom_A_screen']=='TRUE' else 'false':6} "
        f"{'✓' if r['_B1'] else '✗':5} {'✓' if r['_B2'] else '✗':5} "
        f"{'✓' if r['_B3'] else '✗':5} {'✓' if r['_B4'] else '✗':5} "
        f"{'TRUE' if r['gom_B_screen']=='TRUE' else 'false':6} "
        f"{str(round(r['_div_avg3'],3) if r['_div_avg3'] else ''):7} "
        f"{str(round(r['_avg5_glsr'],3) if r['_avg5_glsr'] else ''):6} "
        f"{str(round(r['_slope'],3) if r['_slope'] else ''):6} "
        f"{str(round(r['_oicp'],3) if r['_oicp'] else ''):6} "
        f"{str(round(r['_d_pos3d'],1) if r['_d_pos3d'] is not None else ''):7}")

# ── 7. Print full rows 07/08 + 08/08 (27 key columns) ────────────────────────
PRINT_COLS = [
    "date","o","h","l","c","vol_perp_usd","taker_buy_pct","f_avg","fn",
    "oi_usd","oi_token","data_ok","low_conf","ret_1d","pin_streak","pin_day",
    "oi_vs_med14","div_raw","div_avg3","glsr_slope_5d","d_pos_3d",
    "pos_r","acc_r","gLSR","gom_A_screen","gom_B_screen","oi_cycle_pos"
]
assert len(PRINT_COLS) == 27

log(f"\n{'='*80}")
log("FULL ROWS 27 COLS — 07/08 + 08/08")
log(f"{'='*80}")
for target_date in ["2026-08-07", "2026-08-08"]:
    row = next((r for r in daily_data if r["date"] == target_date), None)
    if not row:
        log(f"  {target_date}: NOT FOUND"); continue
    log(f"\n  [{target_date}]")
    for col in PRINT_COLS:
        log(f"    {col:22} = {row.get(col)}")

# ── 8. Write to Excel ─────────────────────────────────────────────────────────
log(f"\n--- WRITING XLSX ---")

HDR_FILL  = PatternFill("solid", fgColor="1F4E79")
HDR_FONT  = Font(bold=True, color="FFFFFF", size=9)
GRP_FILLS = {
    "PERP":  PatternFill("solid", fgColor="BDD7EE"),
    "DERIV": PatternFill("solid", fgColor="E2EFDA"),
    "CROWD": PatternFill("solid", fgColor="FCE4D6"),
    "SPOT":  PatternFill("solid", fgColor="FFF2CC"),
    "ALPHA": PatternFill("solid", fgColor="F2F2F2"),
    "CHAIN": PatternFill("solid", fgColor="EAD1DC"),
    "GOM":   PatternFill("solid", fgColor="D9D9D9"),
    "SRC":   PatternFill("solid", fgColor="EDEDED"),
    "DERIV2":PatternFill("solid", fgColor="E2EFDA"),
}

COL_GROUPS = [
    ("PERP MACHINE (fapi klines 1d + funding)", 1, 16, "PERP"),
    ("DERIVED (cong thuc canonical — Phu luc A)", 17, 26, "DERIV"),
    ("CROWD — LSR (fapi, 30d window — L-38)", 27, 30, "CROWD"),
    ("SPOT (binance api/v3 k[10]/k[7])", 31, 34, "SPOT"),
    ("ALPHA (ABSTAIN — no alpha_id)", 35, 36, "ALPHA"),
    ("ON-CHAIN (ABSTAIN — Nansen LOCKED)", 37, 37, "CHAIN"),
    ("GOM SCREEN (gom_detect_spec v1.4 ky 08/08)", 38, 40, "GOM"),
    ("NGUON", 41, 42, "SRC"),
    ("DERIV-OI (oi_cycle_pos 30d rolling)", 43, 43, "DERIV2"),
]

HDR_LABELS = [
    "date", "px_avg (H+L+C)/3", "o", "h", "l", "c",
    "vol_perp_usd", "taker_buy_pct (k[10]/k[7])", "f_avg", "f_min", "f_max",
    "fn (4h=6/day)",
    "oi_usd", "oi_token", "data_ok (fn>=6)", "low_conf (fn<6)",
    "ret_1d (close-to-close)", "pin_streak", "pin_day ([4e-5,6e-5] all fn)",
    "oi_vs_med14", "vol_vs_med14",
    "div_raw (pos_r/acc_r)", "div_avg3 (avg3(pos_r)/avg3(acc_r))",
    "glsr_slope_5d (ratio t/t-5)", "d_pos_3d (%chg)", "d_acc_3d (%chg)",
    "pos_r", "acc_r", "gLSR", "taker_lsr (buy/sell)",
    "vol_spot_usd", "taker_spot_pct (k[10]/k[7])", "spot_perp_ratio", "l29_flag",
    "vol_alpha (ABSTAIN)", "taker_alpha (BANNED)",
    "on_chain_source",
    "gom_A_screen", "gom_B_screen", "gom_note (spec v1.4 ky 08/08)",
    "data_source_perp", "data_source_lsr",
    "oi_cycle_pos (rolling 30d OI window)",  # col 43
]
assert len(HDR_LABELS) == 43, f"Expected 43 HDR_LABELS, got {len(HDR_LABELS)}"

try:
    wb = openpyxl.load_workbook(XLSX)
except PermissionError as e:
    log(f"  PERMISSION ERROR: {e}"); raise

# Remove old DAILY and recreate
if "DAILY" in wb.sheetnames:
    idx = wb.sheetnames.index("DAILY")
    del wb["DAILY"]
    ws_daily = wb.create_sheet("DAILY", idx)
else:
    ws_daily = wb.create_sheet("DAILY", 1)

# Row 1: group headers
for label, cs, ce, grp in COL_GROUPS:
    ws_daily.merge_cells(start_row=1, start_column=cs, end_row=1, end_column=ce)
    c = ws_daily.cell(1, cs)
    c.value = label
    c.fill  = GRP_FILLS.get(grp, HDR_FILL)
    c.font  = Font(bold=True, size=8)
    c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

# Row 2: column labels
for ci, lbl in enumerate(HDR_LABELS, 1):
    c = ws_daily.cell(2, ci)
    c.value = lbl
    c.fill  = HDR_FILL
    c.font  = Font(bold=True, color="FFFFFF", size=9)
    c.alignment = Alignment(wrap_text=True, vertical="center")

ws_daily.row_dimensions[1].height = 28
ws_daily.row_dimensions[2].height = 36

# Data rows (write "" instead of None to force row existence in xlsx XML)
for ri_off, row in enumerate(daily_data):
    ri = ri_off + 3
    for ci, key in enumerate(DAILY_HEADERS, 1):
        val = row.get(key)
        c = ws_daily.cell(ri, ci)
        c.value = val if val is not None else ""
        c.font  = Font(size=8)
        c.alignment = Alignment(vertical="center")
    # Highlights
    if row.get("gom_A_screen") == "TRUE":
        ws_daily.cell(ri, 38).fill = PatternFill("solid", fgColor="FFA500")
    if row.get("gom_B_screen") == "TRUE":
        ws_daily.cell(ri, 39).fill = PatternFill("solid", fgColor="FF6B6B")
    if not row.get("data_ok"):
        ws_daily.cell(ri, 15).fill = PatternFill("solid", fgColor="FFFF00")

ws_daily.freeze_panes = "B3"
ws_daily.column_dimensions["A"].width = 12
for ci in range(2, 44):
    ws_daily.column_dimensions[get_column_letter(ci)].width = 12

try:
    wb.save(XLSX)
    log(f"  Saved DAILY ({len(daily_data)} rows, 43 cols): {XLSX}")
except PermissionError as e:
    log(f"  PERMISSION ERROR: {e}"); raise

# ── 9. L-32 verify ─────────────────────────────────────────────────────────────
wb2 = openpyxl.load_workbook(XLSX, data_only=True)
ws2 = wb2["DAILY"]
cnt = sum(1 for ri in range(3, ws2.max_row + 100)
          if ws2.cell(ri, 1).value not in (None, ""))
log(f"\n  L-32: expected {len(daily_data)}, count non-empty date={cnt}")
assert cnt == len(daily_data), f"ROW COUNT MISMATCH: expected {len(daily_data)}, got {cnt}"
log(f"  L-32: PASS  Sheets: {wb2.sheetnames}")

# ── 10. Append EVENTS entry: line 244 spec-drift ─────────────────────────────
log(f"\n--- EVENTS APPEND ---")
wb3 = openpyxl.load_workbook(XLSX)
if "EVENTS" not in wb3.sheetnames:
    log("  WARN: EVENTS sheet not found, skipping");
else:
    ws_ev = wb3["EVENTS"]
    ev_max = ws_ev.max_row
    # Find last non-empty row
    last_ev = ev_max
    while last_ev > 1 and all(ws_ev.cell(last_ev, c).value in (None, "")
                               for c in range(1, ws_ev.max_column + 2)):
        last_ev -= 1
    new_ev_row = last_ev + 1

    # Read header row to know column mapping
    ev_hdrs = {ws_ev.cell(1, c).value: c for c in range(1, ws_ev.max_column + 2)
               if ws_ev.cell(1, c).value}

    ev_entry = {
        "date": "2026-08-09",
        "type": "CODE_BUG",
        "description": (
            "line 244 spec-drift trong ban va dau (A2/A3 gan nham + nguong 1.0 thay 1.15): "
            "A2 duoc gan la slope<1.0 (nen la avg5(gLSR)<=1.1), "
            "A3 duoc gan la pos_r>1.5 (nen la glsr_slope_5d<=1.15), "
            "nguong A2 dung 1.0 thay 1.15 theo spec. "
            "Phat hien 08/08, va ngay 09/08 bang _task_patch_gom_spec_20260808.py."
        ),
        "impact": "GOM-A re-score toan bo window DAILY — het hieu luc GOM-A fire cu",
        "ref": "_task_rebuild_hei_daily_20260808.py line 234-247",
        "resolved": "2026-08-09",
    }
    # Write to detected columns or fall back to sequential
    if ev_hdrs:
        for hdr, col in ev_hdrs.items():
            val = ev_entry.get(hdr.lower().strip(), ev_entry.get(hdr, ""))
            c = ws_ev.cell(new_ev_row, col)
            c.value = val if val else ""
            c.font  = Font(size=9)
    else:
        # No headers found: write all values sequentially
        vals = list(ev_entry.values())
        for ci, v in enumerate(vals, 1):
            ws_ev.cell(new_ev_row, ci).value = v
            ws_ev.cell(new_ev_row, ci).font = Font(size=9)

    log(f"  EVENTS row {new_ev_row}: line 244 spec-drift appended")
    wb3.save(XLSX)
    log(f"  EVENTS saved.")

# ── 11. Intraday 09/08 snapshot (print only, do NOT write to DAILY) ───────────
log(f"\n--- INTRADAY 09/08 SNAPSHOT (print only) ---")
px_now = fetch_json("https://fapi.binance.com/fapi/v1/ticker/price?symbol=HEIUSDT")
oi_now = fetch_json("https://fapi.binance.com/fapi/v1/openInterest?symbol=HEIUSDT")
snap_ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
log(f"  timestamp: {snap_ts}")
log(f"  px (fapi ticker/price):  {px_now.get('price', 'ERROR')}")
log(f"  OI token (fapi openInterest): {oi_now.get('openInterest', 'ERROR')}")
log(f"  [NOT written to DAILY per L-21 / operator instruction]")

# ── 12. Lesson draft (print only) ─────────────────────────────────────────────
log(f"\n{'='*70}")
log("LESSON DRAFT (khong tu ghi vao LESSONS sheet — operator duyệt truoc):")
log(f"{'='*70}")
log("""
Ten de xuat: Fix theo spec phai trich NGUYEN VAN dieu kien + so dieu kien vao comment
Noi dung:
  Khi viet lai dieu kien GOM (hoac bat ky thuong cua spec), bat buoc:
  1. Trich dan nguyen van nguon (gom_detect_spec.md §1, dong so + version)
     vao comment dong cach co de tham chieu.
  2. Ghi ro so luong dieu kien (vi du: # A1-A5, GOM-A = 5 dieu kien)
     de reviewer dem lai duoc.
  3. KHONG dich lai nguong tu tri nho — copy so tu spec:
     - A2 nguong la 1.1 (avg5 gLSR), khong phai 1.0
     - A3 nguong la 1.15 (slope), khong phai 1.0
     Sai mot so = sai toan bo logic loc.
  4. Neu dieu kien thay doi so voi spec goc (CASE adaptation):
     ghi ro "CASE adaptation: ..." ngay sau comment spec.
Ap dung: moi lan viet/sua code GOM, signals, bat ky re-score logic.
""")

log(f"\n[PATCH DONE — COMMIT READY]")
log(f"  Rows in DAILY: {len(daily_data)}")
log(f"  GOM-A fires: {sum(1 for r in daily_data if r['gom_A_screen']=='TRUE')}")
log(f"    dates: {[r['date'] for r in daily_data if r['gom_A_screen']=='TRUE']}")
log(f"  GOM-B fires: {sum(1 for r in daily_data if r['gom_B_screen']=='TRUE')}")
log(f"  Commit msg: 'CASE_HEI: GOM-A per spec verbatim + rows 08-07/08-08'")
