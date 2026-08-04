# PROBE K1+K6: IDOL — case_daily 03/08 + Suppressor + Campaign
Run: 2026-08-04 03:39 UTC
Freshwatch IDOL rows loaded: 67

## K1 — Daily Series 25/07→latest

| date | fn | px_avg | vol_perp_M | taker% | f_avg | oi_usd_M | pos_r | acc_r | gLSR | data_ok |
|------|----|---------|-----------:|-------:|------:|---------:|------:|------:|-----:|---------|
| 2026-07-27 | 6 | 0.01568 | 16.92 | 48.5 | 0.00034 | 6.60 | 2.059 | 1.360 | 1.369 | True |
| 2026-07-28 | 6 | 0.01681 | 5.93 | 48.0 | 0.00020 | 10.71 | 2.207 | 0.992 | 1.038 | True |
| 2026-07-29 | 6 | 0.01569 | 3.00 | 47.3 | 0.00007 | 9.91 | 2.328 | 1.161 | 1.389 | True |
| 2026-07-30 | 6 | 0.01523 | 3.00 | 52.8 | 0.00010 | 8.87 | 2.558 | 1.209 | 1.459 | True |
| 2026-07-31 | 6 | 0.01640 | 7.34 | 49.9 | 0.00032 | 8.81 | 2.546 | 1.240 | 1.558 | True |
| 2026-08-01 | 6 | 0.02395 | 175.67 | 51.5 | 0.00009 | 9.84 | 2.524 | 1.183 | 1.489 | True |
| 2026-08-02 | 6 | 0.02312 | 40.72 | 50.1 | 0.00005 | 10.48 | 1.731 | 1.178 | 1.144 | True |
| 2026-08-03 | 1 | - | - | 44.6 | 0.00005 | 9.50 | 1.805 | 1.654 | 1.636 | True |

## K1 — L-41 fn Verify (03/08)

- 03/08 fn = 1.0
- **L-41 FAIL** — fn=1.0 (!=6) => tiep tuc giam sat

## K1 — Suppressor Scan (post-climax >=25% tu dinh)

- Dinh confirmed (01/08 lich su): 0.02850 USDT
- Latest px: 0.00000 USDT (date: 2026-08-03)
- Drawdown tu dinh: 0.0%
- Nguong suppressor (75% dinh): 0.02138 USDT
- **SUPPRESSOR: CHUA THOA** (cur 0.00000 > 0.02138)

## K1 — OI + Funding Regime 01→04/08

| date | oi_usd_M | dOI | f_avg | regime | pos_r | gLSR |
|------|---------|-----|-------|--------|-------|------|
| 2026-08-01 | 9.84M | — | 0.000095 | FLOAT | 2.524 | 1.489 |
| 2026-08-02 | 10.48M | +0.64M | 0.000050 | PINNED | 1.731 | 1.144 |
| 2026-08-03 | 9.50M | -0.98M | 0.000050 | PINNED | 1.805 | 1.636 |

## K6 — Campaign Autopsy Timeline

| window | event | so lieu | nguon | bang chung |
|--------|-------|---------|-------|-----------|
| 03-05/07 | Staging on-chain | 7x20M=140M + others -> 273M tong rut Binance Alpha custody | EVENTS E1 (PENDING txhash) | Z4-rev: GOM qua Alpha mechanism |
| 23/07 | Bait-probe DEX | vol=167.26M (8x nen) spike collapse <4d | freshwatch | gLSR 3.95M crowd khong bi trap (sap lai) |
| 27/07 | OI accumulate | OI 10.71M -> tang | freshwatch | pos_r 2.207 28/07 longs loading pre-ignition |
| 28/07 | OI ignition +62% | OI 6.60M->10.71M | freshwatch | taker=0.480 (bear) = MM mua limit khi retail sell |
| 28-31/07 | Build perp (nen do) | OI 8.81M, pos_r 2.546 | freshwatch | Longs loaded pre-markup; gLSR leo |
| 01/08 | Markup ignite | px +54.5%, vol=175.67M (~10x avg), taker=51.5% | freshwatch | BIDWALK-A crowd khong phat hien |
| 02/08 | Thoat perp + on-chain | OI 10.48M, pos_r sap 1.731, rut 273M BSC | freshwatch+EVENTS | gLSR 10.48M sap = longs unwind |
| 03/08 | Post-climax | px ?, OI 9.50M | freshwatch | Funding ghim/float? xem bang K1 OI |
| 04/08 | Round-trip hien tai | px 0.00000, drawdown 0.0% tu dinh | freshwatch latest | Suppressor CHUA THOA |

## K6 — Xep hang 4 gia thuyet ket thuc

| rank | thesis | bang chung ung ho | bang chung phan | ket luan |
|------|--------|------------------|----------------|---------|
| #1 | flip-by-design | Rut 273M TRONG markup (02/08); pos_r sap dung khi crowd vao; staging 7xSent=0 truoc do | Z1 chua confirm redeposit -> cho K2 | DAN DAU neu K2 thay redeposit |
| #2 | fuel-died | gLSR 02/08 sap (crowd unwind, khong du luc); vol 03/08 sup | OI 02/08 khong sap manh (10.48M) — van con open | Co the ket hop voi flip |
| #3 | wrong-side | taker 01/08=51.5% (<55%) MM khong dat cuoc mot chieu; OI on dinh | Markup cuc manh +54.5% kho la wrong-side | THAP |
| #4 | unlock-deadline | Unlock 11/08 97.29M nhung markup no 10d TRUOC | W6: UNLIKELY theo lesson | LOAI |
