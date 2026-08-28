# Đêm-2 C Report · target=2026-08-27 · cron fire 2026-08-28 01:45 UTC

**Nguồn:** `/root/Data_back_test/whale_data/data/logs/gom_h_daily.log` (VPS 5.223.67.21) · SSH pull 2026-08-28.
**Status VPS:** CODE-FREEZE VPS đêm-3 vẫn active (hết 2026-08-29 01:45 UTC) — tripwire_e2_v2.py chưa SCP → [TRIP] trailing dòng dưới đây từ LOCAL simulation (Resolution b · rate=0.4277 · grades-v4 8fdd0a74).

---

## 5 MỐC

| # | mốc | giá trị |
|---|---|---|
| 1 | target_date | 2026-08-27 |
| 2 | n_symbols / store_rows | 139 / 40,480 |
| 3 | GOM-H FIRE count | **8 / 139** (H1-lane 6 · H2-lane 1 · H1+H2 combined 1) |
| 4 | yaml md5 | `3820b87cc5dd87e251b110f72685c704` |
| 5 | CSV output md5 | `9cc8ff655d1d2a0cc03368b56bd3c5be` (`scratch/gom_h_daily_2026-08-27.csv`) |

Coverage (n_fire / n_NA / n_eval / total):
- T0.1 = 3 / 0 / 139 / 139
- H1   = 0 / 8 / 131 / 139  (adapter ingest=2026-08-28, rows=138)
- H2   = 16 / 0 / 139 / 139
- H3   = 1 / 0 / 139 / 139

---

## Telegram nguyên văn (CAMPAIGN-PRE 2026-08-27 · 8 fires + suppressed context)

