# -*- coding: utf-8 -*-
"""
Append IDOL 03-05/08 to CASE_IDOL DAILY + EVENTS 58bro new data.
Freshwatch 03-04/08 from VPS; 05/08 = data_bad=1 (fapi partial 07:17 UTC).
CASE_IDOL has 43 cols (extra: vol_alpha_usd=42, n_trades_alpha=43).
taker stored as percentage form (x100) per existing CASE_IDOL convention.
"""
import openpyxl
from openpyxl.styles import PatternFill

CASE_PATH = "docs/case_files/CASE_IDOL.xlsx"

# Freshwatch 03-04/08 + fapi 05/08
# taker_stored = freshwatch_taker * 100 (per CASE_IDOL format)
ROWS = [
    {
        "date": "2026-08-03",
        "px": 0.018868, "vol": 33874473, "taker": 44.555,
        "f_avg": 7.166e-5, "f_min": 5e-5, "f_max": 1.7046e-4, "f_n": 6,
        "funding_regime": "partial_pin", "pin_streak": 0,
        "oi": 9503666, "pos_r": 1.8049, "acc_r": 1.6539, "glsr": 1.6364,
        "data_bad": 0,
    },
    {
        "date": "2026-08-04",
        "px": 0.016356, "vol": 17027386, "taker": 47.177,
        "f_avg": 2.382e-4, "f_min": 5e-5, "f_max": 6.7558e-4, "f_n": 6,
        "funding_regime": "spike", "pin_streak": 0,
        "oi": 8825999, "pos_r": 1.7453, "acc_r": 1.6274, "glsr": 1.4612,
        "data_bad": 0,
    },
    {
        "date": "2026-08-05",
        "px": 0.016080, "vol": 3100000, "taker": 40.20,  # fapi partial
        "f_avg": None, "f_min": None, "f_max": None, "f_n": None,
        "funding_regime": "near_zero", "pin_streak": 0,
        "oi": 8866000, "pos_r": 1.841, "acc_r": 1.322, "glsr": 1.236,
        "data_bad": 1,
    },
]

YELLOW = PatternFill("solid", fgColor="FFFF00")

wb = openpyxl.load_workbook(CASE_PATH)
ws = wb["DAILY"]

# Max_row in DAILY
max_r = ws.max_row
print(f"DAILY max_row before: {max_r}")

# Get prev_px for ret_1d computation
prev_px = None
for row in ws.iter_rows(min_row=3, values_only=True):
    if row[0] and row[1]:
        try:
            prev_px = float(row[1])
        except: pass

print(f"prev_px (last row): {prev_px}")

for fw in ROWS:
    new_r = max_r + 1
    px = fw["px"]
    ret_1d = (px / prev_px - 1) if prev_px and prev_px > 0 else None

    # Build 43-col row
    row_data = [None] * 43
    row_data[0]  = fw["date"]           # date
    row_data[1]  = px                   # px_avg
    row_data[2]  = ret_1d              # ret_1d (numeric)
    row_data[3]  = fw["vol"]           # vol_perp_usd
    row_data[4]  = fw["taker"]        # taker_buy_pct (×100 form)
    row_data[5]  = fw["f_avg"]        # f_avg
    row_data[6]  = fw["f_min"]        # f_min
    row_data[7]  = fw["f_max"]        # f_max
    row_data[8]  = fw["f_n"]          # f_n
    row_data[9]  = fw["funding_regime"] # funding_regime
    row_data[10] = fw["pin_streak"]   # pin_streak
    row_data[11] = fw["oi"]           # oi_usd
    # oi_vs_med14 (col 13): computed from OI/median14d — skip, formula in formula rows
    row_data[13] = None               # oi_vs_med14
    row_data[14] = fw["pos_r"]        # lsr_pos_r
    row_data[15] = fw["acc_r"]        # lsr_acc_r
    row_data[16] = fw["glsr"]         # lsr_global_r
    # div_raw = pos_r/acc_r
    if fw["pos_r"] and fw["acc_r"] and fw["acc_r"] > 0:
        row_data[17] = fw["pos_r"] / fw["acc_r"]
    row_data[25] = fw["data_bad"]     # data_bad
    # cols 26-41: PENDING (spot, onchain, manual)
    # cols 41-42: vol_alpha, n_trades_alpha: PENDING

    # Write to DAILY sheet
    for col_i, val in enumerate(row_data, start=1):
        c = ws.cell(row=new_r, column=col_i)
        c.value = val
        # Apply formats matching existing rows
        if col_i == 1: c.number_format = "yyyy\\-mm\\-dd"
        elif col_i == 2: c.number_format = "0.00000000"
        elif col_i == 3: c.number_format = "0.0000"
        elif col_i == 4: c.number_format = "0.0"
        elif col_i in (6, 7, 8): c.number_format = "0.000000"
        elif col_i == 9: c.number_format = "0"
        elif col_i in (12,): c.number_format = "#,##0"
        elif col_i in (15, 16, 17): c.number_format = "0.0000"
        elif col_i == 18: c.number_format = "0.000"

    if fw["data_bad"]:
        for col_i in range(1, 44):
            ws.cell(row=new_r, column=col_i).fill = YELLOW

    print(f"  Appended row {new_r}: {fw['date']} px={px:.5f} "
          f"pos_r={fw['pos_r']} gLSR={fw['glsr']} data_bad={fw['data_bad']}")
    prev_px = px
    max_r = new_r

# ── EVENTS: append 58bro new rows ────────────────────────────────
print("\nUpdating EVENTS sheet...")
ws_e = wb["EVENTS"]
max_e = ws_e.max_row

events_new = [
    ["2026-08-04",
     "58bro: nhan 27.06M tokens -> NAP LAI 27.06M cung ngay (roundtrip net=0). "
     "Cung ngay nhan them 10M + 14.3M = 24.3M (giu lai, chua nap)",
     "operator_screenshot_20260806",
     "[THONG DIEP?] Gate->vi->Gate roundtrip 27.06M = ao cu Loai A; "
     "net giu: 24.3M — pending verify co nap tiep khong"],
    ["2026-08-06",
     "58bro: nhan 8.14M tokens (giu lai, chua nap theo screenshot)",
     "operator_screenshot_20260806",
     "Tong net moi giu (04-06/08): 10M+14.3M+8.14M=32.44M — "
     "pending balance check sau 06/08"],
    ["2026-08-06",
     "Y4 PENDING: dia chi vi smart-money operator thay dang gom — "
     "can doi chieu cum 13 vi staging + 58bro + Gate 0x0d0707",
     "CAN_OPERATOR",
     "Loai A confirmed: moi on-chain tu he vi cu = THONG DIEP; "
     "chi vi ngoai he + swap DEX thuc moi dem"],
]

for ev in events_new:
    new_e_r = max_e + 1
    for col_i, val in enumerate(ev, start=1):
        ws_e.cell(row=new_e_r, column=col_i).value = val
    max_e = new_e_r
    print(f"  EVENTS row {new_e_r}: {ev[0]} | {ev[1][:50]}...")

wb.save(CASE_PATH)
print(f"\nDONE. Saved: {CASE_PATH}")
