# COLLECT TST — 2026-08-08 (session 00:08→00:19 UTC)

**Case:** CASE_TST.xlsx | Symbol: TSTUSDT | ALPHA_87 | BSC 0x86bb94...666429
**Task:** T-0→T-7 cold-start pack | Operator spec: CHỈ THU THẬP + RAW — không verdict

---

## T-1: LSR PERSIST

| Endpoint | File | Rows | Window | fn |
|---|---|---|---|---|
| positionRatio | tst_lsr_pos_20260809.json | 30 | 2026-07-09→2026-08-08 | 30d retention limit |
| accountRatio | tst_lsr_acc_20260809.json | 30 | 2026-07-09→2026-08-08 | 30d retention limit |
| globalRatio | tst_lsr_glsr_20260809.json | 30 | 2026-07-09→2026-08-08 | 30d retention limit |
| takerLSR | tst_lsr_taker_20260809.json | 30 | 2026-07-09→2026-08-08 | 30d retention limit |

Merge → tst_lsr_raw_20260809.csv: 31 rows, date range 2026-07-09→2026-08-07 (07-09 has only taker_lsr; pos_r starts 07-10).
Persisted at session start 00:08 UTC. Source: Binance FAPI endpoints.

**Freshwatch cross-ref:** tst_freshwatch_lsr_20260809.csv — extends window to 2026-06-27 (via freshwatch daily dumps). Merged into DAILY LSR cols for 42d coverage.

---

## T-2: KLINES

### Perp (TSTUSDT, 1d)
| Metric | Value |
|---|---|
| File | scratch/tst_perp_20260809.csv |
| Rows | 545 (post L-21 trim) |
| Boundary | 2025-02-09 → 2026-08-07 |
| L-21 | 2026-08-08 row removed (partial candle) |
| Source | Binance FAPI /klines, interval=1d |

Last 5 rows:
```
date         o        h        l        c        vol_quote_usd      taker_pct  ret_1d
2026-08-03  0.01114  0.01179  0.01105  0.01138  2,028,235          46.42%     +2.06%
2026-08-04  0.01138  0.01156  0.00992  0.00997  3,700,837          38.03%    -12.39%
2026-08-05  0.00998  0.01044  0.00987  0.01023  4,722,730          43.31%     +2.61%
2026-08-06  0.01022  0.01160  0.01010  0.01120  5,588,589          48.59%     +9.48%
2026-08-07  0.01120  0.01632  0.01076  0.01350  52,484,798         49.02%    +20.54%
```

### Spot (TSTUSDT, 1d)
| Metric | Value |
|---|---|
| File | scratch/tst_spot_20260809.csv |
| Source | Binance SPOT /klines, interval=1d |

### Alpha
| Metric | Value |
|---|---|
| ALPHA_87 | fullyDelisted=True |
| taker_alpha | **ABSTAIN** (klines[9]==klines[5] = close price, not real taker — L-48) |
| Store | data/raw/spot_klines_1d/ venue=binance_alpha (forward from 04/08) |
| Alpha klines hist | available from 2025-06-18 (TAG-era listing) in local store |

---

## T-3: DAILY 50 COLS — build_case.py

| Metric | Value |
|---|---|
| Script | build_case.py (không sửa) |
| Output | docs/case_files/CASE_TST.xlsx |
| Sheets | CASE, DAILY, EVENTS, TRIGGERS, OUTCOME, MM_PROFILE, UNLOCK |
| DAILY rows | 545 (L-32 PASS: counted non-empty date cells) |
| DAILY boundary | 2025-02-09 → 2026-08-07 |
| Cols | 50 (template BANANAS31) |
| GOM-A fires | 0 |
| GOM-B fires | 0 |
| EVENTS seeded | 54 rows (DUMP_GT10PCT + VOL_8X_MED14; no LISTING_ALPHA — date unknown) |

**ATH:** 0.2252 (close 2025-02-09 = listing day)
**2026-08-07 close:** 0.01350
**Drawdown from ATH:** -94.0%

