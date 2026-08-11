---
topic: C1 stealth_grind — bản thảo spec thành văn
purpose: ANALYSIS xác nhận số canonical + nhả bản cuối → operator ký ≤14/08
deadline: 14/08/2026 (đường găng gate 15/08)
author: Agent claude-sonnet-4-6
date: 2026-08-11
---

# C1 stealth_grind — Draft spec thành văn (chờ ANALYSIS xác nhận)

## Tại sao cần file này

Spec v1.5 §1.3 viết C1 dưới dạng code-pointer:
> `stealth_grind(days, i, cfg)` từ signals.py | Giá tăng chậm +9%+ trên range 14d trong 5d + OI ≥1.3×med14 + taker<55%

Con trỏ này **không đủ tự đứng**: thiếu định nghĩa `range_end`, thiếu OR-check, thiếu taker-max-window.
Gate 15/08 không chấm được C1 nếu người chấm phải giải thích code.

## Số hiện hành — xác nhận trước khi thành văn

Từ `scanner/screener/thresholds.yaml` (calibrated P0-close 2026-07-28):

| Tham số | Giá trị hiện hành | Gốc P0 lock | Lý do thay đổi |
|---------|------------------|-------------|----------------|
| `breakout_pct` | **0.09** | 0.15 | TUT chỉ 9.7% trên range — relaxed để bắt TUT |
| `oi_mult` | **1.3** | 1.5 | TUT OI đỉnh 1.47×med14 — relaxed để bắt TUT |
| `breakout_days` | 5 | 5 | không đổi |
| `taker_buy_max` | 55.0 | 55.0 | không đổi |

Spec v1.5 đang ghi "+9%" và "1.3×" — KHỚP giá trị thresholds.yaml hiện hành. Số trong spec đúng.

**[CHỜ ANALYSIS XÁC NHẬN]:** 0.09/1.3× là semantic intent đã ký, hay ANALYSIS muốn revert về 0.15/1.5×?
Đây là câu hỏi nghĩa-học (dùng TUT làm calibration case = ý định), không phải câu hỏi kỹ thuật.

---

## C1 — Bản thảo thành văn (từ code, agent draft)

> **C1: stealth_grind(days, i)**
>
> Điều kiện "gom bằng grind" — giá breakout nhẹ từ nền tích lũy, OI surge nhưng taker kiểm soát.
>
> **Định nghĩa:**
>
> Cho:
> - `B = days[i−4 .. i]` — **build window** (5 ngày cuối, inclusive)
> - `R = days[i−18 .. i−5]` — **range window** (14 ngày avg_px, kết thúc trước B)
>   (cụ thể: `range_end = i − breakout_days = i − 5`, `_window(days, range_end, 14, "avg_px")`)
> - `range_hi = max(avg_px trong R)`, `range_lo = min(avg_px trong R)`
> - `target = range_hi × (1 + breakout_pct)`   ← **[ANALYSIS XÁC NHẬN: breakout_pct = 0.09]**
>
> **C1 = TRUE** khi tất cả đồng thời:
>
> **(i) Price breakout (OR-check trên window):**
>   `avg_px[i] ≥ target`
>   **HOẶC** tồn tại ≥1 ngày j ∈ B sao cho `avg_px[j] ≥ target`
>   *(không yêu cầu ngày i phải pass; breakout bất kỳ ngày trong 5d là đủ)*
>
> **(ii) OI surge (≥1 ngày trong B):**
>   Tồn tại ≥1 ngày j ∈ B sao cho:
>   `oi_usd[j] ≥ oi_mult × median14(oi_usd tại R)`  ← **[ANALYSIS XÁC NHẬN: oi_mult = 1.3]**
>   (median14 tính trên range window R, KHÔNG bao gồm B)
>
> **(iii) Taker constraint (max trên B):**
>   `max(taker_buy_pct[j] for j ∈ B where data valid) < taker_buy_max (= 55.0)`
>   *(check trên max của window — nếu bất kỳ ngày nào trong B có taker ≥ 55% thì fail)*
>
> **C1 = FALSE** khi:
> - `i < breakout_days (= 5)` — không đủ lịch sử
> - `len(R) < 7` — range window quá ít điểm
> - `range_lo ≤ 0` — giá không hợp lệ
> - `avg_px[i] = NaN` — giá hiện tại không có
> - Không có ngày nào trong B có taker data hợp lệ

---

## Checklist ANALYSIS cần làm

- [ ] Xác nhận: `breakout_pct = 0.09` là ý định canonical (không phải artifact từ TUT calibration)?
- [ ] Xác nhận: `oi_mult = 1.3` là ý định canonical?
- [ ] Review 3 mục structural: range_end, OR-check, taker-max — đúng không, thiếu gì không?
- [ ] Nhả bản C1 cuối (hoặc sửa draft này) để operator ký

Sau khi ANALYSIS xác nhận → agent cập nhật gom_detect_spec.md §1.3 C1 row + conformance row + rerun §6 nếu số thay đổi → operator ký ≤14/08.
