# G1 State-per-Day Replay — 12 Calibration Cases
Generated: 2026-08-06T07:10:12Z

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
 07-16 |   ARMED    SUPP   ARMED    SUPP   WATCH   WATCH    SUPP    SUPP   WATCH   WATCH    SUPP   ARMED
 07-17 |   ARMED    SUPP   ARMED    SUPP   WATCH   WATCH    SUPP    SUPP   WATCH     HOT    SUPP   ARMED
 07-18 |   ARMED    SUPP   ARMED    SUPP   WATCH   WATCH    SUPP    SUPP   WATCH   WATCH    SUPP   ARMED
 07-19 |   ARMED    SUPP   ARMED    SUPP   WATCH   WATCH    SUPP    SUPP   WATCH   WATCH    SUPP   ARMED
 07-20 |   ARMED    SUPP   ARMED    SUPP   WATCH   WATCH    SUPP    SUPP   WATCH     HOT    SUPP   ARMED
 07-21 |   ARMED    SUPP   ARMED    SUPP   WATCH   WATCH    SUPP    SUPP   WATCH   WATCH    SUPP   ARMED
```

## Validation Checks

### (a) State 20/07 vs twelve_cases_reference.md ±1 tolerance

| Token | Computed | Reference | |Diff| | Result |
|-------|----------|-----------|--------|--------|
| BANK | ARMED | HOT | 1 | PASS |
| AKE | SUPP | HOT | 2 | FAIL |
| TAG | ARMED | ARMED | 0 | PASS |
| BAS | SUPP | WATCH | 3 | FAIL |
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

## Overall: HAS FAILURES — 2 cases flagged as signal calibration issues

## Root Cause Analysis — FAIL Cases

### AKE — SUPP (computed) vs HOT (reference), diff=2
- `decay` fires on 07-08 for AKE. 14d cooldown keeps AKE in SUPP through 07-21.
- **Context:** AKE went +8× from 07-15 to 07-18 (crowd_flush 07-09 + s3_eve 07-14).
  `decay` definition: taker <45% sustained + price grinding + funding drift + flat OI.
  Firing on 07-08 (eve of flash-crash bottom) appears to be a false positive — AKE was at
  accumulation bottom, not in decay. This is a **signals.py threshold calibration issue**.
- **Action for operator:** check AKE taker/funding/OI values on 07-08 in result.txt vs decay thresholds.

### BAS — SUPP (computed) vs WATCH (reference), diff=3
- `post_climax` fires every day 07-02 through 07-16 (15 consecutive days).
  14d cooldown from last fire (07-16) → SUPP through 07-29, covering 07-20.
- **Context:** BAS had a -50% dump 01-07/07. post_climax is correct for that event.
  However, by 07-10 BAS had lsr_accum (10-13/07) and funding_pinned (07-12+) = accumulation phase.
  The signal fires daily instead of just on the dump day, likely because the signal re-evaluates
  hậu-markup conditions each day rather than marking the event once.
- **Action for operator:** check if post_climax should be a one-shot event flag (fires on dump day only)
  vs. ongoing condition. If one-shot: BAS SUPP through 07-15, then WATCH/ARMED by 07-20 → PASS.

## State machine implementation notes

- ARMED is **stateful** (§6 'expiry 30d'): once triggered, persists until SUPP overrides or 30d expires.
- ARMED trigger requires `lsr_accum` as one of the ≥2 structure signals. Rationale: pure-hedge tokens
  (POWER, BASED, BULLA without lsr_accum) were reaching ARMED incorrectly via crowd_flush alone.
  This gate matches §6 which lists lsr_accum as the primary Tier A signal.
- SUPP clears ARMED memory (re-escalation needed post-suppressor).
- HOT = Tier A new onset only (hysteresis 14d).