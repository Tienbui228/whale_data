# HOLD-OUT U0-BELL · registration doc · DRAFT · CHƯA PIN

**Trạng thái:** **NHÁP** · CHƯA PIN md5 · chờ DEV chuyển C9/C10 + nguyên văn Q1-Q6, P1-P4, C5-C8.
**Ngày ghi:** 2026-09-23
**Cửa sổ chính thức:** **2026-09-21 → 2026-10-20** (30 ngày · A3.2 registration)
  - 09-20: **chỉ mô tả** (KHÔNG có as-ran · trước cửa sổ chính thức)
  - 09-21: **vào cửa sổ** · V5a bytes md5 canonical=`2f41f23f8bd306d500695c7bdb449cff` (byte-identical shadow≡prod)
  - 09-22: **vào cửa sổ** · shadow từ code R0 · prod chưa sinh (cron 23/09 01:35 UTC)

**Nguyên tắc pin:** khi DEV OK C9/C10 + copy verbatim Q/P/C → pin md5 file này ngay · **KHÔNG sửa sau đó** · sửa = file mới + lý do.

---

## 1 · Nguyên văn ANALYSIS phán (chỗ trống chờ DEV verbatim)

### Q1-Q6

> **[PENDING DEV VERBATIM · Q1 · Q2 · Q3 · Q4 · Q5 · Q6]**
> Agent chưa có bản Q · DEV chuyển vào đây khi ký.

### P1-P4 pins

> **[PENDING DEV VERBATIM · P1 · P2 · P3 · P4]**

### C5 (a có điều kiện), C6, C7 (từng đêm), C8 (a/b/c)

> **[PENDING DEV VERBATIM · C5(a có điều kiện) · C6 · C7 (từng đêm) · C8 (a/b/c)]**

### C9 công thức · C10 ngày chấm

> **[PENDING DEV · C9 công thức · C10 ngày chấm]**
> Đây là hai chỗ trống cuối phải điền TRƯỚC khi pin R1 md5.

### Nền episode theo dải

> **[PENDING · điền trước 21/10 · không đổi sau]**
> Agent đo được nền TOKEN-NIGHT (V3.c bucket rates): <0.3=11.36% · 0.3-0.4=24.33% · 0.4-0.5=53.67%.
> Nền EPISODE (gộp 14d) chưa đo · V6 tiếp theo · KHÔNG in precision chuông trong doc này (thứ tự bắt buộc R1 trước V6).

---

## 2 · Chuẩn hoá so sánh (agent measurable · đã đo)

**Filter U0-BELL rows:** `type ∈ {bell, bell_blind, bell_near}` · sort key `(tok, D, type)` · drop `computed_at` (varies per run).

**Đếm loại (chỉ đếm loại nào ghi rõ):**
- `type=bell` = full BELL fire (dacc ≤ threshold BELL_MAX)
- `type=bell_near` = NEAR (threshold_bell < dacc ≤ threshold_near)
- `type=bell_blind` = BLIND (acc data missing)

**File events chuẩn:** `data/artifacts/events_<T>.jsonl` (NEW events_build.py output)

**File legacy đối chứng:** `data/logs/event_ledger/events_<T>.jsonl` · md5 09-20=`29915ce7f6e7f3b10bb9afd7039cfef9` (star ledger · schema khác · KHÔNG có U0-BELL rows · 0 matches type=bell)

---

## 3 · md5 pinned bộ đóng băng R0 (23/09 00:57:52 UTC · git_sha=`6af9359498a7`)

