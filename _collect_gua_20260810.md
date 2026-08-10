# COLLECT GUA — GUAUSDT (SUPERFORTUNE / ALPHA_483)
**Date:** 2026-08-10 | **Pipeline:** G-0 → G-8 (snap2 pending ≥15:50 UTC)

---

## PROVENANCE
| Trường | Giá trị |
|--------|---------|
| data-source | fapi.binance.com (klines/funding/OI/depth), CASE_GUA.xlsx, freshwatch_daily_*.csv |
| machine | local scratch D:\Data back test\whale_data\scratch |
| date-range | 2025-12-21 → 2026-08-10 (klines); 2026-06-01 → 2026-08-07 (FW LSR) |
| code-commit | TBD (commit sau session) |
| case-file | docs/case_files/CASE_GUA.xlsx (231 DAILY rows × 50 cols) |

---

## G-0: IDENTITY
- **Symbol:** GUAUSDT (perp only, Alpha; NO spot pair GUABTC/GUABNB)
- **Name:** SUPERFORTUNE
- **Alpha ID:** ALPHA_483
- **Onboard:** 2025-12-21 10:15 UTC
- **Contract:** `0xa5c8e1513b6a08334b479fe4d71f1253259469be` (BSC, chainId=56)
- **Total Supply:** 1,000,000,000 (1B)
- **FW universe:** có trong freshwatch_symbols.txt (u50)
- **FW rows:** 64 (2026-06-01 → 2026-08-07)
- **Live Aug10 (real-time):** +59.62% 24h, $37.2M vol — HOT pump in-progress

---

## G-1: LSR + OI
- **LSR endpoints:** 0/4 FOUND (globalLSR, topAccLSR, topPosLSR, takerLSR → tất cả 404)
  - Fallback: freshwatch_daily_*.csv (64 rows)
- **OI 30d:** $3,768,949 → $5,190,235
  - oi_cycle_pos = 1.000 (AT TOP of 30d range — OI peak khi pump)
  - **UNCALIBRATED: FALSE** (max $5.4M < $18M threshold)
- **OI latest:** $5.19M, med14=$3.97M → oi_vs_med14=1.31×
- **Funding last 3 days:** Aug7=-0.000009 (brief NEG), Aug8=+0.000257, Aug9=+0.001101 (EXTREME HOT)

---

## G-2: KLINES + FUNDING
- **Klines:** 232 rows fetched (Dec22→Aug10), 231 DAILY (L-21: Aug10 partial excluded)
- **Range:** 2025-12-22 → 2026-08-09
- **ATH high:** $1.701 (2026-05-25)
- **ATL low:** $0.0332
- **Funding:** 1,492 rows (Dec21→Aug10)

### KEY EVENTS (vol ≥8× med14 hoặc |ret|>10%):
| Date | Event | ret | vol_usd | vol_vs_m |
|------|-------|-----|---------|----------|
| 2026-02-24 | S1 bậc nạp cluster (ngày 1) | +? | $35M | 9.2× |
| 2026-02-25 | S1 bậc nạp cluster (ngày 2) | +? | $91M | 23.6× |
| 2026-02-26 | S1 bậc nạp cluster (ngày 3) | +? | $92M | 24.1× |
| 2026-02-27 | S1 bậc nạp cluster (ngày 4) | +? | $58M | 15.2× |
| 2026-03-20 | Spike | +? | $49M | 12.7× |
| 2026-04-19 | D4 vol-wake | +? | $71M | 14.6× |
| 2026-05-13 | Pre-ATH staging | +? | $50M | 13.0× |
| 2026-05-16 | Pre-ATH staging | +? | $43M | 11.1× |
| 2026-05-25 | **ATH $1.701** | peak | peak | — |
| 2026-05-27 | **MEGA DUMP 1** | -72.6% | $474M | 10.1× |
| 2026-05-28 | **MEGA BOUNCE** | +119.5% | $331M | — |
| 2026-07-02 | BLOWOFF 2 | -58.6% | $84M | — |
| **2026-08-10** | **TODAY (real-time)** | **+54.92%** | **$34M** | **17.96×** |

---

## G-3: TRIAGE BỘ BA

| Metric | Current | Trend | Threshold | Status |
|--------|---------|-------|-----------|--------|
| div_avg3 | 0.4141 | +0.078 (rising from 0.23) | ≥1.0 bull | **BEAR (<1)** |
| gLSR | 2.8745 | -0.5861 (↓ từ 5.93 Jul29) | >1.0 bull | **VERY BULL (>2)** |
| f_avg_3 | 0.000450 | extreme → today 0.001101 | [4e-5,6e-5] | **NOT_PIN (EXTREME HOT)** |
| d_pos_28d | -0.052 | FALLING | >0 rising | **FALLING** |

