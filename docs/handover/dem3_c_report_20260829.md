# Đêm-3 C Report · target=2026-08-28 · cron fire 2026-08-29 01:45 UTC

**Nguồn:** `/root/Data_back_test/whale_data/data/logs/gom_h_daily.log` (VPS 5.223.67.21) · SSH pull 2026-08-29 01:51 UTC.
**Status VPS:** CODE-FREEZE hết (freeze đêm-3 expire) → sẵn sàng SCP-batch. Tripwire trailing LOCAL-simulated (VPS chưa có lib/tripwire_e2_v2.py file).

---

## 5 MỐC + FREEZE-INTEGRITY PAIR (pre-SCP)

| # | mốc | giá trị |
|---|---|---|
| 1 | target_date | 2026-08-28 |
| 2 | n_symbols / store_rows | 139 / 41,000 |
| 3 | GOM-H FIRE count | **1 / 139** (HYPERUSDT [H2] conf=HIGH 4/4) |
| 4 | yaml md5 (VPS cron) | `3820b87cc5dd87e251b110f72685c704` (pre-SCP) |
| 5 | CSV output md5 | `6c218288cbc51808a00faf11ef8a6957` (`scratch/gom_h_daily_2026-08-28.csv`) |
| 4b | **CODE md5 gom_h_daily.py (VPS)** | `f99ef3c819ef60cb3948e5e5ac0bf6ea` — VPS pre-SCP · LOCAL sentinel-fix `ce01f8e14629833f22020196ba66b76d` (BATCH-4 diff · LỆCH) |
| 4c | **ADAPTER md5 (VPS)** | `1bfec529d9212110f510d99797fc097c` — VPS pre-SCP · LOCAL 3d-best `b6ac341ab74bff29a98dd23a1dc44144` (BATCH-3 file 1 · LỆCH) |

Coverage (n_fire / n_NA / n_eval / total):
- T0.1 = 3 / 0 / 139 / 139
- H1   = 0 / 8 / 131 / 139  (adapter ingest=2026-08-29 · rows=138)
- H2   = 13 / 0 / 139 / 139
- H3   = 2 / 0 / 139 / 139

---

## Telegram nguyên văn (CAMPAIGN-PRE 2026-08-28 · 1 fire + suppressed context)

