# _collect_btw_20260810.md
## BTWUSDT — Án tích refresh + CASE_BTW.xlsx (calib #6, S5 SUPPRESSED từ 20/07)

**Ngày:** 2026-08-10  |  **Operator check:** DỪNG chờ đọc — không verdict

---

## PROVENANCE (L-48)

| Trường | Giá trị |
|--------|---------|
| data-source | scratch/btw_klines_20260810.csv · btw_funding_20260810.csv · btw_oi_hist_20260810.csv (fapi.binance.com); freshwatch_daily_*.csv (local scratch); data/raw/spot_klines_1d (alpha store) |
| machine | local scratch (D:\Data back test\whale_data\scratch) — KHÔNG swap lên VPS |
| date-range | 2026-06-05 → 2026-08-09 (klines L-21 cutoff) |
| code-commit | (commit này) |

---

## A.5 MACHINE-FILL XÁC NHẬN

- **CASE_BTW.xlsx:** 7 sheets — CASE, DAILY, EVENTS, TRIGGERS, OUTCOME, MM_PROFILE, UNLOCK ✓
- **DAILY:** 66 rows × 50 cols (Jun 5 → Aug 9) — L-32 PASS ✓
- **Build exit:** 0 (build_case.py BTWUSDT 20260810)
- **GOM-A fires:** 5 (2026-06-19, 20, 21, 07-03, 07-13)
- **GOM-B fires:** 0
- **LSR source:** freshwatch_daily_*.csv (fapi 404 — perp <30d + MISSING khoảng Jul)
- **Alpha vol:** store forward từ 04/08, taker=ABSTAIN (L-48)
- **Spot:** NO spot pair (no spot klines)
- **OI flag:** UNCALIBRATED ✓ (max $48.8M > $18M)

---

## W-3 TRIAGE BỘ BA

| Metric | Giá trị hiện tại | Trend | Threshold | Status |
|--------|-----------------|-------|-----------|--------|
| div_avg3 | **2.3669** (Aug 7-8) | Δ−0.007/day | ≥1.0 bull | HIGH_LONG |
| gLSR | **0.7995** (Aug 7) | slope_5d −0.086↓ | >1.0 bull | BEAR |
| f_avg_3 | **0.000832** | — | [4e-5, 6e-5] | NOT_PIN (14×) |
| d_pos_28d | **+0.0504** | Jul 10→Aug 7 | >0 rising | RISING |

**neg_div window:** Jul 22–30 (6 ngày, min 0.7979 vào Jul 28) → ĐÃ CLEAR từ Jul 31.
**flag_neg_div suppressor:** FALSE (hiện tại).

### div_avg3 detail (last 10 ngày có data FW):
```
Jul 28: 0.7979 ← NEG
Jul 29: 0.8736 ← NEG
Jul 30: 0.9603 ← NEG (cleared next day)
Jul 31: 1.1334
Aug 01: 1.1858
Aug 02: 1.2328
Aug 03: 1.3426
Aug 04: 1.4651
Aug 05: 1.7849 ← >1.5
Aug 06: 2.0152 ← >1.5
Aug 07: 2.3739 ← >1.5  ← ĐỈNH CÓ DATA
```

---

## W-3 TRIGGER-CHECK 3 ĐIỀU KIỆN ĐỒNG THỜI

| Điều kiện | Trạng thái | Detail |
|-----------|-----------|--------|
| C1 Pinned MỚI (f_avg_3 ∈ [4e-5, 6e-5]) | **FAIL ✗** | f_avg_3=0.000832 → 14× above pin range. Funding HOT toàn Aug. |
| C2 Outflow TẠI NỀN (d_pos_28d<0 ∧ div↓) | **FAIL ✗** | d_pos_28d=+0.05 (RISING). div_avg3 đang đỉnh. |
| C3 Pos re-rate MỚI (div↑ mới ∧ gLSR↑) | **FAIL ✗** | div_avg3 đang đỉnh/giảm nhẹ. gLSR=0.7995 BEAR↓. |

