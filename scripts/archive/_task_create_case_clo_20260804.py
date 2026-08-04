#!/usr/bin/env python3
"""Task: tao CASE_CLO.xlsx theo template CASE_BANK/TAG."""
import sys, io, csv, json
from pathlib import Path
from datetime import datetime, timezone
import urllib.request, urllib.error

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

OUT = Path(r"D:\Data back test\whale_data\docs\case_files\CASE_CLO.xlsx")
EXP = Path(r"D:\Check onchain fresh wallets\data\export")

# ── helpers ──────────────────────────────────────────────────────────────────
def gv(r, k):
    v = r.get(k, "")
    if v in ("", None): return None
    try: return float(v)
    except: return None

def fetch_json(url, timeout=25):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        return {"error": str(e)}

def hdr_fill(color="1F4E79"):
    return PatternFill("solid", fgColor=color)

def sec_fill(color="2E75B6"):
    return PatternFill("solid", fgColor=color)

def sub_fill(color="BDD7EE"):
    return PatternFill("solid", fgColor=color)

def bold_white():
    return Font(bold=True, color="FFFFFF", size=10)

def bold_dark():
    return Font(bold=True, color="1F4E79", size=10)

def norm():
    return Font(size=10)

thin = Side(style="thin", color="D9D9D9")
thin_border = Border(left=thin, right=thin, top=thin, bottom=thin)

# ── 1. Fetch klines daily 01/03-04/08 ────────────────────────────────────────
print("Fetching klines daily...")
start_ts = int(datetime(2026, 3, 1, 0, 0, 0, tzinfo=timezone.utc).timestamp() * 1000)
klines = fetch_json(
    f"https://fapi.binance.com/fapi/v1/klines?symbol=CLOUSDT&interval=1d&startTime={start_ts}&limit=200"
)
klines_dict = {}  # date -> row
if isinstance(klines, list):
    prev_c = None
    for k in klines:
        ts = int(k[0])
        d = datetime.fromtimestamp(ts/1000, tz=timezone.utc).strftime('%Y-%m-%d')
        o, h, lo, c = float(k[1]), float(k[2]), float(k[3]), float(k[4])
        vol_usd = float(k[7])
        tb_q = float(k[10])
        tk_pct = tb_q/vol_usd if vol_usd > 0 else None
        ret = (c - prev_c) / prev_c if prev_c else None
        klines_dict[d] = {
            'px': c, 'open': o, 'high': h, 'low': lo,
            'vol': vol_usd, 'tk': tk_pct, 'ret': ret
        }
        prev_c = c
    print(f"  klines: {len(klines_dict)} rows")
else:
    print(f"  klines error: {klines}")

# ── 2. Fetch funding daily aggregates 01/04-04/08 ────────────────────────────
print("Fetching funding...")
start_f = int(datetime(2026, 4, 1, 0, 0, 0, tzinfo=timezone.utc).timestamp() * 1000)
fund_raw = fetch_json(
    f"https://fapi.binance.com/fapi/v1/fundingRate?symbol=CLOUSDT&startTime={start_f}&limit=1000"
)
fund_dict = {}  # date -> {avg, min, max, n}
if isinstance(fund_raw, list):
    daily = {}
    for row in fund_raw:
        ts = int(row['fundingTime'])
        d = datetime.fromtimestamp(ts/1000, tz=timezone.utc).strftime('%Y-%m-%d')
        fr = float(row['fundingRate'])
        if d not in daily: daily[d] = []
        daily[d].append(fr)
    for d, vals in daily.items():
        fund_dict[d] = {
            'avg': sum(vals)/len(vals),
            'min': min(vals),
            'max': max(vals),
            'n': len(vals)
        }
    print(f"  funding: {len(fund_dict)} days")
else:
    print(f"  funding error: {fund_raw}")