```
CAMPAIGN-PRE 2026-08-28: 1 fires (fw-139)
  0GUSDT  [[suppressed:perp]]  conf=MED (3/4; N/A: -)  H3=F  [SUPPRESSED 2/14 lane=perp]
  AIOTUSDT  [[suppressed:kho]]  conf=MED (3/4; N/A: -)  H3=F  [SUPPRESSED 1/14 lane=kho]
  AKEUSDT  [[suppressed:perp]]  conf=MED (3/4; N/A: -)  H3=F  [SUPPRESSED 1/14 lane=perp]  [WALLETSET: BROAD-QUIET]
  ALLOUSDT  [[suppressed:kho]]  conf=MED (3/4; N/A: -)  H3=F  [SUPPRESSED 1/14 lane=kho]
  BANKUSDT  [[suppressed:perp]]  conf=MED (3/4; N/A: -)  H3=F  [SUPPRESSED 2/14 lane=perp]
  BILLUSDT  [[suppressed:perp]]  conf=MED (2/4; N/A: -)  H3=F  [SUPPRESSED 2/14 lane=perp]
  BTRUSDT  [[suppressed:kho+perp]]  conf=LOW (0/4; N/A: -)  H3=T  [SUPPRESSED 1/14 lane=kho] [SUPPRESSED 1/14 lane=perp]  [WALLETSET: BROAD-STRESS · vol=87.5x]
  CAPUSDT  [[suppressed:kho]]  conf=MED (2/4; N/A: -)  H3=F  [SUPPRESSED 3/14 lane=kho]
  CLOUSDT  [[suppressed:kho]]  conf=LOW (0/4; N/A: -)  H3=F  [SUPPRESSED 3/14 lane=kho]
  ENSOUSDT  [[suppressed:perp]]  conf=MED (3/4; N/A: -)  H3=F  [SUPPRESSED 2/14 lane=perp]  [WALLETSET: BROAD-QUIET]
  ERAUSDT  [[suppressed:perp]]  conf=MED (3/4; N/A: -)  H3=F  [SUPPRESSED 2/14 lane=perp]
  GWEIUSDT  [[suppressed:kho]]  conf=MED (2/4; N/A: -)  H3=F  [SUPPRESSED 3/14 lane=kho]
  HANAUSDT  [[suppressed:kho]]  conf=LOW (1/4; N/A: -)  H3=F  [SUPPRESSED 3/14 lane=kho]
  HEMIUSDT  [[suppressed:kho]]  conf=LOW (0/4; N/A: -)  H3=F  [SUPPRESSED 3/14 lane=kho]  [WALLETSET: BROAD-QUIET]
  HOMEUSDT  [[suppressed:perp]]  conf=MED (2/4; N/A: -)  H3=F  [SUPPRESSED 2/14 lane=perp]
  HYPERUSDT  [H2]  conf=HIGH (4/4; N/A: -)  H3=F
  INUSDT  [[suppressed:kho]]  conf=LOW (1/4; N/A: -)  H3=F  [SUPPRESSED 1/14 lane=kho]
  LAUSDT  [[suppressed:perp]]  conf=MED (3/4; N/A: -)  H3=F  [SUPPRESSED 3/14 lane=perp]
  MERLUSDT  [[suppressed:kho]]  conf=LOW (1/4; N/A: -)  H3=F  [SUPPRESSED 3/14 lane=kho]
  MIRAUSDT  [[suppressed:perp]]  conf=HIGH (4/4; N/A: -)  H3=F  [SUPPRESSED 4/14 lane=perp]
  OPNUSDT  [[suppressed:perp]]  conf=MED (3/4; N/A: -)  H3=F  [SUPPRESSED 2/14 lane=perp]
  SOPHUSDT  [[suppressed:kho]]  conf=LOW (1/4; N/A: -)  H3=F  [SUPPRESSED 3/14 lane=kho]
  SQDUSDT  [[suppressed:kho]]  conf=LOW (1/4; N/A: -)  H3=F  [SUPPRESSED 1/14 lane=kho]
  TACUSDT  [[suppressed:kho]]  conf=LOW (1/4; N/A: -)  H3=F  [SUPPRESSED 3/14 lane=kho]  [WALLETSET: BROAD-STRESS · vol=16.8x ret=-41.0%]
  TRIAUSDT  [[suppressed:kho]]  conf=LOW (0/4; N/A: -)  H3=F  [SUPPRESSED 3/14 lane=kho]  [WALLETSET: BROAD-STRESS · ret=-9.2%]
  XPINUSDT  [[suppressed:kho]]  conf=LOW (1/4; N/A: -)  H3=F  [SUPPRESSED 3/14 lane=kho]  [WALLETSET: BROAD-STRESS · ret=-8.9%]
  ZAMAUSDT  [[suppressed:perp]]  conf=LOW (1/4; N/A: -)  H3=F  [SUPPRESSED 2/14 lane=perp]
  ZBTUSDT  [[suppressed:kho]]  conf=MED (2/4; N/A: -)  H3=F  [SUPPRESSED 3/14 lane=kho]
  龙虾USDT  [[suppressed:kho]]  conf=LOW (0/4; N/A: -)  H3=F  [SUPPRESSED 3/14 lane=kho]  [WALLETSET: BROAD-STRESS · vol=40.9x]

---
spec_version: v4.0-draft
amendments_applied: GOI-NHE-20260829, V④-RT-2CHỐT-ANALYSIS-20260828, ⑬-COLUMN-MANIFEST-20260826, GOM-RESTRUCT-20260824
cfg-provenance: yaml_md5=3820b87cc5dd...
tripwire FP-rate=0.428 [TRIP] · raw=0.4277 (context) · grades-v4 md5 8fdd0a74 · Resolution b · [LOCAL-SIMULATED · SCP pending]
```

---

## Ramp-line status

**Không có H1 fire hôm nay** (H1 coverage: 0 fire / 8 N/A / 131 eval). Đêm-2 C ramp APRUSDT [H1-OUT −39.5%] tính vào SUPPRESSED lane=kho counter (nhiều token 3/14 · APRUSDT lần fire đầu vào day-0 cooldown lane=kho). Ramp cron sống tiếp — chỉ hôm nay không ai qua kho-step/ramp threshold.

## Walletset tags (8/29 rows)

- **BROAD-STRESS** (vol/ret trigger): BTRUSDT (vol=87.5×) · TACUSDT (vol=16.8× ret=−41.0%) · TRIAUSDT (ret=−9.2%) · XPINUSDT (ret=−8.9%) · 龙虾USDT (vol=40.9×)
- **BROAD-QUIET** (concentrated dampen): AKEUSDT · ENSOUSDT · HEMIUSDT

TACUSDT hôm nay STRESS **cả 2 chiều đồng thời** (vol=16.8× AND ret=−41.0%) — data mới interesting cho walletset review.

## Caveat 2 metric-variant

**⑩-B3-TAKER-CANONICAL** (24/08): H3 vẫn dùng `vol_source=fapi_k7_fresh` (k[7] trực tiếp). Cột `taker_source` provenance chưa migrate.

**H1-STEP metric-variant** [pending SCP]: VPS Đêm-3 vẫn dùng H1 1d-only (adapter md5 `1bfec529d921...`). LOCAL 3d-best canonical (md5 `b6ac341a...`) SẴN SCP. Kỳ vọng hậu-SCP: H1 fires TĂNG (3d-best bắt nhiều case rút hơn) · tripwire trailing 2 kỷ nguyên trộn — đọc chú thích.

