#!/usr/bin/env python3
"""[A2 verify] Watchlist gate switch struct_n→sn_count_le050.

Chạy watchlist run_date() trên snapshot 08-19, 08-20, 08-21 (nếu có) với 2 gate:
  (i) sn_gate = struct_n (BEFORE — ep_len semantics)
  (ii) sn_gate = sn_count_le050 (AFTER — canonical)

Đo: List A/B token diff, biên struct_n≥5 ∧ sn_count<5 (rows lật quyết định).

PASS = ép fixture SHA/values pass + import + run không crash. Bảng lật List A
là input cho A5 (corrections lớp-2).
"""
from __future__ import annotations
import sys, io, csv
from pathlib import Path
from statistics import mean

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = Path(r"D:\Data back test\whale_data")
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO))

# Import watchlist module directly (avoid running main)
import importlib.util
spec = importlib.util.spec_from_file_location("watchlist_daily", REPO / "scripts" / "watchlist_daily.py")
wd = importlib.util.module_from_spec(spec)
# Guard __main__ so import doesn't execute main()
wd.__name__ = "watchlist_daily"
try:
    spec.loader.exec_module(wd)
except SystemExit:
    pass

TMP = Path(r"C:\Users\Hello\AppData\Local\Temp\e_r7_20260819")

# Load data using watchlist's own loader
td = {}
from lib.hedge_episode import NaN, ok
for m in ["06","07","08"]:
    p = TMP / f"freshwatch_daily_2026-{m}.csv"
    if not p.exists(): continue
    with open(p, encoding="utf-8", errors="replace") as f:
        for r in csv.DictReader(f):
            sym = r.get("symbol","")
            if not sym: continue
            def _f(k, r=r):
                try: return float(r[k])
                except: return NaN
            td.setdefault(sym, []).append({
                "date": r.get("date",""), "px": _f("px_avg"),
                "pos": _f("lsr_pos_r"), "acc": _f("lsr_acc_r"),
                "oi": _f("oi_usd"), "vol": _f("vol_quote"),
                "fund": _f("funding_avg"),
            })
sympath = TMP / "freshwatch_symbols_vps.txt"
with open(sympath, encoding="utf-8", errors="replace") as f:
    universe = sorted({l.strip() for l in f if l.strip() and not l.startswith("#")})
for sym in td: td[sym].sort(key=lambda r: r["date"])
td = {s: v for s, v in td.items() if len(v) >= 14 and s in universe}
print(f"[fw] universe ≥14d: {len(td)} tokens")

# Config extracted from watchlist v1.4 default (skip yaml load for smoke)
CFG = {
    "hedge": {"div_ratio_max": 0.5, "struct_n_min": 5, "episode_break_days": 3},
    "list_b": {"recent_hedge_days": 2, "div_delta_min": 0.0},
    "trends": {"pos_trend_threshold": 0.15, "oi_trend_threshold": 0.10},
    "oi_guard": {"low_conf_usd": 1_000_000},
    "output": {"csv_path": "data/export/watchlist_log_{YYYY-MM}.csv"},
}

TARGET_DATES = ["2026-08-19", "2026-08-20", "2026-08-21"]

print(f"\n{'='*90}")
print("A2 DELTA — List A gate BEFORE (struct_n) vs AFTER (sn_count_le050)")
print(f"{'='*90}")

for tgt in TARGET_DATES:
    ep_cache = {sym: wd.detect_episodes(arr, CFG) for sym, arr in td.items()}
    snaps_a, snaps_b = wd.run_date(tgt, td, CFG, ep_cache=ep_cache)
    if not snaps_a and not snaps_b:
        print(f"\n[{tgt}] no snap (skip-stale or no rows)")
        continue

    # BEFORE: simulate old gate struct_n >= 5
    before_a_syms = set()
    for sym, arr in td.items():
        ep = ep_cache[sym]
        idx = next((i for i, r in enumerate(arr) if r["date"] == tgt), None)
        if idx is None: continue
        s = wd.snapshot(sym, arr, ep, idx, CFG)
        dr = s["div_ratio"]
        if ok(dr) and dr <= 0.5 and s["struct_n"] >= 5:
            before_a_syms.add(sym)

    # AFTER: current gate (via in_list_a)
    after_a_syms = {s["sym"] for s in snaps_a}

    added   = after_a_syms - before_a_syms
    removed = before_a_syms - after_a_syms
    kept    = after_a_syms & before_a_syms

    print(f"\n[{tgt}] BEFORE_A={len(before_a_syms)}  AFTER_A={len(after_a_syms)}  "
          f"kept={len(kept)}  added={len(added)}  removed={len(removed)}")
    if added:
        print(f"  ADDED (gate mới ĐỠ):    {sorted(added)}")
    if removed:
        print(f"  REMOVED (gate mới LOẠI): {sorted(removed)}")

        # Detail: which rows had struct_n≥5 but sn_count<5
        print(f"  ── Row-detail REMOVED (struct_n≥5 ∧ sn_count_le050<5) ──")
        for sym in sorted(removed):
            arr = td[sym]; ep = ep_cache[sym]
            idx = next((i for i, r in enumerate(arr) if r["date"] == tgt), None)
            if idx is None: continue
            e = ep[idx]
            print(f"    {sym:>16}  struct_n={e['struct_n']}  sn_count_le050={e['sn_count_le050']}  "
                  f"ep_start={e['hedge_start_date']}  in_hedge={e['in_hedge']}")

print(f"\n{'='*90}")
print("DONE — A2 verify (delta table above → input cho A5 corrections lớp-2)")
