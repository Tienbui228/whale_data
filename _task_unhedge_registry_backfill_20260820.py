"""_task_unhedge_registry_backfill_20260820.py
E-R7 backfill: 60d fw-139 universe → detect UNHEDGE events per E-R1 rules.
Applies E-R1 conditions (a) OR (b) + (c) + (d), computes REGISTRY-IGNITE per E-R3.

Window: 2026-06-20 → 2026-08-19 (60 days).
Universe: freshwatch symbols (all 527 covered symbols; report fw-139 subset separately if needed).

Gates E-R7:
  (i) HEMI vào ~Jul09-10, ignite Aug15
  (ii) ON vào ~Jul17, ignite T+1
  (iii) TRIA/STBL NOT in Aug (still hedged)
  (iv) <25% universe (<132 of 527) in registry over 60d
"""
import sys, io, csv
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
from datetime import date as _date, timedelta
from collections import defaultdict
from statistics import median

ROOT = Path(r"D:\Data back test\whale_data")
EXPORT = ROOT / "data" / "export"
OUT_CSV = ROOT / "data" / "registry" / "unhedge_registry_backfill_20260820.csv"
OUT_CSV.parent.mkdir(parents=True, exist_ok=True)

WINDOW_START = "2026-06-20"
WINDOW_END = "2026-08-19"

