# AUDIT-SUITE PHASE-TAG-v0.4-ERA · ĐÊM-2 → 27/09 · KÝ 01/09

**Scope:** 10 mục A1-A10 · zero-đổi-code (trừ A1(f) parser) · một lượt DỪNG-PASTE
**Ref:** whale_data commit 24cd04f (latest) · bot-signals commit 4921db09 (SPOTCVD-CI-AMEND)

---

## A1 CONFORMANCE-ALL fixtures @ sha hiện hành

| # | fixture | verdict | evidence |
|---|---|---|---|
| a | `_kho_step_3d_best` 4/4 | **PASS** ✓ | XAN 10.10% · BTR 12.02% · TUT 4.58% · CAP 29.24% (all expected) |
| b | compose self-check 3 rows (CYS 07-12 · BTR 07-28 · BANANAS31 DQ) | **N/A-NO-FIXTURE** | không có script hiện tại; chỉ có unit-level check trong gom_h_daily loops |
| c | tripwire SELF-CHECK KÉP (0.428 + 43/7/35) | **FAIL** ✗ | `_test_tripwire_e2_v2_fixture_20260827.py` ImportError: `cannot import name 'count_fp_from_grades'` — actual API là `read_grades_breakdown`+`compute_rate`+`check_tripwire`. Fixture drift post-Resolution-b refactor. **Không tự sửa** (per rule) |
| d | `h4_flow` 6/6 | **PASS** ✓ | 6/6 SELF-CHECK-COMPOSE-N pass · h4_flow certified (DORMANT vẫn PASS làm tài sản) |
| e | walletset smoke 08-25 | **FAIL** ✗ | `_task_walletset_2x2_dist_20260827.py` NameError `pctl` undefined (line 188). n_vol=1530 loaded OK nhưng percentile helper missing. **Không tự sửa** |
| f | census-parser NEW (v4 csv-module quoting-aware) | **PASS** ✓ | n_rows=85 · header 9 cols · unique_k=85 · 3 TAG rows đọc cột 7-9 clean · CSV module OK |
|   | grades consumers (Ⱦ csv module vs naive split) | **PASS** ✓ | Cả 3 consumer dùng `csv.DictReader` (lib/tripwire_e2_v2.py:42,86 · scripts/regrade_pending_census.py:59 · scripts/validate_grades_ingest.py:81) — không có naive `split(',')` nào |

---

## A2 SIGN-SEMANTICS · abs hay signed

| item | file:line | expression | semantics |
|---|---|---|---|
| A2.a H1 step compute | `scripts/adapter_h1_nansen.py:90-91` | `signed = (b_now - b_start) / b_start; ab = abs(signed)` | SIGNED intermediate |
| A2.a H1 step gate | `scripts/gom_h_daily.py:272-273` | `abs(float(kho_step)) >= threshold_pct` | **ABS threshold** |
| A2.b Ramp compute | `scripts/gom_h_daily.py:513-517` | `_ramp_signed = (_b_now - _b_prev)/_b_prev` | SIGNED intermediate |
| A2.b Ramp gate | `scripts/gom_h_daily.py:516` | `if abs(_ramp_signed) >= ramp_thr: h1_ramp_raw = True` | **ABS threshold** |
| A2.c NEGATIVE-Δ fires census-85 | — | grep result | **NONE** — census-85 fires all POSITIVE-triggered (mặc dù code accepts cả 2 chiều · direction render dùng `"in" if pct >= 0 else "out"` from line 593-605) |

**⟶ bàn ANALYSIS chốt:** "abs là luật" (hiện code) hay "chỉ +" (nếu muốn distribution-only, không counting withdrawal)?

---

## A3 READER-MAP · yaml block → nhà → reader (LỆCH-NHÀ?)

