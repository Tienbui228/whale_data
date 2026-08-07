# COLLECT HEI — Cold-Start Pack  |  2026-08-08

Session: 2026-08-08. Operator lệnh: cold-start HEIUSDT.  
Status: `COLD_START — PENDING (verdict trong tay operator)`.  
L-21: 2026-08-08 NOT in DAILY (cron 00:05 UTC chưa chạy).  
L-38: LSR 30d retention → persisted khẩn cấp đầu session.

---

## H0 — IDENTITY

| Field | Value | Source |
|---|---|---|
| Symbol | HEIUSDT | Binance exchangeInfo |
| underlyingType | COIN | fapi exchangeInfo |
| underlyingSubType | Infrastructure | fapi exchangeInfo |
| contractType | PERPETUAL | fapi exchangeInfo |
| Perp listing (onboardDate) | 2025-02-13 | fapi exchangeInfo |
| Spot listing | 2025-02-13 | api/v3 exchangeInfo |
| Alpha listing | N/A — HEI not in alpha_id_map | grep alpha_id_map.json → no match |
| Contract candidate | 0xf8f173e20e15f3b6cb686fb64724d370689de083 | CoinGecko id=heima, rank=910 — **UNVERIFIED** |
| Homepage candidate | https://www.heima.network/ | CoinGecko — **UNVERIFIED** |

**Ghi chú:** Operator phải xác nhận contract address trước khi dùng bất kỳ on-chain data nào.

---

## H1 — PERP DAILY TABLES (source: Binance fapi)

### H1a — LSR (4 endpoints, L-38: 30d retention limit)

| Endpoint | Rows | Window | fn |
|---|---|---|---|
| topLongShortPositionRatio | 31 | 2026-07-08 → 2026-08-07 | fapi/v1, period=1d, limit=30 |
| topLongShortAccountRatio | 31 | 2026-07-08 → 2026-08-07 | fapi/v1, period=1d, limit=30 |
| globalLongShortAccountRatio | 31 | 2026-07-08 → 2026-08-07 | fapi/v1, period=1d, limit=30 |
| takerlongshortRatio | 31 | 2026-07-08 → 2026-08-07 | fapi/v1, period=1d, limit=30 |

Lưu: `scratch/hei_lsr_raw_20260808.csv` (31 rows, 8 cols: date, pos_r_raw, acc_r_raw, glsr_raw, taker_lsr_raw, pos_r_boundary, acc_r_boundary, glsr_boundary).  
**L-38 boundary:** Giá trị là snapshot 00:00 UTC daily, không phải intraday average.

Range 31-ngày:
- pos_r (topLongShortPositionRatio): 1.1002 → 2.7774 (min 2026-08-07, max ~2026-08-04)
- gLSR (globalLongShortAccountRatio): 0.3824 → 1.0387 — crowd net SHORT toàn bộ cửa sổ
- taker_lsr (takerlongshortRatio): biến động kèm sự kiện spike

### H1b — Funding rates

| Metric | Value | Source |
|---|---|---|
| Days với data | 82 ngày | fapi/v1/fundingRate limit=1000 |
| Window ước tính | ~2026-05-18 → 2026-08-07 | |
| fn/ngày | 6 (interval 4h) | first-day count = 6 settlements |
| data_ok | fn ≥ 6 → TRUE | |
| Pin band | [4e-5, 6e-5] | L-38 convention |
| Deepest NEG seen | -0.000566 (2026-08-06 12:00 UTC) | |
| 2nd deepest | -0.000301 (2026-08-06 08:00 UTC) | |
| Chuỗi NEG đáng kể | 2026-08-05 04:00–20:00 UTC, 08-06 08:00+12:00 UTC | |

**Ghi chú funding cũ (trước 05-18):** fapi limit=1000 chỉ lấy được ~82 ngày. Lịch sử trước = MISSING. VPS premium_1h có dữ liệu 07-27→08-07 nhưng schema khác (mark_price, last_funding_rate — không phải settlement interval chuẩn).

