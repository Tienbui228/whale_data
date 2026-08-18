# CLO REFRESH + UN-HEDGE READOUT — 18/08/2026
**Target:** `docs/case_files/CASE_CLO.xlsx` (schema v1, 41 cols, `lsr_pos_r` prefix)  
**Window:** 2026-07-01 → 2026-08-17 (nến đóng D-1) + intraday 18/08 riêng  
**Backup L-37:** `scratch/CASE_CLO_bak_pre_refresh_20260818.xlsx` (28,055 B) ✓  
**Probes:** `_task_clo_b0..b7_20260818.py` (root, sẽ archive sau)

**Data provenance (L-48):**
- `data-source`: fapi.binance.com (perp klines/funding/OI/LSR — top+global endpoints), bapi/defi/v1 (Alpha meta), api.binance.com (spot verify via VPS)
- `machine`: local Windows scratch + VPS 5.223.67.21 (spot check)
- `date-range`: DAILY window 2026-08-04 → 2026-08-17 (append 14 days); intraday snapshot 2026-08-18 13:50 UTC
- `code-commit`: sẽ commit sau paste

**Layer coverage:** I (Perp) · II (Crowd-LSR, top + global) · III (chưa on-chain) · IV (Funding) · V (Spot/Alpha — Alpha-only, no spot) · VI (chưa) · VII (chưa)

---

## §A. TICKER + LISTING STRUCTURE (B5)

| Metric | Value | Note |
|--------|-------|------|
| PERP fapi | **CLOUSDT** TRADING (onboard 2025-10-14) | Full LSR endpoints available |
| Alpha bapi | **ALPHA_429** "Yei Finance", fullyDelisted=False, offline=False | BSC contract chưa lấy |
| Binance SPOT api/v3 | **KHÔNG có** (VPS check: 3681 total symbols, 0 base=CLO exact, 0 base=YEI) | CLOAKBTC/CLOAKETH ≠ CLO |
| Verdict | **Alpha-only + Perp** — KHÔNG có spot CEX pair | taker_spot_pct = **ABSTAIN-STRUCTURAL** (L-51 draft) |

**Note L-51 draft:** áp cho tất cả token Alpha-only (không có api/v3 spot) — cùng luật với GUA án sáng nay. Vol_alpha bapi tin cậy được (endpoint klines trả OHLCV OK), TAKER Alpha vẫn broken (k[9]≡k[5], k[10]≡k[7] mirror). Không ghi Alpha vol vào `vol_spot_usd` — chỉ ghi vào `vol_alpha` (khi có cột).

---

## §B1. PERP APPEND Aug04→Aug17 (14 rows mới, xlsx row 73-86)

Fetched from `fapi/v1/klines` + `fapi/v1/fundingRate` (interval verify: **4h × 6/day** cả 14 days ✓ L-41) + `fapi/v1/futures/data/openInterestHist` (dedup key = (date, timestamp), 30/30 unique ✓).

**Cell writes:** 717 total.

---

## §B2. LSR CHECK + REPAIR

**Existing rows (Apr01-Aug03):** lsr_pos_r null = 17/70 (24.3%) — không phải toàn null như GUA. Không repair pre-Aug04 rows (chưa có yêu cầu, giữ nguyên trạng thái).

**New rows Aug04-Aug17:** LSR filled từ freshwatch data/export/ (67 CLO rows Jun05→Aug17) — 14/14 rows đầy đủ pos_r + acc_r + global_r.

**Recomputed derived cols cho new rows:** div_raw, div_avg3, glsr_slope_5d, d_pos_3d, d_acc_3d, oi_cycle_pos, oi_vs_med14, pin_streak.

**Note:** Schema CLO v1 KHÔNG có flag_neg_div / flag_hedge_struct / flag_knife_crowd cols (khác GUA v2 schema). Nếu operator muốn nâng v2, cần task riêng.

---

## §B3. UN-HEDGE READOUT — bảng riêng 10/08 → 17/08

