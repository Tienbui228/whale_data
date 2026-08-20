"""_task_registry_c1_c4_20260820.py
[C1] Verify RE-ARM implementation status + implement per operator thresholds 14d/1.10×/1.3×
[C2] Re-run backfill on fw-139 canonical universe (scratch/freshwatch_symbols.txt)
[C3] Sweep drift threshold table + separate column: siết chỉ (b), giữ (a)
[C4] Re-grade gates on fw-139 + RE-ARM

⚠ §E-R4b v1.1 SPEC TEXT KHÔNG có trong repo (both whale_data + binance-bot-signals).
Interpretation của 3 thresholds (14d/1.10×/1.3×):
  RE-ARM criteria (PROVISIONAL — chờ operator confirm interpretation):
    Entry (từ E-R1) đã IGNITED → DORMANT
    Entry RE-ARMED (được bắn IGNITE lần 2) khi:
      (r1) ≥14d kể từ ignite_date
      (r2) price_now ≥ 1.10× local_low_since_ignite (momentum restart)
      (r3) OI_now ≥ 1.3× OI_low_since_ignite (fresh OI build)
    Cần cả 3 (AND).
"""
import sys, io, csv
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
from datetime import date as _date, timedelta
from collections import defaultdict
from statistics import median

ROOT = Path(r"D:\Data back test\whale_data")
EXPORT = ROOT / "data" / "export"
FW139 = ROOT / "scratch" / "freshwatch_symbols.txt"
OUT_DIR = ROOT / "data" / "registry"
OUT_DIR.mkdir(parents=True, exist_ok=True)

WINDOW_START = "2026-06-20"
WINDOW_END = "2026-08-19"

# RE-ARM thresholds (operator-provided §E-R4b v1.1 — spec text NOT found, interpretation PROVISIONAL)
REARM_COOLDOWN_DAYS = 14
REARM_PX_MULT = 1.10
REARM_OI_MULT = 1.30

# Base thresholds
STRUCT_N_MIN = 3
POS_GUARD = 0.90
PX_GUARD = 0.85
DRIFT_MIN_DEFAULT = 0.15  # base value

# ── [C1] RE-ARM implementation check ──
print("="*70)
print("[C1] RE-ARM implementation status check")
print("="*70)

import subprocess
grep_result = subprocess.run(
    ["grep","-l","-iE","RE-ARM|re_arm|re-arm|E-R4b","_task_unhedge_registry_backfill_20260820.py","_task_unhedge_registry_calib_20260820.py"],
    capture_output=True, text=True, cwd=str(ROOT)
)
print(f"grep RE-ARM in existing backfill probes:")
print(f"  stdout: {grep_result.stdout or '(no matches)'}")
print(f"  → RE-ARM logic: **NOT IMPLEMENTED** in registry_backfill.py")
print(f"  → Implementing per operator directive with 3 thresholds:")
print(f"    (r1) cooldown_days = {REARM_COOLDOWN_DAYS}")
print(f"    (r2) px_mult = {REARM_PX_MULT}× local_low_since_ignite")
print(f"    (r3) oi_mult = {REARM_OI_MULT}× OI_low_since_ignite")
print(f"  ⚠ §E-R4b v1.1 spec TEXT chưa merged vào gom_detect_spec.md — interpretation là PROVISIONAL.")

# ── [C2] Load fw-139 universe ──
print("\n" + "="*70)
print("[C2] fw-139 canonical universe")
print("="*70)

fw139_tokens = set()
with open(FW139, encoding="utf-8") as f:
    for line in f:
        s = line.strip().upper()
        if s and not s.startswith("#"):
            fw139_tokens.add(s)
print(f"fw-139 canonical: {len(fw139_tokens)} tokens")
print(f"  Sample first 10: {sorted(list(fw139_tokens))[:10]}")

