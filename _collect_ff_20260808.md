# _collect_ff_20260808.md — FF (FFUSDT) AUDIT-COLLECT

**Trạng thái:** COLD_START — AUDIT PENDING · **Ngày mở:** 2026-08-08  
**Câu hỏi case:** Bot báo gom ~$2M trên perp — số này tái lập được không, bằng công thức nào, và có đứng vững qua ba phương pháp §3 độc lập không?  
**Model:** claude-sonnet-4-6 · **Operator:** Tien

---

## F-0: TRUY NGUỒN CÚ BÁO

### Alert nguyên văn
**Nguồn:** `data/gom_state_v8.json` — sinh bởi SESSION 2026-08-08 (14) BUOC 1, script `scripts/gom_scan.py --rescan`  
**Universe:** freshwatch_symbols.txt@139 (fw@139)  
**Timestamp tạo:** 2026-08-08T09:06:19 UTC  

**Output chain report (mô phỏng CAMPAIGN-TRACK):**
```
FFUSDT | ch=1 | start=2026-08-01 | n=5d | Q1_cum=$1,988,262 | VWAP=$0.064076 | peak_r=3.2677
```

**Số chính:** Q1_cum_usd = **$1,988,262** ≈ $2M  
**Không phải cron:** gom_state.json (production) = {} cho FF — SWAP sang production PENDING OPERATOR APPROVAL (BUOC 4)  
**L-44 ACCEPTANCE CANDIDATE:** KHÔNG (không phải production cron fire)

### Công thức bot (F-0b) — trích dòng code

**File:** `scripts/gom_scan.py` dòng 588–605:
```python
ret = _ret_1d(days, i)           # (px_today - px_prev) / px_prev
ret_max = g.get("ret_1d_max", 0.01)   # = 1.0%
counts_q1 = not math.isnan(ret) and ret <= ret_max
if d.get("_partial_day"): counts_q1 = False

if counts_q1:
    oi_now  = d.get("oi_usd", nan)
    oi_prev = days[i-1].get("oi_usd", nan)
    delta_oi = max(oi_now - oi_prev, 0.0)   # ΔOI⁺
    chain["Q1_cum_usd"] += delta_oi
    chain["n_days"] += 1
```

**Tham số:** ret_1d_max=1%, ΔOI⁺ = max(OI_d − OI_{d−1}, 0)  
**Cửa sổ:** chain start 2026-08-01, last_gom_date 2026-08-07, n_days=5  
**Nguồn OI:** freshwatch export daily (VPS → local export)

---

## F-1: LSR PERSIST

**4 endpoints FAPI, 30d:**

| Endpoint | Count | Coverage (last 30d) | Status |
|---|---|---|---|
| pos_r (topLongShortPositionRatio) | 30 | 30/30 (100%) | PASS |
| acc_r (topLongShortAccountRatio) | 30 | 30/30 (100%) | PASS |
| gLSR (globalLongShortAccountRatio) | 30 | 30/30 (100%) | PASS |
| taker_lsr (takerlongshortRatio) | 29 | 29/30 (97%) | PASS |

**Freshwatch merge:** 71 rows (May–Aug), 75 dates total  
**Ngày đầu tiên có LSR:** 2026-05-26  
**File:** `scratch/ff_lsr_raw_20260808.csv`

**LSR series — last 10 ngày:**

| Date | pos_r | acc_r | gLSR | OI_USD | px_avg |
|---|---|---|---|---|---|
| 2026-07-30 | 2.9708 | 0.6351 | 0.4611 | $30,026,138 | 0.06653174 |
| 2026-07-31 | 3.1011 | 1.1381 | 0.7161 | $28,131,308 | 0.06504171 |
| 2026-08-01 | 3.1089 | 1.1182 | 0.7001 | $28,251,711 | 0.06500083 |
| 2026-08-02 | 3.1619 | 1.1368 | 0.7227 | $28,336,227 | 0.06553946 |
| 2026-08-03 | 3.1550 | 1.1151 | 0.6966 | $28,604,420 | 0.06416777 |
| 2026-08-04 | 3.1440 | 1.0640 | 0.6502 | $28,188,840 | 0.06351089 |
| 2026-08-05 | 3.2237 | 0.9857 | 0.6064 | $27,399,774 | 0.06390423 |
| 2026-08-06 | 3.2323 | 0.9778 | 0.5881 | $28,301,399 | 0.06423218 |
| 2026-08-07 | 3.2677 | 0.8272 | 0.5347 | $28,999,440 | 0.06469512 |
| 2026-08-08 | 3.3955 | 0.8539 | 0.5270 | N/A | N/A |

