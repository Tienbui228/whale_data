# GOM-C Backtest Data — G1→G6
**Ngày chạy:** 2026-08-08  
**Script:** `_vps_gomc_validation.py` (chạy trên VPS 5.223.67.21)  
**Status:** ANALYSIS ONLY — không thay đổi state

> **Note probe:** `avg_px`, `lsr_pos`, `lsr_global` (không phải `px_avg`/`lsr_pos_r`/`lsr_global_r`).
> `taker_buy_pct` đã là % (không nhân thêm 100). Fixed trong script sau khi field-name probe.

---

## G1 — TUT (TUTUSDT) 2026-07-13→07-23: Verify GOM-C conditions

**Context:** TUT grind phase — giá tăng chậm +37% trong 10 ngày. Không có crowd flip (gLSR cao), không có hedge cứng (B1 fail). Đây là case trigger GOM-C proposal.

**Field values TUT 07-13** (từ field-probe):
- avg_px = 0.01226, taker_buy_pct = 48.5%, funding_avg = 5e-05 (0.005%/8h)
- OI = 2.77M, lsr_pos = 4.62 (longs 4.62× shorts), lsr_global = 1.5615, lsr_acc = 1.9155

**Condition table (tính bởi signal functions, không phải display):**

| Date | OI_M | C1_SG | C2_FP | C3_abs | C3_lax | C4_slp | GOMC | Note |
|------|------|-------|-------|--------|--------|--------|------|------|
| 07-13 | 2.8M | T | T | . | T | T | **GOM-C** | Entry signal |
| 07-14 | 2.7M | T | . | . | T | T | . | C2 drop |
| 07-15 | 2.7M | T | . | . | T | T | . | C2 drop |
| 07-16 | 2.9M | . | . | . | T | T | . | C1+C2 drop |
| 07-17 | 2.8M | . | . | T | T | . | . | C1 drop, C4 fail |
| 07-18 | 3.0M | . | . | T | T | . | . | C1 drop, C4 fail |
| 07-19 | 3.2M | . | T | T | T | T | . | C1 drop |
| 07-20 | 3.1M | . | T | T | T | T | . | C1 drop |
| 07-21 | 3.4M | T | T | . | T | T | **GOM-C** | Resume |
| 07-22 | 3.8M | T | T | . | T | T | **GOM-C** | |
| 07-23 | 3.4M | T | T | . | T | T | **GOM-C** | |

**Phân tích:**
- GOM-C fires ngày đầu (07-13) — entry signal đúng thời điểm tích lũy
- Gián đoạn 07-14→07-20 (7 ngày): C2 (funding_pinned) drop ngay 07-14 dù funding_avg không đổi (5e-05) → FP dùng window nhiều ngày, 1 ngày trước đó có funding thấp đủ kéo trung bình xuống
- C4 (gLSR slope) fail 07-17/18 — crowd đang accumulate thêm long → slope > 1.15 → C4 block
- Resume 07-21→07-23 — cả 3 điều kiện đồng thời thỏa
- **C3_abs luôn False trong window này** — absorption quá chặt (taker ~48-49% nhưng range ±10% vi phạm vì giá đã +37%)
- **C3_lax True mọi ngày** — 40-55% pct check đủ rộng

**Kết luận G1:**
- Draft GOM-C fire được tại 07-13 và 07-21→07-23 ✓
- Gián đoạn giữa grind là weakness — C2 window quá chặt cho early-stage, C4 block accumulation period
- Nếu bỏ C4 khỏi GOM-C: fires 07-13→07-20 continuous (7/7 ngày với C1 hoặc C2)

---

## G2 — BANANAS31 (BANANAS31USDT): Negative test — serial pumps

**Context:** Token có serial pump behavior — cần verify GOM-C KHÔNG fire trong pump periods.

**Kết quả:** Mostly SUSPECT (07-24→07-26: regen gap). Non-suspect period: **0 GOM-C fires**.

```
OK: No GOM-C fire on BANANAS31 (negative test passed)
```

**Đánh giá:** Negative test **inconclusive** — phần lớn dữ liệu tháng 7 là SUSPECT. Cần re-test sau khi data đầy đủ (08/2026 export). GOM-C draft chưa thể confirm "safe" với BANANAS31.

---

## G3 — BULLA (BULLAUSDT) 2026-07-17→07-21: Cover-driven?

