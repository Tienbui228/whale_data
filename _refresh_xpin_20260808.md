# XPIN CASE REFRESH — 2026-08-08
**Analyst:** claude-sonnet-4-6 | **Session:** 2026-08-08 ~09:00-09:25 UTC  
**File:** docs/case_files/CASE_XPIN.xlsx | **Backup:** scratch/CASE_XPIN_bak_20260808_091552.xlsx  
**DỪNG: chờ operator đọc — không verdict, không đổi Status/TRIGGERS**

---

## X-0. SỔ CŨ NGUYÊN TRẠNG

### CASE Sheet (trước refresh)

| Field | Giá trị |
|---|---|
| token | XPIN |
| full_name | XPIN Network (BSC meme/utility) |
| chain | BSC |
| contract | 0xd955c9ba56fb1ab30e34766e252a97ccce3d31a6 |
| alpha_id | ALPHA_334 |
| archetype | LOAI_A_CANDIDATE — perp-first, PIN discipline, sustained pos_r>2 (chua on-chain confirm) |
| state | WATCH — post-failed-ignition holding (06/08/2026) |
| thesis_1line | 3 ignition attempts: Oct 2025 (OK), Dec 2025 (partial), Jul 2026 (FAIL). Div <1 = crowd > top traders. |
| perp_launch | 2025-09-12 08:00 UTC |
| alpha_listing | ~2026-01-27 |
| total_supply | 100,000,000,000 |
| circ_supply (Alpha) | 48,074,534,161 (48.07%) |
| holders (06/08) | 69,318 |
| px_current (06/08) | 0.001555 |
| ATH | 0.010318 (~2025-10-23) |
| px_vs_ath | -85% |
| T0_ignition | N/A — Jul 11 FAILED, no clean T0 |
| gLSR_latest (06/08) | 2.243 PEAK 30d |
| pos_r_latest (06/08) | 1.865 |
| acc_r_latest (06/08) | 2.019 |
| div_raw_latest (06/08) | 0.924 |
| OI_latest (06/08) | $11,611,000 |
| funding_regime | OSCILLATING |
| pin_pct_historical | 70.6% (353/500 intervals) |

### DAILY: Cuối sổ trước refresh

| Row | date | px_avg | vol_perp | taker | f_avg | f_n | oi_usd | gLSR | pos_r | acc_r | div_raw | data_bad |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 326 | 2026-08-01 | 0.001540 | $1,335,386 | 50.4% | 0.000252 | 6 | $11,951,087 | 2.1939 | 2.0046 | 2.0193 | 0.993 | 0 |
| 327 | 2026-08-02 | 0.001526 | $1,669,407 | 44.3% | 0.000305 | 6 | $12,162,495 | 2.2165 | 1.8030 | 1.9394 | 0.930 | 0 |
| 328 | 2026-08-03 | 0.001548 | $3,294,343 | 50.1% | 0.000188 | 6 | $11,920,802 | 2.2031 | 1.7966 | 1.9603 | 0.917 | 0 |
| 329 | 2026-08-04 | 0.001533 | $1,435,218 | 50.9% | 0.000094 | 6 | $12,069,070 | 2.1348 | 1.8217 | 1.8902 | 0.964 | 0 |
| **330** | **2026-08-05** | 0.001573 | **$598,638** | **56.4%** | 0.000290 | **2** | $11,611,127 | 2.2425 | 1.8651 | 2.0193 | 0.924 | **1** |

> **Ghi chú**: Row 330 (08-05) ghi khi data_bad=1, f_n=2 → partial day. Đã UPDATE trong X-2.

**Schema trước refresh:** 41 cột (thiếu: gom_A, gom_B, vol_alpha, taker_alpha, spot_perp_ratio, depth_ratio, ret_7d, ret_30d, vol_vs_med14, lsr_taker_r, ret_atl)

### TRIGGERS Sheet (trước refresh, nguyên văn)

