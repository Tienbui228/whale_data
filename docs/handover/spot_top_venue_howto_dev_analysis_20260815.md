# Hướng dẫn chuẩn: Lấy spot-data từ venue vol lớn nhất

**Date:** 2026-08-15  
**Author:** agent (synthesized from codebase exploration)  
**Source codebases:**
- `D:\Data back test\whale_data\` — FreshWatch pipeline (perp side, freshwatch-139)
- `D:\Check onchain fresh wallets\` — venue discovery + spot collector

---

## D1 — Tìm venue có vol lớn nhất (Venue Discovery)

**File tham khảo:** `D:\Check onchain fresh wallets\venue_discovery.py`

### Cơ chế

Query 24h spot ticker từ 6 CEX song song:

| Venue | Endpoint |
|-------|----------|
| Binance | `https://api.binance.com/api/v3/ticker/24hr?symbol={sym}USDT` |
| Bybit | `https://api.bybit.com/v5/market/tickers?category=spot&symbol={sym}USDT` |
| Gate | `https://api.gateio.ws/api/v4/spot/tickers?currency_pair={sym}_USDT` |
| Bitget | `https://api.bitget.com/api/v2/spot/market/tickers?symbol={sym}USDT` |
| MEXC | `https://api.mexc.com/api/v3/ticker/24hr?symbol={sym}USDT` |
| KuCoin | `https://api.kucoin.com/api/v1/market/stats?symbol={sym}-USDT` |

### Logic chọn venue

```python
have = {}  # venue -> vol_usd_24h

# Bybit trap: HTTP 200 nhưng retCode=10001 = pair không tồn tại
# Phải check retCode trước khi đọc vol

# Gate: vol = quoteVolume (đã là USD nếu pair là *_USDT)
# KuCoin: vol = volValue (USD)
# MEXC, Binance: quoteVolume (USDT)
# Bitget: usdtVol hoặc quoteVol

venue_top_measurable = max(have, key=have.get)
vol_top_usd = have[venue_top_measurable]
```

**Lưu ý:** Alpha Binance (bapi endpoint) KHÔNG phải spot CEX thông thường — xem D6.

---

## D2 — Wash Test (kiểm vol giả)

**File tham khảo:** `D:\Check onchain fresh wallets\venue_discovery.py`

### Công thức

```
vol_depth_suspect = vol_top_usd / depth2pct_usd
```

Trong đó:
- `vol_top_usd` = vol 24h của venue có vol lớn nhất
- `depth2pct_usd` = tổng USD depth trong ±2% từ mid-price (order book liquidity)

### Ngưỡng

| Ratio | Đánh giá |
|-------|----------|
| < 5 | Bình thường — vol/depth hợp lý |
| 5–20 | Nghi ngờ — xem xét kỹ |
| > 20 | Suspect wash — đánh dấu, không dùng làm số chốt |

### Cách lấy depth

Mỗi venue có endpoint orderbook riêng:
- Binance: `GET /api/v3/depth?symbol={sym}USDT&limit=20`
- Bybit: `GET /v5/market/orderbook?category=spot&symbol={sym}USDT&limit=50`
- Gate: `GET /api/v4/spot/order_book?currency_pair={sym}_USDT&limit=20`

Sum tất cả bid/ask trong ±2% từ mid:
```python
mid = (best_bid + best_ask) / 2
depth_bids = sum(qty * px for px, qty in bids if px >= mid * 0.98)
depth_asks = sum(qty * px for px, qty in asks if px <= mid * 1.02)
depth2pct_usd = depth_bids + depth_asks
```

---

## D3 — Klines API theo từng venue

**File tham khảo:** `D:\Check onchain fresh wallets\spot_collector.py`

### Binance (spot)

```
GET https://api.binance.com/api/v3/klines
  ?symbol={sym}USDT
  &interval=1d
  &limit=100
```

Response: array of `[open_time_ms, open, high, low, close, volume, close_time_ms, quote_vol, n_trades, taker_buy_base, taker_buy_quote, ignore]`

- Timestamp: milliseconds UTC, open-of-candle
- Date: `datetime.utcfromtimestamp(open_time_ms/1000).date()`
- Taker buy vol: `taker_buy_quote` (USD)
- Taker ratio: `taker_buy_quote / quote_vol`

### Bybit

```
GET https://api.bybit.com/v5/market/kline
  ?category=spot
  &symbol={sym}USDT
  &interval=D
  &limit=100
```

Response: `result.list` — array của `[startTime_ms, open, high, low, close, volume_base, volume_quote]`

- Timestamp: milliseconds
- **Không có taker field** — taker = ABSTAIN cho Bybit spot

