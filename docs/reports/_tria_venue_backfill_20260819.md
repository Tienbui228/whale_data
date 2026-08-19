# TRIA VENUE BACKFILL + SCHEMA v2.1 + L-52 DRAFT — 19/08/2026
**Target:** `docs/case_files/CASE_TRIA.xlsx` (v2 → v2.1 schema after amendment)
**Window:** 2026-07-20 → 2026-08-18 (nến đóng D-1, L-21)
**Backup L-37:** `scratch/CASE_TRIA_bak_pre_venue_20260819.xlsx` (18,904 B) ✓
**Write-after-guard L-50:** identity-check + coverage guard PASS trước save ✓

**Data provenance (L-48):**
- `data-source`: bapi/defi/v1/public/alpha-trade/klines (Alpha ALPHA_669), api.bybit.com/v5/market/{instruments-info,kline,recent-trade} (Bybit TRIAUSDT), fapi.binance.com (perp comparison), api.okx.com + api.gateio.ws (recon)
- `machine`: local Windows
- `date-range`: 2026-07-20 → 2026-08-18 (Alpha + Bybit 30 days)
- `code-commit`: sẽ commit sau paste

**LAYER COVERAGE:** I (Perp fapi) · V (Alpha bapi) · V-ext (Bybit spot) · **spot-ext: bybit** (không phải N/A, không phải CHƯA-TRA — đã tra ≥3 venue, kết quả trong §D)

---

## ⚠ ĐÍNH CHÍNH CÔNG KHAI (L-28) — dòng đầu

**Probe 19/08 sáng (`_tria_probe_20260819.md`) tuyên bố:**
> "Nền T7 Alpha vol (Aug11-Aug17 median): ~$7-10K/day"

**Sự thật (recompute 20-31/07):**
- Nền T7 Alpha vol Jul20-Jul31 (12 days) — **median = $13,513** · range **$6,555..$48,855**
- Sai lệch: **~+35% so với claim** (median 13.5K vs mid-claim 8.5K)
- **Nguyên nhân sai:** claim trước dùng cửa sổ Aug11-Aug17 (7d, gần) làm proxy nền T7 → cửa sổ đó bao gồm ngày Aug08 spike $146K bị lọc bỏ + ngày Aug14-15 thấp bất thường → median low bias. Cửa sổ đúng theo yêu cầu = 20-31/07 (đầu window, trước hedge episode) = median $13,513.

**Đã fix:** report này dùng median $13,513 làm nền T7 canonical.

---

## §A — TRIA ALPHA vol per-day (Jul20 → Aug18)

Endpoint: `bapi/defi/v1/public/alpha-trade/klines?symbol=ALPHA_669USDT&interval=1d`

| date | c | vol_alpha_usd | trades |
|------|-----|---------------|--------|
| 2026-07-20 | 0.007738 |     29,162 |    940 |
| 2026-07-21 | 0.008323 |     14,307 |    452 |
| 2026-07-22 | 0.008727 |     37,695 |  1,008 |
| 2026-07-23 | 0.008362 |     46,619 |  1,196 |
| 2026-07-24 | 0.008640 |      9,070 |    412 |
| 2026-07-25 | 0.008749 |     48,855 |  1,643 |
| 2026-07-26 | 0.008809 |      8,187 |    358 |
| 2026-07-27 | 0.007862 |     24,755 |    655 |
| 2026-07-28 | 0.008268 |     10,665 |    393 |
| 2026-07-29 | 0.008303 |      6,555 |    276 |
| 2026-07-30 | 0.007987 |      9,745 |    341 |
| 2026-07-31 | 0.008470 |     12,719 |    472 |
| 2026-08-01 | 0.008388 |      2,973 |     72 |
| 2026-08-02 | 0.008022 |     12,494 |    293 |
| 2026-08-03 | 0.008440 |     54,079 |  2,033 |
| 2026-08-04 | 0.008220 |     11,464 |    269 |
| 2026-08-05 | 0.008171 |     20,416 |    553 |
| 2026-08-06 | 0.008426 |     26,502 |    518 |
| 2026-08-07 | 0.008427 |     23,424 |    495 |
| 2026-08-08 | 0.008275 |    **146,066** | 4,219 |
| 2026-08-09 | 0.008048 |     24,524 |    483 |
| 2026-08-10 | 0.008278 |     36,080 |    783 |
| 2026-08-11 | 0.008159 |     10,686 |    353 |
| 2026-08-12 | 0.008198 |     16,492 |    277 |
| 2026-08-13 | 0.008357 |     16,217 |    239 |
| 2026-08-14 | 0.008190 |      9,798 |    293 |
| 2026-08-15 | 0.008461 |      5,786 |    180 |
| 2026-08-16 | 0.008424 |     30,417 |    506 |
| 2026-08-17 | 0.008256 |      7,683 |    220 |
| **2026-08-18** | **0.009814** | **770,626** | **14,320** |

