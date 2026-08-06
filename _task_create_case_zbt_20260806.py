"""Create CASE_ZBT.xlsx — fill DAILY sheet từ ZBT cold-refresh data (23/07→05/08).
Schema: clone từ CASE_BR.xlsx. Verdict = blank (operator only).
"""
import sys, io, statistics
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
from datetime import date
import openpyxl
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
from openpyxl.utils import get_column_letter
import copy

case_dir = Path(r"D:\Data back test\whale_data\docs\case_files")
out_path = case_dir / "CASE_ZBT.xlsx"

# ── DATA ──────────────────────────────────────────────────────────────────────
# OI hist 30d (for med14 / cycle_pos computation)
oi_hist = {
    "2026-07-08": 8447113, "2026-07-09": 8233642, "2026-07-10": 8232407,
    "2026-07-11": 8695522, "2026-07-12": 8249896, "2026-07-13": 8028748,
    "2026-07-14": 11221125, "2026-07-15": 8437412, "2026-07-16": 7765104,
    "2026-07-17": 7747593, "2026-07-18": 7708393, "2026-07-19": 9173495,
    "2026-07-20": 8087758, "2026-07-21": 7909722, "2026-07-22": 8502284,
    "2026-07-23": 8725833, "2026-07-24": 9318649, "2026-07-25": 8545317,
    "2026-07-26": 8452299, "2026-07-27": 8786963, "2026-07-28": 8860722,
    "2026-07-29": 8609763, "2026-07-30": 8476904, "2026-07-31": 9143286,
    "2026-08-01": 8981809, "2026-08-02": 8718627, "2026-08-03": 9297648,
    "2026-08-04": 8579454, "2026-08-05": 7889446,
}
oi_dates = sorted(oi_hist.keys())

def med14(d_str):
    idx = oi_dates.index(d_str)
    window = [oi_hist[oi_dates[i]] for i in range(max(0, idx-13), idx+1)]
    if len(window) < 14:
        return None
    return statistics.median(window)

def oi_cycle(d_str):
    idx = oi_dates.index(d_str)
    window = [oi_hist[oi_dates[i]] for i in range(max(0, idx-13), idx+1)]
    if len(window) < 14:
        return None
    mn, mx = min(window), max(window)
    if mx == mn:
        return None
    return (oi_hist[d_str] - mn) / (mx - mn)

# Rows: (date_str, px_avg, vol_perp, taker_pct, f_avg, f_min, f_max, fn,
#         oi, pos_r, acc_r, glsr, vol_spot, data_bad)
# None = MISSING for that field
ROWS = [
    # date_str       px_avg     vol_perp    taker  f_avg  f_min  f_max fn       oi          pos_r   acc_r   gLSR    vol_spot  db
    ("2026-07-23", 0.108405, 22092107.0,  50.6, 5e-05, 5e-05, 5e-05, 6, 8725833.0,  2.3707, 0.5780, 0.3951, 2362962.0, 0),
    ("2026-07-24", None,     10524962.0,  None,  None,  None,  None, None, 9318649.0, None,   None,   None,   2037632.0, 1),
    ("2026-07-25", None,      4582927.0,  None,  None,  None,  None, None, 8545317.0, None,   None,   None,   1103203.0, 1),
    ("2026-07-26", None,      9322656.0,  None,  None,  None,  None, None, 8452299.0, None,   None,   None,   2345884.0, 1),
    ("2026-07-27", 0.114577,  6418842.0,  47.1, 5e-05, 5e-05, 5e-05, 6, 8786963.0,  2.7540, 0.6614, 0.4482, 1483029.0, 0),
    ("2026-07-28", 0.112762,  4704342.0,  49.0, 5e-05, 5e-05, 5e-05, 6, 8860722.0,  2.7491, 0.7097, 0.4575, 1323597.0, 0),
    ("2026-07-29", 0.112684,  4983027.0,  47.1, 5e-05, 5e-05, 5e-05, 6, 8609763.0,  2.6781, 0.7024, 0.4626, 1541066.0, 0),
    ("2026-07-30", 0.116593,  6910711.0,  51.7, 5e-05, 5e-05, 5e-05, 6, 8476904.0,  2.7421, 0.7077, 0.4535, 2118287.0, 0),
    ("2026-07-31", 0.115980,  4394032.0,  48.6, 5e-05, 5e-05, 5e-05, 6, 9143286.0,  2.9249, 0.7106, 0.4643, 1013687.0, 0),
    ("2026-08-01", 0.116464,  2541983.0,  45.8, 5e-05, 5e-05, 5e-05, 6, 8981809.0,  3.0691, 0.7699, 0.5140,  535087.0, 0),
    ("2026-08-02", 0.122224,  6211662.0,  49.4, 5e-05, 5e-05, 5e-05, 6, 8718627.0,  3.4081, 0.7544, 0.5117, 1688089.0, 0),
    ("2026-08-03", 0.118481,  3507809.0,  47.1, 5e-05, 5e-05, 5e-05, 6, 9297648.0,  3.2607, 0.8245, 0.5586,  860103.0, 0),
    ("2026-08-04", 0.111582,  3564479.0,  50.0, 5e-05, 5e-05, 5e-05, 6, 8579454.0,  3.3595, 0.8175, 0.5571,  957955.0, 0),
    ("2026-08-05", 0.117641, 15060833.0,  50.6, 5e-05, 5e-05, 5e-05, 6, 7889446.0,  3.4072, 0.7467, 0.4914, 4776726.0, 0),
]

