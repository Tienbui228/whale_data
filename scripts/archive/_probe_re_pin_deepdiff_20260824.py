#!/usr/bin/env python3
"""[RE-PIN-20260824 (ii)] Deep-diff old golden (e1c9028 lineage from 2193f9d) vs
NEW snapshot (in-tree tests/fixtures/data_snapshot_20260824/, window ≤ 08-23).

Categorize every drift:
  (v1) F5a vol_quote rebuild — should be ZERO (proven at F5e).
  (v2) rows 08-20..23 — extended end_date, new events, new episodes.

Any drift outside {v1, v2} → DỪNG, không pin.
"""
from __future__ import annotations
import csv, hashlib, json, sys, io, subprocess
from pathlib import Path
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = Path(r"D:/Data back test/whale_data")
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))

from lib.hedge_episode import detect_episodes, calc_div, NaN, ok
from lib.registry_events import (
    _detect_ev, _pos_ok, _px_ok,
    window_prefilter_and_detect, dedup_b_events,
)
import importlib.util as _iu
_spec = _iu.spec_from_file_location("watchlist_daily", REPO / "scripts" / "watchlist_daily.py")
wd = _iu.module_from_spec(_spec)
_spec.loader.exec_module(wd)

SNAP_DIR = REPO / "tests/fixtures/data_snapshot_20260824"
FIX_OLD = REPO / "tests/fixtures/registry_conformance_20260821.json"

# Load OLD golden (current on-disk copy; lineage from 2193f9d unchanged in VALUES per F5e proof)
old_fix = json.loads(FIX_OLD.read_text(encoding="utf-8"))
OLD_WS = old_fix["window_start"]
OLD_WE = old_fix["window_end"]
NEW_WS = OLD_WS
NEW_WE = "2026-08-23"

print("═" * 90)
print(" [RE-PIN-20260824 (ii)] DEEP-DIFF old golden vs new snapshot")
print("═" * 90)
print(f"  OLD fixture window: {OLD_WS} → {OLD_WE}")
print(f"  NEW snapshot window: {NEW_WS} → {NEW_WE}  (extended 4 days)")

# Load new data from in-tree snapshot
def _load_td(targets):
    td = {}
    for m in ["06","07","08"]:
        p = SNAP_DIR / f"freshwatch_daily_2026-{m}.csv"
        with open(p, encoding="utf-8", errors="replace") as f:
            for r in csv.DictReader(f):
                sym = r.get("symbol", "")
                if sym not in targets: continue
                def _f(k, r=r):
                    try: return float(r[k])
                    except Exception: return NaN
                td.setdefault(sym, []).append({
                    "date": r.get("date",""), "px": _f("px_avg"),
                    "pos": _f("lsr_pos_r"), "acc": _f("lsr_acc_r"),
                    "oi": _f("oi_usd"), "vol": _f("vol_quote"),
                    "fund": _f("funding_avg"),
                })
    for s in td:
        td[s].sort(key=lambda r: r["date"])
    return td

targets = list(old_fix["tokens"].keys())
td = _load_td(targets)
cfg_wl = old_fix["config"]["watchlist"]

# ─── (A) Registry episodes drift ───
print(f"\n──── (A) Registry episodes drift per token ────")
new_episodes = {}
drift_counts = {"v1_vol_rebuild": 0, "v2_extended_range": 0, "OTHER": 0}
drift_details = []

