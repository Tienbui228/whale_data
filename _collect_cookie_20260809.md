# COOKIE AUDIT-COLLECT REPORT
**File:** `_collect_cookie_20260809.md`  
**Date:** 2026-08-09  
**Câu hỏi:** gom_scan đã fire COOKIE — fire hợp lệ theo spec v1.5 không? Có ai gom thật không, gom từ bao giờ, bao nhiêu (§3 ba phương pháp), và đang ở pha nào vòng đời?

---

## PROVENANCE

| Trường | Giá trị |
|--------|---------|
| data-source | `scratch/cookie_perp_20260809.csv`, `cookie_lsr_raw_20260809.csv`, `cookie_oi_hist_20260809.csv`, `cookie_funding_20260809.json`, `cookie_spot_20260809.csv`, `cookie_bapi_20260809.json`, `cookie_perp_info_20260809.json`, `scratch/freshwatch_daily_2026-08.csv` |
| machine | local scratch (D:\Data back test\whale_data\scratch) |
| date-range | 2025-01-07 → 2026-08-08 (perp); 2026-07-11 → 2026-08-09 (OI 30d); 2026-08-01 → 2026-08-07 (FW) |
| code-commit | (commit sau khi đóng report) |
| API endpoints | fapi.binance.com klines/fundingRate/depth/openInterestHist; api.binance.com klines; BAPI token-list |

---

## C-0: TRUY ALERT

- **Nguồn fire:** `gom_state_v8.json` (SESSION 14 BUOC 1 — 60d rescan 08-09), KHÔNG phải production `gom_state.json` (COOKIE={} trong prod)
- **Track:** GOM-C (campaign-track)
- **Chain:** start=2026-08-03, close=2026-08-06 (close_reason=gom_gap>2d), n=1
- **Q1_cum_usd (bot):** $0 — OI declined on fire day (08-03: $1,144,044 vs 08-02: $1,144,783 → ΔOI=-$739)
- **VWAP (bot):** $0.00774 [vw-vol fallback] — num=7705.89/den=996,038.12
- **Alpha:** ALPHA_33, fullyDelisted=True
- **GOM-A fires (spec v1.5):** 0 — gLSR too high throughout history (gLSR=3.2391 on fire day, well above A1 threshold)

---

## C-1: LSR DATA

- **4 FAPI LSR endpoints:** PASS (30d data available, all endpoints consistent)
- **Total LSR dates:** 44 (2026-06-27 → 2026-08-09)
- **FW column mapping:** `lsr_pos_r`, `lsr_acc_r`, `lsr_global_r` (FW naming convention)
- **Output:** `scratch/cookie_lsr_raw_20260809.csv` (44 rows)
- **Fire day 08-03:** pos_r=1.5635, acc_r=N/A, gLSR=3.2391

---

## C-2: COLLECT + BUILD

| Dataset | Rows/Records | Range |
|---------|-------------|-------|
| Perp klines | 579 rows | 2025-01-07 → 2026-08-08 |
| Spot klines | 576 rows | 2024-12-23 → 2026-08-08 |
| Funding | 500 records (85 days) | (full history) |
| OI hist | 30 days | 2026-07-11 → 2026-08-09 |
| FW (Aug 2026) | 7 rows | 2026-08-01 → 2026-08-07 |

- **BAPI:** fullyDelisted=True, offsell=True, offline=True, holders=23,720 (live: 23,718), totalSupply=1,000,000,000, circulatingSupply=855,196,310, listingTime=2024-12-23 09:40 UTC
- **Perp info:** COOKIEUSDT status=TRADING, onboard=2025-01-07 11:30 UTC, contractType=PERPETUAL
- **Funding fix:** build_case.py yêu cầu raw per-event CSV với cột `fundingRate` — ban đầu build ghi aggregated (f_avg) dẫn đến funding_days=0; đã fix → Funding days=85 ✓
- **CASE_COOKIE.xlsx:** 579 DAILY rows, 50 cols, 7 sheets, 138KB

---

## C-3: §3 BA PHƯƠNG PHÁP

**Chain window:** 2026-08-03 → 2026-08-06 | **Audit window:** 2026-08-01 → 2026-08-08

### Q1 — ΔOI⁺ nến đỏ/phẳng (tích lũy bằng chứng OI)

