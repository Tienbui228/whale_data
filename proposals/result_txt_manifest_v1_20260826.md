# _result.txt COLUMN MANIFEST v1 — CANONICAL (⑬ ký 26/08/2026)

**Status:** SIGNED — nguồn canonical duy nhất cho _result.txt.
**Operator ký chat 26/08 ⑬.**
**Companion:** ⑩-AMENDMENT `41d8d717` + R4-v2 regen `b400b5fc` + backfill Scope A `fa4e259`.
**Draft source:** chat (a) 24/08 bảng manifest + 3 sửa ký + ANALYSIS input (file not yet in proposals/ tại thời điểm soạn — merge sau nếu có).

---

## Luật nền (⑬ hiệu lực)

1. **REGEN** = cột chuẩn hóa từ store canonical, ghi mới vào _result.txt (một lượt, một changelog).
2. **VERIFY-THEN-KEEP** = diff cột hiện tại vs canonical trong retention; sạch (diff nhỏ) → giữ + note verified-ngày; lệch → regen cột đó.
3. **DEPRECATE-RENAME** = đổi header nhưng GIỮ vị trí cột + bytes; replay.py parse positional nên không ảnh hưởng; assertion là "không signal đọc header rename".
4. **N/A-BLOCK** = file không có block đó (e.g. `ake_result.txt` không có RATIO/KLINES block delimiter).

---

## MANIFEST v1

### Block: (top of file, funding raw 3-col)

| col | verdict | nguồn hiện tại _result.txt | store canonical | consumer signals | canonical đề xuất |
|---|---|---|---|---|---|
| `funding_avg` | **VERIFY-THEN-KEEP** | curated 28/07 `b0b4cff4` | `funding_8h/month=YYYY-MM/` col `funding_rate` aggregated → daily avg per (symbol, date) | funding_pinned (B2) · funding_neg_div (B4/SUPP) · funding_extreme (SUPP) · c2_quiet (GOM-C) | store funding_8h agg daily avg |
| `funding_min` | **VERIFY-THEN-KEEP** | curated 28/07 | store funding_8h min per day (min of interval settlements) | display + funding_pinned band | store min per day |
| `funding_max` | **VERIFY-THEN-KEEP** | curated 28/07 | store funding_8h max per day (max of interval settlements) | display + funding_pinned band | store max per day |
| `funding_n` (implicit — số kỳ/ngày) | **AMENDMENT-⑬-FN-EXPLICIT** | không xuất trong _result.txt | count settlements per (symbol, date) | funding_pinned bands (implicit assumption 6 = 4h interval canonical, 3 = 8h, 24 = 1h) | **Công thức tường minh:** `funding_n = count(funding_settlements where date=D)`, canonical 8h → 3/day, 4h → 6/day, 1h → 24/day. Kiểm 8h interval per symbol via funding_intervals.json cache. **Nếu funding_n mismatch expected interval → suspect** (đã có `funding_settlement_count_mismatch` log warning tại `export_freshwatch_daily.py` — ví dụ ONGUSDT actual=24 expected=6 interval_h=4). |

### Block: `--- OI <TOKEN>USDT ---`

| col | verdict | nguồn hiện tại | store canonical | consumer signals | canonical đề xuất |
|---|---|---|---|---|---|
| `OI_end_usd` | **VERIFY-THEN-KEEP** | curated 28/07 (endpoint TBD, likely `/futures/data/openInterestHist` field `sumOpenInterestValue`) | `oi_hist_1d/date=YYYY-MM-DD/` col `sum_open_interest_value` | oi_ignition (A2 aux, display) · A5 oi_cycle_pos (rolling 30d) · breakout_oi_5d · A1 lsr_accum via _median14 · crowd_flush cause | store `oi_hist_1d.sum_open_interest_value` |

### Block: `--- RATIO <TOKEN>USDT ---`

| col | verdict | nguồn hiện tại | store canonical | consumer signals | canonical đề xuất |
|---|---|---|---|---|---|
| `topLSR_pos` (→ DayData.`lsr_pos`) | ✓ CANONICAL (R4-v1) | R4-v1 regen từ store `top_pos_1d` (bot-signals commit `b400b5fc`) | `top_pos_1d.long_short_ratio` | hedge_structure (B1) via _div_ratio · pos_rerate (A4) · lsr_dist (SUPP) · lsr_accum (A1) | store `top_pos_1d.long_short_ratio` |
| `topLSR_acc` (→ `lsr_acc`) | ✓ CANONICAL (R4-v1) | R4-v1 regen từ store `top_acct_1d` | `top_acct_1d.long_short_ratio` | _div_ratio (B1/A1) · lsr_dist · lsr_accum | store `top_acct_1d.long_short_ratio` |
| `globalLSR` (→ `lsr_global`) | ✓ CANONICAL (R4-v1) | R4-v1 regen từ store `retail_global_1d` | `retail_global_1d.long_short_ratio` | A2 avg5(lsr_global) · lsr_accum companion · A3 _a3_slope · crowd_flush cause | store `retail_global_1d.long_short_ratio` |
| `takerRatio` header | **DEPRECATE-RENAME** | R4-v1 regen từ store `taker_ratio_1d.buy_sell_ratio` | `taker_ratio_1d.buy_sell_ratio` (fapi `takerlongshortRatio`, ratio-of-position-counts — khác `taker_buy_pct` k[10]/k[7] ratio-of-quote-vols) | **KHÔNG signal đọc trực tiếp** (verified grep — signals đọc `taker_buy_pct` từ KLINES, không đọc `taker_ratio` từ RATIO block) | **RENAME header** cột 5 RATIO block: `takerRatio` → `taker_ratio_endpoint_legacy`. **GIỮ vị trí cột 5 + bytes** (replay.py parse positional line 111-114: `taker_ratio=_parse_num(parts[4])`). **Assertion:** grep không signal đọc header string — pass (đã verified). Purpose rename: phân biệt rõ với canonical taker_buy_pct k[10]/k[7]. |

