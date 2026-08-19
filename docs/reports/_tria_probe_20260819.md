# TRIA UN-HEDGE PROBE — 19/08/2026
**Target:** TRIAUSDT (Alpha ALPHA_669 "Tria" · BSC + Perp fapi)  
**Window:** 2026-07-20 → 2026-08-18 (nến đóng D-1, L-21) + intraday 19/08 [UNVERIFIED, TÁCH]  
**Probe:** `_probe_tria_20260819.py` (read-only, no CASE file, no commit gì thay đổi số)  

**Data provenance (L-48):**
- `data-source`: fapi.binance.com (klines/fundingRate/OI/topLongShortPositionRatio/topLongShortAccountRatio/globalLongShortAccountRatio + ticker/24hr + openInterest snapshot), `data/export/freshwatch_daily_*.csv` (LSR history, 81 TRIA rows), bapi/defi/v1 (Alpha), VPS 5.223.67.21 (`/root/Data_back_test/whale_data/data/export/watchlist_log_2026-08.csv`)
- `machine`: local Windows (fetch) + VPS (cross-check)
- `date-range`: 2026-07-20→2026-08-18 (daily); intraday 2026-08-19 03:12 UTC
- `code-commit`: probe committed post-paste

**Layer coverage:** I (Perp) · II (Crowd-LSR 4 endpoints) · IV (Funding) · V (Spot/Alpha, Alpha-only)

---

## §A. STRUCTURE

| Metric | Value |
|--------|-------|
| PERP fapi | **TRIAUSDT** TRADING (onboard 2026-02-06) |
| Alpha bapi | **ALPHA_669** "Tria" · fullyDelisted=False · offline=False · BSC |
| Binance SPOT api/v3 | **KHÔNG có** (0 base=TRIA match) — **Alpha-only + Perp** |
| taker_spot_pct | ABSTAIN-STRUCTURAL (L-51 draft, không tank spot) |

---

## §B1. PERP PER-DAY TABLE (Jul20→Aug18)

**Constraints verified:**
- Funding interval 4h × 6/day EVERY day (L-41) ✓
- OI dedup-at-read (30/30 unique, key=(date, timestamp)) ✓
- Taker scale-check: percent [43.77–52.39] scale ✓ (không cần ×100)

