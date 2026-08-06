# ZBT Cold-Refresh Report — 2026-08-06

**Symbol:** ZBTUSDT  **Window:** 2026-07-23 → 2026-08-05 (closed days) + intraday 06/08  
**Boundary:** 00:00 UTC = open ngày D  **Probe:** _probe_zbt_20260806.py  **UTC:** 2026-08-06T06:56:16

---

## Z1 — Export canonical (freshwatch_daily_2026-08.csv + 07.csv)

**Source:** `D:\Check onchain fresh wallets\data\export\freshwatch_daily_2026-08.csv` (+ 07.csv fallback)  
**Schema:** date | px_avg | vol_quote | taker_buy_pct | funding_avg | fn | oi_usd | lsr_pos_r | lsr_acc_r | lsr_global_r | data_ok | low_conf | src_ratio

Export MISSING: `2026-07-24, 2026-07-25, 2026-07-26` → fallback klines (LSR/funding=MISSING)

```
date         px_avg     vol_q_usdt  taker%    f_avg         fn    oi_usd      pos_r   acc_r   gLSR    ok    lc
-----------------------------------------------------------------------------------------------------------
2026-07-23   0.108405   22,092,107   50.6%  5.00e-05      6    8,725,833   2.3707  0.5780  0.3951  True  F
2026-07-24   [MISSING]  10,524,962      —       —          —    9,318,649      —       —       —     —     —  fapi_klines
2026-07-25   [MISSING]   4,582,927      —       —          —    8,545,317      —       —       —     —     —  fapi_klines
2026-07-26   [MISSING]   9,322,656      —       —          —    8,452,299      —       —       —     —     —  fapi_klines
2026-07-27   0.114577    6,418,842   47.1%  5.00e-05      6    8,786,963   2.7540  0.6614  0.4482  True  F
2026-07-28   0.112762    4,704,342   49.0%  5.00e-05      6    8,860,722   2.7491  0.7097  0.4575  True  F
2026-07-29   0.112684    4,983,027   47.1%  5.00e-05      6    8,609,763   2.6781  0.7024  0.4626  True  F
2026-07-30   0.116593    6,910,711   51.7%  5.00e-05      6    8,476,904   2.7421  0.7077  0.4535  True  F
2026-07-31   0.115980    4,394,032   48.6%  5.00e-05      6    9,143,286   2.9249  0.7106  0.4643  True  F
2026-08-01   0.116464    2,541,983   45.8%  5.00e-05      6    8,981,809   3.0691  0.7699  0.5140  True  F
2026-08-02   0.122224    6,211,662   49.4%  5.00e-05      6    8,718,627   3.4081  0.7544  0.5117  True  F
2026-08-03   0.118481    3,507,809   47.1%  5.00e-05      6    9,297,648   3.2607  0.8245  0.5586  True  F
2026-08-04   0.111582    3,564,479   50.0%  5.00e-05      6    8,579,454   3.3595  0.8175  0.5571  True  F
2026-08-05   0.117641   15,060,833   50.6%  5.00e-05      6    7,889,446   3.4072  0.7467  0.4914  True  F
```

**fn=6 tất cả ngày export** → không có SUSPECT từ fn  
**data_ok=True tất cả** → không có data_bad  
**low_conf=False tất cả** → taker_ratio reliable

---

## Z2 — PERP klines 1d (fapi, 00:00-23:59 UTC)

**Source:** `fapi/v1/klines?symbol=ZBTUSDT&interval=1d&limit=30` fetched 2026-08-06T06:56 UTC