# ── 3. Fetch OI daily 07/05-04/08 ─────────────────────────────────────────────
print("Fetching OI...")
oi_raw = fetch_json(
    "https://fapi.binance.com/futures/data/openInterestHist?symbol=CLOUSDT&period=1d&limit=90"
)
oi_dict = {}  # date -> oi_usd
if isinstance(oi_raw, list):
    for row in oi_raw:
        ts = int(row['timestamp'])
        d = datetime.fromtimestamp(ts/1000, tz=timezone.utc).strftime('%Y-%m-%d')
        oi_dict[d] = float(row['sumOpenInterestValue'])
    print(f"  OI: {len(oi_dict)} rows")
else:
    print(f"  OI error: {oi_raw}")

# ── 4. Load freshwatch CLO ─────────────────────────────────────────────────────
print("Loading freshwatch...")
fw_dict = {}  # date -> row_dict
for f in sorted(EXP.glob("freshwatch_daily_2026-*.csv")):
    for r in csv.DictReader(open(f, encoding="utf-8-sig")):
        if r.get("symbol","") == "CLOUSDT":
            fw_dict[r["date"]] = r
print(f"  freshwatch: {len(fw_dict)} rows")

# ── 5. Build DAILY rows ────────────────────────────────────────────────────────
# Pre-freshwatch key dates (from klines only, data_bad=1)
pre_fw_dates = [
    # Campaign 1 key days
    "2026-04-01",  # kick-off +20%
    "2026-04-05",  # wave 1 H=0.100
    "2026-04-06",  # vol 13.5M
    "2026-04-17",  # wave 2 peak vol 29M, f=0.00086
    "2026-04-18",  # H=0.150
    "2026-04-22",  # abs high H=0.173
    "2026-05-07",  # vol burst +30.5%
    "2026-05-16",  # crash -28.2%
    "2026-05-19",  # low L=0.055
    # Campaign 2 build + markup
    "2026-05-27",  # kick-off +18.5%
    "2026-05-28",  # vol 25.5M
    "2026-05-29",  # vol 34M
    "2026-05-30",  # +26.4%
    "2026-06-01",  # +29.2%
    "2026-06-02",  # +31.7% to 0.140
    "2026-06-03",  # H=0.199, vol 147M
    "2026-06-04",  # crash -29.6%
]

def make_daily_row(date):
    """Build 41-col DAILY row for given date."""
    k = klines_dict.get(date, {})
    fw = fw_dict.get(date, {})
    fd = fund_dict.get(date, {})
    oi = oi_dict.get(date)

    in_fw = bool(fw)
    data_bad = None if in_fw else 1  # klines-only rows

    # px_avg: prefer freshwatch px_avg, else klines close
    px = gv(fw, 'px_avg') if in_fw else k.get('px')
    vol = gv(fw, 'vol_quote') if in_fw else k.get('vol')
    tk = gv(fw, 'taker_pct') if in_fw else (k.get('tk') * 100 if k.get('tk') else None)
    ret = gv(fw, 'ret_1d') if in_fw else k.get('ret')

    # funding: prefer freshwatch, then fapi daily agg
    if in_fw:
        f_avg = gv(fw, 'funding_avg')
        f_n   = gv(fw, 'funding_n')
        f_min = None
        f_max = None
    else:
        f_avg = fd.get('avg')
        f_min = fd.get('min')
        f_max = fd.get('max')
        f_n   = fd.get('n')

    # funding_regime
    if f_avg is not None:
        if f_avg <= 5.5e-5:
            regime = "PINNED"
        elif f_avg >= 0.0003:
            regime = "HOT"
        elif f_avg < 0:
            regime = "NEG"
        else:
            regime = "WARM"
    else:
        regime = None

    # OI: prefer freshwatch oi_usd, then fapi OI
    oi_usd = gv(fw, 'oi_usd') if in_fw else oi

    # LSR
    pos_r = gv(fw, 'lsr_pos_r') if in_fw else None
    acc_r = gv(fw, 'lsr_acc_r') if in_fw else None
    gLSR  = gv(fw, 'lsr_global_r') if in_fw else None

    # derived
    div_raw  = gv(fw, 'div_raw') if in_fw else None
    div_avg3 = gv(fw, 'div_avg3') if in_fw else None
    slope    = gv(fw, 'slope') if in_fw else None
    d_pos_3d = gv(fw, 'd_pos_3d') if in_fw else None
    d_acc_3d = gv(fw, 'd_acc_3d') if in_fw else None

    return [
        date, px, ret, vol, tk,
        f_avg, f_min, f_max, f_n, regime, None,   # pin_streak manual
        oi_usd, None, None,                         # oi_vs_med14, oi_cycle_pos
        pos_r, acc_r, gLSR,
        div_raw, div_avg3, slope,
        d_pos_3d, d_acc_3d,
        None, None, None,                           # signals_bullish, suppress, screen_rank
        data_bad,
        None, None, None,                           # spot_venue, vol_spot_usd, taker_spot_pct
        None, None, None, None, None, None,         # depth, walls
        None,                                       # alpha_suspect
        None, None, None,                           # exch_balance_delta, wallet_activity, dominance_pct
        None, None                                  # note_operator, mm_note
    ]