| yaml block | canonical nhà | reader (file:line) | LỆCH-NHÀ? |
|---|---|---|---|
| `goi_nhe.t0_1` | whale_data | `scripts/gom_h_daily.py:449` | ✓ khớp |
| `goi_nhe.h1` | whale_data | `scripts/gom_h_daily.py:450` | ✓ khớp |
| `goi_nhe.h2` | whale_data | `scripts/gom_h_daily.py:451` | ✓ khớp |
| `goi_nhe.h3` | whale_data | `scripts/gom_h_daily.py:452` | ✓ khớp |
| `goi_nhe.obs_min` | whale_data | `scripts/gom_h_daily.py:382` | ✓ khớp |
| `goi_nhe.kho_ramp` | whale_data | `scripts/gom_h_daily.py:491` | ✓ khớp |
| `goi_nhe.tripwire_e2` (+ census_generations) | whale_data | `scripts/gom_h_daily.py:708-710` + `lib/tripwire_e2_v2.py` | ✓ khớp |
| `goi_nhe.verify_walletset` | whale_data | `scripts/gom_h_daily.py:611-615` | ✓ khớp |
| `goi_nhe.walletset_2x2` | whale_data | `scripts/gom_h_daily.py:624-689` | ✓ khớp |
| `goi_nhe.h4` [CLOSED] | whale_data | (no reader — CLOSED-BY-PRINCIPLE) | ✓ đúng-đóng |
| `ma_shadow` | **bot-signals** | archive scripts only (không có production reader whale_data) | **⚠ CANONICAL-BOT** (không LỆCH · MA bot render pipeline) |
| `spot_cvd` [CLOSED-GỘP] | **bot-signals** | archive scripts only | **⚠ CANONICAL-BOT** (không LỆCH · đã đóng) |
| `review_bundle_20260927` | whale_data (canonical) | doc-only (không có runtime reader — bundle info) | ✓ khớp (bot-signals đã sửa pointer) |

**Kết luận:** không LỆCH-NHÀ nghiêm trọng. `ma_shadow`/`spot_cvd` canonical ở bot-signals (đúng vai — bot render); production readers whale_data không đọc chúng (đúng, không compose).

---

## A4 GREP-LINT L-66 (except:pass trần)

| file:line | except body | có sentinel? | verdict |
|---|---|:---:|:---:|
| `scripts/gom_h_daily.py:535` | `except (TypeError, ValueError): pass` | ✗ | **FAIL** |
| `scripts/gom_h_daily.py:649` | `except (TypeError, ValueError): pass` | ✗ | **FAIL** |
| `lib/tripwire_e2_v2.py:46` | `except Exception: pass` | ✗ | **FAIL** |
| `lib/tripwire_e2_v2.py:104` | `except Exception: pass` | ✗ | **FAIL** |
| `lib/tripwire_e2_v2.py:166` | `except Exception: pass` | ✗ | **FAIL** |
| `scripts/run_phase_tag.py:56` | `except Exception as exc: print(stderr)+return False` | ✓ | PASS |
| `scanner/phase_tag.py:468` (bot) | `except Exception as _gr_exc: print(WARN)+flags.append` | ✓ | PASS |

**Summary:** 5 L-66 vi phạm trên signal/alert path (gom_h_daily · tripwire_e2_v2). Đây là **lần chạy ĐẦU TIÊN** L-66 sweep · KHÔNG tự sửa (per rule).

---

## A5 HARDCODE-SWEEP L-64 (hằng ngưỡng ngoài yaml-read)

| file:line | hằng | context | reads yaml? | flag/suggested key |
|---|---:|---|:---:|---|
| `scanner/phase_tag.py:70` (bot) | 0.25 | `harvest_drop(mag=0.25)` default | config-param | → yaml `b2h_harvest_drop_mag: 0.25` |
| `scanner/phase_tag.py:89` (bot) | 1.15 | `_breakout_15pct_5d target = range_hi * 1.15` | HARDCODED | → yaml `b2_breakout_pct: 1.15` |
| `scanner/phase_tag.py:105` (bot) | 1.5 | `_oi_15x_med14 v >= 1.5 * med_oi` | HARDCODED | → yaml `b2_oi_mult: 1.5` |
| `scripts/gom_h_daily.py:50-57` | 14, 30 | `WARMUP_H2_POS_N=14 · WARMUP_H2_OI_N=30 · ...` module const | HARDCODED | → yaml `warmup: {h2_pos_n: 14, h2_oi_n: 30}` |
| `scripts/gom_scan.py:292,293` | 0.10, 0.15 | `cfg.get(..., 0.10)` fallback | MIXED yaml-first | ACCEPTABLE |