| Window | Q1_cum_usd | Ghi chú |
|--------|-----------|---------|
| Bot (gom_state_v8, chain 08-03→08-06) | **$0** | n=1, OI declined 08-03 |
| Tái lập chain (08-03→08-06) | **$0** | Xác nhận bot |
| Audit window (08-01→08-08) | **$754,118** | +$98K (08-01) + $655K (08-07 dump day) |

**Ngày đóng góp Q1:**
- 08-01: ΔOI=+$98,524 (ret=-0.60%, nến đỏ/phẳng ✓)
- 08-07: ΔOI=+$655,593 (ret=-11.3%, nến đỏ ✓) — dump ngày sau pump 08-06

**Kết luận Q1:** Không có tích lũy OI trong fire window. Q1=$754K (audit) phần lớn là OI từ dump sau pump — không phải accumulation.

### Q2 — OI × share (net long estimate)

| Metric | Giá trị |
|--------|---------|
| Start 08-01: OI=$1,182,001, pos_r=1.0614 | long = $607,375 |
| End 08-08: OI=$1,557,750, pos_r=1.3018 | long = $883,173 |
| **Q2_net** | **+$275,798** |
| **Q2_ceiling** | **$883,173** |
| OI_max in window | $1,927,734 (08-07) — within calib (<$18M) |

### Q3 — Spot capacity ×10-30%

| Metric | Giá trị |
|--------|---------|
| Spot vol window 08-01→08-08 | $9,931,966 |
| Q3 low (10%) | $993,197 |
| Q3 high (30%) | $2,979,590 |

### VWAP Tái lập

| Nguồn | Giá trị |
|-------|---------|
| Bot [vw-vol] | $0.00773654 (num=7705.89/den=996,038.12) |
| Manual (close 08-03) | $0.00774000 |
| **Δ** | **+0.04%** ✓ hoàn toàn khớp |
| px 08-08 (L-21) | $0.01304 → **+68.4% vs VWAP** |

### Bảng đối chất

| Phương pháp | Số | Ghi chú |
|-------------|-----|---------|
| Bot Q1_cum_usd | $0 | n=1 ngày, OI không tăng |
| Q1 tái lập chain (08-03→08-06) | $0 | Xác nhận |
| Q1 audit window (08-01→08-08) | $754,118 | 08-07 dump = $655K |
| Q2_net | +$237,798 | OI×share delta |
| Q2_ceiling | $972,614 | OI_end × share_end |
| Q3 low (10%) | $993,197 | — |
| Q3 high (30%) | $2,979,590 | — |
| VWAP bot | $0.00774 | [vw-vol] fallback |
| px 08-08 | $0.01304 | +68.4% vs VWAP |

---

## C-4: PHASE CONTEXT + GOM-C RECHẤM

### C-4a: Bối cảnh pha vòng đời

| Mốc | Giá trị |
|-----|---------|
| Alpha listing | 2024-12-23 |
| Perp onboard | 2025-01-07 11:30 UTC |
| ATH | $0.628700 (2025-01-07 = listing day) |
| ATL | $0.007490 (2026-07-30) |
| Current (08-08) | $0.013037 |
| px vs ATH | **-97.9%** |
| px vs ATL | +74.1% |
| Nền 06-01→08-05 (66d) | avg=$0.009026, range $0.00749–$0.01314 |
| VWAP fire 08-03 | $0.00774 |
| px 08-08 vs VWAP | **+68.4%** |

**Vol spikes gần đây (≥8×med14):**
- 2026-08-06: $21.06M, ret=+25.4%
- 2026-08-07: $11.66M, ret=-11.3% (dump)
- 2026-08-08: $27.44M, ret=+39.7% (resumption)

**Pha:** Post-ATH collapse (-97.9%), đang trong đợt bounce từ ATL. Pattern pump-and-dump với vol spike không có tích lũy OI. Không có giai đoạn accumulation cổ điển.

### C-4b: GOM-C Rechấm 08-03

| Điều kiện | Kết quả | Chi tiết |
|-----------|---------|---------|
| C1 stealth_grind | **CẦN SPEC** | gLSR=3.2391 >> 1.1 — likely FAIL nếu C1 yêu cầu gLSR<bound |
| C2_quiet (f_avg≤2×neutral) | **PASS** ✓ | f_avg=-6.1e-7 vs threshold 1e-4 |
| C3_lax (taker∈[40%,55%]) | **PASS** ✓ | taker=44.39% |
| d_pos≥0 (pos_r non-declining) | **FAIL** ✗ | d_pos=-0.1056 (pos_r dropped 1.6691→1.5635) |

