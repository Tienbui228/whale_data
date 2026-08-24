---
type: triage-report
name: GOM-GATE-TRIAGE — 5 FAIL rows post-C1b/C1
date: 2026-08-24
status: ANALYSIS pending — bảng về ANALYSIS quyết re-baseline vs regression
signed_by: DEV (agent, chat 24/08 relay)
---

# GOM-GATE-TRIAGE — 5 pre-existing FAIL rows tách F5(a)-vol vs code-drift

**Ký:** operator ký chat 24/08 (DEV → AGENT · GOM-GATE-TRIAGE, song song PHA D).
**Không sửa expected, không sửa code — bảng về ANALYSIS.**

## Bước (1) — Store-independence check: `--backtest6` KHÔNG đọc freshwatch CSVs

**Grep code path (`scripts/gom_scan.py`):**
```
L52-53:   parse_result_file / build_days imported từ replay module (bot-signals)
L55:      CASE_DIR = BOT_ROOT / "docs" / "case study"
L1002-05: for fpath in sorted(CASE_DIR.glob("*_result.txt")):
              funding, oi, ratio, klines = parse_result_file(fpath)
              days = build_days(funding, oi, ratio, klines)
```

`_result.txt` files chứa raw funding/oi/ratio/klines FROZEN tại calib time.
- `--backtest6` mode: đọc CASE_DIR/*_result.txt (bot-signals repo) → build_days → check formulas
- `--daily` mode (khác biệt): đọc `data/export/freshwatch_daily_*.csv` (whale_data repo)

**Kết luận (1):** `--backtest6` **HOÀN TOÀN ĐỘC LẬP** với freshwatch CSVs. F5(a) rebuild vol_quote (commit 68c824d) **KHÔNG THỂ** ảnh hưởng bất kỳ FAIL nào ở --backtest6.

Không cần A/B swap CSVs (redundant — proved by code path).

**Cross-ref**: `--daily` mode (production cron 01:25 UTC) đọc freshwatch CSVs → F5(a) sẽ ảnh hưởng đó (nhưng đó không phải phạm vi triage này).

## Bước (2) — Per-row FAIL analysis

Signal vol usage grep (`bot-signals/scanner/screener/signals.py`):

| Signal | Line | Uses vol_quote? | Notes |
|--------|------|-----------------|-------|
| `lsr_accum` | L150 | ❌ NO | LSR-only |
| `hedge_structure` | L167 | ❌ NO | div_ratio (pos/acc) |
| `pos_rerate` | L181 | ❌ NO | pos_r-only |
| `funding_pinned/_strong/_unpin/_neg_div/_extreme` | L249/254/266/314/335 | ❌ NO | funding-only |
| `crowd_flush` | L362 | ❌ NO | pos_r drop |
| `stealth_grind` | L392 | ❌ NO | OI median14 + price range + taker_buy_pct |
| `s3_eve` (A5 taker_burst) | L446-465 | ✅ **YES** | vol/median14(vol) + taker |
| `oi_ignition` | L490 | ❌ NO | OI-only |

### Bảng 5 FAIL rows

| Row | Token | Episode | Expected (L976) | Actual events | Rule failing | Uses vol? | Ngày lệch | Diagnosis |
|-----|-------|---------|-----------------|---------------|--------------|-----------|-----------|-----------|
| 4 | BANK | chapter | crowd_flush 07-02 → chapter mới | 07-09 chain_open, 07-09/10 gom, 07-13 chain_closed:gom_gap>2d (no chapter event 07-02) | `crowd_flush` (§8.2 chapter rule) | ❌ NO | 07-02 expected → 0 fire | Rule không trigger trên _result.txt data — pos_r drop threshold không đạt |
| 5 | BANK | close-iv | Chain ĐÓNG 07-19~21 pos_r sập ≥30% | 07-13 chain_closed:gom_gap>2d (chain đã đóng bởi gap rule TRƯỚC 07-19) | `pos_r_drop_close` (§8.4iv) | ❌ NO | Chain closed EARLY (07-13 gap-close, không đến 07-19 pos_r-drop-close) | Gap rule (§8.1 break_gap_max=2d) trigger trước → pos_r_drop_close không có cơ hội eval |
| 6 | TAG | open | 07-12 lsr_accum + crowd_flush → chain open | 06-16→06-28 dq (age+lsr_dist), 07-05 slope_dq, 07-15/16 wrong_side+slope_dq, no chain_open | GOM-A compose (A1 lsr_accum + A2 avg5_glsr + A3 slope-fuel + A4/A5) | Partial: A5 s3_eve **YES** (nếu A5 required) | 07-12 expected → không compose | A3 slope_dq trên 07-05 → per-day DQ block. On 07-12 no compose success — lsr_accum/A2/A3/A4/A5 fail |
| 9 | BULLA | open (B-path) | stealth_grind + B-path 07-17 → GOM fires (B1+B3+B4) | 06-16→06-28 dq (age+lsr_dist), 06-24 decay+age, 07-09 wrong_side+slope_dq, no chain_open | Post-C1b: compose GOM-A only (không compose B) | Partial: stealth_grind uses OI/price/taker, không vol; hedge_base_strict B-formula ❌ NO | 07-17 expected → không có gom_day (B-only) | **EXPECTED post-C1b — B-only case, gom_day = gom_a_fire only, B rời compose. Row 9 spec obsolete post v4.0.** |
| 10 | TUT | chapter | 07-11 stealth_grind + crowd_flush → chapter mới | 06-16→06-28 dq (age), 07-16/17/18 slope_dq, no chain_open ever | Cần chain_open trước → stealth_grind (post-C1 archived) hoặc GOM-A open. Then crowd_flush. | Partial: stealth_grind ❌ NO vol · crowd_flush ❌ NO vol | 07-11 expected → 0 fire | Post-C1 stealth_grind guarded off (gomc_enabled=false). Pre-C1 cũng không fire. Compose GOM-A trên 07-11 also fail. Row 10 pre-existing v3.x FAIL. |
| 11 | IDOL | open | 07-06 lsr_accum + pos_rerate + A3-ok → GOM-A fires (A1+A2+A3+A4) | 06-16→06-28 dq (age), 07-01 wrong_side, 07-07-11 slope_dq, no chain_open | GOM-A compose (A1 lsr_accum + A2 avg5_glsr + A3 + A4 pos_rerate) | ❌ NO — A1/A2/A3/A4 all không vol | 07-06 expected → không compose | Pre-existing v3.x baseline FAIL. lsr_accum hoặc pos_rerate không đạt trên _result.txt IDOL data 07-06. |

## Bước (3) — Bảng ANALYSIS quyết

| Row | Category | Justification | ANALYSIS action needed |
|-----|----------|---------------|-------------------------|
| 4 BANK chapter | **CODE/SPEC DRIFT** | Rule (crowd_flush) không vol. F5(a) rebuild KHÔNG áp đến `_result.txt`. FAIL từ v3.x baseline. | Re-baseline OR verify crowd_flush threshold vs BANK 07-02 pos_r drop actual |
| 5 BANK close-iv | **CODE/SPEC DRIFT** (semantic overlap) | Chain closed 07-13 bởi §8.1 gap rule TRƯỚC 07-19 pos_r-drop-close. Chain-lifetime semantic: expected close-iv giả định chain open đến 07-19+, actual close-by-gap sớm. | Re-baseline: chấp nhận close-by-gap 07-13 = valid close, hoặc adjust break_gap_max |
| 6 TAG open | **CODE/SPEC DRIFT** (potential vol-drift IF A5 required) | A3 slope_dq blocks trên 07-05. On 07-12: unknown which A signal fail. A5 s3_eve dùng vol nhưng _result.txt frozen → không impact từ F5(a). | Deep-dive per-day GOM-A eval on 07-12 TAG — báo A1/A2/A3/A4/A5 individual state |
| **9 BULLA open (B-path)** | **EXPECTED post-C1b** — spec v3.x obsolete | Row 9 expected fires from B-path (B1+B3+B4). Post-C1b: gom_day = gom_a_fire only. B-only cases obsolete. | **Re-baseline REQUIRED**: Row 9 v4.0 = "gom_day KHÔNG fire · hedge_base_strict fire on B-path date" (see step 4) |
| 10 TUT chapter | **CODE/SPEC DRIFT** (stealth_grind archived) | Post-C1 stealth_grind guard off (gomc_enabled=false). Even pre-C1 was pre-existing FAIL. | Re-baseline: v4.0 expected obsolete (stealth_grind archived), remove or update |
| 11 IDOL open | **CODE/SPEC DRIFT** | Rule GOM-A no vol. Pre-existing v3.x baseline FAIL. | Deep-dive per-day GOM-A eval on 07-06 IDOL — báo A1/A2/A3/A4/A5 |

## Bước (4) — BULLA v4.0 expected draft (CHỜ KÝ, chưa ghi spec)

**OLD (v3.x, row 9 BACKTEST_GATE `scripts/gom_scan.py` L988):**
```python
("BULLA",  "open",    "stealth_grind + B-path 07-17 → GOM fires (B1+B3+B4 path)"),
```

**NEW (v4.0 draft, CHỜ OPERATOR KÝ):**
```python
("BULLA",  "hedge_base_strict", "B-path 07-08: B1 (hedge_structure ≥7d) + B3 (absorption) + B4 (funding OK) → hedge_base_strict=True (feeder §E-R tier-STRICT). gom_day KHÔNG fire (B rời compose per v4.0 GOM-RESTRUCT-20260824). stealth_grind reference removed (GOM-C archived)."),
```

**Ngày `07-08` là DRAFT** — cần operator verify:
- 07-08 = first date B-path (B1+B3+B4) fires trong BULLA _result.txt data
- Hiện tại BULLA events không hiển thị hedge_base_strict fire (backtest6 chỉ track chain_open/dq/gom, không track intermediate hedge_base_strict). Cần probe riêng để xác định first-fire date.

**Alternate approach for BULLA verification** (đề xuất, chờ ký):
- Probe `_probe_bulla_hbs_date_20260824.py` — chạy `_evaluate_day()` per day BULLA 06-15 → 08-20, capture `hedge_base_strict` field per day, list first-True date.
- Operator ký kết quả trước khi merge vào BACKTEST_GATE.

## Cross-ref

- Store-independence: `--backtest6` code path L1002-05 vs `--daily` L1151
- Signal vol usage: `bot-signals/scanner/screener/signals.py` L446-465 (s3_eve only)
- v4.0 GOM-RESTRUCT: bot-signals 8a96eacc + whale_data afbad16 (episode hai tier LOOSE/STRICT)
- C1b rename: whale_data 95e18fe (gom_b_fire → hedge_base_strict)
- C1 disable: whale_data 940b9ab + b5c0365 (GOM-C off, formatter off)
- F5(a) rebuild: whale_data 68c824d (vol_quote fresh — không áp `--backtest6`)

## Verdict tổng

- **F5(a) vol rebuild KHÔNG gây bất kỳ FAIL nào ở --backtest6** — proved by code path independence.
- **5 pre-existing FAILs = code/spec drift** (từ v3.x baseline), KHÔNG phải regression từ v4.0.
- **BULLA row 9 = EXPECTED post-C1b** — spec v3.x obsolete, draft v4.0 (chờ ký).
- **KHÔNG SỬA expected, KHÔNG SỬA code** — bảng gửi ANALYSIS quyết action.

Chờ ANALYSIS ký decision per row: re-baseline / deep-dive / accept-as-is.
