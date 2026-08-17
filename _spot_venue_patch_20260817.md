# SPOT-TOP-VENUE PATCH — AIN / GUA / APR
**Date:** 2026-08-17  
**Tokens:** AINUSDT, GUAUSDT, APRUSDT  
**Howto:** docs/handover/spot_top_venue_howto_dev_analysis_20260815.md  
**Probes:** _probe_spot_venue_20260817.py, _probe_spot_klines_20260817.py, _probe_spot_write_20260817.py

---

## S-0 — Store Probe

Store: `data/raw/spot_klines_1d/` — 481 date partitions, 2025-04-10 → 2026-08-03  
Schema cols: `symbol, date_str, open, high, low, close, base_vol, quote_vol, venue, taker_abstain, ...`

| Token | Alpha ID | Store rows | Last store date |
|-------|----------|-----------|----------------|
| AIN | ALPHA_260 | 395 | 2026-08-03 |
| GUA | ALPHA_483 | 250 | 2026-08-03 |
| APR | NOT IN MAP | — | — |

→ AIN/GUA in store through Aug03. Fetched Aug04-Aug16 from Alpha bapi (`{alpha_id}USDT`).  
→ APR not in Alpha store — fetched KuCoin full range.

---

## S-1 — Venue Discovery (24h ticker, 2026-08-17)

| Venue | AIN vol (USD) | GUA vol (USD) | APR vol (USD) |
|-------|-------------|-------------|-------------|
| Binance spot | ABSENT | ABSENT | ABSENT |
| Bybit spot | ABSENT (retCode=10001) | ABSENT | ABSENT |
| Gate | 76,633 | 25,721 | ABSENT |
| Bitget | ABSENT | ABSENT | ABSENT |
| MEXC | **88,553** | **345,744** | 682,453 |
| KuCoin | 20,753 | ABSENT | **1,509,837** |
| Alpha (store) | ~32,317/day avg | ~875k/day Aug05-11 | — |

**CEX top venue:** AIN→MEXC, GUA→MEXC, APR→KuCoin

---

## S-2 — Wash Test

| Token | Top CEX venue | Vol 24h | Depth ±2% | Ratio | Verdict |
|-------|-------------|---------|----------|-------|---------|
| AIN | MEXC | 88,553 | 2,829 | **31.3x** | WASH |
| GUA | MEXC | 345,744 | 1,764 | **196.0x** | WASH |
| APR | KuCoin | 1,509,837 | 15,352 | **98.4x** | WASH |

All three flag WASH (>20x threshold). AIN/GUA override: use `binance_alpha` (store) — cleaner than MEXC wash. APR retains KuCoin with `wash_suspect_flag=True`.

---

## S-3 — DEX (APR only)

APR CoinGecko: `id=apriori`, BSC contract `0x299ad4299da5b2b93fba4c96967b040c7f611099`  
DexScreener BSC: top pair liq=$681, vol24h=$758 — **negligible**  
→ APR is CEX-only market (KuCoin primary, MEXC secondary). No meaningful DEX vol.

---

## S-4 — Klines Fetched (Jul01-Aug16)

| Token | Source | Rows | Range |
|-------|--------|------|-------|
| AIN | Alpha store + bapi Aug04-16 | 47 | 2026-07-01 → 2026-08-16 |
| GUA | Alpha store + bapi Aug04-16 | 47 | 2026-07-01 → 2026-08-16 |
| APR | KuCoin | 47 | 2026-07-01 → 2026-08-16 |

Scratch: `scratch/spot_klines_{SYM}_20260817.csv`

---

## S-5 — Columns Written

**Schema:** Col31=vol_spot_usd, Col32=taker_spot_pct, Col33=spot_perp_ratio (row 2 field names)

| Token | Rows written | ratio_ok | oi_null | taker_spot_pct | Status |
|-------|------------|---------|--------|---------------|--------|
| AIN | 47 | 29 | 18 | NaN/ABSTAIN (Alpha) | **TEMP FILE** (AIN locked in Excel) |
| GUA | 40 | 29 | 11 | NaN/ABSTAIN (Alpha) | SAVED (last date Aug09) |
| APR | 43 | 32 | 11 | NaN/ABSTAIN (KuCoin) | SAVED (last date Aug12) |

**oi_null:** Early Jul rows (Jul01-Jul18 ≈) had no oi_usd in DAILY → spot_perp_ratio=None for those dates.  
**taker_spot_pct:** ABSTAIN (NaN) for all three tokens:
- AIN/GUA: Alpha endpoint — klines[9]==klines[5] (broken field, per L-ALPHA-TAKER rule)
- APR: KuCoin klines no taker_buy field

**ACTION REQUIRED:**  
Close CASE_AIN.xlsx in Excel → copy `scratch/CASE_AIN_spot_patch_20260817.xlsx` → `docs/case_files/CASE_AIN.xlsx`

