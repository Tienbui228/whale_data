"""Create CASE_TUT.xlsx - 7 sheets following CASE_BANK template."""
import subprocess
import urllib.request
import json
from datetime import datetime, timezone, date, timedelta
import openpyxl
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
from openpyxl.utils import get_column_letter

VPS = "root@5.223.67.21"
OUT = "docs/case_files/CASE_TUT.xlsx"

# ─── Colors ───────────────────────────────────────────────
BLUE_FILL   = PatternFill("solid", fgColor="4472C4")
LTBLUE_FILL = PatternFill("solid", fgColor="BDD7EE")
YELLOW_FILL = PatternFill("solid", fgColor="FFFF00")
RED_FILL    = PatternFill("solid", fgColor="FF0000")
ORANGE_FILL = PatternFill("solid", fgColor="FFC000")
GREEN_FILL  = PatternFill("solid", fgColor="E2EFDA")
GRAY_FILL   = PatternFill("solid", fgColor="D9D9D9")
WHITE_FILL  = PatternFill("solid", fgColor="FFFFFF")
WHT_FONT    = Font(color="FFFFFF", bold=True)
BLD_FONT    = Font(bold=True)

def ssh(cmd, timeout=30):
    r = subprocess.run(
        ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=10",
         VPS, cmd],
        capture_output=True, text=True, timeout=timeout
    )
    return r.stdout.strip()

import time

def fapi_get(url, timeout=15, retries=3):
    import ssl
    ctx = ssl.create_default_context()
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
                return json.loads(r.read())
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(2 + attempt * 2)
            else:
                raise
    raise RuntimeError("fapi_get exhausted retries")

# ─── Step 1: Collect freshwatch data from VPS ─────────────
print("[1] Loading freshwatch TUT data from VPS...")

def get_fw_rows(month_file):
    raw = ssh(f"grep 'TUTUSDT' /root/Data_back_test/whale_data/data/export/{month_file} 2>/dev/null")
    rows = []
    for line in raw.strip().split("\n"):
        if not line or "TUTUSDT" not in line:
            continue
        f = line.split(",")
        if len(f) < 17:
            continue
        rows.append(f)
    return rows

fw_rows_jun = get_fw_rows("freshwatch_daily_2026-06.csv")
fw_rows_jul = get_fw_rows("freshwatch_daily_2026-07.csv")
fw_rows_aug = get_fw_rows("freshwatch_daily_2026-08.csv")

all_fw = fw_rows_jun + fw_rows_jul + fw_rows_aug
print(f"  Jun: {len(fw_rows_jun)} rows, Jul: {len(fw_rows_jul)}, Aug: {len(fw_rows_aug)}")
print(f"  Total freshwatch: {len(all_fw)} rows")

# Build dict: date_str -> parsed values
fw_dict = {}
for f in all_fw:
    d = f[0]
    fw_dict[d] = {
        "px":       float(f[2]),
        "vol":      float(f[3]),
        "taker":    float(f[4]),
        "f_avg":    float(f[5]),
        "f_min":    float(f[6]),
        "f_max":    float(f[7]),
        "f_n":      int(f[8]),
        "oi":       float(f[9]),
        "pos_r":    float(f[10]),
        "acc_r":    float(f[11]),
        "gLSR":     float(f[12]),
        "tk_ratio": float(f[13]),
        "low_conf": f[14].strip().lower() == "true",
        "src":      f[15].strip(),
        "data_ok":  f[16].strip().lower() == "true",
    }

# ─── Step 2: Fetch fapi klines (01/05→26/06 pre-freshwatch + 24-26/07 gap) ──
print("[2] Fetching fapi klines 01/05->26/06 + gap 24-26/07...")

start_ts = int(datetime(2026, 5, 1, tzinfo=timezone.utc).timestamp() * 1000)
end_ts   = int(datetime(2026, 6, 27, tzinfo=timezone.utc).timestamp() * 1000)  # exclusive

klines_url = (f"https://fapi.binance.com/fapi/v1/klines?symbol=TUTUSDT"
              f"&interval=1d&startTime={start_ts}&endTime={end_ts}&limit=200")
klines_data = fapi_get(klines_url)
print(f"  Pre-freshwatch klines: {len(klines_data)} bars")

# Also get gap 24-26/07
time.sleep(1)
gap_start = int(datetime(2026, 7, 24, tzinfo=timezone.utc).timestamp() * 1000)
gap_end   = int(datetime(2026, 7, 27, tzinfo=timezone.utc).timestamp() * 1000)
try:
    gap_klines = fapi_get(f"https://fapi.binance.com/fapi/v1/klines?symbol=TUTUSDT"
                           f"&interval=1d&startTime={gap_start}&endTime={gap_end}&limit=10")