```
CAMPAIGN-PRE 2026-08-27: 8 fires (fw-139)
  0GUSDT  [[suppressed:perp]]  conf=MED (3/4; N/A: -)  H3=F  [SUPPRESSED 1/14 lane=perp]
  AIOTUSDT  [H1]  conf=MED (3/4; N/A: -)  H3=F
  AKEUSDT  [H2]  conf=MED (2/4; N/A: -)  H3=F  [SUPPRESSED 2/14 lane=kho]
  ALLOUSDT  [H1]  conf=MED (2/4; N/A: -)  H3=F
  APRUSDT  [H1-OUT -39.5%]  conf=LOW (1/4; N/A: -)  H3=F
  BANKUSDT  [[suppressed:perp]]  conf=MED (2/4; N/A: -)  H3=F  [SUPPRESSED 1/14 lane=perp]
  BILLUSDT  [[suppressed:perp]]  conf=LOW (1/4; N/A: -)  H3=F  [SUPPRESSED 1/14 lane=perp]
  BTRUSDT  [H1 + H2]  conf=LOW (0/4; N/A: -)  H3=F  [WALLETSET: BROAD-STRESS · vol=259.2x]
  CAPUSDT  [[suppressed:kho]]  conf=LOW (1/4; N/A: -)  H3=F  [SUPPRESSED 2/14 lane=kho]
  CLOUSDT  [[suppressed:kho+perp]]  conf=MED (2/4; N/A: -)  H3=F  [SUPPRESSED 2/14 lane=kho] [SUPPRESSED 1/14 lane=perp]  [WALLETSET: BROAD-STRESS · vol=6.6x]
  ENSOUSDT  [[suppressed:perp]]  conf=HIGH (4/4; N/A: -)  H3=F  [SUPPRESSED 1/14 lane=perp]
  ERAUSDT  [[suppressed:perp]]  conf=MED (2/4; N/A: -)  H3=F  [SUPPRESSED 1/14 lane=perp]
  FUSDT  [[suppressed:perp]]  conf=MED (2/4; N/A: -)  H3=F  [SUPPRESSED 1/14 lane=perp]
  GWEIUSDT  [[suppressed:kho]]  conf=MED (3/4; N/A: -)  H3=F  [SUPPRESSED 2/14 lane=kho]
  HANAUSDT  [[suppressed:kho]]  conf=LOW (1/4; N/A: -)  H3=F  [SUPPRESSED 2/14 lane=kho]
  HEMIUSDT  [[suppressed:kho]]  conf=LOW (0/4; N/A: -)  H3=F  [SUPPRESSED 2/14 lane=kho]  [WALLETSET: BROAD-QUIET]
  HOMEUSDT  [H1]  conf=MED (2/4; N/A: -)  H3=F  [SUPPRESSED 1/14 lane=perp]
  INUSDT  [H1]  conf=LOW (1/4; N/A: -)  H3=F
  LABUSDT  [[suppressed:kho]]  conf=MED (2/4; N/A: -)  H3=F  [SUPPRESSED 2/14 lane=kho]  [WALLETSET: BROAD-QUIET]
  LAUSDT  [[suppressed:perp]]  conf=MED (3/4; N/A: -)  H3=F  [SUPPRESSED 2/14 lane=perp]  [WALLETSET: BROAD-QUIET]
  MERLUSDT  [[suppressed:kho]]  conf=LOW (1/4; N/A: -)  H3=F  [SUPPRESSED 2/14 lane=kho]  [WALLETSET: BROAD-STRESS · vol=5.1x]
  MIRAUSDT  [[suppressed:perp]]  conf=HIGH (4/4; N/A: -)  H3=F  [SUPPRESSED 3/14 lane=perp]
  OPNUSDT  [[suppressed:perp]]  conf=MED (3/4; N/A: -)  H3=F  [SUPPRESSED 1/14 lane=perp]
  SAHARAUSDT  [[suppressed:perp]]  conf=MED (2/4; N/A: -)  H3=F  [SUPPRESSED 1/14 lane=perp]  [WALLETSET: BROAD-QUIET]
  SLXUSDT  [[suppressed:perp]]  conf=MED (2/4; N/A: -)  H3=F  [SUPPRESSED 1/14 lane=perp]
  SOPHUSDT  [[suppressed:kho]]  conf=LOW (1/4; N/A: -)  H3=F  [SUPPRESSED 2/14 lane=kho]
  SQDUSDT  [H1]  conf=LOW (1/4; N/A: -)  H3=F
  TACUSDT  [[suppressed:kho]]  conf=LOW (0/4; N/A: -)  H3=F  [SUPPRESSED 2/14 lane=kho]  [WALLETSET: BROAD-STRESS · vol=154.3x]
  TAGUSDT  [[suppressed:kho]]  conf=MED (2/4; N/A: -)  H3=F  [SUPPRESSED 2/14 lane=kho]
  TOWNSUSDT  [[suppressed:kho]]  conf=LOW (1/4; N/A: -)  H3=F  [SUPPRESSED 2/14 lane=kho]
  TRIAUSDT  [[suppressed:kho]]  conf=LOW (0/4; N/A: -)  H3=F  [SUPPRESSED 2/14 lane=kho]
  XPINUSDT  [[suppressed:kho]]  conf=LOW (1/4; N/A: -)  H3=F  [SUPPRESSED 2/14 lane=kho]
  ZBTUSDT  [[suppressed:kho+perp]]  conf=MED (2/4; N/A: -)  H3=F  [SUPPRESSED 2/14 lane=kho] [SUPPRESSED 1/14 lane=perp]
  龙虾USDT  [[suppressed:kho]]  conf=LOW (0/4; N/A: -)  H3=F  [SUPPRESSED 2/14 lane=kho]  [WALLETSET: BROAD-STRESS · ret=-14.5%]

---
spec_version: v4.0-draft
amendments_applied: GOI-NHE-20260829, V④-RT-2CHỐT-ANALYSIS-20260828, ⑬-COLUMN-MANIFEST-20260826, GOM-RESTRUCT-20260824
cfg-provenance: yaml_md5=3820b87cc5dd...
tripwire FP-rate=0.428 [TRIP] · raw=0.4277 (context) · grades-v4 md5 8fdd0a74 · Resolution b · [LOCAL-SIMULATED · SCP pending]
```

---

## Ramp-line ĐẦU TIÊN trên cron (từ 2026-08-28)

**APRUSDT [H1-OUT -39.5%]  conf=LOW (1/4; N/A: -)  H3=F**

Nghiệm chứng ramp-fire lần đầu qua cron production sau khi rev4-FINAL restore ramp compute (kho_ramp.delta_min 0.15 / window 14d). Sổ CLAUDE.md khai "ramp sống lần đầu trên cron từ 2026-08-28" — MATCHES.

## Walletset tags trong đêm (9/34 rows)

- **BROAD-STRESS** (vol/ret trigger): BTRUSDT (vol=259.2×) · CLOUSDT (vol=6.6×) · MERLUSDT (vol=5.1×) · TACUSDT (vol=154.3×) · 龙虾USDT (ret=−14.5%)
- **BROAD-QUIET** (concentrated dampen): HEMIUSDT · LABUSDT · LAUSDT · SAHARAUSDT

