"""Vùng-rung probe: marginal zone scan across fw-filtered tokens, 60d window.

Seven thresholds checked:
  A2   avg5(gLSR)          ≤ 1.10   (GOM-A)
  A3   slope_5d            ≤ 1.15   (GOM-A)
  B1   div_avg3 per-day    ≤ 0.50   (GOM-B hedge streak input)
  C3lo taker_buy_pct       ≥ 40.0   (GOM-C provisional)
  C3hi taker_buy_pct       ≤ 55.0   (GOM-C provisional)
  quiet f_avg              ≤ 2e-4   (GOM-C C2, 8h default)
  riv  pos_r drop 30d-peak ≥ 0.30   (chain-close rule-iv)
  Q2d  div_avg3            ≥ 3.00   (Q2 manual gate display)

For each (token, day, threshold) where |value − threshold| < ε:
  (a) changed-outcome: flipping changes GOM-A fire (only A2/A3 — fully computable)
  (b) harmless: outcome unchanged

ε ∈ {0.005, 0.01, 0.02}

data-source: scratch/freshwatch_daily_2026-0{6,7,8}.csv (local)
machine: local scratch
date-range: 2026-06-10 → 2026-08-09
code-commit: see git log
"""
from __future__ import annotations
import sys, io, csv, math
from pathlib import Path
from collections import defaultdict, deque

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

SCRATCH   = Path(r"D:\Data back test\whale_data\scratch")
EPSILONS  = [0.005, 0.01, 0.02]
DATE_FROM = "2026-06-10"   # 60d back from 08-09 + buffer for rolling windows
DATE_TO   = "2026-08-09"

# ── Load freshwatch CSVs ──────────────────────────────────────────────────────
def load_fw(months):
    rows = []
    for mo in months:
        p = SCRATCH / f"freshwatch_daily_{mo}.csv"
        if not p.exists():
            print(f"  WARN: {p.name} missing"); continue
        with open(p, encoding="utf-8") as f:
            rows.extend(csv.DictReader(f))
    return rows

all_rows = load_fw(["2026-06", "2026-07", "2026-08"])
print(f"Loaded {len(all_rows)} freshwatch rows")

def sf(v, d=None):
    try: return float(v) if v not in (None, "", "None", "nan") else d
    except: return d

# ── Build per-symbol ordered day list ────────────────────────────────────────
sym_days: dict[str, list[dict]] = defaultdict(list)
for r in all_rows:
    d = r.get("date", "")
    if d < DATE_FROM or d > DATE_TO:
        continue
    sym_days[r["symbol"]].append(r)

for sym in sym_days:
    sym_days[sym].sort(key=lambda r: r["date"])

# Filter: ≥30 data rows in window → "fw-filtered" threshold
MIN_ROWS = 30
filtered = {s: v for s, v in sym_days.items() if len(v) >= MIN_ROWS}
print(f"Symbols with ≥{MIN_ROWS} rows in window: {len(filtered)}")

# ── Signal helpers ────────────────────────────────────────────────────────────
def _vals(buf, field, n):
    """Last n non-None values of field from deque."""
    vals = [v[field] for v in list(buf)[-n:] if v.get(field) is not None]
    return vals

def avg3_ratio(pos_vals, acc_vals):
    """div_avg3 = avg3(pos_r) / avg3(acc_r). None if insufficient."""
    if len(pos_vals) < 3 or len(acc_vals) < 3:
        return None
    ap = sum(pos_vals[-3:]) / 3
    aa = sum(acc_vals[-3:]) / 3
    if aa <= 0: return None
    return ap / aa

# ── Threshold definitions ─────────────────────────────────────────────────────
# (name, threshold, pass_dir, group, counterfactual_group)
#   pass_dir: "le" (value ≤ threshold) or "ge" (value ≥ threshold)
#   cf_group: "gom_a" if changed-outcome computable, else "display"
THRESHOLDS = [
    ("A2",   1.10,  "le", "gom_a"),
    ("A3",   1.15,  "le", "gom_a"),
    ("B1",   0.50,  "le", "gom_b"),    # per-day input to streak — no full cf
    ("C3lo", 40.0,  "ge", "gomc"),
    ("C3hi", 55.0,  "le", "gomc"),
    ("quiet",2e-4,  "le", "gomc"),
    ("riv",  0.30,  "ge", "chain"),
    ("Q2d",  3.00,  "ge", "display"),
]

