# SPOT-SHADOW-PAIR · GÓI-KÝ 27/09 (lắp sẵn, chờ đọc-và-ký)

**Status:** DRAFT-READY-FOR-SIGN · ANALYSIS format · KÝ 01/09  
**Purpose:** 27/09 là đọc-và-ký, không phải build. Tất cả evidence + numbers + CI đã có; operator chỉ chọn giá trị trong [ ] và ký.  
**Bundle scope:** `MA-only 3 ô` + `DQ-DELIST` + `SPOT-CVD closed-gộp` + sổ giao-điểm.  
**Ref bundle yaml:** `screen_thresholds.yaml goi_nhe.review_bundle_20260927`

---

## §1 — MA 3 Ô (đề cử · [ ] chờ operator ký)

**Yaml canonical:** `binance-bot-signals/screen_thresholds.yaml ma_shadow` block (bot render pipeline · KHÔNG wire whale_data cron).

**Evidence source:** [ma_lift_grid_v2_20260828.csv](../reports/ma_lift_grid_v2_20260828.csv) md5 `655a0b091d4a2302978fc551cf302876` (grid 8 nấc · joint bootstrap N=10k · seed=42).

### Ô (i) · taker_max ∈ {42.5%, **[45%]** đề cử}
| taker_max | fires | uncens | hits | rate | matched | lift | CI-90% | Δlift-kề |
|---|---:|---:|---:|---:|---:|---:|:---:|---:|
| 42.5% (vol=1.0) | 127 | 77 | 10 | 13.0% | 11.60% | **1.12×** | [0.59, 1.75] | −0.34 |
| **45.0% (vol=1.0)** | 325 | 175 | 26 | 14.9% | 9.00% | **1.65×** | [1.14, 2.26] | **+0.53** |
| **45.0% (vol=1.5)** | 104 | 74 | 14 | 18.9% | 9.70% | **1.95×** | [1.18, 2.88] | **+0.78** |

**Đề cử:** `taker_max = 45%` — lift 1.65×-1.95× · CI_5% > 1 (better than random) · Δlift-vs-kề dương (gradient tăng khi thắt).

### Ô (ii) · vol_x ∈ {1.0, **[1.5]** đề cử}
| vol_x @ taker=45% | fires | uncens | lift | CI-90% | note |
|---|---:|---:|---:|:---:|---|
| 1.0 | 325 | 175 | 1.65× | [1.14, 2.26] | vùng permissive · fires nhiều · lift nhỏ hơn |
| **1.5** | 104 | 74 | **1.95×** | [1.18, **2.88**] | **thắng tại vùng dao · CI upper 2.88 (approach CLOSED-THIN 2× cutline)** |

**Note vùng-mỏng:** `vol_x=1.5, taker=40%` → lift 0.76× · CI [0.00, 2.24] (11 uncens · **thua ở 40-mỏng** · không đủ sample). Đề cử 1.5 vì thắng vùng dao, tránh vùng-mỏng.

### Ô (iii) · ret_abs_max = **[3%]** giữ regime-leg
Regime-leg MA (parallel với px_min30 ≤ 1.3 của SPOT-CVD). Không đề cử thay đổi — đây là định-nghĩa "ngày phẳng". Grid không sweep ret vì đổi = đổi bản chất nhãn.

### Tổng đề cử §1 · CI in cạnh
```yaml
ma_shadow:
  vol_x:      1.5              # lift 1.95x · CI-90% [1.18, 2.88]
  taker_max:  0.45             # taker ≤ 45% · gradient +0.78 vs kề
  ret_abs:    0.03             # regime-leg, không đổi
```

---

## §2 — DQ-DELIST draft (khuôn DQ-SERIAL · [ ] chờ ký)

**Rationale:** DEATH-MIMICRY THẬT (ex-SOPH micro-table [ma_ex_soph_micro_20260828.csv](../reports/ma_ex_soph_micro_20260828.csv) md5 `5deea6310979d681c9d29e18832c2767`). SOPH fires DO NOT hit (0/9 eps @ vol1.0 · 0/6 eps @ vol1.5) → **DQ-DELIST mua alert-cleanliness** (loại 26 fires @ vol1.0 · 11 @ vol1.5 · 8-11% noise reduction) hơn lift-boost (Δlift +0.00× / +0.20×).

### Bảng giá ex-SOPH (2 nấc ứng viên)
| nấc | with-SOPH lift | ex-SOPH lift | Δlift | fires saved | SOPH_eps |
|---|:---:|:---:|:---:|:---:|:---:|
| vol1.0_tk45.0 | 1.33× [0.92, 1.80] | 1.33× [0.92, 1.81] | **+0.00×** | 26 (8.0%) | 9 |
| vol1.5_tk45.0 | 1.75× [1.06, 2.56] | **1.95×** [1.20, 2.86] | **+0.20×** | 11 (10.6%) | 6 |

(Lift numbers ex-SOPH differ slightly từ grid v2 vì seed re-init per nấc — nhưng pattern ổn định.)

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

**Văn bia:** point lift 5.50× · joint bootstrap N=10k CI-90% [1.85×, 8.93×] · CI_5% < 2.0 → hai vế (a) chết-sạch (CI_5% có phần dưới 1.3×) hoặc (c) thin-signal cùng khả năng · gap có tên · reopen khi n ≥ 5 hits (evidence-ceil operator ký tương lai).

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