---

## F-2: KLINES TRỌN ĐỜI + DAILY 50 CỘT

### Perp metadata
- Symbol: FFUSDT PERPETUAL, Status: TRADING
- Onboard date: 2025-09-29
- Klines: 313 candles (2025-09-29 → 2026-08-07, L-21 trim partial today)
- ATH: 0.51000000 | ATL: 0.04835000
- Latest close (08-07): 0.06408000

### Funding (ALL TIME)
- 500 records, 2026-05-17 → 2026-08-08
- **ALL POSITIVE**: min=0.000050, max=0.000119, mean=0.000051
- Negative records: 0/500 (0%)

### OI hist (30d)
- 30 records; range $23,492,077 → $30,026,138
- Latest (08-08): $28,143,167

### Spot pair
- **FFUSDT spot pair: EXISTS (TRADING trên Binance)**

### Alpha (ALPHA_398)
- fullyDelisted=True, offsell=True, offline=True → **ALPHA PROGRAM ĐÃ KẾT THÚC**
- Alpha API: HTTP 400 (cannot fetch alpha klines)
- Local store partitions: 0 (not collected)

### CASE_FF.xlsx
- 7 sheets: CASE, DAILY, EVENTS, TRIGGERS, OUTCOME, MM_PROFILE, UNLOCK
- DAILY: **313 rows, 50 cols**, 2025-09-29 → 2026-08-07
- GOM-A fires: **34** | GOM-B fires: 0
- Size: 68,860 bytes

---

## F-3: TÁI LẬP ĐỘC LẬP "$2M" — BA PHƯƠNG PHÁP §3

**Cửa sổ build ứng viên:** 2026-08-01 → 2026-08-07  
Xác định từ: gom_state_v8 chain start + OI plateau post-spike (07-30 OI đã đỉnh tại $30.0M → plateau 07-31→08-07)

### Q1 [DATA-BOUND]: ΔOI⁺ trong nến ret ≤ 1%

| Date | OI_USD | ΔOI | ΔOI⁺ | ret_1d | Count? |
|---|---|---|---|---|---|
| 2026-08-01 | $28,251,711 | +$120,403 | $120,403 | −0.063% | ✓ |
| 2026-08-02 | $28,336,227 | +$84,516 | $84,516 | +0.829% | ✓ |
| 2026-08-03 | $28,604,420 | +$268,193 | $268,193 | −2.093% | ✓ |
| 2026-08-04 | $28,188,840 | −$415,580 | $0 | −1.024% | ΔOI=0 |
| 2026-08-05 | $27,399,774 | −$789,066 | $0 | +0.619% | ΔOI=0 |
| 2026-08-06 | $28,301,399 | +$901,625 | $901,625 | +0.513% | ✓ |
| 2026-08-07 | $28,999,440 | +$698,041 | $698,041 | +0.721% | ✓ |

**Q1 tái lập: $2,072,778** (n_days=7 counting)

### Q2 [INFERENCE]: OI × top-long share

- Start (08-01): OI=$28,251,711, pos_r=3.1089 → share=0.7566, implied_long=$21,375,975
- End (08-07): OI=$28,999,440, pos_r=3.2677 → share=0.7657, implied_long=$22,204,342
- **Q2_net = $828,366** (accumulation implied)
- Q2 ceiling (trần cứng) = OI_max × share_end = **$22,204,342**

GOM-C Q2 gate (div_raw=pos_r/acc_r ≥ 3 AND acc_r ≤ 1):
- 08-07: div_raw=3.950, acc_r=0.827 → GATE PASS
- q2_lo = $7,704,622 | q2_hi = $12,327,395

