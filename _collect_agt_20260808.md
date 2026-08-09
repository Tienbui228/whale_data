# COLLECT AGT — 2026-08-08 (session 08:36→08:45 UTC)

**Case:** CASE_AGT.xlsx | Symbol: AGTUSDT | ALPHA_191 | BSC 0x5dbde81fce337ff4bcaaee4ca3466c00aecae274
**Câu hỏi case:** Có lực gom không? Ai kiểm soát giá, gom từ bao giờ, quy mô §3, và đang ở pha nào của vòng đời (build/ignite/harvest/nghỉ)?
**Quy tắc:** CHỈ THU THẬP + RAW — không verdict. Mọi số: nguồn + boundary + fn.

---

## A-0: VÁ BUILD_CASE.PY (diff thực hiện)

| Change | File | Lines | Nội dung |
|---|---|---|---|
| A-0a: load_alpha_meta() | build_case.py | +36 lines | Dynamic lookup từ alpha_id_map.json + pre-fetched BAPI/perp JSONs |
| A-0a: lsr_by_d normalize | build_case.py | +14 lines | Handle cả "pos_r" và "pos_r_raw" column names |
| A-0a: spot_by_d normalize | build_case.py | +8 lines | Map vol_quote_usd→vol_spot_usd, taker_pct→taker_spot_pct |
| A-0a: CASE sheet dynamic | build_case.py | -15/+21 lines | Xóa hardcode BANANAS31; dùng meta dict |
| A-0a: EVENTS seed dynamic | build_case.py | -4/+10 lines | Listing dates từ meta, không hardcode |
| A-0a: vol_alpha dynamic | build_case.py | -1/+2 lines | Kiểm tra fullyDelisted từ meta |
| A-0a: CASE_QUESTION param | build_case.py | +1 line | sys.argv[3] optional arg |
| A-0b: LSR guard | build_case.py | +10 lines | RAISE nếu pos_r null >50% last 30d |
| A-0b: Spot guard | build_case.py | +5 lines | WARNING nếu vol_spot null >50% last 30d |

**Bug phát hiện và sửa (TST retroactive):**
- `lsr_by_d.get("pos_r_raw")` = None cho fresh LSR CSV dùng "pos_r" column → normalized
- `spot_by_d.get("vol_spot_usd")` = None cho spot CSV dùng "vol_quote_usd" → normalized
- `if SYM_BASE == "BANANAS31"` hardcode trong vol_alpha → thay bằng `meta.get("fullyDelisted")`

---

## A-1: LSR PERSIST

| Endpoint | File | Rows | Window | fn | Status |
|---|---|---|---|---|---|
| topLongShortPositionRatio | agt_lsr_pos_20260808.json | 30 | 2026-07-10→2026-08-08 | 30d limit | ✓ |
| topLongShortAccountRatio | agt_lsr_acc_20260808.json | 30 | 2026-07-10→2026-08-08 | 30d limit | ✓ |
| globalLongShortAccountRatio | agt_lsr_glsr_20260808.json | 30 | 2026-07-10→2026-08-08 | 30d limit | ✓ |
| takerlongshortRatio | agt_lsr_taker_20260808.json | 30 | 2026-07-09→2026-08-07 | 30d limit | ✓ |

Merge → agt_lsr_raw_20260808.csv: 31 rows, 2026-07-09→2026-08-08
Coverage: pos_r_raw 30/31 non-null (08/08 partial day = 1 null).

**Freshwatch cross-ref:** 32 rows AGTUSDT (2026-06-27→2026-07-31) trong freshwatch_daily_*.csv → extends LSR to 2026-06-27.

Tổng LSR window sau merge freshwatch: **43 dates** (2026-06-27→2026-08-07).

---

## A-2: KLINES TRỌN ĐỜI

### Perp (AGTUSDT, 1d)
| Metric | Value |
|---|---|
| File | scratch/agt_perp_20260808.csv |
| Rows | 445 (post L-21 trim) |
| Boundary | 2025-05-20 → 2026-08-07 |
| L-21 | 2026-08-08 partial candle removed (collect tại 08:38 UTC, ngày chưa đóng) |
| Source | Binance FAPI /klines, interval=1d |

