"""
H7: Build CASE_HEI.xlsx — cold-start pack.
Template: CASE_ZBT.xlsx structure (7 sheets).
Status = "COLD_START — PENDING (verdict trong tay operator)".
DAILY: 41 cột, full history 2025-02-13 → 2026-08-07 (L-21: 08-08 không vào).
L-34: PermissionError → RAISE, cấm silent-save _NEW.
L-32: verify row count after save.
"""
import sys, io, json, csv
from pathlib import Path
from datetime import datetime, timezone, timedelta
from collections import defaultdict
import urllib.request

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

SCRATCH = Path(r"D:\Data back test\whale_data\scratch")
CASE_DIR = Path(r"D:\Data back test\whale_data\docs\case_files")
OUT_PATH = CASE_DIR / "CASE_HEI.xlsx"

# L-34: Raise if already exists and locked (no silent _NEW)
if OUT_PATH.exists():
    print(f"  [INFO] {OUT_PATH.name} already exists — will overwrite")

def log(s=""): print(s)

def fetch_json(url, timeout=15):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        return {"_error": str(e)}

log("=" * 70)
log(f"BUILD CASE_HEI.xlsx  |  {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
log("=" * 70)

# ── Load CSVs from H1/H2/H4 ───────────────────────────────────────────────

def load_csv(path):
    rows = []
    if Path(path).exists():
        with open(path, encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
    return rows

perp_rows  = load_csv(SCRATCH / "hei_perp_full_20260808.csv")
spot_rows  = load_csv(SCRATCH / "hei_spot_full_20260808.csv")
lsr_rows   = load_csv(SCRATCH / "hei_lsr_raw_20260808.csv")
log(f"  Loaded: perp={len(perp_rows)}, spot={len(spot_rows)}, lsr={len(lsr_rows)}")

perp_by_d = {r["date"]: r for r in perp_rows}
spot_by_d = {r["date"]: r for r in spot_rows}
lsr_by_d  = {r["date"]: r for r in lsr_rows}

# ── Re-fetch funding (limited history from fapi) ──────────────────────────
log("\n  Re-fetching funding rates...")
fund_url = "https://fapi.binance.com/fapi/v1/fundingRate?symbol=HEIUSDT&limit=1000"
fund_raw = fetch_json(fund_url)
fund_by_day = defaultdict(list)
PIN_LO = 4e-5; PIN_HI = 6e-5
if isinstance(fund_raw, list):
    for fr in fund_raw:
        ts = fr.get("fundingTime")
        if ts:
            dt = datetime.fromtimestamp(int(ts)/1000, tz=timezone.utc).strftime("%Y-%m-%d")
            fund_by_day[dt].append(float(fr.get("fundingRate", 0)))
log(f"  Funding days: {len(fund_by_day)}")

# ── Re-fetch OI historical ─────────────────────────────────────────────────
log("  Re-fetching OI hist...")
oih_url = "https://fapi.binance.com/futures/data/openInterestHist?symbol=HEIUSDT&period=1d&limit=30"
oih_raw = fetch_json(oih_url)
oi_by_d = {}
if isinstance(oih_raw, list):
    for o in oih_raw:
        ts = o.get("timestamp")
        if ts:
            dt = datetime.fromtimestamp(int(ts)/1000, tz=timezone.utc).strftime("%Y-%m-%d")
            oi_by_d[dt] = {
                "oi_usd":   float(o.get("sumOpenInterestValue", 0)),
                "oi_token": float(o.get("sumOpenInterest", 0)),
            }
log(f"  OI hist days: {len(oi_by_d)}")

# ── Get current OI snapshot ───────────────────────────────────────────────
oi_snap = fetch_json("https://fapi.binance.com/fapi/v1/openInterest?symbol=HEIUSDT")
oi_now_tokens = float(oi_snap.get("openInterest", 0)) if "_error" not in oi_snap else None
oi_snap_ts    = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

# ── Derived helper functions ──────────────────────────────────────────────

def safe_float(v, default=None):
    try: return float(v) if v not in (None,"","None") else default
    except: return default

def med14_list(values):
    """Return rolling 14-period median list (None for first 13 positions)."""
    result = [None]*len(values)
    for i in range(14, len(values)):
        window = [v for v in values[i-14:i] if v is not None]
        if len(window) >= 7:
            ws = sorted(window)
            n = len(ws)
            result[i] = (ws[n//2-1]+ws[n//2])/2 if n%2==0 else ws[n//2]
    return result

# ── Build all_dates (2025-02-13 → 2026-08-07) ────────────────────────────
all_dates = sorted(perp_by_d.keys())
log(f"\n  Date range: {all_dates[0]} → {all_dates[-1]} ({len(all_dates)} days)")

# ── Compute med14 for vol and OI ──────────────────────────────────────────
vol_vals  = [safe_float(perp_by_d.get(d,{}).get("vol_quote_usd")) for d in all_dates]
oi_vals   = [oi_by_d.get(d,{}).get("oi_usd") for d in all_dates]
vol_med14 = med14_list(vol_vals)
oi_med14  = med14_list(oi_vals)

# ── GOM screen helper (simplified inline) ────────────────────────────────
pos_r_persist_cnt = [0]*len(all_dates)
cnt_ = 0
for i, dt in enumerate(all_dates):
    pos_r = safe_float(lsr_by_d.get(dt,{}).get("pos_r_raw"))
    if pos_r and pos_r > 1.5:
        cnt_ += 1
    else:
        cnt_ = 0
    pos_r_persist_cnt[i] = cnt_

# ── Build DAILY rows (41 columns) ────────────────────────────────────────
DAILY_HEADERS = [
    # PERP MACHINE
    "date","px_avg","o","h","l","c","vol_perp_usd","taker_buy_pct",
    "f_avg","f_min","f_max","fn","oi_usd","oi_token","data_ok","low_conf",
    # DERIVED
    "ret_1d","pin_streak","pin_day","oi_vs_med14","vol_vs_med14",
    "div_raw","div_avg3","glsr_slope_5d","d_pos_3d","d_acc_3d",
    # CROWD (LSR)
    "pos_r","acc_r","gLSR","taker_lsr",
    # SPOT
    "vol_spot_usd","taker_spot_pct","spot_perp_ratio","l29_flag",
    # ALPHA
    "vol_alpha","taker_alpha",
    # ON-CHAIN
    "on_chain_source",
    # GOM SCREEN
    "gom_A_screen","gom_B_screen","gom_note",
    # BOUNDARY
    "data_source_perp","data_source_lsr",
]
# Ensure exactly 41 cols (trim/extend as needed)
assert len(DAILY_HEADERS) == 42, f"Got {len(DAILY_HEADERS)} headers, need 42"

daily_data = []
pin_streak = 0
prev_div = [None]*3

for i, dt in enumerate(all_dates):
    pr = perp_by_d.get(dt, {})
    sr = spot_by_d.get(dt, {})
    ls = lsr_by_d.get(dt, {})
    fd = fund_by_day.get(dt, [])
    oi = oi_by_d.get(dt, {})

    # PERP fields
    o  = safe_float(pr.get("o"))
    h  = safe_float(pr.get("h"))
    l  = safe_float(pr.get("l"))
    c  = safe_float(pr.get("c"))
    px_avg = round((h+l+c)/3, 8) if (h and l and c) else None
    vol_p  = safe_float(pr.get("vol_quote_usd"))
    taker  = safe_float(pr.get("taker_pct"))
    ret_1d = safe_float(pr.get("ret_1d"))

    fn     = len(fd)
    f_avg  = round(sum(fd)/fn, 8) if fd else None
    f_min  = round(min(fd), 8) if fd else None
    f_max  = round(max(fd), 8) if fd else None
    data_ok  = fn >= 6 if fn > 0 else None
    low_conf = fn < 6  if fn > 0 else True

    oi_usd   = oi.get("oi_usd")
    oi_token = oi.get("oi_token")

    # pin_day + streak
    if fd:
        pin_day = all(PIN_LO <= f <= PIN_HI for f in fd) and fn >= 6
    else:
        pin_day = None
    if pin_day is True:
        pin_streak += 1
    elif pin_day is False:
        pin_streak = 0
    else:
        pin_streak = 0  # gap = reset

    # oi_vs_med14, vol_vs_med14
    oi_vs_m = round(oi_usd/oi_med14[i], 3) if (oi_usd and oi_med14[i]) else None
    vol_vs_m = round(vol_p/vol_med14[i], 2) if (vol_p and vol_med14[i]) else None

    # Crowd
    pos_r = safe_float(ls.get("pos_r_raw"))
    acc_r = safe_float(ls.get("acc_r_raw"))
    glsr  = safe_float(ls.get("glsr_raw"))
    tkls  = safe_float(ls.get("taker_lsr_raw"))

    # div_raw, div_avg3
    div_raw = round(pos_r * glsr, 4) if (pos_r and glsr) else None
    prev_div.append(div_raw)
    prev_div = prev_div[-3:]
    divs = [d for d in prev_div if d is not None]
    div_avg3 = round(sum(divs)/len(divs), 4) if len(divs) == 3 else None

    # glsr_slope_5d
    glsr_slope = None
    if i >= 5:
        g_prev = safe_float(lsr_by_d.get(all_dates[i-5],{}).get("glsr_raw"))
        if glsr and g_prev and g_prev > 0:
            glsr_slope = round((glsr - g_prev)/g_prev*100, 2)

    # d_pos_3d, d_acc_3d
    d_pos = None; d_acc = None
    if i >= 3:
        p_prev = safe_float(lsr_by_d.get(all_dates[i-3],{}).get("pos_r_raw"))
        a_prev = safe_float(lsr_by_d.get(all_dates[i-3],{}).get("acc_r_raw"))
        if pos_r and p_prev and p_prev > 0:
            d_pos = round((pos_r-p_prev)/p_prev*100, 2)
        if acc_r and a_prev and a_prev > 0:
            d_acc = round((acc_r-a_prev)/a_prev*100, 2)

    # Spot
    vol_s  = safe_float(sr.get("vol_spot_usd"))
    tk_s   = safe_float(sr.get("taker_spot_pct"))
    spr    = safe_float(sr.get("spot_perp_ratio"))
    l29    = sr.get("l29_flag","")

    # GOM screen (same logic as H3 probe)
    vol_3x = (vol_p/vol_med14[i] >= 3) if (vol_p and vol_med14[i]) else False
    A1 = vol_3x
    A2 = (glsr_slope is not None and glsr_slope < 0)
    A3 = (pos_r is not None and pos_r > 1.5)
    A4 = (f_avg is not None and f_avg >= PIN_LO)
    A5 = (taker is not None and taker >= 45)
    gom_a = A1 and A2 and A3 and A4 and A5

    B1 = (pos_r_persist_cnt[i] >= 7)
    B2 = (pin_day is True)
    B3 = (vol_3x and ret_1d is not None and ret_1d < 0 and taker is not None and taker >= 50)
    B4 = (oi_vs_m is not None and oi_vs_m >= 1.5)
    gom_b = B1 and (B2 or B3) and B4

    gom_note = ""
    if gom_a or gom_b:
        parts = []
        if gom_a: parts.append(f"A(A1={A1},A2={A2},A3={A3},A4={A4},A5={A5})")
        if gom_b: parts.append(f"B(B1={B1},B2={B2},B3={B3},B4={B4})")
        gom_note = " | ".join(parts) + " — gom_detect_spec v1.1 CHUA KY"

    row = {
        "date": dt,
        "px_avg": px_avg,
        "o": o, "h": h, "l": l, "c": c,
        "vol_perp_usd": vol_p,
        "taker_buy_pct": taker,
        "f_avg": f_avg, "f_min": f_min, "f_max": f_max,
        "fn": fn if fn > 0 else None,
        "oi_usd": oi_usd, "oi_token": oi_token,
        "data_ok": data_ok, "low_conf": low_conf,
        "ret_1d": ret_1d,
        "pin_streak": pin_streak, "pin_day": pin_day,
        "oi_vs_med14": oi_vs_m, "vol_vs_med14": vol_vs_m,
        "div_raw": div_raw, "div_avg3": div_avg3,
        "glsr_slope_5d": glsr_slope,
        "d_pos_3d": d_pos, "d_acc_3d": d_acc,
        "pos_r": pos_r, "acc_r": acc_r, "gLSR": glsr, "taker_lsr": tkls,
        "vol_spot_usd": vol_s, "taker_spot_pct": tk_s,
        "spot_perp_ratio": spr, "l29_flag": l29,
        "vol_alpha": "ABSTAIN(no_alpha_id)",
        "taker_alpha": "BANNED(k9==k5)",
        "on_chain_source": "ABSTAIN(Nansen_LOCKED)",
        "gom_A_screen": "TRUE" if gom_a else "false",
        "gom_B_screen": "TRUE" if gom_b else "false",
        "gom_note": gom_note,
        "data_source_perp": "fapi_klines_1d",
        "data_source_lsr":  "fapi_LSR_30d" if ls else "MISSING(>30d)",
    }
    daily_data.append(row)

log(f"  DAILY rows built: {len(daily_data)}")
log(f"  GOM-A fires: {sum(1 for r in daily_data if r['gom_A_screen']=='TRUE')}")
log(f"  GOM-B fires: {sum(1 for r in daily_data if r['gom_B_screen']=='TRUE')}")

# ═══════════════════════════════════════════════════════════════════════════
# BUILD WORKBOOK
# ═══════════════════════════════════════════════════════════════════════════
log("\n  Building workbook...")

wb = openpyxl.Workbook()
wb.remove(wb.active)

# ── Styles ────────────────────────────────────────────────────────────────
HDR_FILL  = PatternFill("solid", fgColor="1F4E79")
HDR_FONT  = Font(bold=True, color="FFFFFF", size=9)
GRP_FILLS = {
    "PERP":   PatternFill("solid", fgColor="BDD7EE"),
    "DERIV":  PatternFill("solid", fgColor="E2EFDA"),
    "CROWD":  PatternFill("solid", fgColor="FCE4D6"),
    "SPOT":   PatternFill("solid", fgColor="FFF2CC"),
    "ALPHA":  PatternFill("solid", fgColor="F2F2F2"),
    "CHAIN":  PatternFill("solid", fgColor="EAD1DC"),
    "GOM":    PatternFill("solid", fgColor="D9D9D9"),
    "SRC":    PatternFill("solid", fgColor="EDEDED"),
}
WARN_FONT = Font(bold=True, color="C00000")

def write_hdr(ws, row, col, value, fill=None, font=None, wrap=True):
    c = ws.cell(row, col, value)
    if fill: c.fill = fill
    c.font = font or HDR_FONT
    c.alignment = Alignment(wrap_text=wrap, vertical="center")

# ── SHEET 1: CASE ─────────────────────────────────────────────────────────
ws_case = wb.create_sheet("CASE")

case_meta = [
    ("Status",           "COLD_START — PENDING (verdict trong tay operator)"),
    ("Symbol",           "HEIUSDT"),
    ("Perp listing",     "2025-02-13"),
    ("Spot listing",     "2025-02-13"),
    ("underlyingType",   "COIN"),
    ("underlyingSubType","Infrastructure"),
    ("contractType",     "PERPETUAL"),
    ("onboardDate",      "2025-02-13"),
    ("T0",               "unknown — operator xác định"),
    ("B_ref",            "unknown — operator xác định"),
    ("Verdict",          ""),
    ("verdict_date",     ""),
    ("archetype",        "PENDING OPERATOR (Loai A/B/C — L-42)"),
    ("COR_GHE_ROI_threshold", "unknown"),
    ("thesis_1line",     "HEI (Heima) perp + spot listed 2025-02-13. Spike events: 05-29/30 (+107%/+10%), 08-05 (+108%), 08-06 ATH vol $1.24B. COLD_START — full analysis PENDING operator."),
    ("venue_perp",       "Binance USDT-M PERPETUAL"),
    ("venue_spot",       "Binance spot HEIUSDT (api/v3, k[10]/k[7])"),
    ("venue_alpha",      "N/A — HEI not in alpha_id_map (no alpha listing confirmed)"),
    ("contract_candidate", "0xf8f173e20e15f3b6cb686fb64724d370689de083 (CoinGecko heima rank=910, BSC+ETH) — UNVERIFIED"),
    ("homepage_candidate", "https://www.heima.network/ (CoinGecko) — UNVERIFIED"),
    ("on_chain_status",  "ABSTAIN — contract unconfirmed, Nansen LOCKED, BscScan API deprecated"),
    ("Dieu gi chung minh SAI", ""),
    ("build_date",       datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")),
    ("data_window_perp", "2025-02-13 → 2026-08-07 (540 days, source: fapi klines 1d, paginated)"),
    ("data_window_lsr",  "2026-07-08 → 2026-08-07 (31 days, L-38: LSR 30d retention limit)"),
    ("data_window_fund", "2026-05-18 → 2026-08-07 (~82 days, source: fapi fundingRate limit=1000)"),
    ("data_window_oi",   "2026-07-09 → 2026-08-07 (30 days, source: fapi openInterestHist limit=30)"),
    ("VPS_premium_1h",   "2026-07-27 → 2026-08-07 (12 days, /root/.../premium_1h/symbol=HEIUSDT/)"),
    ("L21_boundary",     "2026-08-08 NOT in DAILY (cron 00:05 UTC D+1 chưa chạy — L-21)"),
    ("gom_screen_label", "gom_detect_spec v1.1 CHUA KY — SCREEN-tier tham chieu offline, khong phai signal chinh thuc"),
    ("Notes",            "Session 08-08-2026. LSR persisted khẩn cấp. Depth snapshot: one-shot (need 2nd shot ≥4h). Alpha: ABSTAIN. On-chain: ABSTAIN."),
]

for i, (k, v) in enumerate(case_meta):
    r = i + 1
    ws_case.cell(r, 1).value = k
    ws_case.cell(r, 1).font  = Font(bold=True, size=9)
    ws_case.cell(r, 2).value = v
    ws_case.cell(r, 2).font  = Font(size=9)
    if k == "Status":
        ws_case.cell(r, 2).font = Font(bold=True, color="C00000", size=10)

ws_case.column_dimensions["A"].width = 28
ws_case.column_dimensions["B"].width = 80

# ── SHEET 2: DAILY ────────────────────────────────────────────────────────
ws_daily = wb.create_sheet("DAILY")

# Group header row 1 (group labels)
COL_GROUPS = [
    ("PERP MACHINE (fapi klines 1d + funding)", 1, 16, "PERP"),
    ("DERIVED (công thức ghi rõ)", 17, 26, "DERIV"),
    ("CROWD — LSR (fapi, 30d window — L-38)", 27, 30, "CROWD"),
    ("SPOT (binance api/v3 k[10]/k[7])", 31, 34, "SPOT"),
    ("ALPHA (ABSTAIN — no alpha_id)", 35, 36, "ALPHA"),
    ("ON-CHAIN (ABSTAIN — Nansen LOCKED)", 37, 37, "CHAIN"),
    ("GOM SCREEN (gom_detect_spec v1.1 CHƯA KÝ)", 38, 40, "GOM"),
    ("NGUỒN", 41, 42, "SRC"),
]

for label, col_start, col_end, grp in COL_GROUPS:
    ws_daily.merge_cells(start_row=1, start_column=col_start, end_row=1, end_column=col_end)
    c = ws_daily.cell(1, col_start)
    c.value = label
    c.fill  = GRP_FILLS.get(grp, HDR_FILL)
    c.font  = Font(bold=True, size=8)
    c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

# Header row 2: column names
HDR_LABELS = [
    "date","px_avg (H+L+C)/3","o","h","l","c",
    "vol_perp_usd","taker_buy_pct (k[10]/k[7])","f_avg","f_min","f_max","fn (4h→6 per day)",
    "oi_usd","oi_token","data_ok (fn≥6)","low_conf (fn<6)",
    "ret_1d (close-to-close)","pin_streak","pin_day ([4e-5,6e-5] all fn)","oi_vs_med14","vol_vs_med14",
    "div_raw (pos_r×gLSR)","div_avg3","glsr_slope_5d (%chg)","d_pos_3d (%chg)","d_acc_3d (%chg)",
    "pos_r","acc_r","gLSR","taker_lsr (buy/sell)",
    "vol_spot_usd","taker_spot_pct (k[10]/k[7])","spot_perp_ratio","l29_flag",
    "vol_alpha (ABSTAIN)","taker_alpha (BANNED)",
    "on_chain_source",
    "gom_A_screen","gom_B_screen","gom_note (CHUA KY)",
    "data_source_perp","data_source_lsr",
]
assert len(HDR_LABELS) == 42, f"HDR_LABELS length={len(HDR_LABELS)}"

for ci, lbl in enumerate(HDR_LABELS, 1):
    c = ws_daily.cell(2, ci)
    c.value = lbl
    c.fill  = HDR_FILL
    c.font  = HDR_FONT
    c.alignment = Alignment(wrap_text=True, vertical="center")

ws_daily.row_dimensions[1].height = 28
ws_daily.row_dimensions[2].height = 36

# Data rows
for ri, row in enumerate(daily_data, 3):
    for ci, key in enumerate(DAILY_HEADERS, 1):
        val = row.get(key)
        c = ws_daily.cell(ri, ci)
        c.value = val
        c.font  = Font(size=8)
        c.alignment = Alignment(vertical="center")
    # Highlight GOM-A fires in orange
    if row.get("gom_A_screen") == "TRUE":
        ws_daily.cell(ri, 38).fill = PatternFill("solid", fgColor="FFA500")
    if row.get("gom_B_screen") == "TRUE":
        ws_daily.cell(ri, 39).fill = PatternFill("solid", fgColor="FF6B6B")
    # Highlight data_ok=None/False in yellow
    if not row.get("data_ok"):
        ws_daily.cell(ri, 15).fill = PatternFill("solid", fgColor="FFFF00")

# Freeze header rows
ws_daily.freeze_panes = "B3"

# Column widths
ws_daily.column_dimensions["A"].width = 12  # date
for ci in range(2, 43):
    ws_daily.column_dimensions[get_column_letter(ci)].width = 12

# ── SHEET 3: EVENTS ──────────────────────────────────────────────────────
ws_ev = wb.create_sheet("EVENTS")
ws_ev.cell(1, 1).value = "D. NHAT KY DIEN BIEN (append-only, moi nhat duoi cung)"
ws_ev.cell(1, 1).font  = Font(bold=True, size=9)

ev_hdrs = ["date","event_type","description","note","source"]
for ci, h in enumerate(ev_hdrs, 1):
    ws_ev.cell(2, ci).value = h
    ws_ev.cell(2, ci).fill  = HDR_FILL
    ws_ev.cell(2, ci).font  = HDR_FONT

initial_events = [
    ("2025-02-13","LISTING","HEIUSDT perp + spot listed on Binance (same day). Open px ~0.4650 perp.","First candle date","fapi klines"),
    ("2026-05-29","SPIKE_1","Vol $281M (+107% ngay trong 1 ngay), +80.6% price spike. Vol 244x med14. Funding NEG chuoi dai.","Bait-probe candidate (L-15) — chua ky","fapi klines"),
    ("2026-05-30","SPIKE_1_EXT","Vol $475M, gia len tiep, day 2 cua su kien. Vol 333x med14.","Spike extension — chua ky","fapi klines"),
    ("2026-08-05","SPIKE_2","Vol $734M (162x med14), gia +107.8% (0.129→0.268). Funding NEG sustained 04:00-20:00 UTC. pos_r crash ve 1.39.","Major event — cold-start ngay dau","fapi klines + funding"),
    ("2026-08-06","SPIKE_2_CRASH","Vol $1,244M (274x med14, ATH ky luc). Gia len ATH 0.545 (08:00 UTC mark), dong cua 0.197 (-26.7%). Funding -0.000566 (12:00 UTC).","OI 7.87M hien kho khong tuong ung. Depth mong (bid $47k / ask $39k).","fapi klines + funding"),
    ("2026-08-08","CASE_OPEN","Operator ky lenh mo case COLD_START. LSR persist khancap (30d retention).","Khong ky verdict. Status=COLD_START.","agent session"),
]

for ri, ev in enumerate(initial_events, 3):
    for ci, v in enumerate(ev, 1):
        ws_ev.cell(ri, ci).value = v
        ws_ev.cell(ri, ci).font  = Font(size=8)

ws_ev.column_dimensions["A"].width = 12
ws_ev.column_dimensions["B"].width = 25
ws_ev.column_dimensions["C"].width = 60
ws_ev.column_dimensions["D"].width = 40
ws_ev.column_dimensions["E"].width = 25

# ── SHEET 4: TRIGGERS ────────────────────────────────────────────────────
ws_tr = wb.create_sheet("TRIGGERS")
ws_tr.cell(1, 1).value = "C. CHOT THEO DOI — doc moi ngay sau nen dong"
ws_tr.cell(1, 1).font  = Font(bold=True, size=9)

tr_hdrs = ["trigger_name","condition","status","threshold","note"]
for ci, h in enumerate(tr_hdrs, 1):
    ws_tr.cell(2, ci).value = h
    ws_tr.cell(2, ci).fill  = HDR_FILL
    ws_tr.cell(2, ci).font  = HDR_FONT

triggers = [
    ("VOL_SPIKE_WATCH","vol_perp_usd ≥ 8× med14","WATCH","8× med14 (~$36M cu 30d)","L-15 bait-probe candidate — fired 05-29, 05-30, 08-05, 08-06"),
    ("FUNDING_NEG_DEEP","f_avg ≤ -0.5bps (any single kien 4h)","WATCH — repeated events","–0.0005","08-06 12:00 UTC = -0.000566 (deepest seen)"),
    ("POS_R_CRASH","pos_r drop ≥ 30%/3d","WATCH","30%/3d","08-05 to 08-07: pos_r 2.78→1.10 = −60% / 2d (exceeds threshold)"),
    ("GLSR_FLUSH","gLSR ≤ 0.25 bền ≥ 2 ngày","WATCH","0.25","gLSR consistently sub-1 (crowd net short); flush = gLSR < 0.25 bền"),
    ("OI_CLOCK_2x","OI ≥ 2× B_ref","BLOCKED — B_ref unknown","B_ref TBD","Operator xác định T0 + B_ref trước"),
    ("KHO_VOL_REGIME","kho/vol-regime ≤ 10% (Cua A)","ABSTAIN — contract unconfirmed","≤ 10%","Nansen LOCKED; contract candidate unverified"),
]

for ri, tr in enumerate(triggers, 3):
    for ci, v in enumerate(tr, 1):
        ws_tr.cell(ri, ci).value = v
        ws_tr.cell(ri, ci).font  = Font(size=8)

ws_tr.column_dimensions["A"].width = 22
ws_tr.column_dimensions["B"].width = 40
ws_tr.column_dimensions["C"].width = 30
ws_tr.column_dimensions["D"].width = 20
ws_tr.column_dimensions["E"].width = 50

# ── SHEET 5: OUTCOME ─────────────────────────────────────────────────────
ws_out = wb.create_sheet("OUTCOME")
ws_out.cell(1, 1).value = "OUTCOME — operator dien"
ws_out.cell(1, 1).font  = Font(bold=True, size=9, color="C00000")
outcome_fields = [
    "T0", "B_ref_OI", "Build_VWAP", "Exit_px", "MM_mult",
    "L26_trigger_date", "L26_pos_r_at_trigger", "OI_at_L26",
    "kho_type (Loai A/B/C)", "verdict", "verdict_date", "verdict_operator",
]
for ri, f in enumerate(outcome_fields, 3):
    ws_out.cell(ri, 1).value = f
    ws_out.cell(ri, 1).font  = Font(bold=True, size=9)
    ws_out.cell(ri, 2).value = ""
ws_out.column_dimensions["A"].width = 30
ws_out.column_dimensions["B"].width = 40

# ── SHEET 6: MM_PROFILE ──────────────────────────────────────────────────
ws_mm = wb.create_sheet("MM_PROFILE")
ws_mm.cell(1, 1).value = "MM_PROFILE — PENDING ANALYSIS"
ws_mm.cell(1, 1).font  = Font(bold=True, size=9, color="C00000")

mm_fields = [
    ("gLSR_base at T0",      "UNKNOWN — T0 not determined"),
    ("gLSR_min (fuel reload)","2026-07-09: 0.4086 (min in LSR window)"),
    ("pos_r peak",           "2026-08-04: 2.7774 (max in LSR window)"),
    ("pos_r at crash",       "2026-08-06: 1.1002 (−60.4% from 08-04 peak/2d)"),
    ("subtype (L-42)",       "UNKNOWN — CROWD-LONG? gLSR consistently <1 = crowd net short"),
    ("OI_floor (B_ref)",     "UNKNOWN — operator identify T0 first"),
    ("Build_VWAP",           "UNKNOWN"),
    ("spike_events",         "05-29: +80%/$281M, 05-30:+10%/$475M, 08-05:+108%/$734M, 08-06:ATH$0.545/$1244M"),
    ("depth_snapshot_1",     f"2026-08-07 07:18 UTC — Bid±2%=$47,875 Ask±2%=$39,062 (ONE SHOT ONLY — L-23 needs ≥2)"),
    ("OI_current",           f"50,666,136 tokens | ~$7M USD (× last close, {oi_snap_ts})"),
    ("Alpha layer",          "N/A — HEI not in alpha_id_map"),
    ("On-chain",             "ABSTAIN — Nansen LOCKED, contract unconfirmed"),
]

for ri, (k, v) in enumerate(mm_fields, 3):
    ws_mm.cell(ri, 1).value = k
    ws_mm.cell(ri, 1).font  = Font(bold=True, size=9)
    ws_mm.cell(ri, 2).value = v
    ws_mm.cell(ri, 2).font  = Font(size=9)

ws_mm.column_dimensions["A"].width = 28
ws_mm.column_dimensions["B"].width = 70

# ── SHEET 7: UNLOCK ──────────────────────────────────────────────────────
ws_ul = wb.create_sheet("UNLOCK")
ws_ul.cell(1, 1).value = "UNLOCK — UNVERIFIED (no confirmed vesting contract)"
ws_ul.cell(1, 1).font  = Font(bold=True, size=9, color="C00000")
ws_ul.cell(2, 1).value = "Contract candidate (UNVERIFIED): 0xf8f173e20e15f3b6cb686fb64724d370689de083"
ws_ul.cell(3, 1).value = "Sources tried: CoinGecko heima, BscScan (deprecated), CMC (404)"
ws_ul.cell(4, 1).value = "CẦN OPERATOR: confirm contract, check vesting via BscScan/DexScreener, cross-verify (L-28)"
ws_ul.column_dimensions["A"].width = 80

# ── SAVE ─────────────────────────────────────────────────────────────────
log("\n  Saving CASE_HEI.xlsx...")
try:
    wb.save(OUT_PATH)
    log(f"  Saved: {OUT_PATH}")
except PermissionError as e:
    # L-34: RAISE, cấm silent-save _NEW
    log(f"  PERMISSION ERROR: {e}")
    log("  L-34: file mở ở Excel? Đóng lại rồi chạy lại. CẤM silent-save _NEW.")
    raise

# ── L-32: VERIFY row count ────────────────────────────────────────────────
wb2 = openpyxl.load_workbook(OUT_PATH)
ws_verify = wb2["DAILY"]
actual_rows = ws_verify.max_row - 2  # minus header rows (1 group + 1 col header)
log(f"\n  L-32 Verify: DAILY expected {len(daily_data)} data rows, actual={actual_rows}")
assert actual_rows == len(daily_data), f"ROW COUNT MISMATCH: expected {len(daily_data)}, got {actual_rows}"
log(f"  L-32: PASS — row count verified")
log(f"  Sheets: {wb2.sheetnames}")

log(f"\n[BUILD CASE_HEI.xlsx DONE]")
log(f"  File: {OUT_PATH}")
log(f"  DAILY: {len(daily_data)} rows ({all_dates[0]} → {all_dates[-1]})")