except Exception as e:
    print(f"  Gap klines error: {e} — will use klines_only/data_bad=1 for 24-26/07")
    gap_klines = []
print(f"  Gap klines (24-26/07): {len(gap_klines)} bars")

# Also get 05/08 real-time
time.sleep(1)
try:
    rt_klines = fapi_get("https://fapi.binance.com/fapi/v1/klines?symbol=TUTUSDT"
                          "&interval=1d&limit=2")
except Exception as e:
    print(f"  RT klines error: {e}")
    rt_klines = []
print(f"  Latest klines (for 05/08): {len(rt_klines)} bars")

def parse_kline(k):
    ts = int(k[0])
    d = datetime.fromtimestamp(ts/1000, tz=timezone.utc).strftime("%Y-%m-%d")
    px = float(k[4])
    vol = float(k[7])  # quote vol
    base_vol = float(k[5])
    taker_base = float(k[9])
    taker_pct = taker_base / base_vol if base_vol > 0 else None
    return d, px, vol, taker_pct

klines_dict = {}
for k in klines_data:
    d, px, vol, tk = parse_kline(k)
    klines_dict[d] = {"px": px, "vol": vol, "taker": tk}
for k in gap_klines:
    d, px, vol, tk = parse_kline(k)
    klines_dict[d] = {"px": px, "vol": vol, "taker": tk}
# Latest (05/08)
if rt_klines:
    d, px, vol, tk = parse_kline(rt_klines[-1])
    if d == "2026-08-05":
        klines_dict[d] = {"px": px, "vol": vol, "taker": tk}

# Also get real-time OI for 05/08
time.sleep(1)
try:
    oi_rt = fapi_get("https://fapi.binance.com/fapi/v1/openInterest?symbol=TUTUSDT")
except Exception as e:
    print(f"  OI RT error: {e}")
    oi_rt = None
oi_rt_val = None
if oi_rt and rt_klines:
    try:
        oi_rt_val = float(oi_rt["openInterest"]) * float(rt_klines[-1][4])
    except Exception:
        pass
print(f"  Real-time OI (05/08): ${oi_rt_val/1e6:.3f}M" if oi_rt_val else "  OI RT: N/A")

# ─── Step 3: Build date range 01/05 → 05/08 ──────────────
print("[3] Building date range...")
all_dates = []
d = date(2026, 5, 1)
end_d = date(2026, 8, 5)
while d <= end_d:
    all_dates.append(d.strftime("%Y-%m-%d"))
    d += timedelta(days=1)
print(f"  Total dates: {len(all_dates)}")

# B_T0 for OI clock
B_T0 = 1922202.30  # OI in USD at T0 (09/07)
T0_DATE = "2026-07-09"

# ─── Step 4: Build DAILY rows ─────────────────────────────
print("[4] Building DAILY rows...")

daily_rows = []
prev_px = None

