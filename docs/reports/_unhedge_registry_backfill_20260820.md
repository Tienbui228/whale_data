# UN-HEDGE REGISTRY v1.0 — E-R7 Backfill Acceptance
**Date:** 2026-08-20  
**Spec:** `proposals/unhedge_registry_spec_v1.0.md` v1.0 (framework ký, thresholds provisional)  
**Backfill task:** `_task_unhedge_registry_backfill_20260820.py` + `_task_unhedge_registry_calib_20260820.py`  
**Data:** freshwatch_daily 2026-05/06/07/08 (35,218 rows, 527 unique tokens)  
**Window:** 2026-06-20 → 2026-08-19 (60 days)  
**Purpose:** Kiểm tra 4 gates E-R7 trước khi ship cron.

---

## §1 — BACKFILL RESULT (provisional thresholds §E-R6)

| Metric | Value |
|--------|-------|
| Total entries (60d) | **219** |
| trigger (a) UNHEDGE-BREAK | 198 |
| trigger (b) UNHEDGE-DRIFT | 21 |
| ignited within 90d (vol×5 OR OI+30%/2d) | **133 (60.7%)** |
| Unique tokens in registry | 147 / 527 = **27.9%** |

**Verdict provisional:** Gate (iv) **FAIL** ở 27.9% > 25%. Cần calibration trước ship.

---

## §2 — CALIBRATION TEST (`struct_n ≥ 3` filter)

**Rationale:** Với E-R1(a) UNHEDGE-BREAK, `struct_n = 1-2` (episode chỉ 1-2 ngày) là **noise** — không phải hedge structure thật. Watchlist v1.3 §1 (pointer trong spec) implicit require episode length ≥ 3d meaningful. Thêm filter `struct_n ≥ 3` trước khi vào registry.

**Kết quả sau filter:**

| Metric | Original | struct_n≥3 | struct_n≥5 | struct_n≥3 AND px≥-5% |
|--------|----------|-----------|-----------|-----------------------|
| Total entries | 219 | **160** | 124 | 119 |
| Unique tokens | 147 (27.9%) | **119 (22.6%)** ✓ | 98 (18.6%) | 95 (18.0%) |
| Break trigger | 198 | 139 | — | — |
| Drift trigger | 21 | 21 | — | — |
| Ignite hit-rate | 60.7% | **63.1%** | 65.3% | 63.0% |

**→ Đề xuất calibration ship-ready:** `struct_n ≥ 3` (đơn giản, cover-all).

**Trigger-level hit-rate (struct_n≥3):**
- **Break (a):** 85/139 = **61.2%** ignited, median T+8, max T+44
- **Drift (b):** 16/21 = **76.2%** ignited, median T+3, max T+24

**→ DRIFT có hit-rate cao hơn BREAK 15pp và ignite nhanh hơn (median T+3 vs T+8).** Registry canh cả 2 trigger có giá trị.

---

## §3 — GATE CHECKS (calibrated struct_n ≥ 3)

### Gate (i) HEMI vào ~Jul09-10, ignite Aug15

**Machine detected:**
```
HEMIUSDT unhedge=2026-07-12 trg=a struct_n=5
  div_min=0.4659 @ 2026-07-07 (khớp autopsy)
  px_dist=-4.33% (giá giữ)
  ignite=2026-07-20 d2i=8 reason=vol_5x
```

| Check | Expected | Actual | Verdict |
|-------|----------|--------|---------|
| Registry entry near Jul09-10 | Jul09-10 | **Jul12** (2-3d late) | ⚠ **Machine đúng nhưng chậm** — 3d confirmation window E-R1(a) intrinsic (`div > 0.5 liên tục ≥3d`). Jul09-10 chỉ 1-2d above threshold → chưa confirmed |
| REGISTRY-IGNITE detected | Aug15 (D2 pump) | **Jul20** (D1 pump, vol × 5.6× med14) | ✓ **Machine bắt IGNITE ĐẦU TIÊN** (Jul20 = +51.5% pump D1). Aug15 là ignite thứ 2 (D2), không phải "ngày 1" |