| date | px | ret% | oi_usd | Δoi_1d | f_avg | fn | pin | pos_r | acc_r | gLSR | div_raw | takerBUY% |
|------|-----|------|--------|--------|-------|-----|-----|-------|-------|------|---------|-----------|
| 08-08 | 0.12284 | +0.55 | 4,435,028 | -22,397 | 0.000229 | 6 | 0 | 0.860 | 2.374 | 2.402 | 0.362 | 50.88 |
| 08-09 | 0.12481 | +1.60 | 4,533,614 | +98,586 | 0.000437 | 6 | 0 | 0.853 | 2.476 | 2.524 | 0.344 | 49.70 |
| **08-10** | **0.10663** | **-14.57** | **4,504,549** | **-29,065** | 0.000431 | 6 | 0 | 0.851 | 2.530 | 2.630 | 0.337 | 47.24 |
| **08-11** | **0.11481** | **+7.67** | **4,074,995** | **-429,554** | 0.000322 | 6 | 0 | **0.913** | 2.215 | 2.056 | 0.412 | 48.75 |
| 08-12 | 0.11672 | +1.66 | **4,911,632** | **+836,637** | 0.000392 | 6 | 0 | **0.939** | 1.807 | 1.637 | **0.520** | 48.38 |
| 08-13 | 0.11405 | -2.28 | 4,449,205 | -462,427 | 0.000346 | 6 | 0 | 0.985 | 2.244 | 2.028 | 0.439 | 47.99 |
| 08-14 | 0.11586 | +1.59 | 4,145,527 | -303,678 | 0.000489 | 6 | 0 | **1.024** | 2.417 | 2.179 | 0.424 | 47.70 |
| 08-15 | 0.11602 | +0.14 | 4,047,338 | -98,189 | 0.000446 | 6 | 0 | **1.028** | 2.642 | 2.383 | 0.389 | 46.60 |
| 08-16 | 0.11635 | +0.28 | 4,040,788 | -6,550 | 0.000325 | 6 | 0 | 0.973 | 2.759 | 2.588 | 0.352 | 47.86 |
| **08-17** | **0.11702** | **+0.58** | **3,952,578** | **-88,210** | 0.000407 | 6 | 0 | **1.002** | 2.717 | 2.617 | 0.369 | 47.39 |

*(px = px_avg (H+L+C)/3; Δoi_1d = oi_usd(t) - oi_usd(t-1))*

### (a) B1 SHORT-COVER tell: pos_r ↑ ≥15%/1-2d ∧ OI ↓?

**KHÔNG đạt threshold ≥15% trong toàn window Aug10-17.**

- Ngày gần nhất kiểu cover: **Aug10→Aug11 (1d)**
  - pos_r: 0.851 → **0.913** = **+7.3%** (dưới threshold 15%)
  - OI: 4,504,549 → **4,074,995** = **-9.5%**
  - → Pattern cover đúng chiều (pos_r↑, OI↓) nhưng magnitude nhỏ. Không phải "un-hedge one-shot" như ON 17/07 (+30%/1d).

- 2-day: **Aug09→Aug11:** pos_r +7.0% (0.853→0.913), OI -10.1% (4.53M→4.07M). Vẫn dưới 15%.

**Verdict:** Không có B1 SHORT-COVER classical trong Aug10-17. Cover Aug11 = **micro-cover** (10% OI unwound, 7% pos_r rerate).

### (b) B2 LONG-MỚI: pos_r ↑ ∧ OI ↑?

**CÓ — 1 nhịp rõ Aug11→Aug12:**
- pos_r: 0.913 → **0.939** (+2.8%)
- OI: 4,074,995 → **4,911,632** (+**20.5%**)
- → LONG BUILD medium sau khi Aug11 unwind. Kho perp rebuild ngay 1 ngày.

**Aug13-15 (3d):** pos_r 0.985 → 1.024 → 1.028 (**cross 1.0 tại Aug14**), OI đi ngang→giảm nhẹ. → **pos rerate mà OI KHÔNG build** = crowd position increase nhưng size không nở → hoặc là short unwind tinh, hoặc là long-build từng người nhỏ.