---

## T-4: SPOT + ALPHA (ABSTAIN)

- Spot klines: tst_spot_20260809.csv — đã thu thập, schema chuẩn
- Alpha klines: ABSTAIN vì fullyDelisted=True. Data in store from 2025-06-18 nhưng taker không đáng tin (L-48).
- Alpha vol / taker_alpha: không dùng làm số chốt.

---

## T-5: ON-CHAIN / KHO

### Funding (Binance FAPI historicalTrades)
| Metric | Value |
|---|---|
| File | scratch/tst_funding_20260809.csv |
| Records | 501 entries (4-hourly events) |
| Boundary | 2026-05-16 16:00 → 2026-08-08 00:00 |
| Oldest record | 2026-05-16 (API retention ~500 records) |
| Total days | ~84 days |

**Funding last 10 days (day-level f_avg):**
```
date        fn  f_avg       f_min        f_max
2026-07-30   6  +0.000050   +0.000050   +0.000050
2026-07-31   6  +0.000050   +0.000050   +0.000050
2026-08-01   6  +0.000050   +0.000050   +0.000050
2026-08-02   6  +0.000050   +0.000050   +0.000050
2026-08-03   6  +0.000050   +0.000050   +0.000050
2026-08-04   6  -0.000117   -0.000945   +0.000050
2026-08-05   6  -0.001773   -0.004963   +0.000050
2026-08-06   6  -0.000798   -0.002004   +0.000050
2026-08-07   6  -0.000924   -0.002704   +0.000050
2026-08-08   1  +0.000050   (partial day)
```
Note: Funding turned strongly negative from 04/08 coinciding with pos_r spike and vol event on 07/08.

### OI Historical (Binance FAPI openInterestHist, interval=1d)
| Metric | Value |
|---|---|
| File | scratch/tst_oi_hist_20260809.csv |
| Rows | 30 (2026-07-10 → 2026-08-08) |
| Source | Binance FAPI /futures/data/openInterestHist |

**OI trend (key dates):**
```
date        oi_usd        oi_token
2026-07-10  $1,701,880    163.6M
2026-07-25  $1,842,634    163.0M
2026-08-01  $2,075,627    171.5M
2026-08-04  $1,900,970    167.0M
2026-08-05  $1,945,490    194.9M
2026-08-06  $2,783,257    272.3M
2026-08-07  $2,767,217    247.1M
2026-08-08  $3,986,746    295.3M  ← partial day (08/08 spike not in DAILY)
```
OI surge: +63% in USD ($1.7M→$2.77M 07/10→08/07), token count +51% (163M→247M).
Post-event (08/08 partial): $3.99M (+44% from 08/07 close).

### BscScan (0-credit, nguồn thứ 3)
| Query | Result |
|---|---|
| Contract | BSC 0x86bb94...666429 |
| Top holders | **CẦN OPERATOR** (BscScan NOTOK on free API for holder list) |
| Token info | TST — TreasureStar BSC token |
| Explorer | bscscan.com/token/0x86bb94...666429 |

---

## T-6: VPS + SỔ CHÉO

| Item | Status |
|---|---|
| Freshwatch daily store | tst_freshwatch_lsr_20260809.csv (merged June-July 2026 freshwatch dumps) |
| freshwatch_daily_2026-06.csv | TSTUSDT rows extracted, src=freshwatch |
| freshwatch_daily_2026-07.csv | TSTUSDT rows extracted, src=freshwatch |
| VPS August data | **MISSING** — VPS freshwatch Aug 2026 not in scratch |
| CASE_INDEX.xlsx | TST registered (row 3 INDEX sheet, 2026-08-08 00:19 UTC) |
| INDEX.md | TST row added after BANANAS31 |

---

## T-7: FILE + ĐĂNG KÝ