### H1c — OI Historical

| Metric | Value | Source |
|---|---|---|
| OI hist days | 30 ngày | fapi openInterestHist period=1d limit=30 |
| Window | 2026-07-09 → 2026-08-07 | |
| OI snapshot (session) | 50,666,136 tokens | fapi/v1/openInterest 2026-08-07 07:15 UTC |
| OI USD ước tính | ~$7.05M (× close 2026-08-07 ~0.139) | |

### H1d — Premium Index / Mark Price

VPS premium_1h store: `scratch/hei_h5b_vps_supplement_20260808.txt`  
Schema: symbol, as_of_ts_ms, mark_price, index_price, last_funding_rate, next_funding_time  
12 parquet files (2026-07-27 → 2026-08-07). Usable để extend funding history nếu cần.

---

## H2 — PERP KLINES — KEY HIGHLIGHTS

File: `scratch/hei_perp_full_20260808.csv` (540 rows).  
Fetch: fapi klines 1d, 2 page: page1=500 nến (→ 2026-06-27) + page2=40 nến (2026-06-28 → 2026-08-06).  
fn: close-to-close daily, boundary = 00:00 UTC → 00:00 UTC.

| Metric | Value | Date |
|---|---|---|
| px_min (daily L) | 0.0221 | ~2025-08–09 period |
| px_max (daily H) | 1.2801 | 2025-02-13 (listing day ATH) |
| Recent high | 0.545 | 2026-08-06 intraday |
| vol_max | $1,244,585,779 | 2026-08-06 |
| Days \|ret\|>10% | 55 | full window |
| Days vol≥8×med14 (L-15) | **28** | full window (L-15 bait-probe candidates) |

### Spike events (vol≥8×med14, nghiêm trọng):

| Date | ret_1d | vol_usd | vol/med14 est. | Note |
|---|---|---|---|---|
| 2025-03-14 | — | — | ≥8× | Early spike |
| 2025-04-08 | — | — | ≥8× | Early spike |
| 2025-07-12/19/22 | — | — | ≥8× | Summer cluster |
| 2026-05-29 | +80.6% | ~$281M | ~244× | Spike cluster 1 |
| 2026-05-30 | ~+10% | ~$475M | ~333× | Spike cluster 1 ext |
| 2026-06-25/26 | — | — | ≥8× | Jun cluster |
| 2026-08-04 | +48.6% | ~$73.8M | ~8× | Pre-spike build |
| **2026-08-05** | **+107.8%** | **~$734M** | **~162×** | **Major event** |
| **2026-08-06** | **-26.7%** | **~$1,244M** | **~274×** | **ATH vol, crash** |

**L-15 bait-probe:** 28 ngày là ứng viên bait — cần operator cross-check từng event trước khi ký nhãn.

---

## H3 — DERIVED + GOM SCREEN

fn: Tất cả derived tính inline trong `_task_build_case_hei_20260808.py`, ghi vào DAILY.  
Spec: gom_detect_spec v1.1 **CHƯA KÝ** — SCREEN-tier offline, không phải signal chính thức.

| Metric | Value |
|---|---|
| GOM-A fires | **1 ngày: 2026-08-01** (conditions: A1 vol≥3×med14, A2 gLSR_slope<0, A3 pos_r>1.5, A4 f_avg≥4e-5, A5 taker≥45%) |
| GOM-B fires | 0 |
| gLSR window (31d) | 0.38–1.04 — crowd consistently net short |
| pos_r peak | 2.7774 (~2026-08-04) |
| pos_r trough | 1.1002 (2026-08-07) |
| Funding pin streak | Bị phá nhiều lần bởi NEG events |
| div_raw (pos_r×gLSR) | Biến động; div_avg3 = rolling 3d |
| glsr_slope_5d | Âm trước/quanh spike events |

