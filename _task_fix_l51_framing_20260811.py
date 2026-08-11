"""Fix L-51 bai_hoc framing in CASE_INDEX LESSONS sheet.
Change: 'stale defaults — không phải running values' → 'comment sai (lying comments, bug), đã sửa'
data-source: docs/case_files/CASE_INDEX.xlsx
machine: local
date-range: 2026-08-11
code-commit: 4606b86b (signals.py fix)
"""
from __future__ import annotations
import sys, io, openpyxl
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

CASE_INDEX = Path(r"D:\Data back test\whale_data\docs\case_files\CASE_INDEX.xlsx")
wb = openpyxl.load_workbook(CASE_INDEX)
ws = wb["LESSONS"]

# Find L-51 row
l51_row = None
for r in range(1, ws.max_row + 1):
    if ws.cell(row=r, column=1).value == "L-51":
        l51_row = r
        break

if l51_row is None:
    print("ERROR: L-51 not found")
    sys.exit(1)

current = ws.cell(row=l51_row, column=4).value
print(f"L-51 at row {l51_row}")
print(f"Current bai_hoc: {str(current)[:120]}...")

NEW_BAI_HOC = (
    "Comment signals.py lệch yaml — comment sai (lying comments = bug), đã sửa commit 4606b86b. "
    "Running values từ thresholds.yaml: breakout_pct=0.09 / oi_mult=1.3 (calibrated TUT P0-close). "
    "Runtime-confirmed bằng _probe_c1_runtime_20260811.py STEP 1+2. "
    "Spec v1.5 '+9%/1.3×' KHỚP thresholds.yaml = ĐÚNG về số. "
    "Còn 3 điều kiện cấu trúc thiếu trong spec: (1) range_end=i-5 (14d range kết thúc TRƯỚC 5d build window); "
    "(2) OR-check: giá đạt target bất kỳ ngày nào trong 5d; (3) taker check là max(window)<55%, không phải per-day. "
    "Bài học: khi spec changelog nói 'X thay Y' → luôn trace thresholds.yaml, không đọc code comments."
)

ws.cell(row=l51_row, column=4).value = NEW_BAI_HOC
ws.cell(row=l51_row, column=6).value = "DA SUA — comment fix 4606b86b + runtime-confirmed 11/08"

wb.save(CASE_INDEX)
print(f"\nL-51 bai_hoc updated.")
print(f"New (first 120): {NEW_BAI_HOC[:120]}...")
print("Saved.")