---

## S-5 Spot-Checks

```
AIN Aug16: vol_spot=10,664 USD  ratio=0.002228  oi_usd=4,786,108  venue=binance_alpha
AIN Aug15: vol_spot=60,038 USD  ratio=0.012707  oi_usd=4,724,817  taker=NaN
AIN Aug12: vol_spot=22,965 USD  ratio=0.005033  oi_usd=4,562,411

GUA Aug09: vol_spot=1,053,263 USD  ratio=0.2029   oi_usd=5,190,235  venue=binance_alpha
GUA Aug08: vol_spot=427,662 USD   ratio=0.0867   oi_usd=4,932,196

APR Aug12: vol_spot=3,928,680 USD  ratio=0.4054  oi_usd=9,689,917  venue=kucoin WASH
APR Aug15: vol_spot=1,709,485 USD  ratio=N/A     (date past DAILY last row Aug12)
```

---

## S-6 — Analysis

### AIN — "30M token ≈ $2.4M nạp từ 04/08"

| Metric | Value |
|--------|-------|
| Price Aug16 | $0.07960 |
| 30M tokens value | $2,388,033 |
| Alpha vol Jul avg | 28,191 USD/day (31 days) |
| Alpha vol Aug04-15 avg | 32,317 USD/day (12 days) |
| Vol change post-nạp | **+14.6%** (NHÍCH nhẹ) |

**Exit liquidity (use Alpha vol — more reliable than MEXC WASH):**

| Participation | Exit days |
|--------------|-----------|
| 10% of Alpha vol | **739 days** |
| 30% of Alpha vol | **246 days** |
| 10% of MEXC vol (WASH) | 270 days |
| 30% of MEXC vol (WASH) | 90 days |

→ AIN effectively **illiquid** on current vol. Even at MEXC wash vol (optimistic) = 90 days at 30% participation.  
→ Top vol days all pre-Aug04: Jul02 (109k), Jul20 (70k), Jul30 (61k). Post-nạp vol không đột phá.

### GUA — Alpha vol spike Aug

| Period | Avg vol/day |
|--------|------------|
| Jul 2026 | 176,006 USD |
| Aug05-11 | **875,192 USD** (+397%) |

Top dates: Aug10 (2.89M), Jul02 (2.78M), Aug11 (1.30M), Aug09 (1.05M)  
Price: Jul02 = $0.0644 → Aug10 = $0.0557 → Aug16 = $0.0429 (downtrend)  
→ Volume spike with falling price = distribution signal. GUA DAILY cần rebuild Aug10-16 để thấy đủ.

### APR — CEX vol vs claim

| Metric | Value |
|--------|-------|
| Jul avg vol (KuCoin) | 47,018 USD/day |
| Aug01-16 avg vol | 609,363 USD/day |
| Aug12 peak | **3,928,680 USD** |
| Aug15 KuCoin now | 1,709,485 USD |
| "$42.6M/day" claim | **28x off vs KuCoin** |
| DEX BSC | $758 vol — negligible |

Aug12-16 price collapse: $0.60 → $0.20 (-67%). Vol spike coincides with dump. wash_flag=True (98.4x depth ratio) — confirmed wash pattern.

---

## SANITY

| Check | Result |
|-------|--------|
| AIN taker_spot_pct = NaN | PASS (ABSTAIN, not 0 or 1) |
| GUA venue = binance_alpha (not MEXC wash) | PASS |
| APR wash_suspect_flag = True | PASS |
| APR taker_spot_pct = NaN | PASS (KuCoin no taker) |
| spot_perp_ratio = vol_spot / oi_usd | PASS (29-32 rows computed) |
| DEX fallback only for APR | PASS (but BSC negligible → CEX wins) |
| AIN store confirmed before fetch | PASS (PROBE STORE TRƯỚC rule) |

---

## Venue Selection (Final)

| Token | venue_top_measurable | wash_suspect_flag | taker_spot_pct |
|-------|---------------------|-----------------|---------------|
| AIN | binance_alpha | False (override from MEXC WASH) | NaN ABSTAIN |
| GUA | binance_alpha | False (override from MEXC WASH) | NaN ABSTAIN |
| APR | kucoin | **True** (ratio=98.4x) | NaN ABSTAIN |

---

## Pending / DỪNG

- **CASE_AIN.xlsx:** Cần operator đóng Excel → copy temp patch file (xem S-5 ACTION REQUIRED)
- **CASE_GUA DAILY + CASE_APR DAILY:** Kết thúc ở Aug09/Aug12 — cần rebuild để fill Aug10-16 spot cols
- **Data source metadata:** Chưa ghi vào col41/col42 (NGUON section) — todo nếu cần audit trail đầy đủ