```
date         open      high      low       close     vol_q_usdt       flag
--------------------------------------------------------------------------
2026-07-18   0.0914    0.1069    0.0806    0.1020    33,010,291      VOL≥3×med, MOVE+11.6%
2026-07-19   0.1020    0.1071    0.0930    0.0934    24,825,748
2026-07-20   0.0934    0.0970    0.0877    0.0902    10,527,484      LOW_MIN (chuỗi hồi)
2026-07-21   0.0902    0.1011    0.0870    0.0981    15,143,840
2026-07-22   0.0982    0.1051    0.0957    0.1024     9,718,756
2026-07-23   0.1024    0.1148    0.1004    0.1122    11,046,053
2026-07-24   0.1122    0.1168    0.1055    0.1092    10,524,962
2026-07-25   0.1092    0.1133    0.1072    0.1086     4,582,927
2026-07-26   0.1086    0.1221    0.1050    0.1134     9,322,656
2026-07-27   0.1133    0.1179    0.1106    0.1148     6,122,781
2026-07-28   0.1148    0.1163    0.1084    0.1139     4,704,342
2026-07-29   0.1139    0.1156    0.1095    0.1105     4,983,027
2026-07-30   0.1105    0.1249    0.1061    0.1177     6,910,711
2026-07-31   0.1178    0.1197    0.1127    0.1175     4,394,032
2026-08-01   0.1175    0.1197    0.1135    0.1163     2,541,983
2026-08-02   0.1163    0.1269    0.1154    0.1226     6,211,662
2026-08-03   0.1226    0.1237    0.1130    0.1164     3,507,809
2026-08-04   0.1164    0.1172    0.1074    0.1077     3,564,479
2026-08-05   0.1077    0.1330    0.1026    0.1269    15,060,833      MOVE+17.8%
2026-08-06*  0.1269    0.1328    0.1246    0.1300    10,547,971      *partial intraday
```

**med14 vol_perp:** 9,322,656 USDT  
**MIN close 14d:** 2026-07-20 c=0.0902  
**Taker perp:** từ export (canonical) — thấy cột Z1

---

## Z3 — Derived metrics

### Z3a — Pin streak (f_avg ∈ [4e-05, 6e-05])

```
Ngày trong window có export:   2026-07-23, 07-27→08-05 (tất cả f_avg=5.00e-05)
Streak liên tục đến 2026-08-05: 10 ngày  (07-27 → 08-05, 07-23 gián đoạn 24-26)
Ngày f âm (micro-dip): KHÔNG CÓ
```

> Note: 24-26/07 thiếu export → streak thực tế có thể cao hơn nếu ngày đó cũng pin. Klines fallback không có funding.

### Z3b — pos_r series (gate cũ >3.0)

```
date         pos_r    ≥3.0?
2026-07-23   2.3707
2026-07-27   2.7540
2026-07-28   2.7491
2026-07-29   2.6781
2026-07-30   2.7421
2026-07-31   2.9249
2026-08-01   3.0691   YES
2026-08-02   3.4081   YES
2026-08-03   3.2607   YES
2026-08-04   3.3595   YES
2026-08-05   3.4072   YES
```

Max=3.4081 (02/08) · Min=2.3707 (23/07)  
**Vượt 3.0 liên tục từ 2026-08-01 đến 2026-08-05 (5 ngày)**

### Z3c — div_avg3 = avg3(pos_r) / avg3(acc_r)  [rolling 3d]

```
date         pos_r    acc_r    avg3_pos   avg3_acc   div_avg3   window
2026-07-25      —        —      MISSING    MISSING        —     [23,24,25] — missing 24-25
2026-07-26      —        —      MISSING    MISSING        —     [24,25,26] — missing 24-26
2026-07-27      —        —      MISSING    MISSING        —     [25,26,27] — missing 25-26
2026-07-28      —        —      MISSING    MISSING        —     [26,27,28] — missing 26
2026-07-29   2.6781   0.7024    2.7271     0.6912      3.9456  [27,28,29]
2026-07-30   2.7421   0.7077    2.7231     0.7066      3.8538  [28,29,30]
2026-07-31   2.9249   0.7106    2.7817     0.7069      3.9351  [29,30,31]
2026-08-01   3.0691   0.7699    2.9120     0.7294      3.9924  [30,31,01]
2026-08-02   3.4081   0.7544    3.1340     0.7450      4.2069  [31,01,02]
2026-08-03   3.2607   0.8245    3.2460     0.7829      4.1459  [01,02,03]
2026-08-04   3.3595   0.8175    3.3428     0.7988      4.1847  [02,03,04]
2026-08-05   3.4072   0.7467    3.3425     0.7962      4.1978  [03,04,05]
```

**div_avg3 xu hướng:** tăng từ 3.85 (30/07) lên 4.20 (02/08), ổn định 4.1-4.2 qua 03-05/08

### Z3d — glsr_slope_5d = gLSR(t) / gLSR(t−5)