### Block: `--- KLINES <TOKEN>USDT ---`

| col | verdict | nguồn hiện tại | store canonical | consumer signals | canonical đề xuất |
|---|---|---|---|---|---|
| `avg_px` | **REGEN** (⑬ mở scope) | curated 28/07 `b0b4cff4` READ-ONLY (ngoài scope ⑩) | `klines_1h/date=YYYY-MM-DD/` daily agg: `VWAP = sum(quote_volume) / sum(base_volume)` | absorption (B3 `px_range` ≤10%) signals.py:526 · dist_wall (SUPP `px cumulative` ≤-10%) · crowd_flush (bait cause pri drop 8%+ hoặc rally 8%+) · post_climax (SUPP crash 25%+ 14d) · A6 price_slope_guard | store klines_1h VWAP daily agg (`k[7]/k[5]` weighted) |
| `perp_vol$` (→ `vol_quote`) | **REGEN** (⑬ chuẩn hóa) | curated 28/07 | `klines_1h.quote_volume` daily sum (= k[7] sum) | crowd_flush (bait vol 8× med14) · stealth_grind C1 (vol ≥1.3× med14) · absorption (indirect via px_range calc share) | **REGEN từ store k[7]** với fallback = "store post-F5a guard-verified" (F5a-VOL-REBUILD-20260824 canonical vol_source=`fapi_k7_fresh_20260824`; sẵn dùng, verified) |
| `takerBUY%` (→ `taker_buy_pct`) | ✓ CANONICAL (R4-v2 + collector migrate) | R4-v2 regen từ store `klines_1h` k[10]/k[7] canonical (bot-signals `b400b5fc`); collector migrate deploy 25/08 UTC | `klines_1h`: `taker_buy_quote_vol / quote_volume` daily agg (= k[10]/k[7]) | absorption (B3 [44,53]% signals.py:520) · dist_wall (SUPP ≥50%) · decay (SUPP <48%) · C1 stealth_grind (taker_buy_max=55) · phase_tag _window(5, 'taker_buy_pct') | store `klines_1h k[10]/k[7]` (ĐÃ canonical R4-v2 + migrate 25/08) |
| `o/h/l/c` (optional cols) | **REGEN** nếu có | curated 28/07 (some files) | `klines_1h`: aggregate open (first)/high (max)/low (min)/close (last) per day | Không direct signal consumer (chỉ auditing/CASE display) | store `klines_1h` OHLC daily agg standard |

---

## AKE = N/A-BLOCK

`ake_result.txt` không có RATIO/KLINES block delimiters (`--- RATIO AKEUSDT ---`, `--- KLINES AKEUSDT ---`). File chỉ có funding raw + OI. REGEN skipped cho tất cả KLINES/RATIO cols. Coverage-note trong changelog: "AKE 11/12 REGEN scope; funding/OI VERIFY-THEN-KEEP nếu block tồn tại; assertion Row 13 SUPP checker không đọc LSR/taker → 0 impact."

---

## Amendment absorption basis (⑬ điều kiện i) — 1 dòng verbatim

**Vào `binance-bot-signals/docs/gom_detect_spec.md` §GOM-B row B3 (companion commit):**

> **[⑬-COLUMN-MANIFEST-BASIS-20260826]** absorption() reads BOTH `taker_buy_pct` (k[10]/k[7]) AND `avg_px` (VWAP k[7]/k[5]) — cả 2 fields cùng basis store klines_1h; mixed basis (curated vs canonical) gây B3 flip do px_range check.

---

## Điều kiện (ii) — BULLA 07-05 chấm lại trên canonical (neutral hai chiều)

Post-regen manifest deploy, BULLA 07-05 expected chấm lại trên INPUT CANONICAL:

- Input canonical: `avg_px` k[7]/k[5] VWAP + `taker_buy_pct` k[10]/k[7] + LSR store canonical
- **Expected = số CANONICAL tính ra** (không pre-set từ K4 probe `4fd5ae4` cũ dùng bulla_result pre-regen)
- **B-truth 04→15/07 rebuild** với B1/B2/B3/B4 canonical, pin per-day HBS mới
- **Neutral hai chiều:**
  - **Flip T→F post-regen:** provenance note verbatim: *"artifact input pre-regen — K4 first-True 07-05 = artifact of avg_px basis pre-regen"*
  - **Trùng (giữ T):** provenance note verbatim: *"K4 survives canonical — first-True 07-05 xác nhận cross-basis"*
- Cause tags eligible (post-regen residual nếu có): RÌA-TRÁI · WARMUP · (v)-px-basis · (v)-taker-basis · (v)-basis-mixed · KHÁC (block)

---

## CONFLICT columns

Không có (v1). Nếu ANALYSIS file copy vào proposals/ sau này có xung đột với v1, agent DỪNG hỏi trước khi merge.

---

## Post-regen assertions (per ⑬ luật nền)

1. Backup L-37: 11 file `.bak_pre_regen_manifest_20260826`
2. Changelog `docs/reports/resulttxt_regen_manifest_20260826.md` — md5 cũ→mới per file, replaced count per col
3. Identity-check L-51 per col regen: ≥3 mẫu khác regime (early / mid / late window) paste cạnh diff
4. Rename header `takerRatio` → `taker_ratio_endpoint_legacy`: verify replay.py parse positional không lỗi
5. **Fixture L-58 đầu commit:** 5/5 PASS (registry+watchlist không đọc funding/OI/klines cols)

**Chờ VERIFY FUNDING + OI (step 1) trước khi mở regen script.**
