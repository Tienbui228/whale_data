# R6 FIXTURE PIN v2 ONE-TIME — SIGNED 27/08

**Status:** SIGNED post ⑬-CLOSE + HEMI GATE PASS + 6 fix applied.
**Operator ký chat 27/08 gói cuối ⑬-CLOSE.**
**Companion:** manifest v1 `4cd6ec3` + REGEN `4e3851c2` + ①②⑪⑫ merge `b17efe8` + HEMI GATE R6 PASS.

---

## Vocabulary v1 (cause-tag)

**Post-canonical vocabulary (⑬-CLOSE):**

| tag | ý nghĩa | acceptance | count post-⑬-CLOSE |
|---|---|---|---:|
| `RÌA-TRÁI` | Store data chưa bắt đầu (date < first_seen) | expected | 11 (BULLA calib 06-16..06-26) |
| `WARMUP` | i < hedge_lb−1 (⑨ N/A-WARMUP sentinel); formula = `first_seen + max(7, 14 nếu med14) − 1` | expected | 6 (BULLA runtime 06-27..07-02) |
| `SAME` | Both HBS đồng nhất | expected | 18 |
| `(v)-taker-lineage` / `(v)-px-basis` / `(v)-basis-mixed` | Basis divergence between families | pending backfill/regen scope decision | **0** (hội tụ khép post-canonical) |
| `KHÁC` | Bug thật (block merge) | **0 required** | **0** |

## 6 fix (từ operator ký 24/08 R6 pin HOÃN) — resolved trong pin v2

| # | Fix | Status |
|---:|---|:---:|
| 1 | Paste full changelog md5 R4-v2 (thay `32b6d018...` truncated) | ✓ file `docs/reports/resulttxt_regen_v2_changelog_20260824.md` + regen-manifest changelog `20260827` |
| 2 | Unify rows 6/14 (TAG open + TAG-trap) → **1 row TAG** | ✓ Row 6 mới = TAG-trap-negative unified (bỏ row 14 duplicate) |
| 3 | Unify rows 11/14 (IDOL open + IDOL-NEG 4b) → **1 row IDOL** | ✓ Row 11 mới = IDOL-NEG 4b unified (bỏ row 14 dup) |
| 4 | Fix cross-ref TUT 10/16 → **1 row TUT unified** | ✓ Row 10 mới = TUT-A-NEG unified (bỏ row 16 dup); Row 15 giữ ARCHIVED-chapter |
| 5 | BANANAS31 re-scope (⑪) — GOM-C ARCHIVED → 2 rows re-target | ✓ Row 13 BANANAS31 a-not-open + Row 14 h-not-fire-pending |
| 6 | Row 4 thêm ref CASE_BANK md5 9179c51e per chữ ký | ✓ Row 4 đã có md5 trong BACKTEST_GATE gom_scan.py:1019 |
| Bonus | Commit case_lsr_ref (path + sha) | ✓ committed `5a3acd3` at `data/reference/case_lsr_ref_20260824.csv` md5 `7de16e7e...` |
| Bonus | Pin one-time trên giá trị hậu-backfill+canonical | ✓ this file (post ⑬-CLOSE stack: `b17efe8`) |

---

## Fixture pin v2 — 15 rows canonical numbering (chuẩn hóa từ BACKTEST_GATE)

**Snapshot pin md5:**
- `case_lsr_ref_20260824.csv` md5 `7de16e7e8838aefeea067efa71148b55` (path `data/reference/`)
- `klines_taker_daily_20260824.csv` (fresh k[10]/k[7] agg 987 rows × 12 tokens)
- L-58 `tests/fixtures/data_snapshot_20260824/freshwatch_daily_2026-{06,07,08}.csv`

**_result.txt post-regen-manifest md5 pin (from `resulttxt_regen_manifest_20260827.md`):**

| # | file | md5 pin one-time |
|---:|---|---|
| 1 | `BANK_result.txt` | `cac3b67c...` |
| 2 | `TAG_result.txt` | `07f538a2...` |
| 3 | `bas_result.txt` | `61bedc00...` |
| 4 | `based_result.txt` | `06a39cce...` |
| 5 | `btw_result.txt` | `6a8d1b05...` |
| 6 | `bulla_result.txt` | `3ec7e4a8...` |
| 7 | `clo_result.txt` | `346979f1...` |
| 8 | `esport_result.txt` | `92f352ed...` |
| 9 | `idol_result.txt` | `1404d59a...` |
| 10 | `power_result.txt` | `b617e23c...` |
| 11 | `tut_result.txt` | `a0927a8c...` |
| 12 | `ake_result.txt` | (unchanged; ④ N/A-BLOCK) |

## BACKTEST_GATE 15 rows canonical (v2 pin)

