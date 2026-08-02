#!/usr/bin/env python3
"""Append L-40 to CASE_INDEX.xlsx LESSONS sheet + regenerate lessons_learned.md (rev.6)."""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import openpyxl
from pathlib import Path

CASE_INDEX = Path(r"D:\Data back test\whale_data\docs\case_files\CASE_INDEX.xlsx")
LESSONS_MD = Path(r"D:\Data back test\whale_data\docs\lessons_learned.md")

# L-40 data
L40 = [
    "L-40",
    "2026-08-02",
    "NANSEN_KEY_LOCKED blast-radius (02/08) — bot fresh wallets",
    (
        "Chốt chặn cấp máy có blast radius cấp máy — trước khi gạt công tắc dùng chung "
        "(env/key/config toàn cục), bắt buộc liệt kê MỌI consumer hợp lệ; ràng buộc nhắm vào "
        "agent phải đặt ở tầng hẹp nhất đủ dùng (per-process wrapper), không đặt tầng chung. "
        "Bằng chứng: bot fresh wallets chết 3 ngày (gap 31/07–02/08) vì NANSEN_API_KEY rename "
        "sang NANSEN_KEY_LOCKED — automated job \FreshWatch không đọc được key."
    ),
    "rule",
    "DA SUA — run_daily_wrapper.py (02/08); FreshWatch task updated",
    (
        "trước khi rename/remove bất kỳ env/key/config toàn cục: "
        "grep MỌI consumer (scheduled task + code), sửa wrapper per-process trước khi rename"
    ),
    None,
]

# Load workbook
wb = openpyxl.load_workbook(str(CASE_INDEX))
ws = wb["LESSONS"]

# Verify last row is L-39
last_vals = [ws.cell(ws.max_row, c).value for c in range(1, 5)]
print(f"Last row before append: {last_vals}")

ws.append(L40)
print(f"Appended L-40: {L40[:4]}")

wb.save(str(CASE_INDEX))
print(f"Saved: {CASE_INDEX}")

# Regenerate lessons_learned.md
wb2 = openpyxl.load_workbook(str(CASE_INDEX), read_only=True, data_only=True)
ws2 = wb2["LESSONS"]
all_rows = list(ws2.iter_rows(values_only=True))
wb2.close()

data_rows = [r for r in all_rows[1:] if r[0] is not None and str(r[0]).startswith("L-")]
print(f"\nTotal lessons: {len(data_rows)}")

lines = [
    "# Lessons Learned",
    f"_Generated from CASE_INDEX.xlsx sheet LESSONS — {len(data_rows)} entries_",
    "",
]
for r in data_rows:
    lid = r[0] or ""
    dt = r[1] or ""
    txt = r[3] or ""
    lines.append(f"**{lid}** ({dt}): {txt}")
    lines.append("")

LESSONS_MD.write_text("\n".join(lines), encoding="utf-8")
print(f"Regenerated: {LESSONS_MD} (rev.6, {len(data_rows)} lessons)")

print("\nLast 3 lessons:")
for r in data_rows[-3:]:
    print(f"  {r[0]} | {r[1]} | {str(r[3])[:80]}...")
