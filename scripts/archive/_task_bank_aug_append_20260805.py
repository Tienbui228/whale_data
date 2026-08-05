# -*- coding: utf-8 -*-
"""
Append BANK 01-05/08 to CASE_BANK DAILY + fill OUTCOME T+30.
Freshwatch 01-04/08 from VPS. 05/08 = data_bad=1 (fapi partial).
"""
import openpyxl
from openpyxl.styles import PatternFill
from datetime import datetime

CASE_PATH = "docs/case_files/CASE_BANK.xlsx"

# ── Freshwatch 01-04/08 (từ VPS export) ─────────────────────────
# cols: date, px_avg, vol_quote, taker_buy_pct, f_avg, f_min, f_max, f_n,
#       oi_usd, lsr_pos_r, lsr_acc_r, lsr_global_r
FW = {
    "2026-08-01": dict(
        px=0.056915, vol=253304478, taker=0.4804, f_avg=-0.000806, f_min=-0.002363,
        f_max=-0.000139, f_n=24, oi=18027284, pos_r=1.1805, acc_r=2.0276, glsr=1.7996,
        data_bad=0),
    "2026-08-02": dict(
        px=0.047883, vol=172554826, taker=0.4791, f_avg=-0.000349, f_min=-0.000722,
        f_max=-0.0000966, f_n=24, oi=17469390, pos_r=1.3197, acc_r=2.2658, glsr=1.8843,
        data_bad=0),
    "2026-08-03": dict(
        px=0.043163, vol=143022585, taker=0.4883, f_avg=-0.000186, f_min=-0.000821,
        f_max=0.0000035, f_n=24, oi=17252550, pos_r=1.3123, acc_r=2.1466, glsr=1.7263,
        data_bad=0),
    "2026-08-04": dict(
        px=0.051353, vol=471564742, taker=0.4906, f_avg=-0.000548, f_min=-0.002347,
        f_max=0.0000125, f_n=24, oi=17356910, pos_r=1.3135, acc_r=2.0460, glsr=1.6490,
        data_bad=0),
    # 05/08: fapi partial (07:03 UTC), data_bad=1
    "2026-08-05": dict(
        px=0.05190, vol=102200000, taker=0.4860, f_avg=None, f_min=None,
        f_max=None, f_n=None, oi=18070000, pos_r=1.1990, acc_r=None, glsr=1.3960,
        data_bad=1),
}

# Spot data from probe (W2 hardcoded)
SPOT = {
    "2026-08-01": (19910000, 0.462),
    "2026-08-02": (12180000, 0.493),
    "2026-08-03": (12350000, 0.481),
    "2026-08-04": (46830000, 0.483),
    "2026-08-05": (6860000, 0.473),
}

# Funding regimes (negative batch = crowd shorts paying longs)
REGIME = {
    "2026-08-01": "neg_batch",
    "2026-08-02": "neg_light",
    "2026-08-03": "neg_light",
    "2026-08-04": "neg_batch",
    "2026-08-05": "near_zero",
}

YELLOW = PatternFill("solid", fgColor="FFFF00")

wb = openpyxl.load_workbook(CASE_PATH)
ws = wb["DAILY"]

# Find last row with data
last_row = 2  # header row
for row in ws.iter_rows(min_row=3, values_only=True):
    if row[0]:
        last_row += 1

print(f"Last populated row: {last_row}")

# Get previous px for ret_1d calculation
prev_px_cell = ws.cell(row=last_row, column=2).value
prev_px = float(prev_px_cell) if prev_px_cell else None

