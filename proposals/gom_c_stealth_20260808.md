# Đề xuất GOM-C: Khuôn Stealth Grind (chờ operator ký)

**Ngày:** 2026-08-08  
**Người đề xuất:** Agent (claude-sonnet-4-6)  
**Án dẫn đến đề xuất:** TUT probe 07-01→07-20 — false-negative có hệ thống

---

## 1. Bằng chứng kích hoạt (probe TUT 07-01→07-20)

Kết quả per-day A1-A5/B1-B4 toàn bộ pha build TUT:

```
Date         A1  A2  A3  A4  A5  B1  B2  B3  B4  Note
2026-07-01   .   .   .   .   .   .   .   .   T   no-chain
2026-07-03   .   .   T   .   .   .   T   .   T   no-chain  ← B2=T, B4=T, nhưng B1=F
2026-07-05   .   .   T   .   .   .   T   .   T   no-chain
...
2026-07-11   .   .   T   .   .   .   T   .   T   no-chain  ← Đây chính là pha SG+FP sống
...
2026-07-13   .   .   T   .   .   .   T   .   T   no-chain
2026-07-19   .   .   T   .   .   .   T   T   T   no-chain  ← B3 bật, vẫn không đủ (B1=F)
2026-07-20   .   .   T   .   .   .   T   T   T   no-chain
```

**Tại sao không bật:**
- A1=False: `lsr_accum` yêu cầu `div_avg3 ≥ 1.5 AND avg5(gLSR) ≤ 1.1`. TUT pha grind: crowd đang LONG (gLSR cao) → avg5(gLSR) > 1.1 → fail.
- A2=False: cùng lý do gLSR.
- B1=False: yêu cầu `all(hedge_structure)` trong 7 ngày liên tiếp = `div_avg3 ≤ 0.5` liên tục. TUT grind không có áp short đủ mạnh đồng đều trong 7 ngày.

Kết luận: TUT không kích hoạt GOM-A (cần crowd đảo chiều) cũng không GOM-B (cần short hedge cứng), dù **SG + FP sống 10+ ngày trong build window**.

---

## 2. Định nghĩa archetype GOM-C: "Gom bằng grind"

**Đặc điểm nhận dạng:**
- Giá tăng từ từ (+30-50%) trong 7-14 ngày — không pumping, không sideways
- Funding pinned dương (longs trả phí, nhưng chưa flip)
- Taker buy <55% — không phải FOMO buy, là accumulation từ từ
- `pos_r` (long position ratio) tăng dần đều — longs đang build seat
- gLSR cao (crowd long) nhưng đây là accumulation của smart money, không phải crowd flush
- Không có distribution signal (post_climax, dist_wall, lsr_dist, decay)

**Khác với GOM-A/B:**
- GOM-A: bắt crowd đảo chiều short → long (A1: div cao, gLSR thấp)
- GOM-B: bắt nén bằng hedge cứng (B1: all-7d short pressure)
- GOM-C: bắt tích lũy bằng drift-up (không cần crowd flip, không cần hedge cứng)

---

## 3. Điều kiện đề xuất GOM-C (chưa ký)

```
GOM-C = C1 AND C2 AND C3 AND C4 AND NOT any_supp_dq
```

| Tín hiệu | Ký hiệu | Định nghĩa đề xuất |
|---|---|---|
| Stealth grind | C1 | `stealth_grind(days, i, cfg)` = True (đã có sẵn trong signals.py, auxiliary) |
| Funding bền | C2 | `funding_pinned(days, i, cfg)` OR `funding_pinned_strong(days, i, cfg)` (= B2) |
| Taker vừa phải | C3 | `absorption(days, i, cfg)` (= B3) — hoặc loose version: taker_buy_pct ∈ [40, 55] |
| Clean | C4 | B4 (`not funding_neg_div`) = đã có |
| Guard | NOT supp | Không có dist_wall/lsr_dist/decay/post_climax/funding_extreme |

**Lưu ý C1:** `stealth_grind` hiện là auxiliary-only trong gom_scan (không phải A2, chỉ display). Cần xác nhận logic `stealth_grind` trong signals.py phù hợp với archetype này.

**Vấn đề cần operator phán xử:**
1. Threshold cho C3: absorption (yêu cầu taker_buy_pct ∈ [44, 50.5] + range ±10%) có thể quá chặt cho drift-up (giá +37% đã vi phạm ±10%?). Cần loose version.
2. Thời gian minimum C1 active: SG cần mấy ngày liên tiếp mới tính?
3. Có cần `pos_r tăng dần` (so sánh pos_r hiện tại vs pos_r 5d trước)?
4. GOM-C có cộng Q1 theo cùng logic (ΔOI⁺)? TUT Q1 sẽ nhỏ vì OI flat — cần metric riêng?

---

## 4. Backtest cần trước khi ký

- [ ] TUT: chạy GOM-C trên 07-03→07-13 (pha SG+FP) → xác nhận fire đúng ngày
- [ ] Kiểm tra false-positive rate: token nào khác sẽ fire GOM-C trong cùng period?
- [ ] Kiểm tra ESPORTS (nếu có trong fw137): archetype tương tự TUT không?

---

## 5. Trạng thái

**CHƯA KÝ — chờ operator phê duyệt**

Operator cần quyết định:
- Có chấp nhận GOM-C như khuôn thứ ba không?
- Nếu có: điều chỉnh threshold nào trước khi implement?
- Nếu không: ghi lý do vào agent_log

**Agent không implement GOM-C cho đến khi có chữ ký operator.**