**Aug17→Aug18 (intraday, tách):** pos_r Aug17 = 1.002, OI Aug17 = 3.95M USD. Intraday Aug18 13:50 UTC: **OI = 6.27M USD (+58.8%)** — LONG BUILD MASSIVE trong 14h. → xem §B4.

**Phân biệt B1 vs B2 (câu tường minh):**
- Aug10-11: pattern B1 (cover) — magnitude nhỏ
- Aug11-12 + Aug17-Aug18: pattern B2 (long build mới) — Aug18 magnitude LỚN

### (c) Funding regime + pin?

**Trong Aug04-Aug17:** **KHÔNG có pin day nào** (f_avg 0.000229 → 0.000507, tất cả WARM regime, đều > pin band [4e-5, 6e-5]).

**Historical (pre-Aug04):** PINNED status tồn tại tại Jul30 (row 68, f_avg 5e-5) — pin regime chấm dứt từ Aug01 khi f_avg lên WARM.

**Burst ≥15bps?**
- Aug09 f_max = **0.00122** (~12.2 bps) — gần threshold nhưng không đạt
- Aug10 f_max = **0.00137** (~13.7 bps, cao nhất window) — vẫn dưới 15bps
- Aug14 f_max = 0.00096 (~9.6 bps)
- **KHÔNG có burst ≥15bps trong window.** Chỉ có f_max cao Aug09-10 (~12-14bps) đi cùng dump.

**Intraday Aug18 funding:** 04:00=0.00064 · 08:00=0.00033 · 12:00=**0.00077** (~7.7bps, đang tăng trong pump nhưng chưa đến 15bps burst).

### (d) div_raw chuỗi 10-17/08 — hedge_struct (≤0.5) đang tháo?

```
08-10: 0.337 (thấp, hedge tight)
08-11: 0.412 (leo)
08-12: 0.520 ← VƯỢT 0.5 (hedge tháo 1 ngày)
08-13: 0.439
08-14: 0.424
08-15: 0.389
08-16: 0.352
08-17: 0.369
```

**Verdict:** hedge **tháo 1 nhịp Aug12** (div_raw chạm 0.52), sau đó **build lại về 0.37** — hedge structure vẫn còn (div ≤ 0.5 = hedged-waiting posture). Không có xu hướng leo bền vững = **chưa un-hedge full**. Vẫn hedged-waiting tư thế (VIII.3 khuôn div<1 đọc funding).

---

## §B4. INTRADAY 18/08 [UNVERIFIED — TÁCH RIÊNG, không trộn DAILY]

**Snapshot:** 2026-08-18 **13:50 UTC**

| Metric | Value | vs 17/08 close |
|--------|-------|----------------|
| Price (last) | **$0.14754** | vs open 24h $0.11604 = **+27.15%** |
| OI (token) | 42,504,307 | vs Aug17 close 34,071,014 = **+24.7%** |
| OI (USD, calc = OI_tok × px) | **$6,271,085** | vs Aug17 close $3,952,578 = **+58.7%** |
| Vol 24h | **$44,022,136** | vs Aug17 daily $925,637 = **~47× ngày trước** |
| Funding kỳ 04:00 UTC | +0.00063953 (~6.4 bps) | tăng vs Aug17 avg 0.00041 |
| Funding kỳ 08:00 UTC | +0.00033400 (~3.3 bps) | |
| Funding kỳ 12:00 UTC | +0.00077267 (~7.7 bps) | rising during pump |

**Đọc intraday:**
- **B2 LONG-BUILD MASSIVE trong 14h** (OI +58.7% USD). Không phải cover — vì OI TĂNG chứ không giảm.
- Vol ~47× ngày Aug17 = crowd tham gia dày (không phải MM lẻ).
- Funding rising nhưng chưa burst ≥15bps → chưa quá overheated. 
- pos_r hiện tại chưa có (endpoint LSR chỉ update 1×/day). Giá trị Aug17=1.002 → có thể đã leo cao hơn intraday.