| date | c | ret% | vol_usd | oi_usd | Δoi | f_avg | fn | pos_r | acc_r | gLSR | div | div3 | tk% |
|------|---|------|---------|--------|-----|-------|-----|-------|-------|------|-----|------|-----|
| 07-20 | 0.00776 |   —   | 6,079,091 |       —   |    — | 0.000050 | 6 | 1.729 | 1.706 | 1.375 | 1.014 |     — | 43.77 |
| 07-21 | 0.00838 | +7.99 | 4,030,161 | 3,100,564 |    — | 0.000050 | 6 | 1.622 | 1.667 | 1.278 | 0.973 |     — | 47.64 |
| 07-22 | 0.00874 | +4.31 | 12,335,560| 3,325,556 | +224,993 | 0.000050 | 6 | 1.690 | 1.483 | 1.146 | 1.140 | 1.038 | 47.31 |
| 07-23 | 0.00839 | -4.05 | 11,772,537| 3,382,583 | +57,026  | 0.000050 | 6 | 1.816 | 1.516 | 1.162 | 1.198 | 1.099 | 46.03 |
| 07-24 | 0.00865 | +3.09 | 4,217,330 | 2,987,170 | -395,413 | 0.000050 | 6 | 1.864 | 1.614 | 1.292 | 1.154 | 1.164 | 49.54 |
| 07-25 | 0.00873 | +0.93 | 4,667,638 | 3,156,032 | +168,862 | 0.000050 | 6 | 1.799 | 1.766 | 1.399 | 1.019 | 1.119 | 47.85 |
| 07-26 | 0.00884 | +1.31 | 2,429,343 | 3,096,415 | -59,617  | 0.000050 | 6 | 1.825 | 2.067 | 1.605 | 0.883 | 1.007 | 52.39 |
| 07-27 | 0.00791 |-10.58 | 5,514,361 | 3,126,905 | +30,490  | 0.000050 | 6 | 1.771 | 2.046 | 1.675 | 0.866 | 0.918 | 46.25 |
| 07-28 | 0.00821 | +3.86 | 4,866,177 | 2,869,910 | -256,995 | 0.000050 | 6 | 1.632 | 2.090 | 1.643 | 0.781 | 0.843 | 48.59 |
| 07-29 | 0.00840 | +2.34 | 4,382,676 | 2,861,858 | -8,052   | 0.000050 | 6 | 1.769 | 2.215 | 1.756 | 0.799 | 0.814 | 46.86 |
| 07-30 | 0.00801 | -4.69 | 3,436,601 | 2,870,008 | +8,150   | 0.000050 | 6 | 1.697 | 2.178 | 1.723 | 0.779 | 0.786 | 46.30 |
| 07-31 | 0.00856 | +6.86 | 2,728,541 | 2,690,190 | -179,818 | 0.000050 | 6 | 1.598 | 2.385 | 1.908 | 0.670 | 0.747 | 46.85 |
| 08-01 | 0.00830 | -3.03 | 1,894,247 | 2,830,006 | +139,816 | 0.000050 | 6 | 1.576 | 2.499 | 2.007 | 0.631 | 0.690 | 47.23 |
| 08-02 | 0.00809 | -2.52 | 2,468,048 | 2,764,345 | -65,661  | 0.000050 | 6 | 1.544 | 2.939 | 2.495 | 0.525 | 0.603 | 50.63 |
| 08-03 | 0.00839 | +3.78 | 4,290,120 | 2,805,648 | +41,303  | 0.000050 | 6 | 1.423 | 3.223 | 2.775 | 0.441 | 0.524 | 49.88 |
| **08-04** | 0.00824 | -1.85 | 2,873,229 | 2,917,055 | +111,407 | 0.000050 | 6 | 1.416 | 3.184 | 2.775 | 0.445 | **0.469** ● | 49.74 |
| 08-05 | 0.00819 | -0.63 | 2,441,948 | 2,924,428 | +7,373   | 0.000050 | 6 | 1.374 | 3.292 | 2.979 | 0.417 | 0.434 ● | 49.88 |
| 08-06 | 0.00844 | +3.03 | 2,578,458 | 3,065,909 | +141,481 | 0.000050 | 6 | 1.287 | 3.460 | 3.281 | 0.372 | 0.410 ● | 48.47 |
| 08-07 | 0.00840 | -0.39 | 2,458,217 | 3,185,340 | +119,431 | 0.000050 | 6 | 1.330 | 3.498 | 3.417 | 0.380 | 0.389 ● | 47.57 |
| 08-08 | 0.00829 | -1.33 | 3,642,748 | 3,211,695 | +26,355  | 0.000050 | 6 | 1.275 | 3.762 | 3.686 | 0.339 | 0.363 ● | 46.31 |
| 08-09 | 0.00805 | -2.91 | 2,315,747 | 3,212,983 | +1,288   | 0.000050 | 6 | 1.242 | 4.476 | 4.179 | 0.277 | 0.328 ● | 44.76 |
| 08-10 | 0.00823 | +2.20 | 2,838,957 | 3,121,814 | -91,169  | 0.000050 | 6 | 1.260 | 3.771 | 3.682 | 0.334 | 0.315 ● | 46.22 |
| 08-11 | 0.00816 | -0.83 | 2,549,615 | 3,224,192 | +102,378 | 0.000050 | 6 | 1.223 | 4.408 | 4.322 | 0.277 | 0.294 ● | 45.75 |
| 08-12 | 0.00831 | +1.86 | 1,446,259 | 3,034,190 | -190,001 | 0.000050 | 6 | 1.313 | 4.516 | 4.356 | 0.291 | 0.299 ● | 49.60 |
| 08-13 | 0.00841 | +1.14 | 2,296,721 | 3,103,750 | +69,560  | 0.000050 | 6 | 1.349 | 3.993 | 4.089 | 0.338 | 0.301 ● | 47.65 |
| **08-14** | 0.00821 | -2.38 | 1,906,018 | 3,148,787 | +45,037 | 0.000050 | 6 | 1.290 | **5.017** | **4.662** | 0.257 | **0.292** min ● | 44.80 |
| 08-15 | 0.00839 | +2.28 | 1,108,783 | 3,025,427 | -123,360 | 0.000050 | 6 | 1.322 | 3.787 | 3.897 | 0.349 | 0.309 ● | 46.26 |
| 08-16 | 0.00843 | +0.46 | 1,897,745 | 3,022,999 | -2,429   | 0.000050 | 6 | 1.376 | 3.751 | 3.953 | 0.367 | 0.318 ● | 50.83 |
| 08-17 | 0.00826 | -1.98 | 1,243,683 | 3,269,761 | +246,762 | 0.000050 | 6 | 1.384 | 4.784 | 4.666 | 0.289 | 0.331 ● | 46.04 |
| **08-18** | **0.00975** | **+17.94** | **25,063,774** | 3,162,835 | -106,926 | 0.000050 | 6 | 1.395 | 4.628 | 4.754 | 0.301 | 0.316 ● | **50.13** |