# ── DERIVED METRICS ────────────────────────────────────────────────────────────
def compute_derived(rows):
    n = len(rows)
    result = []
    for i, r in enumerate(rows):
        d, px, vp, tk, fa, fmn, fmx, fn, oi, pr, ar, gLSR, vs, db = r

        # ret_1d: use px_avg sequential, skip klines-only rows
        ret_1d = None
        if i > 0 and px is not None and rows[i-1][1] is not None:
            ret_1d = round((px / rows[i-1][1] - 1) * 100, 4)

        # pin_streak: f_avg in [4e-5, 6e-5], restart if no funding
        pin = None
        if fa is not None and 4e-5 <= fa <= 6e-5:
            # count back
            streak = 1
            j = i - 1
            while j >= 0 and rows[j][4] is not None and 4e-5 <= rows[j][4] <= 6e-5:
                streak += 1
                j -= 1
            pin = streak

        # oi_vs_med14
        m14 = med14(d)
        oi_med = round(oi / m14, 4) if (oi and m14) else None

        # oi_cycle_pos
        ocp = oi_cycle(d)
        ocp = round(ocp, 4) if ocp is not None else None

        # div_raw = pos_r / acc_r
        div_raw = round(pr / ar, 4) if (pr and ar) else None

        # div_avg3 = avg3(pos_r) / avg3(acc_r)
        div_avg3 = None
        if i >= 2:
            prs = [rows[k][9] for k in range(i-2, i+1)]
            ars = [rows[k][10] for k in range(i-2, i+1)]
            if all(v is not None for v in prs + ars):
                div_avg3 = round(sum(prs)/3 / (sum(ars)/3), 4)

        # glsr_slope_5d = gLSR(t) / gLSR(t-5)
        slope5 = None
        if i >= 5 and gLSR is not None:
            ref = rows[i-5][11]
            if ref is not None:
                slope5 = round(gLSR / ref, 4)

        # d_pos_3d = pos_r(t) - pos_r(t-3)
        d_pos3 = None
        if i >= 3 and pr is not None and rows[i-3][9] is not None:
            d_pos3 = round(pr - rows[i-3][9], 4)

        # d_acc_3d = acc_r(t) - acc_r(t-3)
        d_acc3 = None
        if i >= 3 and ar is not None and rows[i-3][10] is not None:
            d_acc3 = round(ar - rows[i-3][10], 4)

        result.append({
            "date": d, "px_avg": px, "ret_1d": ret_1d, "vol_perp_usd": vp,
            "taker_buy_pct": tk, "f_avg": fa, "f_min": fmn, "f_max": fmx, "f_n": fn,
            "funding_regime": None, "pin_streak": pin,
            "oi_usd": oi, "oi_vs_med14": oi_med, "oi_cycle_pos": ocp,
            "lsr_pos_r": pr, "lsr_acc_r": ar, "lsr_global_r": gLSR,
            "div_raw": div_raw, "div_avg3": div_avg3, "glsr_slope_5d": slope5,
            "d_pos_3d": d_pos3, "d_acc_3d": d_acc3,
            "signals_bullish": None, "signals_suppress": None, "screen_rank": None,
            "data_bad": db,
            "spot_venue": "binance_spot", "vol_spot_usd": vs,
            "taker_spot_pct": None,   # ABSTAIN — units invalid
            "depth_bid2_usd": None, "depth_ask2_usd": None,
            "bid_wall_px": None, "bid_wall_usd": None,
            "ask_wall_px": None, "ask_wall_usd": None,
            "alpha_suspect": "DELISTED",  # ZBT fullyDelisted on Alpha
            "exch_balance_delta": None, "wallet_activity": None,
            "dominance_pct": None,
            "note_operator": None, "mm_note": None,
        })
    return result