**KHÔNG ghi vào DAILY sheet** (chưa đóng nến). Chỉ ghi 1 dòng EVENTS `PUMP_INTRADAY_18` (§B7).

---

## §B5. SPOT/ALPHA (đã trả lời trong §A)

**Kết luận:**
- CLO = Alpha-only listing (Yei Finance, ALPHA_429). BSC contract.
- Không có Binance spot pair (api/v3 exchangeInfo trả 0 match). 
- taker_spot_pct = **ABSTAIN-STRUCTURAL** (không data-gap, không trigger guard).

**Vol chân spot/alpha 3 ngày gần nhất vs nền T7:**
- Aug15-Aug17 (bapi Alpha klines đã fetch trong probe): Alpha vol Aug15 = ?, Aug16 = ?, Aug17 = ? — **CHƯA fetch riêng trong task này** (spot cols của CLO v1 đang trống, không có vol_alpha col). Cần task phụ nếu muốn Alpha vol chuỗi.
- **Note:** Vol perp Aug17 = $926K. Vol Alpha (nếu Yei-Finance vol/24h < 1M) → thanh khoản spot < perp = TYPICAL Alpha-only pattern. Băng-thông xả spot rất hẹp.

**Doctrine #10 draft (kho/băng-thông) — chưa có số:** cần Alpha vol T7 baseline. Bỏ cho task riêng.

---

## §B6. PHASE-TAG CROSS-CHECK — **⚠ BUG GO-LIVE**

**Tìm kiếm `phase_tag_daily.csv`:**
- **Local (Windows):** 0 candidates via rglob toàn cây
- **VPS (5.223.67.21):** 0 file matching `phase_tag*.csv` trong `/root/Data_back_test/whale_data/`
- VPS chỉ có: `scanner/phase_tag.py` (code file, không phải output)
- data/ folder VPS: `gom_h_daily.csv` (Aug15), `gom_h2prime_daily.csv` (Aug18), `gom_heartbeat.txt` — **KHÔNG có phase_tag output**

**⚠ ALERT OPERATOR:** phase_tag cron **CHƯA sinh output CSV** — bug go-live PHASE-TAG-v0.3.3 (per commit 20de185). Có thể:
1. Cron chạy nhưng dedup-fail hoặc guard-fail → không write CSV
2. Script viết vào path khác (chưa tìm ra)
3. Cron chưa được enable trên VPS

**KHÔNG thể đối chiếu CLO stage/flags/event_tag/state_conflict từ phase-tag CSV.** Bug cần fix trước khi kiểm tra state-conflict.

**Đề nghị:** operator check `crontab -l` trên VPS + log phase-tag chạy 18/08.

---

## §B7. EVENTS APPEND

Appended 6 rows vào `EVENTS` sheet (rows 27-32):

| row | ngay | su_kien | nguon | doc_nhanh |
|-----|------|---------|-------|-----------|
| 27 | 08-08 | funding cool: f_avg 0.000229 vs 0.000466 avg trước = warmdown | fapi funding | warmdown |
| 28 | 08-10 | **CRASH -14.57%**, vol 10.6M spike, OI stable 4.5M (crowd flushed nhưng perp size unchanged) | fapi klines+OI | flush_wave1 |
| 29 | 08-11 | **REBOUND +7.67%**, vol 16.1M biggest day, OI -9.5% to 4.07M, pos_r 0.851→0.913 (SHORT-COVER partial) | fapi klines+LSR | cover_wave1 |
| 30 | 08-12 | pos_r 0.939 leo, OI 4.91M rebuild, div_raw 0.520 CHẠM 0.5 (hedge tháo tạm) | fapi+LSR | hedge_untap_wave1 |
| 31 | 08-14 | pos_r **CROSS 1.0** (0.985→1.024), gLSR 2.18 leo, div_raw 0.424 rơi lại (re-hedge) | fapi LSR | pos_r_cross_1 |
| 32 | 08-18 | **INTRADAY PUMP +27.15%** (0.11604→0.14754 @13:50 UTC), OI 3.95M→6.27M (+58.8%), vol 24h $44M | fapi ticker+OI intraday | PUMP_INTRADAY_18 |