| # | Chốt | Điều kiện | Trạng thái 06/08 |
|---|---|---|---|
| 1 | NEXT_IGNITION_SETUP | gLSR <1.2 AND div >1.5 AND stable_PIN >=7d AND OI build | NOT MET (0/4) |
| 2 | DIV_RECOVERY | div_raw > 1.5 sustained >=3d | FAIL (div=0.92 declining) |
| 3 | gLSR_RESET | gLSR < 1.2 sustained >=3d | FAIL (gLSR=2.243, peak) |
| 4 | FUND_RESTABLE | f_avg <= 5.5e-5 AND f_min=5e-5 >=7 intervals | FAIL (oscillating 0.0002-0.0006) |
| 5 | OI_BUILD | OI increase >20% from floor $8.56M trong 5 ngay | FAIL (OI flat $11-12M) |
| 6 | BITMART_VOL_VERIFY | Confirm BitMart $1.1B/day = wash or real | PENDING OPERATOR |

### EVENTS (10 dòng cuối)

| date | type | px_close | vol_perp | taker | oi_delta | note |
|---|---|---|---|---|---|---|
| 2025-12-22 | CAMPAIGN2_CONT | 0.00292 | $148,352,367 | 49.9% | — | Continuation. 6.2x avg. Then declined. |
| 2026-03-25 | CAPITULATION | 0.00117 | ? | 39.6% | — | Heavy sell. Bottom proximity. |
| 2026-04-07 | APRIL_BOUNCE | 0.00125 | $16,079,502 | 48.3% | — | Bounce from $0.001 floor. 6.7x avg. |
| 2026-07-10 | IGNITION3_BUILD | 0.00188 | $33,353,935 | 50.2% | OI +4% | Build-up day. |
| 2026-07-11 | IGNITION3_FAIL | 0.00197 | $207,302,334 | 50.6% | OI $10M→$14.9M | FAILED. 9x avg. taker 50.6% neutral. |
| 2026-07-12 | POST_FAIL_DUMP | 0.00191 | $32,019,150 | 49.7% | OI peaked $15.6M | OI peak, unwind started. |
| 2026-07-17 | HIGH_POS_R | 0.00155 | $3,291,790 | 50.7% | OI $10.9M | pos_r=2.359 peak 30d. Ignition failed. |
| 2026-07-29 | DIV_BREAK | 0.00151 | $2,031,064 | 53.1% | OI $11.7M | div crosses below 1.5 (div=1.101). |
| 2026-07-31 | DIV_INVERT | 0.00154 | $2,413,990 | 53.5% | OI $11.3M | div=0.991 inverted. acc_r>pos_r. gLSR=2.017. |
| 2026-08-05 | LATEST | 0.00156 | $567,000 | 56.4% | OI $11.6M | gLSR=2.243 peak. data_bad=1 partial. |

---

## X-1. LSR PERSIST

**Kết quả:** FAPI LSR 404 tất cả 4 endpoints (topLongShortPositionRatio, topLongShortAccountRatio, globalLongShortAccountRatio, takerlongshortRatio) — XPIN không được serve LSR riêng trên FAPI (confirmed permanent, không retry).

**Nguồn thay thế:** Freshwatch export (derived_1h canonical):

| File | XPIN rows |
|---|---|
| freshwatch_daily_2026-06.csv | 27 rows (06-04→06-30) |
| freshwatch_daily_2026-07.csv | 28 rows (07-01→07-31) |
| freshwatch_daily_2026-08.csv | 7 rows (08-01→08-07) |
| **Tổng** | **62 rows (06-04→08-07)** |

**Coverage last 30 dates (07-06→08-07):**

| Field | Non-null | Status |
|---|---|---|
| pos_r_raw | 30/30 | PASS |
| acc_r_raw | 30/30 | PASS |
| glsr_raw | 30/30 | PASS |
| taker_lsr_raw | 0/30 | FAIL (permanent FAPI 404 — không retry) |

**Last 10 rows:**