(● = div_avg3 ≤ 0.5 = trong episode hedge)

---

## §B2. HEDGE EPISODE READOUT (watchlist v1.3)

**Episode #1 (ONGOING):**
| Field | Value |
|-------|-------|
| **start** | **2026-08-04** ✓ (khớp task nhận định) |
| end | 2026-08-18 (chưa break) |
| **hedge_start_px** | **$0.008398** (giá đóng Aug04) |
| px_today (Aug18 close) | $0.00975 |
| **px_dist%** | **+18.3%** (Aug18) hoặc **+22.75%** (intraday Aug19 03:12 UTC = $0.010304) |
| **struct_n** | **15 days** (Aug04 → Aug18) |
| **min div_avg3** | **0.2922 @ 2026-08-14** |
| div_avg3 hiện tại (Aug18) | 0.3157 (dưới 0.5, chưa break) |
| gap-tolerance | không dùng (chưa có ngày div>0.5 phá break) |

**Div_avg3 series trong episode (start → today):**
```
Aug04: 0.469 ● start
Aug05: 0.434
Aug06: 0.410
Aug07: 0.389 (dip)
Aug08: 0.363
Aug09: 0.328
Aug10: 0.315
Aug11: 0.294
Aug12: 0.299
Aug13: 0.301
Aug14: 0.292 ← MIN (đáy hedge, shorts dày nhất)
Aug15: 0.309 → bắt đầu NỚI
Aug16: 0.318
Aug17: 0.331
Aug18: 0.316 (dip nhẹ trở lại)
```

**→ Div bắt đầu nới:** Aug15 (từ 0.292 → 0.309, +0.017) — 1 ngày sau min.
**→ Nới thực chất:** Aug15→Aug17 (0.309→0.331) leo đều nhưng Aug18 dip lại 0.316. Chưa break 0.5. Struct vẫn còn.

---

## §B3. UN-HEDGE ANATOMY quanh 15-19/08

### (a) pos_r series — cú BẬT bắt đầu ngày nào?

```
Aug11: 1.223 (đáy pos_r)
Aug12: 1.313  (+7.4% 1d — bắt đầu leo)
Aug13: 1.349  (+2.7%)
Aug14: 1.290  (-4.4% dip)
Aug15: 1.322  (+2.5%)
Aug16: 1.376  (+4.1%)
Aug17: 1.384  (+0.6%)
Aug18: 1.395  (+0.8%)
```