**Ghi chú GOM-A 08-01:** Thuộc giai đoạn tích lũy trước spike 08-04/05. Không có GOM-B nào → không có dấu hiệu kho bền vững theo spec v1.1 CHƯA KÝ. Cần operator xem xét.

---

## H4 — SPOT

File: `scratch/hei_spot_full_20260808.csv` (540 rows).  
Source: api/v3 klines 1d, 2 page (cùng cấu trúc perp), taker = k[10]/k[7].  
Boundary: close-to-close daily 00:00 UTC.

### L-29 Guard (spot/perp vol ratio)

| Metric | Value | Result |
|---|---|---|
| spot/perp ratio (min) | 0.064 | CLEAR |
| spot/perp ratio (max) | 0.688 | CLEAR |
| spot/perp ratio (avg) | 0.341 | CLEAR |
| L-29 threshold | > 3× → ABSTAIN | **Toàn bộ 540 ngày: CLEAR** |

Spot vol usable — không có ngày nào vi phạm L-29.

### Depth Snapshot

| Shot | Timestamp | Bid±2% | Ask±2% | Status |
|---|---|---|---|---|
| #1 | 2026-08-07 07:18 UTC | $47,875 | $39,062 | DONE |
| #2 | TBD (≥ 11:18 UTC 08-07) | — | — | **MISSING — L-23 cần ≥2 shots ≥4h apart** |

**CẦN OPERATOR:** Chạy thêm 1 depth snapshot sau 11:18 UTC 2026-08-07 để L-23 compliance.

---

## H5 — ON-CHAIN

| Source | Result |
|---|---|
| Nansen | **LOCKED** (NANSEN_KEY_LOCKED — tầng HUMAN) |
| CoinGecko | Tìm thấy id=heima, symbol=HEI, rank=910 — chain BSC+ETH |
| Contract candidate | 0xf8f173e20e15f3b6cb686fb64724d370689de083 — **UNVERIFIED** |
| BscScan v1 | Deprecated → "switch to Etherscan API V2" |
| BscScan v2 | 404 (token supply endpoint) |
| BscScan top holders | MISSING (deprecated endpoint, no API key) |
| CMC search | 404 |
| Vesting schedule | UNVERIFIED — không tìm thấy deployer/vesting contract |

**On-chain layer: ABSTAIN** — contract unconfirmed, Nansen LOCKED.  
**CẦN OPERATOR:** confirm contract address + Nansen access cho top holders + vesting.

---

## H6 — VPS INVENTORY

VPS: `root@5.223.67.21`, SSH.

| Store | Path | HEI data | Note |
|---|---|---|---|
| premium_1h | /root/.../premium_1h/symbol=HEIUSDT/ | **✓ 12 files (07-27→08-07)** | Schema: mark_price, index_price, last_funding_rate |
| spot_klines_1d | /root/.../spot_klines_1d/ | KHÔNG có | HEI không trong alpha_id_map |
| freshwatch_daily | /root/.../freshwatch_daily/ | KHÔNG có | HEI không trong u50 universe |
| /root/archive/ | archive bundles | KHÔNG có | |
| docs/ | VPS docs | KHÔNG có | |
| data/raw/ (toàn bộ) | recursive find | KHÔNG có | trừ premium_1h |

**Kết luận H6:** Toàn bộ data session này lấy fresh từ Binance fapi/api. VPS premium_1h là bonus reference (không dùng làm nguồn chính).

---

## LAYER COVERAGE

