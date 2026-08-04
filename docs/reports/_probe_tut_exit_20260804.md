# PROBE TUT EXIT — E1/E2/E3/E5
Run: 2026-08-04 04:34 UTC
TUT rows loaded: 35

Window 20/07→latest: 12 ngày

## E1 — Daily Series 20/07→03/08

| date | fn | px_avg | vol_M | taker% | f_avg | f_min | f_max | OI_M | pos_r | acc_r | gLSR | div_avg3 | glsr_s5d | ret_20j |
|------|----|---------:|------:|-------:|------:|------:|------:|-----:|------:|------:|-----:|---------:|----------:|--------|
| 2026-07-20 | 6 | 0.01371 | 7.23 | 48.6 | 0.00005 | 0.00005 | 0.00005 | 3.09 | 4.725 | 2.433 | 1.909 | — | — | +0.0% |
| 2026-07-21 | 6 | 0.01516 | 15.80 | 49.4 | 0.00005 | 0.00005 | 0.00005 | 3.41 | 4.305 | 2.466 | 1.896 | +10.54% | — | +10.5% |
| 2026-07-22 | 6 | 0.01444 | 7.49 | 42.6 | 0.00005 | 0.00005 | 0.00005 | 3.76 | 3.887 | 2.233 | 1.778 | +2.90% | — | +5.3% |
| 2026-07-23 | 6 | 0.01387 | 4.03 | 49.1 | 0.00005 | 0.00005 | 0.00005 | 3.39 | 5.083 | 2.308 | 1.728 | +0.61% | — | +1.1% |
| 2026-07-27 | 6 | 0.01571 | 1.53 | 48.0 | 0.00005 | 0.00005 | 0.00005 | 4.20 | 4.333 | 2.481 | 1.904 | +1.53% | — | +14.6% |
| 2026-07-28 | 6 | 0.01389 | 2.43 | 45.0 | 0.00005 | 0.00005 | 0.00005 | 3.74 | 4.657 | 2.779 | 2.018 | -0.76% | 1.057 | +1.3% |
| 2026-07-29 | 6 | 0.01466 | 2.23 | 51.0 | 0.00005 | 0.00005 | 0.00005 | 3.68 | 4.911 | 2.525 | 1.922 | +2.42% | 1.014 | +6.9% |
| 2026-07-30 | 6 | 0.01460 | 1.13 | 47.6 | 0.00005 | 0.00005 | 0.00005 | 3.75 | 4.585 | 2.405 | 1.851 | -2.16% | 1.041 | +6.4% |
| 2026-07-31 | 6 | 0.01560 | 2.39 | 51.5 | 0.00005 | 0.00005 | 0.00005 | 3.90 | 4.959 | 2.359 | 1.857 | +4.01% | 1.074 | +13.8% |
| 2026-08-01 | 6 | 0.01735 | 9.82 | 52.0 | 0.00005 | 0.00005 | 0.00005 | 4.29 | 4.169 | 2.430 | 2.031 | +5.90% | 1.067 | +26.6% |
| 2026-08-02 | 6 | 0.01741 | 3.06 | 47.6 | 0.00005 | 0.00005 | 0.00005 | 5.00 | 3.458 | 2.103 | 1.721 | +6.15% | 0.853 | +27.0% |
| 2026-08-03 | 6 | 0.01986 | 17.95 | 52.7 | 0.00005 | 0.00005 | 0.00005 | 4.83 | 4.014 | 2.206 | 1.685 | +8.54% | 0.877 | +44.8% |

## E2 — 5 Co Exit (BIDWALK khuon)

### Co 1 — GHE ROI: pos_r sap >=25-30% tu dinh

- Dinh pos_r: 5.083 (ngay 2026-07-23)
- Hien tai pos_r: 4.014 (ngay 2026-08-03)
- Drop tu dinh: 21.0%
- **CO 1: CHUA THOA** — can sap them 4.0% nua (hien tai 21.0% vs nguong 25%)

### Co 2 — NHIEN LIEU CAN: gLSR ve ~1 (L-17: ve 1 = dinh trong vai gio)

- gLSR hien tai: 1.685 (ngay 2026-08-03)
- gLSR 5 ngay truoc: 1.922
- slope_5d (A5): 0.877
- **CO 2: CHUA THOA** — gLSR=1.685 (cach 1 = 0.685); slope_5d=+0.877

### Co 3 — FUNDING: ghim con khong? Bung duong + parabol = co dinh nong

- f_avg hien tai: 0.00005
- f_avg max trong window: 0.00005 (ngay 2026-07-20)
- **CO 3: PINNED** — f_avg=0.00005 (=5bps min ghim); chua bung parabol

### Co 4 — SUPPRESSOR: dist_wall (taker>=50% ma gia tut) + post_climax

- Dinh px: 0.01986 (ngay 2026-08-03)
- Hien tai px: 0.01986 (ngay 2026-08-03)
- Drawdown tu dinh: 0.0%
- **CO 4: CHUA THOA** — drawdown 0.0% (can them 25.0% nua)
- dist_wall: khong co ngay nao taker>=50% + px tut trong window

### Co 5 — GIA TANG + OI GIAM (cover/thoat vao da — pha muon)

- Ngay px+ va OI-: 2 ngay
  - 2026-07-29: px +5.6%, OI -1.4% → ai do cover vao da tang
  - 2026-08-03: px +14.1%, OI -3.3% → ai do cover vao da tang
- **CO 5: THOA** — 2 ngay px+/OI- → pattern thoat ro rang

## E3 — Tang toc rui ro: px hien tai vs 0.0130 (moc 20/07)

- Moc 20/07: 0.0130 USDT
- Hien tai: 0.01986 USDT (ngay 2026-08-03)
- Tong ret tu moc: +52.7%
- Ngay vol max (parabol candidate): 2026-08-03 — vol=17.95M
- Ngay ret max 1 ngay: 2026-08-03 — ret=+14.1%
- Ngay vol > 3x avg (6.26M avg): 0 ngay
- Tang toc: GRIND DEU — chua co parabol ro net (token overhang 83% = lua chon chot tot)

## E5 — Summary: Co dang bat + Khoang cach con lai

**Co bat: 1 / 5 chinh**

| co | trang thai | so | ngay | khoang cach con lai |
|----|-----------|-----|------|---------------------|
| Co1 GHE-ROI | **CHUA** | drop 21.0% | 2026-08-03 | can them 4.0% drop nua |
| Co2 NHIEN-LIEU | **CHUA** | gLSR=1.685 | 2026-08-03 | gLSR can xuong ~1.0 (0.685 nua) |
| Co3 FUNDING | **PINNED** | f=0.00005 | 2026-08-03 | ghim 5bps, chua bung |
| Co4 SUPPRESSOR | **CHUA** | draw=0.0% | 2026-08-03 | can them 25.0% tu dinh |
| Co5 PX+OI- | **THOA** | 2 ngay px+/OI- | 2026-08-03 | da bat |

_E4 (on-chain exchange balance TUT): operator feed — may khong co nguon nay._