for d_str in all_dates:
    in_fw = d_str in fw_dict
    in_kl = d_str in klines_dict

    if not in_fw and not in_kl:
        # No data at all - skip (don't create empty rows)
        continue

    if in_fw:
        fw = fw_dict[d_str]
        px = fw["px"]
        vol = fw["vol"]
        taker = fw["taker"]
        f_avg = fw["f_avg"]
        f_min = fw["f_min"]
        f_max = fw["f_max"]
        f_n = fw["f_n"]
        oi = fw["oi"]
        pos_r = fw["pos_r"]
        acc_r = fw["acc_r"]
        gLSR = fw["gLSR"]
        tk_ratio = fw["tk_ratio"]
        low_conf = fw["low_conf"]
        src = fw["src"]
        data_bad = None
        src_note = f"freshwatch/{src}"
    else:
        kl = klines_dict[d_str]
        px = kl["px"]
        vol = kl.get("vol")
        taker = kl.get("taker")
        f_avg = f_min = f_max = None
        f_n = None
        oi = None
        pos_r = acc_r = gLSR = tk_ratio = None
        low_conf = None
        src = "klines_only"
        data_bad = 1
        src_note = "fapi_klines_only"

    # Special: 05/08 partial day - add OI from real-time
    if d_str == "2026-08-05" and in_kl and not in_fw:
        oi = oi_rt_val
        src_note = "fapi_klines+oi_rt"

    # ret_1d
    ret = (px / prev_px - 1) if prev_px and px else None
    prev_px = px if px else prev_px

    # oi_delta and oi_delta_b
    oi_delta = None  # computed from context below
    oi_delta_b = (oi / B_T0) if oi else None  # ΔOI/B ratio

    # funding_regime
    if f_avg is not None:
        if f_avg <= 0:
            funding_regime = "NEGATIVE"
        elif abs(f_avg - 5e-5) < 1e-6:
            funding_regime = "PINNED"
        elif f_avg > 5e-5 * 3:
            funding_regime = "BURST"
        elif f_avg < 4e-5:
            funding_regime = "UNPIN_LOW"
        else:
            funding_regime = "NEAR_PIN"
    else:
        funding_regime = None

    # advisor_flag
    flag = None
    if pos_r is not None and pos_r <= 3.81:
        flag = "GHE_ROI"

    # Compute gLSR / lsr signal
    # campaign_phase based on date
    if d_str < "2026-05-03":
        cphase = "QUIET"
    elif d_str <= "2026-05-04":
        cphase = "C1_MARKUP"
    elif d_str <= "2026-05-28":
        cphase = "C1_FLUSH"
    elif d_str <= "2026-07-03":
        cphase = "BAIT_CONSOLIDATION"
    elif d_str <= "2026-07-08":
        cphase = "PRE_IGNITION"
    elif d_str == T0_DATE:
        cphase = "IGNITION_T0"
    elif d_str <= "2026-07-11":
        cphase = "C3_RAMP"
    elif d_str == "2026-07-12":
        cphase = "C3_LOCAL_TOP1+WASH"
    elif d_str <= "2026-07-22":
        cphase = "C3_GRIND"
    elif d_str <= "2026-07-29":
        cphase = "C3_COOLDOWN"
    else:
        cphase = "C3_ACCELERATION"

    # 41 columns matching CASE_BANK structure:
    # PERP: date px_avg ret_1d vol_perp_usd taker_buy_pct f_avg f_min f_max f_n
    #       funding_regime pin_streak oi_usd oi_vs_med14 oi_cycle_pos
    #       lsr_pos_r lsr_acc_r lsr_global_r div_raw div_avg3 glsr_slope_5d
    #       d_pos_3d d_acc_3d signals_bullish signals_suppress screen_rank data_bad
    # SPOT: spot_venue vol_spot_usd taker_spot_pct depth_bid2_usd depth_ask2_usd
    #       bid_wall_px bid_wall_usd ask_wall_px ask_wall_usd alpha_suspect
    # ON-CHAIN: exch_balance_delta wallet_activity dominance_pct
    # MANUAL: note_operator mm_note

    row = [
        d_str,           # date
        px,              # px_avg
        ret,             # ret_1d
        vol,             # vol_perp_usd
        taker,           # taker_buy_pct
        f_avg,           # f_avg
        f_min,           # f_min
        f_max,           # f_max
        f_n,             # f_n
        funding_regime,  # funding_regime
        None,            # pin_streak (compute later or leave)
        oi,              # oi_usd
        None,            # oi_vs_med14 (ABSTAIN)
        oi_delta_b,      # oi_cycle_pos → reuse for ΔOI/B
        pos_r,           # lsr_pos_r
        acc_r,           # lsr_acc_r
        gLSR,            # lsr_global_r
        None,            # div_raw (ABSTAIN)
        None,            # div_avg3
        None,            # glsr_slope_5d
        None,            # d_pos_3d
        None,            # d_acc_3d
        None,            # signals_bullish
        None,            # signals_suppress
        cphase,          # screen_rank → reuse for campaign_phase
        data_bad,        # data_bad
        "BSC_DEX_WBNB",  # spot_venue
        None,            # vol_spot_usd (ABSTAIN — BSC DEX not collected)
        None,            # taker_spot_pct
        None,            # depth_bid2_usd
        None,            # depth_ask2_usd
        None,            # bid_wall_px
        None,            # bid_wall_usd
        None,            # ask_wall_px
        None,            # ask_wall_usd
        None,            # alpha_suspect (TUT not in Alpha store)
        None,            # exch_balance_delta (PENDING OPERATOR)
        None,            # wallet_activity (PENDING OPERATOR)
        None,            # dominance_pct
        flag,            # note_operator → advisor flag
        src_note,        # mm_note → src_note
    ]
    daily_rows.append(row)

print(f"  Built {len(daily_rows)} DAILY rows")

# ─── Step 5: Create XLSX ──────────────────────────────────
print("[5] Creating XLSX...")
wb = openpyxl.Workbook()

# ── CASE sheet ──────────────────────────────────────────────
ws_case = wb.active
ws_case.title = "CASE"
ws_case.column_dimensions["A"].width = 32
ws_case.column_dimensions["B"].width = 50