**Δ pos_r rolling (2d):**
- Aug11→Aug13: 1.223→1.349 = **+10.3%** ✗ dưới 15%
- Aug13→Aug15: 1.349→1.322 = **-2.0%** (dip)
- Aug15→Aug17: 1.322→1.384 = **+4.7%**
- Aug16→Aug18: 1.376→1.395 = **+1.4%**

**Verdict:** cú BẬT bắt đầu **Aug12** (từ đáy 1.223 Aug11) nhưng **CHƯA đạt ngưỡng 🔵 15%/2d bất kỳ đâu trong window**. Cover kiểu slow-drip, không one-shot.

*(intraday Aug19: fapi topPos đưa Aug19 = 1.0613 — GIẢM mạnh vs Aug18 1.395, không phải bật. Chưa xác định do fapi thay đổi denominator hay pos_r thật sự sập. Không dùng số này cho DAILY conclusion.)*

### (b) OI GIẢM từ đỉnh nào, cover đi được mấy phần?

**Đỉnh OI trong window:** Jul23 = **$3,382,583** (2 tuần trước)  
**Sub-window Aug10-18 peak:** Aug17 = **$3,269,761**  
**Aug18 close:** $3,162,835 = **-3.3% vs Aug17** (chỉ nhích, không cover mạnh)

**Δ vs Aug17 peak:**
- Aug17→Aug18: -$106,926 (-3.3%) → cover **rất nhẹ**
- Từ đỉnh Jul23 → Aug18: -$219,748 (-6.5%) — cũng nhẹ

**Tank shorts còn lại:** div_raw Aug18 = 0.301. Từ min div 0.292 Aug14 → 0.301 Aug18 = **nới ~3%**. Shorts vẫn dày (div 0.30 vs neutral 1.0 = short-heavy 3.3× count).

Cover mới đi được phần rất nhỏ — **shorts còn nguyên tank**.

### (c) Funding: pin trước? un-pin/burst 15-18/08?

**Pin regime CỰC MẠNH:** f_avg = **+0.00005 EVERY DAY** trong toàn bộ 30 ngày (Jul20-Aug18) — nằm đúng cạnh pin band [4e-5, 6e-5]. **pin_streak = 30 days**.

- **KHÔNG có burst ≥15bps** trong daily window (f_avg cố định 5e-5 = 0.5bps daily).
- Tất cả 30 ngày f_min = f_max = 0.00005 (100% ticks đóng đinh 5e-5).

**Intraday Aug19:**
- Aug18 16:00 UTC: +0.00005 (còn pin)
- Aug18 20:00 UTC: +0.00005 (còn pin)
- **Aug19 00:00 UTC: -0.00010496** (**UN-PIN + FLIP ÂM** = -10.5bps burst, đứt chuỗi pin 30-ngày)

**→ Un-pin xảy ra INTRADAY Aug19 (không trong daily window B3).** Burst âm 10.5bps = short-side pressure (shorts trả funding cho longs).

### (d) gLSR/acc chuỗi — CROWD-CHASE bật ngày nào, crowd vào TRƯỚC hay SAU pos BẬT?

**gLSR / acc_r trend (crowd position):**
```
date    | gLSR  | acc_r
--------|-------|------
Aug08   | 3.686 | 3.762
Aug09   | 4.179 | 4.476  ← bắt đầu leo mạnh
Aug10   | 3.682 | 3.771  (dip)
Aug11   | 4.322 | 4.408  (bật lên)
Aug12   | 4.356 | 4.516
Aug13   | 4.089 | 3.993
Aug14   | 4.662 | 5.017  ← acc_r peak
Aug15   | 3.897 | 3.787  (dip)
Aug16   | 3.953 | 3.751
Aug17   | 4.666 | 4.784  (leo lại)
Aug18   | 4.754 | 4.628
```