# Collect all dates
all_dates = sorted(set(list(pre_fw_dates) + list(fw_dict.keys())))
daily_rows = []
for d in all_dates:
    if d in klines_dict or d in fw_dict:
        daily_rows.append(make_daily_row(d))

print(f"  DAILY rows built: {len(daily_rows)}")

# ── 6. Build workbook ─────────────────────────────────────────────────────────
wb = openpyxl.Workbook()
wb.remove(wb.active)  # remove default sheet

# ── SHEET: CASE ───────────────────────────────────────────────────────────────
ws = wb.create_sheet("CASE")
ws.column_dimensions['A'].width = 28
ws.column_dimensions['B'].width = 72

case_data = [
    ["CASE FILE — CLO", None],
    ["Nguon: case_tracker v1.1 · verdict chi operator ghi · so kem nguon · PENDING khong doan", None],
    [None, None],
    ["Status",          "TRACKING (post-campaign cooldown — verdict PENDING operator 04/08)"],
    ["Loai",            "pump-setup multi-campaign (3 vong xac nhan: Apr/May-Jun/Jul 2026)"],
    ["Ngay phat hien",  "04/08/2026 — thesis test session (C1-C6 analysis)"],
    ["T0",              "2026-07-07 (Campaign 3 kick-off) · px T0 ~0.148 (close 06/07)"],
    ["action_class",    "PENDING operator ky — hai phuong an: (a) NO_SETUP/WATCH-nhat  (b) STAND_ASIDE co dong ho (overhang C4)"],
    [None, None],
    ["A. CAMPAIGN HISTORY", None],
    ["Campaign 1",      "Apr 2026: build~0.070, H=0.173 (22/04), px_mult~2.3x, f_peak=0.00086, vol_peak=40M"],
    ["Campaign 2",      "May-Jun 2026: build~0.067, H=0.304 (23/06), px_mult~3.5x, f_peak=0.00090, OI_peak=10.95M"],
    ["Campaign 3",      "Jul 2026: build_VWAP=0.143, exit_VWAP=0.256, px_mult=1.79x, B=3.944M, OI_peak=10.394M (2.63x)"],
    [None, None],
    ["B. MM-ECON SUMMARY", None],
    ["Build_VWAP C3",   "0.1433 USDT (07/01-07/06, vol-weighted klines daily)"],
    ["Exit_VWAP C3",    "0.2559 USDT (07/12-07/13, 2-day VWAP)"],
    ["OI_mult C3",      "2.63x (B_T0=3.944M -> peak=10.394M)"],
    ["dOI_cum/B peak",  "+1.64x at D+6 (07/13) — fast campaign vs BANK D+10 (+5.16x)"],
    ["gLSR behavior",   "SHORT-WASH cau truc: gLSR < 0.85 tai peak MOI campaign (08/07, 12/07, 21/07)"],
    [None, None],
    ["C. COOLDOWN STATUS (04/08)", None],
    ["gLSR",            "2.6483 (03/08) — ANOMALY: cao nhat toan bo 53-row history; crowd LONG nhat trong flat price"],
    ["pos_r",           "0.854 (declining, duoi 1.0 tu 13/07)"],
    ["OI",              "4.1-4.6M stable — khong build, khong xa het"],
    ["vol cooldown",    "1.7-8M/day (dead market)"],
    ["L-26 trigger",    "KHONG fire trong C3 exit — exit theo price dump (07/13 -15.1%), khong phai pos_r flush"],
    ["dist_wall/lsr_dist", "ABSENT trong freshwatch CLO (khong verify duoc)"],
    [None, None],
    ["D. ON-CHAIN (R4)", None],
    ["Dominance",       "THAP — full tieng noi on-chain nhu R4"],
    ["K_spot kho",      "PENDING OPERATOR (O1) — calibrate C4 overhang clock"],
    ["On-chain balance","PENDING OPERATOR (O3) — Nansen LOCKED"],
]