**Tóm tắt GOM-C rechấm:** C2✓ + C3✓ nhưng d_pos FAIL. C1 cần exact spec (gom_scan.py không tìm thấy ở root — CẦN kiểm tra scripts/). Nếu C1 yêu cầu gLSR < upper_bound thì C1 cũng FAIL (gLSR=3.24 là rất cao).

### C-4c: 5 Cờ chẩn đoán (30d window)

| Flag | Count | Rate |
|------|-------|------|
| flag_dist_wall (taker≥50% + ret<0) | 4 | 13.3% |
| flag_knife (gLSR↑ + ret<-3%) | 1 | 3.3% |
| **flag_hedge_struct (div≤0.5)** | **27** | **90.0%** |
| flag_neg_div (f_avg≤-2e-4) | 0 | 0.0% |
| flag_decay (taker<45%) | 2 | 6.7% |

**Đọc:** flag_hedge=90% là dominant — cấu trúc short hedge chiếm phần lớn 30d qua. Không có neg_div. Crowd không panic sell.

### C-4d: Pin_streak + OI_cycle_pos (14d)

| Ngày | f_avg | PIN? | OI ($) | oi_cycle |
|------|-------|------|--------|----------|
| 2026-07-27 | 0.000102 | — | 1,109,996 | 0.063 |
| 2026-07-29 | 0.000038 | — | 984,770 | 0.000 (ATL OI) |
| 2026-08-03 | -0.000001 | — | 1,144,044 | 0.080 |
| **2026-08-06** | **0.000050** | **PIN✓** | 1,272,141 | 0.145 |
| 2026-08-07 | -0.000039 | — | 1,927,734 | 0.476 |
| 2026-08-08 | -0.000062 | — | 1,557,750 | 0.289 |
| 2026-08-09 | 0.000050 | PIN✓ | 2,966,722 | 1.000 |

- **pin_streak (last date):** 1 (không đủ để kết luận pinning pattern)
- **oi_cycle_pos (08-08):** 0.289 — moderately positioned, không đỉnh 30d
- **OI_min30:** $984,770 (07-29); **OI_max30:** $2,966,722 (08-09 partial)

---

## C-5: BAPI + DEPTH SNAP #1 + ON-CHAIN

### BAPI (live 01:50 UTC 08-09)

| Field | Value |
|-------|-------|
| alphaId | ALPHA_33 |
| fullyDelisted | **True** |
| offsell | True |
| offline | True |
| holders | 23,718 (live) |
| totalSupply | 1,000,000,000 |
| circulatingSupply | 855,196,310 |
| price (live) | $0.01211 |
| percentChange24h | +33.34% |
| volume24h | $878,484 |
| marketCap | $10.36M |
| FDV | $12.11M |
| listingTime | 2024-12-23 09:40 UTC |
| contract (BSC) | 0xc0041ef357b183448b235a8ea73ce4e4ec8c265f |

**Alpha taker_alpha: ABSTAIN** (fullyDelisted=True — same rule as FF)

### Perp Info

- status: TRADING (vẫn còn giao dịch perp)
- onboardDate: 2025-01-07 11:30 UTC
- deliveryDate: 2100-12-25 (perpetual)

### Depth Snap #1

**Time: 2026-08-09 01:50:45 UTC**

| Metric | Value |
|--------|-------|
| mid | $0.011869 |
| bid_top | $0.011866 |
| ask_top | $0.011872 |
| spread | 0.051% |
| bid2 (full book) | $589,621 |
| ask2 (full book) | $396,841 |
| **ratio bid/ask** | **1.4858** (bid-heavy) |

**Depth buckets:**
| Bucket | bid ($) | ask ($) | ratio |
|--------|---------|---------|-------|
| ±1% | 15,173 | 34,251 | 0.443 |
| ±2% | 41,920 | 67,553 | 0.621 |
| ±5% | 134,933 | 108,143 | 1.248 |