Last 5 perp rows:
```
date         o        h        l        c        vol_quote_usd  taker_pct  ret_1d
2026-08-03  0.01478  0.01487  0.01374  0.01404  1,137,067      46.35%     -1.16%
2026-08-04  0.01404  0.01464  0.01393  0.01427  2,899,044      46.84%     +1.64%
2026-08-05  0.01427  0.01434  0.01390  0.01403  895,395        46.88%     -1.68%
2026-08-06  0.01402  0.01432  0.01369  0.01404  1,621,680      48.04%     +0.07%
2026-08-07  0.01404  0.01527  0.01385  0.01489  1,330,207      48.43%     +6.11%
```

### Spot
| Metric | Value |
|---|---|
| Spot pair | **KHÔNG TỒN TẠI** (AGTUSDT HTTP 400 trên api.binance.com) |
| vol_spot_usd | MISSING — lý do: không có spot pair trên Binance |
| col_spot | Tất cả null — spot_perp_ratio = N/A |

### Alpha (ALPHA_191)
| Metric | Value |
|---|---|
| alphaId | ALPHA_191 |
| fullyDelisted | **False** (offsell=False, offline=False) |
| vol_alpha | alpha_klines_store(forward 2026-08-04, venue=binance_alpha) |
| taker_alpha | **ABSTAIN** (bapi alpha klines[9]==klines[5], L-48) |

---

## A-3: DAILY 50 COLS

| Metric | Value |
|---|---|
| Script | build_case.py AGTUSDT 20260808 (patched A-0) |
| Output | docs/case_files/CASE_AGT.xlsx |
| Sheets | CASE, DAILY, EVENTS, TRIGGERS, OUTCOME, MM_PROFILE, UNLOCK |
| DAILY rows | 445 (L-32 PASS) |
| Boundary | 2025-05-20 → 2026-08-07 |
| Cols | 50 |
| GOM-A fires | 0 |
| GOM-B fires | 0 |
| Events seeded | 80 rows (LISTING + DUMP_GT10PCT + VOL_8X_MED14) |

**Đặc điểm giá:**
| Metric | Value |
|---|---|
| ATH close | 0.034016 on 2025-05-27 (1 tuần sau listing!) |
| Close 07/08 | 0.014890 |
| Drawdown từ ATH | -56.23% |
| Ngày listing (perp) | 2025-05-20 |
| Ngày listing (Alpha) | 2025-05-16 |
| Dump days (ret≤-5%) | 103 / 445 = 23.1% |
| Red days last 30d | 10/30 |

---

## A-4: SPOT + ALPHA

### Depth snap #1 (08:44:20 UTC 08/08/2026)
| Metric | Value |
|---|---|
| mid | 0.0155015 |
| bid 2% depth | $8,669 USDT |
| ask 2% depth | $16,547 USDT |
| bid/ask ratio | 0.524 (ask-heavy — sell pressure > buy pressure) |
| Source | Binance FAPI depth?limit=500 |

Top 5 bids: 0.015484($370), 0.015483, 0.015481, 0.015476, 0.015475
Top 5 asks: 0.015519($65), 0.015520, 0.015522($100), 0.015523($65), 0.015525

Note: ask side ($16.5k) outweighs bid ($8.7k) ≈ 2:1 at time of snap.

### Depth snap #2 (13:21:23 UTC 08/08/2026)
| Metric | Value |
|---|---|
| mid | 0.01563050 |
| bid 2% depth | $15,990 USDT |
| ask 2% depth | $14,480 USDT |
| bid/ask ratio | 1.1043 (bid-slight-heavy) |
| Time gap | 4h 37m after snap #1 ✓ |

**Δ vs snap #1:**
| Metric | Snap #1 (08:44) | Snap #2 (13:21) | Δ |
|---|---|---|---|
| mid | 0.01550 | 0.01563 | +0.84% |
| bid ±2% | $8,669 | $15,990 | +$7,321 (+84.5%) |
| ask ±2% | $16,547 | $14,480 | -$2,067 (-12.5%) |
| ratio | 0.524 | 1.1043 | +0.5803 |

→ Bid depth tăng mạnh (+84.5%), ask giảm (-12.5%). Ratio đảo chiều từ ask-heavy (0.52) sang balanced/bid-slight (1.10). Price tăng nhẹ +0.84% trong 4h37m.

---

## A-5: ON-CHAIN / KHO