for i, row in enumerate(case_data, 1):
    ws.cell(i, 1, row[0])
    ws.cell(i, 2, row[1])
    # Header row
    if i == 1:
        for c in [1, 2]:
            ws.cell(i, c).fill = hdr_fill()
            ws.cell(i, c).font = Font(bold=True, color="FFFFFF", size=12)
    elif row[0] and row[0].startswith(("A.", "B.", "C.", "D.")):
        ws.cell(i, 1).fill = sec_fill()
        ws.cell(i, 1).font = bold_white()
    elif row[0] and row[1] is not None:
        ws.cell(i, 1).font = Font(bold=True, size=10, color="1F4E79")
        ws.cell(i, 2).font = norm()

# ── SHEET: DAILY ──────────────────────────────────────────────────────────────
ws2 = wb.create_sheet("DAILY")

# Section header row 1
sec_headers = [
    ("PERP (may)", 1, 26),
    ("SPOT/ALPHA (may)", 27, 36),
    ("ON-CHAIN (ban tu dong)", 37, 39),
    ("MANUAL (operator)", 40, 41),
]
for label, col_start, col_end in sec_headers:
    ws2.cell(1, col_start, label)
    ws2.cell(1, col_start).fill = sec_fill()
    ws2.cell(1, col_start).font = bold_white()
    ws2.cell(1, col_start).alignment = Alignment(horizontal="center")
    if col_end > col_start:
        ws2.merge_cells(start_row=1, start_column=col_start, end_row=1, end_column=col_end)

# Column headers row 2
col_names = [
    'date','px_avg','ret_1d','vol_perp_usd','taker_buy_pct',
    'f_avg','f_min','f_max','f_n','funding_regime','pin_streak',
    'oi_usd','oi_vs_med14','oi_cycle_pos',
    'lsr_pos_r','lsr_acc_r','lsr_global_r',
    'div_raw','div_avg3','glsr_slope_5d',
    'd_pos_3d','d_acc_3d',
    'signals_bullish','signals_suppress','screen_rank','data_bad',
    'spot_venue','vol_spot_usd','taker_spot_pct',
    'depth_bid2_usd','depth_ask2_usd',
    'bid_wall_px','bid_wall_usd','ask_wall_px','ask_wall_usd',
    'alpha_suspect',
    'exch_balance_delta','wallet_activity','dominance_pct',
    'note_operator','mm_note'
]
for j, name in enumerate(col_names, 1):
    c = ws2.cell(2, j, name)
    c.fill = sub_fill()
    c.font = bold_dark()
    c.alignment = Alignment(horizontal="center")

# Data rows
for i, row in enumerate(daily_rows, 3):
    for j, val in enumerate(row, 1):
        c = ws2.cell(i, j, val)
        c.font = norm()
        c.border = thin_border
        # Alternate shading
        if i % 2 == 0:
            c.fill = PatternFill("solid", fgColor="F2F7FB")
        # Color-code data_bad rows
        if row[25] == 1:
            ws2.cell(i, 1).fill = PatternFill("solid", fgColor="FFF2CC")
        # Color-code gLSR anomaly
        if j == 17 and val is not None:
            if val >= 2.0:
                c.fill = PatternFill("solid", fgColor="FF6B6B")
                c.font = Font(bold=True, color="FFFFFF", size=10)
            elif val < 0.85:
                c.fill = PatternFill("solid", fgColor="FFD966")