for d_str in sorted(FW.keys()):
    fw = FW[d_str]
    sp_vol, sp_tak = SPOT.get(d_str, (None, None))
    regime = REGIME.get(d_str, "")

    px = fw["px"]
    ret_1d = (px / prev_px - 1) if (prev_px and px and prev_px > 0) else None

    # Build 41-column row
    row_data = [None] * 41
    # PERP (cols 1-26)
    row_data[0]  = d_str           # date
    row_data[1]  = px              # px_avg
    row_data[2]  = ret_1d          # ret_1d
    row_data[3]  = fw["vol"]       # vol_perp_usd
    row_data[4]  = fw["taker"]     # taker_buy_pct (decimal 0-1)
    row_data[5]  = fw["f_avg"]     # f_avg
    row_data[6]  = fw["f_min"]     # f_min
    row_data[7]  = fw["f_max"]     # f_max
    row_data[8]  = fw["f_n"]       # f_n
    row_data[9]  = regime          # funding_regime
    row_data[10] = None            # pin_streak
    row_data[11] = fw["oi"]        # oi_usd
    row_data[12] = None            # oi_vs_med14
    row_data[13] = None            # oi_cycle_pos
    row_data[14] = fw["pos_r"]     # lsr_pos_r
    row_data[15] = fw["acc_r"]     # lsr_acc_r
    row_data[16] = fw["glsr"]      # lsr_global_r
    # div_raw = pos_r / acc_r
    if fw["pos_r"] and fw["acc_r"]:
        row_data[17] = fw["pos_r"] / fw["acc_r"]
    row_data[18] = None            # div_avg3 (need 3d window)
    row_data[19] = None            # glsr_slope_5d
    row_data[20] = None            # d_pos_3d
    row_data[21] = None            # d_acc_3d
    row_data[22] = None            # signals_bullish
    row_data[23] = None            # signals_suppress
    row_data[24] = None            # screen_rank
    row_data[25] = fw["data_bad"]  # data_bad
    # SPOT (cols 27-36)
    row_data[26] = "Binance_spot"  # spot_venue
    row_data[27] = sp_vol          # vol_spot_usd
    row_data[28] = sp_tak          # taker_spot_pct
    # cols 29-35: PENDING
    # ON-CHAIN (cols 37-39)
    # MANUAL (cols 40-41)
    row_data[39] = None            # mm_note

    # Write row
    new_row = last_row + 1
    for col_idx, val in enumerate(row_data, start=1):
        c = ws.cell(row=new_row, column=col_idx)
        c.value = val
        # Format numbers
        if col_idx == 1:
            c.number_format = "@"
        elif col_idx in (2,):
            c.number_format = "0.00000"
        elif col_idx == 3:
            c.number_format = "0.0%"
        elif col_idx in (4, 5, 28):
            c.number_format = "0.0%"
        elif col_idx == 4:
            c.number_format = "0.0%"
        elif col_idx in (11,):
            c.number_format = '#,##0'
        elif col_idx in (27,):
            c.number_format = '#,##0'

    # Yellow for data_bad rows
    if fw["data_bad"]:
        for col_idx in range(1, 42):
            ws.cell(row=new_row, column=col_idx).fill = YELLOW

    print(f"  Appended row {new_row}: {d_str} px={px:.5f} oi=${fw['oi']/1e6:.2f}M"
          f" pos_r={fw['pos_r']} gLSR={fw['glsr']} data_bad={fw['data_bad']}")
    prev_px = px
    last_row = new_row

# ── Fill OUTCOME T+30 ─────────────────────────────────────────────
print("\nFilling OUTCOME T+30...")
ws_out = wb["OUTCOME"]

T30_PX = 0.0495
T0_REF = 0.0377
RET_T30 = T30_PX / T0_REF - 1  # +31.3%
PEAK_PX = 0.67205  # 1h spike 27/07
RET_PEAK = T30_PX / PEAK_PX - 1  # -92.6% from spike

for row in ws_out.iter_rows(min_row=1, max_row=ws_out.max_row):
    if row[0] and str(row[0].value) == "T+30":
        row_idx = row[0].row
        ws_out.cell(row=row_idx, column=2).value = "2026-08-09"  # ngay_han
        ws_out.cell(row=row_idx, column=3).value = T30_PX        # px
        ws_out.cell(row=row_idx, column=3).number_format = "0.00000"
        ws_out.cell(row=row_idx, column=4).value = f"+{RET_T30:.1%} vs T0={T0_REF}"
        ws_out.cell(row=row_idx, column=5).value = (
            f"Tu +897% dinh (0.672, 27/07 wick) ve +31.3%. "
            f"advisor exit VWAP 0.1971 -> px_now/exit = {T30_PX/0.1971-1:.1%}. "
            f"Crowd giu tui -73.4% tu exit."
        )
        ws_out.cell(row=row_idx, column=9).value = "MUA_T0_DUNG — exit advisor 19-21/07 chuan xac"
        print(f"  T+30 row {row_idx}: px={T30_PX}, ret={RET_T30:.1%}")
        break

wb.save(CASE_PATH)
print(f"\nDONE. Saved: {CASE_PATH}")
