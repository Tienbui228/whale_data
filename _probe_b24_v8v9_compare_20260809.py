"""B2.4: V8 vs V9 gom_state comparison.
Checks:
  1. All tokens present in v8 are present in v9 (no drops)
  2. Chain classification unchanged: rule-iv, supp, gap categories
  3. Anchor: PARTI, ZBT, BANK — rule-iv classification bất động
  4. VWAP changes: tokens that now show [vw-vol] vs oi_weighted
  5. Gross/net M4 fields present in v9 (new fields)
"""
import json, math
from pathlib import Path

V8 = Path("data/gom_state_v8_backup.json")
V9 = Path("data/gom_state_v9.json")

def load(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)

v8 = load(V8)
v9 = load(V9)

def cat(ch):
    reason = ch.get("close_reason", "")
    if (ch.get("close_note") == "chuyen pha phan phoi"
            or "pos_r_drop" in reason
            or ch.get("retro_tag")):
        return "rule-iv"
    if "suppressor" in reason or "dq_cooldown" in reason:
        return "supp"
    if ch.get("chain_open"):
        return "open"
    return "gap"

def vwap_tier(ch, rep_frac=0.05):
    vd   = ch.get("vwap_den", 0.0)
    ois  = ch.get("oi_start_usd", 0.0) or 0.0
    t1ok = vd > 0 and (ois <= 0 or vd >= rep_frac * ois)
    if t1ok:
        return "T1-oi_wt"
    vvd = ch.get("vwap_vol_den", 0.0)
    if vvd > 0:
        return "T2-vw-vol"
    return "N/A"

toks_v8 = set(v8.keys())
toks_v9 = set(v9.keys())

print("=" * 70)
print("B2.4 V8 vs V9 comparison")
print("=" * 70)

print(f"\n--- Token set ---")
print(f"  v8 tokens: {len(toks_v8)}")
print(f"  v9 tokens: {len(toks_v9)}")
dropped = toks_v8 - toks_v9
added   = toks_v9 - toks_v8
if dropped:
    print(f"  DROPPED from v8: {sorted(dropped)}")
else:
    print(f"  Dropped: none")
if added:
    print(f"  New in v9: {sorted(added)}")
else:
    print(f"  New: none")

print(f"\n--- Category changes ---")
changed = []
for tok in sorted(toks_v8 & toks_v9):
    c8 = cat(v8[tok])
    c9 = cat(v9[tok])
    if c8 != c9:
        changed.append((tok, c8, c9))
if changed:
    for tok, c8, c9 in changed:
        print(f"  {tok}: {c8} -> {c9}  *** CHANGE")
else:
    print(f"  No category changes: PASS")

print(f"\n--- VWAP tier changes (M2 rep-threshold) ---")
tier_changes = []
for tok in sorted(toks_v8 & toks_v9):
    t8 = vwap_tier(v8[tok])
    t9 = vwap_tier(v9[tok])
    if t8 != t9:
        vd8 = v8[tok].get("vwap_den", 0.0)
        vd9 = v9[tok].get("vwap_den", 0.0)
        ois9 = v9[tok].get("oi_start_usd", 0.0) or 0.0
        tier_changes.append((tok, t8, t9, vd8, vd9, ois9))
if tier_changes:
    print(f"  {'Token':<12} {'v8_tier':>12} -> {'v9_tier':>12} {'vwap_den':>10} {'oi_start':>10}")
    for tok, t8, t9, vd8, vd9, ois9 in tier_changes:
        print(f"  {tok:<12} {t8:>12} -> {t9:>12} ${vd9/1e3:>7.0f}k  ${ois9/1e6:>6.2f}M")
else:
    print(f"  No tier changes (expected — same calib data)")

print(f"\n--- Anchor check: PARTI / ZBT / BANK rule-iv (bat dong) ---")
anchors = ["PARTI", "ZBT", "BANK"]
for tok in anchors:
    in_v8 = tok in v8
    in_v9 = tok in v9
    if not in_v8:
        print(f"  {tok}: NOT IN v8 (not a calib token — expected)")
        continue
    c8 = cat(v8[tok])
    c9 = cat(v9[tok]) if in_v9 else "MISSING"
    ok = c8 == c9
    print(f"  {tok}: v8={c8}  v9={c9}  {'PASS' if ok else 'FAIL *** CHANGED'}")

print(f"\n--- M4 new fields present in v9 ---")
m4_fields = ["gross_adds_usd", "oi_start_usd", "oi_last_usd", "net_oi_delta_usd"]
# Sample from tokens that have chain_open=False and have GOM history
sample = [t for t, ch in v9.items() if ch.get("vwap_den", 0) > 0 or ch.get("vwap_vol_den", 0) > 0][:5]
for tok in sample:
    ch9 = v9[tok]
    has = {f: f in ch9 for f in m4_fields}
    missing = [f for f, ok in has.items() if not ok]
    if missing:
        print(f"  {tok}: MISSING M4 fields: {missing}")
    else:
        gross = ch9.get("gross_adds_usd", ch9.get("Q1_cum_usd", 0.0))
        net   = ch9.get("net_oi_delta_usd", float("nan"))
        net_s = f"${net/1e3:.0f}k" if not math.isnan(net) else "N/A"
        print(f"  {tok}: M4 fields OK (gross=${gross/1e3:.0f}k  net={net_s})")

if not sample:
    print("  (no tokens with VWAP data in v9 — only calib cases)")

print(f"\n--- GOM-C M5 fields present ---")
m5_fields = ["confirm_01"]
for tok, ch in v9.items():
    if not ch.get("chain_open"):
        continue
    if "confirm_01" not in ch:
        print(f"  {tok}: confirm_01 missing (will default False)")
        break
else:
    print("  (no open chains in v9 fresh-state calib — expected)")

print(f"\nDone. B2.4 comparison complete.")