computed = compute_derived(ROWS)

# ── BUILD XLSX ─────────────────────────────────────────────────────────────────
# Load CASE_BR as template for formatting
wb_template = openpyxl.load_workbook(case_dir / "CASE_BR.xlsx")

wb = openpyxl.Workbook()
wb.remove(wb.active)  # remove default sheet

SHEETS = ["CASE", "DAILY", "EVENTS", "TRIGGERS", "OUTCOME", "MM_PROFILE", "UNLOCK"]
for sh in SHEETS:
    wb.create_sheet(sh)

# ── CASE sheet ──
ws_case = wb["CASE"]
ws_case["A1"] = "CASE FILE — ZBT"
ws_case["A2"] = "Nguon: case_tracker v1.1 · verdict chi operator ghi · so kem nguon · PENDING khong doan"
ws_case["A3"] = "Status"
ws_case["B3"] = "COLD_REFRESH — PENDING (verdict trong tay operator)"
ws_case["A4"] = "Loai"
ws_case["B4"] = "cold-refresh (diem mu sau U50, chua phan loai)"
ws_case["A5"] = "Ngay phat hien"
ws_case["B5"] = "06/08/2026 — cold-refresh lan dau tu 23/07"
ws_case["A6"] = "T0"
ws_case["B6"] = "unknown — chua xac dinh"
ws_case["A7"] = "action_class"
ws_case["B7"] = "PENDING — verdict trong tay operator"
ws_case["A8"] = "Vi the"
ws_case["B8"] = "none"
ws_case["A9"] = "Tom tat input"
ws_case["B9"] = ("ZBTUSDT cold-refresh 23/07→05/08. "
                 "Alpha DELISTED (ALPHA_435 fullyDelisted, HTTP 400). "
                 "Export gap 24-26/07 (LSR/funding MISSING). "
                 "Pin streak 10d (27/07→05/08), f_avg=5e-05 toan window. "
                 "pos_r>=3.0 tu 01/08 (5 ngay lien tuc, max 3.4081 ngay 02/08). "
                 "div_avg3 4.1-4.2 tu 02/08. gLSR slope_5d >1.0 toan window. "
                 "OI floor 14d YES (05/08=min), 30d NO (06/08 tang len 10.1M). "
                 "Depth ±2% snapshot 06/08T06:56 UTC: bid=$11,723 ask=$17,857 (~$29K). "
                 "Nansen LOCKED. Unlock UNVERIFIED. "
                 "Xem: docs/reports/_collect_zbt_20260806.md")
ws_case["A10"] = "Verdict (operator)"
ws_case["B10"] = None   # HUMAN — blank
ws_case["A11"] = "Dieu gi chung minh SAI"
ws_case["B11"] = None   # HUMAN — blank
ws_case["A12"] = "LEGEND"
ws_case["B12"] = ("O vang = operator dien/quyet · "
                  "Header nau vang (sheet DAILY) = cot manual · "
                  "Dong to cam (DAILY) = data_bad=1, so mang sai so (24-26/07: LSR/funding MISSING) · "
                  "Cot cong thuc (ret_1d, div, slope, oi_vs_med14, oi_cycle_pos) da tinh san trong file nay.")