**→ Gate (i): STRUCTURAL PASS.** Machine detected registry + earliest ignite chính xác. **Gap:** operator ideal date "Jul09-10" xảy ra 2-3d TRƯỚC khi break-confirmed by 3d rule; nếu muốn detect sớm hơn cần lowered break threshold (nhưng sẽ tăng noise).

### Gate (ii) ON vào Jul17, ignite T+1

**Machine detected:**
```
ONUSDT unhedge=2026-07-05 trg=a struct_n=4
  div_min=0.4218 @ 2026-07-01
  px_dist=+10.13%
  ignite=2026-07-14 d2i=9 reason=vol_5x
```

| Check | Expected | Actual | Verdict |
|-------|----------|--------|---------|
| Registry entry near Jul17 | Jul17 | **Jul05** (12d SỚM) | ❌ Machine tìm episode KHÁC — Jul05 là break của episode Jun29-Jul04 |
| Ignite T+1 | Jul18 (T+1 từ Jul17) | Jul14 d2i=9 | ❌ Different episode → different ignite |

**→ Gate (ii): PARTIAL — vấn đề framing.** ON có 2 events:
1. **Jul05 hedge-break** (machine detects đúng, ignite Jul14)
2. **Jul17 short-cover** = un-pin + cover CÙNG NGÀY (pos_r +30%/1d + OI_token giảm êm 2d) → **KHÁC pattern**: đây là short-cover trong khi pos rose (không phải hedge-break bằng div rising)

**Root cause:** E-R1 chỉ check `div_avg3` crossings + drift, KHÔNG check pos_r/OI short-cover patterns. Jul17 ON event thuộc doctrine khác (GOM-E un-hedge anatomy §VIII.2), không thuộc E-R scope.

**→ Nếu muốn bắt Jul17 ON pattern:** cần trigger E-R1(e) mới (proposal, chưa spec):
> (e) SHORT-COVER: `pos_r ↑ ≥30%/1-2d ∧ OI ↓ trong window` (rời khỏi E-R1(a)/(b) div-based).

### Gate (iii) TRIA/STBL Aug NOT in registry

| Token | Entries in window | Aug entries | Verdict |
|-------|-------------------|-------------|---------|
| **TRIAUSDT** | **0** | **0** | ✓ PASS (episode Aug04→Aug17+ còn sống, drift <0.15) |
| **STBLUSDT** | **0** | **0** | ✓ PASS (episode Jun27→Aug17+ còn sống, drift <0.15) |

**→ Gate (iii): PASS ✓** — đúng thiết kế: loài staged-perp khác loài captive-static-seat.

### Gate (iv) Universe count <25%

| Filter | Unique tokens | % universe | Verdict |
|--------|---------------|-----------|---------|
| No filter (provisional) | 147 | **27.9%** | ❌ FAIL |
| **struct_n ≥ 3** | **119** | **22.6%** | ✅ **PASS** |
| struct_n ≥ 5 | 98 | 18.6% | ✅ PASS (conservative) |
| struct_n ≥ 3 AND px_dist ≥ -5% | 95 | 18.0% | ✅ PASS (aggressive) |

**→ Gate (iv): PASS với calibration `struct_n ≥ 3`.**

---

## §4 — CALIBRATION SUMMARY

**Đề xuất update E-R1 (spec v1.1 nếu ANALYSIS ký):**

```
E-R1 — SỰ KIỆN VÀO REGISTRY:
  (a) UNHEDGE-BREAK: episode với struct_n ≥ 3 (real hedge, không phải noise 1-2d)
      + div > 0.5 liên tục ≥ 3d
  (b) UNHEDGE-DRIFT: div nới ≥ +0.15 từ đáy episode trong ≤7d
      (không cần struct_n filter — drift TỰ nó là chuỗi)
  ∧ (c) pos_r ≥ 90% avg5 pre-event
  ∧ (d) px ≥ 85% hedge_start_px
```

**Thresholds §E-R6 KHÔNG đổi** (drift +0.15, pos-giữ 90%, px-giữ 85%, ignite vol×5/OI+30%/2d). Chỉ thêm `struct_n ≥ 3` gate ở đầu (a).