| date | pos_r | acc_r | gLSR | src |
|---|---|---|---|---|
| 2026-07-29 | 1.9818 | 1.8003 | 1.8074 | fw Jul |
| 2026-07-30 | 1.9487 | 1.5368 | 1.6846 | fw Jul |
| 2026-07-31 | 1.9555 | 1.9727 | 2.0166 | fw Jul |
| 2026-08-01 | 2.0046 | 2.0193 | 2.1939 | fw Aug |
| 2026-08-02 | 1.8030 | 1.9394 | 2.2165 | fw Aug |
| 2026-08-03 | 1.7966 | 1.9603 | 2.2031 | fw Aug |
| 2026-08-04 | 1.8217 | 1.8902 | 2.1348 | fw Aug |
| 2026-08-05 | 1.8651 | 2.0193 | 2.2425 | fw Aug |
| 2026-08-06 | 1.8425 | 2.1046 | 2.4471 | fw Aug |
| **2026-08-07** | **1.8671** | **2.1857** | **2.5211** | fw Aug |

---

## X-2. APPEND DAILY

### Schema update: 11 cột mới thêm (col 42-52, không backfill)

| Col | Tên | Ghi chú |
|---|---|---|
| 42 | gom_A | GOM-A fire flag; gLSR>>1.1 → False toàn bộ window |
| 43 | gom_B | GOM-B fire flag; div_ratio>>0.5 → False toàn bộ window |
| 44 | vol_alpha | ABSTAIN(API400) — klines endpoint 400 |
| 45 | taker_alpha | ABSTAIN(L-48) |
| 46 | spot_perp_ratio | None 08-06/07 (spot MISSING) |
| 47 | depth_ratio | None (chỉ điền khi có depth snap) |
| 48 | ret_7d | Computed từ px_avg |
| 49 | ret_30d | Computed từ px_avg |
| 50 | vol_vs_med14 | vol / median(vol_14d) |
| 51 | lsr_taker_r | taker_ratio từ freshwatch |
| 52 | ret_atl | vs ATL=0.000735 |

### UPDATE row 330 (2026-08-05): partial → complete

| Field | Trước | Sau | Nguồn |
|---|---|---|---|
| vol_perp_usd | $598,638 | $2,549,221 | fw_aug |
| taker_buy_pct | 0.56402 | 0.49153 | fw_aug |
| f_avg | 0.000290 | 0.000142 | fw_aug |
| f_min | 0.000170 | 0.000050 | fw_aug |
| f_max | 0.000411 | 0.000411 | fw_aug |
| f_n | **2** | **6** | fw_aug |
| data_bad | **1** | **0** | fw_aug |
| vol_vs_med14 | None | 1.051 | computed |

### APPEND rows mới

| Field | 2026-08-06 | 2026-08-07 |
|---|---|---|
| px_avg | 0.001624 | 0.001739 |
| ret_1d | +2.39% | +7.11% |
| vol_perp_usd | $2,269,665 | **$6,048,619** |
| taker_buy_pct | 49.44% | 46.58% |
| f_avg | 0.000182 | 0.000108 |
| f_min | 5.0e-5 | 5.0e-5 |
| f_max | 0.000396 | 0.000155 |
| f_n | 6 | 6 |
| funding_regime | volatile | low |
| oi_usd | $12,422,964 | $13,000,982 |
| oi_vs_med14 | 1.041 | 1.092 |
| oi_cycle_pos | 0.479 | 0.560 |
| lsr_pos_r | 1.8425 | 1.8671 |
| lsr_acc_r | 2.1046 | 2.1857 |
| lsr_global_r | 2.4471 | 2.5211 |
| div_raw | 0.8755 | 0.8542 |
| div_avg3 | 0.921 | 0.884 |
| glsr_slope_5d | 0.050 | 0.095 |
| d_pos_3d | -0.044 | +0.070 |
| d_acc_3d | +0.196 | +0.226 |
| vol_vs_med14 | 0.943 | **2.493** |
| lsr_taker_r | 0.978 | 0.872 |
| gom_A | 0 | 0 |
| gom_B | 0 | 0 |
| spot_venue | BSC_DEX_PancakeSwapV3_0.01% | BSC_DEX_PancakeSwapV3_0.01% |
| vol_spot_usd | MISSING (GT 403) | MISSING (GT 403) |
| vol_alpha | ABSTAIN(API400) | ABSTAIN(API400) |
| taker_alpha | ABSTAIN(L-48) | ABSTAIN(L-48) |
| data_bad | 0 | 0 |