# ── Main scan ─────────────────────────────────────────────────────────────────
# Per-threshold, per-epsilon accumulators
# marginal_events: list of (token, date, value, threshold, pass_before, pass_after_flip, gom_a_before, gom_a_after)
thresh_events: dict[str, list[dict]] = {t[0]: [] for t in THRESHOLDS}

for sym, days in filtered.items():
    # Rolling buffers
    pos_buf  = []   # lsr_pos_r
    acc_buf  = []   # lsr_acc_r
    gsr_buf  = []   # lsr_global_r
    oi_buf   = []   # oi_usd
    px_buf   = []   # px_avg (for ret_1d)

    for i, row in enumerate(days):
        dt = row["date"]
        pos_r  = sf(row.get("lsr_pos_r"))
        acc_r  = sf(row.get("lsr_acc_r"))
        gsr    = sf(row.get("lsr_global_r"))
        oi_usd = sf(row.get("oi_usd"))
        taker  = sf(row.get("taker_buy_pct"))
        f_avg  = sf(row.get("funding_avg"))
        px     = sf(row.get("px_avg"))

        # Scale taker fraction → pct
        if taker is not None and taker <= 1.0:
            taker *= 100.0

        pos_buf.append(pos_r)
        acc_buf.append(acc_r)
        gsr_buf.append(gsr)
        oi_buf.append(oi_usd)
        px_buf.append(px)

        # ── Compute signals ──
        # div_avg3
        pos_v = [v for v in pos_buf[-3:] if v is not None]
        acc_v = [v for v in acc_buf[-3:] if v is not None]
        if len(pos_v) == 3 and len(acc_v) == 3:
            ap = sum(pos_v) / 3; aa = sum(acc_v) / 3
            div_avg3 = ap / aa if aa > 0 else None
        else:
            div_avg3 = None

        # A1: div_avg3 ≥ 1.5
        a1 = div_avg3 is not None and div_avg3 >= 1.5

        # A2: avg5(gLSR) ≤ 1.1
        gsr_v5 = [v for v in gsr_buf[-5:] if v is not None]
        avg5 = sum(gsr_v5) / len(gsr_v5) if gsr_v5 else None
        a2_val = avg5
        a2 = avg5 is not None and avg5 <= 1.1

        # A3: slope_5d ≤ 1.15 (positional i-5)
        slope5 = None
        if i >= 5:
            g0_raw = gsr_buf[i - 5]
            g1_raw = gsr
            if g0_raw is not None and g1_raw is not None and g0_raw > 0:
                slope5 = g1_raw / g0_raw
        a3_val = slope5
        a3 = slope5 is not None and slope5 <= 1.15

        # A4: d_pos_3d ≥ 0
        if i >= 3 and pos_r is not None and pos_buf[i-3] is not None:
            d_pos = pos_r - pos_buf[i-3]
            a4 = d_pos >= 0
        else:
            a4 = False

        # A5: oi_cycle_pos ≤ 0.5
        oi_w = [v for v in oi_buf[-30:] if v is not None]
        if len(oi_w) >= 10 and oi_usd is not None:
            oi_mn, oi_mx = min(oi_w), max(oi_w)
            if oi_mx > oi_mn:
                oicp = (oi_usd - oi_mn) / (oi_mx - oi_mn)
                a5 = oicp <= 0.5
            else:
                oicp = 0.5; a5 = True
        else:
            oicp = None; a5 = False

        gom_a = a1 and a2 and a3 and (a4 or a5)

        # B1 per-day: div_avg3 ≤ 0.5 (hedge_structure per-day input)
        b1_day = div_avg3 is not None and div_avg3 <= 0.5

        # C3: taker ∈ [40, 55]
        c3lo = taker is not None and taker >= 40.0
        c3hi = taker is not None and taker <= 55.0

        # quiet: f_avg ≤ 2e-4 (8h default)
        quiet_thr = 2e-4
        quiet_pass = f_avg is not None and f_avg <= quiet_thr

        # rule-iv: pos_r drop from 30d-rolling-peak ≥ 0.30
        pos_peak_30 = max((v for v in pos_buf[-30:] if v is not None), default=None)
        if pos_r is not None and pos_peak_30 and pos_peak_30 > 0:
            riv_val = (pos_peak_30 - pos_r) / pos_peak_30
        else:
            riv_val = None
        riv_pass = riv_val is not None and riv_val >= 0.30

        # Q2-div: div_avg3 ≥ 3.0
        q2d_pass = div_avg3 is not None and div_avg3 >= 3.0

        # ── Per-threshold marginal check ──
        checks = {
            "A2":   (a2_val,   1.10,  a2,   "le"),
            "A3":   (a3_val,   1.15,  a3,   "le"),
            "B1":   (div_avg3, 0.50,  b1_day,"le"),
            "C3lo": (taker,    40.0,  c3lo, "ge"),
            "C3hi": (taker,    55.0,  c3hi, "le"),
            "quiet":(f_avg,    quiet_thr, quiet_pass, "le"),
            "riv":  (riv_val,  0.30,  riv_pass, "ge"),
            "Q2d":  (div_avg3, 3.00,  q2d_pass, "ge"),
        }

        for t_name, (val, thr, passes, direction) in checks.items():
            if val is None:
                continue
            dist = abs(val - thr)

            # Counterfactual: only for A2, A3 (fully computable gom_a cf)
            if t_name == "A2":
                a2_flip = not a2
                gom_a_cf = a1 and a2_flip and a3 and (a4 or a5)
                cf_changes = (gom_a != gom_a_cf)
            elif t_name == "A3":
                a3_flip = not a3
                gom_a_cf = a1 and a2 and a3_flip and (a4 or a5)
                cf_changes = (gom_a != gom_a_cf)
            else:
                gom_a_cf = None
                cf_changes = None   # unknown / out-of-scope

            thresh_events[t_name].append({
                "sym": sym, "date": dt, "val": val, "thr": thr,
                "dist": dist, "passes": passes, "direction": direction,
                "gom_a": gom_a, "gom_a_cf": gom_a_cf,
                "cf_changes": cf_changes,
            })

