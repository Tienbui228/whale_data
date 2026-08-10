# APRUSDT — Audit-Collect Report
**Date:** 2026-08-10  |  **Operator:** whale-data-operator  |  **Status:** OPEN — DỪNG CHỜ ĐỌC

---

## Case question
> "Có lực gom không? Nếu có: gom từ bao giờ, bao nhiêu (§3), pha nào vòng đời?  
> Nếu không: farm hay xác hay bàn-vừa-lau?"

---

## A-0. Định danh

| Field | Value |
|-------|-------|
| Symbol perp | APRUSDT |
| onboardDate | 2025-10-23 10:30 UTC |
| contractType | PERPETUAL |
| status | TRADING |
| Alpha token | **KHÔNG** (G3 FAIL — not in BAPI/alpha_id_map) |
| APR* variants | NONE — single identity, không cần disambiguation |
| MM_ID | N/A (not Alpha) |
| LSR live API | **ALL 404** — không có LSR endpoint cho symbol này |

**Nguồn LSR thay thế:** freshwatch_daily_2026-06/07/08.csv → 65 dates (2026-06-01 → 2026-08-07).

---

## A-3a. Triage bộ ba

### div_avg3 (top-trader position / account ratio)

| Metric | Value |
|--------|-------|
| Last valid | 1.6959 (2026-08-07, 2d ago) |
| Peak (window) | 2.1642 on 2026-08-04 |
| Min (window) | 0.8195 |
| >1.5 streak | 6 ngày liên tiếp (2026-08-02 → 2026-08-07) |

Trend gần đây:
```
2026-07-19: 0.9536   (thấp nhất tháng 7)
2026-07-23: 1.0611
2026-07-29: 1.4678   ↑ tăng mạnh sau 07-24 data gap
2026-08-02: 1.5564   ← vượt 1.5
2026-08-03: 1.8380
2026-08-04: 2.1642   ← đỉnh
2026-08-05: 1.8955
2026-08-06: 1.8302
2026-08-07: 1.6959   ← last known
```
→ Top traders tăng mạnh position bias long từ cuối tháng 7. Cấu trúc hiện tại rõ thiên LONG.

### gLSR (global long/short ratio)

| Metric | Value |
|--------|-------|
| Last valid | 1.1891 (2026-08-07) |
| Slope 5d | 1.4009 (gLSR tăng so với 5d trước — LONG tăng) |
| Recent trend | Giảm từ đỉnh 2.097 (07-19) → đáy 0.849 (08-02) → phục hồi 1.189 |

gLSR biến động mạnh quanh đáy 08-02 (dump -10.82%, OI tăng $2.06M NET). Hiện phục hồi.

### pin_streak (f_avg ∈ [4e-5, 6e-5])

| Metric | Value |
|--------|-------|
| max streak | 25 ngày |
| Total pin days | 135/291 (46.4% lifetime) |
| Current streak | **0** (pin đã kết thúc — f_avg elevated 2+ tuần) |
| Recent f_avg | 0.000076~0.000573 (trên ngưỡng pin 6e-5 từ 07-26) |

Token từng pin rất nhiều (46.4% lifetime) — dấu hiệu funding farm kéo dài. Hiện **không pin**, f_avg đang cao (funding premium tăng = ai đó đang mua perp aggressively).

### Machine classification

```
div_avg3=1.6959 (2d ago, >1.5 nhưng đang giảm từ đỉnh 2.16)
pin_streak=0 (f_avg elevated — không đủ tiêu chí pin)
gLSR=1.1891 trend=↑ (slope5d=1.4009)
→ ANALYSIS
```
Lý do ANALYSIS thay vì GOM-SIDE: div vừa qua đỉnh, pin không active. Cần thêm data điểm 08-08/09 để confirm. Signal hướng GOM nhưng chưa cleanly cross rule.

---

## §3. Analytics

### §3 Q1 — OI delta (accumulation measurement)

**Provenance:** data-source=scratch/apr_oi_hist_20260810.csv (fapi/futures/data/openInterestHist), machine=local, date-range=2026-07-12→2026-08-10, code-commit=hiện tại

| Metric | Value |
|--------|-------|
| Q1_GROSS | $5,793,601 (tất cả ngày ΔOI⁺) |
| Q1_NET | $5,195,431 (ΔOI⁺ trên ngày đỏ/flat) |
| Q1_NET/GROSS | **89.7%** — NET dominant |

Top Q1_NET events (OI tăng khi giá giảm):
```
2026-08-02: +$2,061,687  ret=-10.82%  ← dominates
2026-08-08: +$1,110,614  ret=-2.63%
2026-07-13: +$783,574    ret=-7.83%
2026-08-06: +$527,899    ret=-0.15%
2026-07-17: +$296,273    ret=-3.76%
```
**Q1 đọc:** OI tăng nhất vào ngày đỏ mạnh → ngoài việc short cover, còn có thể là long entry trên dump. Q1_NET/GROSS=89.7% rất cao — pattern gom qua dump.

### §3 Q2 — OI × share