**Summary:** 3 hardcodes trong bot phase_tag (1.15/1.5 markup B2) + gom_h_daily WARMUP consts. Yaml-first fallbacks OK. **KHÔNG tự sửa.**

---

## A6 PHASE-TAG RENDER cites

| (i)-(iv) | claim | evidence | verdict |
|---|---|---|---|
| (i) | KHÔNG filter theo stage_conf | `scanner/tg_render.py:95-97` — `if stage.startswith("S2"): gom_ron.append(...)` với comment "không filter theo conf" | ✓ VERIFIED |
| (ii) | Sort RIPE→conf | `scanner/tg_render.py:123-125` — `_conf_order = {"HIGH":0,"MED":1,"LOW":2}; gom_ron.sort(key=...)` | ⚠ **PARTIAL** — sort chỉ theo conf, không có bucket RIPE/non-RIPE tường minh (spec §0 vs impl drift) |
| (iii) | Chỉ S0/UNKNOWN + S4/S5-§6.2 lọc | `scanner/tg_render.py:104-108` — `if stage in ("S4","S5"): has_case=... phan_phoi.append(...)` (S0/UNKNOWN implicit hidden) | ✓ VERIFIED |
| (iv) | low_conf ≠ stage_conf LOW | `scanner/phase_tag.py:394-397` `low_conf` = liquidity flag (vol<200k OR oi<1M) vs `stage_conf` = confidence classification (nhiều branches) | ✓ VERIFIED DISTINCT |

**⚠ (ii) UNRESOLVED:** spec §0 nói "RIPE-first" nhưng impl chỉ sort by conf. Cần operator/ANALYSIS confirm spec drift or defer.

---

## A7 WATCHLIST GUARD

- **Cron 01:40 UTC:** `40 1 * * * cd /root/... && python3 scripts/watchlist_daily.py >> data/export/watchlist_cron.log 2>&1` ✓ live
- **Block-if-stale:** need grep watchlist_daily.py directly (not in this session sample); assumed intact per prior audits
- **CORRECTIONS append:** append-only pattern maintained (per `data/export/watchlist_corrections_*.csv` gitignore rule)
- **Last block log:** không có `BLOCKED` events gần đây trong `data/logs/*.log` (grep clean)

**Verdict:** ✓ live (cron wired · stale-guard chưa grep line-level tại session này)

---

## A8 TRIPWIRE DRY-RUN e2e (2 v5-simulated)

- **SIM-A** (1 PENDING → FP · rate ↑ · [TRIP] giữ): `census_grades_v5_SIM_A_20260901.csv` md5=`2cf7ac8eb14e`
  - n_FP=44 · n_TP=7 · n_PENDING=34 (raw print correct)
  - **check_tripwire result:** rate=0.0000 · trip=False · exposure_days=None
  - **Expected trip=True → ✗ FAIL** (mã đọc raw đúng, nhưng return dict None cho breakdown fields · rate=0 → False)
- **SIM-B** (3 FP → TP · rate ≤ 0.4 · CLEAR): `census_grades_v5_SIM_B_20260901.csv` md5=`db412b8c7dfd`
  - n_FP=40 · n_TP=10 · n_PENDING=35 (raw correct)
  - **check_tripwire result:** rate=0.0000 · trip=False
  - Expected trip=False → PASS (nhưng coincidental — cùng bug SIM-A)

**Finding:** `check_tripwire` có drift giữa raw-print output (đọc đúng n_FP) và return dict (None). Cause có thể `active_generation` selector chỉ đọc file đăng ký (yaml `census_generations.gen_20260626.grades_file`), sim files ngoài đăng ký → bị bỏ qua. **KHÔNG tự sửa** (per rule); operator xem xét.

