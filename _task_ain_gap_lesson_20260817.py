"""
_task_ain_gap_lesson_20260817.py
Record staleness lesson to CASE_INDEX LESSONS sheet + agent_log.
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
from datetime import datetime, timezone
import openpyxl

ROOT = Path(r"D:\Data back test\whale_data")
NOW  = datetime.now(timezone.utc)

# ── LESSONS sheet ──────────────────────────────────────────────────────────
index_path = ROOT / "docs" / "case_files" / "CASE_INDEX.xlsx"
wb = openpyxl.load_workbook(index_path)

if "LESSONS" in wb.sheetnames:
    ws_l = wb["LESSONS"]
    max_r = ws_l.max_row
    next_r = max_r + 1
    ws_l.cell(next_r, 1, "L-BUG-STALE-CASE")
    ws_l.cell(next_r, 2, "2026-08-17")
    ws_l.cell(next_r, 3, "CASE")
    ws_l.cell(next_r, 4, (
        "build_case.py dùng scratch CSV theo DATE_TAG baked vào lệnh. "
        "Khi build chạy muộn (5 ngày sau fetch), data gap âm thầm — không có guard. "
        "Fix: thêm STALENESS GUARD: gap > 2d → RAISE. "
        "Lesson: scratch CSV là nguồn duy nhất cho build_case; "
        "không có pipeline auto-refresh → PHẢI re-fetch trước khi build muộn."
    ))
    ws_l.cell(next_r, 5, "AINUSDT 20260813 fetch, build chạy 20260817 → thiếu Aug13-16")
    print(f"LESSONS row {next_r} added")
else:
    print("WARN: LESSONS sheet not found — skip")

wb.save(index_path)
print("CASE_INDEX saved")

# ── agent_log ──────────────────────────────────────────────────────────────
log_path = ROOT / "agent_log.md"
entry = f"""
---

## AIN DATA GAP FIX — {NOW.strftime('%Y-%m-%d %H:%M UTC')}

**Bug:** CASE_AIN.xlsx built 17/08 trên scratch CSV fetch từ 13/08 → thiếu 5 ngày (Aug13-16+17).

**Root cause [1-4]:**
- [1] Store: không có perp klines daily store — build_case đọc trực tiếp scratch CSV (`ain_perp_20260813.csv`). Scratch không auto-refresh.
- [2] freshwatch_symbols.txt: ABSENT local. collect_daily cover all TRADING USDT-PERP nhưng chỉ lưu 1h store — không có klines_1d perp.
- [3] Staleness guard: KHÔNG CÓ. `MAX_DATE = sorted(perp_by_d.keys())[-1]` chỉ set, không compare với today.
- [4] case_daily.py: không cover AIN (status COLD_START, chỉ cover OPEN/TRACKING).

**Fix:**
- Re-fetch fapi klines Aug13-16 + append → ain_perp_20260817.csv (228 rows, Jan01-Aug16)
- Funding merge: old 1343 + 25 new Aug13-17 entries = 1368 entries
- OI: rename sumOpenInterestValue→oi_usd, sumOpenInterest→oi_token
- Rebuild: CASE_AIN.xlsx 228 rows, validate_written_pack PASS
- Added STALENESS GUARD to build_case.py: gap > 2d → RuntimeError

**Schema bugs phát hiện (minor, ghi để tránh):**
- New perp CSV schema `o/h/l/c` + no ret_1d → build_case computes ret_1d as FRACTION → scale mismatch vs percent filter
- OI CSV: phải có `oi_usd/oi_token` fields (không phải `sumOpenInterestValue/sumOpenInterest`)
- Perp CSV: phải có `ret_1d` pre-computed as percent OR dùng short names và guard phải scale check

**Lesson (L-BUG-STALE-CASE):** Thêm vào CASE_INDEX LESSONS.

**Lesson bổ sung về lệnh build_case:**
CẦN re-fetch scratch CSVs (date_tag=today) MỖI LẦN build_case chạy không cùng ngày với fetch.
Không có pipeline tự động → khi build muộn > 0 ngày phải chạy fetch probe trước.
"""
with open(log_path, "a", encoding="utf-8") as f:
    f.write(entry)
print(f"agent_log appended ({len(entry)} chars)")
print("[DONE]")