case_data = [
    ("CASE FILE — TUT", None),
    ("Nguon: case_tracker | verdict chi operator ghi | so kem nguon | PENDING khong doan", None),
    (None, None),
    ("A. THONG TIN CO BAN", None),
    ("token", "TUT"),
    ("full_name", "TUT (BSC meme) — unknown issuer"),
    ("venue_perp", "Binance TUTUSDT"),
    ("venue_spot", "BSC DEX TUT/WBNB 1% (0x6dafbf), khong co Binance spot"),
    ("archetype", "LOAI_C_MEME — meme, khong vesting, MM tu mua spot (operator confirm 05/08)"),
    ("state", "TRACKING_WITH_POSITION — operator giu vi the, chot canh = exit flags"),
    ("thesis_1line", "Loai C: tu mua kho spot BSC, ban theo ke hoach khi hype du qua perp (campaign)"),
    (None, None),
    ("B. TIMELINE CHIEN DICH", None),
    ("T0_ignition", "2026-07-09"),
    ("T0_px", 0.01062),
    ("T0_oi_usd", 1922202.30),
    ("C1_markup_date", "2026-05-03/04 (probe, H=0.01450, px_mult=1.37x)"),
    ("bait_date", "2026-06-04/07 (pump-dump, KHONG phai campaign)"),
    ("C3_start", "2026-07-09 (MAIN — dang chay)"),
    ("advisor_exit_ref", 0.01986),
    ("scorecard_ref", "exit scorecard 2 lop dang chay (session 04/08)"),
    (None, None),
    ("C. KEY METRICS (tai T0 va hom nay)", None),
    ("build_VWAP_total", 0.01079),
    ("build_VWAP_note", "blend 30/50/20 Window A/B/C (perp proxy, spot PENDING operator)"),
    ("B_T0_oi_usd", 1922202.30),
    ("OI_latest_usd", 7138000.0),
    ("OI_note", "fapi real-time 05/08 03:41 UTC"),
    ("delta_OI_over_B", "7.138M/1.922M = 3.71x (real-time 05/08)"),
    ("gLSR_trend", "3.115 -> 1.438 (declining: crowd adding shorts, MM harvesting)"),
    ("pos_r_peak14d", 5.083),
    ("pos_r_peak14d_note", "23/07, window 21/07-04/08"),
    ("COR_GHE_ROI_threshold", 3.81),
    ("COR_GHE_ROI_status", "FIRED 02/08 (pos_r=3.4581), bounce 03/08, confirmed 04/08 (pos_r=2.8299)"),
    (None, None),
    ("D. PENDING OPERATOR", None),
    ("O1_total_supply", "PENDING — can de tinh K_spot"),
    ("O2_cost_basis_spot", "PENDING — BscScan/Nansen, cluster vi gom"),
    ("O3_exchange_balance_1y", "PENDING — Nansen LOCKED, operator feed"),
]

for i, (k, v) in enumerate(case_data, 1):
    ws_case.cell(i, 1, k)
    ws_case.cell(i, 2, v)
    if i == 1:
        ws_case.cell(i, 1).font = Font(bold=True, size=13)
        ws_case.cell(i, 1).fill = BLUE_FILL
        ws_case.cell(i, 1).font = Font(bold=True, size=13, color="FFFFFF")
    elif v is None and k and k.startswith(("A.", "B.", "C.", "D.")):
        ws_case.cell(i, 1).fill = LTBLUE_FILL
        ws_case.cell(i, 1).font = BLD_FONT

# ── DAILY sheet ──────────────────────────────────────────────
ws_daily = wb.create_sheet("DAILY")

# Row 1: section headers
PERP_COLS = 26
SPOT_COLS = 10
OC_COLS = 3
MAN_COLS = 2
TOTAL_COLS = PERP_COLS + SPOT_COLS + OC_COLS + MAN_COLS  # 41

sections = [
    (1, PERP_COLS, "PERP (may)"),
    (PERP_COLS+1, PERP_COLS+SPOT_COLS, "SPOT/ALPHA (may)"),
    (PERP_COLS+SPOT_COLS+1, PERP_COLS+SPOT_COLS+OC_COLS, "ON-CHAIN (ban tu dong)"),
    (PERP_COLS+SPOT_COLS+OC_COLS+1, TOTAL_COLS, "MANUAL (operator)"),
]
for c_start, c_end, label in sections:
    ws_daily.cell(1, c_start, label)
    ws_daily.cell(1, c_start).fill = BLUE_FILL
    ws_daily.cell(1, c_start).font = WHT_FONT
    if c_end > c_start:
        ws_daily.merge_cells(start_row=1, start_column=c_start,
                             end_row=1, end_column=c_end)