| Metric | Value |
|--------|-------|
| OI latest | $9,677,955 |
| OI max30 | $10,923,763 |
| OI min30 | $8,260,907 |
| OI med30 | $9,377,764 |
| oi_cycle_pos | 0.532 (mid-cycle) |
| UNCALIBRATED | **NO** (max < $18M threshold) |

Q2 calibrated. OI đang ở mid-cycle (0.532) — không đỉnh, không đáy.

### §3 Q3 — VWAP M2 [vw-vol]

**Window:** 2026-07-12 → 2026-08-09 (29d, khớp OI hist)

| Metric | Value |
|--------|-------|
| VWAP M2 | $0.2065 |
| Current close | $0.1991 |
| px vs VWAP | **-3.58%** (dưới VWAP 29d) |

Giá hiện tại nhẹ dưới VWAP. Không phải top, không phải đáy sâu. Bình thường cho token đang trong vùng tích lũy.

---

## ATH / ATL

| Metric | Value |
|--------|-------|
| ATH | $0.75 (2025-10-24, ngày 2 sau launch) |
| ATL | $0.0624 (2026-02-06) |
| Current | $0.1991 |
| vs ATH | **-73.45%** |
| vs ATL | **+219.28%** |

ATH tại launch + 1d → token dump mạnh từ đầu. Recovery 219% từ ATL là đáng kể — có multiple pump cycles phục hồi.

---

## Phase context — Vòng đời

### Vol spikes ≥8× med14 (L-15 candidates)

| Cluster | Dates | Peak vol | Peak ret | Notes |
|---------|-------|----------|----------|-------|
| C1 | 2025-12-20 | 8.7× | +16.2% | Mini pump |
| C2 | 2026-02-15 | 8.3× | +2.6% | Bounce from ATL |
| **C3** | 2026-03-14→20 | **58.4×** | +29.0% | Massive pump cluster |
| C4 | 2026-04-06 | 10.7× | +5.7% | Reload |
| **C5** | 2026-04-14→15 | **20.2×** | **+66.5%** | Đỉnh lớn nhất → -27.6% dump |
| **C6** | 2026-05-18→19 | **51.0×** | +19.9% | Pump lần 3 |
| **C7** | 2026-06-02→03 | **22.4×** | **+41.0%** | Pump lần 4 → GOM-C bắt đầu |

**Phase timeline:**
```
Oct 23: Launch $0.625
Oct 24: ATH $0.75
Oct→Feb: Crash -92% → ATL $0.062
Feb 6:  ATL
Feb→Mar: Recovery + C2/C3 pumps (Mar 14: 58× vol!)
Apr 14: C5 pump +66.5% → đỉnh local $0.326
Apr 15→: Dump -27.6%
May 18: C6 pump +19.9%
Jun 2:  C7 pump +41.0% → $0.244
Jun→Aug: Gradual decline + GOM-C signals
Aug 10: Current $0.197
```

**Pha hiện tại:** Post-C7 correction. Token đang trong vùng $0.19-0.23 sau cluster pumps Jun. GOM-C signals bắt đầu từ Jun 2 (sau C7 pump). Red-day dominant gần đây (18/30 đỏ).

---

## GOM-C rechấm (C2_quiet ∧ C3_lax ∧ d_pos)

**Spec:** C2 = |f_avg| ≤ 2×1e-4, C3 = taker ∈ [40%, 55%], d_pos = Δpos_r ≥ 0  
**C1 = PROVISIONAL** (LSR không có live endpoint — freshwatch data dùng thay thế)

**GOM-C PROVISIONAL: 22 ngày** (2026-06-02 → 2026-08-04)

```
Jun: 02, 04, 05, 06, 12, 13, 14, 16, 18, 23, 24, 29, 30
Jul: 02, 12, 17, 22, 23, 28, 30
Aug: 03, 04
```

Recent (last 15d visible):
```
2026-07-22: C2=PASS C3=PASS d_pos=Y → GOM-C ✓
2026-07-23: C2=PASS C3=PASS d_pos=Y → GOM-C ✓
2026-07-28: C2=PASS C3=PASS d_pos=Y → GOM-C ✓
2026-07-30: C2=PASS C3=PASS d_pos=Y → GOM-C ✓
2026-08-03: C2=PASS C3=PASS d_pos=Y → GOM-C ✓
2026-08-04: C2=PASS C3=PASS d_pos=Y → GOM-C ✓
2026-08-05→09: C2 fail (f_avg 0.000076-0.000573) hoặc d_pos N/A
```

**GOM-C đứt từ 08-05** — f_avg elevated (lên đến 0.000573 ngày 08-09, gấp ~10× neutral).

---

## Verify-tay 5 rows (A.5 — guard-câm workaround)

**Guard-câm status:** KHÔNG CÓ — build exit=0, xlsx close khớp CSV 100%.

