# G1 State-per-Day Replay — 12 Calibration Cases
Generated: 2026-08-06T07:25:20Z

**State machine §6 master plan:**
- NONE → WATCH(B) → HOT(A) → ARMED → SUPPRESSED
- Priority: SUPP > ARMED > HOT > WATCH > NONE
- STRUCTURE_LOOKBACK=7d, SUPPRESSOR_COOLDOWN=14d, HOT_HYSTERESIS=14d

**Tier A (HOT):** lsr_accum new onset · stealth_grind/s3_eve new · pos_rerate on hedge backdrop · funding_unpin on pinned+lsr_accum
**Tier B (WATCH):** lsr_accum/hedge_structure alive · funding_pinned_strong · crowd_flush · absorption · oi_ignition alone
**ARMED:** ≥2 structure signals alive (7d) + ≥1 timing tell today + no suppressor
**SUPPRESSED:** any suppressor in last 14d → overrides all bullish

## State-per-Day Matrix

```
  date |    BANK     AKE     TAG     BAS   POWER   BASED     CLO     BTW     TUT   BULLA ESPORTS    IDOL
-------------------------------------------------------------------------------------------------------
 06-19 |    NONE    NONE    NONE    NONE    NONE    NONE    NONE    NONE    NONE    NONE    SUPP    NONE
 06-20 |    NONE    NONE    NONE    NONE    NONE    NONE    NONE    NONE    NONE    NONE    SUPP    NONE
 06-21 |    NONE    NONE    NONE    NONE    NONE    NONE    NONE    SUPP    NONE    NONE    SUPP    NONE
 06-22 |    NONE    NONE    NONE    NONE    NONE    NONE    NONE    SUPP    NONE    NONE    SUPP    NONE
 06-23 |    NONE    NONE    NONE    NONE    NONE    NONE    NONE    SUPP    NONE    NONE    SUPP    NONE
 06-24 |    NONE    NONE    NONE    NONE    NONE    NONE    NONE    SUPP    NONE    SUPP    SUPP    NONE
 06-25 |   WATCH    NONE   WATCH    NONE    NONE    NONE    NONE    SUPP    NONE    SUPP    SUPP   WATCH
 06-26 |   WATCH    NONE   WATCH    NONE    NONE    NONE    NONE    SUPP    NONE    SUPP    SUPP   WATCH
 06-27 |   WATCH    NONE   WATCH    NONE   WATCH    NONE    NONE    SUPP    NONE    SUPP    SUPP   WATCH
 06-28 |   WATCH    NONE   WATCH    NONE   WATCH    NONE    NONE    SUPP    NONE    SUPP    SUPP   WATCH
 06-29 |     HOT    NONE   WATCH    NONE   WATCH    NONE    NONE    SUPP   WATCH    SUPP    SUPP   WATCH
 06-30 |   WATCH    NONE   WATCH    NONE   WATCH    NONE    NONE    SUPP   WATCH    SUPP    SUPP   WATCH
 07-01 |   WATCH    NONE   WATCH    NONE   WATCH   WATCH    NONE    SUPP   WATCH    SUPP    SUPP   WATCH
 07-02 |   ARMED    NONE   WATCH    SUPP   WATCH     HOT    NONE    SUPP   WATCH    SUPP    SUPP   WATCH
 07-03 |   ARMED   WATCH   WATCH    SUPP   WATCH   WATCH    NONE    SUPP   WATCH    SUPP    SUPP   WATCH
 07-04 |   ARMED   WATCH   WATCH    SUPP   WATCH   WATCH   WATCH    SUPP   WATCH    SUPP    SUPP   WATCH
 07-05 |   ARMED   WATCH   WATCH    SUPP   WATCH   WATCH   WATCH    SUPP   WATCH    SUPP    SUPP   WATCH
 07-06 |   ARMED   WATCH   WATCH    SUPP   WATCH    NONE   WATCH    SUPP   WATCH    SUPP    SUPP   ARMED
 07-07 |   ARMED   WATCH   WATCH    SUPP   WATCH    NONE   WATCH    SUPP   WATCH    SUPP    SUPP   ARMED
 07-08 |   ARMED    SUPP   WATCH    SUPP   WATCH   WATCH   WATCH    SUPP   WATCH   WATCH    SUPP   ARMED
 07-09 |   ARMED    SUPP   WATCH    SUPP   WATCH    NONE   WATCH    SUPP   WATCH   WATCH    SUPP   ARMED
 07-10 |   ARMED    SUPP   WATCH    SUPP   WATCH    NONE   WATCH    SUPP   WATCH   WATCH    SUPP   ARMED
 07-11 |   ARMED    SUPP   WATCH    SUPP   WATCH    NONE   WATCH    SUPP     HOT   WATCH    SUPP   ARMED
 07-12 |   ARMED    SUPP   ARMED    SUPP   WATCH   WATCH     HOT    SUPP   WATCH   WATCH    SUPP   ARMED
 07-13 |   ARMED    SUPP   ARMED    SUPP   WATCH   WATCH   WATCH    SUPP   WATCH   WATCH    SUPP   ARMED
 07-14 |   ARMED    SUPP   ARMED    SUPP   WATCH   WATCH    SUPP    SUPP   WATCH   WATCH    SUPP   ARMED
 07-15 |   ARMED    SUPP   ARMED    SUPP   WATCH   WATCH    SUPP    SUPP   WATCH   WATCH    SUPP   ARMED
 07-16 |   ARMED    SUPP   ARMED   WATCH   WATCH   WATCH    SUPP    SUPP   WATCH   WATCH    SUPP   ARMED
 07-17 |   ARMED    SUPP   ARMED   WATCH   WATCH   WATCH    SUPP    SUPP   WATCH     HOT    SUPP   ARMED
 07-18 |   ARMED    SUPP   ARMED   WATCH   WATCH   WATCH    SUPP    SUPP   WATCH   WATCH    SUPP   ARMED
 07-19 |   ARMED    SUPP   ARMED   WATCH   WATCH   WATCH    SUPP    SUPP   WATCH   WATCH    SUPP   ARMED
 07-20 |   ARMED    SUPP   ARMED   WATCH   WATCH   WATCH    SUPP    SUPP   WATCH     HOT    SUPP   ARMED
 07-21 |   ARMED    SUPP   ARMED   WATCH   WATCH   WATCH    SUPP    SUPP   WATCH   WATCH    SUPP   ARMED
```