# Row 2: column headers
col_headers = [
    "date","px_avg","ret_1d","vol_perp_usd","taker_buy_pct",
    "f_avg","f_min","f_max","f_n","funding_regime","pin_streak",
    "oi_usd","oi_vs_med14","oi_cycle_pos",
    "lsr_pos_r","lsr_acc_r","lsr_global_r","div_raw","div_avg3",
    "glsr_slope_5d","d_pos_3d","d_acc_3d",
    "signals_bullish","signals_suppress","screen_rank","data_bad",
    "spot_venue","vol_spot_usd","taker_spot_pct",
    "depth_bid2_usd","depth_ask2_usd","bid_wall_px","bid_wall_usd",
    "ask_wall_px","ask_wall_usd","alpha_suspect",
    "exch_balance_delta","wallet_activity","dominance_pct",
    "note_operator","mm_note",
]
assert len(col_headers) == TOTAL_COLS, f"col count mismatch: {len(col_headers)} vs {TOTAL_COLS}"

for c, h in enumerate(col_headers, 1):
    cell = ws_daily.cell(2, c, h)
    cell.fill = LTBLUE_FILL
    cell.font = BLD_FONT

# Widen key columns
for c, w in [(1,12),(2,10),(3,8),(4,13),(5,10),(6,10),(12,12),(15,10),(17,10),(26,10),(41,18)]:
    ws_daily.column_dimensions[get_column_letter(c)].width = w

# Data rows
for r_idx, row in enumerate(daily_rows, 3):
    for c_idx, val in enumerate(row, 1):
        cell = ws_daily.cell(r_idx, c_idx, val)
        # Format percentages
        if c_idx in (3, 5) and val is not None:
            cell.number_format = "0.00%"
        if c_idx in (6, 7, 8) and val is not None:
            cell.number_format = "0.000000"
        if c_idx == 2 and val is not None:
            cell.number_format = "0.00000"

    d_str = row[0]
    data_bad = row[25]
    pos_r_val = row[14]
    flag = row[39]  # note_operator (advisor flag)

    # Yellow = data_bad=1
    if data_bad == 1:
        for c in range(1, TOTAL_COLS+1):
            ws_daily.cell(r_idx, c).fill = YELLOW_FILL

    # Red pos_r cells where flag fired
    if flag == "GHE_ROI":
        ws_daily.cell(r_idx, 14).fill = RED_FILL  # lsr_pos_r
        ws_daily.cell(r_idx, 39).fill = RED_FILL  # note_operator
        ws_daily.cell(r_idx, 39).font = WHT_FONT

    # Highlight T0 row
    if d_str == T0_DATE:
        ws_daily.cell(r_idx, 1).fill = GREEN_FILL
        ws_daily.cell(r_idx, 1).font = BLD_FONT

print(f"  DAILY sheet: {len(daily_rows)} data rows, {TOTAL_COLS} columns")

# ── EVENTS sheet ──────────────────────────────────────────────
ws_ev = wb.create_sheet("EVENTS")
ws_ev.cell(1, 1, "D. NHAT KY DIEN BIEN (append-only, moi nhat duoi cung)")
ws_ev.cell(1, 1).fill = BLUE_FILL
ws_ev.cell(1, 1).font = WHT_FONT
ws_ev.merge_cells("A1:D1")
ws_ev.append([None])
ws_ev.append(["ngay", "su_kien_so_lieu", "nguon", "doc_nhanh"])
for c in range(1, 5):
    ws_ev.cell(3, c).fill = LTBLUE_FILL
    ws_ev.cell(3, c).font = BLD_FONT
ws_ev.column_dimensions["A"].width = 14
ws_ev.column_dimensions["B"].width = 60
ws_ev.column_dimensions["C"].width = 18
ws_ev.column_dimensions["D"].width = 30