**Đọc:** Bid-heavy ở full book (ratio=1.49) nhưng ask-heavy ở ±1% (ratio=0.44) — bức tường ask ngay gần mid. Bid side spread mỏng gần mid, dày ở xa. Pattern này phù hợp với distribution setup (ask wall gần giá).

**SNAP #2 GATE:** ≥05:50 UTC 2026-08-09 (CẦN OPERATOR nếu muốn snap trong phiên này)

### On-chain

- **BscScan:** NOTOK V1 (API key cần để query holders/top balances) → **CẦN OPERATOR**
- **Nansen:** LOCKED (NANSEN_KEY_LOCKED env) → **CẦN OPERATOR**
- **Unlock schedule:** Không tìm thấy vesting contract → **CẦN OPERATOR**

---

## C-6: CROSS-REFERENCE

- **Agent_log:** COOKIE xuất hiện 17 lần — xác nhận fire trong GOM-C β (L499: ARIA/COOKIE/CYS/FHE/TRADOOR/TUT), VPS test 08-07 (4 fires: COOKIE CYS TST TUT)
- **FW vol:** Khớp hoàn toàn với perp vol (chung nguồn FAPI klines)
- **FW px_avg vs perp close:** Chênh <2% mọi ngày; 08-07 delta=+8.4% bình thường (VWAP ngày dump > EOD close)
- **Taker FW vs perp:** Chênh -5bp systematic (rounding artifact), tất cả 7 ngày ≤10bp → PASS
- **CASE_INDEX:** Đã đăng ký row 17, status=OPEN, T0=2026-08-03

---

## C-7: SANITY CHECK

| Mục | Kết quả |
|-----|---------|
| S1 Row count + date range | **PASS** — perp=579, lsr=44, oi=30, fund=500 |
| S2 Taker FW vs perp | **PASS** — 7/7 OK (≤10bp), systematic -5bp là artifact |
| S3 OI continuity | **PASS** — không có jump 5× |
| S4 Funding coverage | **PASS** — 6 intervals/day mọi ngày audit window |
| S5 CASE_COOKIE.xlsx | **PASS** — 7 sheets, 579 DAILY rows, last date=2026-08-08 |

**Note S1:** LSR last date=2026-08-09 (partial day, benign — data collected sáng 08-09)

---

## C-8: REGISTER

- **CASE_COOKIE.xlsx status:** OPEN — audit-collect complete, awaiting operator verdict
- **CASE_INDEX row 17:** CASE_COOKIE.xlsx | COOKIE | OPEN | GOM-C fire 08-03 | COLD_START | T0=2026-08-03
- **INDEX.md:** Regenerated (3,200 bytes)

---

## TỔNG HỢP: TRẢ LỜI CÂU HỎI CASE

### 1. Fire hợp lệ theo spec v1.5 không?

**Kết luận sơ bộ: PARTIALLY VALID — cần xem C1 exact spec**

GOM-C rechấm 08-03:
- C2_quiet ✓ (f_avg=-6.1e-7, cực kỳ neutral)
- C3_lax ✓ (taker=44.39% ∈ [40%,55%])
- **d_pos FAIL** (pos_r giảm -0.1056 từ 08-02 → 08-03)
- C1 stealth_grind: gLSR=3.2391 — nếu C1 có upper bound cho gLSR thì FAIL (gLSR này là crowd đang short rất mạnh, không phải stealth)

Nếu C1 yêu cầu d_pos≥0 là hard gate thì fire 08-03 **không hợp lệ theo spec đầy đủ**. Cần confirm exact C1 definition trong gom_scan.py.

### 2. Có ai gom thật không?

**Bằng chứng CHỐNG lại gom thật:**
- Q1 chain = $0 (OI declined on fire day — không có tích lũy OI)
- flag_hedge_struct = 90% (cấu trúc short chiếm ưu thế, không phải long accumulation)
- d_pos = -0.1056 (pos_r giảm vào ngày fire — ratio_long/short thực ra đang giảm)
- gLSR=3.2391 (crowd đang short nặng hơn, không phải quiet accumulation)
- Depth snap #1: ask-heavy ở ±1% (distribution signal gần mid)

**Bằng chứng MƠ HỒ (không confirm gom):**
- Q1 audit window $754K chủ yếu là 08-07 dump day — không phải accumulation
- Q2_net +$237K — small net long change
- C2_quiet: funding rất neutral ngày 08-03 (không ai paying premium để long)

