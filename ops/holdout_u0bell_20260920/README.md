# ops/holdout_u0bell_20260920/ · README

**Hold-out window:** 2026-09-20 → 2026-10-20 (30 ngày · A3.2 registration)
**Directory naming:** `20260920` = hold-out window START date · **KHÔNG phải snapshot date**
**Snapshot chụp tại:** `2026-09-23T00:57:52Z` (R0 · git_sha `6af9359498a7`)
**Snapshot lần 2 (S5 roster):** `2026-09-23T01:14Z` (git_sha sau BC/AZ commits)

## Purpose

Đóng băng CODE + DATA + ROSTER cho U0-BELL tại thời điểm chụp · làm neo cho:
- R3 SHADOW HARNESS (S1) · chứng minh byte-identical mọi SCP trong window
- R4 sổ đã-nhìn · md5 trước/sau mỗi touch
- R5 baseline 33.4% audit trail

## Files (md5 pinned)

| file | md5 | vai trò |
|------|-----|---------|
| u0_bell.py.snap | `baa8f525a8c03c2d183351f7fe64ba8c` | U0-BELL calculator (dacc_bwd thresholds) |
| u0_bell_audit.py.snap | `2ab17d49ef1d3ef6fcc668cdf1685e77` | audit runner + collect_audit() |
| events_build.py.snap | `2a6ab5a578e91e8d2b3483347faf7b59` | events orchestrator (emit bell/class/u1/btier) |
| **b_state_tracker.py.snap** | `b422d88e8898bb02fbaae782ba5b5e51` | **U0-CLASS classifier + B-tier state tracker · KHÔNG phải roster builder** |
| u0_class_tier.py.snap | `08bbbbd08c86fa68ea1173ec8e1fb87c` | shared L1/L2/L3/BLIND classifier lib (AW-α' α1) |
| events_2026-09-20_legacy_ledger.jsonl.snap | `29915ce7f6e7f3b10bb9afd7039cfef9` | LEGACY star ledger (data/logs/event_ledger/) · schema khác · KHÔNG có U0-BELL rows |
| events_2026-09-20_artifacts.jsonl.snap | `ae150ca18688def3b0490d412adbd24a` | NEW events_build.py output (data/artifacts/) · có U0-BELL rows |
| roster_2026-09-20.txt | `a67c667b93624645049f2ff48b936896` | 222 tokens = fw_universe (228) ∩ data_at_target (524) |
| roster_daily.py.snap | `7d5ce81904259b295e90dd6f37e305ac` | S5 · roster builder canonical (NEW) · scripts/roster_daily.py |

## Roster builder clarification (S5)

**b_state_tracker.py = U0-CLASS + B-tier state tracker** (build_b_state, _check_u0_class_L1, _check_u1_v2v1, _find_latest_cross). **KHÔNG phải roster builder.**

**Roster builder canonical = `scripts/roster_daily.py`** (S5 · added 23/09):
- Formula: `fw_universe ∩ data_at_target`
- Output: `data/state/roster_<date>.txt + .md5`
- Usage: `python3 scripts/roster_daily.py --target <YYYY-MM-DD>`

## Shadow harness (S1)

- **Location:** `shadow_run/` subdir
- **Scripts:** copies of *.snap files at `shadow_run/scripts/`
- **PATCH runtime** (documented): `sys.path.insert(0, '$SHADOW_SCRIPTS')` inserted AFTER prod insert trong shadow's events_build.py để shadow imports win. Snap file md5 giữ pristine.
- **Cleanup rule:** `rm -rf scripts/__pycache__` trước mỗi mutation run (Python .pyc cache đề phòng)
- **Entry:** `PYTHONPATH=$(pwd)/scripts python3 scripts/events_build.py --target <T> --out-dir data_out`

## Reports

- `R0_R5_report_20260923.md` · vòng 1 · R0/R2/R4/R5 (23/09 00:57)
- `S1_S5_report_20260923.md` · vòng 2 · S1/S2/S3/S4/S5 (23/09 01:14)

## Ranh giới hold-out

- KHÔNG chạm code U0/events_build/collector acc/pos/div trong window
- Mọi touch phải log vào `docs/holdout_u0bell_touch_log.md` (R4)
- KHÔNG chạy `compute_night_verdict` không `--dry` (§KỶ-LUẬT #11)