**Crowd bật:** gLSR leo từ ~3.7 (Aug08) → ~4.7 (Aug14 peak) = **+27%** trong 6 ngày (Aug08→Aug14).

**pos_r bật:** từ 1.223 (Aug11 đáy) → 1.395 (Aug18) = +14%.

**Thứ tự:**
- **CROWD (gLSR) BẬT TRƯỚC** — leo mạnh Aug08-Aug11 (từ 3.686→4.322 = +17% trong 3d)
- **POS (top-trader) BẬT SAU** — Aug11-Aug18 (từ 1.223→1.395 = +14% trong 7d)

**→ Pattern: CROWD-CHASE dẫn, TOP-TRADER theo sau.** Đúng khuôn CROWD-CHASE-EARLY (phase_tag máy chấm S2-EARLY — xem §B6). Crowd chạy trước tin, top trader tăng position theo sau.

---

## §B4. CHÂN HÀNG — Perp vs Alpha

**SPOT api/v3:** KHÔNG có TRIA base pair. Alpha-only listing.

**Alpha vol 5d gần nhất (bapi klines):**
| date | close | vol_usd |
|------|-------|---------|
| 2026-08-14 | 0.00819 | **$9,797** |
| 2026-08-15 | 0.00846 | $5,786 |
| 2026-08-16 | 0.00842 | $30,416 |
| 2026-08-17 | 0.00826 | $7,683 |
| **2026-08-18** | **0.00981** | **$770,626** ← spike ~100× nền |
| 2026-08-19 (in-progress) | 0.01038 | $416,433 |

**Nền T7 Alpha vol** (Aug11-Aug17 median): ~$7-10K/day  
**Aug18 Alpha vol** = **$770,626** → **~85× nền T7**  
**Perp vol Aug18** = **$25,063,774** → **~10× nền T7 perp** ($2-4M/day)

**Perp/Alpha ratio Aug18:** $25M / $770K = **~32:1** → cú +17.94% Aug18 chạy CHÍNH TRÊN PERP, Alpha đóng góp trace nhưng cũng ignite hơn 85× nền. Băng-thông xả chân spot (Alpha) hẹp — 100% vol ≥$100K/ngày sẽ móc Alpha rất nhanh.

---

## §B5. INTRADAY 19/08 [UNVERIFIED — TÁCH RIÊNG]

**Snapshot:** 2026-08-19 **03:12 UTC**

| Metric | Value | vs 18/08 close |
|--------|-------|----------------|
| Price (last) | **$0.010304** | vs Aug18 close $0.00975 = **+5.7%** (extra move); vs open 24h $0.008256 = **+24.81%** |
| OI (token) | 691,433,197 | vs Aug18 close 324,000,000-ish tokens (implied from 3.16M÷0.00975) ≈ **~+114%** |
| **OI (USD)** | **$7,124,528** | vs Aug18 close $3,162,835 = **+$3,961,693 (+125.3%)** |
| Vol 24h | **$51,264,131** | vs Aug18 daily $25.06M ≈ **~2× ngày Aug18** (24h rolling) |
| Funding kỳ 04:00 UTC (Aug18) | +0.00005 | vẫn pin |
| Funding kỳ 08:00 UTC (Aug18) | (chưa fetch — probe show 16/20/00) | |
| Funding kỳ 16:00 UTC (Aug18) | +0.00005 | pin |
| Funding kỳ 20:00 UTC (Aug18) | +0.00005 | pin |
| **Funding kỳ 00:00 UTC (Aug19)** | **-0.00010496** | **UN-PIN + FLIP ÂM (-10.5bps)** ← đứt chuỗi pin 30-ngày |