# Column widths
widths = {1:12, 2:10, 3:9, 4:14, 5:12,
          6:9, 7:9, 8:9, 9:5, 10:13, 11:10,
          12:12, 13:12, 14:12,
          15:10, 16:10, 17:10,
          18:10, 19:10, 20:14,
          21:10, 22:10,
          23:14, 24:14, 25:12, 26:9,
          27:12, 28:14, 29:14,
          30:14, 31:14, 32:12, 33:12, 34:12, 35:12,
          36:13, 37:18, 38:15, 39:13,
          40:24, 41:24}
for col, w in widths.items():
    ws2.column_dimensions[get_column_letter(col)].width = w

ws2.freeze_panes = "B3"
ws2.row_dimensions[1].height = 18
ws2.row_dimensions[2].height = 16

# ── SHEET: EVENTS ─────────────────────────────────────────────────────────────
ws3 = wb.create_sheet("EVENTS")
ws3.column_dimensions['A'].width = 12
ws3.column_dimensions['B'].width = 60
ws3.column_dimensions['C'].width = 20
ws3.column_dimensions['D'].width = 28

events_data = [
    ["D. NHAT KY DIEN BIEN (append-only, moi nhat duoi cung)", None, None, None],
    [None, None, None, None],
    ["ngay", "su_kien_so_lieu", "nguon", "doc_nhanh"],
    ["04-01", "Campaign 1 kick-off +20% to 0.084, vol 22M", "fapi klines", "C1_start"],
    ["04-17", "C1 wave 2 peak: H=0.138, vol 29M, f=0.00086 (highest ever)", "fapi klines+funding", "C1_peak_funding"],
    ["04-22", "C1 absolute high: H=0.173, vol 40M, gLSR N/A", "fapi klines", "C1_abs_high"],
    ["05-16", "C1 crash -28.2%, vol 18M -> 0.082", "fapi klines", "C1_exit"],
    ["05-19", "C1 bottom: L=0.055, vol 11.5M", "fapi klines", "C1_low"],
    ["05-27", "Campaign 2 kick-off +18.5%, vol 19M", "fapi klines", "C2_start"],
    ["06-02/03", "C2 escalation: vol 39M/147M, H=0.199, f=0.00093/0.00076", "fapi klines+funding", "C2_vol_burst"],
    ["06-07/08", "C2 wave 2: OI 9.9->10.95M (peak 1), gLSR 1.22, vol 40-42M", "freshwatch", "C2_OI_peak1"],
    ["06-12", "C2 funding peak: f_avg=0.00090 (6 ticks), vol 38M, OI 8.2->7.8M", "fapi funding", "C2_f_peak"],
    ["06-15", "C2 wave 3 H=0.275, vol 101M, OI 8.0M, f=0.00073", "freshwatch", "C2_wave3"],
    ["06-21", "C2 OI peak 2: 10.72M, vol 66M, H=0.282", "freshwatch", "C2_OI_peak2"],
    ["06-23", "C2 absolute high: H=0.304, vol 84M, OI 9.3M, f=0.00046", "freshwatch", "C2_abs_high"],
    ["06-27", "C2 crash -27.4%, vol 24M -> cooldown (OI 5.8->4.0M 06/27-06/29)", "freshwatch", "C2_exit"],
    ["07-07", "Campaign 3 kick-off +36.5%, vol 40M, OI 3.944M (B_T0)", "freshwatch+klines", "C3_start"],
    ["07-08", "C3 vol 64M, OI +60% to 6.34M, gLSR 0.840 (SHORT-WASH signal 1)", "freshwatch", "C3_OI_spike"],
    ["07-11", "C3 push: H=0.272, vol 80M, f=0.00045", "freshwatch+klines", "C3_push"],
    ["07-12", "C3 absolute high: H=0.293, vol 48M, OI 10.16M, gLSR 0.849 (SHORT-WASH 2)", "freshwatch", "C3_abs_high"],
    ["07-13", "C3 OI peak: 10.394M (D+6), price dump -15.1% — exit window close", "freshwatch+OI", "C3_OI_peak"],
    ["07-21", "gLSR min: 0.8232 (SHORT-WASH 3, fuel-reload nadir), px 0.125", "freshwatch", "C3_glsr_min"],
    ["07-22", "px cooldown bottom: 0.109 (L=0.100 intraday), -66% from H=0.293", "freshwatch+klines", "C3_px_low"],
    ["07-23", "Bounce +12.2%, vol 31M (largest post-peak vol) — nghi distribution sell", "klines", "cooldown_bounce"],
    ["08-03", "gLSR ANOMALY: 2.648 — cao nhat 53-row history trong flat price; acc_r=2.894", "freshwatch", "glsr_anomaly"],
    ["08-04", "Verdict due (overdue tu 27/07): PENDING operator. Thesis C1-C6 complete.", "agent", "verdict_pending"],
]

