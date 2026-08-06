# BANK/BR Vol Anomaly — Analysis Note
Date: 2026-08-06 · Probe: `_probe_a4_vol_20260806.py`

## Kết luận nhanh

BANK pre-29/07: **tất cả vol là số tròn** — manually backfilled, không phải từ case_daily.
BANK 18/07 và 25/07: **cùng vol = 1,900,000,000** — vật lý bất khả thi (2 ngày khác nhau, cùng giá trị chính xác đến đồng).
BANK 08/05: vol tròn (102,200,000) + taker Δ=0.001198 — hàng nghi vấn manually entered.

BR pre-29/07: vol lệch 0.04–3.75% — round numbers tự nhiên hơn, nhưng vẫn lệch CSV.
BR: không có fraction row nào (tất cả đã convert pass 2).

---

## BANK — Chi tiết

### Pre-29/07 rows (06/09–25/07): manual backfill

| Dấu hiệu | Ví dụ |
|---|---|
| Vol tròn đến 100K | 670,000; 2,700,000; 12,000,000 |
| Vol lệch CSV 0.04–2.46% | Đủ lệch để thấy không khớp exact |
| **Placeholder 1.9B × 2 ngày** | 18/07=1,900,000,000 (csv 1,920M) · 25/07=1,900,000,000 (csv 1,885M) |

Kết luận: pre-29/07 BANK vol **không đến từ case_daily** và không đến từ CSV export tại thời điểm chạy.
Nguồn khả năng: nhập tay hoặc backfill script cũ có rounding về triệu (1M).

### 26-28/07: chuyển tiếp format

- 26/07: xl_taker=51.21 (percent, OLD code), vol khớp CSV chính xác 0%.
- 27/07: xl_taker=50.85 (percent), vol xl=1,529,118,313 vs csv=144,539,447 → **lệch 957%**.
  Giải thích: BANKUSDT có volume spike thật trên 27/07 (1.53B), nhưng CSV hiện tại (re-export sau đó) chỉ còn 144.5M. Hoặc xl value từ nguồn khác.
- 28/07: taker=None, vol=None → **hàng bị bỏ trống**.

### 29-31/07: case_daily đúng

Vol khớp CSV 100% (0.00%). Taker đã convert pass 1 → percent.

### 08/01–04/08: case_daily đúng (new code, no 2.5(a))

Vol khớp CSV 100%. Taker fraction (chờ convert nếu BANK pass audit).

### 08/05: suspect

| Trường | xlsx | CSV hôm nay | Δ |
|---|---|---|---|
| taker_buy_pct | 0.4860 | 0.4848 | 0.001198 |
| vol_quote | 102,200,000 | 226,476,484 | **54.87%** |

- vol_xl=102,200,000 là số tròn (102.2M chính xác) — pattern giống pre-29/07 manual rows.
- vol và taker đều lệch → hoặc (a) CSV re-export thay đổi data 08/05 sau khi case_daily viết,
  hoặc (b) hàng 08/05 BANK cũng manually entered.
- Taker Δ=0.001198 > ngưỡng 0.0001 → A1 verdict: **BANK NOT WRITTEN**.

---

## BR — Chi tiết

### Pre-29/07: percent values, vol 0.04–3.75% off CSV

- Tất cả taker ở dạng percent (44.32–53.90%) — OLD code Zone-A-agg.
- Vol lệch 0.04–3.26% — pattern nhất quán (cùng chiều: luôn gần đúng, không bao giờ chính xác).
- Giải thích: BR pre-29/07 được viết bởi case_daily cũ, CSV export sau đó có thể đã re-aggregate.
- **Không có placeholder chính xác** như BANK 18+25/07.

### Post-29/07: case_daily mới, vol = 0%

Từ 28/07: vol khớp CSV tuyệt đối. Taker convert pass 2 (61 cells) đã hoàn tất.

---

## Quyết định

| Case | Action | Lý do |
|---|---|---|
| BANK pre-29/07 fraction | **KHÔNG CONVERT** | Vol manually entered, provenance không rõ |
| BANK 08/01–04 fraction | PENDING A1 audit | Vol đúng, taker Δ < 0.00005 |
| BANK 08/05 fraction | **KHÔNG CONVERT** | Taker Δ=0.001198, vol suspect |
| BR | DONE (61 cells) | Verify PASS, taker match, vol pattern OK |

---

## Ghi chú kỹ thuật

- Vol ROUND pattern: `round(vol, -5)` hoặc `-6` → truncate tới 100K hay 1M.
- Probe source: `_probe_a4_vol_20260806.py`.
- Backup convert trước mọi write: `scratch/backup_taker_20260805/`.