**Kết luận bộ ba:** PHÂN KỲ CỨNG — div BEAR (smart money short-biased) trong khi gLSR VERY BULL (retail rất long). Đây là cấu trúc crowd-trap kinh điển: retail nắm long, funding cực cao, smart money ở phía ngược.

---

## LĂNG KÍNH 1 — §3 BUILD-PERP

**Q1 — GOM fires:**
- GOM-A: **0 fires** (GOM-A COLD)
- GOM-B: **0 fires**
- GOM-C: **64 days total, 0 post-Aug1** (recent Jun-Jul cluster: 07/07-09, 07/20, 07/24-26)
- TODAY Aug10 +54.92%, 17.96× → real-time, chưa vào DAILY (L-21)
  - Nếu Aug10 vào DAILY: vol_vs_med14=17.96× > 8 ngưỡng GOM-A → cần kiểm tra threshold

**Q2 — OI:**
- OI 30d range: $3.77M → $5.19M (NOT UNCALIBRATED)
- oi_cycle_pos = 1.000 (tại đỉnh 30d range, khi token đang pump)
- OI bình thường tương đối nhỏ so với volume ($34M vol vs $5.4M OI = 6.3× OI/day)

**Q3 — VWAP M2:**
- VWAP M2 (231 days): **$0.282**
- Px Aug9: **$0.0376** → -86.66% below VWAP M2
- Px Aug10 real-time: ~$0.060 → -78.7% below VWAP M2
- ATH close: $1.619, ATH high: $1.701
- Drawdown from ATH: **-97.68%**

---

## LĂNG KÍNH 2 — STAGE-CHECK

| Stage | Status | Key Data |
|-------|--------|----------|
| S0 GHẾ-NỀN | PARTIAL | nền $0.034-$0.050 thấp hơn listing $0.060; 21d range 59.5% |
| S0.5 CROWD | EXTREME | gLSR 2.87 VERY BULL (đỉnh 5.93 Jul29-31); crowd rất long |
| S1 STAGING-KỆ | ĐÃ QUA | cluster Feb24-27 (9-24×); Apr19, May13-16 = bậc nạp lịch sử |
| S2 CẦU-THANG | ĐÃ QUA | Jun11→May25: ATH $1.701; giũ giữa thang (May1, Jun1, Jun4) |
| S3 XẢ-VÙNG-NHỚ | **PARTIAL** | BLOWOFF1 May27 (-72.6% $474M), BLOWOFF2 Jul2 (-58.6% $84M); dist_wall=27 |
| S4 XÁC | **PARTIAL** | knife_crowd=12, decay=19, gLSR VERY BULL = bắt dao crowd |

**Stage Assessment (2 lăng kính):**
- Giá đang ở vùng S3/S4 border: -97.7% từ ATH, post-2 blowoff events
- TODAY pump (+54.92%) xảy ra ở đáy tuyệt đối (≈listing price)
- pos_r đang TĂNG (+0.003 slope) nhưng d_pos_28d=-0.052 FALLING (short-term contradicts long-term)
- **Kết luận tạm:** S4-bounce triggered by external catalyst hoặc controlled distribution pocket

---

## GOM-D DRAFT CHECK (draft chưa ký — tham chiếu)

| Gate | Status | Evidence |
|------|--------|----------|
| D1 nền-chết (px<15% ATH=~$0.255) | **PASS** | 72 days below Dec22→Mar3 |
| D3 nạp-bậc (≥2 vol cluster ≥8×) | **PASS** | Feb24-27 (4-day cluster), Apr19, May13+16 |
| D4 vol-wake (vol ≥5× ngày đầu pump) | **PASS** | Apr19 14.6×, May12 5.75×, Aug10 17.96× |
| D5 churn (vol ≥8× sau staging) | **PASS** | Feb25-26 23-24×, May13 13× |
| Suppressor neg_div 7d | **OFF** | 0 days f_avg < -2e-4 |

**GOM-D DRAFT: 4/4 PASS, suppressor OFF → cấu trúc DNA staged-pump có mặt lịch sử**
*Note: draft chưa ký → không dùng làm signal fire; dùng tham chiếu template so sánh*

---

## G-4: ON-CHAIN
- BscScan v1 API deprecated (NOTOK all endpoints)
- **Nansen: LOCKED → CẦN OPERATOR**
  - a) Top 50 holders + % supply tập trung
  - b) Fresh wallet check (<30d trong top 20)
  - c) On-chain flow BSC 7d
  - d) Cross-ref cụm ví GUA vs ON/BTW/AGT

