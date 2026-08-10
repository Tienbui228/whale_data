"""
build_case.py  —  Reusable CASE xlsx builder (refactored từ _task_patch_gom_spec_20260808.py).
Usage: python build_case.py <SYMBOL_PERP> [YYYYMMDD]
  e.g. python build_case.py BANANAS31USDT 20260807

GOM-A/B conditions copy nguyên văn từ gom_detect_spec.md v1.4 §1
(operator CASE adaptation 08/08/2026, xác nhận bằng _task_patch_gom_spec_20260808.py).
div_raw / div_avg3 / glsr_slope_5d theo Phụ lục A docs/analysis_playbook.md.

Columns 1-43: template HEI-đã-vá (giống _task_patch_gom_spec_20260808.py)
Columns 44-50: B-2 diagnostic flags (case-specific — BANANAS31 dump analysis)
"""
import sys, io, json, csv, shutil
from pathlib import Path
from datetime import datetime, timezone
from collections import defaultdict
import urllib.request

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# ── Args ───────────────────────────────────────────────────────────────────────
if len(sys.argv) < 2:
    print("Usage: python build_case.py <SYMBOL_PERP> [YYYYMMDD]"); sys.exit(1)
SYMBOL_PERP = sys.argv[1].upper()          # e.g. BANANAS31USDT
DATE_TAG    = sys.argv[2] if len(sys.argv) > 2 else datetime.now(timezone.utc).strftime("%Y%m%d")
SYM_BASE    = SYMBOL_PERP.replace("USDT","")   # e.g. BANANAS31
SYM_LOWER   = SYM_BASE.lower()                 # e.g. bananas31

SCRATCH   = Path(r"D:\Data back test\whale_data\scratch")
CASE_DIR  = Path(r"D:\Data back test\whale_data\docs\case_files")
ALPHA_MAP = Path(r"D:\Data back test\whale_data\data\config\alpha_id_map.json")
XLSX      = CASE_DIR / f"CASE_{SYM_BASE}.xlsx"
PIN_LO, PIN_HI = 4e-5, 6e-5
CASE_QUESTION = sys.argv[3] if len(sys.argv) > 3 else "Cau hoi case: TBD — operator dien"

import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter
sys.path.insert(0, str(Path(__file__).resolve().parent / "scripts"))
from case_guard import validate_written_pack

def log(s=""): print(s)

def load_alpha_meta(sym_base, date_tag, scratch):
    """A-0a: Dynamic lookup — NO hardcoded values. Reads pre-fetched BAPI/perp JSONs."""
    meta = {
        "alpha_id": "NOT_IN_MAP",
        "fullyDelisted": None,
        "contract": "UNKNOWN — CAN OPERATOR",
        "total_supply": "UNKNOWN",
        "circ_supply": "UNKNOWN",
        "holders": "UNKNOWN",
        "alpha_listing_date": "UNKNOWN",
        "perp_onboard": "UNKNOWN",
        "alpha_status": "UNKNOWN",
    }
    # 1. alpha_id from map
    if ALPHA_MAP.exists():
        alpha_map = json.loads(ALPHA_MAP.read_text(encoding="utf-8"))
        meta["alpha_id"] = alpha_map.get(sym_base, "NOT_IN_MAP")
    # 2. BAPI token details from pre-fetched JSON
    bapi_path = scratch / f"{sym_base.lower()}_bapi_{date_tag}.json"
    if bapi_path.exists():
        bapi = json.loads(bapi_path.read_text(encoding="utf-8"))
        meta["fullyDelisted"] = bapi.get("fullyDelisted", None)
        meta["contract"] = bapi.get("contractAddress", "UNKNOWN — CAN OPERATOR")
        meta["total_supply"] = bapi.get("totalSupply", "UNKNOWN")
        meta["circ_supply"] = bapi.get("circulatingSupply", "UNKNOWN")
        meta["holders"] = bapi.get("holders", "UNKNOWN")
        ts = int(bapi.get("listingTime", 0) or 0)
        if ts:
            meta["alpha_listing_date"] = datetime.fromtimestamp(ts/1000, tz=timezone.utc).strftime("%Y-%m-%d")
        fd = bapi.get("fullyDelisted", False)
        meta["alpha_status"] = (f"fullyDelisted={fd}, offsell={bapi.get('offsell',False)}, "
                                 f"offline={bapi.get('offline',False)}")
    else:
        log(f"  WARN: {bapi_path.name} not found — CASE meta will be UNKNOWN")
    # 3. Perp onboard from pre-fetched exchangeInfo
    pinfo_path = scratch / f"{sym_base.lower()}_perp_info_{date_tag}.json"
    if pinfo_path.exists():
        pinfo = json.loads(pinfo_path.read_text(encoding="utf-8"))
        onboard_ms = pinfo.get("onboardDate", 0) or 0
        if onboard_ms:
            meta["perp_onboard"] = datetime.fromtimestamp(onboard_ms/1000, tz=timezone.utc).strftime("%Y-%m-%d")
    return meta

def safe_float(v, d=None):
    try:
        return float(v) if v not in (None, "", "None") else d
    except: return d
def fetch_json(url, timeout=20):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        return {"_error": str(e)}
def load_csv(path):
    p = Path(path)
    if not p.exists():
        log(f"  WARN CSV missing: {p}"); return []
    with open(p, encoding="utf-8") as f:
        return list(csv.DictReader(f))

NOW  = datetime.now(timezone.utc)
meta = load_alpha_meta(SYM_BASE, DATE_TAG, SCRATCH)  # A-0a: dynamic lookup
log("=" * 70)
log(f"BUILD CASE  {SYM_BASE}  |  {NOW.strftime('%Y-%m-%d %H:%M UTC')}")
log(f"  alpha_id={meta['alpha_id']}  contract={meta['contract'][:20]}...  "
    f"fullyDelisted={meta['fullyDelisted']}")