### Gate

```
GET https://api.gateio.ws/api/v4/spot/candlesticks
  ?currency_pair={sym}_USDT
  &interval=1d
  &limit=100
```

Response: array của `[timestamp_SECONDS, quote_vol, close, high, low, open, base_vol, closed_flag, window_label]`

- **QUAN TRỌNG:** timestamp là GIÂY, không phải ms → `datetime.utcfromtimestamp(int(ts))`
- `quote_vol` = vol tính theo USDT (col 1, index 1)
- Không có taker — ABSTAIN

### Bitget

```
GET https://api.bitget.com/api/v2/spot/market/candles
  ?symbol={sym}USDT
  &granularity=1day
  &limit=100
```

Response: array của `[timestamp_ms, open, high, low, close, base_vol, usdt_vol]`

- **QUAN TRỌNG:** candle mở lúc 08:00 UTC+8 = 00:00 UTC → timestamp raw là UTC+8 → cần `+ timedelta(days=1)` nếu parse theo UTC local date convention của pipeline.
- Verify: so `date_from_ts` với ngày thực tế theo Bitget UI trước khi dùng.

### MEXC

```
GET https://api.mexc.com/api/v3/klines
  ?symbol={sym}USDT
  &interval=1d
  &limit=100
```

Response: cùng format Binance (12 field).  
Taker fields (idx 9, 10) có nhưng độ tin cậy thấp hơn Binance — ghi rõ nguồn khi dùng.

### KuCoin

```
GET https://api.kucoin.com/api/v1/market/candles
  ?type=1day
  &symbol={sym}-USDT
```

Response: `data` — array của `[timestamp_SECONDS, open, close, high, low, vol_base, vol_quote]`

- Timestamp: **GIÂY**, không phải ms
- Chú ý format symbol: `{sym}-USDT` (có dấu gạch, khác Binance)
- Không có taker

---

## D4 — Ghi vào DAILY schema

**Quy ước (L-25, một cột một nguồn):**

| Col | Tên | Ghi chú |
|-----|-----|---------|
| 31 | `vol_spot_usd` | Vol 24h USD từ venue thắng (venue_top_measurable) |
| 32 | `taker_spot_pct` | % taker buy (chỉ Binance/MEXC có; các venue khác = NaN/ABSTAIN) |
| 33 | `spot_perp_ratio` | vol_spot_usd / oi_usd (spot vol chia OI perp) |

### Cách điền

1. Chạy venue discovery → ghi `venue_top_measurable` vào `data_source` row
2. Fetch klines từ venue đó → parse `close`, `quote_vol`
3. `vol_spot_usd` = `quote_vol` của ngày D
4. `taker_spot_pct`:
   - Binance: `taker_buy_quote / quote_vol`
   - Bybit/Gate/KuCoin/Bitget: ghi `NaN` — ABSTAIN, không điền 0
5. `spot_perp_ratio` = `vol_spot_usd / oi_usd` (oi_usd từ freshwatch_daily col oi_usd)

### Ghi data_source

Trong header row hoặc metadata của CASE sheet, ghi:
```
vol_spot_usd source: {venue_top_measurable} spot klines 1d UTC
date: {run_date}
wash_suspect_flag: {True/False} (ratio={vol_depth_suspect:.1f})
```

---

## D4-ext — SPOT-EXT amendment (v2.1, ký 2026-08-19, án V1-20260819)

**Nguồn:** L-52 draft `proposals/lessons_pending_batch_20260818.md` §D.1 · exhibit TRIA 19/08 (Bybit turnover Aug18 $2.3M = 3× Alpha).

**Vấn đề:** Cột 31 `vol_spot_usd` canonical = Binance api/v3 (một-thứ-hai-tên L-51/GUA). Khi token KHÔNG có Binance spot pair NHƯNG CÓ spot venue lớn khác (Bybit/OKX/Gate/...), không có nơi ghi vol chân spot đó → mù dữ liệu, doctrine #10 (kho ÷ băng-thông) sai hệ số.

**Amendment — 2 cột canonical mới (v2.1):**

| Col | Tên | Ghi chú |
|-----|-----|---------|
| 51 | `vol_spot_ext_usd` | Vol 24h USD từ **spot venue-ext** (venue spot khác Binance). Trong 1 case chỉ được có 1 venue-ext ưu tiên; nếu >1 venue-ext lớn tương đương, chọn theo thứ tự Bybit > OKX > Gate > KuCoin > MEXC > Bitget (khớp `spot_top_venue_howto` §S-1). |
| 52 | `spot_ext_venue` | Tên venue-ext (chuỗi: `bybit` / `okx` / `gate` / `kucoin` / `mexc` / `bitget`). Phải khai kể cả những ngày `vol_spot_ext_usd` null (nếu venue đã confirm existence — ngày null = missing data trong window). |

