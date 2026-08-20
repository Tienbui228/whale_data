"""_task_pumpbtc_triggers_events_20260820.py
Append TRIGGERS + EVENTS per operator relay 20/08:
- TRIGGERS: DRIP-WATCH 20/08 với 4 ngưỡng nâng cấp
- EVENTS: List B report chuỗi 17-20/08 NOISE-DRIP-WATCH
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
import openpyxl

XLSX = Path(r"D:\Data back test\whale_data\docs\case_files\CASE_PUMPBTC.xlsx")
wb = openpyxl.load_workbook(XLSX)

# ── TRIGGERS ──
ws_tr = wb["TRIGGERS"]
# Clear existing content
for r in range(1, ws_tr.max_row+1):
    for c in range(1, 10):
        ws_tr.cell(r, c).value = None

# Headers + DRIP-WATCH entry
ws_tr.cell(1, 1).value = "trigger_name"
ws_tr.cell(1, 2).value = "date_opened"
ws_tr.cell(1, 3).value = "observation"
ws_tr.cell(1, 4).value = "escalate_condition"
ws_tr.cell(1, 5).value = "action_if_triggered"
ws_tr.cell(1, 6).value = "status"

# Row 2: DRIP-WATCH
ws_tr.cell(2, 1).value = "DRIP-WATCH"
ws_tr.cell(2, 2).value = "2026-08-20"
ws_tr.cell(2, 3).value = "List B drip pos +17%/13d · div_avg3 +0.064 từ đáy episode (0.184@Jul23 → 0.248@Aug06 range) · struct_n=51 · vẫn dưới threshold registry 10× (fw-139 backfill 0 rows PUMPBTC)"
ws_tr.cell(2, 4).value = ("Nâng cấp thành alert đọc lại khi bất kỳ: "
                          "(1) div_avg3 ≥ 0.35  · "
                          "(2) pos_r +15%/2d  · "
                          "(3) gLSR flush ≥30%/3d  · "
                          "(4) episode break (div > 0.5 liên tiếp ≥3d = E-R1(a))")
ws_tr.cell(2, 5).value = "Alert operator đọc lại + candidate vào unhedge_registry E-R7 nếu (4) fires"
ws_tr.cell(2, 6).value = "ACTIVE"

print(f"TRIGGERS: 1 row appended (DRIP-WATCH)")

# ── EVENTS ──
ws_ev = wb["EVENTS"]
next_r = ws_ev.max_row + 1
# Find first empty row (in case max_row lags)
for r in range(2, ws_ev.max_row + 2):
    if not ws_ev.cell(r, 1).value:
        next_r = r
        break

new_event = [
    "2026-08-17→2026-08-20",  # date range
    "NOISE-DRIP-WATCH",
    ("List B report chuỗi 17-20/08 (4d liên tiếp): drip pos +17%/13d + div_avg3 +0.064 từ đáy episode. "
     "Dưới ngưỡng registry E-R1 10× (drift threshold cần ≥+0.15/7d, current +0.064/13d = ~5× dưới ngưỡng). "
     "Classified NOISE-DRIP-WATCH — không đủ signal vào unhedge_registry, "
     "nhưng đủ signal đặt trigger DRIP-WATCH (§TRIGGERS row 2) chờ escalation."),
    "operator relay 20/08 + watchlist_log v1.4 List B",
    "unresolved",
]
for c, val in enumerate(new_event, start=1):
    ws_ev.cell(next_r, c).value = val
print(f"EVENTS: row {next_r} appended (NOISE-DRIP-WATCH 17-20/08)")

wb.save(XLSX)
print(f"\nSAVED: {XLSX}")

# Verify
wb2 = openpyxl.load_workbook(XLSX, data_only=True)
ws_tr2 = wb2["TRIGGERS"]
ws_ev2 = wb2["EVENTS"]
print(f"\nTRIGGERS row 2:")
for c in range(1, 7):
    v = ws_tr2.cell(2, c).value
    if v: print(f"  col {c}: {v[:120] if isinstance(v,str) else v}")
print(f"\nEVENTS last row ({ws_ev2.max_row}):")
for c in range(1, 6):
    v = ws_ev2.cell(ws_ev2.max_row, c).value
    if v: print(f"  col {c}: {v[:120] if isinstance(v,str) else v}")

print("\n[DONE]")