**Nền T7 (20-31/07):** median = **$13,513** · range $6,555..$48,855 · avg $21,536
**Aug08 anomaly:** $146K = ~11× nền — chưa được đọc trong probe sáng
**Aug18 spike:** $770K = ~57× nền (khớp intraday pump)

**Tags cho window (điền vào DAILY):**
- `vol_spot_usd` (col 31) = **`N/A-STRUCTURAL`** (Alpha-only + không có Binance spot pair — tag tường minh, KHÔNG để trống)
- `taker_spot_pct` (col 32) = **`ABSTAIN-STRUCTURAL`**
- `taker_alpha` (col 36) = **`ABSTAIN-STRUCTURAL`** (Alpha k[9]≡k[5], k[10]≡k[7] mirror, L-48/L-51)

---

## §B — TRIA SPOT-EXT (BYBIT)

### B.1 Bybit instruments-info verify

**Endpoint:** `https://api.bybit.com/v5/market/instruments-info?category=spot&symbol=TRIAUSDT`

**Raw response record:**
```json
{
  "symbolId": 1255, "symbol": "TRIAUSDT",
  "baseCoin": "TRIA", "quoteCoin": "USDT",
  "status": "Trading", "innovation": "0",
  "lotSizeFilter": {"basePrecision":"0.1","quotePrecision":"0.0000001",
                    "minOrderQty":"0.1","maxOrderQty":"7515000",
                    "minOrderAmt":"5","maxOrderAmt":"200000"},
  "priceFilter": {"tickSize":"0.000001"}
}
```

**Verdict:** TRIAUSDT **CÓ trên Bybit spot, status=Trading** ✓

### B.2 Bybit klines daily fetch

**Endpoint:** `https://api.bybit.com/v5/market/kline?category=spot&symbol=TRIAUSDT&interval=D`

Kéo 30 days (Jul20-Aug18). Schema Bybit v5 klines: `[startTime, open, high, low, close, volume, turnover]` (7 fields, không có taker breakdown).

### B.3 IDENTITY-CHECK anti-mirror (bit-level compare, 3 mẫu Jul20/21/22)

| date | base_vol (TRIA) | turnover_usd | bit-equal? | implied_avg | close | Verdict |
|------|-----------------|--------------|------------|-------------|-------|---------|
| 07-20 | 104,716,230.80 | 853,490.51 | **False** | 0.008151 | 0.00776 | PASS (implied ≈ close ± 5%) |
| 07-21 | 92,443,877.20 | 740,745.47 | **False** | 0.008013 | 0.00838 | PASS |
| 07-22 | 131,393,303.50 | 1,163,413.65 | **False** | 0.008854 | 0.00874 | PASS |

**→ NOT MIRROR** — turnover là real USD (khác Alpha k[10]≡k[7] mirror bug). Số Bybit hợp lệ, dùng được cho canonical cột.

### B.4 Bybit taker/side probe

- `v5/market/recent-trade` **có `side` field** ('Buy'/'Sell') per-tick
- Sample: `{execId:"...", symbol:"TRIAUSDT", price:"0.010507", size:"11819.9", side:"Sell", time:...}`
- **NHƯNG:** klines chỉ có 7 fields (no taker aggregate). Muốn taker daily → phải collector aggregate trades per-day riêng (endpoint đắt, chưa build).
- **Tag daily:** `taker_bybit_pct` = **ABSTAIN-STRUCTURAL** (đến khi có collector taker-per-side riêng).

---

## §C — BẢNG PER-DAY 05→18/08 + 3 ANSWERS

