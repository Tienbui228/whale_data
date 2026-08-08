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

## 3. Điều kiện GOM-C (ĐÃ KÝ PROVISIONAL-β, operator 2026-08-08)

```
GOM-C_β = C1 AND C2_quiet AND C3_lax AND d_pos≥0
           AND NOT(slope>1.15 sustained ≥3d) AND NOT any_supp_dq
```

| Tín hiệu | Ký hiệu | Định nghĩa đã ký | Ghi chú |
|---|---|---|---|
| Stealth grind | C1 | `stealth_grind(days, i, cfg)` | Encodes taker<55% trong build window |
| Funding quiet | C2_quiet | single-day: `f_avg ≤ max(2×rate_min, 1e-4) = 1e-4` | **Thay** funding_pinned-window (Q1-decision) |
| Taker lax | C3_lax | `taker_buy_pct ∈ [40, 55]` per-day | **Thay** absorption strict (Q3-decision) |
| pos_r guard | d_pos≥0 | `lsr_pos[i] ≥ lsr_pos[i-1]` | Guard L-19 chính — bắt harvest (Q2-decision) |
| Slope-close | C4 demoted | NOT(slope>1.15 cho ≥3 ngày liên tiếp) | Đổi vai: chỉ đóng chuỗi khi dai dẳng (Q2) |
| Guard | NOT supp | Không có dist_wall/lsr_dist/decay/post_climax/funding_extreme | Giữ nguyên |

**Q1 (C2):** Dùng single-day `f_avg ≤ 1e-4` — funding_pinned window 7d trộn ngữ cảnh pre-grind → gây miss 14-15/07. Continuity lo bởi §8 break-≤2d rule khi implement full chain.

**Q2 (C4):** d_pos≥0 là guard bắt buộc sắc hơn slope: TUT 17-18/07 slope>1.15 nhưng pos_r leo (build thật) → không block; BANK pos_r drop → d_pos<0 block ngay. C4 slope chỉ đóng chuỗi khi >1.15 sustained ≥3 ngày.

**Q3 (C3):** C3_lax (40-55%): C1 stealth_grind đã encode taker<55% trong window; C3 là continuation check. Band absorption 44-50.5% là chữ ký SIDEWAY không phải grind. Fence trên giữ nghiêm: ngày taker≥55% không đếm vào chuỗi.

---

## 4. Backtest — trạng thái sau G1→G6

- [x] TUT: GOM-C fires 07-13 (entry) và 07-21→23 (peak) — **PASS** (G1)
- [x] BULLA: GOM-C blocked (C2=False) — **PASS** (G3: thuộc GOM-B territory)
- [x] BANK: pos_r harvest xác nhận — close rule-iv đúng ngày (G4)
- [ ] BANANAS31 negative test: **INCONCLUSIVE** (data SUSPECT 07-24→07-26) → re-test 15/08
- [ ] COOKIE/CYS/TST: 3 token mới fire 08-07 → cần verify archetype

---

## 5. Trạng thái — PROVISIONAL-β (08/08/2026)

**ĐÃ KÝ PROVISIONAL-β — deploy display-only**

Implement: `_gomc_beta_check()` trong `gom_scan.py`, output `━━ GOM-C β (N fires)`.
- 08-07: **4 fires** — COOKIE, CYS, TST, TUT
- State: display only, không tạo chain, không ghi state.json
- **Sign-off cuối chờ G2 negative test re-run 15/08** (luật gate §6: cần đủ positive+negative)

**Sau sign-off đầy đủ:**
- Thêm chain tracking cho GOM-C (mở/đóng chương)
- §8 continuity rule (break ≤2d)
- Q2 metric: `seat_rot_index` thay Q1_cum (vì Q1=0 toàn bộ seat-rot builds)
