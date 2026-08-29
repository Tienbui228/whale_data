# SPOT-SHADOW-PAIR · GÓI-KÝ 27/09 (lắp sẵn, chờ đọc-và-ký)

**Status:** DRAFT-READY-FOR-SIGN · ANALYSIS format · KÝ 01/09  
**Purpose:** 27/09 là đọc-và-ký, không phải build. Tất cả evidence + numbers + CI đã có; operator chỉ chọn giá trị trong [ ] và ký.  
**Bundle scope:** `MA-only 3 ô` + `DQ-DELIST` + `SPOT-CVD closed-gộp` + sổ giao-điểm.  
**Ref bundle yaml:** `screen_thresholds.yaml goi_nhe.review_bundle_20260927`

---

## §1 — MA 3 Ô (đề cử · [ ] chờ operator ký) · CANONICAL N=10k

**Yaml canonical:** `binance-bot-signals/screen_thresholds.yaml ma_shadow` block (bot render pipeline · KHÔNG wire whale_data cron).

**Evidence CANONICAL (thay N=1000 screening):** [ma_canonical_n10k_20260828.csv](../reports/ma_canonical_n10k_20260828.csv) md5 `dca9457cde0a6b1c33bed8dc96359981` — N=10,000 draws/cell · seed per-cell in header.

**Exhibit (superseded cho 2 ô dao):** [ma_lift_grid_v2_20260828.csv](../reports/ma_lift_grid_v2_20260828.csv) md5 `655a0b091d4a2302978fc551cf302876` [MC-N1000 · screening] (8 nấc gradient · Δlift-vs-kề · %delist_v2).

### CANONICAL bảng N=10k · 4 cells (2 nấc dao × with/ex-SOPH)
| nấc | set | fires | uncens | hits | rate | matched | **lift** | **CI-90%** | robust CI_5%>1 |
|---|:---:|---:|---:|---:|---:|---:|:---:|:---:|:---:|
| vol1.0_tk45.0 | with-SOPH | 325 | 175 | 26 | 14.9% | 11.48% | 1.29× | [0.91, 1.70] | ✗ mấp mé |
| vol1.0_tk45.0 | ex-SOPH | 299 | 167 | 26 | 15.6% | 11.09% | 1.40× | [0.99, 1.84] | ✗ mấp mé |
| **vol1.5_tk45.0** | **with-SOPH** | 104 | 74 | 14 | 18.9% | 10.45% | **1.81×** | **[1.13, 2.57]** | **✓ ROBUST** |
| **vol1.5_tk45.0** | **ex-SOPH** | 93 | 69 | 14 | 20.3% | 10.89% | **1.86×** | **[1.16, 2.64]** | **✓ ROBUST** |

### Đề cử vận hành
**`taker=45 · vol=1.5 = ô robust duy nhất qua re-draw độc lập N=10k`** — CI_5% > 1 cả with-SOPH (1.13×) LẪN ex-SOPH (1.16×). `vol=1.0` mấp mé CI_5% (0.91×-0.99×) cả hai bản → chọn 1.5 an toàn qua noise MC.

**`taker=42.5 loại tại screening`** (lift 1.12-1.17× N=1000, gap −0.5× vs nấc 45 > 3× MC-noise ±0.2×) — không cần bản canonical; ô điền thực chất là xác nhận 45.

### Ca-đối-chiếu-sống HUMA (post-ruling MỌI-H3=T · exhibit n=1)
**HUMAUSDT** top-3 MA-episode (18 cửa sổ · [ma_shadow_backtest_20260828.csv](../reports/ma_shadow_backtest_20260828.csv)) · con 🌊-ngoài-tập đầu tiên post-ruling RENDER-V2 MỌI-H3=T (data 28/08 · h1_raw=F · h2t01=F · h3_raw=T · vol=11.5× · BROAD-STRESS). Exhibit n=1 cho giá trị khối 🌊 + MA-lane cùng bắt một token — bàn 27/09 đọc kèm 3 ô số MA (taker · vol_x · ret_abs).