for i, row in enumerate(events_data, 1):
    for j, val in enumerate(row, 1):
        c = ws3.cell(i, j, val)
        if i == 1:
            c.fill = hdr_fill(); c.font = bold_white()
        elif i == 3:
            c.fill = sub_fill(); c.font = bold_dark()
        else:
            c.font = norm(); c.border = thin_border
    if i == 1:
        ws3.merge_cells(start_row=1, start_column=1, end_row=1, end_column=4)

# ── SHEET: TRIGGERS ───────────────────────────────────────────────────────────
ws4 = wb.create_sheet("TRIGGERS")
ws4.column_dimensions['A'].width = 5
ws4.column_dimensions['B'].width = 22
ws4.column_dimensions['C'].width = 48
ws4.column_dimensions['D'].width = 36
ws4.column_dimensions['E'].width = 24

triggers_data = [
    ["C. CHOT THEO DOI — doc moi ngay sau nen dong", None, None, None, None],
    [None, None, None, None, None],
    ["#", "chot", "dieu_kien", "nghia_khi_bat", "trang_thai_hom_nay"],
    ["1", "Campaign 4 setup", "pos_r >1.2 + OI build >6M + vol burst >30M/day", "ARM_trigger — chien dich tai khoi dong", "PENDING — OI 4.6M, vol dead"],
    ["2", "gLSR SHORT-WASH", "gLSR < 0.85 (Campaign 4 peak signal)", "crowd short flood = peak signal nhu 08/07, 12/07, 21/07", "gLSR 2.648 — con xa"],
    ["3", "Funding burst", "f_avg > 0.00050 sustained 3d (>= 3 consecutive)", "pre-Campaign 4 crowd long overheating", "04/08: 0.00048 (theo doi)"],
    ["4", "Overhang terminus", "on-chain cum vi balance -> 0 hoac capitulation dump", "overhang cleared — STAND_ASIDE ket thuc", "PENDING OPERATOR (O3)"],
    ["5", "Bounce distribution", "vol spike >20M trong cooldown range (0.12-0.18)", "MM xa hang vao demand — KHONG phai reversal", "07/23 da co (31M) — 1 lan"],
]

for i, row in enumerate(triggers_data, 1):
    for j, val in enumerate(row, 1):
        c = ws4.cell(i, j, val)
        if i == 1:
            c.fill = hdr_fill(); c.font = bold_white()
        elif i == 3:
            c.fill = sub_fill(); c.font = bold_dark()
        else:
            c.font = norm(); c.border = thin_border
    if i == 1:
        ws4.merge_cells(start_row=1, start_column=1, end_row=1, end_column=5)