events = [
    ("2026-05-01", "LISTEN/QUIET phase bat dau. px~0.01062, vol 0.75M USDT", "fapi_klines", "Flat, vol cuc thap"),
    ("2026-05-03/04", "CHUONG 1 MARKUP: px 0.01063->H=0.01450 (+36%), vol 11.5M+29.7M. Funding PINNED.", "fapi_klines", "Debut probe campaign, bien do nho"),
    ("2026-05-05/09", "Controlled fill post-C1: vol 10.52M+5.24M+4.23M, taker 47.8% avg. Floor hap thu tai 0.01267.", "fapi_klines", "Loai C pattern: mua sau markup"),
    ("2026-06-04/07", "BAIT/TEST: pump +50% (04-05/06), dump -6.5% (07/06). Gia khong vuot C1 high. Khong phai campaign.", "fapi_klines", "Bait flush - khong sustain"),
    ("2026-06-27", "Freshwatch bat dau cover TUTUSDT. OI=2.352M, gLSR=3.115 (crowd cuc long), pos_r=4.367", "freshwatch", "OI da ton tai truoc coverage - tich luy trang 5-6 khong verify duoc"),
    ("2026-07-08", "OI dip ve local low 2.020M - pre-ignition trough. px=0.00965 (day gap nhat trong chuoi)", "freshwatch", "Tich luy truoc ignition"),
    ("2026-07-09", "IGNITION (T0): px 0.01062->0.01276 (+20%), vol spike 9.4M, OI 1.922M. gLSR=2.997", "freshwatch", "T0 confirmed - bat dau C3 MAIN"),
    ("2026-07-12", "LOCAL TOP 1 + SHORT-WASH: px RED -4.1%, OI NHAY +0.669M (+26%), gLSR SOP 2.18->1.195. Crowd shorts flood in.", "freshwatch", "SHORT-WASH cau truc - fuel reload cho squeeze"),
    ("2026-07-15", "pos_r dinh tuyet doi: 5.8117 (14/07: 5.4747, 15/07: 5.8117, 16/07: 5.7058). OI=2.708M", "freshwatch", "Peak crowd-long period"),
    ("2026-07-22", "LOCAL TOP 2: px RED -9%, OI +0.351M, gLSR=1.779. MM gom them vao dump.", "freshwatch", "Gom vao local top 2"),
    ("2026-07-23", "pos_r=5.083: DINH rolling-peak-14d cho tinh nguong CO GHE-ROI. OI=3.387M", "freshwatch", "Reference peak cho trigger #1"),
    ("2026-07-24/26", "GAP DATA (freshwatch gap). Klines only, OI/LSR ABSTAIN.", "fapi_klines", "data_bad=1"),
    ("2026-07-27/29", "LOCAL DUMP: px 0.01622->0.01439 (-11.3%). OI xay tiep: 4.202M", "freshwatch", "Cooldown sau local top 2"),
    ("2026-08-01", "ACCELERATION bat dau: vol 9.82M (spike), OI +0.395M. pos_r=4.169, gLSR=2.031", "freshwatch", "Vol surge signal bat dau tang toc"),
    ("2026-08-02", "CO GHE-ROI LAN 1: pos_r=3.4581 <= 3.81 (25% drop tu peak 5.083). px=0.01741. OI=4.997M", "freshwatch", "!!! EXIT TRIGGER FIRE - lan 1 (bounce lai 03/08)"),
    ("2026-08-03", "pos_r bounce 4.014 (tren nguong 3.81 - flag reset?). Vol DINH 17.95M. OI=4.831M", "freshwatch", "Bounce bat thuong - theo doi"),
    ("2026-08-04", "CO GHE-ROI CONFIRMED fn=6: pos_r=2.8299 (44.3% drop). OI=5.672M. f_avg=4.26e-05 (nhe lo ghim)", "freshwatch", "!!! TRIGGER CONFIRMED sustained - exit window"),
    ("2026-08-05", "OI ATH: 7.138M (fapi real-time 03:41 UTC). px~0.02391. Freshwatch 05/08 chua co (export 01:20 UTC)", "fapi_rt", "OI tiep tuc build sau trigger"),
    ("2026-08-05", "pos_r 05/08 verify: PENDING freshwatch (export 01:20 UTC - qua som cho fn=6)", "pending", "Can kiem tra next export"),
]

for ev in events:
    ws_ev.append(ev)

# ── TRIGGERS sheet ──────────────────────────────────────────────
ws_tr = wb.create_sheet("TRIGGERS")
ws_tr.cell(1, 1, "C. CHOT THEO DOI — doc moi ngay sau nen dong")
ws_tr.cell(1, 1).fill = BLUE_FILL
ws_tr.cell(1, 1).font = WHT_FONT
ws_tr.merge_cells("A1:E1")
ws_tr.append([None])
ws_tr.append(["#", "chot", "dieu_kien", "nghia_khi_bat", "trang_thai_hom_nay"])
for c in range(1, 6):
    ws_tr.cell(3, c).fill = LTBLUE_FILL
    ws_tr.cell(3, c).font = BLD_FONT
ws_tr.column_dimensions["B"].width = 25
ws_tr.column_dimensions["C"].width = 35
ws_tr.column_dimensions["D"].width = 35
ws_tr.column_dimensions["E"].width = 40