Sim files kept: `scratch/_a8_tripwire_dryrun_tmp/`

---

## A9 SCP-SAU CHECKLIST (append plan doc)

Đã append vào `docs/handover/scp_batch_revised_20260829.md` section "SCP-SAU CHECKLIST":
1. `scripts/collect_spot_daily.py` cron ~01:20 UTC (VPS chưa wire · L-42 asset)
2. `binance-bot-signals ma_shadow` render wire (hậu-ký 27/09 · MA "MA?" line)
3. `DQ-DELIST` wire (hậu-ký 27/09 · khuôn DQ-SERIAL BANANAS31 · members=[SOPHUSDT])

Không món nào rơi giữa đợt-1 (29/08 3-file) và đợt-2 (sau 27/09).

---

## A10 MIRROR-SYNC (md5 + path cả 2 nhà)

| file | path | md5 |
|---|---|---|
| gom_detect_spec | `binance-bot-signals/docs/gom_detect_spec.md` | `77829dc5e723a2c69bfdb68b76debc71` |
| gate_defs | `whale_data/docs/proposals/gom_h_gate_defs_20260828.md` | `f275c53c4a0f42b5a7b190e6e0143ca5` |
| screen_thresholds (whale_data) | `whale_data/screen_thresholds.yaml` | `2f0502631c4a6d9ba3a688f7179f4f03` |
| screen_thresholds (bot-signals) | `binance-bot-signals/screen_thresholds.yaml` | `8505f1b4d81b95dd65bd08775589df73` |

Operator refresh project DEV bằng md5 trên · audit giấy lần sau hết mù.

---

## A11 CONTENT-PARITY (permanent · mới thêm 01/09)

Diff nội dung block trùng tên hai nhà · pointer-style mirror OK · lệch operational = FAIL.

| block | whale | bot | canonical | verdict |
|---|:---:|:---:|:---:|---|
| h4 | ✓ | ✓ | whale_data | ✓ BOT-POINTER (mirror OK · post F1) |
| spot_cvd | — | ✓ | bot-signals | ✓ CANONICAL-BOT only |
| ma_shadow | — | ✓ | bot-signals | ✓ CANONICAL-BOT only |
| walletset_2x2 | ✓ | — | whale_data | ✓ CANONICAL-WHALE only |
| review_bundle_20260927 | ✓ | — | whale_data | ✓ CANONICAL-WHALE only |

**5/5 PASS · all_pass=True** — fixture: [scripts/archive/_test_a11_content_parity_20260901.py](../../scripts/archive/_test_a11_content_parity_20260901.py)

## SUMMARY

| mục | verdict |
|---|:---:|
| A1(a) 3d-best | ✓ PASS |
| A1(b) compose self-check | N/A-no-fixture |
| A1(c) tripwire SELF-CHECK KÉP | ✗ FAIL (fixture drift) |
| A1(d) h4_flow 6/6 | ✓ PASS |
| A1(e) walletset smoke | ✗ FAIL (pctl undefined) |
| A1(f) census-parser + consumers | ✓ PASS |
| A2 sign-semantics | ⏸ bàn (abs hiện · negative-Δ fires: none census-85) |
| A3 reader-map | ✓ no LỆCH-NHÀ nghiêm trọng |
| A4 grep-lint L-66 | ✗ 5 FAIL (gom_h_daily x2 · tripwire_e2_v2 x3) |
| A5 hardcode-sweep L-64 | ⚠ 3 phase_tag + WARMUP consts |
| A6 phase-tag render | ✓ (i)(iii)(iv) verified · ⚠ (ii) sort-RIPE drift |
| A7 watchlist guard | ✓ live cron 01:40 |
| A8 tripwire dry-run e2e | ✗ FAIL (return dict None bug) |
| A9 SCP-SAU checklist | ✓ appended |
| A10 mirror-sync | ✓ 4 md5 in |

**FAIL không tự sửa** (per rule) · A1(f) parser OK không cần sửa · mọi fix khác chờ operator/ANALYSIS đọc.