**SCORE: 0/3 → KHÔNG TRIGGER. Ba điều kiện KHÔNG thỏa ĐỒNG THỜI.**

Án tích đặt câu hỏi: *"3 tuần sau verdict trap: ba điều kiện thức dậy đúng không?"*
→ **Không đúng** — BTW không thức dậy theo kịch bản án tích. Thay vào đó: BLOWOFF 2.0.

---

## §3 Q1 / Q2 / Q3

### Q1 — GOM-A quality

| Date | Vol perp | Taker% | Phase | Note |
|------|----------|--------|-------|------|
| 2026-06-19 | $146M | 50.5% | blowoff | +90% ret ngày — pump stage |
| 2026-06-20 | $756M | 51.3% | blowoff ĐỈnh | vol kỷ lục |
| 2026-06-21 | $482M | 49.1% | blowoff crash | −39.6% ret |
| 2026-07-03 | $16M | 47.9% | decay | vol thấp, ret −0.2% |
| 2026-07-13 | $4.7M | 49.5% | decay | vol thấp nhất |

**Q1 status: UNCALIBRATED** — GOM-A fires nằm hoàn toàn trong blowoff phase (Jun) và decay (Jul). Không có fire mới từ Aug 1+. Agent-log ghi GOM-A live $7.5M ngày 08-08 (retroactive build không có — live vs retroactive divergence).

### Q2 — OI calibration

- OI range (30 ngày): $6.62M → **$48.82M**
- OI latest (Aug 9): $46.86M
- OI med14: $19.26M
- oi_cycle_pos: **0.899** (gần peak 30d range)
- **Q2: UNCALIBRATED** ✗ (max $48.8M > $18M — do pump Aug 6-9)

### Q3 — VWAP M2 + price structure

- VWAP M2 (full lifetime): **$0.0844**
- Px (Aug 9 close): $0.21484 → **+154.57% trên VWAP M2**
- Px live (08:01 UTC Aug 10): **$0.2001** (vừa chạm lại $0.20 — original blowoff level)
- ATH close: **$0.2240** (Aug 7) — NEW ATH, VƯỢT original Jun blowoff
- Drawdown từ ATH: −4.09%

---

## GOM-C STATUS

- **Định nghĩa:** C2_quiet (|f_avg|≤2e-4) ∧ C3_lax (taker∈[40%,55%]) ∧ d_pos (Δpos_r≥0)
- **GOM-C days tổng:** 14 (Jun 5 → Jul 26)
- **Post-cooldown (≥Aug 1):** **0 ngày** — funding > 2e-4 từ Jul 27 trở đi
- **C1 gate:** PROVISIONAL (gate date: 2026-08-15 chưa đến)
- **Status: PROVISIONAL / KHÔNG ACTIVE** — GOM-C bị ngắt bởi funding HOT từ Jul 27

---

## W-4 PHASE LIFECYCLE

### Lifecycle flags (toàn window 66 ngày)

| Flag | Days True | Last 14d | Current |
|------|-----------|----------|---------|
| flag_neg_div | 0 | 0 | False |
| flag_dist_wall | 1 | 0 | False |
| flag_decay | 0 | 0 | False |
| flag_hedge_struct | 0 | 0 | False |
| flag_knife_crowd | 7 | 0 | False |

**oi_cycle_pos:** 0.899 (đỉnh — was 1.000 for Jul 21, 22, 26, 28, 29, Aug 1, 4, 5, 6, 7, 8)

### Price lifecycle

```
ATL (listing ~Jun 4):  $0.0481
Original blowoff:      ~$0.20 (Jun 8-10, $638M vol, funding +0.294%/ngày)
Trap/decay bottom:     $0.052–0.065 (Jun 27 → Jul 26)
DQ cooldown end:       2026-07-31
S5 SUPPRESSED:         từ 2026-07-20
New ATH (Aug 7):       $0.2240  ← VƯỢT original blowoff
Current (Aug 9 close): $0.2148 (−4.09% từ ATH)
Live (Aug 10 08:01):   $0.2001 (+7.4% vs original blowoff $0.20... hoặc AT blowoff)
```