### Note vùng-mỏng (từ grid v2 exhibit)
`vol_x=1.5, taker=40%` → lift 0.76× · CI [0.00, 2.24] (11 uncens · **thua ở 40-mỏng** · không đủ sample). Đề cử 1.5/45 vì thắng vùng dao, tránh vùng-mỏng.

### Ô (iii) · ret_abs_max = **[3%]** giữ regime-leg
Regime-leg MA (parallel với px_min30 ≤ 1.3 của SPOT-CVD). Không đề cử thay đổi — đây là định-nghĩa "ngày phẳng". Grid không sweep ret vì đổi = đổi bản chất nhãn.

### Tổng đề cử §1 · CANONICAL CI cạnh
```yaml
ma_shadow:
  vol_x:      1.5              # lift 1.81x with-SOPH · CI-90% [1.13, 2.57] (CANONICAL N=10k)
  taker_max:  0.45             # ex-SOPH lift 1.86x · CI-90% [1.16, 2.64]
  ret_abs:    0.03             # regime-leg, không đổi
```

### L-64 · MC-precision (bộ số tự vệ phương sai máy đo)
- **N=10,000 draws/cell** · seed per-cell = 42 + sha256(cell_key)[:8] % 100000 · in header CSV
- MC error co ~3× vs N=1000 screening: ±0.3pp matched → ±~0.05× lift
- Grid-v2 + micro-table (N=1000) đánh dấu **[MC-N1000 · screening, superseded cho 2 ô dao]** — giữ làm exhibit gradient, không phải bộ số vận hành

---

## §2 — DQ-DELIST draft (khuôn DQ-SERIAL · [ ] chờ ký)

**Rationale:** DEATH-MIMICRY THẬT — SOPH fires DO NOT hit (0/9 eps @ vol1.0 · 0/6 eps @ vol1.5) → **DQ-DELIST mua alert-cleanliness** (loại 26 fires @ vol1.0 · 11 @ vol1.5 · 8-11% noise reduction) hơn lift-boost.

### Bảng giá ex-SOPH · CANONICAL N=10k (2 nấc ứng viên)
| nấc | with-SOPH lift | ex-SOPH lift | **Δlift** | fires saved | SOPH_eps |
|---|:---:|:---:|:---:|:---:|:---:|
| vol1.0_tk45.0 | 1.29× [0.91, 1.70] | 1.40× [0.99, 1.84] | **+0.11×** | 26 (8.0%) | 9 |
| **vol1.5_tk45.0** | 1.81× [1.13, 2.57] | **1.86×** [1.16, 2.64] | **+0.05×** | 11 (10.6%) | 6 |

**Evidence:** [ma_canonical_n10k_20260828.csv](../reports/ma_canonical_n10k_20260828.csv) md5 `dca9457cde0a6b1c33bed8dc96359981` (CANONICAL).
Screening exhibit (superseded): [ma_ex_soph_micro_20260828.csv](../reports/ma_ex_soph_micro_20260828.csv) md5 `5deea6310979d681c9d29e18832c2767` [MC-N1000].

### DQ-DELIST khuôn DQ-SERIAL (yaml draft)
```yaml
# [DQ-DELIST 01/09 draft · khuôn DQ-SERIAL BANANAS31 · CHỜ Tiên KÝ 27/09]
dq_delist:
  members: [SOPHUSDT]
  source: "network-withdrawal curated · SOPH BSC network suspend 2026-08-21 08:00 UTC"
  cites:
    - "https://www.cryptometer.io/news/binance-flags-five-tokens-as-possible-delisting-risks/"
    - "https://crypto.news/binance-flags-5-tokens-as-possible-delisting-risks/"
    - "https://bitcoinfoundation.org/news/crypto-companies-news/binance-puts-5-altcoins-on-delisting-watch-as-movr-and-glmr-prices-tumble/"
  source_file: "docs/handover/soph_triage_20260827.md"
  check_before_emit: true             # same pattern DQ-SERIAL BANANAS31
  emit_label: "[DQ-DELIST]"           # khi bị chặn (không im · khuôn SUPPRESSED)
  fire_bypass_cooldown: true          # fire bị chặn KHÔNG khởi cooldown (same DQ-SERIAL rule)
  add_remove_rule: "chữ ký operator từng thay đổi (không auto-detect)"
```