for sym in targets:
    arr = td[sym]
    arr_reg, ep_reg = window_prefilter_and_detect(arr, NEW_WS)
    got_eps = []
    seen = set()
    for i, e in enumerate(ep_reg):
        eid = e.get("episode_id", 0)
        if eid == 0 or eid in seen: continue
        start_i = i
        end_i = i
        for j in range(i, len(ep_reg)):
            if ep_reg[j].get("episode_id") == eid and ep_reg[j]["in_hedge"]:
                end_i = j
            elif ep_reg[j].get("episode_id") == eid: continue
            else: break
        gap_days = sum(1 for j in range(start_i, end_i+1)
                       if not (ok(calc_div(arr_reg, j)) and calc_div(arr_reg, j) <= 0.5))
        count_le050 = ep_reg[end_i].get("sn_count_le050", 0)
        ep_len = end_i - start_i + 1
        got_eps.append({
            "episode_id": eid,
            "start_date": arr_reg[start_i]["date"],
            "end_date": arr_reg[end_i]["date"],
            "gap_days": gap_days,
            "count_le050": count_le050,
            "ep_len": ep_len,
            "hedge_start_px": (round(ep_reg[end_i]["hedge_start_px"], 6)
                               if ep_reg[end_i]["hedge_start_px"] and ok(ep_reg[end_i]["hedge_start_px"])
                               else None),
        })
        seen.add(eid)
    new_episodes[sym] = got_eps

    exp_eps = old_fix["tokens"][sym]["episodes"]
    if got_eps == exp_eps:
        print(f"  {sym}: 0 drift ✓")
        continue
    for a, b in zip(got_eps, exp_eps):
        for k in set(a.keys()) | set(b.keys()):
            va, vb = a.get(k), b.get(k)
            if va != vb:
                # classify
                if k in ("end_date", "count_le050", "ep_len") and a["episode_id"] == b["episode_id"]:
                    if k == "end_date" and vb <= OLD_WE and va > OLD_WE:
                        drift_counts["v2_extended_range"] += 1
                        drift_details.append(f"    {sym} ep_id={a['episode_id']} {k}: {vb} → {va}  [v2 extended range]")
                    elif k in ("count_le050", "ep_len") and isinstance(vb, int) and isinstance(va, int) and vb < va:
                        drift_counts["v2_extended_range"] += 1
                        drift_details.append(f"    {sym} ep_id={a['episode_id']} {k}: {vb} → {va}  [v2 extended range]")
                    else:
                        drift_counts["OTHER"] += 1
                        drift_details.append(f"    {sym} ep_id={a['episode_id']} {k}: {vb} → {va}  [OTHER!]")
                elif k == "gap_days":
                    if a["episode_id"] == b["episode_id"] and (va > vb):
                        drift_counts["v2_extended_range"] += 1
                        drift_details.append(f"    {sym} ep_id={a['episode_id']} {k}: {vb} → {va}  [v2 extended range]")
                    else:
                        drift_counts["OTHER"] += 1
                        drift_details.append(f"    {sym} ep_id={a['episode_id']} {k}: {vb} → {va}  [OTHER!]")
                else:
                    drift_counts["OTHER"] += 1
                    drift_details.append(f"    {sym} ep_id={a.get('episode_id')} {k}: {vb} → {va}  [OTHER!]")
    # extra episodes in new (past OLD_WE)
    if len(got_eps) > len(exp_eps):
        for ep in got_eps[len(exp_eps):]:
            if ep["start_date"] > OLD_WE:
                drift_counts["v2_extended_range"] += 1
                drift_details.append(f"    {sym} NEW ep_id={ep['episode_id']} start={ep['start_date']} end={ep['end_date']}  [v2 extended range]")
            else:
                drift_counts["OTHER"] += 1
                drift_details.append(f"    {sym} NEW ep_id={ep['episode_id']} start={ep['start_date']}  [OTHER!]")

# ─── (B) Registry events drift ───
print(f"\n──── (B) Registry events drift per token ────")
new_events = {}
for sym in targets:
    arr = td[sym]
    arr_reg, ep_reg = window_prefilter_and_detect(arr, NEW_WS)
    _raw = []
    for i in range(len(arr_reg)):
        ev = _detect_ev(arr_reg, ep_reg, i, sn_min=3, window_start=NEW_WS, window_end=NEW_WE)
        if ev: _raw.append(ev)
    _dedup = dedup_b_events(_raw, sym=sym)
    got_events = []
    for ev in _dedup:
        got_events.append({
            "date": ev["date"], "trig": ev["trig"], "sn": ev["sn"],
            "rel_ep_id": ev["rel_ep_id"], "rel_ep_kind": ev["rel_ep_kind"],
            "ep_min": round(ev["ep_min"], 4) if ok(ev["ep_min"]) else None,
            "hspx": round(ev["hspx"], 6) if ev["hspx"] and ok(ev["hspx"]) else None,
            "pass_c": _pos_ok(arr_reg, ev["i"]),
            "pass_d": _px_ok(arr_reg, ev["i"], ev["hspx"]),
        })
    new_events[sym] = got_events
    exp = old_fix["tokens"][sym]["registry_events"]
    if got_events == exp:
        print(f"  {sym}: 0 drift ✓")
        continue
    for a, b in zip(got_events, exp):
        for k in set(a.keys()) | set(b.keys()):
            va, vb = a.get(k), b.get(k)
            if va != vb:
                if k in ("sn",) and va > vb and a["date"] == b["date"]:
                    drift_counts["v2_extended_range"] += 1
                    drift_details.append(f"    {sym} ev {a['date']} {k}: {vb} → {va}  [v2 extended range]")
                else:
                    drift_counts["OTHER"] += 1
                    drift_details.append(f"    {sym} ev {a.get('date')} {k}: {vb} → {va}  [OTHER!]")
    if len(got_events) > len(exp):
        for ev in got_events[len(exp):]:
            if ev["date"] > OLD_WE:
                drift_counts["v2_extended_range"] += 1
                drift_details.append(f"    {sym} NEW ev date={ev['date']} trig={ev['trig']}  [v2 extended range]")
            else:
                drift_counts["OTHER"] += 1
                drift_details.append(f"    {sym} NEW ev date={ev['date']} trig={ev['trig']}  [OTHER!]")

