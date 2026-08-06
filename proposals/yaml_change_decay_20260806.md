# Proposal: `decay.taker_buy_max` 48.0 → 45.0

**Date:** 2026-08-06  
**Author:** agent (session K2)  
**Status:** PENDING OPERATOR SIGN-OFF  
**Requires:** 12-case regression (all PASS) + changelog + operator signature before apply

---

## Motivation

G1 gate calibration (session K2) reveals that `decay.taker_buy_max = 48.0` causes AKE to be
SUPPRESSED on 07-20 (reference: HOT). This is the only remaining FAIL in the 12-case regression
after episode-based SUPP fix (11/12 PASS).

### AKE evidence

Signal `decay` fired on 07-08 for AKE. Lookback window 07-04..07-08:

| Date  | taker_buy_pct | < 48.0? | < 45.0? |
|-------|--------------|---------|---------|
| 07-04 | 47.3%        | YES     | NO      |
| 07-05 | 41.7%        | YES     | YES     |
| 07-06 | 45.9%        | YES     | NO      |
| 07-07 | 46.4%        | YES     | NO      |
| 07-08 | 47.9%        | YES     | NO      |

- Under yaml `taker_buy_max=48.0`: ALL 5 < 48.0 → `decay` fires **genuinely** (not a data/replay bug).
- Under proposed `taker_buy_max=45.0`: 07-04, 07-06, 07-07, 07-08 are ≥ 45.0 → `decay` does NOT fire.
- AKE at 07-08 was accumulation bottom, eve of flash-crash/liftoff. The 48.0% threshold incorrectly
  catches pre-pump taker plateau as "decay" — spec intent is taker persistently below 45% (exhausted
  sellers, structural decay).

### Signal intent vs threshold discrepancy

`signals.py` comment for `decay` reads: "taker_buy_pct < 45.0% kéo dài" (persistent taker < 45%).  
yaml currently has `taker_buy_max: 48.0` — 3 points higher than comment, crossing into normal
accumulation territory for many coins.

---

## Proposed change

```yaml
# thresholds.yaml — section: decay
# BEFORE
taker_buy_max: 48.0

# AFTER
taker_buy_max: 45.0
```

---

## Impact assessment

- **AKE:** decay does NOT fire 07-08 → AKE 07-20 = HOT (matches reference). Diff 0.
- **Full 12-case regression required** before applying — other tokens must not regress.
  Tokens most likely to be affected: BTW (decay fires 07-10..07-12, 07-18 — need to verify
  all still pass with 45.0), CLO (no decay fires), BULLA (decay fires 06-24).
- **BTW:** decay on 07-10..07-18 window values should be checked — BTW reference is SUPP on
  07-20 (already SUPP from post_climax episode), so even if decay no longer fires, BTW state
  should be unaffected on 07-20.

---

## Regression checklist (for operator / agent to complete before applying)

- [ ] Run `_probe_g1_state_20260806.py` with patched yaml (taker_buy_max=45.0)
- [ ] All 12 cases PASS check (a) ±1 tolerance on 07-20
- [ ] Check (b) TAG/BANK transitions unchanged
- [ ] Check (c) ESPORTS 07-19 = SUPP unchanged
- [ ] Check (d) BTW 07-02..05 = SUPP unchanged
- [ ] Generate diff of signals fired: BTW decay window [07-10..07-18] at 45.0 vs 48.0
- [ ] Append to LESSONS in CASE_INDEX.xlsx: "decay threshold 48.0 too permissive; 45.0 aligns with spec"

---

## Changelog entry (to prepend to thresholds.yaml when applied)

```
# 2026-08-06 — decay.taker_buy_max: 48.0 → 45.0
#   Reason: 48.0 caught AKE accumulation-bottom plateau as decay (false positive in G1 calib).
#   Signal comment says "< 45%" — aligned threshold with spec intent.
#   Regression: 12/12 PASS (see g1_state_per_day_20260806.md).
#   Operator: ___________________  Date: ___________
```

---

## Authoring notes

- This change is OUT OF SCOPE for G1 gate session K2. G1 gate runs against yaml-as-locked.
- G1 final result: **11/12 PASS** (AKE = 1 remaining FAIL, documented here).
- Do NOT apply this change without operator sign-off per CLAUDE.md §TẦNG HUMAN rule 2.