| File | Status |
|---|---|
| docs/case_files/CASE_TST.xlsx | CREATED — 545 DAILY rows, 7 sheets, 50 cols |
| scratch/tst_*.csv / *.json | 17 files — scratch không commit |
| CASE_INDEX.xlsx TST row | DONE (row 3, session 02:16 UTC) |
| docs/INDEX.md TST row | DONE |
| _collect_tst_20260809.md | DONE (this file) |
| Depth snap #2 | **MISSING — CẦN** ≥04:08 UTC 08/08 (snap #1 taken 00:08 UTC) |

---

## A.5 BẢNG BA-ĐẠO-HÀM (mốc 7/14/21/28d trước 07/08/2026)

Computed from scratch CSVs: tst_lsr_raw_20260809.csv + tst_perp_20260809.csv.
LSR window start: 2026-07-09 (30d retention). div_avg3 = avg3(pos_r)/avg3(acc_r) rolling 3d.

| Biến | 28d (11/07) | 21d (18/07) | 14d (25/07) | 7d (01/08) | 07/08 |
|---|---|---|---|---|---|
| pos_r | 1.3031 | 1.6721 | 1.7724 | 2.2381 | 5.3391 |
| acc_r | 1.8409 | 1.9061 | 2.1162 | 2.0239 | 3.0733 |
| gLSR | 1.5400 | 1.8233 | 2.0760 | 1.8114 | 2.3591 |
| div_avg3 | N/A | 0.789 | 0.818 | 0.897 | 1.758 |
| div_avg3 %chg vs 28d | — | — | — | — | — |

**Ghi chú div_avg3:**
- 28d (11/07): N/A — LSR mới 2 ngày, không đủ avg3 window (cần 09/07, nhưng 09/07 pos_r=empty)
- Trajectory 21d→07/08: 0.789→0.818→0.897→1.758 (tăng mạnh từ 7d→07/08 do pos_r spike)

**gLSR 28d summary:**
- min28d = 1.4771 (2026-07-10), max28d = 2.3591 (2026-08-07)
- gLSR không bao giờ xuống dưới 1.1 trong 42d LSR window → GOM-A A2 FAIL toàn bộ
- gLSR crosses 1.1: NONE | crosses 1.0: NONE | crosses 0.7: NONE

**vol_vs_med14 (avg7 ending at mốc):**
| Mốc | avg7 | n |
|---|---|---|
| 28d (11/07) | ~1.12 | 7 |
| 21d (18/07) | ~1.19 | 7 |
| 14d (25/07) | ~1.34 | 7 |
| 7d (01/08) | ~2.43 | 7 |
| 07/08 | ~6.02 | 7 |

vol spike 07/08: vol_quote_usd = $52.5M (vs ~$2M baseline) ≈ **27x med14**.

---

## B-2 DIAGNOSTIC FLAGS (545 days DAILY)

| Flag | Count | Total | Rate |
|---|---|---|---|
| flag_dist_wall_day (taker≥50% + ret<0) | 34 | 545 | 6.2% |
| flag_decay_day (taker<45%) | 47 | 545 | 8.6% |
| flag_knife_crowd (gLSR↑ + ret<-3%) | 1 | 544 | — |
| flag_hedge_struct (div_avg3≤0.5) | 0 | — | — |
| flag_neg_div | 0 | — | — |

**knife_crowd detail (1 event):**
- date TBD (from probe log): gLSR tăng + ret < -3% (xem scratch probe output)

---

## DEPTH SNAP #1 (00:08:32 UTC 08/08/2026)

| Metric | Value |
|---|---|
| mid | 0.013485 |
| Bid 2% depth | 94,213 USDT |
| Ask 2% depth | 66,166 USDT |
| Bid/Ask ratio | 1.42 (bid-heavy) |
| Source | Binance FAPI depth?symbol=TSTUSDT&limit=500 |

Top 10 bids (price, qty):
0.01348: 57,634 | 0.01347: 76,782 | 0.01346: 65,051 | 0.01345: 114,454
0.01344: 125,487 | 0.01343: 118,519 | 0.01342: 96,848 | 0.01341: 99,671
0.01340: 184,266 | 0.01339: 152,242