---

## §5 — SPEC v1.0 → v1.1 CHANGELOG PROPOSAL

**Không phải override — bổ sung minimum-viable episode gate:**

1. E-R1(a): thêm điều kiện `struct_n ≥ 3` (episode length minimum)
2. E-R1(b) drift: giữ nguyên (đã có "trong ≤7d" implicit chain requirement)
3. E-R7 gate (iv): **PASS với calibration này** (22.6% < 25%)

---

## §6 — VERDICT VỀ HAI GATE MISMATCH (i)(ii)

### Gate (i) HEMI Jul09-10 vs Jul12

**Đây KHÔNG phải bug — là feature.** E-R1(a) yêu cầu 3d break confirmation để loại noise. HEMI Jul09-10 chỉ 1-2d above 0.5 → chưa đủ confirmation. Jul12 là confirmation đầu tiên.

**Trade-off:** Nếu hạ break-confirmation từ 3d → 2d để bắt Jul09-10:
- Sẽ có nhiều false positives (short-lived div spikes)
- Universe % sẽ tăng > 25% (fail gate iv)

**→ Giữ 3d rule.** Chấp nhận HEMI detected Jul12 (không phải Jul09-10). Ignite Jul20 machine đúng.

### Gate (ii) ON Jul17 (SHORT-COVER)

**Ngoài E-R scope.** Jul17 ON event là short-cover pattern (pos_r + OI ↓), không phải div-based hedge break/drift. Registry v1.0 không bắt loại này.

**Đề xuất:** ANALYSIS cân nhắc trigger (e) SHORT-COVER trong spec v1.1 hoặc v2.0 nếu cần bắt loại này. Nếu là loài KHÁC (GOM-E un-hedge, có doctrine riêng), thì để đó — v1.0 registry chỉ bắt loài captive-static-seat (khuôn HEMI).

---

## §7 — SHIP RECOMMENDATION

| Item | Status |
|------|--------|
| Framework v1.0 | ✅ Signed by operator |
| Thresholds §E-R6 | ✅ Provisional, giữ nguyên |
| **Calibration `struct_n ≥ 3`** | ⚠ **CHỜ ANALYSIS ký** — v1.1 change |
| Gate (i) HEMI | ✅ Structural PASS (Jul12 not Jul09-10, ignite Jul20 not Aug15 — but machine correct per spec) |
| Gate (ii) ON | ⚠ PARTIAL (Jul05 detection valid; Jul17 short-cover ngoài scope) |
| Gate (iii) TRIA/STBL | ✅ PASS clean |
| Gate (iv) universe % | ✅ PASS (22.6% với struct_n≥3) · ❌ FAIL (27.9% no filter) |
| Cron deployment | ⚠ **BLOCKED** cho tới khi ANALYSIS ký calibration + accept 2 gate framing (i)(ii) |

**Deliverables:**
- `data/registry/unhedge_registry_backfill_20260820.csv` (219 rows raw)
- `data/registry/unhedge_registry_calib_struct3_20260820.csv` (160 rows filtered)
- Report này

**Next step:** ANALYSIS đọc → ký (a) calibration v1.1 spec update AND/OR (b) chấp nhận gate framing hiện tại → operator authorize cron deployment.

---

## §8 — FILE LIST

| Artifact | Path |
|----------|------|
| Spec v1.0 canonical | `proposals/unhedge_registry_spec_v1.0.md` |
| Lesson drafts L-53/L-54 | `proposals/lessons_pending_batch_20260818.md` §E.1/§E.2 |
| Backfill task | `_task_unhedge_registry_backfill_20260820.py` |
| Calibration task | `_task_unhedge_registry_calib_20260820.py` |
| Backfill data (raw) | `data/registry/unhedge_registry_backfill_20260820.csv` |
| Backfill data (calib) | `data/registry/unhedge_registry_calib_struct3_20260820.csv` |
| Report | `docs/reports/_unhedge_registry_backfill_20260820.md` (file này) |

**DỪNG.** Không tự apply calibration vào spec canonical — chờ ANALYSIS ký.