**Quy tắc L-51 tuyệt đối:**
- **CẤM** ghi số Bybit/OKX/... vào `vol_spot_usd` (col 31). Cột đó CANONICAL = Binance api/v3 spot klines quote_vol duy nhất.
- Alpha vol → col 35 `vol_alpha` (không phải col 31).
- Bybit/OKX/Gate/... vol → col 51 `vol_spot_ext_usd`.
- Nếu token có CẢ Binance spot + Bybit spot: col 31 = Binance canonical, col 51 = Bybit ext. Cả hai điền song song, KHÔNG cộng dồn.

**Taker Bybit/OKX/Gate:**
- Bybit v5 klines không có taker breakdown (7 fields: [startTime, open, high, low, close, volume, turnover]).
- Bybit v5 `market/recent-trade` có `side` field ('Buy'/'Sell') nhưng per-tick → cần aggregate daily riêng (endpoint đắt, cần collector riêng nếu cần).
- OKX v5 klines không có taker breakdown.
- Gate v4 klines không có taker breakdown.
- **Quy ước tạm:** cột taker cho spot-ext = ABSTAIN-STRUCTURAL (L-51/L-52 amendment) đến khi có collector taker-per-side riêng.

**Identity-check anti-mirror (bắt buộc trước dùng field từ venue mới):**

Trước khi ghi số từ venue mới lần đầu tiên: bit-level compare ≥3 mẫu giữa `base_vol` và `turnover_usd` (hoặc `quote_vol` tương đương). Nếu bit-equal ở ≥1 mẫu → nghi mirror (bug kiểu Alpha k[9]≡k[5], k[10]≡k[7]) → ABSTAIN, ghi vào án E clone.

TRIA-Bybit sample 3 ngày (Jul20/21/22): bit-equal=**False** cả 3 · implied_avg (turnover/base_vol) ≈ close ± spread → PASS identity check.

**LAYER COVERAGE header bắt buộc từ 19/08:**

Mỗi report case phải khai:
```
spot-ext: <venue1[,venue2]> / N/A / CHƯA-TRA
```

Quy ước:
- `bybit`, `okx`, `gate`, ... = tên venue tìm thấy có pair
- `N/A` = ĐÃ TRA cả ≥3 venue lớn (Bybit + OKX + Gate) và xác nhận không có pair
- `CHƯA-TRA` = **chưa** tra venue nào → PHẢI đổi thành N/A hoặc venue trước khi commit report

**CHƯA-TRA ≠ N/A.** Ghi N/A khi chưa tra là bug mù.

**Case-open probe từ 19/08 checklist:**
- [ ] Binance api/v3 exchangeInfo (base=SYM exact)
- [ ] Bybit v5 instruments-info (category=spot, symbol={SYM}USDT)
- [ ] OKX v5 public/instruments (instType=SPOT, instId={SYM}-USDT)
- [ ] Gate v4 spot/currency_pairs/{SYM}_USDT
- Nếu ≥1 venue có pair → tra klines full window, ghi vol_spot_ext_usd + spot_ext_venue
- Nếu tất cả ∅ → spot-ext = N/A (chân perp+alpha only)

**Áp dụng ngay 4 case đang mở (recon 19/08, chỉ instruments-info):**

| Token | Bybit | OKX | Gate | Kết quả |
|-------|-------|-----|------|---------|
| BTW | ∅ | ∅ | ∅ | spot-ext = N/A (perp-only chain) |
| GUA | ∅ | ∅ | **TRADABLE GUA_USDT** | spot-ext = gate (án 17-18/08 bỏ sót — báo cáo lại) |
| APR | ∅ | ∅ | ∅ | spot-ext = N/A |
| CLO | ∅ | ∅ | ∅ | spot-ext = N/A (Alpha-only + perp confirmed) |
| TRIA | **Trading TRIAUSDT** | ∅ | ∅ | spot-ext = bybit (backfilled Jul20-Aug18) |

Kéo klines chi tiết cho từng case sẽ theo lệnh riêng (task này chỉ reconnaissance).

---

## D5 — DEX handling

**Tình trạng hiện tại (2026-08-15):**

### GeckoTerminal

- Endpoint: `https://api.geckoterminal.com/api/v2/networks/bsc/tokens/{contract}/pools`
- Vấn đề: **HTTP 403 thường xuyên** — rate limit hoặc bot detection
- Không đáng tin cậy trong automation script
- Nếu dùng: implement retry với jitter + user-agent header