# ── Load freshwatch data ──
print("Loading freshwatch_daily 2026-06/07/08 …")
by_token = defaultdict(dict)  # symbol → {date: row dict}
n_rows = 0
for month in ["2026-05","2026-06","2026-07","2026-08"]:
    fp = EXPORT / f"freshwatch_daily_{month}.csv"
    if not fp.exists(): continue
    with open(fp, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            sym = row.get("symbol","").upper()
            d_str = row.get("date","")[:10]
            if not sym or not d_str: continue
            # only rows with LSR data
            try:
                pos_r = float(row.get("lsr_pos_r") or 0)
                acc_r = float(row.get("lsr_acc_r") or 0)
                if not pos_r or not acc_r: continue
            except: continue
            by_token[sym][d_str] = {
                "date": d_str,
                "px": float(row.get("px_avg") or 0),
                "vol": float(row.get("vol_quote") or 0),
                "oi": float(row.get("oi_usd") or 0),
                "f_avg": float(row.get("funding_avg") or 0),
                "pos_r": pos_r,
                "acc_r": acc_r,
                "gLSR": float(row.get("lsr_global_r") or 0),
                "taker_ratio": float(row.get("taker_ratio") or 0),
            }
            n_rows += 1
print(f"  {len(by_token)} tokens, {n_rows} rows loaded")

# ── For each token: compute div_avg3, detect episodes, apply E-R1 ──
def safe(v, w=6, p=3):
    return f"{v:>{w}.{p}f}" if isinstance(v, (int, float)) else " "*w

def analyze_token(sym, days_dict):
    """
    Returns list of registry entries for this token.
    """
    all_dates = sorted(days_dict.keys())
    if len(all_dates) < 10: return []  # need enough history

    # Filter to window (need earlier for div_avg3 lookback, so include ≥5d before window start)
    # Get all dates from before window (for computing baselines)
    d0 = _date.fromisoformat(WINDOW_START) - timedelta(days=5)
    filtered_dates = [d for d in all_dates if _date.fromisoformat(d) >= d0]
    if len(filtered_dates) < 3: return []

    # Compute div_avg3
    div_avg3 = {}
    for i, d in enumerate(filtered_dates):
        if i < 2: continue
        p3 = []; a3 = []
        for j in range(i-2, i+1):
            r = days_dict.get(filtered_dates[j])
            if r:
                p3.append(r["pos_r"]); a3.append(r["acc_r"])
        if len(p3) == 3 and len(a3) == 3:
            aa = sum(a3)/3
            if aa > 0:
                div_avg3[d] = round((sum(p3)/3) / aa, 4)

    # Detect episodes: div_avg3 ≤ 0.5. Track episode start/end/min
    episodes = []
    cur_ep = None
    days_below_after = 0
    for d in filtered_dates:
        if d not in div_avg3: continue
        v = div_avg3[d]
        if v <= 0.5:
            if cur_ep is None:
                cur_ep = {"start": d, "end": d, "min_v": v, "min_d": d, "vals": [(d, v)]}
            else:
                cur_ep["end"] = d
                cur_ep["vals"].append((d, v))
                if v < cur_ep["min_v"]:
                    cur_ep["min_v"] = v; cur_ep["min_d"] = d
            days_below_after = 0
        else:
            if cur_ep is not None:
                days_below_after += 1
                cur_ep["vals"].append((d, v))
                if days_below_after >= 3:
                    # break confirmed at 3d above 0.5
                    cur_ep["break_confirmed_at"] = d
                    episodes.append(cur_ep)
                    cur_ep = None
                    days_below_after = 0
    if cur_ep:
        episodes.append(cur_ep)  # ongoing at end

    # Apply E-R1 per day within window
    entries = []
    win_start_d = _date.fromisoformat(WINDOW_START)
    win_end_d = _date.fromisoformat(WINDOW_END)
    for d_str in filtered_dates:
        d = _date.fromisoformat(d_str)
        if d < win_start_d or d > win_end_d: continue
        if d_str not in div_avg3: continue
        v = div_avg3[d_str]

        # Find current or most recent episode
        rel_ep = None
        for ep in episodes:
            if ep["start"] <= d_str <= ep.get("break_confirmed_at", ep["end"]):
                rel_ep = ep; break
            if ep.get("break_confirmed_at") and ep["break_confirmed_at"] <= d_str:
                # check if within reasonable "post-episode" window (say 30d)
                gap_days = (d - _date.fromisoformat(ep["break_confirmed_at"])).days
                if gap_days <= 30 and (rel_ep is None or ep["break_confirmed_at"] > rel_ep.get("break_confirmed_at","")):
                    rel_ep = ep

        if rel_ep is None: continue

        # Check (a) UNHEDGE-BREAK
        trigger_a = False
        if rel_ep.get("break_confirmed_at") == d_str:
            trigger_a = True

        # Check (b) UNHEDGE-DRIFT: within 7d prior div_avg3 min, current div ≥ min + 0.15
        trigger_b = False
        # Get last 7d div_avg3 values within same episode's active period
        lookback_start = d - timedelta(days=7)
        recent_within_ep = []
        for (dd, vv) in rel_ep["vals"]:
            dd_d = _date.fromisoformat(dd)
            if lookback_start <= dd_d < d and vv <= 0.5:
                recent_within_ep.append((dd, vv))
        if recent_within_ep:
            recent_min = min(vv for _, vv in recent_within_ep)
            if v >= recent_min + 0.15 and v <= 0.5:
                trigger_b = True

        if not (trigger_a or trigger_b):
            continue

        # Check (c) pos_r ≥ 90% avg5 pre-event
        pre_dates = []
        for j in range(1, 6):
            prev_d = (d - timedelta(days=j)).isoformat()
            if prev_d in days_dict:
                pre_dates.append(days_dict[prev_d]["pos_r"])
        if len(pre_dates) < 3: continue
        avg5_pre = sum(pre_dates) / len(pre_dates)
        pos_r_event = days_dict[d_str]["pos_r"]
        trigger_c = pos_r_event >= 0.9 * avg5_pre

        # Check (d) px ≥ 85% hedge_start_px
        hedge_start_r = days_dict.get(rel_ep["start"], {})
        hedge_start_px = hedge_start_r.get("px", 0)
        px_event = days_dict[d_str]["px"]
        trigger_d = hedge_start_px > 0 and px_event >= 0.85 * hedge_start_px

        if trigger_c and trigger_d:
            entries.append({
                "symbol": sym,
                "unhedge_date": d_str,
                "trigger": "a" if trigger_a else "b",
                "unhedge_px": round(px_event, 8),
                "hedge_start": rel_ep["start"],
                "hedge_start_px": round(hedge_start_px, 8),
                "episode_end": rel_ep["end"],
                "div_min": rel_ep["min_v"],
                "div_min_date": rel_ep["min_d"],
                "struct_n": sum(1 for _, vv in rel_ep["vals"] if vv <= 0.5),
                "div_avg3_event": v,
                "pos_r_event": round(pos_r_event, 4),
                "avg5_pos_pre": round(avg5_pre, 4),
                "pos_ratio_vs_avg5": round(pos_r_event/avg5_pre, 4),
                "px_dist_pct": round((px_event/hedge_start_px - 1) * 100, 2) if hedge_start_px > 0 else None,
            })

    # De-dup consecutive drift entries (only keep first drift per episode)
    dedup = []
    seen_ep = set()
    for e in entries:
        key = (sym, e["hedge_start"], e["trigger"])
        if e["trigger"] == "b" and key in seen_ep:
            continue
        dedup.append(e)
        if e["trigger"] == "b":
            seen_ep.add(key)

    # Add IGNITE detection: for each entry, look forward to find ignite date
    # IGNITE: vol ≥5× med14 OR OI +30%/2d
    for e in dedup:
        event_d = _date.fromisoformat(e["unhedge_date"])
        # look forward up to 90d
        for k in range(1, 91):
            check_d = (event_d + timedelta(days=k)).isoformat()
            r = days_dict.get(check_d)
            if not r: continue
            # med14: last 14d before check_d
            vol14 = []
            for j in range(1, 15):
                pd = (event_d + timedelta(days=k-j)).isoformat()
                if pd in days_dict:
                    vol14.append(days_dict[pd]["vol"])
            if not vol14: continue
            med14 = median(vol14)
            vol_ok = r["vol"] >= 5 * med14 if med14 > 0 else False
            # OI +30%/2d
            oi_ok = False
            prev2_d = (event_d + timedelta(days=k-2)).isoformat()
            if prev2_d in days_dict and days_dict[prev2_d]["oi"] > 0:
                oi_ratio = r["oi"] / days_dict[prev2_d]["oi"]
                if oi_ratio >= 1.3:
                    oi_ok = True
            if vol_ok or oi_ok:
                e["ignite_date"] = check_d
                e["days_to_ignite"] = k
                e["ignite_reason"] = "vol_5x" if vol_ok else "oi_30_2d"
                break

    return dedup

# ── Run across universe ──
print(f"\nRunning E-R1 detection for {len(by_token)} tokens (window {WINDOW_START}→{WINDOW_END})…")
all_entries = []
for sym in sorted(by_token.keys()):
    entries = analyze_token(sym, by_token[sym])
    all_entries.extend(entries)

print(f"  Total registry entries: {len(all_entries)}")
n_break = sum(1 for e in all_entries if e["trigger"] == "a")
n_drift = sum(1 for e in all_entries if e["trigger"] == "b")
n_ignited = sum(1 for e in all_entries if "ignite_date" in e)
print(f"    trigger (a) UNHEDGE-BREAK: {n_break}")
print(f"    trigger (b) UNHEDGE-DRIFT: {n_drift}")
print(f"    ignited within 90d: {n_ignited}")

# ── Save CSV ──
fields = ["symbol","unhedge_date","trigger","unhedge_px","hedge_start","hedge_start_px",
          "episode_end","div_min","div_min_date","struct_n","div_avg3_event",
          "pos_r_event","avg5_pos_pre","pos_ratio_vs_avg5","px_dist_pct",
          "ignite_date","days_to_ignite","ignite_reason"]
with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
    w.writeheader()
    for e in all_entries: w.writerow(e)
print(f"\nWritten: {OUT_CSV}")

# ── E-R7 GATE CHECKS ──
print("\n" + "="*70)
print("E-R7 GATE CHECKS")
print("="*70)

def find_entries(sym):
    return [e for e in all_entries if e["symbol"] == sym]

# Gate (i) HEMI ~Jul09-10 in registry, ignite Aug15
print("\n(i) HEMI vào ~Jul09-10, ignite Aug15")
hemi = find_entries("HEMIUSDT")
if hemi:
    for e in hemi:
        print(f"  HEMI entry: unhedge_date={e['unhedge_date']} trigger={e['trigger']} "
              f"hedge_start={e['hedge_start']} div_min={e['div_min']} @ {e['div_min_date']} "
              f"struct_n={e['struct_n']} · ignite={e.get('ignite_date','none')} "
              f"days_to_ignite={e.get('days_to_ignite','-')} reason={e.get('ignite_reason','-')}")
    dates = [e["unhedge_date"] for e in hemi]
    ignites = [e.get("ignite_date") for e in hemi if e.get("ignite_date")]
    gate_i_registry = any("2026-07-08" <= d <= "2026-07-12" for d in dates)
    gate_i_ignite = any(ig and "2026-08-14" <= ig <= "2026-08-17" for ig in ignites)
    print(f"  → GATE (i): registry near Jul09-10={gate_i_registry} · ignite near Aug15={gate_i_ignite}")
else:
    print("  ⚠ HEMI: NO ENTRIES DETECTED — GATE (i) FAIL")

# Gate (ii) ON ~Jul17, ignite T+1
print("\n(ii) ON vào ~Jul17, ignite T+1")
on = find_entries("ONUSDT")
if on:
    for e in on:
        print(f"  ON entry: unhedge_date={e['unhedge_date']} trigger={e['trigger']} "
              f"hedge_start={e['hedge_start']} div_min={e['div_min']} @ {e['div_min_date']} "
              f"struct_n={e['struct_n']} · ignite={e.get('ignite_date','none')} "
              f"days_to_ignite={e.get('days_to_ignite','-')}")
    dates = [e["unhedge_date"] for e in on]
    dti = [e.get("days_to_ignite") for e in on if e.get("days_to_ignite") is not None]
    gate_ii_registry = any("2026-07-15" <= d <= "2026-07-19" for d in dates)
    gate_ii_ignite_near = any(d in (1, 2, 3) for d in dti)
    print(f"  → GATE (ii): registry near Jul17={gate_ii_registry} · ignite T+1..T+3={gate_ii_ignite_near}")
else:
    print("  ⚠ ON: NO ENTRIES DETECTED — GATE (ii) FAIL")

# Gate (iii) TRIA/STBL Aug NOT in registry
print("\n(iii) TRIA/STBL Aug KHÔNG vào registry (episode còn sống)")
for sym in ["TRIAUSDT", "STBLUSDT"]:
    entries = find_entries(sym)
    aug_entries = [e for e in entries if e["unhedge_date"].startswith("2026-08")]
    print(f"  {sym}: total entries={len(entries)}, Aug entries={len(aug_entries)}")
    for e in aug_entries:
        print(f"    ! {e['unhedge_date']} trigger={e['trigger']} — unexpected in Aug")

# Gate (iv) <25% universe (<132 of ≤527)
unique_tokens_in_registry = len(set(e["symbol"] for e in all_entries))
universe_size = len(by_token)
pct = unique_tokens_in_registry / universe_size * 100
print(f"\n(iv) Universe count check: {unique_tokens_in_registry}/{universe_size} = {pct:.1f}%")
print(f"  → GATE (iv): {'PASS' if pct <= 25 else 'FAIL (thresholds loãng, calib lại)'}")

# ── Top 20 entries preview ──
print("\n" + "="*70)
print("SAMPLE — 20 entries đầu (sorted by unhedge_date)")
print("="*70)
print(f"{'symbol':<15} {'unhedge_date':<12} {'trg':>3} {'div_event':>9} {'div_min':>7} "
      f"{'struct':>6} {'pos_ratio':>9} {'px_dist%':>8} {'ignite':<12} {'d2i':>3}")
for e in sorted(all_entries, key=lambda x: x["unhedge_date"])[:25]:
    print(f"{e['symbol']:<15} {e['unhedge_date']:<12} {e['trigger']:>3} "
          f"{e['div_avg3_event']:>9.4f} {e['div_min']:>7.4f} "
          f"{e['struct_n']:>6d} {e['pos_ratio_vs_avg5']:>9.4f} "
          f"{str(e['px_dist_pct'] or '-'):>8} {str(e.get('ignite_date','-')):<12} "
          f"{str(e.get('days_to_ignite','-')):>3}")

print("\n[DONE backfill]")