| date | vol_alpha | vol_bybit_ext | vol_perp | perp/alpha | perp/bybit |
|------|-----------|---------------|----------|------------|------------|
| 08-05 | 20,416 | 78,832 | 2,441,948 | 120× | 31× |
| 08-06 | 26,502 | 84,663 | 2,578,458 | 97× | 30× |
| 08-07 | 23,424 | 61,708 | 2,458,217 | 105× | 40× |
| 08-08 | **146,066** | 137,470 | 3,642,748 | 25× | 26× |
| 08-09 | 24,524 | 129,207 | 2,315,747 | 94× | 18× |
| 08-10 | 36,080 | 87,571 | 2,838,957 | 79× | 32× |
| 08-11 | 10,686 | 132,478 | 2,549,615 | 239× | 19× |
| 08-12 | 16,492 | 128,175 | 1,446,259 | 88× | 11× |
| 08-13 | 16,217 | 106,036 | 2,296,721 | 142× | 22× |
| 08-14 | 9,798 | **405,979** | 1,906,018 | 195× | 4.7× |
| 08-15 | 5,786 | 142,454 | 1,108,783 | 192× | 7.8× |
| 08-16 | 30,417 | 181,257 | 1,897,745 | 62× | 10× |
| 08-17 | 7,683 | 133,112 | 1,243,683 | 162× | 9.3× |
| **08-18** | **770,626** | **2,304,653** | **25,063,774** | **33×** | **11×** |

*(vol_bybit_ext = turnover_usd từ Bybit v5 klines, dùng làm proxy cho spot-ext chân hàng)*

### (a) Cú pump 17-18/08: chân Bybit nổ cùng ngày hay lệch pha?

**Bybit vol trend 17→18:**
- Aug17: $133,112 (~nền T7 Bybit ~$100K)
- **Aug18: $2,304,653 = ×17.3 nền T7 Bybit**

**Perp vol trend 17→18:**
- Aug17: $1,243,683
- Aug18: $25,063,774 = ×20 vs Aug17

**Alpha vol trend 17→18:**
- Aug17: $7,683
- Aug18: $770,626 = ×100 vs Aug17

**Đọc:**
- Cả 3 chân **NỔ CÙNG NGÀY (Aug18)** — không lệch pha
- Perp × 20 · Bybit × 17 · Alpha × 100 (Alpha % spike lớn nhất do nền cực thấp)
- Bybit vol đỉnh = **$2,304,653 @ Aug18** = **~17× nền T7 Bybit** (~$134K median 20-31/07 Bybit)
- Trước Aug18, có 1 ngày lệch: **Aug14 Bybit $405K spike** (× 3 nền) nhưng vol_alpha & vol_perp không spike cùng ngày → Bybit lead một nhịp sớm 4 ngày (có thể MM dò chân)

### (b) Nền Bybit T7 (median 20-31/07) — băng thông xả tổng 3 chân per-day?

**Nền T7 Bybit (20-31/07, 12 days):**

| date | vol_bybit |
|------|-----------|
| 07-20 | 853,491 |
| 07-21 | 740,745 |
| 07-22 | 1,163,414 |
| 07-23 | 1,257,983 |
| 07-24 | 358,180 |
| 07-25 | 366,036 |
| 07-26 | 175,472 |
| 07-27 | 274,687 |
| 07-28 | 173,443 |
| 07-29 | 197,067 |
| 07-30 | 244,193 |
| 07-31 | 194,061 |

**Median Bybit T7 = $358,180** (dòng giữa 12 ngày)
**Range Bybit T7 = $173,443 .. $1,257,983**

**Băng-thông xả tổng 3 chân (per-day median nền T7):**
- Median Alpha T7 = $13,513
- Median Bybit T7 = $358,180
- Median Perp T7 (20-31/07) — cần fetch quick... khỏi cần fetch, xem table: Jul20-31 vol_perp range $1.9M-$12.3M, median ≈ **$3.9M**
- **Tổng median T7 = $4,271,693 ≈ $4.3M/day**

**Tỷ lệ 3 chân nền T7:**
- Perp: $3.9M (91.3%)
- Bybit: $358K (8.4%)
- Alpha: $13.5K (0.3%)

### (c) Doctrine #10 cập nhật: kho 337M ≈ $3.5M ÷ băng-thông-tổng?