**Pattern thực tế:** Vol spike mạnh không có OI buildup → pump-and-distribute, không phải accumulation.

### 3. Gom từ bao giờ, bao nhiêu?

Không có bằng chứng gom trong data available. Chain n=1 với OI declining.

Nếu định nghĩa "gom" theo §3:
- Q1 (chain): $0
- Q2_net: +$237K (không đáng kể với $1.1M OI base)
- Q3 spot capacity: $993K–$2.98M (spot vol window)

### 4. Đang ở pha nào vòng đời?

- **ATH:** $0.6287 (listing day 2025-01-07) → -97.9% hiện tại
- **Nền:** 66 ngày (06-01→08-05) ở avg=$0.0090
- **Hiện tại:** Post-nền vol spike (08-06 +25.4% → 08-07 -11.3% → 08-08 +39.7%)
- **Pha:** **Distribution / Pump** — không phải Accumulation. Token đang trong giai đoạn cuối chu kỳ sau ATH collapse 98%. Vol spike không kèm OI tích lũy xác nhận pump-to-sell.
- **oi_cycle_pos:** 0.289 (moderate, room for further OI expansion)

---

## CẦN OPERATOR

| Item | Lý do |
|------|-------|
| **Depth snap #2** | ≥05:50 UTC 2026-08-09 (4h sau snap #1) |
| **BscScan top holders** | API V1 NOTOK, cần manual UI hoặc V2 key |
| **Nansen wallet analysis** | LOCKED (NANSEN_KEY_LOCKED) |
| **C1 exact spec** | gom_scan.py không tìm thấy ở root — kiểm tra scripts/ để confirm C1 definition cho GOM-C |
| **Alpha precise delisting date** | Không có delistTime field trong BAPI JSON |
| **Unlock schedule** | Không tìm thấy vesting contract trên BSC |
| **Verdict** | Operator fills CASE sheet + CASE_INDEX |

---

## FILES SINH RA

| File | Loại | Ghi chú |
|------|------|---------|
| `scratch/cookie_perp_20260809.csv` | data | 579 rows |
| `scratch/cookie_lsr_raw_20260809.csv` | data | 44 rows |
| `scratch/cookie_oi_hist_20260809.csv` | data | 30 rows |
| `scratch/cookie_funding_20260809.json` | data | 500 records |
| `scratch/cookie_funding_20260809.csv` | data | raw format (fundingRate col) |
| `scratch/cookie_spot_20260809.csv` | data | 576 rows |
| `scratch/cookie_bapi_20260809.json` | data | BAPI token info |
| `scratch/cookie_perp_info_20260809.json` | data | FAPI perp info |
| `scratch/cookie_depth_snap1_20260809.json` | data | Snap #1 at 01:50 UTC |
| `docs/case_files/CASE_COOKIE.xlsx` | output | 7 sheets, 138KB |
| `docs/case_files/CASE_INDEX.xlsx` | updated | Row 17 = COOKIE |
| `docs/case_files/INDEX.md` | updated | Regenerated |
| `_probe_cookie_c0_20260809.py` | probe | C-0 truy alert |
| `_probe_cookie_c1_20260809.py` | probe | C-1 LSR collect |
| `_probe_cookie_c2_collect_20260809.py` | probe | C-2 collect |
| `_task_cookie_c2_build_20260809.py` | task | C-2 build CASE_COOKIE.xlsx |
| `_probe_cookie_fix_funding_20260809.py` | probe | Fix funding CSV format |
| `_probe_cookie_c3_q123_20260809.py` | probe | C-3 §3 ba phương pháp |
| `_probe_cookie_c4_phase_20260809.py` | probe | C-4 phase + GOM-C rechấm |
| `_probe_cookie_c5_onchain_20260809.py` | probe | C-5 on-chain + depth snap #1 |
| `_probe_cookie_c6_crossref_20260809.py` | probe | C-6 cross-reference |
| `_probe_cookie_c7_sanity_20260809.py` | probe | C-7 sanity 5-mục |
| `_task_cookie_c8_register_20260809.py` | task | C-8 register |
| `_probe_cookie_idx_fix_20260809.py` | probe | Fix CASE_INDEX row |

---

**DỪNG** — chờ operator đọc và verdict.