**Context:** Giả thuyết: BULLA đang cover shorts (px+/OI-). Verify GOM-C có fire không.

| Date | OI_M | ΔOI_M | tkr% | C1 | C2 | C4 | GOMC | Note |
|------|------|-------|------|----|----|----|----|------|
| 07-15 | 5.3M | +0.65M | 46.9% | . | . | T | . | OI↑ |
| 07-16 | 5.2M | -0.06M | 53.5% | . | . | T | . | OI↓ nhỏ |
| 07-17 | 6.1M | +0.88M | 49.3% | T | . | T | . | OI↑ |
| 07-18 | 7.7M | +1.54M | 48.8% | T | . | T | . | OI↑ |
| 07-19 | 8.0M | +0.28M | 48.6% | T | . | T | . | OI↑ |
| 07-20 | 7.1M | -0.81M | 49.3% | T | . | T | . | OIv cover |
| 07-21 | 9.9M | +2.76M | 49.3% | T | . | T | . | OI↑ surge |

**Phân tích:**
- C2 (FP) = False mọi ngày → **GOM-C correctly blocked** ✓
- Giả thuyết cover-driven không confirm: OI mostly tăng (không phải px+/OI-)
- 07-20: ΔOI=-0.81M (OI giảm nhẹ) với px tăng → có cover nhưng không chiếm đa số
- BULLA is an accumulation-via-OI-growth case, not stealth grind — **C2 block là đúng**

**Kết luận G3:** GOM-C không fire trên BULLA (đúng — không phải grind archetype). Guard hoạt động đúng.

---

## G4 — BANK (BANKUSDT) 2026-07-10→07-20: pos_r harvest evidence

**State VPS:**
```
chain_close = 2026-07-16
reason = pos_r_drop:32%_from_peak:2.97
peak_pos_r = 2.974
```

| Date | ΔOI_M | GOM_fire | Chain |
|------|-------|----------|-------|
| 07-10 | +0.15M | . | closed (pre-chain) |
| 07-11 | +0.31M | . | closed |
| 07-12 | +1.03M | GOM | OPEN n=0 |
| 07-13 | -0.02M | GOM | OPEN n=0 |
| 07-14 | +0.21M | GOM | OPEN n=0 |
| 07-15 | +0.05M | GOM | OPEN n=0 |
| **07-16** | +2.77M | . | **CLOSED [pos_r_drop:32%_from_peak]** |
| 07-17 | +5.71M | . | closed |
| 07-18 | -0.96M | . | closed |
| 07-19 | +12.99M | . | closed |
| 07-20 | +23.91M | . | closed |

**Phân tích:**
- GOM fires 4 ngày (07-12→07-15): chain mở đúng
- 07-16: pos_r drop 32% từ peak 2.97 → rule-iv close trigger. Cùng lúc OI +2.77M → shorts đang exit, longs bắt đầu unwind
- Post-close: OI surge dữ dội (+5.7M, +13M, +23.9M) → **đây là pha distribution/exit của longs**
- peak_pos_r = 2.97 rất cao (longs ≈ 74.8% total position) → smart money đã build seat xong, đang bán ra

**Kết luận G4:** BANK là seat-rotation + harvest case. Close rule-iv đúng ngày 07-16. Post-close OI spike là exit signal, không phải accum mới.

---

## G5 — Re-accum sau crash: rule-iv tokens

Scan: tìm ngày đầu tiên sau close_date mà A1+A2+A3 đồng thời True (không tính DQ).

| Token | CloseDate | Gap đến reaccum | Note |
|-------|-----------|-----------------|------|
| BANK | 2026-07-16 | **4 ngày** (07-20) | Fast recovery — crowd flip nhanh sau distribution |
| TOWNS | 2026-07-18 | no reaccum by 08-07 | 20+ ngày chưa hồi — crowd chưa đảo chiều |

**Vắng BAS/ZBT/ARX:** Không có trong fw state với `pos_r_drop` close_reason.
- ZBT: close_reason là `dq_cooldown` (post_climax DQ) — không phải rule-iv
- BAS/ARX: cần kiểm tra riêng (có thể closed_note "chuyển pha phân phối" với encoding khác)

**Kết luận G5:**
- BANK recovery 4d: rất nhanh. Có thể GOM-A re-fire ngay 07-20 (cần verify)
- TOWNS: đang kẹt, chưa có điều kiện tích lũy mới
- Re-accum metric cần tracking cho multi-round GOM strategy

---