## Tripwire trailing dòng [TRIP]

```
tripwire FP-rate=0.428 [TRIP] · raw=0.4277 (context) · grades-v4 md5 8fdd0a74 · Resolution b · [LOCAL-SIMULATED · SCP pending]
```

**Ghi chú:** VPS chưa có `lib/tripwire_e2_v2.py` (BATCH-3 file 3 pending). Post-SCP dòng emit từ chính cron với `[TRIP]` state trực tiếp.

## ERRATA-giấy sort-RIPE (lần đầu)

**Render tới nay sort lệch spec §0 — số đúng, thứ tự đổi.** Impl `scanner/tg_render.py:123-125` chỉ sort by conf (single criterion `HIGH→MED→LOW`); spec §0 "RIPE trước, rồi conf" (2-level bucket). Số hiển thị đúng, chỉ **thứ tự** sắp xếp lệch bucket-first-conf-second. Fix nằm `tg_render.py` → SCP-SAU cùng phase_tag re-deploy (VPS chưa đổi render thì dòng chưa in được — giấy đi trước, màn hình theo sau). Ref: audit A6(ii).

---

## Confirm H1-ABS-20260901 + bundle MA pointer (đã đóng LOCAL)

- **H1-ABS-20260901** spec merged (bot-signals commit `e355610b` · spec md5 `3c57a13b606c4b9c7550c5ab1f601b7a`): changelog VERBATIM + shorthand `|Δ|` dòng 188+195 · dòng 148 giữ. **VPS render chưa impact** (VPS đọc yaml có spec_version=v4.0-draft, không đọc spec doc trực tiếp).
- **Bundle MA-item pointer** append (whale_data commit `84c3216` · yaml md5 `3d11e572d77a657a2e5638dd6027e3a8`): `goi_nhe.review_bundle_20260927.items[MA-only]` thêm pointer `docs/proposals/spot_shadow_pair_goi_ky_20260927.md md5 b90e722b`.
- **F1/F2 bot-yaml** đóng LOCAL (bot-yaml commit `f5de0228` · md5 `7637d1a77d61508e9b1af936505c5cc7`): h4 mirror-CLOSED pointer-style + spot_cvd.source clobber fix.

---

## Checklist 5+3+1+1+2 (12 mục)

### 5 items sống review-bundle 27/09 (yaml `goi_nhe.review_bundle_20260927.items`)
- [x] ramp: kho_ramp.delta_min 0.15 / window 14d · Đêm-3 KHÔNG fire (cooldown lane=kho activated từ Đêm-2 C APRUSDT)
- [x] verify_walletset [50%]: min_abs_delta 0.50 · anchor SOPH · TAC 08-28 vol=16.8× ret=−41% multi-axis stress row bổ sung sample
- [x] walletset_2x2: {50% · 5 abs · 5×∨−8% OR} · **8 tags emit đêm-3 C (5 stress · 3 quiet) ✓**
- [x] AKE-row2: via-ramp PROVISIONAL-30d · AKE hôm nay BROAD-QUIET tag
- [x] MA-only (3 ô): gói-ký md5 b90e722b · store spot-51 tài sản (19,452 rows) chờ 27/09 operator ky

### 3 items hồ-sơ-đóng-trình-đọc
- [x] V③-cutpoint: closed-no-change · changelog V3-CLOSED-20260831
- [x] E2-tripwire: [TRIP] tại review (rate=0.428 · grades-v4 md5 8fdd0a74 · Resolution b)
- [x] H4-CLOSED + SPOT-CVD-GỘP: holder metric mù + CI-90% [1.85×, 8.93×] KNOWN-GAP-LIGHT

### 1 conf-kiểm-định
- [x] conf-labeler audit: obs_min=14 canonical · WALLETSET 2×2 emit · ramp sống cron từ 2026-08-28 (Đêm-2 C ✓)

### 1 ramp-line status
- [x] Đêm-3 C: H1 fire=0 · Đêm-2 C ramp APRUSDT vào SUPPRESSED lane=kho counter · cooldown 14d hoạt đúng

### 2 SCP / audit-fix status
- [x] SCP-batch REVISED post-freeze: 4 file md5 stable · MD5 DISCIPLINE re-verified 01:51 UTC 29/08
- [x] AUDIT-FIX đợt 1 đóng LOCAL: tripwire clean + gom_h_daily sentinel + fixtures + A11 CONTENT-PARITY 5/5

---

## Kết luận

Đêm-3 C nghiệm chứng: 1 fire (HYPERUSDT [H2] conf=HIGH) · nhiều SUPPRESSED cooldown counter tăng đều · walletset 8 tags · cron behave đúng. Ramp im hôm nay (cooldown hoạt), không phải fault. VPS pre-SCP còn 3 file (adapter · yaml · tripwire) + BATCH-4 option gom_h_daily sentinel — chờ operator "ok scp" + chọn batch.