### BAPI Token Details
| Field | Value | Source |
|---|---|---|
| Contract (BSC) | 0x5dbde81fce337ff4bcaaee4ca3466c00aecae274 | BAPI token list |
| Name | Alaya Governance Token | BAPI |
| Total supply | 5,000,000,000 AGT | BAPI |
| Circ supply | 3,087,161,125 AGT | BAPI |
| Holders | 190,729 | BAPI |
| Alpha listing | 2025-05-16 (listingTime=1747386300000) | BAPI |
| Perp onboard | 2025-05-20 (onboardDate=1747737000000) | FAPI exchangeInfo |
| fullyDelisted | False | BAPI |
| chainId | 56 (BSC) | BAPI |

### Contract verify L-28
| Source | Status |
|---|---|
| BAPI token list | OK — primary source |
| BscScan V1 API | NOTOK (deprecated V1 endpoint) → **CẦN OPERATOR** |
| BscScan V2 API | Không implement — CẦN OPERATOR |
| Nansen | LOCKED → CẦN OPERATOR |

### Funding (Binance FAPI)
| Metric | Value |
|---|---|
| Records | 500 (API limit) |
| Boundary | 2026-05-17 → 2026-08-08 |
| Days | 84 |
| Funding character | **DƯƠNG** toàn bộ giai đoạn |

Last 5 days funding:
```
date        fn  f_avg      f_min      f_max
2026-08-04   6  +0.000153  +0.000050  +0.000276
2026-08-05   6  +0.000171  +0.000050  +0.000432
2026-08-06   6  +0.000277  +0.000050  +0.000577
2026-08-07   6  +0.000407  +0.000254  +0.000593
2026-08-08   3  +0.000331  +0.000224  +0.000523  (partial day)
```

Note: Funding tăng dần từ 04-07/08 (max 0.000593 = flat positive, NOT pinned [4e-5, 6e-5]). Khác hoàn toàn với TST (âm mạnh). pin_day = False trong toàn bộ window.

### OI Historical
| Metric | Value |
|---|---|
| Records | 30 (2026-07-10→2026-08-08) |
| 2026-07-10 | $3.28M (233.5M tokens) |
| 2026-08-07 | $3.13M (210.1M tokens) |
| 2026-08-08 partial | $3.49M (234.7M tokens) |
| Trend | Flat-ish, slight decline July then recovery |

---

## A-6: VPS + SỔ CHÉO

| Nguồn | Kết quả |
|---|---|
| freshwatch daily | AGTUSDT 32 rows (2026-06-27→2026-07-31) — extends LSR |
| freshwatch_daily_2026-06.csv | AGTUSDT rows extracted |
| freshwatch_daily_2026-07.csv | AGTUSDT rows extracted |
| VPS freshwatch Aug 2026 | MISSING — không có data Aug trong scratch |
| gom_state (session_state.json) | AGT: {} — không có open chain |
| u50 universe | AGT có trong alpha_id_map.json (ALPHA_191) |
| CASE_INDEX | Row 15 đã đăng ký (08:45 UTC) |
| INDEX.md | Row AGT added |
| Ledger/CAMPAIGNS | Chưa kiểm — CẦN |
| CASE_HEI/BANANAS31 cross-ref | Không có AGT mention |

---

## A.5 BẢNG BA-ĐẠO-HÀM (mốc 7/14/21/28d trước 07/08/2026)

LSR window: 2026-06-27 (freshwatch) + 2026-07-10 (fresh). Computed từ scratch CSVs.

| Biến | 28d (11/07) | 21d (18/07) | 14d (25/07) | 7d (01/08) | 07/08 |
|---|---|---|---|---|---|
| pos_r | 1.4910 | 1.4372 | 1.4778 | 1.5096 | 1.5733 |
| acc_r | 1.7218 | 2.1486 | 2.1387 | 2.4388 | 2.6088 |
| gLSR | 1.5265 | 2.4722 | 2.2331 | 2.7467 | 2.7327 |
| div_avg3 | N/A¹ | 0.6525 | 0.6742 | 0.5996 | 0.6638 |

¹ 28d (11/07) = index 2 vào window fresh LSR → div_avg3 cần 3 ngày liên tiếp có pos_r. 07/10 là ngày đầu fresh LSR.

**gLSR 28d:** min=1.5265 max=3.2499 (peak 02/08: 3.25)
- gLSR crosses 0.7/1.0/1.1/1.5: **NONE** trong toàn bộ 28d
- gLSR chưa bao giờ xuống dưới 1.53 trong 28d → GOM-A A2 FAIL toàn bộ