| item | md5 | path snapshot |
|------|-----|---------------|
| u0_bell.py | `baa8f525a8c03c2d183351f7fe64ba8c` | ops/holdout_u0bell_20260920/u0_bell.py.snap |
| u0_bell_audit.py | `2ab17d49ef1d3ef6fcc668cdf1685e77` | ops/holdout_u0bell_20260920/u0_bell_audit.py.snap |
| events_build.py | `2a6ab5a578e91e8d2b3483347faf7b59` | ops/holdout_u0bell_20260920/events_build.py.snap |
| b_state_tracker.py | `b422d88e8898bb02fbaae782ba5b5e51` | ops/holdout_u0bell_20260920/b_state_tracker.py.snap |
| lib/u0_class_tier.py | `08bbbbd08c86fa68ea1173ec8e1fb87c` | ops/holdout_u0bell_20260920/u0_class_tier.py.snap |
| roster_daily.py | `7d5ce81904259b295e90dd6f37e305ac` | ops/holdout_u0bell_20260920/roster_daily.py.snap |
| roster_2026-09-20.txt (222 tokens) | `a67c667b93624645049f2ff48b936896` | ops/holdout_u0bell_20260920/roster_2026-09-20.txt |
| events_2026-09-20_legacy_ledger.jsonl | `29915ce7f6e7f3b10bb9afd7039cfef9` | ops/holdout_u0bell_20260920/events_2026-09-20_legacy_ledger.jsonl.snap |
| events_2026-09-20_artifacts.jsonl | `ae150ca18688def3b0490d412adbd24a` | ops/holdout_u0bell_20260920/events_2026-09-20_artifacts.jsonl.snap |

## 4 · md5 probe files

| item | md5 | path |
|------|-----|------|
| _probe_ao_20260918.py (baseline gốc AO2/AO3) | `d840135ca65420e6a8322dae57839666` | root repo |
| _probe_v3_baseline_instrumented_20260923.py (V3 instrumented) | `0ac206841dc711241676bf380f25ef84` | root repo |
| _probe_s1_shadow_diff_20260923.py (S1 shadow diff) | `62392a4121c643535ac8f492bea7849a` | root repo |
| _probe_v5a_bell_bytediff_20260923.py (V5a byte diff) | `2a1a1b010e466b3038574e15bd2fedfc` | root repo |

## 5 · Đêm 09-21 · byte-identical evidence (§17)

**V5a:** U0-BELL rows (bell/bell_blind/bell_near) byte-identical giữa:
- shadow R0 events_build md5=`2a6ab5a5` (post-α1)
- prod events_build md5=`154eb6d2` (pre-α1)

md5 canonical (sorted, no computed_at): `2f41f23f8bd306d500695c7bdb449cff` · **n_rows=7** · empty diff -u.

## 6 · Đêm 09-22 · code R0 · prod chưa sinh

Shadow events_2026-09-22.jsonl md5=`ee71db39016cd3424e5b2070ad8547c1` (run 23/09 01:13:43 UTC · code R0 frozen).

Prod artifacts: **CHƯA SINH** (cron 23/09 01:35 UTC chưa chạy khi ghi). V5c defer sau cron.

## 7 · Ranh giới hold-out

- **KHÔNG chạm** code U0/events_build/collector acc/pos/div trong cửa sổ 21/09 → 20/10
- **KHÔNG** run `compute_night_verdict` không `--dry` (§KỶ-LUẬT #11)
- **CÓ** log mọi touch vào `docs/holdout_u0bell_touch_log.md` (R4)
- Regen events artifacts được coi là touch · phải log

## 8 · Pin condition

**Pin md5 R1 khi ĐỦ:**
- ✓ md5 R0 snapshot pinned (Section 3)
- ✓ md5 probes pinned (Section 4)
- ✗ Q1-Q6 verbatim (Section 1 · [PENDING])
- ✗ P1-P4 verbatim (Section 1 · [PENDING])
- ✗ C5-C8 verbatim (Section 1 · [PENDING])
- ✗ C9 công thức (Section 1 · [PENDING])
- ✗ C10 ngày chấm (Section 1 · [PENDING])
- ✗ Nền episode theo dải (Section 1 · [PENDING V6])

**Trạng thái hiện tại:** 3/9 điều kiện xong · 6/9 chờ DEV/V6 · **KHÔNG PIN**.

Sau khi DEV chuyển hết chữ → pin `hashlib.md5(this_file.encode('utf-8')).hexdigest()` · ghi vào cuối doc · từ đó KHÔNG sửa.