---

## G-5: DEPTH SNAP
**SNAP 1 (13:49 UTC):**
- mid: $0.0600100
- bid±2%: $59,829 | ask±2%: $47,820
- ratio: **1.2511 → BID-HEAVY**
- Context: token đang pump, buyers stacking bids

**SNAP 2: PENDING ≥15:50 UTC**

---

## G-6: CROSS-REF
| Source | Kết quả |
|--------|---------|
| FW daily | 64 rows (Jun1→Aug7) |
| gom_state.json (current) | NOT FOUND (12 tokens tracked) |
| gom_state_v8/v9 (historical) | FOUND (GUA tracked historically) |
| alpha_id_map.json | FOUND (ALPHA_483 resolved) |
| CASE_INDEX | Pending G-8 |
| alpha store | 250 rows |
| freshwatch_symbols.txt | FOUND (u50 universe) |
| ON/BTW/AGT wallet crossref | CẦN OPERATOR (Nansen LOCKED) |

**Không có bằng chứng wallet crossref với ON/BTW/AGT từ nguồn available (local-only).**

---

## G-7: SANITY
**5/5 PASS:**
- S1 DAILY row count: 231 ✓
- S2 Date continuity Dec22→Aug9: no gaps ✓
- S3 GOM-A fires: 0 ✓
- S4 taker_buy_pct range [39.2, 55.0] ✓
- S5 f_avg last 14d no extreme: OK (max 0.001101 < 0.005 threshold) ✓

---

## G-8: CASE_INDEX
- Registered at row **23** in CASE_INDEX.xlsx INDEX sheet
- status=ACTIVE, alpha_id=ALPHA_483
- Verdict: **KHÔNG điền** — tầng HUMAN

---

## TỔNG HỢP

### Câu hỏi case: "Có lực gom không? Hay captive staged-pump?"

**Trả lời (dữ liệu đến Aug9, pump Aug10 real-time):**

**A. Lực gom (GOM-A/B/C)?**
- GOM-A/B: **COLD** — 0 fires trong 231 ngày lịch sử (kể cả vol clusters lớn như Feb25 23.6×, Apr19 14.6×)
- GOM-C: 64 ngày nhưng 0 post-Aug1 → tín hiệu gom nhẹ đã tắt
- Điều này gợi ý: hoặc threshold GOM-A calibrate cao cho GUA, hoặc không có accumulation pattern đủ clean

**B. Captive staged-pump (khuôn ON/BTW)?**
- GOM-D draft: D1+D3+D4+D5 **đều PASS** → DNA staged-pump CÓ MẶT trong lịch sử GUA
- Pattern: nạp Feb24-27 (cluster 4 ngày), pump Apr-May→ATH, xả May27 -72.6%, bounce May28 +119.5%, decay, Jul2 blowoff2, và NOW Aug10 pump mới
- Đây là cấu trúc multi-cycle: mỗi cycle có: nạp bậc → pump → xả → decay → repeat

**C. Stage hiện tại (Aug10)?**
- Post-blowoff2 (Jul2): GUA đang ở vùng nền thứ 2 (~$0.034-$0.050)
- TODAY pump (+54.92%, 17.96×) xảy ra ĐÚNG lúc gLSR=2.87 (retail VERY LONG) và div=0.41 (smart short)
- Đây là cấu trúc **crowd-trap ở nền thứ 2**, hoặc là pre-launch của cycle mới
- **Funding 0.001101** = longs trả phí cực cao → không bền nếu pump không có backing mới

**D. Wallet crossref ON/BTW/AGT?**
- CẦN OPERATOR — không thể verify từ local data (Nansen LOCKED, BscScan v1 deprecated)

### Verdict đề xuất (operator đọc, KHÔNG agent điền):
*Xem thêm sau snap2 (≥15:50 UTC) và operator on-chain review.*

---

## PENDING (DỪNG CHỜ ĐỌC)
1. **Snap2** (≥15:50 UTC): chạy `python _probe_gua_snap2_20260810.py` → so sánh ratio
2. **G-4 on-chain**: operator export BscScan top holders CSV → fresh wallet check
3. **G-4 wallet crossref**: operator Nansen → GUA vs ON/BTW/AGT wallet overlap
4. **Verdict**: operator đọc report → điền CASE_GUA.xlsx sheet VERDICT (tầng HUMAN)
5. **Aug10 candle**: sau 00:00 UTC Aug11 → build_case.py refresh để Aug10 (+54.92%, 17.96×) vào DAILY

*Án GUA OPEN — DỪNG chờ operator đọc report này và snap2.*
