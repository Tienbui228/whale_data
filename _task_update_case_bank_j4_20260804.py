#!/usr/bin/env python3
"""J4: Update CASE_BANK.xlsx — unlock schedule + June events + px_max correction.

UNLOCK sheet: điền lịch 17/06, 17/07, 17/08.
EVENTS sheet: append unlock-correlation rows + 06-08/06 mini-pump.
OUTCOME: fix px_max row.

Source: _probe_bank_june_unlock_20260804.py (04/08/2026)
"""
import io, sys
from pathlib import Path
import openpyxl
from openpyxl.styles import PatternFill, Font

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

XLSX = Path(r"D:\Data back test\whale_data\docs\case_files\CASE_BANK.xlsx")
wb = openpyxl.load_workbook(XLSX)

# ─── UNLOCK sheet ─────────────────────────────────────────────────────────────
ws_unlock = wb["UNLOCK"]
print(f"UNLOCK current max_row: {ws_unlock.max_row}")

# Replace PENDING rows with operator-fed data (17/month, ~2% supply)
# Keep header rows (1-2), then fill schedule
# Current structure A1:B8 — replace B col values

update_map = {
    "Circulating / Total": "PENDING (operator feed)",
    "Nguon tra":           "operator 04/08/2026 — CryptoRank/TokenUnlocks",
    "Unlock KE TIEP":      "17/08/2026 (T+38 từ T0 10/07) — ~2% supply/tháng",
    "Unlock 90 ngay toi":  "17/08 · 17/09 · 17/10 (~2%/tháng mỗi lần)",
    "Cliff da qua gan nhat": "17/07/2026 — KHỚP exact với exit window 19-21/07 (T+7→T+9)",
    "Doc":                 "Khuôn L-12: MM xả T+2→T+4 sau unlock 17/07. Cảnh báo 17/08.",
}

for row in ws_unlock.iter_rows():
    key = row[0].value
    if key in update_map:
        row[1].value = update_map[key]
        print(f"  UNLOCK[{key}] → updated")

# Add unlock schedule block
next_row = ws_unlock.max_row + 2
ws_unlock.cell(next_row, 1, "=== UNLOCK CALENDAR (operator 04/08) ===")
ws_unlock.cell(next_row, 1).font = Font(bold=True)
next_row += 1

unlock_cal = [
    ("17/06/2026", "PAST",
     "Quanh 17/06: KHÔNG có markup. Trước đó 05-08/06 vol spike 50M→41M (mini-pump T-10 đến T-9). "
     "Funding BURST 08/06 (23.4bps). Unlock chính ngày 17/06 = QUIET (vol 1.6M). "
     "Sau 17/06: px giảm -8% đến 22/06. Pattern = đè-sau-unlock (chưa campaign)."),
    ("17/07/2026", "PAST — KHỚP CAMPAIGN",
     "Unlock T+7 từ T0 (10/07). Trong đỉnh markup (+280% đến ngày này). "
     "MM XẢ T+2→T+4 sau unlock: pos_r 3.7→1.09 (19-21/07). "
     "KẾT LUẬN: unlock là mốc xả — MM dùng vol unlock làm thanh khoản thoát."),
    ("17/08/2026", "UPCOMING — T+38 từ T0",
     "CẢNH BÁO: token đang SUPPRESSED (px 0.043 = -93.6% từ spike 0.672). "
     "Nếu khuôn lặp: cửa sổ bait = 02/08→17/08. "
     "NHƯNG: pos_r chưa reset, không có bằng chứng MM build mới. "
     "→ Theo dõi như RỦI RO (không phải cơ hội). Operator quyết."),
]

for date_s, status, note in unlock_cal:
    ws_unlock.cell(next_row, 1, date_s)
    ws_unlock.cell(next_row, 2, f"[{status}] {note}")
    next_row += 1

print(f"UNLOCK: added calendar block")

