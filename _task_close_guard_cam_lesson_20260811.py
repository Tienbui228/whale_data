"""Task: Append GUARD-CÂM + P0 closing lessons to CASE_INDEX.xlsx LESSONS sheet.
Rows 4=header; last lesson L-48 at row 51 → append L-49/50/51 at 52/53/54.

data-source: docs/case_files/CASE_INDEX.xlsx
machine: local
date-range: 2026-08-10 → 2026-08-11
code-commit: see git log
"""
from __future__ import annotations
import sys, io, openpyxl
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

CASE_INDEX = Path(r"D:\Data back test\whale_data\docs\case_files\CASE_INDEX.xlsx")
wb = openpyxl.load_workbook(CASE_INDEX)
ws = wb["LESSONS"]

# Columns (header row 4): id=1, ngay=2, case_nguon=3, bai_hoc=4, loai=5, trang_thai=6, hanh_dong_tiep=7
# Find first truly empty row after last data
last_data = 4
for r in range(ws.max_row, 4, -1):
    if ws.cell(row=r, column=1).value:
        last_data = r
        break

start_row = last_data + 1
print(f"Last lesson row: {last_data}, appending at row {start_row}")

LESSONS = [
    {
        "id": "L-49",
        "ngay": "2026-08-11",
        "case_nguon": "GUARD-CÂM / ALL tokens",
        "bai_hoc": (
            "save_state() fail-open: ghi state.json không kiểm tra invariants → state corrupt không bị bắt. "
            "Sửa: validate_gom_state() wired vào save_state() pre-write (4 invariants: open chain ≤3d gap, "
            "không open+cooldown đồng thời, vwap_type hợp lệ, cooldown_end ≥ episode_start). "
            "Violation → RuntimeError → exit≠0 → Telegram alert (L-44). Commit c3d49e1."
        ),
        "loai": "GUARD",
        "trang_thai": "DA VAO gom_scan.py c3d49e1",
        "hanh_dong_tiep": "Verify sau SCP: validator không thay đổi write behavior (md5 re-check post manual run)",
    },
    {
        "id": "L-50",
        "ngay": "2026-08-11",
        "case_nguon": "P0 / FFUSDT 2026-08-01",
        "bai_hoc": (
            "P0 root cause: floating-point boundary tại A3 slope_5d = 1.15. FFUSDT 08-01: slope=1.14902 "
            "(dist=0.00098 từ ngưỡng). State corrupt xảy ra vì backfill chạy lại trên đoạn đã có chapter, "
            "không phải cron viết lại. Incremental mode §8.2 đã xác nhận đúng: md5 closed-chapters IDENTICAL "
            "sau cron 01:25 UTC 08-11 (a5a929dcc4ba17f71eb3243146be2314). Vùng-rung probe: A3 có 32 "
            "changed-outcome events / 60d / 525 tokens tại ε=0.005. Mốc V4 monitor: MARGINAL-V4 đến 25/08."
        ),
        "loai": "P0",
        "trang_thai": "DONG — md5 PASS 11/08",
        "hanh_dong_tiep": "V4 monitor: đếm chain oscillation do A2/A3 marginal qua marginal_hits.csv đến 25/08",
    },
    {
        "id": "L-51",
        "ngay": "2026-08-11",
        "case_nguon": "GOM-C C1 spec / TỔNG HỢP",
        "bai_hoc": (
            "Code comments (# 0.15 / # 1.5 trong signals.py) là stale defaults — không phải running values. "
            "Running values đến từ thresholds.yaml: breakout_pct=0.09 / oi_mult=1.3 (calibrated cho TUT P0-close). "
            "Spec v1.5 số đúng nhưng thiếu 3 điều kiện cấu trúc: (1) range_end=i-5 (14d range kết thúc TRƯỚC "
            "5d build window); (2) OR-check: giá đạt target bất kỳ ngày nào trong 5d; (3) taker check là "
            "max(window)<55%, không phải per-day. Bài học: khi spec nói 'X thay Y' trong changelog — luôn "
            "trace thresholds.yaml chứ không đọc code comments."
        ),
        "loai": "SPEC-DRIFT",
        "trang_thai": "DE XUAT — chờ ANALYSIS ký C1 text ≤14/08",
        "hanh_dong_tiep": "ANALYSIS xác nhận số canonical (0.09/1.3× hay 0.15/1.5×) + ký C1 text → operator ký ≤14/08",
    },
]

for i, lesson in enumerate(LESSONS):
    row = start_row + i
    ws.cell(row=row, column=1).value = lesson["id"]
    ws.cell(row=row, column=2).value = lesson["ngay"]
    ws.cell(row=row, column=3).value = lesson["case_nguon"]
    ws.cell(row=row, column=4).value = lesson["bai_hoc"]
    ws.cell(row=row, column=5).value = lesson["loai"]
    ws.cell(row=row, column=6).value = lesson["trang_thai"]
    ws.cell(row=row, column=7).value = lesson["hanh_dong_tiep"]
    print(f"  Row {row}: [{lesson['id']}] {lesson['bai_hoc'][:60]}...")

wb.save(CASE_INDEX)
print(f"\nSaved {CASE_INDEX.name}")
print(f"Done. {len(LESSONS)} lessons appended (rows {start_row}→{start_row + len(LESSONS) - 1}).")