**Đọc:**
- **B2 LONG-BUILD MASSIVE INTRADAY** — OI +125% USD trong ~14h (khớp mẫu CLO 18/08).
- Funding **UN-PIN + ÂM** — pin 30-ngày đứt đúng lúc pump. Shorts đang trả phí cho longs.
- OI +125% đi cùng price +24.8% = **long build mới**, KHÔNG phải short cover. Cover phải là pos_r ↑ + OI ↓.
- fapi topPos Aug19 = 1.0613 (từ 1.395 Aug18) — nếu số đúng, top-trader SẼ ĐANG REDUCE net-long position (đóng long) trong khi crowd/OI leo. Có thể là top-trader đang **BÁN VÀO** pump (không phải short cover, mà là long-take-profit).

---

## §B6. ĐỐI CHIẾU BA MÁY (18/08)

### Watchlist_log CSV — dòng TRIA (VPS: `/root/Data_back_test/whale_data/data/export/watchlist_log_2026-08.csv`)

**LATEST run_date = 2026-08-17.** Aug18 row **KHÔNG có trong CSV** (cron cuối chạy Aug19 01:00 UTC nhưng chưa có Aug18 rows — có thể cron chưa process xong, hoặc TRIA đã bị drop khỏi list. **Cần operator verify: `tail /root/Data_back_test/whale_data/data/export/watchlist_cron.log` xem run Aug19 01:00 lỗi gì**).

**Aug17 rows TRIA (2 dòng — cả list A + B) — nguyên văn:**
```
2026-08-17,TRIAUSDT,A,0.3313,0.2990,+0.0323,14,1,2026-08-04,0.008398,0.008394,-0.05,BẬT,PHẲNG,,+0.0050
2026-08-17,TRIAUSDT,B,0.3313,0.2990,+0.0323,14,1,2026-08-04,0.008398,0.008394,-0.05,BẬT,PHẲNG,,+0.0050
```

**Header (parse):**
```
run_date | symbol | list | div_ratio | div_5d_ago | div_delta | struct_n | episode_id 
| hedge_start_date | hedge_start_px | px_now | px_dist_pct | pos_trend | oi_trend | oi_note | funding_pct
```

| Field | Aug17 value | Đọc |
|-------|-------------|-----|
| list | A + B (cả hai) | Trên cả hai watchlist |
| div_ratio | 0.3313 | dưới 0.5, còn trong episode |
| div_5d_ago | 0.2990 | div đang leo (nới) |
| div_delta | +0.0323 | positive delta = nới |
| struct_n | 14 | 14 ngày trong episode |
| hedge_start_date | **2026-08-04** | ✓ khớp task/probe |
| hedge_start_px | 0.008398 | ✓ khớp |
| px_now | 0.008394 | Aug17 close |
| px_dist_pct | -0.05% | chưa đi đâu vs entry |
| pos_trend | BẬT | pos_r rerating (Aug15-Aug17) |
| oi_trend | PHẲNG | OI ngang, không cover mạnh |
| oi_note | (empty) | không xả cụ thể |
| funding_pct | +0.0050 | +0.5% cumulative daily (pin band) |

### Phase_tag_daily.csv — **⚠ P0 BUG CÒN SỐNG**

**`phase_tag_daily.csv` KHÔNG tồn tại** trên VPS. Sau `[PHASE-TAG-GOLIVE-CRON-20260818]` commit đã activate cron 01:30 UTC — cron chạy được (log có nội dung), NHƯNG chỉ output TEXT vào `.log` + Telegram, không sinh CSV.

**Trong phase_tag.log (VPS `/root/Data_back_test/whale_data/data/logs/phase_tag.log` tail):**
```
TRIA  CROWD-CHASE  stage-hôm-nay=S2-EARLY
```

**→ Máy chấm:** TRIA = **CROWD-CHASE**, stage = **S2-EARLY**  
(khớp §B3(d) đọc thứ tự crowd-lead-then-pos)