# ─── (C) Watchlist daily drift ───
print(f"\n──── (C) Watchlist daily drift per token ────")
new_watchlist = {}
for sym in targets:
    arr = td[sym]
    ep_wl = wd.detect_episodes(arr, cfg_wl)
    got = []
    for i in range(len(arr)):
        d = arr[i]["date"]
        if not (NEW_WS <= d <= NEW_WE): continue
        s = wd.snapshot(sym, arr, ep_wl, i, cfg_wl)
        got.append({
            "date": d,
            "div_ratio": round(s["div_ratio"], 4) if ok(s["div_ratio"]) else None,
            "struct_n": s["struct_n"],
            "sn_count_le050": s.get("sn_count_le050", 0),
            "in_list_a": wd.in_list_a(s, cfg_wl),
            "in_list_b": wd.in_list_b(s, ep_wl, i, cfg_wl),
        })
    new_watchlist[sym] = got
    exp = old_fix["tokens"][sym]["watchlist_daily"]
    # New rows for 08-20..23 = v2 extended range (expected)
    n_new_rows = len(got) - len(exp)
    # Diff within overlap
    diffs_within_overlap = 0
    for a, b in zip(got, exp):
        for k in set(a.keys()) | set(b.keys()):
            if a.get(k) != b.get(k):
                diffs_within_overlap += 1
                drift_counts["OTHER"] += 1
                drift_details.append(f"    {sym} wl {a.get('date')} {k}: {b.get(k)} → {a.get(k)}  [OTHER!]")
    if n_new_rows > 0:
        # verify all new rows are in extended range
        new_dates = [r["date"] for r in got[len(exp):]]
        if all(d > OLD_WE for d in new_dates):
            drift_counts["v2_extended_range"] += n_new_rows
            print(f"  {sym}: +{n_new_rows} rows extended {new_dates[0]}..{new_dates[-1]}  [v2 extended range]  overlap diffs={diffs_within_overlap}")
        else:
            drift_counts["OTHER"] += n_new_rows
            drift_details.append(f"    {sym} wl NEW rows include dates within OLD window: {new_dates}  [OTHER!]")
    elif diffs_within_overlap == 0:
        print(f"  {sym}: 0 drift ✓")

# ─── Report ───
print(f"\n" + "═" * 90)
print(f" DRIFT SUMMARY")
print(f"═" * 90)
print(f"  (v1) F5a vol_quote rebuild changes  : {drift_counts['v1_vol_rebuild']}  (expected ZERO per F5e proof)")
print(f"  (v2) rows 08-20..23 extended range  : {drift_counts['v2_extended_range']}")
print(f"  (OTHER — UNEXPLAINED)               : {drift_counts['OTHER']}")

if drift_details:
    print(f"\n  Drift details:")
    for d in drift_details[:50]:
        print(d)
    if len(drift_details) > 50:
        print(f"    ... {len(drift_details) - 50} more")

if drift_counts["OTHER"] == 0:
    print(f"\n[VERDICT] ✓ ALL drift explainable by (v1) or (v2) — safe to re-pin")
else:
    print(f"\n[VERDICT] ✗ {drift_counts['OTHER']} OTHER drift — DỪNG, không pin, báo operator")

# ─── Emit new golden fixture JSON ───
print(f"\n──── Emit NEW golden fixture ────")
new_fix = json.loads(FIX_OLD.read_text(encoding="utf-8"))
# Get current git commits for meta
def _git(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=REPO)
    return r.stdout.strip()

# md5s for new snapshot
def _md5(p):
    h = hashlib.md5()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1<<16), b""): h.update(c)
    return h.hexdigest()

new_fix["snapshot_date"] = "2026-08-23"
new_fix["window_end"] = NEW_WE
new_fix["data_snapshot_md5"] = {
    "freshwatch_daily_2026-06.csv": _md5(SNAP_DIR / "freshwatch_daily_2026-06.csv"),
    "freshwatch_daily_2026-07.csv": _md5(SNAP_DIR / "freshwatch_daily_2026-07.csv"),
    "freshwatch_daily_2026-08.csv": _md5(SNAP_DIR / "freshwatch_daily_2026-08.csv"),
}
# Update golden values
for sym in targets:
    new_fix["tokens"][sym]["episodes"] = new_episodes[sym]
    new_fix["tokens"][sym]["registry_events"] = new_events[sym]
    new_fix["tokens"][sym]["watchlist_daily"] = new_watchlist[sym]

# case_gap_gua probe — recalc GUA 07-05→07-09 (unchanged, keep same values but verify)
# (Existing probe values in old_fix; if v2 only extended, ep_id=1 for GUA still 07-05→09 unchanged)
# We just carry over.

new_json_path = REPO / "tests/fixtures/registry_conformance_20260821.json"
if drift_counts["OTHER"] == 0:
    new_json_path.write_text(json.dumps(new_fix, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"  WROTE {new_json_path}")
    print(f"    new snapshot_date = {new_fix['snapshot_date']}")
    print(f"    new window_end    = {new_fix['window_end']}")
    print(f"    new data_snapshot_md5:")
    for k, v in new_fix["data_snapshot_md5"].items():
        print(f"      {k}: {v}")
else:
    print(f"  DỪNG — không ghi vì {drift_counts['OTHER']} OTHER drift")
