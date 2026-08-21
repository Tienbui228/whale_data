#!/usr/bin/env python3
"""[A1 P0 SAFE verify] detect_episodes lib bit-equal watchlist inline — 139 tokens.

Sau sửa lib.hedge_episode.py (conformance-pack amend): thêm sn_count_le050 + ep_len.
Watchlist inline detect_episodes KHÔNG được lệch struct_n/in_hedge/episode_id/hspx.

PASS = 139 tokens, 0 diffs trên field {in_hedge, episode_id, hedge_start_date,
hedge_start_px, struct_n} (fields cũ bit-equal). Fields mới (sn_count_le050, ep_len)
chỉ có trong lib output → không compare (watchlist inline không sinh).
"""
from __future__ import annotations
import sys, io, csv
from pathlib import Path
from statistics import mean

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = Path(r"D:\Data back test\whale_data")
sys.path.insert(0, str(REPO))
from lib.hedge_episode import detect_episodes as det_lib, NaN, ok

# ── Inline watchlist copy (paste from scripts/watchlist_daily.py L107-158) ──
from statistics import mean
def avg3_wl(arr, i, field):
    vals = [arr[j][field] for j in range(max(0, i-2), i+1) if ok(arr[j][field])]
    return mean(vals) if vals else NaN

def calc_div_wl(arr, i):
    a3p = avg3_wl(arr, i, "pos"); a3a = avg3_wl(arr, i, "acc")
    if not ok(a3p) or not ok(a3a) or a3a == 0: return NaN
    return a3p / a3a

def detect_episodes_wl(arr, cfg):
    div_max  = cfg["hedge"]["div_ratio_max"]
    ep_break = cfg["hedge"]["episode_break_days"]
    out = []
    ep_id = 0; ep_si = None; ep_spx = None
    in_hedge = False; n_above = 0
    for i, row in enumerate(arr):
        dr = calc_div_wl(arr, i)
        if ok(dr) and dr <= div_max:
            if not in_hedge:
                ep_id += 1; ep_si = i
                ep_spx = row["px"] if ok(row["px"]) else None
            in_hedge = True; n_above = 0
        else:
            if in_hedge:
                n_above += 1
                if n_above >= ep_break:
                    in_hedge = False; n_above = 0
        sn = (i - ep_si + 1) if (in_hedge and ep_si is not None) else 0
        out.append({
            "in_hedge": in_hedge,
            "episode_id": ep_id if in_hedge else 0,
            "hedge_start_date": arr[ep_si]["date"] if (in_hedge and ep_si is not None) else "",
            "hedge_start_px": ep_spx if in_hedge else None,
            "struct_n": sn,
        })
    return out

# ── Load 139-token universe from VPS snapshot ──
TMP = Path(r"C:\Users\Hello\AppData\Local\Temp\e_r7_20260819")
td = {}
for m in ["06","07","08"]:
    p = TMP / f"freshwatch_daily_2026-{m}.csv"
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
            })
for sym in td:
    td[sym].sort(key=lambda r: r["date"])

sympath = TMP / "freshwatch_symbols_vps.txt"
with open(sympath, encoding="utf-8", errors="replace") as f:
    universe = sorted({l.strip() for l in f if l.strip() and not l.startswith("#")})
td = {s: v for s, v in td.items() if len(v) >= 14 and s in universe}
print(f"[fw] universe ≥14d: {len(td)} tokens")

CFG = {"hedge": {"div_ratio_max": 0.5, "episode_break_days": 3}}
COMPARE_FIELDS = ("in_hedge", "episode_id", "hedge_start_date", "hedge_start_px", "struct_n")

n_tok = 0; n_ok = 0; n_diff = 0
diffs = []
for sym in sorted(td):
    n_tok += 1
    arr = td[sym]
    ep_lib = det_lib(arr, CFG)
    ep_wl  = detect_episodes_wl(arr, CFG)
    if len(ep_lib) != len(ep_wl):
        n_diff += 1
        diffs.append(f"{sym}: len {len(ep_lib)} vs {len(ep_wl)}")
        continue
    tok_ok = True
    for i, (a, b) in enumerate(zip(ep_lib, ep_wl)):
        for f in COMPARE_FIELDS:
            if a.get(f) != b.get(f):
                tok_ok = False
                if len(diffs) < 20:
                    diffs.append(f"{sym} i={i} d={arr[i]['date']} {f}: {a.get(f)} vs {b.get(f)}")
                break
        if not tok_ok:
            break
    if tok_ok:
        n_ok += 1
    else:
        n_diff += 1

print(f"\n[A1 P0 SAFE] {n_ok}/{n_tok} tokens bit-equal (lib vs watchlist inline)")
print(f"           diffs: {n_diff}")
if diffs:
    print("\n[FAIL] first diffs:")
    for d in diffs[:20]:
        print(f"  {d}")
    sys.exit(1)
else:
    print("\n[PASS] bit-equal — lib new fields (sn_count_le050, ep_len) không phá backward-compat")
    # verify new fields present in lib output
    sample = det_lib(td[sorted(td)[0]], CFG)
    have_sn = "sn_count_le050" in sample[-1]
    have_el = "ep_len" in sample[-1]
    print(f"           new fields sample: sn_count_le050={have_sn} · ep_len={have_el}")