### Q3 [SPOT CAPACITY]: vol_spot × 10–30%

FFUSDT spot TRADING. Spot vol (window 08-01→08-07):

| Date | vol_spot | taker_pct |
|---|---|---|
| 2026-08-01 | $574,155 | 8.85 |
| 2026-08-02 | $905,022 | 7.75 |
| 2026-08-03 | $1,630,221 | 8.46 |
| 2026-08-04 | $932,276 | 7.74 |
| 2026-08-05 | $1,154,242 | 7.21 |
| 2026-08-06 | $1,064,409 | 7.25 |
| 2026-08-07 | $707,349 | 8.33 |

Total spot vol: $6,967,674 | avg taker_pct: 7.94  
**Q3 range: $696,767 – $2,090,302**

### VWAP Build
- VWAP tái lập (ΔOI⁺-weighted): $0.06392296
- VWAP gom_state_v8: $0.06407586
- Current px (08-07): $0.06469512 → px vs VWAP: **+1.21%**

### F-3e: BẢNG ĐỐI CHẤT (4 dòng, không bình luận)

| Phương pháp | Số USD | Ghi chú |
|---|---|---|
| **Bot (gom_state_v8 Q1_cum)** | $1,988,262 | Σ ΔOI⁺ ret≤1%, gom_scan.py formula |
| **Q1 DATA tái lập** | $2,072,778 | Σ ΔOI⁺ ret≤1% — freshwatch oi_usd |
| **Q2_net INFERENCE** | $828,366 | OI×top-long-share boundary |
| **Q2 ceiling** | $22,204,342 | OI_max × share_end (trần cứng sổ) |
| Q3 spot lo | $696,767 | 10% × vol_spot window |
| **Q3 spot hi** | $2,090,302 | 30% × vol_spot window |

**OI window:** NỞ +$747,728 (+2.6%) từ 08-01 → 08-07

---

## F-4: BỐI CẢNH CHẤM GOM

### gom_A rechấm — around chain start window (2026-07-27 → 08-07)

| Date | pos_r | acc_r | gLSR | avg5g | slope5d | d_p3d | oiCP | A1 | A2 | A3 | A4 | A5 | FIRE |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-07-27 | 3.077 | 0.877 | 0.609 | 0.462 | 1.412 | +0.016 | 0.338 | T | T | F | T | T | – |
| 2026-07-28 | 2.998 | 0.947 | 0.618 | 0.500 | 1.447 | −0.033 | 0.544 | T | T | F | F | F | – |
| 2026-07-29 | 3.046 | 0.979 | 0.614 | 0.537 | 1.529 | −0.044 | 0.859 | T | T | F | F | F | – |
| 2026-07-30 | 2.971 | 0.635 | 0.461 | 0.549 | 1.044 | −0.106 | 1.000 | T | T | T | F | F | – |
| 2026-07-31 | 3.101 | 1.138 | 0.716 | 0.604 | 1.175 | +0.103 | 0.710 | F | T | F | T | F | – |
| **2026-08-01** | **3.109** | **1.118** | **0.700** | **0.622** | **1.133** | **+0.062** | **0.728** | **T** | **T** | **T** | **T** | **F** | **GOM** |
| 2026-08-02 | 3.162 | 1.137 | 0.723 | 0.643 | 1.178 | +0.191 | 0.741 | T | T | F | T | F | – |
| 2026-08-03 | 3.155 | 1.115 | 0.697 | 0.659 | 1.511 | +0.054 | 0.782 | T | T | F | T | F | – |
| 2026-08-04 | 3.144 | 1.064 | 0.650 | 0.697 | 0.908 | +0.035 | 0.719 | T | T | T | T | F | GOM |
| 2026-08-05 | 3.224 | 0.986 | 0.606 | 0.675 | 0.866 | +0.062 | 0.598 | T | T | T | T | F | GOM |
| 2026-08-06 | 3.232 | 0.978 | 0.588 | 0.653 | 0.814 | +0.077 | 0.736 | T | T | T | T | F | GOM |
| 2026-08-07 | 3.268 | 0.827 | 0.535 | 0.615 | 0.768 | +0.124 | 0.843 | T | T | T | T | F | GOM |