**Ref evidence:** [ma_delist_flag_v2_20260828.csv](../reports/ma_delist_flag_v2_20260828.csv) md5 `177c9e6c8ffbf913d22c90de1903a640` (v2 · 1/51 flagged SOPHUSDT · fire-rate 3.59× vs unflagged).

---

## §3 — SPOT-CVD-SHADOW văn bia GỘP (merged · reference)

**Trạng thái:** CLOSED-GỘP KNOWN-GAP-LIGHT (đã merge vào spec + yaml). Bundle 27/09 mục trình-đọc.

**Changelog refs:** `SPOTCVD-CI-AMEND-20260901` + `SPOTCVD-CLOSED-20260901` (bot-signals gom_detect_spec.md).

**Văn bia:** point lift 5.50× · joint bootstrap N=10k CI-90% [1.85×, 8.93×] · CI_5% < 2.0 → hai vế **tín-hiệu-có-hình** (CI_5% có phần dưới 1.3× nhưng point lift 5.50× · hình có · thiếu base) hoặc **mẫu-không-nuôi-nổi-nhãn** (n=3 hits · luật-2 vùng Nhiễu · mẫu không đủ chấm số) cùng khả năng · gap có tên · reopen khi n ≥ 5 hits (evidence-ceil operator ký tương lai).

**GÓI ĐÓNG y nguyên:** bundle MA-only 3 ô · D4/HYPER/D5 CANCELLED · store spot-51 giữ (MA + case). Vận hành KHÔNG đổi.

**Evidence refs:**
- [spot_cvd_annex125d_20260828.csv](../reports/spot_cvd_annex125d_20260828.csv) md5 `268f5e70f89da3fa5fcdef6324741d45` (matched-control bootstrap N=1000)
- [spot_cvd_ci_addendum_20260828.csv](../reports/spot_cvd_ci_addendum_20260828.csv) md5 `fb990645003ab3b1d08bcad1fb6055f2` (joint CI N=10k)

---

## §4 — Sổ giao-điểm (n=1 events · ghi sổ · không mở việc)

### ENSO · FORMULA-NEAR ∧ CVD+ pre-D_cross
- **Nguồn:** ANNEX-125c CROSS-REF · [spot_cvd_annex125c_20260828.csv](../reports/spot_cvd_annex125c_20260828.csv)
- ENSO = FORMULA-NEAR (U-v3 annex oi 5.6%) ∧ CVD+ episode pre-D_cross
- **best_fwd_30d = +52.80%** · hit=True · n=1
- Ghi sổ · KHÔNG mở việc (SPOT-CVD closed-gộp · một n=1 không mở lại rule)

### (a) mồ-côi chờ RIDE (open register)
- Placeholder for future evidence: singletons matching either (a) chết-sạch hoặc (c) thin-signal cửa của CVD gộp → chờ n ≥ 5 hits để reopen SPOT-CVD
- Currently: ENSO là singleton duy nhất; chờ evidence bổ sung

---

## Wait-state (khi ký xong 27/09)

- MA 3 ô ký → whale_data cron KHÔNG nhận (bot render pipeline chỉ, không compose) · bot deploy update yaml sau
- DQ-DELIST ký → yaml block wire trong bot render + whale_data phase_tag (khuôn DQ-SERIAL)
- SPOT-CVD-CLOSED-GỘP: không có action (đóng · reopen rule đã ghi)
- Sổ giao-điểm ENSO: idle observer

## Refs

- Bundle canonical: [whale_data/screen_thresholds.yaml](../../screen_thresholds.yaml) `goi_nhe.review_bundle_20260927`
- Store: `data/raw/spot_klines_1d` venue=binance_spot (51 sym · 19,452 rows · last=2026-08-27)
- CEX curated list (SPOT-CVD legacy): [docs/reference/cex_addresses_bsc.txt](../reference/cex_addresses_bsc.txt) md5 `0983fb5f8a190872ac2b904798b3cbf7`