### DexScreener (alternative)

```
GET https://api.dexscreener.com/latest/dex/tokens/{contract_address}
```

- Batch tối đa **30 địa chỉ** mỗi request (comma-separated)
- Response: `pairs[]` với `volume.h24`, `priceUsd`, `liquidity.usd`
- Miễn phí, không cần API key
- Pick pair có liquidity cao nhất làm canonical

### Tìm contract BSC

```
GET https://api.coingecko.com/api/v3/coins/list?include_platform=true
```

Filter `platforms.binance-smart-chain` để lấy BSC contract address.  
Map từ ticker → contract address, lưu vào `data/config/bsc_contract_map.json`.

### Lưu ý quan trọng

- DEX vol có double-count (cùng trade qua nhiều pool) → không so sánh trực tiếp với CEX vol
- Nếu token chỉ có DEX (không niêm yết CEX): ghi `venue_top_measurable = "dex_bsc"`, `wash_suspect_flag = True` (vì không có depth chuẩn để wash-test)
- **Alpha token BSC:** Nếu token có `alpha_id` trong `data/config/alpha_id_map.json` → ưu tiên Alpha klines endpoint trước DEX (xem D6)

---

## D6 — Giới hạn và điều không làm được

### Alpha Binance — taker ABSTAIN

**Đây là giới hạn đã chốt (04/08/2026):**

Alpha klines từ `https://www.binance.com/bapi/defi/v1/public/alpha-trade/klines` trả về field tương tự Binance spot nhưng:

```
klines[9] == klines[5]  (taker_buy_base == base_vol)  # LUÔN LUÔN
```

→ `taker_spot_pct` cho Alpha = ABSTAIN, điền `NaN`, KHÔNG điền 1.0 hay 0.5.

**Collector chính:** `scripts/collect_alpha_daily.py` (cron 02:00 UTC)  
Store: `data/raw/spot_klines_1d` venue=`binance_alpha`

### CEX nhỏ (Bitget/MEXC/KuCoin/Gate)

- Taker buy thường không expose trong klines
- Nếu cần: phải query trade-level API (resource intensive, rate-limit tight)
- Cho mục đích DAILY: taker = ABSTAIN cho tất cả non-Binance venue

### Venue switching

Khi venue_top thay đổi theo ngày (hôm nay Bybit, ngày mai Gate):
- **Không** tự động switch trong time-series một cột
- Nếu phải switch: ghi chú `venue_change: {old}→{new} on {date}` trong metadata
- Hoặc: luôn dùng Binance làm anchor nếu có, chỉ dùng venue khác khi Binance không list

### Không dựng collector song song ad-hoc

**Quy tắc CLAUDE.md:** PROBE STORE TRƯỚC — kiểm tra VPS store trước, chỉ fetch ngoài khi:
- (b) cần lịch sử trước ngày store bắt đầu (one-off backfill, có nhãn)
- (c) data type không có trong store

Spot klines nằm ngoài VPS freshwatch store hiện tại → đủ điều kiện (c) để fetch CEX trực tiếp.  
Nhưng sau khi fetch: phải lưu vào store có tên rõ ràng (không để chỉ trong scratch/).

---

## Quy trình tổng hợp (checklist)

```
[ ] 1. Chạy venue discovery → chọn venue_top_measurable
[ ] 2. Wash test: tính vol_depth_suspect → flag nếu >20
[ ] 3. Fetch klines từ venue_top (xem D3, chú ý timestamp/timezone)
[ ] 4. Parse: date, close, quote_vol, taker (nếu có)
[ ] 5. Ghi vol_spot_usd (col 31), taker_spot_pct (col 32, NaN nếu ABSTAIN)
[ ] 6. Tính spot_perp_ratio (col 33)
[ ] 7. Ghi metadata: venue, run_date, wash_flag
[ ] 8. DEX fallback chỉ khi không có CEX listing
```

---

## Files tham khảo

| File | Mô tả |
|------|-------|
| `D:\Check onchain fresh wallets\venue_discovery.py` | Query 6 CEX, tính wash ratio |
| `D:\Check onchain fresh wallets\spot_collector.py` | Klines + depth fetcher đa venue |
| `D:\Data back test\whale_data\scripts\collect_alpha_daily.py` | Alpha collector (cron) |
| `D:\Data back test\whale_data\data\config\alpha_id_map.json` | 137 Alpha token ID map |
| `D:\Data back test\whale_data\data\config\freshwatch_symbols.txt` | 139 FreshWatch universe |