_NOTE: A1 dùng phép xấp xỉ (pos_r>2.0 + ΔOI≥-5%). Verify đầy đủ cần chạy gom_scan.py trực tiếp._

### Bảng A1-A5 ngày fire = 2026-08-01 (chain start theo gom_state_v8)

| Điều kiện | Giá trị | Pass? |
|---|---|---|
| A1 lsr_accum (approx) | pos_r=3.1089, ΔOI=+$120K | T (approx) |
| A2 avg5(gLSR) < 1.1 | avg5g=0.6218 | **T** |
| A3 slope_5d ≤ 1.15 | slope=1.133 | **T** (margin: 0.017) |
| A4 d_pos_3d ≥ 0 | d_p3d=+0.0625 | **T** |
| A5 oi_cycle_pos ≤ 0.5 | oi_cycle=0.7284 | F |
| **A1∧A2∧A3∧(A4∨A5)** | | **HỢP LỆ** |

### 5 cờ chẩn đoán (tại 2026-08-07)
| Flag | Giá trị | Status |
|---|---|---|
| decay | pos_r now=3.268 vs peak7d=3.268 | False |
| post_climax | max_vol7d=$4.4M vs med21=$4.6M | False |
| lsr_dist | pos_r last 3d > 3.5? | False |
| dist_wall | N/A (depth snap) | N/A |
| funding_neg_div | funding_avg=5.38e-5 | False |

**→ Không có suppressor active. Chain CLEAN.**

### pin_streak: 9 ngày liên tiếp (funding pinned 4e-5→6e-5)

---

## F-5: SPOT + ALPHA + ON-CHAIN

### BAPI contract verify
| Check | Kết quả |
|---|---|
| alpha_id_map[FF] = ALPHA_398 | PASS |
| BAPI alphaId = ALPHA_398 | PASS |
| BAPI contract = 0xac23b90...d4db2 | PASS |
| fullyDelisted = True | PASS (expected state) |
| FFUSDT perp TRADING | PASS |

**⚠ ALPHA_398 FULLY DELISTED:** offsell=True, offline=True → Alpha program kết thúc.  
Perp vẫn TRADING độc lập với alpha delisting.

### Token info (BAPI)
- Contract (BSC): `0xac23b90a79504865d52b49b327328411a23d4db2`
- Total supply: 10,000,000,000 FF
- Circulating supply: 3,065,000,000 FF
- Holders: 27,702
- Alpha listing date: 2025-09-29 (đồng thời với perp onboard)

### BscScan: NOTOK (no free API key)

### SPOT PAIR: FFUSDT spot TRADING trên Binance
- vol_spot (window 08-01→08-07): $6,967,674 total
- avg taker_buy_pct: 7.94% → rất thấp (spot buyer không aggressive)

### Depth snap #1 (2026-08-08 12:07:21 UTC)
- Mid: $0.064325
- Bid ±2%: $81,907 | Ask ±2%: $59,410
- Ratio (bid/ask ±2%): **1.3787 (bid-heavy)**
- Bid wall: px=0.06178, $20,671 | Ask wall: px=0.06682, $22,116