triggers = [
    (1, "COR GHE-ROI", "pos_r <= 3.81 (25% drop tu peak 14d = 5.083, nguong = 5.083*0.75 = 3.81)",
     "Crowd long bat dau thoat (ghe roi): MM co the exit perp vao crowd shorts. EXIT SIGNAL.",
     "FIRED 02/08 (3.4581), bounce 03/08 (4.014), CONFIRMED 04/08 (2.8299 fn=6). px_trigger=0.02249"),
    (2, "FUNDING VO GHIM", "f_avg outside [4e-5, 6e-5] — sustained (>=2 periods lien tiep)",
     "Crowd overheating (burst) = exit sau burst; pin sup (negative) = stress signal.",
     "WATCH — 04/08 f_avg=4.26e-05 (borderline, 1 ky nhe lo). f_min=1.22e-05 (1 tick). Chua sustain."),
    (3, "NGAN DO LON", "Nen do >= -8%, vol > 5x median (median ~1.8M USDT)", "Luc ban manh: OI giam kem = MM exit; OI tang = wash va tiep tuc.",
     "WATCH — 03/08 gLSR declining nhung nen xanh. Chua co nen do >= -8% vol lon trong C3."),
    (4, "gLSR FLUSH <= 1.1", "gLSR <= 1.1 tren bat ky ngay nao (KHONG phai exit — nap dan)",
     "SHORT-WASH: crowd short flood in, MM se squeeze. Chieu NGUOC voi exit. Theo doi 1-3 ngay tiep.",
     "WATCH — gLSR dang giam tu 3.115->1.438. Chua ve 1.1. 12/07 da thap nhat 1.195 (gần)."),
    (5, "OI-CLOCK", "DeltaOI/B vs band [x1, x3, x5, x7]. TUT la diem calib dau tien (n=0 prior data)",
     "Pha OI: build (<3x), peak (3-5x), exit (>5x). Band Loai C CHUA CALIBRATE.",
     "HIEN TAI: 3.71x (05/08 fapi). Target: 5x=9.61M; 7x=13.45M. Toc do ~0.5M/day. Loai C n=0."),
]
for tr in triggers:
    ws_tr.append(tr)
# Color row of FIRED trigger
for r in range(4, 4+len(triggers)):
    if "FIRED" in str(ws_tr.cell(r, 5).value) or "CONFIRMED" in str(ws_tr.cell(r, 5).value or ""):
        ws_tr.cell(r, 1).fill = RED_FILL

# ── OUTCOME sheet ──────────────────────────────────────────────
ws_oc = wb.create_sheet("OUTCOME")
ws_oc.cell(1, 1, "E. OUTCOME — dien tai moc; advisor_vs_thesis: chot canh dung/sai o diem nao")
ws_oc.cell(1, 1).fill = BLUE_FILL
ws_oc.cell(1, 1).font = WHT_FONT
ws_oc.merge_cells("A1:I1")
ws_oc.append([None])
ws_oc.append(["moc", "ngay_han", "px", "ret_pct", "drawup_drawdown", "oi_usd", "gLSR", "dien_bien", "advisor_vs_thesis"])
for c in range(1, 10):
    ws_oc.cell(3, c).fill = LTBLUE_FILL
    ws_oc.cell(3, c).font = BLD_FONT
ws_oc.column_dimensions["A"].width = 12
ws_oc.column_dimensions["B"].width = 14
ws_oc.column_dimensions["H"].width = 40
ws_oc.column_dimensions["I"].width = 40

outcomes = [
    ("T0", "2026-07-09", 0.01062, None, None, 1922202.30, 2.997, "IGNITION confirmed, gLSR=2.997", "Thesis: Loai C, C3 MAIN bat dau"),
    ("T+7", "2026-07-16", 0.01287, "+21.2%", None, 2893354.0, 1.990, "Grind up, gLSR declining. OI+0.971M tu T0", "TRACKING — build pha dang chay"),
    ("T+14", "2026-07-23", 0.01387, "+30.6%", "max=+32% (22/07 local top)", 3387147.0, 1.729, "Post local-top 2. pos_r=5.083 (DINH)", "TRACKING — pos_r dinh, sap vo ghim"),
    ("T+30", "2026-08-08", None, None, None, None, None, "PENDING — 3 ngay nua", "Verify: CO GHE-ROI da ban truoc T+30?"),
    ("T+60", "2026-09-07", None, None, None, None, None, "PENDING", "Verify: campaign ket thuc chua?"),
    ("exit_tell", None, 0.01986, None, None, None, None, "advisor_exit_ref (scorecard 2 lop)", "Nguong exit: px=0.01986 hoac trigger bat"),
    ("CO_GHE_ROI", "2026-08-02", 0.01741, None, None, 4997475.0, 1.7211, "FIRE LAN 1 (bounce 03/08). Confirmed 04/08 px=0.02249", "Exit signal da bat. Operator can ky verdict."),
]
for oc in outcomes:
    ws_oc.append(oc)

# ── MM_PROFILE sheet ──────────────────────────────────────────────
ws_mm = wb.create_sheet("MM_PROFILE")
ws_mm.cell(1, 1, "I. MM / OPERATOR PROFILE — van tay hanh vi (moi MM danh mot kieu)")
ws_mm.cell(1, 1).fill = BLUE_FILL
ws_mm.cell(1, 1).font = WHT_FONT
ws_mm.merge_cells("A1:B1")
ws_mm.column_dimensions["A"].width = 30
ws_mm.column_dimensions["B"].width = 70
ws_mm.append([None])