# ── DAILY sheet ──
ws = wb["DAILY"]
COLS = [
    "date","px_avg","ret_1d","vol_perp_usd","taker_buy_pct",
    "f_avg","f_min","f_max","f_n","funding_regime","pin_streak",
    "oi_usd","oi_vs_med14","oi_cycle_pos",
    "lsr_pos_r","lsr_acc_r","lsr_global_r",
    "div_raw","div_avg3","glsr_slope_5d","d_pos_3d","d_acc_3d",
    "signals_bullish","signals_suppress","screen_rank","data_bad",
    "spot_venue","vol_spot_usd","taker_spot_pct",
    "depth_bid2_usd","depth_ask2_usd",
    "bid_wall_px","bid_wall_usd","ask_wall_px","ask_wall_usd",
    "alpha_suspect",
    "exch_balance_delta","wallet_activity","dominance_pct",
    "note_operator","mm_note",
]
assert len(COLS) == 41

SECTION_ROW = [None]*41
SECTION_ROW[0]  = "PERP (may)"
SECTION_ROW[26] = "SPOT/ALPHA (may)"
SECTION_ROW[36] = "ON-CHAIN (ban tu dong)"
SECTION_ROW[39] = "MANUAL (operator)"

ws.append(SECTION_ROW)
ws.append(COLS)

# Fill styles
fill_bad = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")
fill_hdr = PatternFill(start_color="BF8F00", end_color="BF8F00", fill_type="solid")
bold = Font(bold=True)

# Style section header row
for i, v in enumerate(SECTION_ROW, 1):
    if v is not None:
        ws.cell(1, i).font = bold

# Style col header row
for i in range(1, 42):
    ws.cell(2, i).font = bold

# Data rows
for rec in computed:
    row = [rec[c] for c in COLS]
    ws.append(row)

# Highlight data_bad=1 rows (red fill)
for r_idx, rec in enumerate(computed, start=3):
    if rec["data_bad"] == 1:
        for c_idx in range(1, 42):
            ws.cell(r_idx, c_idx).fill = fill_bad

# Mark manual cols (40,41) header in brown/gold
for c_idx in [40, 41]:
    ws.cell(2, c_idx).fill = fill_hdr
    ws.cell(2, c_idx).font = Font(bold=True, color="FFFFFF")

# Column widths
ws.column_dimensions["A"].width = 12
for c in range(2, 42):
    ws.column_dimensions[get_column_letter(c)].width = 13

# ── EVENTS sheet (header only) ──
ws_ev = wb["EVENTS"]
ws_ev["A1"] = "D. NHAT KY DIEN BIEN (append-only, moi nhat duoi cung)"
ws_ev.append(["date", "event", "source", "note"])

# ── TRIGGERS sheet ──
ws_tr = wb["TRIGGERS"]
ws_tr["A1"] = "C. CHOT THEO DOI — doc moi ngay sau nen dong"
ws_tr.append(["#", "trigger", "met?", "date_met", "note"])

# ── OUTCOME sheet ──
ws_out = wb["OUTCOME"]
ws_out["A1"] = "E. OUTCOME — dien tai moc; verdict_check: verdict luc mo DUNG/SAI o diem nao"

# ── MM_PROFILE sheet ──
ws_mm = wb["MM_PROFILE"]
ws_mm["A1"] = "I. MM / OPERATOR PROFILE — van tay hanh vi"

# ── UNLOCK sheet ──
ws_ul = wb["UNLOCK"]
ws_ul["A1"] = "J. TOKENOMICS / UNLOCK — dong cung co lich, MM danh quanh no"
ws_ul["A2"] = "ZBT unlock schedule: UNVERIFIED (L-28 — can operator xac minh nguon)"

# ── SAVE ──
wb.save(out_path)
print(f"Saved: {out_path}")
print(f"DAILY rows: {len(computed)} (rows 3-{2+len(computed)})")
print("\nSample computed rows:")
for rec in computed:
    print(f"  {rec['date']}  px={rec['px_avg']}  ret={rec['ret_1d']}  pin={rec['pin_streak']}"
          f"  oi_med={rec['oi_vs_med14']}  ocp={rec['oi_cycle_pos']}"
          f"  div_avg3={rec['div_avg3']}  slope5={rec['glsr_slope_5d']}  db={rec['data_bad']}")
print("\n[DONE]")