```
date         gLSR(t)  gLSR(t-5)   slope_5d
2026-07-28    0.4575    0.3951      1.1579  (ref: 23/07)
2026-07-29       —         —        MISSING  (ref: 24/07 missing)
2026-07-30       —         —        MISSING  (ref: 25/07 missing)
2026-07-31       —         —        MISSING  (ref: 26/07 missing)
2026-08-01    0.5140    0.4482      1.1468  (ref: 27/07)
2026-08-02    0.5117    0.4575      1.1185  (ref: 28/07)
2026-08-03    0.5586    0.4626      1.2075  (ref: 29/07)
2026-08-04    0.5571    0.4535      1.2284  (ref: 30/07)
2026-08-05    0.4914    0.4643      1.0584  (ref: 31/07)
```

**slope_5d dương >1.0 tất cả ngày đủ data** → gLSR vẫn cao hơn 5d trước

### Z3e — oi_cycle_pos

```
OI window = 23/07→05/08 (export dates only):
  min14: 7,889,446 USDT (05/08)  · max14: 9,297,648 USDT (03/08)
  OI_05/08: 7,889,446 → OI/min=1.0000 → floor_flag ≤1.1×: YES

OI hist 30d (fapi endpoint, 00:00 UTC snapshot):
  min30: 7,708,393 (18/07)  · max30: 11,221,125 (14/07)
  latest (06/08 00:00): 10,084,563
  OI_latest/min30: 1.3083 → floor_flag: NO
```

> Hai window cho kết quả khác nhau do ngày 06/08 OI tăng mạnh (7.9M→10.1M)

---

## Z4 — Spot layer

### Z4a — Binance SPOT klines (ZBTUSDT)

**Source:** `api/v3/klines?symbol=ZBTUSDT&interval=1d`

```
date         open      high      low       close     vol_spot_usdt   vol_spot/vol_perp
--------------------------------------------------------------------------------------
2026-07-18   0.0914    0.1071    0.0808    0.1021     7,559,250       0.229
2026-07-19   0.1020    0.1070    0.0932    0.0935     3,816,425       0.154
2026-07-20   0.0936    0.0971    0.0879    0.0903     1,667,069       0.158
2026-07-21   0.0903    0.1010    0.0872    0.0982     2,615,429       0.173
2026-07-22   0.0981    0.1053    0.0956    0.1024     1,971,541       0.203
2026-07-23   0.1025    0.1148    0.1005    0.1122     2,362,962       0.214
2026-07-24   0.1121    0.1170    0.1056    0.1092     2,037,632       0.194
2026-07-25   0.1091    0.1133    0.1073    0.1085     1,103,203       0.241
2026-07-26   0.1085    0.1217    0.1050    0.1133     2,345,884       0.252
2026-07-27   0.1133    0.1178    0.1107    0.1148     1,483,029       0.242
2026-07-28   0.1147    0.1163    0.1083    0.1140     1,323,597       0.281
2026-07-29   0.1139    0.1156    0.1098    0.1108     1,541,066       0.309
2026-07-30   0.1106    0.1248    0.1062    0.1177     2,118,287       0.307
2026-07-31   0.1177    0.1196    0.1130    0.1175     1,013,687       0.231
2026-08-01   0.1175    0.1198    0.1136    0.1163       535,087       0.210
2026-08-02   0.1163    0.1270    0.1154    0.1226     1,688,089       0.272
2026-08-03   0.1225    0.1237    0.1131    0.1164       860,103       0.245
2026-08-04   0.1164    0.1172    0.1076    0.1078       957,955       0.269
2026-08-05   0.1077    0.1332    0.1028    0.1270     4,776,726       0.317
```

**vol_spot/vol_perp max = 0.317** (05/08) → không ngày nào vượt 3× → L-29 guard: CLEAR (không có ngày ABSTAIN)  
**Spot taker:** k[9]/k[7]=346.2% → ABSTAIN (units invalid — base not quote)

### Z4b — Alpha layer (ALPHA_435)

