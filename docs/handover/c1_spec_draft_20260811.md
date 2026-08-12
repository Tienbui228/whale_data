---
topic: C1 stealth_grind — spec thành văn (FINAL v2)
purpose: Operator ký ≤14/08 → gate C4 15/08
deadline: 14/08/2026 (đường găng gate 15/08)
author: Agent claude-sonnet-4-6
confirmed: 2026-08-12
---

# C1 stealth_grind — Spec thành văn (FINAL v2 — sẵn sàng operator ký)

## Số hiện hành — đã xác nhận

Từ `scanner/screener/thresholds.yaml` (calibrated P0-close 2026-07-28), runtime-confirmed commit 4606b86b:

| Tham số | Giá trị hiện hành | Gốc P0 lock | Lý do thay đổi |
|---------|------------------|-------------|----------------|
| `breakout_pct` | **0.09** | 0.15 | TUT chỉ 9.7% trên range — relaxed để bắt TUT |
| `oi_mult` | **1.3** | 1.5 | TUT OI đỉnh 1.47×med14 — relaxed để bắt TUT |
| `breakout_days` | 5 | 5 | không đổi |
| `taker_buy_max` | 55.0 | 55.0 | không đổi |

0.09/1.3× là **canonical hiện hành** (runtime-confirmed). Comment cũ 0.15/1.5 = STALE (fix commit 4606b86b).

**Ngưỡng review v-tiếp (không block ký):** calibrate lại 0.09/1.3× khi có ≥2 case đối chứng mới sau TUT. Ghi nhận tồn đọng — không reopen C1.

---

## C1 — Bản thành văn (verified từ code scanner/screener/signals.py:392-436)

> **C1: stealth_grind(days, i)**
>
> Điều kiện "gom bằng grind" — giá breakout nhẹ từ nền tích lũy, OI surge nhưng taker kiểm soát.
>
> **Định nghĩa:**
>
> Cho:
> - `B = days[i−4 .. i]` — **build window** (5 ngày cuối, inclusive; `range(i−4, i+1)`)
> - `R = days[i−18 .. i−5]` — **range window** (≤14 ngày, min 7; guard `len(R) < 7` → FALSE)
>   (cụ thể: `range_end = i − breakout_days = i − 5`; `_window(days, range_end, 14, field)`)
> - **B và R không chồng lấp (L-24 guard):** R kết thúc tại i−5, B bắt đầu tại i−4 — không có ngày chung.
> - `range_hi = max(avg_px trong R)`, `range_lo = min(avg_px trong R)`
> - `target = range_hi × (1 + breakout_pct)`  (breakout_pct = **0.09**)
> - `median14_oi = median(oi_usd trong R)` — **cùng window R** (i−18..i−5), KHÔNG phải 14d kết thúc tại i
>   (code: `_median14(days, i − brk_days, "oi_usd")` = `_window(days, i−5, 14, "oi_usd")` ✓)
>
> **C1 = TRUE** khi tất cả đồng thời:
>
> **(i) Price breakout (existential trên B):**
>   Tồn tại ≥1 ngày j ∈ B sao cho `avg_px[j] ≥ target` (NaN bỏ qua)
>   *(i ∈ B nên vế "avg_px[i] ≥ target" đã gồm trong existential — không tách riêng)*
>
> **(ii) OI surge (≥1 ngày trong B):**
>   Tồn tại ≥1 ngày j ∈ B sao cho:
>   `oi_usd[j] ≥ oi_mult × median14_oi`  (oi_mult = **1.3**)
>   (median14_oi lấy trên R — cùng window với range_hi/lo, không bao gồm B)
>
> **(iii) Taker constraint (max-over-valid trên B — Option A permissive):**
>   Lọc B: `tb_valid = {j ∈ B : taker_buy_pct[j] không NaN}`
>   `max(taker_buy_pct[j] for j ∈ tb_valid) < taker_buy_max (= 55.0)`
>   Taker = CONTROL phân biệt grind vs pump — NaN không được quyết ngầm:
>   - Option A (code hiện hành): bỏ NaN, max trên phần valid; nếu tb_valid rỗng → C1 FALSE
>   - Option B (conservative): bất kỳ NaN trong B → C1 FALSE *(không áp dụng hiện tại)*
>
> **C1 = FALSE** khi:
> - `i < breakout_days (= 5)` — không đủ lịch sử
> - `len(R) < 7` — range window quá ít điểm
> - `range_lo ≤ 0` — giá không hợp lệ
> - `avg_px[i] = NaN` — giá ngày i không có (early-exit; j=i trong existential cũng NaN-filtered)
> - `median14_oi ≤ 0 hoặc NaN` — OI baseline vỡ; 1.3×0=0 trivially true → silent-pass → FALSE
> - `tb_valid rỗng` (toàn bộ B không có taker data hợp lệ) → C1 FALSE

---

## Trạng thái xác nhận

- [x] Số canonical 0.09/1.3× — runtime-confirmed (commit 4606b86b), không reopen
- [x] Structural: range_end, OR-check, taker-max-window — verified từ signals.py:392-436
- [x] B/R non-overlap — confirmed: R[i−18..i−5] → B[i−4..i], không chồng lấp (L-24 guard)
- [x] median14_oi = R window — verified: `_median14(days, i−5, "oi_usd")` = `_window(days, i−5, 14, ...)` = i−18..i−5 ✓
- [x] iii-TAKER: "where valid" khôi phục + chọn Option A (permissive, code hiện hành) + tb_valid=∅ → FALSE
- [x] ii-OI GUARD: `median14_oi ≤ 0/NaN → FALSE` thêm vào FALSE-cases (song song range_lo ≤ 0)
- [x] nhỏ-(a): R = "≤14 ngày, min 7" (guard len<7 đã ghi)
- [x] nhỏ-(b): vế thừa `avg_px[i] ≥ target` bỏ — existential trên B (i∈B) đã gồm
- [ ] **Operator ký — deadline 14/08/2026**

Sau khi operator ký → agent cập nhật gom_detect_spec.md §1.3 C1 row + xóa [PROVISIONAL] + §6 nếu số thay đổi.