# ── Load freshwatch data for fw-139 only ──
print(f"\nLoading freshwatch data (fw-139 subset only)…")
by_token = defaultdict(dict)
n_rows = 0
for month in ["2026-05","2026-06","2026-07","2026-08"]:
    fp = EXPORT / f"freshwatch_daily_{month}.csv"
    if not fp.exists(): continue
    with open(fp, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            sym = row.get("symbol","").upper()
            if sym not in fw139_tokens: continue
            d_str = row.get("date","")[:10]
            if not sym or not d_str: continue
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
tokens_with_data = len(by_token)
print(f"  Tokens with LSR data: {tokens_with_data}/{len(fw139_tokens)}")
print(f"  Total rows: {n_rows}")

# ── Detection function with drift_min parameterized + RE-ARM ──
def analyze_token(sym, days_dict, drift_min=DRIFT_MIN_DEFAULT, struct_n_min=STRUCT_N_MIN):
    """Returns list of entries (each may include re_arm data)."""
    all_dates = sorted(days_dict.keys())
    if len(all_dates) < 10: return []

    d0 = _date.fromisoformat(WINDOW_START) - timedelta(days=5)
    filtered = [d for d in all_dates if _date.fromisoformat(d) >= d0]
    if len(filtered) < 3: return []

    div_avg3 = {}
    for i, d in enumerate(filtered):
        if i < 2: continue
        p3, a3 = [], []
        for j in range(i-2, i+1):
            r = days_dict.get(filtered[j])
            if r: p3.append(r["pos_r"]); a3.append(r["acc_r"])
        if len(p3) == 3 and len(a3) == 3:
            aa = sum(a3)/3
            if aa > 0:
                div_avg3[d] = round((sum(p3)/3)/aa, 4)

    # Detect episodes
    episodes = []
    cur_ep = None; days_above = 0
    for d in filtered:
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
            days_above = 0
        else:
            if cur_ep is not None:
                days_above += 1
                cur_ep["vals"].append((d, v))
                if days_above >= 3:
                    cur_ep["break_confirmed_at"] = d
                    episodes.append(cur_ep); cur_ep = None; days_above = 0
    if cur_ep: episodes.append(cur_ep)

    entries = []
    win_start_d = _date.fromisoformat(WINDOW_START)
    win_end_d = _date.fromisoformat(WINDOW_END)
    for d_str in filtered:
        d = _date.fromisoformat(d_str)
        if d < win_start_d or d > win_end_d: continue
        if d_str not in div_avg3: continue
        v = div_avg3[d_str]
        rel_ep = None
        for ep in episodes:
            if ep["start"] <= d_str <= ep.get("break_confirmed_at", ep["end"]):
                rel_ep = ep; break
            if ep.get("break_confirmed_at") and ep["break_confirmed_at"] <= d_str:
                gap = (d - _date.fromisoformat(ep["break_confirmed_at"])).days
                if gap <= 30 and (rel_ep is None or ep["break_confirmed_at"] > rel_ep.get("break_confirmed_at","")):
                    rel_ep = ep
        if rel_ep is None: continue

        # Filter struct_n
        struct_n = sum(1 for _, vv in rel_ep["vals"] if vv <= 0.5)
        if struct_n < struct_n_min: continue

        # (a) break
        trigger_a = rel_ep.get("break_confirmed_at") == d_str
        # (b) drift
        trigger_b = False
        lookback_start = d - timedelta(days=7)
        recent = [(dd, vv) for dd, vv in rel_ep["vals"]
                   if lookback_start <= _date.fromisoformat(dd) < d and vv <= 0.5]
        if recent:
            recent_min = min(vv for _, vv in recent)
            if v >= recent_min + drift_min and v <= 0.5:
                trigger_b = True

        if not (trigger_a or trigger_b): continue

        # (c) pos guard
        pre_pos = []
        for j in range(1, 6):
            pd = (d - timedelta(days=j)).isoformat()
            if pd in days_dict: pre_pos.append(days_dict[pd]["pos_r"])
        if len(pre_pos) < 3: continue
        avg5_pre = sum(pre_pos)/len(pre_pos)
        pos_r_event = days_dict[d_str]["pos_r"]
        if pos_r_event < POS_GUARD * avg5_pre: continue

        # (d) px guard
        hs_r = days_dict.get(rel_ep["start"], {})
        hs_px = hs_r.get("px", 0)
        px_event = days_dict[d_str]["px"]
        if not (hs_px > 0 and px_event >= PX_GUARD * hs_px): continue

        e = {
            "symbol": sym, "unhedge_date": d_str,
            "trigger": "a" if trigger_a else "b",
            "unhedge_px": round(px_event, 8),
            "hedge_start": rel_ep["start"], "hedge_start_px": round(hs_px, 8),
            "episode_end": rel_ep["end"],
            "div_min": rel_ep["min_v"], "div_min_date": rel_ep["min_d"],
            "struct_n": struct_n, "div_avg3_event": v,
            "pos_r_event": round(pos_r_event, 4),
            "avg5_pos_pre": round(avg5_pre, 4),
            "px_dist_pct": round((px_event/hs_px - 1)*100, 2) if hs_px > 0 else None,
        }
        entries.append(e)

    # Dedup drift (keep first per episode+trigger)
    dedup = []; seen = set()
    for e in entries:
        key = (sym, e["hedge_start"], e["trigger"])
        if e["trigger"] == "b" and key in seen: continue
        dedup.append(e)
        if e["trigger"] == "b": seen.add(key)

    # Add IGNITE (first) + RE-ARM logic
    for e in dedup:
        event_d = _date.fromisoformat(e["unhedge_date"])
        # First ignite: scan forward, look for vol×5 OR OI+30%/2d
        e["ignites"] = []  # list of (date, days_to, reason)
        for k in range(1, 91):
            check_d = (event_d + timedelta(days=k)).isoformat()
            r = days_dict.get(check_d)
            if not r: continue
            vol14 = [days_dict[(event_d + timedelta(days=k-j)).isoformat()]["vol"]
                     for j in range(1, 15)
                     if (event_d + timedelta(days=k-j)).isoformat() in days_dict]
            if not vol14: continue
            med14 = median(vol14)
            vol_ok = r["vol"] >= 5 * med14 if med14 > 0 else False
            prev2 = (event_d + timedelta(days=k-2)).isoformat()
            oi_ok = False
            if prev2 in days_dict and days_dict[prev2]["oi"] > 0:
                if r["oi"] / days_dict[prev2]["oi"] >= 1.3:
                    oi_ok = True
            if vol_ok or oi_ok:
                e["ignites"].append({
                    "date": check_d, "days_to": k,
                    "reason": "vol_5x" if vol_ok else "oi_30_2d",
                    "px": r["px"], "oi": r["oi"],
                })
                # first ignite
                if not e.get("ignite_date"):
                    e["ignite_date"] = check_d
                    e["days_to_ignite"] = k
                    e["ignite_reason"] = "vol_5x" if vol_ok else "oi_30_2d"
                break  # first-only for original registry

        # RE-ARM logic (v1.1 PROVISIONAL): after first ignite, check for re-arm criteria
        # then look for SECOND ignite after re-arm
        if e.get("ignite_date"):
            first_ig_d = _date.fromisoformat(e["ignite_date"])
            first_ig_px = days_dict[e["ignite_date"]]["px"]
            first_ig_oi = days_dict[e["ignite_date"]]["oi"]

            # scan post-cooldown for RE-ARM eligibility + next ignite
            local_low_px = first_ig_px
            local_low_oi = first_ig_oi if first_ig_oi > 0 else None
            rearm_date = None
            for k in range(1, 91):
                check_d = (first_ig_d + timedelta(days=k)).isoformat()
                r = days_dict.get(check_d)
                if not r: continue
                # track locals since ignite
                if r["px"] > 0:
                    local_low_px = min(local_low_px, r["px"])
                if r["oi"] > 0 and local_low_oi:
                    local_low_oi = min(local_low_oi, r["oi"])
                elif r["oi"] > 0:
                    local_low_oi = r["oi"]
                # Check RE-ARM criteria
                if k >= REARM_COOLDOWN_DAYS and rearm_date is None:
                    px_ok = local_low_px > 0 and r["px"] >= REARM_PX_MULT * local_low_px
                    oi_ok = local_low_oi is not None and local_low_oi > 0 and r["oi"] >= REARM_OI_MULT * local_low_oi
                    if px_ok and oi_ok:
                        rearm_date = check_d
                        e["rearm_date"] = rearm_date
                        e["rearm_px_mult"] = round(r["px"]/local_low_px, 3) if local_low_px > 0 else None
                        e["rearm_oi_mult"] = round(r["oi"]/local_low_oi, 3) if local_low_oi else None

                # After RE-ARM: look for next ignite
                if rearm_date and check_d > rearm_date:
                    vol14 = [days_dict[(first_ig_d + timedelta(days=k-j)).isoformat()]["vol"]
                             for j in range(1, 15)
                             if (first_ig_d + timedelta(days=k-j)).isoformat() in days_dict]
                    if not vol14: continue
                    med14_r = median(vol14)
                    vol_ok = r["vol"] >= 5 * med14_r if med14_r > 0 else False
                    prev2 = (first_ig_d + timedelta(days=k-2)).isoformat()
                    oi_ok2 = False
                    if prev2 in days_dict and days_dict[prev2]["oi"] > 0:
                        if r["oi"] / days_dict[prev2]["oi"] >= 1.3:
                            oi_ok2 = True
                    if vol_ok or oi_ok2:
                        e["ignite2_date"] = check_d
                        e["days_to_ignite2"] = k
                        e["ignite2_reason"] = "vol_5x" if vol_ok else "oi_30_2d"
                        break
    return dedup

# ── Run baseline fw-139 with default thresholds ──
print(f"\n" + "="*70)
print("[C2] Baseline detection fw-139 (drift=0.15, struct_n≥3)")
print("="*70)
baseline = []
for sym in sorted(by_token.keys()):
    baseline.extend(analyze_token(sym, by_token[sym]))
unique_baseline = len(set(e["symbol"] for e in baseline))
print(f"Total entries: {len(baseline)} · unique tokens: {unique_baseline}/{tokens_with_data}={unique_baseline/tokens_with_data*100:.1f}%")

# save
out_p = OUT_DIR / "unhedge_registry_fw139_20260820.csv"
fields = ["symbol","unhedge_date","trigger","unhedge_px","hedge_start","hedge_start_px",
          "episode_end","div_min","div_min_date","struct_n","div_avg3_event",
          "pos_r_event","avg5_pos_pre","px_dist_pct",
          "ignite_date","days_to_ignite","ignite_reason",
          "rearm_date","rearm_px_mult","rearm_oi_mult",
          "ignite2_date","days_to_ignite2","ignite2_reason"]
with open(out_p, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
    w.writeheader()
    for e in baseline: w.writerow(e)
print(f"Written: {out_p}")

# ── HEMI RE-ARM detail ──
print("\n" + "="*70)
print("[C1] HEMI RE-ARM detail")
print("="*70)
hemi = [e for e in baseline if e["symbol"] == "HEMIUSDT"]
for e in hemi:
    print(f"\nHEMI entry: unhedge={e['unhedge_date']} trg={e['trigger']} struct_n={e['struct_n']}")
    print(f"  first ignite: {e.get('ignite_date','none')} d2i={e.get('days_to_ignite','-')} reason={e.get('ignite_reason','-')}")
    print(f"  rearm_date:   {e.get('rearm_date','NO-REARM')}")
    if e.get('rearm_date'):
        print(f"    rearm_px_mult={e['rearm_px_mult']}× · rearm_oi_mult={e['rearm_oi_mult']}×")
        print(f"    (threshold: px≥{REARM_PX_MULT}× local_low, oi≥{REARM_OI_MULT}× local_low, ≥{REARM_COOLDOWN_DAYS}d cooldown)")
    print(f"  ignite #2:    {e.get('ignite2_date','none')} d2i2={e.get('days_to_ignite2','-')} reason2={e.get('ignite2_reason','-')}")

# ── HEMI px/OI chuỗi Jul21-Aug14 to see if re-arm should have fired ──
print(f"\nHEMI px/OI chuỗi post-first-ignite (Jul21→Aug14):")
hemi_days = by_token.get("HEMIUSDT", {})
first_ig_dt = _date(2026, 7, 20)  # from HEMI autopsy
first_ig_px = hemi_days.get("2026-07-20", {}).get("px", 0)
first_ig_oi = hemi_days.get("2026-07-20", {}).get("oi", 0)
print(f"  first ignite Jul20: px={first_ig_px} oi=${first_ig_oi:,.0f}")
low_px_running = first_ig_px
low_oi_running = first_ig_oi if first_ig_oi > 0 else None
print(f"\n  {'date':<11} {'px':>9} {'oi':>10} {'px/low_px':>9} {'oi/low_oi':>9} {'days_since':>10} {'rearm?':>8}")
for k in range(1, 30):
    check_d = (first_ig_dt + timedelta(days=k)).isoformat()
    r = hemi_days.get(check_d)
    if not r: continue
    if r["px"] > 0: low_px_running = min(low_px_running, r["px"])
    if r["oi"] > 0:
        low_oi_running = min(low_oi_running, r["oi"]) if low_oi_running else r["oi"]
    px_mult = r["px"] / low_px_running if low_px_running > 0 else 0
    oi_mult = r["oi"] / low_oi_running if low_oi_running else 0
    px_ok = px_mult >= REARM_PX_MULT
    oi_ok = oi_mult >= REARM_OI_MULT
    cooldown_ok = k >= REARM_COOLDOWN_DAYS
    rearm = px_ok and oi_ok and cooldown_ok
    mark = "REARM" if rearm else ""
    print(f"  {check_d:<11} {r['px']:>9.5f} {r['oi']:>10.0f} {px_mult:>9.3f} {oi_mult:>9.3f} {k:>10d} {mark:>8}")

# ── [C3] SWEEP drift threshold ──
print("\n" + "="*70)
print("[C3] SWEEP drift threshold (fw-139)")
print("="*70)

print(f"\n  {'drift':<7} {'entries(a)':>10} {'entries(b)':>10} {'total':>7} {'tokens':>7} "
      f"{'%univ':>7} {'ig_hit':>7} {'%univ-b-only':>13}")

for drift in [0.15, 0.20, 0.25, 0.30, 0.35]:
    entries_all = []
    entries_b_only = []
    for sym in sorted(by_token.keys()):
        # full: drift = drift, struct_n = 3
        full = analyze_token(sym, by_token[sym], drift_min=drift, struct_n_min=3)
        entries_all.extend(full)
        # separator: siết chỉ (b) — filter existing baseline (a) + only (b) at this drift
        b_this_drift = [e for e in full if e["trigger"] == "b"]
        # keep baseline (a) entries
        a_from_baseline = [e for e in baseline if e["symbol"] == sym and e["trigger"] == "a"]
        entries_b_only.extend(a_from_baseline + b_this_drift)

    n_a = sum(1 for e in entries_all if e["trigger"] == "a")
    n_b = sum(1 for e in entries_all if e["trigger"] == "b")
    unique_tok = len(set(e["symbol"] for e in entries_all))
    pct = unique_tok / tokens_with_data * 100
    ig_hit = sum(1 for e in entries_all if e.get("ignite_date")) / max(len(entries_all),1) * 100

    unique_tok_b_only = len(set(e["symbol"] for e in entries_b_only))
    pct_b_only = unique_tok_b_only / tokens_with_data * 100

    marker = " ←baseline" if abs(drift - 0.15) < 0.001 else ""
    print(f"  {drift:<7} {n_a:>10d} {n_b:>10d} {len(entries_all):>7d} {unique_tok:>7d} "
          f"{pct:>6.1f}% {ig_hit:>6.1f}% {pct_b_only:>12.1f}%{marker}")

print(f"\n  (baseline: drift=0.15, struct_n≥3)")
print(f"  Cột %univ-b-only: siết chỉ ngưỡng (b) DRIFT, giữ (a) BREAK ở drift 0.15 baseline")

# ── [C4] GATE re-check with RE-ARM + fw-139 ──
print("\n" + "="*70)
print("[C4] GATE RE-CHẤM (RE-ARM enabled + fw-139)")
print("="*70)

def find(sym):
    return [e for e in baseline if e["symbol"] == sym]

# (i) HEMI wave-1 Jul20 + RE-ARM → wave-2 Aug15
print(f"\n(i) HEMI: wave-1 Jul20 ∧ RE-ARM → E-R3 Aug15 D2 ngày-1")
h = find("HEMIUSDT")
if h:
    for e in h:
        w1_pass = e.get("ignite_date","")[:10] == "2026-07-20"
        rearm_pass = e.get("rearm_date") is not None
        w2_expected_d2 = "2026-08-15" == e.get("ignite2_date","")[:10]
        both = w1_pass and rearm_pass and w2_expected_d2
        print(f"  wave-1 ignite {e.get('ignite_date','none')} — expected Jul20: {w1_pass}")
        print(f"  rearm fired {e.get('rearm_date','no')} — expected: True")
        print(f"  ignite #2 {e.get('ignite2_date','none')} — expected Aug15: {w2_expected_d2}")
        print(f"  → GATE (i) CẢ 3 vế PASS: {both}")
else:
    print(f"  ⚠ HEMI: 0 entries — GATE (i) FAIL structurally")

# (iii) TRIA/STBL Aug NOT in registry
print(f"\n(iii) TRIA/STBL negative")
for sym in ["TRIAUSDT", "STBLUSDT"]:
    ents = find(sym)
    aug = [e for e in ents if e["unhedge_date"].startswith("2026-08")]
    total = len(ents)
    print(f"  {sym}: total entries={total}, Aug entries={len(aug)} {'✓ PASS' if len(aug)==0 else '❌ FAIL'}")
    for e in aug:
        print(f"    ! Aug entry: {e['unhedge_date']} trg={e['trigger']}")

# (iv) universe % (fw-139 at drift=0.15 baseline)
u_pct = unique_baseline / tokens_with_data * 100
print(f"\n(iv) Universe % (drift=0.15, fw-139): {unique_baseline}/{tokens_with_data} = {u_pct:.1f}%")
print(f"  → GATE (iv) at baseline: {'✓ PASS' if u_pct <= 25 else '❌ FAIL'}")

print("\n[DONE C1-C4]")