Walletset 2×2 tags emit stable, precedence "stress > 2x2" chưa gặp conflict (không có concentrated + broad-stress đồng thời).

## Caveat metric-variant

**⑩-B3-TAKER-CANONICAL amendment (24/08):** basis pin `k[10]/k[7]` (quote/quote), CẤM `k[9]/k[7]` (mixed đơn vị). Vế H3 hiện dùng `vol_source=fapi_k7_fresh` (k[7] trực tiếp — SỐNG cho tới khi P0 STORE-VOL-DUP đóng). Cột `taker_source` provenance chưa migrate — residual hai họ trong lúc chưa migrate mang cause-tag `(v)` taker-lineage (không ảnh hưởng lane H3 hôm nay: FIRE=1).

## Tripwire trailing dòng [TRIP]

```
tripwire FP-rate=0.428 [TRIP] · raw=0.4277 (context) · grades-v4 md5 8fdd0a74 · Resolution b · [LOCAL-SIMULATED · SCP pending]
```

**Ghi chú:** Trong Đêm-2 C này VPS chưa có tripwire_e2_v2.py (LOCAL commit chỉ). Dòng trên tính từ lib/tripwire_e2_v2.py REAL-RUN LOCAL (rate = 43 × 30 / 52 / 58 = 0.4277 ≈ 0.428 → [TRIP]). Sau SCP-batch REVISED (29/08 hết freeze) dòng này emit từ chính cron.

---

## Checklist 5+3+1+1+2 (12 mục)

### 5 items sống review-bundle 27/09 (yaml `goi_nhe.review_bundle_20260927.items`)
- [x] ramp: kho_ramp.delta_min 0.15 / window 14d · provisional_start 2026-08-28 — **lần fire đầu 27/08 APRUSDT H1-OUT −39.5% ✓**
- [x] verify_walletset [50%]: min_abs_delta 0.50 · anchor SOPH · grade tracking
- [x] walletset_2x2: {50% · 5 abs · 5×∨-8% OR} · **9 tags emit đêm-2 C (5 stress · 4 quiet) ✓**
- [x] AKE-row2: via-ramp PROVISIONAL-30d · fixture Row-2 · auto_revert nếu ramp khai tử
- [x] MA-shadow: [PENDING-DEF] chờ operator drop spec

### 3 items hồ-sơ-đóng-trình-đọc (yaml `hồ_sơ_đóng_trình_đọc`)
- [x] V③-cutpoint: closed-no-change per ANALYSIS 31/08 · changelog V3-CLOSED-20260831
- [x] E2-tripwire: [TRIP] tại review (rate=0.428 · Resolution b · grades-v4 md5 8fdd0a74)
- [x] H4-CLOSED: holder-composition metric mù loài captive-nội-sàn (survey fa55cf7c · changelog H4V1-CLOSED-20260901)

### 1 conf-kiểm-định (yaml `conf_kiem_dinh`)
- [x] conf-labeler audit: obs_min=14 canonical · WALLETSET 2×2 tag emit · ramp sống cron từ 2026-08-28 — review FP-load 30d

### 1 ramp-line status
- [x] Ramp-fire lần đầu qua cron: APRUSDT [H1-OUT −39.5%] target=2026-08-27

### 2 code-freeze / SCP status
- [x] Code-freeze VPS đêm-3 active tới 2026-08-29 01:45 UTC — LOCAL commits ready SCP: 4 file (adapter_h1_nansen · yaml drift · lib/h4_flow[DORMANT] · lib/tripwire_e2_v2)
- [x] SCP-BATCH REVISED (per ANALYSIS verdict 01/09): rút h4_flow + runner-integration → 3 file: adapter_h1_nansen · yaml (drift + h4-closed + census_generations) · lib/tripwire_e2_v2

---

## Kết luận

Đêm-2 C nghiệm chứng 4 khối wire mới trên cron production (rev4-FINAL, walletset 2×2, ramp sống, obs_min=14 canonical) — không lỗi, coverage đầy đủ, ramp-fire lần đầu qua APRUSDT. Tripwire [TRIP] simulate LOCAL (rate 0.4277), real-emit sau SCP-batch REVISED 29/08. H4-v1 CLOSED-BY-PRINCIPLE 01/09 rút khỏi review-bundle 27/09 sống → hồ-sơ-đóng-trình-đọc 3 mục.