| date | open | high | low | close | ret_1d | vol_usd | taker |
|------|------|------|-----|-------|--------|---------|-------|
| 2026-08-05 | 0.1856 | 0.2135 | 0.1817 | 0.1953 | +5.23% | $3,920,452 | 48.5% |
| 2026-08-06 | 0.1955 | 0.2028 | 0.1911 | 0.195 | -0.15% | $1,973,192 | 52.3% |
| 2026-08-07 | 0.1949 | 0.2254 | 0.1869 | 0.2127 | +9.08% | $5,079,682 | 51.0% |
| 2026-08-08 | 0.2125 | 0.2148 | 0.2009 | 0.2071 | -2.63% | $9,520,865 | 49.5% |
| 2026-08-09 | 0.207 | 0.2295 | 0.1951 | 0.1991 | -3.86% | $4,382,550 | 48.6% |

Vol 08-08 bất thường cao ($9.5M, ~2× ngày khác). Cần chú ý.

---

## Depth snap #1

**Time:** 2026-08-10 03:42 UTC  
**Mid:** $0.19755  |  **Spread:** 0.0506%

| Band | Bid $ | Ask $ | Ratio B/A |
|------|-------|-------|-----------|
| ±0.5% | $10,998 | $12,515 | 0.879 |
| ±1.0% | $20,875 | $18,208 | 1.146 |
| **±2.0%** | **$47,293** | **$28,879** | **1.638** |
| ±5.0% | $106,593 | $60,947 | 1.749 |

**BID-HEAVY** trên tất cả bands từ ±1%. Depth mỏng (tổng ±2%: $76K).  
**Snap #2 gate: ≥07:42 UTC 2026-08-10**

---

## Sổ chéo (A-6)

- **agent_log:** 17 mentions — APR trong "16 OPEN chains" (08-09); GOM-A fire 08-06 ($527K OI delta, scan có sẵn)
- **FW freshwatch:** 65 rows (Jun-Aug 07) — đang được track
- **gom_scan.csv:** không tìm thấy
- **CASE_INDEX:** chưa registered (đã đăng ký trong A-8)
- **Alpha store:** 0 rows (correct — not Alpha)
- **APR* variants in FW:** none

---

## Sanity (A-7)

| Check | Result |
|-------|--------|
| S1: Klines row count | **PASS** (291/291) |
| S2: Identity lock | **PASS** |
| S3: LSR+OI overlap | **PASS** |
| S4: CASE_APR.xlsx rows | **PASS** (291/291) |
| S5: No variants contamination | **PASS** |
| S6: Verify-tay | **PASS** (close khớp 5/5) |

**6/6 PASS**

---

## CASE_INDEX registration

Row 20: CASE_APR.xlsx | APR | OPEN | GOM-C 22ngay PROVISIONAL | COLD_START | 2026-08-10  
moc_ke_tiep: depth snap#2 ≥07:42 UTC; GOM-C C1 gate 15/08

---

## CẦN OPERATOR

1. **BscScan on-chain:** Không thể gọi Nansen. Operator cần kiểm tra:
   - Top holders APR (contract N/A — APR là perp-only, không có token on-chain Binance track)
   - Note: APR không phải Alpha → không có BSC contract để check "rút-trước-nạp-sau"
   - Nếu có native token trên chain khác: operator cần xác nhận và cung cấp contract

2. **Venue top (L-30):** Bitget/Gate có APRUSDT perp không? Vol ratio Binance vs venue khác?

3. **Snap #2:** Thu thập ≥07:42 UTC 2026-08-10 (cần ≥4h sau snap1)

4. **GOM-C C1 gate:** Verify 15/08/2026 — cần live LSR calibration (endpoint 404 hiện tại)

5. **div_avg3 08-08/09:** freshwatch chỉ có đến 08-07. Cần data 08-08/09 để confirm xu hướng div_avg3 (đang giảm từ đỉnh 2.16 về 1.70)

6. **Verdict:** KHÔNG điền — operator quyết định

---

## Tóm tắt kỹ thuật (không verdict)

**Positives:**
- GOM-C 22 ngày PROVISIONAL (Jun→Aug 4) — số lượng lớn, pattern nhất quán
- Q1_NET/GROSS=89.7% — OI tăng chủ yếu trên ngày đỏ
- div_avg3 >1.5 liên tục 6 ngày (Aug 2-7) — top traders thiên long mạnh
- Depth snap BID-HEAVY (ratio 1.638) — buyer support hiện tại
- OI calibrated, mid-cycle (0.532)
- Recovery từ ATL +219% qua nhiều pump cycles

**Negatives/Questions:**
- ATH tại launch — token chưa bao giờ vượt launch price
- 7 pump clusters nhưng giá không tích lũy cao hơn — mỗi pump đều bị sell
- post-Jun 3: 18/30 ngày đỏ
- f_avg elevated từ 07-26 — pin đứt, ai đó đang pay premium mua perp
- LSR endpoint 404 — không thể verify live, phải dùng freshwatch (stale 2d)
- Depth rất mỏng ($47K bid trong ±2%) — dễ moved

**Câu hỏi mở:** Vol 08-08 spike $9.5M (2× ngày khác, taker 49.5%) — cần context: có event nào trigger không?

---

*[A-0→A-8 DONE | DỪNG CHỜ ĐỌC | KHÔNG VERDICT]*