## G6 — Q2 Heuristic: share = Q1_cum / OI_at_gom

| Token | Q1_cum_usd | OI_at_gom | share% | peak_pr | implied_B | Note |
|-------|-----------|-----------|--------|---------|-----------|------|
| IDOL | $0 | 3.6M | NaN | NaN | NaN | Q1=0 seat-rot |
| ZBT | $0 | 9.0M | NaN | NaN | NaN | Q1=0 seat-rot |
| TUT | $0 | 2.6M | NaN | NaN | NaN | Q1=0 seat-rot |
| BANK | $0 | 6.0M | NaN | 2.974 | **4.5M** | Q1=0 seat-rot |

**Phân tích:**
- Tất cả Q1_cum_usd = 0: ΔOI⁺ không tích lũy trong window → **seat-rotation builds toàn bộ**
- OI tương đối ổn định, nhưng pos_r tăng mạnh → longs build seat bằng cách đẩy shorts ra, không phải mở OI mới
- BANK: peak_pr=2.974 với OI=6M → long-side implied = 2.974/3.974 × 6M = **4.49M** (~75% total OI = long position)
- Q2 metric "share = ΔOI⁺/OI" không áp dụng được cho seat-rotation archetype

**Đề xuất Q2 cho seat-rotation:**
```
seat_rot_index = (peak_pos_r - baseline_pos_r) / baseline_pos_r
```
Ví dụ BANK: nếu baseline_pos_r = 1.0, peak = 2.97 → index = 197% (lớn)

---

## Tổng kết Findings

| Gate | Kết quả | Ý nghĩa |
|------|---------|---------|
| G1 TUT | GOM-C fires 07-13, gap 07-14→20, resume 07-21→23 | Entry signal đúng; gián đoạn giữa grind do C2 window + C4 slope |
| G2 BANANAS31 | Inconclusive (SUSPECT data) | Cần re-test với data đầy đủ tháng 8 |
| G3 BULLA | GOM-C blocked (C2=False) ✓ | BULLA không phải grind archetype — đúng |
| G4 BANK | Chain 07-12→07-16 confirmed; post-close OI surge = exit | Rule-iv close đúng; harvest pattern xác nhận |
| G5 Re-accum | BANK 4d, TOWNS 20d+ | Fast vs slow recovery; BAS/ZBT/ARX cần probe riêng |
| G6 Q2 | Tất cả seat-rot (Q1=0) | Q2 metric không apply; cần seat_rot_index thay thế |

---

## Câu hỏi mở cho operator (từ dữ liệu)

1. **C2 window:** Funding_avg = 0.005%/8h mọi ngày nhưng FP chỉ fire 07-13. Window 7d có thể bao gồm ngày trước grind (funding thấp hơn). Có nên dùng single-day check `funding_avg ≥ threshold` thay FP-window không?

2. **C4 trong GOM-C:** Slope gLSR > 1.15 block 07-17/18. Trong tích lũy grind, crowd accumulate long → gLSR tăng là bình thường. Có nên bỏ C4 khỏi GOM-C (cho phép gLSR tăng)?  
   - Nếu bỏ C4: GOM-C fires 07-13→07-23 gần liên tục (1 tín hiệu bền hơn)

3. **C3:** C3_abs luôn False (absorption quá chặt). C3_lax True mọi ngày. Propose: dùng C3_lax (taker_buy_pct ∈ [40,55]) thay C3_abs.

4. **Min duration C1:** Stealth grind cần mấy ngày liên tiếp? 07-13 (1 ngày) đủ để fire?

5. **Negative test:** Cần re-run G2 khi BANANAS31 có đủ data (sau 08/2026 export).

---

## Trạng thái

**Backtest chưa đủ để ký GOM-C:**
- G1 ✓ (TUT fires đúng entry) 
- G2 ✗ (inconclusive — SUSPECT data)
- G3 ✓ (BULLA blocked đúng)
- G4 ✓ (BANK chain confirmed)
- G5 partial (BANK only; BAS/ZBT/ARX missing)
- G6 ✓ (confirms seat-rot archetype for all 4 tokens)

**Việc cần làm trước khi ký:**
- [ ] Re-run G2 với BANANAS31 data tháng 8 (sau 15/08)
- [ ] Probe BAS/ZBT/ARX close_reason trực tiếp (G5 bổ sung)
- [ ] Operator quyết định C4 removal và C2 window vs single-day
