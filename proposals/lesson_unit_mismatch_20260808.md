---
type: lesson_proposal
for_sheet: CASE_INDEX.xlsx → LESSONS
date: 2026-08-08
status: DRAFT — chờ operator duyệt
---

# Đề xuất LESSON entry: Unit mismatch tại biên loader

## Text đề xuất cho sheet LESSONS

**Title:** Unit mismatch tại biên layer → đảo ngữ nghĩa signal im lặng

**Body:**
Taker_buy_pct decimal (0.47) vs percentage (47.0): decay-threshold 48.0 luôn thỏa → decay
always-on → suppress toàn bộ universe. Bug âm thầm — PASS/FAIL không lỗi, chỉ sai số.
Đây là bug thang thứ TƯ cùng họ trong 10 ngày: workbook fraction/percent (07-30) · k[9]
base/quote ZBT (07-31) · alpha k[9] broken (08-04) · loader CSV taker (08-08). Pattern:
mỗi lần data_reader bị trì hoãn → một bug thang mới xuất hiện đúng hẹn. Số-tự-bảo-vệ
(tripwire max ≤ 1.0 → WARNING + convert) áp ngay tại biên INPUT CODE, không chỉ ở report.

**Kiến trúc:** data_reader (nơi DUY NHẤT dán nhãn đơn vị) phải là module ưu tiên cao nhất.
Consumer code (signals, gate probe, Excel writer) KHÔNG được giải quyết đơn vị tự ý — đó
là dấu hiệu data_reader chưa tồn tại hoặc bị bypass. Mỗi bypass = nợ kỹ thuật sẽ phát nổ
khi source thay format.

**Fix áp dụng:**
- `load_fw_csv()` (gate probe): tripwire `_taker_scale()` — detect raw max ≤ 1.0 → ×100 + WARNING stderr; raise nếu mixed.
- `_load_export_csv()` (case_daily.py): post-load tripwire — log.warning nếu max > 1.0 (×100 sẽ double-scale).

**Lesson ID (gợi ý):** L-45 — CHỈ append sau khi xác nhận sheet đã có L-43 và L-44;
nếu chưa có → báo operator, không chen số (án đánh số lỗ).
**Tags:** unit-bug, data-reader, tripwire, decay, loader