log("=" * 70)

# ── 0. Backup existing xlsx ────────────────────────────────────────────────────
if XLSX.exists():
    bkp = SCRATCH / f"CASE_{SYM_BASE}_BACKUP_{NOW.strftime('%Y%m%d_%H%M')}.xlsx"
    shutil.copy2(XLSX, bkp)
    log(f"  Backup: {bkp}")

# ── 1. Load CSVs ───────────────────────────────────────────────────────────────
perp_rows = load_csv(SCRATCH / f"{SYM_LOWER}_perp_{DATE_TAG}.csv")
spot_rows = load_csv(SCRATCH / f"{SYM_LOWER}_spot_{DATE_TAG}.csv")
lsr_rows  = load_csv(SCRATCH / f"{SYM_LOWER}_lsr_raw_{DATE_TAG}.csv")
fund_rows = load_csv(SCRATCH / f"{SYM_LOWER}_funding_{DATE_TAG}.csv")
oi_rows   = load_csv(SCRATCH / f"{SYM_LOWER}_oi_hist_{DATE_TAG}.csv")
log(f"  CSVs: perp={len(perp_rows)}, spot={len(spot_rows)}, "
    f"lsr={len(lsr_rows)}, fund={len(fund_rows)}, oi={len(oi_rows)}")

perp_by_d = {r["date"]: r for r in perp_rows}

# A-0a fix: normalize spot CSV columns (vol_quote_usd → vol_spot_usd, taker_pct → taker_spot_pct)
spot_by_d = {}
for r in spot_rows:
    dt = r.get("date","")
    if not dt: continue
    spot_by_d[dt] = {
        "vol_spot_usd":   safe_float(r.get("vol_spot_usd") or r.get("vol_quote_usd")),
        "taker_spot_pct": safe_float(r.get("taker_spot_pct") or r.get("taker_pct")),
        "spot_perp_ratio": safe_float(r.get("spot_perp_ratio")),
    }

# A-0a fix: normalize LSR CSV columns (handles both "pos_r" and "pos_r_raw" naming)
lsr_by_d = {}
for r in lsr_rows:
    dt = r.get("date","")
    if not dt: continue
    lsr_by_d[dt] = {
        "pos_r_raw":     safe_float(r.get("pos_r_raw") or r.get("pos_r")),
        "acc_r_raw":     safe_float(r.get("acc_r_raw") or r.get("acc_r")),
        "glsr_raw":      safe_float(r.get("glsr_raw") or r.get("gLSR") or r.get("glsr")),
        "taker_lsr_raw": safe_float(r.get("taker_lsr_raw") or r.get("taker_lsr")),
        "_src":          r.get("_src", "fapi_LSR_30d"),
    }

