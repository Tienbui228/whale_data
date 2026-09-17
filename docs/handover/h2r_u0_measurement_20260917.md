# HANDOVER · h2r + U0 measurement · KÝ 17/09

## Bối cảnh

Chuỗi đo X/Y/Z/A/B/C từ 17/09 nhằm trả lời câu "detector h2r có mang tin không, và nếu có thì mở universe scope có bắt thêm signal thật không". Kết quả: tường n=1. Đóng sổ, mở lại khi hedge-proven subset đạt ≥6 ca.

## Kết quả · BA TẦNG (không gộp)

### Tầng 1 · h2r → U0
**ĐO ĐƯỢC và PHẲNG**. Sau backfill 122d (2026-05-18 → 2026-09-17) trên freshwatch 139:
- h2r ≥ q90 (4.135) fires: 1448
- → U0 trong 30d sau: 71 · precision **4.90%**
- Nền U0 rate: 4.22%
- **Lift 1.16×** · **n=71 · ĐỦ MẪU để kết luận**

Kết luận: h2r đo TRƯỚC U0 KHÔNG dự báo U0 mạnh hơn nền. Tầng này phẳng.

### Tầng 2 · chuỗi h2r → U0 → ×2
**CHƯA ĐO ĐƯỢC**. Numerator n=72 chain xuất hiện nhưng chỉ 5 hit ×2, cả 5 đều là **BTR** — 5 ngày fire khác nhau (07-21, 07-23, 07-25, 08-01, 08-10) dẫn về CÙNG một cross 2026-08-13 và CÙNG một lần ×2 6.46x. **n thật = 1 event**, không phải 72 chain.

Ghi "not measured". KHÔNG ghi "lift 1.42× yếu" — vì 1.42× tính trên n=72 giả (5 chain-hit của cùng 1 event).

### Tầng 3 · quỹ đạo h2r_max[D-10..-2] / h2r_mean[D-1..+1]
**CHƯA ĐO ĐƯỢC**. Đăng ký giả thuyết trước, đo sau:

| group | n | median | scatter |
|-------|--:|-------:|---------|
| POS proven (BTR, BULLA, UAI) | 3 | 5.30 | 0.89 · 5.30 · 30.90 (variance khổng lồ) |
| NEG SOPH (đối chứng) | 1 | 6.71 | (n=1) |
| BASELINE random | 500 | 3.17 | p75 = 6.09 |

POS n=3 · NEG n=1. POS median 5.30 chỉ hơi vượt baseline p50, ca âm SOPH 6.71 NẰM GIỮA dải dương. **Không có power để đánh giá phân tách**.

## Câu đúng · KHÔNG viết "h2r không mang tin"

> **h2r + U0 phủ MỘT cơ chế; cơ chế đó hiện có 3 ca đã biết (BTR/BULLA/UAI); 3 ca không kiểm chứng được gì. Thứ chặn là SỐ CA, không phải detector, không phải cửa sổ — đã nhân 4 lần cửa sổ (30d → 122d), tường không đổi.**

## C1 tìm ĐÚNG · KHỚP PATTERN_BOOK

Đo tìm ra 3/13 proven có U0 detect: **BTR (08-13) · BULLA (09-05) · UAI (07-09)**. 10 proven còn lại im.

**Đây là luật chạy ĐÚNG, không phải quá chặt**. PATTERN_BOOK v1.3 §5 ghi rõ:
> "3 proven còn lại (AKE, ON, HEMI) **không** phải unhedge-do-crowd (episode 4-5 ngày, Δpos +2…+26) — máy đã thấy chúng qua kênh khác (kho AKE, H1 ON, H2b HEMI)."

Tức là h2r+U0 CHỈ phủ subset "hedge-do-crowd" (BULLA, BTR, UAI, + 3 chưa detect được là LOBSTER, PROM, CAP - có thể khác cơ chế hoặc D_cross ngoài window). AKE/ON/HEMI/CYS/BTW/TUT/BANK — kênh khác, không phải h2r+U0 target.

**Detector chạy đúng phạm vi thiết kế. Kết quả im lặng ≠ detector yếu.**

## Mốc mở lại

Mở lại đo h2r+U0 khi **hedge-proven subset đạt ≥6 ca** (thêm 3 case hedge-crowd mới). Trước đó, mọi đo lift/precision đều thiếu sample power → dừng.

## Không nới U0 rule

Rule hiện: `div_avg3 vượt 0.5→0.7 trong ≤3d ∧ acc_r rơi ≥30% cùng cửa sổ`. **KHÔNG nới sau khi thấy kết quả** — nới sau-kết-quả = fitting. Cũng sẽ trộn cơ chế L1/L2/L3 (hedge-crowd vs khác kênh) và phá phân loại PATTERN_BOOK.

Rule chỉ được review khi ANALYSIS ký (không do agent).

## Probes bằng chứng

Tất cả trong `sandbox/v1_3_dryrun/`:
- `_probe_U1234_funnel_20260917.py` — U1-U4 phễu 4 tầng, timing collect
- `_probe_V1234_deeper_20260917.py` — V1 timing thật 300 samples, V2 3-trục, V3 union, V4 perp vol
- `_probe_W1234_load_20260917.py` — W1-W4 tải nếu mở sang perp, master body size
- `_probe_X1234_holes_20260917.py` — X1 base rate, X2 detector search, X3 mcap, X4 PROM
- `_probe_Y1234_detector_load_20260917.py` — Y1/Y2 gom_h_daily + h2prime existing store, Y3 body char, Y4 h2prime precision, Y5 filter code map
- `_probe_Z1234_backfill_20260917.py` — Z1-Z5 backfill 385 x 30, Z4 fw benchmark, Z5 h2r distribution
- `_probe_A1234_h2r_power_20260917.py` — A1 base internal, A2 lift fw, A3 lift excl, A4 proven h2r@D0
- `_probe_B1234_h2r_U0_20260917.py` — B1 h2r trước D_cross, B2/B3 chain, B4 A4 redo với D_cross
- `_probe_C1234_backfill_deep_20260917.py` — C1 backfill 122d, C2 B2/B3 rerun, C3 trajectory, C4 baseline

## Sign-off

- Đo: agent 17/09
- Chốt dừng: operator (nhánh 3) 17/09
- Mở lại: chờ hedge-proven ≥6 ca