## Validation Checks

### (a) State 20/07 vs twelve_cases_reference.md ±1 tolerance

| Token | Computed | Reference | |Diff| | Result |
|-------|----------|-----------|--------|--------|
| BANK | ARMED | HOT | 1 | PASS |
| AKE | SUPP | HOT | 2 | FAIL |
| TAG | ARMED | ARMED | 0 | PASS |
| BAS | WATCH | WATCH | 0 | PASS |
| POWER | WATCH | WATCH | 0 | PASS |
| BASED | WATCH | WATCH | 0 | PASS |
| CLO | SUPP | SUPP | 0 | PASS |
| BTW | SUPP | SUPP | 0 | PASS |
| TUT | WATCH | HOT | 1 | PASS |
| BULLA | HOT | HOT | 0 | PASS |
| ESPORTS | SUPP | SUPP | 0 | PASS |
| IDOL | ARMED | ARMED | 0 | PASS |

### (b) Transition timelines TAG / BANK

**TAG:**
```
  06-19: START → NONE     [(no signal)]
  06-25:  NONE → WATCH    [funding_pinned]
  07-12: WATCH → ARMED    [crowd_flush, oi_ignition, lsr_accum]
```

**BANK:**
```
  06-19: START → NONE     [(no signal)]
  06-25:  NONE → WATCH    [absorption]
  06-29: WATCH → HOT      [absorption, lsr_accum]
  06-30:   HOT → WATCH    [absorption, lsr_accum]
  07-02: WATCH → ARMED    [absorption, lsr_accum, crowd_flush]
```

### (c) ESPORTS 07-19 = SUPPRESSED → PASS
- funding_extreme fires 07-19 (climax suppressor). stealth_grind + oi_ignition also fire but SUPP overrides all bullish. ✓

### (d) BTW 07-02..05 = SUPPRESSED

- BTW 07-02: SUPP → PASS  signals=['post_climax', 'lsr_accum']
- BTW 07-03: SUPP → PASS  signals=['post_climax', 'lsr_accum']
- BTW 07-04: SUPP → PASS  signals=['post_climax', 'lsr_accum']
- BTW 07-05: SUPP → PASS  signals=['post_climax', 'lsr_accum']

## Overall: HAS FAILURES — 1 case (AKE) — yaml threshold proposal required

## Root Cause Analysis

### BAS — FIXED by episode-based cooldown (state layer code change)
- `post_climax` embeds its own 14d cooldown internally (signals.py lines 601-609).
  It scans back cooldown+1=15 days; correct behavior.
- Old G1 state machine: rolling 14d window on TOP of signal → total = crash_day + 28d (doubled!)
- Fix: episode-based SUPP check. Crash on 07-02 (−27.4%). Episode starts 07-02.
  14d from episode_start → SUPP 07-02..07-15. From 07-16: episode expired; same continuous
  streak doesn't re-trigger. BAS 07-20 = WATCH ✓. PASS.
- **Code change:** `supp_ep + supp_last` per-suppressor tracking replaces rolling window.
  Fires within same consecutive streak don't extend the 14d once it started.

### AKE — FAIL (yaml threshold issue, NOT replay bug)
- `decay` fires 07-08 for AKE. Episode start = 07-08. SUPP 07-08..07-20. AKE = SUPP on 07-20.
- **Investigation:** AKE taker 07-04..07-08 = [47.3, 41.7, 45.9, 46.4, 47.9]
  - yaml `decay.taker_buy_max = 48.0%` (NOT 45.0% as the signal comment says)
  - All 5 values < 48.0 → decay fires GENUINELY under current yaml
  - This is NOT a replay/input bug
- **Root cause:** `decay.taker_buy_max: 48.0` is more permissive than spec intent ('taker <45% kéo dài').
  AKE was at accumulation bottom (07-08 = eve of flash-crash/liftoff), not in genuine decay.
  The 48.0% threshold catches AKE pre-pump taker plateau incorrectly.
- **Fix required:** `proposals/yaml_change_decay_20260806.md` — change taker_buy_max 48.0→45.0
  with 12-case regression + changelog. Operator sign-off needed. Out of G1 gate scope.
- **G1 result:** AKE = 1 remaining FAIL. diff=2 (SUPP vs HOT ref).

## State machine implementation notes (v2 — episode-based SUPP)

- **SUPP:** Episode-based (14d from first-fire of episode). Same consecutive streak doesn't extend.
  Gap ≥1d then new fire after episode expired = new episode. This correctly handles `post_climax`
  which already embeds 14d cooldown — prevents double-counting.
- **ARMED:** Stateful, persists 30d (§6 'expiry 30d'). lsr_accum must be one of the ≥2 structures.
- **HOT:** Tier A new onset only (14d hysteresis).
- **Priority:** SUPP > ARMED > HOT > WATCH > NONE.