---
type: adapter-spec
name: ADAPTER-DAILY v0.1 (CASE_*.xlsx DAILY sheet → DayData)
version: v0.1 (24/08/2026)
status: SIGNED — operator ký chat 24/08 tại ĐIỂM DỪNG 1 nguyên văn 5 dòng
signed_by: operator (chat 24/08)
consumer: replay.py::parse_result_file (input builder) — gate calib pipeline
---

# ADAPTER-DAILY v0.1

**Ký:** operator chat 24/08 tại ĐIỂM DỪNG 1, nguyên văn 5 mục dưới đây.

## Spec (nguyên văn, KHÔNG diễn giải)

1. Đọc sheet DAILY, map cột theo bảng tên tường minh (yaml), cột không có trong map → lỗi, không đoán.

2. Ratio cột phải khai quy ước (keep-last 23:00 canonical); quy ước khác → từ chối, không convert.

3. Cột thiếu → NaN + low_conf=1 ghi từng hàng; không điền mặc định.

4. Output = CSV schema --daily hiện có; gọi builder gốc, KHÔNG sửa replay.py/parse_result_file.

5. Token adapter chỉ chạy scan; vào bộ calib 12→13 chỉ khi có _result.txt + GATE dict do ANALYSIS viết, operator ký.

## Cross-ref

- ĐIỂM DỪNG 1 sign-off: operator chat 24/08
- Cross-ref adapter-H1: `proposals/adapter_h1_spec_v0.1_20260824.md`
- CASE_*.xlsx location: `docs/case_files/CASE_<TOKEN>.xlsx` (8 CASE: BANK/TUT/CYS/AKE/BTW/HEMI/ON/CAP per A5b)
- builder gốc: `replay.py::parse_result_file` (KHÔNG sửa per mục 4)