print(f"\nTotal events collected: {sum(len(v) for v in thresh_events.values())}")

# ── Build output table ─────────────────────────────────────────────────────────
print(f"\n{'='*80}")
print(f"VÙNG-RUNG ANALYSIS — fw tokens={len(filtered)}, window={DATE_FROM}→{DATE_TO}")
print(f"{'='*80}")
print(f"\nε values: {EPSILONS}")
print(f"(a) = changed-outcome (GOM-A flip); (b) = harmless or scope=display/chain")
print()

header = f"{'Condition':<8} | {'ε':>6} | {'n_marginal':>10} | {'n(a)_changed':>12} | {'n(b)_harmless':>13} | scope"
print(header)
print("-" * len(header))

# Detailed changed-outcome events per threshold (for table)
changed_detail: dict[str, list[dict]] = {t[0]: [] for t in THRESHOLDS}

for t_name, _, _, cf_scope in THRESHOLDS:
    evs = thresh_events[t_name]
    for eps in EPSILONS:
        marginal = [e for e in evs if e["dist"] < eps]
        n_total = len(marginal)
        if cf_scope == "gom_a":
            n_changed = sum(1 for e in marginal if e.get("cf_changes") is True)
            n_harmless = n_total - n_changed
            scope_label = "GOM-A"
            for e in marginal:
                if e.get("cf_changes") and eps == min(EPSILONS):
                    changed_detail[t_name].append(e)
        else:
            n_changed = 0
            n_harmless = n_total
            scope_label = cf_scope
        print(f"  {t_name:<6} | {eps:>6.3f} | {n_total:>10} | {n_changed:>12} | {n_harmless:>13} | {scope_label}")
    print()

# ── Changed-outcome events ε=0.005 ───────────────────────────────────────────
print(f"\n{'='*80}")
print(f"CHANGED-OUTCOME EVENTS (ε=0.005, GOM-A scope only)")
print(f"{'='*80}")

for t_name in ["A2", "A3"]:
    evs = [e for e in thresh_events[t_name] if e["dist"] < 0.005 and e.get("cf_changes")]
    if not evs:
        print(f"\n  {t_name}: 0 events")
        continue
    print(f"\n  {t_name} — {len(evs)} events where gom_A flips:")
    print(f"  {'Token':<20} {'Date':<12} {'Value':>10} {'Thr':>6} {'Dist':>8} {'Passes':>7} {'GOM-A':>7} {'CF_A':>7}")
    print(f"  {'-'*80}")
    for e in sorted(evs, key=lambda x: (x["date"], x["sym"])):
        pdir = "≤thr" if e["passes"] else ">thr"
        print(f"  {e['sym']:<20} {e['date']:<12} {e['val']:>10.5f} {e['thr']:>6.3f} "
              f"{e['dist']:>8.5f} {pdir:>7} {str(e['gom_a']):>7} {str(e['gom_a_cf']):>7}")

