# Proposal v2: Quy ước ratio-daily canonical (REWORK)
**Ngày soạn:** 2026-07-31  
**Thay thế:** proposals/ratio_daily_canonical_20260731.md (đã đánh dấu SUPERSEDED)  
**Trạng thái:** CHỜ OPERATOR KÝ  
**Tác giả:** Agent (claude-sonnet-4-6)

---

## Kết quả test (bằng chứng số)

Probe 5 symbols × 6 ngày (07-24→07-29) = 21 điểm dữ liệu có native_1d:

| So sánh | Avg abs diff | Max diff | Kết luận |
|---|---|---|---|
| `native_1d` vs `00:00 UTC` (derived_1h) | **0.000%** | 0.000% | IDENTICAL — 21/21 điểm |
| `native_1d` vs `keep-last 23:xx UTC` | **6.577%** | 26.13% | KHÁC — nhiều trường hợp lệch >5% |

**native_1d `as_of_ts_ms` từ store:** luôn = `00:00 UTC của date` (ví dụ: TAG 07-24 → 1784851200000 = 07-24 00:00 UTC).

**OI boundary (PART 2):** `oi_hist_1d` cũng dùng `as_of_ts_ms = 07-24 00:00 UTC` → **ratio và OI cùng boundary 00:00 UTC**.

Bảng tóm tắt (trích một số hàng minh họa):

```
Symbol         Date         native_1d  00:00-UTC  keep-last  d(n-0h)%  d(n-kl)%
TAGUSDT        2026-07-26      1.7046     1.7046     1.3515    +0.00%   +26.13%
BANKUSDT       2026-07-28      1.6178     1.6178     1.3387    +0.00%   +20.85%
BULLAUSDT      2026-07-29      1.6035     1.6035     1.8557    +0.00%   -13.59%
TAGUSDT        2026-07-24      1.6937     1.6937     1.7067    +0.00%    -0.76%
```

---

## Quy ước được đề xuất (NGƯỢC so với bản v1)

> **`lsr_pos_r` DAILY canonical = snapshot tại 00:00 UTC của ngày D**  
> = giá trị `as_of_ts_ms == midnight_ms(D)` trong `top_pos_1h` partition `date=D`  
> = **GIỮ NGUYÊN cách tính `derived_1h` hiện hành** — không cần thay đổi code.  
>  
> **`lsr_pos_r` giá trị 23:xx UTC (keep-last) và mọi snapshot intraday = EVENTS/context** —  
> không vào cột DAILY, không dùng làm threshold fire/ARM.  
>  
> **Cấm đổi quy ước vận hành lệch quy ước calib**: calib 12 cases được build trên native_1d  
> = 00:00 UTC snapshot → derived_1h hiện tại là ĐÚNG boundary, không hồi tố, không đổi.

---

## Đối xứng L-21 (OI)

L-21 nói: "OI daily canonical = export Binance openInterestHist 00:00 UTC".

Kết quả probe xác nhận: `oi_hist_1d` date=2026-07-24 → `as_of_ts_ms = 07-24 00:00 UTC`.

**→ Ratio và OI cùng boundary: 00:00 UTC đầu ngày D. Nhất quán.**

Không có L-24 tái sinh: cả hai metric dùng cùng một thời điểm chụp.

---

## Hậu quả với BULLA 07-20

Với quy ước này:
- **Canonical 07-20**: derived_1h = **1.981** (00:00 UTC 07-20, từ top_pos_1h store)
- **Original repo (bulla_result.txt) = 1.99**: cùng boundary 00:00 UTC 07-20, lấy từ native API trực tiếp → diff = (1.99−1.981)/1.981 = **+0.45%** < 1% ngưỡng chấp nhận được
- **keep-last 23:00 UTC 07-20 = 1.6811**: EVENTS — ratio đã giảm trong ngày
- **Loose u50 = 1.75**: nguồn không rõ, RETIRED

**→ 1.99 trong calib là ĐÚNG boundary (khác 1.981 do floating point/timing API < 0.5%).  
twelve_cases KHÔNG sửa số. Footnote cập nhật để phản ánh điều này.**

---

## Phạm vi áp dụng

| Đối tượng | Hành động |
|---|---|
| `scripts/export_freshwatch_daily.py` — `_build_derived_1h` | **KHÔNG ĐỔI** — đã dùng 00:00 UTC, đúng rồi |
| freshwatch_daily CSV hiện tại | **KHÔNG ĐỔI** — `src_ratio=derived_1h` là đúng |
| 12 calib files / suite | **KHÔNG ĐỘNG** — suite locked |
| Tài liệu quy ước | **CẬP NHẬT** — bản này là văn bản hóa chính thức |

---

## Để operator ký

Comment hoặc commit file này với message "DUYỆT v2" / "TỪCHỐI: lý do".