**vol_vs_m avg7 ending at mốc:**
| Mốc | avg7 | n |
|---|---|---|
| 28d (11/07) | 0.758 | 7 |
| 21d (18/07) | 0.583 | 7 |
| 14d (25/07) | 2.082 | 7 |
| 7d (01/08) | 1.214 | 7 |
| 07/08 | 1.240 | 7 |

Note: vol bình thường (~1x), spike 25/07 avg7 là do 20/07 spike (6.57x trong cluster).

**Trajectory pos_r / acc_r / div_avg3 (42d):**
- pos_r cực kỳ ổn định: 1.39→1.57 (range chỉ 0.18) → không spike như TST
- acc_r TĂNG DẦN: 1.24→2.61 (tăng x2 trong 42d)
- div_avg3 = pos_r/acc_r: 1.39→0.66 (GIẢM từ tháng 6) → nhiều tài khoản long hơn (retail crowd)
- Sign-corr: 53.8% OPPOSITE (pos_r tăng khi giá giảm — crowd long trong dump)
- pos_r OLS slope last 30d: +0.0048/ngày RISING nhẹ

---

## NHỊP CỤM PUMP LỊCH SỬ (vol ≥8x med14)

19 events trong 445 ngày (2025-05-20→2026-08-07). Clusters:

| Cluster | Dates | Đỉnh vol_vs_m | Gap tới cluster tiếp |
|---|---|---|---|
| C1 | 2025-07-09 (1 ngày) | 8.26x | 23 ngày |
| C2 | 2025-08-01/02 (2 ngày) | 19.41x | 75 ngày |
| C3 | 2025-10-17 (1 ngày) | 8.12x | 73 ngày |
| C4 | 2025-12-29 (1 ngày) | 9.67x | 98 ngày |
| C5 | 2026-04-07,09,10 (3 ngày) | 93.22x | 16 ngày |
| C6 | 2026-04-26,27,28 (3 ngày) | 45.83x | 28 ngày |
| C7 | 2026-05-08 (1 ngày) | 11.64x | 14 ngày |
| C8 | 2026-05-22,24,25 (3 ngày) | 75.17x | 23 ngày |
| C9 | 2026-06-17,18,19,20 (4 ngày) | 84.16x | >49 ngày |

ATH context: 0.034016 on 2025-05-27, ngay sau C8 (2026-05-24/25 là mốc gần nhất — wait, this is 2026, ATH is 2025-05-27, so C8 is 2026 which is after ATH). Actually ATH = 2025-05-27, and C8 = 2026-05-22/24/25 = 1 year later.

Clusters C5-C9 (April-June 2026, 5 clusters trong 70 ngày) là giai đoạn mật độ cao nhất.
Sau C9 (tháng 6), không có cluster nào ≥8x trong >49 ngày tới 07/08.

Mỗi cluster: chỉ số, không kết luận ai làm.

---

## B-2 DIAGNOSTIC FLAGS (445 ngày)

| Flag | Count | Total | Rate |
|---|---|---|---|
| flag_dist_wall_day (taker≥50% + ret<0) | 44 | 445 | 9.9% |
| flag_decay_day (taker<45%) | nhiều — từ DAILY | — | — |
| flag_knife_crowd (gLSR↑ + ret<-3%) | 7 | 444 | — |
| flag_hedge_struct (div_avg3≤0.5) | 2 (07-29/07-30) | — | — |
| flag_neg_div | 0 (funding không âm) | — | — |

7 knife_crowd events (gLSR tăng + ret<-3%):
- 2026-07-01: ret=-14.99% (gLSR rising)
- 2026-07-02: ret=-17.97%
- 2026-07-03: ret=-20.66%
- 2026-07-05: ret=-18.35%
- 2026-07-08: ret=-5.31%
- 2026-07-20: ret=-20.95% (vol 6.57x)
- 2026-07-28: ret=-10.84%

Pattern: July 2026 là giai đoạn dump nặng nhất với knife_crowd liên tiếp.

---

## A-7: SANITY CHECK (4 mục)

| # | Item | Kết quả | Chi tiết |
|---|---|---|---|
| [1] | Contract 0x5dbde81... + ALPHA_191 + supply 5B | **PASS** | Khớp BAPI lookup độc lập |
| [2] | LSR coverage: pos_r null last 30d | **PASS** | 3.3% null (1/30 = 08/08 partial) |
| [3] | Spot coverage: vol_spot_usd last 30d | **WARNING** | 100% null — lý do: NO spot pair on Binance |
| [4] | DAILY last row = 07/08, count = 445 | **PASS** | last_date=2026-08-07, count=445 |