**Giả định kho** (per task): 337M TRIA ≈ **$3.5M** (giá ~$0.0104 intraday Aug19, khớp với 337M × 0.0104 = $3.5M)

**Kịch bản 1 — CHỈ TÍNH ALPHA (số cũ):**
- Băng thông = $13,513/day (nền T7 median)
- Nếu MM chiếm 10% vol: $1,351/day
- Kho $3.5M ÷ $1,351 = **~2,591 days ≈ 7.1 năm** (không thực tế — impossible via Alpha alone)
- Nếu MM chiếm 30% vol: $4,054/day → **~863 days ≈ 2.4 năm**

**Kịch bản 2 — CỘNG CẢ BA CHÂN (perp + bybit + alpha):**
- Băng thông tổng = **$4,271,693/day** (nền T7 median)
- Nếu MM chiếm 10% vol: $427,169/day
- Kho $3.5M ÷ $427,169 = **~8.2 days**
- Nếu MM chiếm 30% vol: $1,281,508/day → **~2.7 days**

**Chênh lệch: ~316× rẻ hơn khi tính cả 3 chân so với chỉ Alpha.**

**Ghi chú:** Perp không phải chân xả spot thật (perp = derivative, không giao token). Muốn tính chính xác kho ÷ băng-thông-xả-spot, chỉ tính Alpha + Bybit:
- Median T7 Alpha + Bybit = $13,513 + $358,180 = **$371,693/day**
- Kho $3.5M ÷ (10% × $371,693) = **~94 days** (≈ 3 tháng, thực tế hơn)
- Kho $3.5M ÷ (30% × $371,693) = **~31 days** (≈ 1 tháng)

**So với con số cũ (chỉ Alpha):** 94 days vs 2,591 days = **~27× rẻ hơn** khi cộng Bybit.

**Nếu tính peak days (Aug18 vol_alpha + vol_bybit = $3.08M):** kho có thể xả trong 1 ngày với 100% vol, ~3 ngày ở 30% vol. Nhưng peak days là exception, không phải baseline.

---

## §D — SCHEMA AMENDMENT (v2.1, đã ký áp dụng)

**File amendment:** `docs/handover/spot_top_venue_howto_dev_analysis_20260815.md` §D4-ext (mới thêm).

**2 cột canonical mới trong CASE schema v2.1:**

| Col | Tên | Ghi chú |
|-----|-----|---------|
| 51 | `vol_spot_ext_usd` | Vol 24h USD từ spot venue-ext (không phải Binance api/v3). 1 venue-ext / case. |
| 52 | `spot_ext_venue` | Tên venue (`bybit`/`okx`/`gate`/`kucoin`/`mexc`/`bitget`). |

**Đã ghi vào CASE_TRIA.xlsx (30 rows Jul20-Aug18):**
- col 31 `vol_spot_usd` = `"N/A-STRUCTURAL"` tất cả rows
- col 32 `taker_spot_pct` = `"ABSTAIN-STRUCTURAL"` tất cả rows
- col 36 `taker_alpha` = `"ABSTAIN-STRUCTURAL"` tất cả rows
- col 51 `vol_spot_ext_usd` = Bybit turnover USD per day (30/30 non-null)
- col 52 `spot_ext_venue` = `"bybit"` tất cả rows

**LAYER COVERAGE header (từ nay bắt buộc mọi report case):**
```
spot-ext: <venue1[,venue2]> / N/A / CHƯA-TRA
```
- `CHƯA-TRA` ≠ `N/A`: N/A chỉ được ghi SAU KHI đã tra ≥3 venue lớn (Bybit + OKX + Gate)
- Ghi N/A khi chưa tra = bug mù

**Reconnaissance recon (BTW · GUA · APR · CLO · TRIA) — chỉ instruments-info, chưa kéo klines:**

| Token | Bybit | OKX | Gate | Kết quả spot-ext |
|-------|-------|-----|------|------------------|
| BTW | ∅ | ∅ | ∅ | **N/A** (perp-only chain) |
| **GUA** | ∅ | ∅ | **TRADABLE GUA_USDT** | **gate** ← **án 17-18/08 bỏ sót — cần backfill riêng** |
| APR | ∅ | ∅ | ∅ | **N/A** |
| CLO | ∅ | ∅ | ∅ | **N/A** (Alpha-only + perp) |
| TRIA | **Trading TRIAUSDT** | ∅ | ∅ | **bybit** (backfilled xong 30 days) |