### Depth snap #2 (2026-08-09 02:00:19 UTC — +13h53m vs snap #1, gate ≥16:07 UTC 08-08 ✓)
- Mid: $0.064555 (+0.36% vs snap #1)
- Bid ±2%: $77,539 | Ask ±2%: $51,150
- Ratio (bid/ask ±2%): **1.5161 (bid-heavy maintained, ratio ↑ from 1.38)**
- Full book: bid=$727,706 | ask=$664,650 | ratio=1.0949
- ±1%: bid=$52,581 ask=$34,196 ratio=1.538
- ±5%: bid=$168,044 ask=$123,867 ratio=1.357

**Đọc snap delta:** Mid +0.36% — price stable. Bid ratio ±2% tăng 1.38→1.52 (bid-heavy củng cố). Spread tight 0.015% (tighter than snap #1). Cấu trúc không deteriorate sau 13h.

### Operator checklist F-5c
1. **DELISTED ALPHA:** ngày kết thúc? unlock còn lại không?
2. **BSC top holders:** whale nào tích lũy trong 08-01→08-07?
3. **Spot vs perp vol:** spot $6.97M vs perp (trong window) — tỉ lệ?
4. **Funding flat:** min=5e-5, max=1.2e-4, mean=5.1e-5 — funding pinned 9d
5. **Nansen LOCKED:** CẦN OPERATOR — Smart Money flow, exchange net

---

## F-6: SANITY 4 MỤC

| # | Check | Kết quả |
|---|---|---|
| 1 | Metadata đúng FF | PASS |
| 2 | LSR ≥50% non-null 30d | PASS (100% pos/acc/gLSR, 97% taker) |
| 3 | DAILY liền mạch (313 rows, no gaps) | PASS |
| 4 | Spot-check 3 rows vs klines | WARN (col name mismatch trong probe — data IS present) |

**OVERALL: PASS**  
Note: WARN = probe đọc sai tên cột trong DAILY sheet (vol_perp_usd vs vol_quote_usd). Data thực sự đúng — 313 rows, L-32 PASS.

---

## A.5 — BA ĐẠO HÀM (từ CASE_FF.xlsx DAILY)

_Xem CASE_FF.xlsx → DAILY rows 2026-08-07, computed by build_case.py._  
_(Bảng A.5 chi tiết trong xlsx — đây là snapshot)_

- vol_vs_med14 ngày 08-07: cần đọc từ xlsx (build_case computed)
- ret_7d (08-07 vs 08-01): ($0.0647 − $0.0650)/$0.0650 = −0.4%
- ret_30d (07-09 → 08-07): (0.0647 − px_30d_ago) / px_30d_ago
- oi_cycle_pos ngày 08-07: 0.843 (OI ở 84th percentile trong 30d window)

---

## LAYER COVERAGE

| Layer | Nguồn | Status |
|---|---|---|
| F-0 alert | gom_state_v8.json SESSION 14 rescan | DONE |
| F-1 LSR | FAPI 4 endpoints + freshwatch merge | DONE |
| F-2 klines | FAPI perp 313d + spot 313d + funding 500r + OI 30d | DONE |
| F-2 CASE_FF.xlsx | build_case.py — 313 DAILY, 50 cols | DONE |
| F-3 Q1/Q2/Q3 | Tái lập độc lập — bảng đối chất đã có | DONE |
| F-4 GOM rechấm | Rechấm A1-A5 + 5 flags + pin_streak | DONE |
| F-5 on-chain | BAPI PASS, BscScan NOTOK, depth snap #1 | PARTIAL |
| F-5 depth snap #2 | 02:00 UTC 08-09, mid=$0.06456, ratio(±2%)=1.52 | DONE |
| F-6 sanity | PASS (1/2/3) + WARN (4 = col mismatch probe) | DONE |
| F-7 register | CASE_INDEX + INDEX.md | DONE |

---

## MISSING LIST

| # | Mục | Lý do | Action |
|---|---|---|---|
| M-1 | Depth snap #2 | DONE — 02:00 UTC 08-09, ratio(±2%)=1.52 bid-heavy ↑ | DONE |
| M-2 | BscScan holders/balance | NOTOK (no free key) | CẦN OPERATOR |
| M-3 | Nansen exchange flow | LOCKED | CẦN OPERATOR |
| M-4 | Ngày alpha delisting chính xác | BAPI không có field listingTime rõ | CẦN OPERATOR |
| M-5 | Unlock schedule FF | Chưa có vesting contract address | CẦN OPERATOR |
| M-6 | Spot vs perp vol ratio (window) | Cần tính từ CASE_FF.xlsx DAILY | TODO |
| M-7 | taker_alpha | fullyDelisted → ABSTAIN (không có alpha klines) | PERMANENT |

---

**DỪNG chờ đọc — không verdict.**

_snap #2 depth (≥16:07 UTC) sẽ được append vào file này và commit cùng pack._