# ── Changed-outcome events ε=0.01 ─────────────────────────────────────────────
print(f"\n{'='*80}")
print(f"CHANGED-OUTCOME EVENTS (ε=0.01, GOM-A scope)")
print(f"{'='*80}")

for t_name in ["A2", "A3"]:
    evs = [e for e in thresh_events[t_name]
           if 0.005 <= e["dist"] < 0.01 and e.get("cf_changes")]
    if not evs:
        print(f"\n  {t_name}: 0 additional events in [0.005, 0.01)")
        continue
    print(f"\n  {t_name} — {len(evs)} additional events in [0.005,0.01):")
    for e in sorted(evs, key=lambda x: (x["date"], x["sym"])):
        pdir = "≤thr" if e["passes"] else ">thr"
        print(f"  {e['sym']:<20} {e['date']:<12} {e['val']:>10.5f} {e['thr']:>6.3f} "
              f"{e['dist']:>8.5f} {pdir:>7} gom_a={e['gom_a']} → {e['gom_a_cf']}")

# ── C3 / quiet / riv / Q2d — marginal count only (no cf) ─────────────────────
print(f"\n{'='*80}")
print(f"DISPLAY-ONLY / PROVISIONAL / CHAIN-RULE MARGINAL COUNTS")
print(f"{'='*80}")
print(f"(no changed-outcome — scope không compute được from fw data alone)")
print()
for t_name, thr, pdir, scope in THRESHOLDS:
    if scope in ("gom_a",):
        continue
    evs = thresh_events[t_name]
    row = [f"  {t_name:<8} thr={thr}"]
    for eps in EPSILONS:
        n = sum(1 for e in evs if e["dist"] < eps)
        row.append(f" ε={eps}: {n:>5}")
    print("  ".join(row))

# ── Summary: fragility ranking ────────────────────────────────────────────────
print(f"\n{'='*80}")
print(f"FRAGILITY RANKING (GOM-A scope, ε=0.005, by n_changed_outcome)")
print(f"{'='*80}")

ranked = []
for t_name in ["A2", "A3"]:
    evs = thresh_events[t_name]
    n_changed = sum(1 for e in evs if e["dist"] < 0.005 and e.get("cf_changes"))
    n_total   = sum(1 for e in evs if e["dist"] < 0.005)
    n_days    = sum(1 for e in evs if e["date"] >= "2026-08-01" and e["dist"] < 0.005 and e.get("cf_changes"))
    ranked.append((t_name, n_changed, n_total, n_days))

ranked.sort(key=lambda x: -x[1])
for t_name, n_ch, n_tot, n_aug in ranked:
    pct = n_ch / n_tot * 100 if n_tot > 0 else 0
    print(f"  {t_name}: {n_ch} changed / {n_tot} marginal ({pct:.0f}%)  Aug-01 onward: {n_aug}")

# ── Token fragility leaderboard ───────────────────────────────────────────────
print(f"\n{'='*80}")
print(f"TOKEN FRAGILITY (A2+A3 combined, ε=0.005, changed-outcome events)")
print(f"{'='*80}")

tok_counts: dict[str, int] = defaultdict(int)
for t_name in ["A2", "A3"]:
    for e in thresh_events[t_name]:
        if e["dist"] < 0.005 and e.get("cf_changes"):
            tok_counts[e["sym"]] += 1

if tok_counts:
    for tok, cnt in sorted(tok_counts.items(), key=lambda x: -x[1])[:30]:
        print(f"  {tok:<22} {cnt} event(s)")
else:
    print("  (none at ε=0.005)")

# ── Aug-01 specific check (P0 root cause) ─────────────────────────────────────
print(f"\n{'='*80}")
print(f"AUG-01 MARGINAL CHECK (P0 root cause validation)")
print(f"{'='*80}")
for t_name in ["A2", "A3"]:
    aug_evs = [e for e in thresh_events[t_name] if e["date"] == "2026-08-01"]
    if not aug_evs:
        print(f"  {t_name}: no data on 2026-08-01"); continue
    print(f"  {t_name} on 2026-08-01 ({len(aug_evs)} tokens):")
    for e in sorted(aug_evs, key=lambda x: x["dist"]):
        cf_label = f"→cf={e['gom_a_cf']}" if e.get("cf_changes") is not None else ""
        print(f"    {e['sym']:<22} val={e['val']:.5f} dist={e['dist']:.5f} "
              f"passes={e['passes']} gom_a={e['gom_a']} {cf_label}")

print(f"\nProbe complete. Tokens={len(filtered)}, total events={sum(len(v) for v in thresh_events.values())}")