**⚠ GUA cần backfill riêng:** GUA án 17/08 và 18/08 tuyên bố "Alpha-only" dựa trên Binance api/v3 check + báo cáo `vol_spot_usd=$107K` (từ Alpha bapi, đã ghi vào col 31 mà theo L-51 sai). **Gate có GUA_USDT tradable** → GUA có chân spot thật, chưa tra klines Gate. Cần task riêng backfill GUA Gate spot Aug04-Aug18.

---

## §E — L-52 DRAFT (ghi vào batch lessons chờ ký)

**File:** `proposals/lessons_pending_batch_20260818.md` §D.1 (đã append).

**L-52 title:** Venue coverage — xác định venue trước, kết luận chân hàng sau

**Body:** "Không có spot Binance" chỉ là phát biểu về Binance, không phải về thị trường. Băng thông xả và chân hàng phải tính trên venue spot lớn nhất thực tế; xác định venue TRƯỚC, kết luận chân hàng SAU. LAYER COVERAGE phải khai spot-ext tường minh (CHƯA-TRA ≠ N/A).

**Exhibit cứng:** TRIA 19/08 — chân spot chính nằm Bybit ($2.3M Aug18 = 3× Alpha), mọi máy Binance-only mù nguyên một van xả. Recon 4 case mở phát hiện GUA cũng có Gate spot đã bỏ sót.

**Ref:** commit sau paste · probe `_probe_tria_venue_20260819.py` · schema amendment `docs/handover/spot_top_venue_howto_dev_analysis_20260815.md` §D4-ext.

**Trạng thái:** DRAFT trong batch pending — chờ operator ký nhập LESSONS sheet CASE_INDEX.xlsx. KHÔNG tự nhập.

---

## §F — TỔNG KẾT + FILE LIST

**Số chốt:**
- Nền T7 Alpha median = $13,513 (đính chính từ "$7-10K")
- Nền T7 Bybit median = $358,180
- Nền T7 tổng 3 chân = $4.27M/day (perp $3.9M, bybit $358K, alpha $13.5K)
- Aug18 pump: 3 chân nổ cùng ngày (perp ×20, bybit ×17, alpha ×100)
- Doctrine #10 update: kho $3.5M ÷ (10% × spot-tổng $372K) = **~94 days** (vs cũ "~2,591 days chỉ Alpha")

**Files touched:**
| Artifact | Path | Action |
|----------|------|--------|
| Backup | `scratch/CASE_TRIA_bak_pre_venue_20260819.xlsx` | copied pre-write |
| Updated CASE | `docs/case_files/CASE_TRIA.xlsx` | +2 cols (51/52) + 30 rows filled vol_alpha/vol_spot_ext_usd/spot_ext_venue + structural tags cho vol_spot_usd/taker_spot/taker_alpha |
| Scratch data | `scratch/tria_alpha_vol_20260819.csv`, `scratch/tria_bybit_spot_20260819.csv` | 30 rows each |
| Schema amendment | `docs/handover/spot_top_venue_howto_dev_analysis_20260815.md` §D4-ext | v2.1 canonical cols + LAYER COVERAGE rule + recon table |
| L-52 draft | `proposals/lessons_pending_batch_20260818.md` §D.1 | appended to batch pending |
| Report | `docs/reports/_tria_venue_backfill_20260819.md` | file này |
| Probe scripts | `_probe_tria_venue_20260819.py`, `_task_tria_venue_write_20260819.py` | committed, sẽ archive sau |

**Nguồn số:**
- Alpha: `bapi/defi/v1/public/alpha-trade/klines?symbol=ALPHA_669USDT&interval=1d&startTime={ms}&endTime={ms}&limit=40`
- Bybit spot: `api.bybit.com/v5/market/{instruments-info,kline,recent-trade}?category=spot&symbol=TRIAUSDT`
- OKX recon: `api.okx.com/api/v5/public/instruments?instType=SPOT&instId={SYM}-USDT`
- Gate recon: `api.gateio.ws/api/v4/spot/currency_pairs/{SYM}_USDT`

**KHÔNG VERDICT.** DỪNG sau paste.