```
ZBT = ALPHA_435  (xác nhận từ alpha_id_map.json + token list API)
Status: fullyDelisted=True, offline=True  (token list 06/08)
Alpha klines endpoint → HTTP 400 Bad Request
Local store (spot_klines_1d, venue=binance_alpha): ZBT NOT FOUND
  → ZBT là 1 trong 11 symbols fail trong backfill 04/08 (no klines data)

vol_alpha = MISSING (delisted) → L-29 alpha guard: N/A
Alpha taker: ABSTAIN (k[9]==k[5] per spec, moot vì delisted)
```

### Z4c — Order book depth ±2% (snapshot 06/08T06:56 UTC)

```
px_now = 0.1299  |  bid±2% = $11,723  |  ask±2% = $17,857  |  total ≈ $29,580
[tham chiếu U50 target: $164,000]  [caveat: intraday snapshot, không historical]
```

---

## Z5 — On-chain / kho

| Layer | Status |
|-------|--------|
| Nansen wallet flow | LOCKED (NANSEN_KEY_LOCKED) — CẦN OPERATOR |
| BscScan balance | CHƯA PROBE — cần operator approve |
| Unlock schedule | UNVERIFIED — nguồn aggregator đơn = không đủ chuẩn L-28 |
| Exchange dominance | MISSING — không có baseline ZBT trong ledger |

---

## Z6 — Cross-reference grep

**Source:** grep "ZBT" across whale_data + Check-onchain dirs (06/08)

| File | Finding |
|------|---------|
| `docs/reports/missing_jul.md` | ZBTUSDT missing=3/29 dates=2026-07-24,25,26 |
| `docs/reports/_probe_alpha_resolver_20260804.md` | ZBT→ALPHA_435, OK |
| `docs/reports/_probe_alpha_deadcode_20260803.md` | ZBTUSDT OK(0.4825) |
| `D:\Check onchain\u50_universe.csv` | ZBT, zerobase, 0xfab99...7777, 124904111, cg |
| `D:\Check onchain\u50_venues.csv` | ZBT binance, vol_perp=2,610,159 (reference period) |
| `D:\Check onchain\data\export\freshwatch_daily_2026-07.csv` | có rows 01-03/07 |
| `D:\Check onchain\data\history\daily_2026-08.csv` | có rows 01-03/08 |
| `D:\Check onchain\data\history\run_log.csv` | runs 24,25,26/07 OK với 1 skip/ngày |
| agent_log.md | ZBT KHÔNG có trong agent_log — cold-refresh lần đầu |

**Kết luận Z6:** Export gap 24-26/07 khớp với run_log (1 skip/ngày → raw klines 30-nến bị bỏ qua ngày đó). ZBT có trong U50 universe. Baseline từ u50_venues: vol_perp_ref=2.61M USDT (chu kỳ u50 cũ).

---

## Layer coverage summary

| Layer | 23/07 | 24-26/07 | 27/07→05/08 | 06/08 intraday |
|-------|-------|----------|-------------|----------------|
| px (perp klines) | OK | OK (klines) | OK | OK |
| vol_perp | OK | OK (klines) | OK | partial |
| funding / fn | fn=6 | MISSING | fn=6 | — |
| OI | OK | OK (hist) | OK | OK |
| LSR pos_r/acc_r | OK | MISSING | OK | partial |
| gLSR | OK | MISSING | OK | OK (5m) |
| taker_buy_pct | 50.6% | MISSING | 45-52% | — |
| spot OHLCV | OK | OK | OK | partial |
| alpha vol | MISSING (delisted) | MISSING | MISSING | MISSING |
| on-chain | LOCKED | LOCKED | LOCKED | LOCKED |

---

## Intraday 06/08 (L-21 — KHÔNG vào bảng DAILY)

*Ghi nhận raw, timestamp UTC, không kết luận*

```
UTC: 2026-08-06T06:56:16
px:         0.12992
OI_token:   81,580,125 ZBT  (ts=1785999374862)
gLSR:       0.6044  (long=0.3767, short=0.6233) — snapshot 5m 06:50 UTC
OI hist 06/08 00:00:  10,084,563 USDT  [src=fapi openInterestHist]
vol_perp (partial):   10,547,971 USDT  [klines bar đang mở]
```

---

*Report generated: 2026-08-06 | Probes: _probe_zbt_20260806.py, _probe_zbt_alpha2-5_20260806.py*  
*STOP — no commit ngoài agent_log + report file (per task spec)*