---

## §C. TỔNG KẾT SỐ

| Signal | Value | Đọc |
|--------|-------|-----|
| B1 SHORT-COVER | Aug11 pos_r +7.3%, OI -9.5% — dưới threshold 15%/1-2d | Cover micro, không phải un-hedge one-shot |
| B2 LONG-BUILD | Aug11-12 (+20.5% OI) · Aug17-18 intraday (+58.7% OI) | Aug18 MASSIVE — cần theo dõi kỳ funding kế |
| pos_r trend | 0.826 → 1.028 (Aug15 peak) → 1.002 Aug17 | Đã cross 1.0, crowd position rerate |
| gLSR trend | 2.636 → 1.637 (Aug12 trough) → 2.617 Aug17 | Rũ 1 nhịp rồi bò lại full |
| Funding regime | WARM suốt · KHÔNG pin · KHÔNG burst ≥15bps | Committed-long chịu chi phí |
| div_raw window | 0.337 → 0.520 (Aug12 peak) → 0.369 Aug17 | Hedge tháo 1 ngày rồi build lại, chưa un-hedge full |
| Intraday Aug18 | +27% price, +58.7% OI USD, vol $44M (47× ngày) | LONG-BUILD chân dày — cú đẩy đang chạy |
| Alpha status | ALIVE (Yei Finance, ALPHA_429) | Alpha-only + Perp, no spot api/v3 |
| PHASE-TAG check | ⚠ **NO output CSV trên VPS** | Bug go-live phase-tag — cần fix |

**Rủi ro / falsifier:**
- Xả tell: pos_r sập <1.0 sau intraday + OI rơi + funding âm burst
- Bull tell: pos_r phá 1.10 + OI tiếp tục leo + funding burst ≥15bps (chưa xảy ra)

**KHÔNG VERDICT.** Số về, ANALYSIS đọc.

---

## §D. FILE LIST + NGUỒN

| Artifact | Path | Nội dung |
|----------|------|---------|
| Backup pre-refresh | `scratch/CASE_CLO_bak_pre_refresh_20260818.xlsx` | 28,055 B |
| Updated CASE | `docs/case_files/CASE_CLO.xlsx` | DAILY 84 rows (added 14 Aug04-17), EVENTS +6, ~717 cell writes |
| Scratch Aug04-17 fetch | `scratch/clo_{perp,funding,oi_hist,lsr_raw}_*_20260818.csv` | fapi raw + canonical LSR |
| Report | `docs/reports/_clo_unhedge_20260818.md` | File này |
| Probes | `_task_clo_b0..b7_20260818.py` (5 files) + `_probe_clo_b5_vps_20260818.py` | Sẽ archive sau commit |

**Nguồn số chi tiết:**
- Perp/funding Aug04-17: `fapi/v1/{klines,fundingRate}` symbol=CLOUSDT
- OI Aug04-17: `fapi/v1/futures/data/openInterestHist` (dedup key=(date,timestamp))
- LSR Aug04-17: `data/export/freshwatch_daily_2026-{06,07,08}.csv` (67 CLO rows Jun05-Aug17). Fallback fapi: `topLongShortPositionRatio` + `topLongShortAccountRatio` + `globalLongShortAccountRatio`
- Intraday: `fapi/v1/{ticker/24hr,openInterest,fundingRate}` snapshot 13:50 UTC
- Alpha meta: `bapi/defi/v1/public/wallet-direct/buw/wallet/cex/alpha/all/token/list`
- Spot api/v3 verify: `api.binance.com/api/v3/exchangeInfo` **via VPS 5.223.67.21** (geo restrict local)

**DỪNG sau paste.**