# ── SHEET: OUTCOME ─────────────────────────────────────────────────────────────
ws5 = wb.create_sheet("OUTCOME")
ws5.column_dimensions['A'].width = 8
ws5.column_dimensions['B'].width = 14
ws5.column_dimensions['C'].width = 12
ws5.column_dimensions['D'].width = 10
ws5.column_dimensions['E'].width = 36
ws5.column_dimensions['F'].width = 14
ws5.column_dimensions['G'].width = 10
ws5.column_dimensions['H'].width = 40
ws5.column_dimensions['I'].width = 20

outcome_data = [
    ["E. OUTCOME — dien tai moc; verdict_check: verdict luc mo DUNG/SAI o diem nao", None, None, None, None, None, None, None, None],
    [None]*9,
    ["moc","ngay_han","px","ret_pct","drawup_drawdown","oi_usd","gLSR","dien_bien","verdict_check"],
    # C3 T0 = 07/07
    ["C3 T+7",  "2026-07-14", 0.21039, "-28%", "H=0.293 (07/12) — 07/14 dang xuat", 7515000, 1.277, "Dump -28% tu exit_VWAP; OI xa 10.4->7.5M", None],
    ["C3 T+14", "2026-07-21", 0.12475, "-66%", "gLSR min 0.8232 — fuel-reload nadir", 4198000, 0.823, "Giá đáy vùng, gLSR trạm thấp nhất, vol tắt", None],
    ["C3 T+30", "2026-08-06", None, None, None, None, None, None, None],
    ["C3 T+60", "2026-09-05", None, None, None, None, None, None, None],
    [None]*9,
    ["Verdict", "2026-07-27", None, None, "QUA HAN — chua ky (overdue 8 ngay, verdict 04/08 pending)", None, None, None, None],
    ["NOTE_C3",
     "Build_VWAP=0.1433, Exit_VWAP=0.2559, MM_mult=1.79x. Khong co L-26 trigger — exit theo price dump. gLSR 2.648 anomaly trong cooldown (08/03). On-chain PENDING.",
     None, None, None, None, None, None, None],
]

for i, row in enumerate(outcome_data, 1):
    for j, val in enumerate(row, 1):
        c = ws5.cell(i, j, val)
        if i == 1:
            c.fill = hdr_fill(); c.font = bold_white()
        elif i == 3:
            c.fill = sub_fill(); c.font = bold_dark()
        else:
            c.font = norm()
            if val is not None: c.border = thin_border
    if i == 1:
        ws5.merge_cells(start_row=1, start_column=1, end_row=1, end_column=9)

# ── SHEET: MM_PROFILE ─────────────────────────────────────────────────────────
ws6 = wb.create_sheet("MM_PROFILE")
ws6.column_dimensions['A'].width = 28
ws6.column_dimensions['B'].width = 72

mm_data = [
    ["I. MM / OPERATOR PROFILE — van tay hanh vi (moi MM danh mot kieu)", None],
    [None, None],
    ["MM cong bo / nghi van",      "unknown — PENDING (CLO dominance thap, on-chain R4 co tieng noi)"],
    ["MM_ID (so chung)",           "UNKNOWN — chua du van tay de gan; co the MM-MULTI-CAMPAIGN dang calib"],
    ["Van tay funding",            "pin tuyet doi 0.00005 giua campaign; burst ngan tai peak (0.00086-0.00090); floor ngay sau dinh"],
    ["Van tay markup",             "multi-wave (C1: 3 waves; C2: 5 waves; C3: 2-day burst); SHORT-WASH structure tai peak moi campaign"],
    ["Ky thuat quan crowd",        "gLSR < 0.85 tai peak (crowd short flood = SHORT-WASH). Sau dinh: gLSR tang manh vao cooldown (crowd LONG fuel)"],
    ["Ky thuat on-chain",          "PENDING OPERATOR — CLO dominance thap, R4 co the xac nhan kho spot"],
    ["Archetype nghi van",         "C-vo-A-ruot: mua spot lam dao cu (tao price signal) + ket loi o perp long; don vi hach toan = CAMPAIGN"],
    [None, None],
    ["F1 (prior campaigns)",       "PASS — 3 campaigns xac nhan (Apr/May-Jun/Jul 2026)"],
    ["F2 (perp profit structure)", "PARTIAL PASS — MM_mult 1.79-3.47x across campaigns; perp proxy +$356k (K_perp=3.1M C3)"],
    ["F3 (net PnL positive)",      "PENDING — can K_spot tu operator (O1-O2)"],
    [None, None],
    ["Campaign cadence",           "~5-7 tuan giua dinh: C1 dinh 22/04 -> C2 dinh 23/06 (61 ngay) -> C3 dinh 12/07 (19 ngay, RUT NGAN)"],
    ["Ghi chu C3 ngan",            "C3 chi 5 ngay markup vs 5-7 tuan cac vong truoc — co the MM bi forced exit hoac cap lat roi ro"],
]