**OVERALL: PASS** (WARNING [3] đã có lý do rõ ràng)

---

## LAYER COVERAGE — 4 LỚP

| Lớp | Nguồn | Coverage | Status |
|---|---|---|---|
| L1: Perp price/vol | Binance FAPI klines 1d | 2025-05-20→2026-08-07, 445 ngày | ✓ DONE |
| L1: Spot price/vol | Binance api/v3 | **NO PAIR** — AGTUSDT spot không tồn tại | DOCUMENTED |
| L1: Alpha klines | Binance BAPI alpha (store) | Forward từ 2026-08-04, taker=ABSTAIN | ABSTAIN (L-48) |
| L2: LSR (4 endpoints) | FAPI 30d + freshwatch | 2026-06-27→2026-08-07 (43 ngày) | ✓ DONE |
| L2: Funding | FAPI hist | 2026-05-17→2026-08-08, 500 records | ✓ DONE |
| L2: OI | FAPI OI hist | 2026-07-10→2026-08-08, 30 records | ✓ DONE |
| L2: Depth | FAPI depth snap | Snap #1 08:44 UTC + snap #2 13:21 UTC (4h37m gap) | ✓ DONE |
| L3: On-chain | BAPI (primary) | contract+supply+holders confirmed | PARTIAL |
| L3: Top holders | BscScan V1 | NOTOK (deprecated) | MISSING |
| L3: Nansen | LOCKED | — | LOCKED |
| L4: VPS freshwatch | freshwatch_daily | Jun+Jul OK; Aug MISSING | PARTIAL |
| L4: Venue ngoài Binance | Bitget/OKX | Không collect (L-30) | MISSING |

---

## MISSING — GOM MỘT CHỖ

| # | Item | Lý do | Action |
|---|---|---|---|
| ~~M-1~~ | ~~Depth snap #2~~ | ~~CẦN ≥12:44 UTC~~ | **DONE** — snap #2 tại 13:21 UTC (ratio=1.10 bid-slight) |
| M-2 | BscScan top holders | NOTOK V1 deprecated | CẦN OPERATOR |
| M-3 | Nansen on-chain | NANSEN_KEY_LOCKED | CẦN OPERATOR |
| M-4 | VPS freshwatch Aug 2026 | Không SCP sang scratch | CẦN |
| M-5 | Venue ngoài Binance | Bitget/OKX spot/perp AGT | L-30 scope — CẦN |
| M-6 | Contract verify L-28 | Chỉ 1 nguồn (BAPI) | CẦN OPERATOR |
| M-7 | Spot pair on Binance | Không có AGTUSDT spot | PERMANENT (documented) |
| M-8 | Funding hist trước 05/17 | API 500 record limit → ~84 ngày | Không có |

---

## BUILD_CASE.PY PATCH — diff tóm tắt (A-0)

Trước: 5 giá trị hardcode (ALPHA_21, contract BANANAS31, holders, listing dates, case question).
Sau: tất cả dynamic từ `load_alpha_meta(sym_base, date_tag, scratch)` đọc pre-fetched JSON.
Bug fix: lsr key mismatch + spot key mismatch (cả hai TST và AGT bị ảnh hưởng).
Guard: RAISE nếu LSR >50% null; WARNING nếu spot >50% null.

---

## GHI CHÚ KỶ LUẬT

- L-38: LSR persist chạy đầu tiên (08:36 UTC), trước mọi step khác
- L-21: Trim 2026-08-08 partial candle (collect tại 08:38 UTC, candle chưa đóng)
- L-24/25: fn ghi kèm: funding fn=6/ngày (4h), OI fn=30, LSR fn=30
- L-48: taker_alpha=ABSTAIN (bapi alpha klines[9]==klines[5])
- L-28: contract chỉ verify từ BAPI 1 nguồn → ghi PARTIAL, CẦN OPERATOR
- A-0b guard: chạy sau L-32 verify, không silent-ship
- Verdict: DỪNG. Chờ operator đọc.

---

*Generated: 2026-08-08 08:45 UTC | Agent session d:\Data back test\whale_data*