| Layer | Source | Window | Status |
|---|---|---|---|
| Perp klines 1d | fapi klines paginated 2-page | 2025-02-13 → 2026-08-06 | ✓ 540 rows |
| Perp funding | fapi fundingRate limit=1000 | ~2026-05-18 → 2026-08-07 | ✓ 82 ngày |
| Perp OI hist | fapi openInterestHist limit=30 | 2026-07-09 → 2026-08-07 | ✓ 30 ngày |
| LSR (4 types) | fapi topLSR/globalLSR/takerLSR | 2026-07-08 → 2026-08-07 | ✓ 31 rows (L-38) |
| Spot klines 1d | api/v3 klines paginated 2-page | 2025-02-13 → 2026-08-06 | ✓ 540 rows |
| Spot depth | api/v3 depth ±2% | 2026-08-07 07:18 UTC | ⚠ ONE SHOT (cần 2nd ≥4h) |
| Alpha klines | binance alpha endpoint | — | **ABSTAIN** — HEI not in alpha_id_map |
| On-chain (top holders) | Nansen / BscScan | — | **ABSTAIN** — Nansen LOCKED, BscScan deprecated |
| On-chain (vesting) | Contract scanner | — | **ABSTAIN** — contract unconfirmed |
| VPS premium_1h | SSH /root/.../premium_1h | 2026-07-27 → 2026-08-07 | ✓ 12 files (reference) |
| VPS spot_klines_1d | SSH | — | KHÔNG có |
| VPS freshwatch | SSH | — | KHÔNG có (không trong u50) |

---

## MISSING (gom một chỗ)

1. **2nd depth snapshot** ≥ 11:18 UTC 2026-08-07 (L-23: cần ≥2 shots ≥4h apart để estimate depth)
2. **Contract address confirmation** — operator xác nhận 0xf8f173e20e15f3b6cb686fb64724d370689de083 = HEIUSDT underlying (BSC)
3. **Top holders** — cần Nansen (LOCKED) hoặc BscScan API key (paid tier)
4. **Vesting schedule** — cần confirmed contract để tìm deployer + vesting contract
5. **T0 + B_ref OI** — operator xác định (CASE OUTCOME sheet để trống)
6. **Archetype (Loai A/B/C)** — operator phân tích sau khi có đủ context
7. **Funding lịch sử cũ (trước 2026-05-18)** — fapi limit=1000 không đủ; VPS premium_1h chỉ từ 07-27
8. **Lý do spike 05-29/30** — vol 244×/333× med14 trong 2 ngày liên tiếp chưa có context

---

## ĐÃ KIỂM KHÔNG CÓ

- HEI trong `data/config/alpha_id_map.json`: **KHÔNG có** (grep toàn file, 0 match)
- HEI trong VPS `spot_klines_1d`: **KHÔNG có** (SSH ls | grep HEI)
- HEI trong VPS `freshwatch_daily`: **KHÔNG có** (grep -r HEIUSDT → 0 row)
- HEI trong VPS `archive/`: **KHÔNG có** (ls /root/archive | grep HEI → 0)
- HEI trong VPS `docs/`: **KHÔNG có** (grep -r HEI /root/.../docs → 0)
- HEI trong VPS `data/raw/` (toàn bộ): **KHÔNG có** (find recursive → 0, trừ premium_1h)
- L-29 vi phạm: **KHÔNG có** (max ratio 0.688 << 3×)

---

## OUTPUT FILES

| File | Path | Rows/Size |
|---|---|---|
| CASE_HEI.xlsx | docs/case_files/CASE_HEI.xlsx | 7 sheets, 540 DAILY rows (L-32 PASS) |
| hei_perp_full_20260808.csv | scratch/ | 540 rows |
| hei_spot_full_20260808.csv | scratch/ | 540 rows |
| hei_lsr_raw_20260808.csv | scratch/ | 31 rows |
| hei_h0h1_raw_20260808.txt | scratch/ | H0+H1 raw log |
| hei_h2h4_raw_20260808.txt | scratch/ | H2+H3+H4 raw log |
| hei_h5h6_raw_20260808.txt | scratch/ | H5+H6 raw log |
| hei_h5b_vps_supplement_20260808.txt | scratch/ | H5b+H6 supplement |

---

*Tạo: 2026-08-08 | Session agent | DỪNG chờ duyệt.*
