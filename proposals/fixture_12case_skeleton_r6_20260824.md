# R6 fixture skeleton — 12-case (calib hậu-regen-v2) + 8-case proven (CASE_*.xlsx)

**Status:** DRAFT SKELETON — golden values embedded, chờ operator ký pin.
**Ngày soạn:** 2026-08-24
**Companion sha stack:** RE-PIN 69b2e2d · R1 434f954 · ⑨-FIX 330d683 · ⑩-AMENDMENT 41d8d717 (bot-signals) · R4-v2 b400b5fc (bot-signals) + 5a3acd3 (whale_data) · ③-IMPL 4b21251 · (5)+(5b) code a594115 · KÝ LƯỢT CUỐI 3f46e6d · backfill proposal ed1fa16.

## Vocabulary

**Cause-tag v0 (chốt ⑩-AMENDMENT KÝ LƯỢT CUỐI 24/08):**

| tag | ý nghĩa | acceptance |
|---|---|---|
| `RÌA-TRÁI` | Store data thiếu history đầu window (lookback insufficient) | Expected, accept |
| `WARMUP` | ⑨-FIX N/A-WARMUP sentinel — B1 fail-closed khi lookback thiếu | Expected, accept |
| `(v)-taker-lineage` | Runtime store legacy derive r/(1+r) vs calib k[10]/k[7] fresh | TỒN TẠI cho đến khi backfill lịch sử taker ký riêng (proposal `backfill_taker_lich_su_20260824.md`) |
| `KHÁC` | **0 required** — xuất hiện = bug thật, DỪNG rule | Block merge |

## Hai họ fixture

### Họ CALIB (12-case bot-signals _result.txt post-regen-v2 canonical k[10]/k[7])

**Pin md5 hậu-regen-v2 (từ `docs/reports/resulttxt_regen_v2_changelog_20260824.md`):**

| # | file | token | md5 hậu-regen | backup |
|---|---|---|---|---|
| 1 | `BANK_result.txt` | BANK | `32b6d018...` (full trong changelog) | `.bak_pre_R4_20260824` |
| 2 | `TAG_result.txt` | TAG | `a85c5285...` | `.bak_pre_R4_20260824` |
| 3 | `bas_result.txt` | BAS | `7d66dacb...` | `.bak_pre_R4_20260824` |
| 4 | `based_result.txt` | BASED | `6be11f36...` | `.bak_pre_R4_20260824` |
| 5 | `btw_result.txt` | BTW | `74a09a92...` | `.bak_pre_R4_20260824` |
| 6 | `bulla_result.txt` | BULLA | `17bc51de...` | `.bak_pre_R4_20260824` |
| 7 | `clo_result.txt` | CLO | `084655e1...` | `.bak_pre_R4_20260824` |
| 8 | `esport_result.txt` | ESPORTS | `0dfb8638...` | `.bak_pre_R4_20260824` |
| 9 | `idol_result.txt` | IDOL | `f7f8d297...` | `.bak_pre_R4_20260824` |
| 10 | `power_result.txt` | POWER | `23238e1c...` | `.bak_pre_R4_20260824` |
| 11 | `tut_result.txt` | TUT | `888f6461...` | `.bak_pre_R4_20260824` |
| 12 | `ake_result.txt` | AKE | (unchanged, no RATIO block; ④ accept) | — |

**Ref pin:** `data/reference/case_lsr_ref_20260824.csv` md5 `7de16e7e...` (operator ký 24/08, k[10]/k[7] canonical mapping).

**Fresh source pin:** `data/reference/klines_taker_daily_20260824.csv` (987 rows × 12 tokens × 116 dates, aggregated từ VPS klines_1h).

### Họ RUNTIME (8-case proven — CASE_*.xlsx với header col 5 `taker_buy_pct`)

**8 file legacy (chưa có basis note trong header — Nhóm B (0)a):**

| # | file | md5 hiện tại (chưa touch) | schema note |
|---|---|---|---|
| 1 | `CASE_BANK.xlsx` | `9179c51e...` (từ pin trong BACKTEST_GATE row 4) | col 5 `taker_buy_pct` (legacy) |
| 2 | `CASE_BR.xlsx` | TBD | (same legacy) |
| 3 | `CASE_CLO.xlsx` | TBD | (same legacy) |
| 4 | `CASE_IDOL.xlsx` | TBD | (same legacy) |
| 5 | `CASE_TAG.xlsx` | TBD | (same legacy) |
| 6 | `CASE_TUT.xlsx` | TBD | (same legacy) |
| 7 | `CASE_XPIN.xlsx` | TBD | (same legacy) |
| 8 | `CASE_ZBT.xlsx` | TBD | (same legacy) |

**Migration policy:** header rebuild sau collector migrate deploy (forward-only) — operator territory. Fixture skeleton chỉ ghi nhận md5 hiện tại + schema note, KHÔNG chạm CASE.