### PHASE VERDICT: **BLOWOFF 2.0** (echo pump / second wave)

Evidence:
- Price vượt original Jun blowoff ATH ($0.224 > ~$0.20)
- Vol Aug 5-9: $85M / $83M / $73M / **$198M** / $101M — blowoff scale
- Funding Aug 5-9: 0.00062 / 0.00075 / 0.00060 / 0.00080 / **0.00109** (8-22× pin range)
- OI: $46.9M, oi_cycle_pos=0.899
- Án tích 3 điều kiện: 0/3 — NOT a recovery, là BLOWOFF

---

## W-5 VENUE + DEPTH SNAP #1

**Snap #1 | 08:01 UTC Aug 10**

| Band | Bid $ | Ask $ | Ratio | Bias |
|------|-------|-------|-------|------|
| ±0.5% | $15,825 | $13,212 | 1.198 | BID |
| ±1.0% | $29,681 | $22,485 | 1.320 | BID |
| ±2.0% | $47,746 | $38,218 | **1.249** | **BID-HEAVY** |
| ±5.0% | $165,231 | $133,786 | 1.235 | BID |

- **Mid:** $0.1988 · Spread: 0.045%
- **Top bid wall:** $21,301 tại $0.1907
- **Top ask wall:** $12,722 tại $0.2050
- **Bias: BID-HEAVY** (buyer support active)
- **Snap #2 gate:** ≥12:01 UTC Aug 10 (CẦN OPERATOR hoặc wakeup)

**Venue audit:**
- Perp: BTWUSDT FAPI ✓
- Spot: KHÔNG có spot pair
- Alpha: ALPHA_778 (BSC, 10B supply, 2.71B circ, 45.2K holders)
- On-chain outflow: **ABSTAIN** (Nansen LOCKED, BscScan = **CẦN OPERATOR**)

---

## W-6 SANITY SUMMARY

| Item | Result |
|------|--------|
| S1 DAILY count (66 rows) | PASS ✓ |
| S2 GOM-A dates (5 fires) | PASS ✓ |
| S3 OI UNCALIBRATED flag | PASS ✓ |
| S4 div_avg3 consistency (Aug 7: 2.3739) | PASS ✓ |
| S5 verify-tay 5 rows (5/5 exact) | PASS ✓ |

**Overall: 5/5 PASS**

---

## W-7 CASE_INDEX

- **CASE_INDEX row 21:** CASE_BTW.xlsx | BTW | COLD_START — PENDING | BLOWOFF2.0 echo; 3-cond trigger 0/3; OI UNCALIBRATED; GOM-C 14d pre-cool | WATCH (án tích refresh) | 2026-08-10

---

## CẦN OPERATOR

1. **BscScan top holders / outflow** — contract 0x444045b0ee1ee319a660a5e3d604ca0ffa35acaa (BSC). Cần check top wallet thay đổi trước/sau pump Aug 5-9.
2. **Depth snap #2** — gate ≥12:01 UTC. Chạy `_probe_btw_5_snap2_20260810.py` (chưa viết — cần sau snap1).
3. **GOM-A live vs retroactive divergence** — agent_log ghi $7.5M Q1 fire ngày 08-08 từ live signals. Build retroactive không có. Operator xác nhận live fire có đúng không?
4. **Verdict/phase call** — Operator read CASE_BTW.xlsx DAILY sheet hậu-án section (từ Jun 20 trở đi).
5. **CASE_INDEX row 10** (placeholder `(hang cho), BTW, du kien CASE-05`) — giữ nguyên hay xóa? Operator quyết.

---

*Build: CASE_BTW.xlsx 66 rows × 50 cols, 5 GOM-A fires, 0 GOM-B. Trigger 0/3. Phase BLOWOFF 2.0. GOM-C 0 ngày post-cool. Snap1 BID-HEAVY 1.249. Sanity 5/5 PASS.*

**DỪNG chờ đọc — không verdict.**