# ─── EVENTS sheet — append new rows ───────────────────────────────────────────
ws_ev = wb["EVENTS"]

# Find last used row
ev_last = ws_ev.max_row
while ev_last > 0 and all(ws_ev.cell(ev_last, c).value is None for c in range(1, 5)):
    ev_last -= 1

print(f"EVENTS current last row with data: {ev_last}")

new_events = [
    # (ngay, su_kien_so_lieu, nguon, doc_nhanh)
    ("06-05/06",
     "mini-pump: vol 10M→25M→50.9M→41M (05-08/06), high 0.045, funding BURST 08/06 (23.4bps peak). "
     "Flush down 05/06 (low 0.022), recover 06-08/06. T-10 so với 17/06 unlock.",
     "fapi klines + fundingRate (probe 04/08)",
     "bait-probe trước unlock Jun? (vol+funding chỉ dấu)"),
    ("06-17",
     "Unlock ~2% supply 17/06: QUIET (vol 1.6M, px ~0.04). Funding toàn PIN. "
     "Sau unlock: px -8% đến 22/06. acc_r=0.952 ngày 13/06 (ĐÃ CAO TRƯỚC UNLOCK).",
     "fapi klines + freshwatch 09/06+13/06 (probe 04/08)",
     "unlock không kèm markup — đè sau để gom rẻ"),
    ("07-17",
     "Unlock ~2% supply 17/07: TRONG đỉnh markup. px=0.068 (T+7). "
     "MM XẢ T+2→T+4 (19-21/07): pos_r 3.7→1.09, vol 1.4-6.5B/ngày. "
     "Khuôn L-12: kéo-trước-xả-vào-hype sau unlock.",
     "freshwatch + calib (probe 04/08)",
     "unlock = mốc xả MM; vol unlock = thanh khoản thoát"),
    ("07-27 06:00",
     "px_max SPIKE 0.67205 USDT (1h native fapi). vol 299.72M USDT trong 1 nến. "
     "Close 0.419. Freshwatch daily avg 27/07=0.374. "
     "Wick spike — không phải close-based peak. px_max trước ghi 0.376 = WRONG.",
     "fapi 1h klines (probe H1 04/08)",
     "px_max thực = 0.672 spike, không phải 0.376 daily avg"),
]

next_ev = ev_last + 1
for ev in new_events:
    for col, val in enumerate(ev, start=1):
        ws_ev.cell(next_ev, col, val)
    next_ev += 1

print(f"EVENTS: appended {len(new_events)} rows (rows {ev_last+1}→{next_ev-1})")

# ─── OUTCOME sheet — fix px_max ───────────────────────────────────────────────
ws_out = wb["OUTCOME"]

# Find T+14 row to also update drawup_drawdown with spike info
for row in ws_out.iter_rows():
    if row[0].value == "T+14":
        # drawup_drawdown col (E=5): add spike note
        row[4].value = "spike_high=0.672 ngày 27/07 (wick); close_max=0.419; daily_avg_max=0.376 (26/07)"
        print(f"  OUTCOME T+14 drawup_drawdown updated with px_max spike note")
        break

# Add a note row below T+60 about px_max correction
t60_row = None
for row in ws_out.iter_rows():
    if row[0].value == "T+60":
        t60_row = row[0].row; break
if t60_row:
    note_row = t60_row + 2
    ws_out.cell(note_row, 1, "NOTE")
    ws_out.cell(note_row, 2,
        "px_max SỬA (probe H1 04/08): 1h spike high = 0.67205 (27/07 06:00 UTC, 299M USDT). "
        "Daily avg max = 0.37632 (26/07 freshwatch). Close max = 0.41958 (27/07). "
        "Markup từ T0 (0.03773): +1681% spike / +897% daily avg / +1012% close.")
    print(f"  OUTCOME: px_max correction note added at row {note_row}")

wb.save(XLSX)
print(f"\nSaved: {XLSX}")
print("J4 DONE")