for i, row in enumerate(mm_data, 1):
    for j, val in enumerate(row, 1):
        c = ws6.cell(i, j, val)
        if i == 1:
            c.fill = hdr_fill(); c.font = bold_white()
        elif row[0] and row[0].startswith(("F1","F2","F3")):
            c.font = Font(bold=True, size=10, color="1F4E79")
        else:
            c.font = norm()
    if i == 1:
        ws6.merge_cells(start_row=1, start_column=1, end_row=1, end_column=2)

# ── SHEET: UNLOCK ─────────────────────────────────────────────────────────────
ws7 = wb.create_sheet("UNLOCK")
ws7.column_dimensions['A'].width = 28
ws7.column_dimensions['B'].width = 60

unlock_data = [
    ["J. TOKENOMICS / UNLOCK — dong cung co lich, MM danh quanh no", None],
    [None, None],
    ["Circulating / Total",   "PENDING OPERATOR — CLO dominance thap, can supply de tinh % kho"],
    ["Nguon tra",             "PENDING — CryptoRank / TokenUnlocks / BscScan"],
    ["Unlock KE TIEP",        "PENDING OPERATOR"],
    ["Unlock 90 ngay toi",    "PENDING OPERATOR"],
    ["Cliff da qua",          "PENDING OPERATOR"],
    ["K_spot kho MM",         "PENDING OPERATOR (O1) — calibrate C4 overhang clock"],
    ["Gia mua spot trung binh","PENDING OPERATOR (O2) — xac nhan F2/F3 PnL"],
    ["On-chain balance",      "PENDING OPERATOR (O3) — Nansen LOCKED; su dung BscScan free"],
    [None, None],
    ["C4 Overhang Clock",     "DEX BSC pool 0x8d23: liq=$1.3M, vol24h=$4.2M. CEX depth $16k. Absorb stealthy: ~$120k-220k/day"],
    ["Thoi han uoc",          "K=5M tokens -> 2.8-5.2 tuan; K=10M -> 5.7-10.4 tuan; K=20M -> 11-21 tuan (tinh tu 04/08)"],
    ["Terminus",              "on-chain balance near-zero HOAC capitulation HOAC Campaign 4 launch confirm"],
    ["Falsifiable",           "Ket thuc overhang = price sustained > 0.180 + vol > 30M/day + OI build > 6M trong 3d lien tiep"],
]

for i, row in enumerate(unlock_data, 1):
    for j, val in enumerate(row, 1):
        c = ws7.cell(i, j, val)
        if i == 1:
            c.fill = hdr_fill(); c.font = bold_white()
        elif row[0] and row[1] is not None:
            c.font = Font(bold=True if j==1 else False, size=10)
        else:
            c.font = norm()
    if i == 1:
        ws7.merge_cells(start_row=1, start_column=1, end_row=1, end_column=2)

# ── Save ───────────────────────────────────────────────────────────────────────
wb.save(OUT)
print(f"\nSaved: {OUT}")
print(f"Sheets: {wb.sheetnames}")
print(f"DAILY rows: {len(daily_rows)} (+ 2 header)")