## Golden values (BACKTEST_GATE rows post KÝ LƯỢT CUỐI)

**Fixture golden CHỜ ký pin:**

| row | token | episode | expected | actual (backtest6 verified 3f46e6d) |
|---:|---|---|---|---|
| 1 | _FORMULA | gom_a_fire | GOM-A = A1∧A2∧A3∧(A4∨A5) | verified (code) |
| 2 | _FORMULA | hedge_base_strict | B1∧(B2∨B3)∧B4 | verified (code, ⑨ warmup sentinel) |
| **3** | **BANK** | **open** | **Chain mở 07-10 hậu-regen-v2** | **PASS (07-10)** ✓ |
| **4** | **BANK** | **pre_chain_crowd_flush** | **crowd_flush 07-03 pre_chain (③ IMPL 4b21251)** | **PASS (07-03)** ✓ |
| **5** | **BANK** | **close-iv** | **Close 07-14 GAP-RULE + post_close_iv 07-16** | **PASS (07-14 gom_gap>2d)** ✓ |
| 6 | TAG | not-open | Correct rejection (A4+A5 fail) | PASS ✓ |
| 7 | BAS | SUPP | 07-02→07-15 post_climax | PASS ✓ |
| 8 | BTW | SUPP | 06-21→07-05 post_climax | PASS ✓ |
| **9-calib** | **BULLA** | **hbs-two-legs (calib regen-v2)** | **HBS 07-05→09 (5d) + 07-11→14 (4d) = 9d, first=07-05** | **PASS (9/9 first=07-05)** ✓ |
| 10 | TUT | ARCHIVED-chapter | SKIP (superseded) | SKIP ✓ |
| 11 | TUT | a-negative | GOM-A 0 fires | PASS ✓ |
| 12 | IDOL | not-open | A2 correct rejection | PASS ✓ |
| 13 | AKE | SUPP | 07-08→07-20 decay | PASS ✓ |
| **17-runtime** | **BULLA** | **registry_tier_STRICT_feeder** | **5d B-path store (07-08 + 07-11→14)** | tier-STRICT via feeder (v)-taker-lineage 4d residual |

**Divergence hai họ (chốt):**
- Row 9 calib: `first=07-05, windows 07-05→09 (5d) + 07-11→14 (4d) = 9d`
- Row 17 runtime: `first=07-08, 5d B-path`
- Cause-tag: `(v)-taker-lineage 4 ngày` (07-05/06/07/09) — TỒN TẠI cho đến backfill

## Skeleton runner

```
python scripts/gom_scan.py --backtest6  # họ calib (12-case _result post-regen-v2)
python _probe_registry_hbs_feeder_20260824.py  # họ runtime (registry tier-STRICT — IMPL PENDING)
python tests/test_conformance.py  # L-58 (registry+watchlist trên fixture data_snapshot_20260824/)
```

## L-58 conformance pin

Fixture `tests/fixtures/registry_conformance_20260821.json` (post RE-PIN 69b2e2d) đã pin:
- md5 data snapshot in-tree: 06 `5cb3761e...`, 07 `4179ddbf...`, 08 `1f3023e7...`
- Golden episodes/events/watchlist per 7 tokens (window 06-20 → 08-23)
- 5/5 PASS ổn định qua toàn stack sha.

## Cause-tag test coverage (mandatory)

Fixture output MỌI residual per (row, day) PHẢI có nhãn ∈ {RÌA-TRÁI, WARMUP, (v)-taker-lineage}. Nhãn `KHÁC` xuất hiện = block merge.

Cross-ref: `_probe_4_bang_kylut_cuoi_20260824.py` (archive) implement classifier tự động — dùng làm skeleton cho fixture runner v2.

## CHỜ OPERATOR KÝ PIN

Sau ký pin R6 skeleton:
1. Fixture golden values đông cứng (SIGNED).
2. Consumer L-58 gate mở rộng: check calib row 3/4/5/9 + runtime row 17 + cause-tag vocabulary.
3. Trigger regen v3 pending backfill taker (nếu ký scope A/B).
4. R5 F5c-ext deploy VPS: `scripts/vol_guard_daily.py --enable-lsr-oi` cron 01:15 UTC hoặc 01:15/01:20 combined.

## R5 F5c-ext deploy note

- Code added scripts/vol_guard_daily.py (this commit).
- CLI: `--enable-lsr-oi` flag PROVISIONAL 2% tolerance.
- First run in DRY-RUN mode để in phân bố `|r-1|` per metric (lsr_pos/lsr_acc/lsr_global/oi_hist).
- Sau phân bố observed → operator ký tolerance thực tế thay PROVISIONAL 2%.
- Cron deploy đề xuất: `15 1 * * *` (01:15 UTC, trước vol-guard vol-only 01:15 cùng slot, có thể merge một call `--enable-lsr-oi`).
- SCP + verify cron log sáng mai (2026-08-25 sau 01:20 UTC).