mm_data = [
    ("MM cong bo / nghi van", "unknown-TUT — chua tra ho so (operator confirm Loai C 05/08)"),
    ("Archetype", "LOAI_C_MEME — meme BSC, MM tu mua kho spot, ban theo ke hoach"),
    ("Ghi chep nay la case TUT", "(C-vo-A-ruot: spot phuc vu campaign perp, khac CLO o cho TUT khong co Binance listing)"),
    (None, None),
    ("VAN TAY XAC NHAN", None),
    ("self_pinned_funding", "0.00005 x 97 ngay (01/05->05/08), XUYEN QUA +149% markup — KHONG CO TOKEN NAO KHAC LAM DUOC"),
    ("bid_walk_taker", "taker 44-53% (trong window quiet: khong co spike)"),
    ("wash_by_rally", "12/07: SHORT-WASH — gLSR 2.18->1.195 tren NEN DO + OI +0.669M. Crowd short, MM squeeze tiep"),
    ("gLSR_trajectory", "3.115 -> 1.438 (declining xuyen OI build: crowd them short, MM dong long vao short = harvest)"),
    ("oi_controlled_build", "OI tang deu tren ca nen xanh lan nen do — khong co dau hieu crowd buying (taker <53%)"),
    (None, None),
    ("CHUA XAC NHAN", None),
    ("serial_pattern", "unknown-TUT — C1 probe (03/05) + bait (06/06) + C3 MAIN. Khong du diem de classify serial"),
    ("spot_accumulation_timing", "PENDING — co so BSC but not quantified (on-chain PENDING OPERATOR)"),
    ("cooperation_exchanges", "PENDING — only Binance perp confirmed, BSC DEX = spot venue"),
]
for k, v in mm_data:
    ws_mm.append([k, v])
    if k and "VAN TAY" in k or k and "CHUA" in k:
        r = ws_mm.max_row
        ws_mm.cell(r, 1).fill = LTBLUE_FILL
        ws_mm.cell(r, 1).font = BLD_FONT

# ── UNLOCK sheet ──────────────────────────────────────────────
ws_ul = wb.create_sheet("UNLOCK")
ws_ul.cell(1, 1, "J. TOKENOMICS / UNLOCK — dong cung co lich, MM danh quanh no")
ws_ul.cell(1, 1).fill = BLUE_FILL
ws_ul.cell(1, 1).font = WHT_FONT
ws_ul.merge_cells("A1:B1")
ws_ul.column_dimensions["A"].width = 30
ws_ul.column_dimensions["B"].width = 70
ws_ul.append([None])

ul_data = [
    ("Circulating / Total", "N/A — meme token, khong co vesting schedule"),
    ("L-12 (mien kiem tra unlock)", "THOA bang vang mat co bang chung: KHONG co TGE doc, KHONG co cliff/vesting, KHONG co PENDING unlock nao trong lich su"),
    ("mu-unlock", "KHONG AP DUNG — Loai C per L-4x: MM la nguoi mua tu do tren thi truong (khong phai insider ban)"),
    ("Total supply", "PENDING OPERATOR — can de tinh K_spot (O1)"),
    ("K_spot estimate", "PENDING — phu thuoc total supply va on-chain balance"),
    ("Ghi chu", "Khac voi BANK/TAG/CLO o cho: KHONG co vesting, khong co nguon phan phoi co ke hoach. Cung = market float."),
    (None, None),
    ("DONG CUNG (historical)", None),
    ("05/2026", "Khong ro — khong co data on-chain"),
    ("BSC DEX liq snapshot 05/08", "$2.37M (TUT/WBNB 1%) + $23K (TUT/USDT 0.25%)"),
    ("Binance Alpha (ALPHA_117)", "KHONG CO PARQUET — spot vol BSC DEX la venue chinh"),
]
for k, v in ul_data:
    ws_ul.append([k, v])

# ── Save ──────────────────────────────────────────────────────
wb.save(OUT)
print(f"\n[DONE] Saved to {OUT}")
print(f"  Sheets: {[s.title for s in wb.worksheets]}")
print(f"  DAILY rows: {len(daily_rows)} (pre-fw: {sum(1 for r in daily_rows if r[25]==1)}, fw: {sum(1 for r in daily_rows if r[25] is None)})")
print(f"  EVENTS: {len(events)}")
print(f"  TRIGGERS: {len(triggers)}")
print(f"  OUTCOME: {len(outcomes)}")