**⚠ ALERT:** Không có CSV để cross-reference program-mable. Bug P0 từ án CLO 18/08 CÒN SỐNG. Cần bổ sung `run_phase_tag.py` write CSV alongside log/Telegram.

---

## §C. TỔNG KẾT

| Signal | Value | Đọc |
|--------|-------|-----|
| Episode | #1 start Aug04, struct_n=15, min div 0.292 @ Aug14 | ONGOING, hedge vẫn còn |
| px_dist% | +18.3% (Aug18) / +22.75% (intraday Aug19) | Đã leo trên hedge_start, chưa flush |
| pos_r trend | +14% (Aug11→Aug18) slow-drip, chưa 🔵15%/2d | Cover chậm, không one-shot |
| OI cover | -3.3% Aug17→Aug18, tank shorts còn nguyên | Chưa vào phase un-hedge cover đúng nghĩa |
| Funding pin | 30 ngày pin liên tục (f_avg=5e-5) | Committed captive rất chặt |
| Funding intraday Aug19 00:00 | **-10.5bps FLIP ÂM** | **UN-PIN đứt** — regime break |
| gLSR crowd | +27% Aug08→Aug14 (crowd leo TRƯỚC pos) | CROWD-CHASE dẫn |
| Intraday Aug19 | +24.8% px, +125% OI USD, vol $51M | **B2 LONG-BUILD MASSIVE**, không phải cover |
| Alpha vol Aug18 | $770K = 85× nền T7 | Chân Alpha bắt đầu ignite (nhưng vẫn nhỏ vs perp $25M) |
| Machine tags | phase_tag=CROWD-CHASE·S2-EARLY, watchlist=BẬT/PHẲNG (Aug17) | Consistent với daily readout |

**Rủi ro / falsifier chưa xong:**
- Un-hedge THẬT: pos_r bật ≥15%/2d + OI ↓ + div break 0.5 (chưa xảy ra Aug18)
- Distribution wall: top-trader pos_r sụt (fapi Aug19 1.06 vs Aug18 1.40 nếu tin cậy)
- Continuation: OI leo tiếp + funding âm tiếp + Alpha vol leo tiếp

**KHÔNG VERDICT.** Số về, ANALYSIS đọc.

---

## §D. FILE LIST + NGUỒN

| Artifact | Path |
|----------|------|
| Probe | `_probe_tria_20260819.py` (local, sẽ commit) |
| Report | `docs/reports/_tria_probe_20260819.md` (file này) |
| Watchlist CSV nguồn | VPS `/root/Data_back_test/whale_data/data/export/watchlist_log_2026-08.csv` |
| Phase_tag output | VPS `/root/Data_back_test/whale_data/data/logs/phase_tag.log` (⚠ không có CSV) |

**Nguồn số:**
- Perp/funding: `fapi/v1/{klines,fundingRate}` symbol=TRIAUSDT (30 days Jul20-Aug18)
- OI: `fapi/v1/futures/data/openInterestHist` (dedup ((date,ts)), 30/30 unique)
- LSR: `data/export/freshwatch_daily_2026-{05,06,07,08}.csv` (81 TRIA rows May26-Aug17) + fapi 4 endpoint fallback (topPos, topAcc, global) for Aug18
- Intraday: `fapi/v1/{ticker/24hr, openInterest, fundingRate}` snapshot 2026-08-19 03:12 UTC
- Alpha meta: `bapi/defi/v1/public/wallet-direct/buw/wallet/cex/alpha/all/token/list` (ALPHA_669)
- Alpha klines: `bapi/defi/v1/public/alpha-trade/klines?symbol=ALPHA_669USDT`
- Spot verify: `fapi/v1/exchangeInfo` (local, TRIA base = 0 matches — Alpha-only confirmed)
- Watchlist cross-check: VPS `watchlist_log_2026-08.csv` via SSH

**DỪNG sau paste.** KHÔNG verdict. KHÔNG đụng CASE file. KHÔNG mở topic mới.