> **Ghi chú vol 08-07**: $6.05M = 2.49× med14 ($2.43M). Spike đáng chú ý — ret +7.1% cùng ngày.  
> **Ghi chú gom_A/gom_B**: cả window LSR 30d đều False (gLSR min=2.13 >> 1.1 → A2 fails; div_ratio ~1.0 >> 0.5 → B1 hedge_structure fails).

---

## X-3. BẢNG A.5 BA-ĐẠO-HÀM

**Target: 2026-08-07**

| Mốc | date | div_avg3 | gLSR | vol_vs_m14 | div_raw | pos_r | acc_r |
|---|---|---|---|---|---|---|---|
| 28d | 2026-07-07 | 1.087 | 1.831 | 2.339 | 1.102 | 1.942 | 1.762 |
| 21d | 2026-07-14 | 1.678 | 1.308 | 2.067 | 1.553 | 2.042 | 1.315 |
| 14d | 2026-07-21 | 1.771 | 1.213 | 0.349 | 1.620 | 1.950 | 1.204 |
| 7d | 2026-07-31 | 1.120 | 2.017 | 0.413 | 0.991 | 1.956 | 1.973 |
| today | 2026-08-07 | **0.884** | **2.521** | **2.399** | **0.854** | **1.867** | **2.186** |

**%CHG từ 28d:**

| Field | 28d | 08-07 | %chg |
|---|---|---|---|
| div_avg3 | 1.087 | 0.884 | **-18.7%** |
| gLSR | 1.831 | 2.521 | **+37.7%** |
| vol_vs_m14 | 2.339 | 2.399 | +2.6% |
| div_raw | 1.102 | 0.854 | **-22.5%** |
| pos_r | 1.942 | 1.867 | -3.8% |
| acc_r | 1.762 | 2.186 | **+24.0%** |

**Pattern đọc:** gLSR tăng mạnh (+37.7%) trong khi div_avg3 giảm (-18.7%) — accounts (acc_r) đang bơm thêm trong khi positions (pos_r) phẳng → crowd dùng đòn bẩy nhiều hơn nhưng không mở thêm positions. Đây là tín hiệu crowd overleveraged, không phải kho build.

---

## X-3b. TRIGGER-CHECK (số cạnh ngưỡng, KHÔNG verdict)

| Trigger | Điều kiện nguyên văn | Giá trị hiện tại | Khoảng cách tới ngưỡng |
|---|---|---|---|
| T1 NEXT_IGNITION (C1) | gLSR < 1.2 | gLSR = 2.521 | -1.321 (cần giảm 52.4%) |
| T1 NEXT_IGNITION (C2) | div_raw > 1.5 | div_raw = 0.854 | +0.646 (cần tăng 75.6%) |
| T1 NEXT_IGNITION (C3) | f_avg ≤ 5.5e-5 AND f_min=5e-5 ≥7d | f_avg=0.000108, streak=0 | +53μ above floor, streak=0/7 |
| T1 NEXT_IGNITION (C4) | OI +20% từ floor $8.56M trong 5d | OI=$13.00M, 5d swing=+12% | 5d swing cần +20%/5d từ near-floor |
| T2 DIV_RECOVERY | div_raw > 1.5 ×≥3d | div_raw=0.854 (5d trend ↓) | +0.646 (+75.6%) |
| T3 gLSR_RESET | gLSR < 1.2 ×≥3d | gLSR=2.521 (7d trend ↑) | -1.321 (-52.4%) |
| T4 FUND_RESTABLE | f_avg ≤ 5.5e-5 AND f_min=5e-5 ×≥7d | f_avg=0.000108, streak=0 | +53μ above floor |
| T5 OI_BUILD | OI +20%/5d từ floor | 5d swing=+12% ($11.6M→$13.0M) | cần +20%/5d từ floor area |
| T6 BITMART_VOL | Confirm wash/real | — | PENDING OPERATOR |