# ── 2. Extend LSR with freshwatch (earlier history) ───────────────────────────
# freshwatch has lsr_pos_r / lsr_acc_r / lsr_global_r — usable before LSR retention window
for fw_csv in sorted((SCRATCH).glob("freshwatch_daily_*.csv")):
    with open(fw_csv, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            sym = row.get("symbol","")
            if sym.upper() != SYMBOL_PERP: continue
            dt = row.get("date","")
            if not dt or dt in lsr_by_d: continue  # live LSR takes priority
            pos_r = safe_float(row.get("lsr_pos_r"))
            acc_r = safe_float(row.get("lsr_acc_r"))
            glsr  = safe_float(row.get("lsr_global_r"))
            tkls  = safe_float(row.get("taker_ratio"))
            if pos_r:
                lsr_by_d[dt] = {"pos_r_raw": pos_r, "acc_r_raw": acc_r,
                                 "glsr_raw": glsr, "taker_lsr_raw": tkls,
                                 "_src": "freshwatch"}
log(f"  LSR after freshwatch merge: {len(lsr_by_d)} dates")

# ── 3. Build funding + OI dicts ────────────────────────────────────────────────
fund_by_day = defaultdict(list)
for fr in fund_rows:
    dt = fr.get("date","")
    rate = safe_float(fr.get("fundingRate"))
    if dt and rate is not None:
        fund_by_day[dt].append(rate)

oi_by_d = {}
for o in oi_rows:
    dt = o.get("date","")
    if dt:
        oi_by_d[dt] = {"oi_usd": safe_float(o.get("oi_usd")),
                        "oi_token": safe_float(o.get("oi_token"))}

log(f"  Funding days: {len(fund_by_day)}, OI days: {len(oi_by_d)}")

# ── 4. Build date range ────────────────────────────────────────────────────────
MAX_DATE = sorted(perp_by_d.keys())[-1]
all_dates = sorted(perp_by_d.keys())
log(f"  Date range: {all_dates[0]} → {all_dates[-1]} ({len(all_dates)} dates)")

# ── 5. Rolling arrays ──────────────────────────────────────────────────────────
N = len(all_dates)
vol_vals  = [safe_float(perp_by_d.get(d,{}).get("vol_quote_usd")) for d in all_dates]
h_vals    = [safe_float(perp_by_d.get(d,{}).get("h"))             for d in all_dates]
l_vals    = [safe_float(perp_by_d.get(d,{}).get("l"))             for d in all_dates]
c_vals    = [safe_float(perp_by_d.get(d,{}).get("c"))             for d in all_dates]
oi_vals   = [oi_by_d.get(d,{}).get("oi_usd")                      for d in all_dates]
pos_r_all = [safe_float(lsr_by_d.get(d,{}).get("pos_r_raw"))      for d in all_dates]
acc_r_all = [safe_float(lsr_by_d.get(d,{}).get("acc_r_raw"))      for d in all_dates]
glsr_all  = [safe_float(lsr_by_d.get(d,{}).get("glsr_raw"))       for d in all_dates]
taker_all = [safe_float(perp_by_d.get(d,{}).get("taker_pct"))     for d in all_dates]
ret_all   = [safe_float(perp_by_d.get(d,{}).get("ret_1d"))        for d in all_dates]

def rolling_med14(vals):
    out = [None] * len(vals)
    for i in range(14, len(vals)):
        w = [v for v in vals[i-14:i] if v is not None]
        if len(w) >= 7:
            s = sorted(w); n = len(s)
            out[i] = (s[n//2-1]+s[n//2])/2 if n%2==0 else s[n//2]
    return out

vol_med14 = rolling_med14(vol_vals)
oi_med14  = rolling_med14(oi_vals)

# (a) div_raw = pos_r / acc_r  [Phụ lục A.1 docs/analysis_playbook.md]
div_raw_all = [
    round(pos_r_all[i]/acc_r_all[i], 4)
    if (pos_r_all[i] and acc_r_all[i] and acc_r_all[i] != 0) else None
    for i in range(N)
]

# (b) div_avg3 = avg3(pos_r) / avg3(acc_r)  [Phụ lục A.2 — BẪY: KHÔNG phải mean(div_raw)]
div_avg3_all = [None] * N
for i in range(2, N):
    p3 = [v for v in pos_r_all[i-2:i+1] if v is not None]
    a3 = [v for v in acc_r_all[i-2:i+1] if v is not None]
    if len(p3) == 3 and len(a3) == 3:
        ap = sum(p3)/3; aa = sum(a3)/3
        div_avg3_all[i] = round(ap/aa, 4) if aa != 0 else None

# (c) glsr_slope_5d = gLSR(t)/gLSR(t-5) ratio  [Phụ lục A.3 — ratio KHÔNG phải %chg]
slope_all = [None] * N
for i in range(5, N):
    g = glsr_all[i]; gp = glsr_all[i-5]
    if g is not None and gp is not None and gp > 0:
        slope_all[i] = round(g/gp, 4)

# (d) avg5_glsr [GOM-A A2]
avg5_glsr = [None] * N
for i in range(4, N):
    w = [v for v in glsr_all[i-4:i+1] if v is not None]
    if len(w) >= 3:
        avg5_glsr[i] = round(sum(w)/len(w), 4)

# (e) avg5_pos_r [GOM-A A4 pos_rerate]
avg5_pos_r = [None] * N
for i in range(4, N):
    w = [v for v in pos_r_all[i-4:i+1] if v is not None]
    if len(w) >= 3:
        avg5_pos_r[i] = round(sum(w)/len(w), 4)

# (f) pos_rerate_streak [GOM-A A4]
pos_rerate_streak = [0] * N
for i in range(N):
    p = pos_r_all[i]; a5 = avg5_pos_r[i]
    if p is not None and a5 is not None and p > a5 + 0.25:
        pos_rerate_streak[i] = (pos_rerate_streak[i-1]+1) if i > 0 else 1
    else:
        pos_rerate_streak[i] = 0

# (g) oi_cycle_pos = (oi - min30) / (max30 - min30) rolling 30d  [GOM-A A5]
oi_cycle_pos_all = [None] * N
for i in range(29, N):
    w = [v for v in oi_vals[i-29:i+1] if v is not None]
    cur = oi_vals[i]
    if len(w) >= 10 and cur is not None:
        mn = min(w); mx = max(w)
        if mx > mn:
            oi_cycle_pos_all[i] = round((cur-mn)/(mx-mn), 4)

# (h) div_avg3_low_streak [GOM-B B1]
div_avg3_low_streak = [0] * N
for i in range(N):
    if div_avg3_all[i] is not None and div_avg3_all[i] <= 0.5:
        div_avg3_low_streak[i] = (div_avg3_low_streak[i-1]+1) if i > 0 else 1
    else:
        div_avg3_low_streak[i] = 0

# (i) taker_absorb_streak [GOM-B B3]
taker_absorb_streak = [0] * N
for i in range(N):
    t = taker_all[i]
    if t is not None and 44.0 <= t <= 50.5:
        taker_absorb_streak[i] = (taker_absorb_streak[i-1]+1) if i > 0 else 1
    else:
        taker_absorb_streak[i] = 0

# (j) range_7d [GOM-B B3]
range_7d = [None] * N
for i in range(6, N):
    h7 = [v for v in h_vals[i-6:i+1] if v is not None]
    l7 = [v for v in l_vals[i-6:i+1] if v is not None]
    if h7 and l7:
        mx = max(h7); mn = min(l7)
        if mn > 0:
            range_7d[i] = round((mx-mn)/mn*100, 2)

# ── B-2 diagnostic arrays ─────────────────────────────────────────────────────
# (k) flag_neg_div: f_avg <= -2e-4 AND range3d(px) <= ±7%
range3d = [None] * N
for i in range(2, N):
    h3 = [v for v in h_vals[i-2:i+1] if v is not None]
    l3 = [v for v in l_vals[i-2:i+1] if v is not None]
    if h3 and l3:
        mx = max(h3); mn = min(l3)
        ref = (mx+mn)/2
        if ref > 0:
            range3d[i] = round((mx-mn)/ref*100, 2)

# (l) flag_dist_wall_day: taker >= 50 AND ret_1d < 0  [B-2 H3a]
dist_wall_day = [False] * N
for i in range(N):
    t = taker_all[i]; r = ret_all[i]
    if t is not None and r is not None and t >= 50.0 and r < 0:
        dist_wall_day[i] = True

# dist_wall_streak: consecutive flag_dist_wall_day
dist_wall_streak = [0] * N
for i in range(N):
    if dist_wall_day[i]:
        dist_wall_streak[i] = (dist_wall_streak[i-1]+1) if i > 0 else 1
    else:
        dist_wall_streak[i] = 0

# dist_wall_cumul_ret: cumulative ret_1d during streak
dist_wall_cumul = [None] * N
for i in range(N):
    if dist_wall_streak[i] > 0:
        start = i - dist_wall_streak[i] + 1
        window_rets = [ret_all[j] for j in range(start, i+1) if ret_all[j] is not None]
        if window_rets:
            cumul = 1.0
            for r in window_rets:
                cumul *= (1 + r/100)
            dist_wall_cumul[i] = round((cumul - 1) * 100, 2)

# (m) flag_decay_day: taker < 45  [B-2 H3b]
# (n) flag_hedge_struct: div_avg3 <= 0.5  [B-2 H4]
# (o) flag_knife_crowd: gLSR(t) > gLSR(t-1) AND ret_1d < -3  [B-2 H4]

log(f"  B-2 arrays computed")

# ── 6. Build DAILY rows ────────────────────────────────────────────────────────
DAILY_HEADERS = [
    # 1-43: HEI template
    "date","px_avg","o","h","l","c","vol_perp_usd","taker_buy_pct",
    "f_avg","f_min","f_max","fn","oi_usd","oi_token","data_ok","low_conf",
    "ret_1d","pin_streak","pin_day","oi_vs_med14","vol_vs_med14",
    "div_raw","div_avg3","glsr_slope_5d","d_pos_3d","d_acc_3d",
    "pos_r","acc_r","gLSR","taker_lsr",
    "vol_spot_usd","taker_spot_pct","spot_perp_ratio","l29_flag",
    "vol_alpha","taker_alpha","on_chain_source",
    "gom_A_screen","gom_B_screen","gom_note",
    "data_source_perp","data_source_lsr",
    "oi_cycle_pos",
    # 44-50: B-2 diagnostic
    "flag_neg_div","flag_dist_wall_day","dist_wall_streak","dist_wall_cumul_ret",
    "flag_decay_day","flag_hedge_struct","flag_knife_crowd",
]
assert len(DAILY_HEADERS) == 50, f"Expected 50, got {len(DAILY_HEADERS)}"

daily_data = []
pin_streak = 0
_prev_close = None  # for ret_1d close-to-close computation

for i, dt in enumerate(all_dates):
    pr = perp_by_d.get(dt, {})
    sr = spot_by_d.get(dt, {})
    ls = lsr_by_d.get(dt, {})
    fd = fund_by_day.get(dt, [])
    oi = oi_by_d.get(dt, {})

    # Accept both "open/high/low/close" (current CSV schema) and "o/h/l/c" (legacy)
    o  = safe_float(pr.get("open",  pr.get("o")))
    h  = safe_float(pr.get("high",  pr.get("h")))
    l  = safe_float(pr.get("low",   pr.get("l")))
    c  = safe_float(pr.get("close", pr.get("c")))
    px_avg = round((h+l+c)/3, 8) if (h and l and c) else None
    vol_p  = safe_float(pr.get("vol_quote_usd", pr.get("vol_perp_usd")))
    taker  = safe_float(pr.get("taker_pct", pr.get("taker_buy_pct")))
    ret_1d = safe_float(pr.get("ret_1d"))
    if ret_1d is None and c and _prev_close:
        ret_1d = round((c - _prev_close) / _prev_close, 8)
    _prev_close = c if c is not None else _prev_close

    fn    = len(fd)
    f_avg = round(sum(fd)/fn, 8)   if fn > 0 else None
    f_min = round(min(fd), 8)      if fn > 0 else None
    f_max = round(max(fd), 8)      if fn > 0 else None
    data_ok  = fn >= 6 if fn > 0 else None
    low_conf = fn < 6  if fn > 0 else True

    oi_usd   = oi.get("oi_usd")
    oi_token = oi.get("oi_token")

    pin_day = all(PIN_LO <= f <= PIN_HI for f in fd) and fn >= 6 if fn > 0 else None
    if pin_day is True:   pin_streak += 1
    elif pin_day is False: pin_streak = 0
    else:                  pin_streak = 0

    oi_vs_m  = round(oi_usd/oi_med14[i], 3)  if (oi_usd  and oi_med14[i])  else None
    vol_vs_m = round(vol_p/vol_med14[i], 2)   if (vol_p   and vol_med14[i]) else None

    pos_r = pos_r_all[i]
    acc_r = acc_r_all[i]
    glsr  = glsr_all[i]
    tkls  = safe_float(ls.get("taker_lsr_raw"))

    d_pos = None; d_acc = None
    if i >= 3:
        pp = pos_r_all[i-3]; ap = acc_r_all[i-3]
        if pos_r and pp and pp > 0: d_pos = round((pos_r-pp)/pp*100, 2)
        if acc_r and ap and ap > 0: d_acc = round((acc_r-ap)/ap*100, 2)

    vol_s = safe_float(sr.get("vol_spot_usd"))
    tk_s  = safe_float(sr.get("taker_spot_pct"))
    spr   = safe_float(sr.get("spot_perp_ratio"))
    if vol_s and vol_p and vol_p > 0:
        spr   = round(vol_s/vol_p, 3)
    l29   = ("L29_ABSTAIN" if spr and spr >= 3 else "CLEAR") if spr else ""

    # ── GOM-A per gom_detect_spec v1.4 §1 (operator CASE adaptation 08/08/2026) ──
    # Copy nguyên văn từ _task_patch_gom_spec_20260808.py (bản đã ký, commit d74016e)
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

    # ── GOM-B per spec §1 ──
    # B1 = div_avg3 <= 0.5 lien tuc >=7d  [hedge_structure >=7d]
    B1 = (div_avg3_low_streak[i] >= 7)
    # B2 = pin_streak >= 5  [funding_pinned]
    B2 = (pin_streak >= 5)
    # B3 = taker [44,50.5]% >=7d lien tuc + range 7d <= 10%  [absorption]
    B3 = (taker_absorb_streak[i] >= 7 and range_7d[i] is not None and range_7d[i] <= 10.0)
    # B4 = NOT funding_neg_div  (f_avg<0 AND |ret_1d|<2%)
    funding_neg_div = (f_avg is not None and f_avg < 0 and
                       ret_1d is not None and abs(ret_1d) < 2.0)
    B4 = not funding_neg_div
    gom_b = B1 and (B2 or B3) and B4

    gom_note = ""
    if gom_a or gom_b:
        parts = []
        if gom_a:
            parts.append(f"A(A1={A1},A2-avg5gLSR={round(avg5_glsr[i],3) if avg5_glsr[i] else '?'},"
                         f"A3-slope={round(slope_all[i],3) if slope_all[i] else '?'},"
                         f"A4={A4},A5-oicp={round(oi_cycle_pos_all[i],3) if oi_cycle_pos_all[i] else '?'})")
        if gom_b:
            parts.append(f"B(B1_streak={div_avg3_low_streak[i]},B2_pin={pin_streak},B3={B3},B4={B4})")
        gom_note = " | ".join(parts) + " — spec v1.4 ky 08/08"

    # ── B-2 diagnostic flags ──────────────────────────────────────────────────
    # flag_neg_div: f_avg <= -2e-4 AND range3d(px) <= ±7%  [H2: neg funding in flat market]
    flag_neg_div = (f_avg is not None and f_avg <= -2e-4 and
                    range3d[i] is not None and range3d[i] <= 7.0)

    # flag_dist_wall_day: taker >= 50 AND ret_1d < 0  [H3a: distribution wall]
    flag_dist_wall = dist_wall_day[i]

    # dist_wall_streak: consecutive flag_dist_wall_day
    dws = dist_wall_streak[i]
    dwc = dist_wall_cumul[i]

    # flag_decay_day: taker < 45  [H3b: seller/decay]
    flag_decay = (taker is not None and taker < 45.0)

    # flag_hedge_struct: div_avg3 <= 0.5  [H4: hedge structure day]
    flag_hedge = (div_avg3_all[i] is not None and div_avg3_all[i] <= 0.5)

    # flag_knife_crowd: gLSR(t) > gLSR(t-1) AND ret_1d < -3  [H4: crowd long into dump]
    glsr_prev = glsr_all[i-1] if i > 0 else None
    flag_knife = (glsr is not None and glsr_prev is not None and
                  glsr > glsr_prev and ret_1d is not None and ret_1d < -3.0)

    lsr_src = ls.get("_src","fapi_LSR_30d") if ls else "MISSING(>30d)"

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
        "vol_alpha": (f"alpha_klines_store(forward_2026-08-04,venue=binance_alpha)"
                      if not meta.get("fullyDelisted") else f"ABSTAIN(fullyDelisted={SYM_BASE})"),
        "taker_alpha": "ABSTAIN(bapi_klines9==klines5_L48)",
        "on_chain_source": "ABSTAIN(Nansen_LOCKED)",
        "gom_A_screen": "TRUE" if gom_a else "false",
        "gom_B_screen": "TRUE" if gom_b else "false",
        "gom_note": gom_note,
        "data_source_perp": "fapi_klines_1d",
        "data_source_lsr": lsr_src,
        "oi_cycle_pos": oi_cycle_pos_all[i],
        # B-2
        "flag_neg_div": "TRUE" if flag_neg_div else "false",
        "flag_dist_wall_day": "TRUE" if flag_dist_wall else "false",
        "dist_wall_streak": dws if dws > 0 else None,
        "dist_wall_cumul_ret": dwc,
        "flag_decay_day": "TRUE" if flag_decay else "false",
        "flag_hedge_struct": "TRUE" if flag_hedge else "false",
        "flag_knife_crowd": "TRUE" if flag_knife else "false",
        # stash for analysis
        "_A1": A1, "_A2": A2, "_A3": A3, "_A4": A4, "_A5": A5,
        "_avg5g": avg5_glsr[i], "_slope": slope_all[i],
        "_div_avg3": div_avg3_all[i], "_d_pos": d_pos,
        "_oicp": oi_cycle_pos_all[i],
        "_B1": B1, "_B2": B2, "_B3": B3, "_B4": B4,
    }
    daily_data.append(row)

log(f"  DAILY rows: {len(daily_data)}")
log(f"  GOM-A fires: {sum(1 for r in daily_data if r['gom_A_screen']=='TRUE')}")
log(f"  GOM-A dates: {[r['date'] for r in daily_data if r['gom_A_screen']=='TRUE']}")
log(f"  GOM-B fires: {sum(1 for r in daily_data if r['gom_B_screen']=='TRUE')}")
log(f"  B-2 flag_dist_wall: {sum(1 for r in daily_data if r['flag_dist_wall_day']=='TRUE')}")
log(f"  B-2 flag_knife_crowd: {sum(1 for r in daily_data if r['flag_knife_crowd']=='TRUE')}")

# ── 7. B-3 Dump anatomy ────────────────────────────────────────────────────────
log(f"\n{'='*70}")
log(f"B-3 DUMP ANATOMY — {SYM_BASE}")
log(f"{'='*70}")

# All days ret_1d <= -5%
dump_days = [(r, i) for i, r in enumerate(daily_data)
             if (r.get("ret_1d") or 0) <= -5.0 and r.get("ret_1d") is not None]
log(f"\n  Days ret_1d <= -5%: {len(dump_days)}")
log(f"  {'Date':12} {'ret%':7} {'vol_vs_m':9} {'taker':7} {'f_min':10} {'oi_usd':12} {'flag_knife':10}")
for r, idx in sorted(dump_days, key=lambda x: x[1])[-30:]:  # last 30 dump days
    log(f"  {r['date']:12} {str(r.get('ret_1d','')):7} {str(r.get('vol_vs_med14','')):9} "
        f"{str(r.get('taker_buy_pct','')):7} {str(r.get('f_min','')):10} "
        f"{str(r.get('oi_usd','')):12} {r.get('flag_knife_crowd',''):10}")

# Most recent peak + drawdown
max_close = max((float(r["c"]) for r in daily_data if r.get("c") and float(r["c"]) > 0), default=0)
max_close_date = next((r["date"] for r in daily_data if r.get("c") and abs(float(r["c"])-max_close)<1e-8), "?")
last_close = float(daily_data[-1]["c"]) if daily_data[-1].get("c") else None
if last_close and max_close:
    drawdown_pct = round((last_close - max_close)/max_close*100, 2)
    log(f"\n  ATH close: {max_close:.8f} on {max_close_date}")
    log(f"  Latest close: {last_close:.8f}")
    log(f"  Drawdown from ATH: {drawdown_pct}%")

# Dump streak (consecutive negative days)
recent_30 = daily_data[-30:]
neg_streak = 0
for r in reversed(recent_30):
    if r.get("ret_1d") is not None and float(r["ret_1d"] or 0) < 0:
        neg_streak += 1
    else:
        break
total_red_30 = sum(1 for r in recent_30 if r.get("ret_1d") is not None and float(r["ret_1d"] or 0) < 0)
log(f"  Recent dump streak (from end): {neg_streak} days")
log(f"  Total red days in last 30: {total_red_30}/30")

# Vol >= 8x med14
vol8x = [(r["date"], r.get("vol_vs_med14")) for r in daily_data
         if r.get("vol_vs_med14") and float(r["vol_vs_med14"] or 0) >= 8.0]
log(f"\n  vol >= 8x med14 (L-15 bait candidates): {len(vol8x)}")
for dt, v in vol8x:
    log(f"    {dt}: {v}x")

# ── 8. B-2 Build-check table ──────────────────────────────────────────────────
log(f"\n{'='*70}")
log(f"B-2 BUILD-CHECK TABLE — pos_r slope + sign correlation")
log(f"{'='*70}")

# pos_r slope 10d (simple linear regression)
window = 30
recent_data = daily_data[-window:]
pos_r_window = [(i, r.get("pos_r")) for i, r in enumerate(recent_data) if r.get("pos_r") is not None]
if len(pos_r_window) >= 5:
    n = len(pos_r_window)
    xs = [x[0] for x in pos_r_window]
    ys = [x[1] for x in pos_r_window]
    xm = sum(xs)/n; ym = sum(ys)/n
    ss_xy = sum((x-xm)*(y-ym) for x,y in zip(xs,ys))
    ss_xx = sum((x-xm)**2 for x in xs)
    slope_10d = round(ss_xy/ss_xx, 4) if ss_xx != 0 else 0
    direction = "↑ RISING" if slope_10d > 0 else "↓ FALLING"
    log(f"\n  pos_r OLS slope (last {window}d available points={n}): {slope_10d} {direction}")

# sign(Δpos_r) vs sign(ret_1d) — count same/opposite days
same = opp = 0
for i in range(1, len(daily_data)):
    p_prev = daily_data[i-1].get("pos_r")
    p_cur  = daily_data[i].get("pos_r")
    r_cur  = daily_data[i].get("ret_1d")
    if p_prev is not None and p_cur is not None and r_cur is not None:
        dp = p_cur - p_prev
        if dp * r_cur > 0:   same += 1
        elif dp * r_cur < 0: opp += 1
total = same + opp
log(f"  sign(Δpos_r) vs sign(ret_1d) (all window, {total} days with both):")
log(f"    SAME direction: {same} ({round(same/total*100,1) if total else 0}%)")
log(f"    OPPOSITE:       {opp} ({round(opp/total*100,1)  if total else 0}%)")
log(f"    → pos_r INVERSO to price: {'YES (pos_r tăng khi giá giảm — SHORT COVER / BTW)' if opp > same else 'NO'}")

# ── 9. Write XLSX ──────────────────────────────────────────────────────────────
log(f"\n--- WRITING XLSX: {XLSX} ---")

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
    "DIAG":  PatternFill("solid", fgColor="FFD700"),
}
COL_GROUPS = [
    ("PERP MACHINE (fapi klines 1d + funding)", 1, 16, "PERP"),
    ("DERIVED (Phu luc A canonical)", 17, 26, "DERIV"),
    ("CROWD — LSR (fapi 30d + freshwatch)", 27, 30, "CROWD"),
    ("SPOT (api/v3 k[10]/k[7])", 31, 34, "SPOT"),
    ("ALPHA (fullyDelisted — ABSTAIN)", 35, 36, "ALPHA"),
    ("ON-CHAIN (Nansen LOCKED)", 37, 37, "CHAIN"),
    ("GOM SCREEN (spec v1.4 ky 08/08)", 38, 40, "GOM"),
    ("NGUON", 41, 42, "SRC"),
    ("DERIV-OI (oi_cycle_pos 30d)", 43, 43, "DERIV2"),
    ("B-2 DIAGNOSTIC FLAGS (dump analysis)", 44, 50, "DIAG"),
]
HDR_LABELS = [
    "date","px_avg (H+L+C)/3","o","h","l","c",
    "vol_perp_usd","taker_buy_pct (k[10]/k[7])","f_avg","f_min","f_max","fn (4h=6/day)",
    "oi_usd","oi_token","data_ok (fn>=6)","low_conf (fn<6)",
    "ret_1d (close-to-close)","pin_streak","pin_day ([4e-5,6e-5])","oi_vs_med14","vol_vs_med14",
    "div_raw (pos_r/acc_r)","div_avg3 (avg3p/avg3a)","glsr_slope_5d (ratio t/t-5)",
    "d_pos_3d (%chg)","d_acc_3d (%chg)",
    "pos_r","acc_r","gLSR","taker_lsr",
    "vol_spot_usd","taker_spot_pct","spot_perp_ratio","l29_flag",
    "vol_alpha","taker_alpha","on_chain_source",
    "gom_A_screen","gom_B_screen","gom_note",
    "data_source_perp","data_source_lsr",
    "oi_cycle_pos (30d rolling)",
    "flag_neg_div (f<=-2e-4&range3d<=7%)","flag_dist_wall_day (taker>=50&ret<0)",
    "dist_wall_streak (consec days)","dist_wall_cumul_ret (%)",
    "flag_decay_day (taker<45)","flag_hedge_struct (div_avg3<=0.5)",
    "flag_knife_crowd (gLSR↑&ret<-3%)",
]
assert len(HDR_LABELS) == 50, f"Expected 50 HDR_LABELS, got {len(HDR_LABELS)}"

# Load or create workbook
if XLSX.exists():
    wb = openpyxl.load_workbook(XLSX)
else:
    wb = openpyxl.Workbook()
    # Create 7 sheets
    wb.remove(wb.active)
    for sheet in ["CASE","DAILY","EVENTS","TRIGGERS","OUTCOME","MM_PROFILE","UNLOCK"]:
        wb.create_sheet(sheet)

# Rebuild DAILY sheet
if "DAILY" in wb.sheetnames:
    idx = wb.sheetnames.index("DAILY")
    del wb["DAILY"]
    ws_d = wb.create_sheet("DAILY", idx)
else:
    ws_d = wb.create_sheet("DAILY", 1)

# Row 1: group headers
for label, cs, ce, grp in COL_GROUPS:
    ws_d.merge_cells(start_row=1, start_column=cs, end_row=1, end_column=ce)
    c = ws_d.cell(1, cs)
    c.value = label
    c.fill  = GRP_FILLS.get(grp, HDR_FILL)
    c.font  = Font(bold=True, size=8)
    c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

# Row 2: column labels
for ci, lbl in enumerate(HDR_LABELS, 1):
    c = ws_d.cell(2, ci)
    c.value = lbl
    c.fill  = HDR_FILL
    c.font  = Font(bold=True, color="FFFFFF", size=9)
    c.alignment = Alignment(wrap_text=True, vertical="center")

ws_d.row_dimensions[1].height = 28
ws_d.row_dimensions[2].height = 40

# Data rows
for ri_off, row in enumerate(daily_data):
    ri = ri_off + 3
    for ci, key in enumerate(DAILY_HEADERS, 1):
        val = row.get(key)
        c = ws_d.cell(ri, ci)
        c.value = val if val is not None else ""
        c.font  = Font(size=8)
        c.alignment = Alignment(vertical="center")
    # Highlights
    if row.get("gom_A_screen") == "TRUE":
        ws_d.cell(ri, 38).fill = PatternFill("solid", fgColor="FFA500")
    if row.get("gom_B_screen") == "TRUE":
        ws_d.cell(ri, 39).fill = PatternFill("solid", fgColor="FF6B6B")
    if row.get("flag_dist_wall_day") == "TRUE":
        ws_d.cell(ri, 45).fill = PatternFill("solid", fgColor="FF9999")
    if row.get("flag_knife_crowd") == "TRUE":
        ws_d.cell(ri, 50).fill = PatternFill("solid", fgColor="FF6600")
    if not row.get("data_ok"):
        ws_d.cell(ri, 15).fill = PatternFill("solid", fgColor="FFFF00")

ws_d.freeze_panes = "B3"
ws_d.column_dimensions["A"].width = 12
for ci in range(2, 51):
    ws_d.column_dimensions[get_column_letter(ci)].width = 11

# ── 10. CASE sheet ─────────────────────────────────────────────────────────────
ws_case = wb["CASE"]
ws_case.cell(1, 1).value = f"CASE_{SYM_BASE}"
ws_case.cell(1, 1).font = Font(bold=True, size=14)
# A-0a: ALL values from dynamic meta lookup — NO hardcoded token-specific values
has_spot = len(spot_rows) > 0
venue_str = "Binance perp + spot" if has_spot else "Binance perp (no spot pair)"
case_meta = [
    ("Symbol (perp)", SYMBOL_PERP),
    ("Symbol (base)", SYM_BASE),
    ("Status", "COLD_START — PENDING"),
    ("Ngay mo", NOW.strftime("%Y-%m-%d")),
    ("Alpha ID", meta["alpha_id"]),
    ("Alpha status", meta["alpha_status"]),
    ("Contract (BSC)", meta["contract"]),
    ("Total supply", str(meta["total_supply"])),
    ("Circ supply", str(meta["circ_supply"])),
    ("Holders", str(meta["holders"])),
    ("Alpha listing", meta["alpha_listing_date"]),
    ("Perp onboard", meta["perp_onboard"]),
    ("Venue", venue_str),
    ("Cau hoi mo", CASE_QUESTION),
    ("Verdict", ""),
    ("T0 (GOM-A open)", ""),
    ("B_ref OI", ""),
    ("Archetype", ""),
    ("CAN OPERATOR", "BscScan top holders | contract verify L-28 | Nansen (LOCKED) | depth snap #2"),
]
for ri, (k, v) in enumerate(case_meta, 3):
    ws_case.cell(ri, 1).value = k
    ws_case.cell(ri, 1).font = Font(bold=True, size=9)
    ws_case.cell(ri, 2).value = v
    ws_case.cell(ri, 2).font = Font(size=9)

ws_case.column_dimensions["A"].width = 22
ws_case.column_dimensions["B"].width = 70

# ── 11. EVENTS sheet — seed entries ───────────────────────────────────────────
ws_ev = wb["EVENTS"]
ev_headers = ["date","type","description","ref","resolved"]
for ci, h in enumerate(ev_headers, 1):
    c = ws_ev.cell(1, ci)
    c.value = h
    c.font  = Font(bold=True, size=9)

# A-0a: EVENTS seed uses dynamic meta — no hardcoded dates
events_seed = []
if meta.get("alpha_listing_date") and meta["alpha_listing_date"] != "UNKNOWN":
    events_seed.append((meta["alpha_listing_date"], "LISTING_ALPHA",
                         f"{SYM_BASE} listed on Binance Alpha ({meta.get('alpha_id','?')})", "", ""))
else:
    events_seed.append(("UNKNOWN", "LISTING_ALPHA",
                         f"{SYM_BASE} Alpha listing date unknown — CAN OPERATOR", "", ""))
if meta.get("perp_onboard") and meta["perp_onboard"] != "UNKNOWN":
    events_seed.append((meta["perp_onboard"], "LISTING_PERP",
                         f"{SYMBOL_PERP} perp listed on Binance fapi (onboardDate)", "", ""))
else:
    events_seed.append(("UNKNOWN", "LISTING_PERP",
                         f"{SYMBOL_PERP} perp onboard date unknown — CAN OPERATOR", "", ""))
for ri, ev in enumerate(events_seed, 2):
    for ci, v in enumerate(ev, 1):
        ws_ev.cell(ri, ci).value = v
        ws_ev.cell(ri, ci).font = Font(size=9)

# Add dump events (ret <= -10%)
ev_ri = len(events_seed) + 2
for r in daily_data:
    if r.get("ret_1d") is not None and float(r["ret_1d"]) <= -10.0:
        ev_row = [r["date"], "DUMP_GT10PCT",
                  f"ret_1d={r['ret_1d']}% vol_vs_m={r.get('vol_vs_med14','')} taker={r.get('taker_buy_pct','')}",
                  "fapi_klines_1d", ""]
        for ci, v in enumerate(ev_row, 1):
            ws_ev.cell(ev_ri, ci).value = v
            ws_ev.cell(ev_ri, ci).font = Font(size=8)
        ev_ri += 1
# vol >= 8x events
for r in daily_data:
    vm = r.get("vol_vs_med14")
    if vm is not None and float(vm) >= 8.0:
        ev_row = [r["date"], "VOL_8X_MED14",
                  f"vol_vs_med14={vm}x taker={r.get('taker_buy_pct','')} ret={r.get('ret_1d','')}%",
                  "fapi_klines_1d", ""]
        for ci, v in enumerate(ev_row, 1):
            ws_ev.cell(ev_ri, ci).value = v
            ws_ev.cell(ev_ri, ci).font = Font(size=8)
        ev_ri += 1

for ci in range(1, 6):
    ws_ev.column_dimensions[get_column_letter(ci)].width = 20 if ci in (3,) else 16

# ── 12. Save ───────────────────────────────────────────────────────────────────
try:
    wb.save(XLSX)
    log(f"  Saved: {XLSX}")
except PermissionError as e:
    log(f"  PERMISSION ERROR: {e}"); raise

# ── 13. L-32 verify ───────────────────────────────────────────────────────────
wb2 = openpyxl.load_workbook(XLSX, data_only=True)
ws2 = wb2["DAILY"]
cnt = sum(1 for ri in range(3, ws2.max_row+100) if ws2.cell(ri,1).value not in (None,""))
log(f"  L-32: expected {len(daily_data)}, count non-empty date={cnt}")
assert cnt == len(daily_data), f"ROW COUNT MISMATCH: {len(daily_data)} vs {cnt}"
log(f"  L-32: PASS  Sheets: {wb2.sheetnames}")

# ── A-0b: LSR + spot coverage guard ────────────────────────────────────────────
log(f"\n--- A-0b COVERAGE GUARD ---")
N_check = N
last30_start = max(0, N_check - 30)
last30_dates = all_dates[last30_start:]

lsr_null = sum(1 for i, d in enumerate(all_dates) if i >= last30_start and pos_r_all[i] is None)
lsr_null_pct = lsr_null / len(last30_dates) * 100 if last30_dates else 100
if lsr_null_pct > 50:
    log(f"!!!! LSR COVERAGE FAIL: pos_r null {lsr_null_pct:.1f}% in last 30d ({lsr_null}/{len(last30_dates)}) !!!!")
    log(f"!!!! ABORT: Check A-1 LSR persist — do not ship !!!!")
    raise ValueError(f"A-0b guard: LSR pos_r null {lsr_null_pct:.1f}% > 50% in last 30d")
else:
    log(f"  LSR guard: pos_r null {lsr_null_pct:.1f}% in last 30d ({lsr_null}/{len(last30_dates)}) — PASS")

spot_null = sum(1 for d in last30_dates if spot_by_d.get(d,{}).get("vol_spot_usd") is None)
spot_null_pct = spot_null / len(last30_dates) * 100 if last30_dates else 100
if spot_null_pct > 50:
    log(f"  SPOT WARNING: vol_spot_usd null {spot_null_pct:.1f}% in last 30d ({spot_null}/{len(last30_dates)})")
    log(f"  → Reason required in report: no spot pair or collect not run")
else:
    log(f"  Spot guard: vol_spot_usd null {spot_null_pct:.1f}% in last 30d — PASS")

# ── Guard V2: validate_written_pack — ONE DOOR ─────────────────────────────────
validate_written_pack(XLSX)
log(f"  Guard V2: validate_written_pack PASS")

log(f"\n[BUILD_CASE DONE — {SYM_BASE}]")
log(f"  DAILY: {len(daily_data)} rows, 50 cols")
log(f"  GOM-A: {sum(1 for r in daily_data if r['gom_A_screen']=='TRUE')} fires")
log(f"  GOM-B: {sum(1 for r in daily_data if r['gom_B_screen']=='TRUE')} fires")