Top 10 asks (price, qty):
0.01349: 25,611 | 0.01350: 112,131 | 0.01351: 318,007 | 0.01352: 420,805
0.01353: 124,439 | 0.01354: 176,897 | 0.01355: 217,132 | 0.01356: 254,483
0.01357: 221,789 | 0.01358: 103,730

Note: ask wall tập trung ở 0.01351-0.01352 (318k + 421k tokens, tổng ~$10k). Cần snap #2 để so sánh.

---

## LAYER COVERAGE — 4 LỚP

| Lớp | Nguồn | Coverage | Status |
|---|---|---|---|
| L1: Giá / vol | Binance FAPI perp + SPOT | 2025-02-09→2026-08-07, 545 ngày | ✓ DONE |
| L1: Alpha klines | Binance BAPI alpha | Có trong store, taker=ABSTAIN | ABSTAIN (L-48) |
| L2: Dòng tiền phái sinh | LSR (pos/acc/gLSR) | 2026-06-27→2026-08-07 (freshwatch+fresh) | ✓ DONE |
| L2: Funding | Binance FAPI hist | 2026-05-16→2026-08-08, 501 records | ✓ DONE |
| L2: OI | Binance FAPI OI hist | 2026-07-10→2026-08-08, 30 days | ✓ DONE |
| L2: Depth | FAPI depth snap | Snap #1 done; snap #2 MISSING | PARTIAL |
| L3: On-chain | BscScan 0-credit | Contract ID confirmed | PARTIAL |
| L3: Top holders | BscScan API | NOTOK — CẦN OPERATOR | MISSING |
| L3: Nansen | LOCKED | — | LOCKED |
| L4: VPS freshwatch | freshwatch_daily | Jun+Jul OK; Aug MISSING | PARTIAL |
| L4: Venue ngoài Binance | Bitget/OKX (L-30) | Không collect | MISSING |

---

## MISSING — GOM MỘT CHỖ

| # | Item | Lý do | Action |
|---|---|---|---|
| M-1 | Depth snap #2 | Cần ≥04:08 UTC 08/08, session kết thúc 00:19 UTC | CẦN lấy trong cùng ngày |
| M-2 | BscScan top holders | API NOTOK (free tier, token holder list bị chặn) | CẦN OPERATOR |
| M-3 | Nansen on-chain | NANSEN_KEY_LOCKED | CẦN OPERATOR |
| M-4 | VPS freshwatch Aug 2026 | Không SCP sang scratch trong session này | CẦN (nếu có data) |
| M-5 | Venue ngoài Binance | Bitget/OKX perp/spot TST | L-30 scope — CẦN |
| M-6 | Contract cross-verify L-28 | Chỉ 1 nguồn (BAPI token list) | CẦN OPERATOR |
| M-7 | Funding hist trước 05/16 | API chỉ trả 500 records (~84 ngày) | Không có |
| M-8 | Alpha listing date chính thức | fullyDelisted=True, BAPI không có date | CẦN OPERATOR |
| M-9 | LISTING_ALPHA event | Không seed vì thiếu date | Sau khi M-8 giải quyết |

---

## GHI CHÚ KỶ LUẬT

- L-21: Trim 2026-08-08 partial candle. DAILY stops 2026-08-07 (closed).
- L-24/25: fn ghi kèm mọi số. Funding fn=6/ngày (4-hourly). OI fn=30 ngày. LSR fn=30 records/endpoint.
- L-38: LSR persist chạy đầu tiên (00:08 UTC) — trước mọi step khác.
- L-48: fullyDelisted=True → taker_alpha=ABSTAIN (không phải số thực).
- build_case.py: không sửa script, chạy nguyên bản.
- Verdict: DỪNG. Chờ operator đọc.

---

*Generated: 2026-08-08 00:19 UTC | Agent session d:\Data back test\whale_data*