**PIN streak history last 14d:**

| date | f_avg | f_min | PIN? |
|---|---|---|---|
| 2026-07-22 | 6.0e-5 | 5e-5 | ✗ |
| 2026-07-23 | 7.8e-5 | 5e-5 | ✗ |
| ... | ... | ... | ... |
| 2026-08-04 | 9.4e-5 | 5e-5 | ✗ |
| 2026-08-05 | 1.4e-4 | 5e-5 | ✗ |
| 2026-08-06 | 1.8e-4 | 5e-5 | ✗ |
| 2026-08-07 | 1.1e-4 | 5e-5 | ✗ |

*Streak = 0 ngày. f_avg chưa xuống sát floor (5.5e-5) trong toàn bộ 14d.*

---

## X-4. SPOT + ALPHA + DEPTH

### Alpha
- **alpha_id:** ALPHA_334 ✓ (BAPI xác nhận)
- **fullyDelisted:** False
- **Alpha klines endpoint:** HTTP 400 (permanent) → vol_alpha = ABSTAIN(API400)
- **taker_alpha:** ABSTAIN(L-48)

### Spot
- **venue_top:** Binance FAPI XPINUSDT (price discovery)
- **Spot venue:** BSC DEX PancakeSwapV3 0.01% pool 0x08de...4a4
- **GeckoTerminal API:** HTTP 403 Forbidden cho 08-06/08-07 → vol_spot MISSING 2 ngày
- **Dữ liệu cũ nhất có:** 08-05 (từ CASE cold-start: vol_spot=$154,800)
- **Note L-30:** Venue ngoài Binance (Gate/KuCoin) — không collect; CEX spot vol tổng từ CASE ~$571K/day est

### Depth Snap #1 — 09:18:03 UTC 08/08/2026

| Field | Giá trị |
|---|---|
| Mid | 0.001699 |
| Bid ±2% | $44,772 |
| Ask ±2% | $16,348 |
| Ratio (bid/ask) | 2.739 (bid-heavy) |
| Bid wall | px=0.001674, usd=$12,030 |
| Ask wall | px=0.001750, usd=$8,433 |

### Depth Snap #2 — 13:21:27 UTC 08/08/2026

| Field | Giá trị |
|---|---|
| Mid | 0.001675 |
| Bid ±2% | $34,419 |
| Ask ±2% | $15,489 |
| Ratio (bid/ask) | 2.2221 (bid-heavy) |
| Bid wall | px=0.001653, usd=$8,157 |
| Ask wall | px=0.001758, usd=$5,521 |
| Time gap | 4h 03m after snap #1 ✓ |

**Δ vs Snap #1 (09:18 UTC):**
| Field | Snap #1 | Snap #2 | Δ |
|---|---|---|---|
| Mid | 0.001699 | 0.001675 | -1.41% |
| Bid ±2% | $44,772 | $34,419 | -$10,353 (-23.1%) |
| Ask ±2% | $16,348 | $15,489 | -$859 (-5.3%) |
| Ratio | 2.7386 | 2.2221 | -0.5165 |

→ Cả bid lẫn ask thu hẹp theo giá, mid giảm -1.41%. Ratio vẫn bid-heavy (>2.0) nhưng giảm từ 2.74 → 2.22 — bid side co lại nhanh hơn ask. Cấu trúc bid-heavy duy trì qua 4h.

---

## X-5. ON-CHAIN

### X-5a: Contract Verify

| Source | alphaId | contract | Kết quả |
|---|---|---|---|
| alpha_id_map.json | ALPHA_334 | — | ✓ |
| BAPI live | ALPHA_334 | 0xd955c9ba56fb1ab30e34766e252a97ccce3d31a6 | ✓ |
| CASE sheet | ALPHA_334 | 0xd955c9ba56fb1ab30e34766e252a97ccce3d31a6 | ✓ |
| **Kết luận** | — | — | **PASS 3 sources (L-28)** |