| # | Token | Episode | Expected | Provenance | Verdict |
|---:|---|---|---|---|---|
| 1 | _FORMULA | gom_a_fire | A1∧A2∧A3∧(A4∨A5) | spec §1 | verified code |
| 2 | _FORMULA | hedge_base_strict | B1∧(B2∨B3)∧B4 | spec §1 + ⑨ warmup sentinel | verified code |
| 3 | **BANK** | open | Chain mở **07-10** hậu-canonical | ② KÝ 27/08 stable | PASS (07-10) |
| 4 | **BANK** | pre_chain_crowd_flush | **07-03** pre_chain (K1 §8.4) pin CASE_BANK md5 `9179c51e` | ③-IMPL `4b21251` | PASS (07-03) |
| 5 | **BANK** | close-iv | Close **07-14** GAP-RULE + post_close_iv 07-16 | ② KÝ 27/08 stable | PASS (07-14) |
| 6 | **TAG** | trap-negative (unified 6+14) | Correct rejection: A4+A5 fail (div 2.17>0.5, oi_cycle_pos>0.5) | TAG-trap ANALYSIS + expected 07/08/26 `4d0987c` | PASS |
| 7 | BAS | SUPP | 07-02→07-15 post_climax | stable pre-24/08 baseline | PASS |
| 8 | BTW | SUPP | 06-21→07-05 post_climax | stable pre-24/08 baseline | PASS |
| 9 | **BULLA** | hbs-two-legs canonical (① re-baseline 27/08) | (i) gom_day=0; (ii) HBS 5d = 07-08, 07-11→07-14, first=07-08 | ⑬-CLOSE `b17efe8` + hai họ đồng nhất canonical | PASS (HBS 5/5 first=07-08) |
| 10 | **TUT** | a-negative (unified 10+16) | GOM-A KHÔNG fire toàn kỳ; A2 fail gLSR>1.1 (g5 min 1.64) | T4 probe 36/36 A2 fail + K2 `2cf7ab3` | PASS |
| 11 | **IDOL** | neg-4b (unified 11+14) | A2 avg5(gLSR)=1.106 border, correct rejection NEGATIVE 21/08 | IDOL-NEG 4b `21/08` | PASS |
| 12 | AKE | SUPP | 07-08→07-20 decay | stable baseline; ④ N/A-BLOCK exception cho _result | PASS |
| 13 | **BANANAS31** | a-not-open (⑪a re-target) | GOM-A KHÔNG fire toàn kỳ serial-pump | gom_detect_spec v2.1 14/08 + probe 14/08 (GOM-C ARCHIVED context) | PASS |
| 14 | **BANANAS31** | h-not-fire-pending (⑪b re-target) | GOM-H KHÔNG fire cùng kỳ | [PENDING-BUILD PHA D] adapter H1 wire | PENDING-BUILD (soft) |
| 15 | **TUT** | ARCHIVED-chapter | [ARCHIVED-expected 08/08/26 giữ lịch sử] | superseded by row 10 per K2 `2cf7ab3` | SKIP |

## Row 16 — Registry tier-STRICT feeder (họ runtime hậu-canonical)

| # | Token | Episode | Expected | Provenance | Verdict |
|---:|---|---|---|---|---|
| 16 | **BULLA** | registry_tier_STRICT_feeder | Episode 06-29→07-17 (freshwatch) nhận tier-STRICT via feeder GOM-B; HBS 5d WITHIN span | K5 fixture + ⑫-BULLA-B6-STRICT-KÝ-27/08 (spec `b17efe8`) | tier-STRICT (feeder impl `59a7a63`) |

## HEMI ANCHOR verify (GATE R6)

Rerun probe `_probe_hemi_anchor_gate_r6_20260827.py` verified:
- HEMI 1 episode 07-05→07-11 (5d) invariant vs baseline
- ⚡ 15/08 vol 48.3× (campaign-defining) TRUE
- Tier LOOSE (count_le050=5)
- GATE(i) 3 vế RE-ARM formula uses px+oi (không đọc taker) → invariant qua canonical basis change
- **GATE R6 PASS** — R6 pin eligible

## Luật no-PASS-rỗng (skeleton — nguyên văn ⑪)

> **Negative row assert trên máy ARCHIVED = tự re-target sang máy kế thừa vai, hoặc [RETIRED] có chữ ký — không tồn tại PASS-rỗng.**

## Runner

```
python scripts/gom_scan.py --backtest6                                # họ calib 15 rows
python _probe_bulla_tier_strict_20260824.py                          # họ runtime row 16
python tests/test_conformance.py                                     # L-58 5/5 PASS
```

## Cross-ref stack sha (final ⑬-CLOSE)

| Item | Sha |
|---|---|
| Manifest v1 SIGNED | `4cd6ec3` |
| VERIFY FUNDING+OI | `585acc0` |
| bot-signals REGEN 11 files + Amendment §B3 | `4e3851c2` |
| whale_data companion changelog | `f501e95` |
| ①②⑪⑫ merge | `b17efe8` |
| R6 pin v2 (this) | (post-commit) |

## SIGNED ONE-TIME

Operator ký 27/08 gói cuối ⑬-CLOSE. Fixture golden values ĐÔNG CỨNG. Consumer L-58 gate mở rộng cause-tag classifier (RÌA-TRÁI/WARMUP/(v)/KHÁC).