### X-5a: BAPI Data (live 08/08/2026)

| Field | Giá trị |
|---|---|
| price | 0.001693 |
| volume24h | $1,313,462 |
| marketCap | $81,402,021 |
| fdv | $169,324,618 |
| totalSupply | 100,000,000,000 |
| circulatingSupply | 48,074,534,161 |
| holders | **69,247** (vs 69,318 cold-start 06/08 → -71) |
| fullyDelisted | False |
| listingCex | False |
| onlineAirdrop | True |

### X-5b: BscScan
- API V1: **NOTOK** (deprecated) → CẦN OPERATOR truy cập thủ công

### X-5c: Operator Checklist

**1. UNLOCK SCHEDULE (CRITICAL)**  
Hỏi: Team vesting contract trên BSC — có trên BscScan không?  
Contract: `0xd955c9ba56fb1ab30e34766e252a97ccce3d31a6`  
Tìm 'internal txns' hoặc 'token transfer' từ địa chỉ vesting.  
*Vì sao:* unlock event = potential supply shock — invalidates ignition window.

**2. TOP HOLDERS / KHO WALLET**  
Hỏi: Top 10 holders tại [BscScan Token Holders tab](https://bscscan.com/token/0xd955c9ba56fb1ab30e34766e252a97ccce3d31a6#balances)  
(a) Địa chỉ kho wallet team là gì?  
(b) Kho wallet có di chuyển token từ sau 08/08/2026 không?  
*Vì sao:* movement kho → sàn = phân phối, invalidates WATCH.

**3. EXCHANGE BALANCE TREND**  
Hỏi: Số dư XPIN tại Binance BSC `0x28C6c...d60` và Gate `0x0D070...e92Fe` — tăng hay giảm so với 08/07/2026?  
(a) Balance tăng → withdrawal-accelerant  
(b) Balance giảm → crowd rút về DEX  
*Vì sao:* leading indicator của OI divergence pattern.

**4. BITMART WASH TRADING**  
Hỏi: Mở BitMart XPIN live order book — spread là bao nhiêu?  
Vol $1.61M vs liq $4.8K = 338× ratio; nếu spread >5% = wash confirmed.  
*Vì sao:* xác định venue_top, ảnh hưởng detection floor tính toán.

**5. NANSEN (LOCKED)**  
Hỏi: (a) Smart Money wallets có hold XPIN không? (b) Exchange flow net 30d = deposit hay withdrawal?  
*Vì sao:* xác nhận P8 taker_detect (hiện ABSTAIN).

### X-5d: Unlock Sheet (PENDING OPERATOR)
- vesting_schedule: PENDING OPERATOR (BscScan contract)
- next_unlock_est: UNKNOWN
- kho_size_est: PENDING OPERATOR

---

## X-6. SỔ CHÉO

| Nguồn | Kết quả |
|---|---|
| alpha_id_map | XPIN → ALPHA_334 ✓ |
| freshwatch fw (all months) | 62 XPINUSDT rows (06-04→08-07) |
| gom_state | NOT FOUND locally (VPS state không copy về) |
| Other case EVENTS (grep XPIN) | 0 mentions |
| Other case MM_PROFILE (grep XPIN) | 0 mentions |
| Fresh-wallets log (gap 31/07-02/08 L-40) | Log path not found locally |
| MM vân tay | Chưa so sánh được (kho_vol_ratio = ABSTAIN) |

---

## X-7. SANITY CHECK

| # | Check | Kết quả |
|---|---|---|
| 1 | Metadata CASE đúng XPIN (lookup độc lập lần 2) | **PASS** (6/6: alphaId, contract, symbol, fullyDelisted, totalSupply, alpha_id_map) |
| 2 | LSR coverage 30d ≥50% non-null | **PASS** (pos/acc/gLSR 30/30; taker 0/30 permanent FAPI 404 không retry) |
| 3 | Append liền mạch không hở ngày | **PASS** (08-05→08-06→08-07, no gaps) |
| 4 | Spot-check 3 dòng append vs klines | **PASS** (vol diff 0.000%, taker diff <0.14%) |

**OVERALL: PASS**

---

## LAYER COVERAGE

| Layer | Status | Ghi chú |
|---|---|---|
| Perp klines | ✓ FULL | 33d klines + fw_aug canonical |
| Funding | ✓ FULL | 08-01→08-07 (f_n=6/day) |
| OI | ✓ FULL | 30d hist |
| LSR pos/acc/gLSR | ✓ FULL | 62 dates (fw) |
| LSR taker | ✗ PERMANENT MISSING | FAPI 404 không serve cho XPIN |
| Spot (BSC DEX) | ✗ MISSING 08-06/07 | GeckoTerminal 403 |
| Alpha vol/taker | ✗ ABSTAIN | klines API 400 |
| Depth | ✓ DONE | Snap #1 (09:18 UTC) + Snap #2 (13:21 UTC, 4h03m gap) |
| On-chain contract | ✓ PASS | BAPI + alpha_id_map + CASE |
| BscScan holders/tx | ✗ NOTOK | Deprecated V1 |
| Nansen | ✗ LOCKED | CẦN OPERATOR |

---

## MISSING LIST

| # | Mục | Tại sao | Hành động |
|---|---|---|---|
| ~~M-1~~ | ~~Depth snap #2~~ | ~~CẦN ≥13:18 UTC~~ | **DONE** — 13:21 UTC, ratio=2.22 bid-heavy maintained |
| M-2 | Spot vol 08-06/08-07 (BSC DEX) | GeckoTerminal 403 | Retry sau / operator check GT |
| M-3 | BscScan top holders + exchange balance | NOTOK deprecated V1 | CẦN OPERATOR (xem X-5c mục 2,3) |
| M-4 | Nansen on-chain | LOCKED | CẦN OPERATOR |
| M-5 | taker_lsr 30d | FAPI 404 permanent | Permanent — ghi án; không retry |
| M-6 | Unlock schedule (vesting) | BscScan NOTOK | CẦN OPERATOR (xem X-5c mục 1) |
| M-7 | BitMart wash confirm | Cần live order book check | CẦN OPERATOR (xem X-5c mục 4) |
| M-8 | kho wallet identification | Cần BscScan top holders | CẦN OPERATOR (xem X-5c mục 2) |
| M-9 | Smart money classification | Nansen LOCKED | CẦN OPERATOR |

---

## KEY NUMBERS TỔNG HỢP (08-07, close of refresh)

| Metric | Giá trị |
|---|---|
| px_avg 08-07 | 0.001739 (+7.1% ngày) |
| vol_perp 08-07 | $6,048,619 (2.49× med14) |
| taker 08-07 | 46.6% (sell-leaning) |
| gLSR 08-07 | 2.521 (NEW PEAK 30d, +37.7% vs 28d) |
| pos_r 08-07 | 1.867 |
| acc_r 08-07 | 2.186 (+24% vs 28d) |
| div_raw 08-07 | 0.854 (inverted: acc_r > pos_r) |
| div_avg3 08-07 | 0.884 (-18.7% vs 28d) |
| OI 08-07 | $13,001,000 (vs peak $15.6M, vs floor $8.56M) |
| oi_cycle_pos | 0.56 (mid-range 30d) |
| f_avg 08-07 | 0.000108 (low funding, not pinned) |
| depth ratio snap1 | 2.74 bid/ask (bid-heavy, 09:18 UTC) |
| depth ratio snap2 | 2.22 bid/ask (bid-heavy maintained, 13:21 UTC) |

**ATL:** 0.000735 → ret_atl 08-07 = +136.9%  
**ATH:** 0.010318 → px_vs_ath = -83.1%  
**holders:** 69,247 (live BAPI)

---

*DỪNG. Không verdict. Không đổi Status/TRIGGERS. Chờ operator đọc + snap #2 ≥13:18 UTC.*
