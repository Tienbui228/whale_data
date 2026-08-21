#!/usr/bin/env python3
"""[A4(2)] Diff ae5f2a0 vs post-A1 (lib.registry_events) trên 7 tokens.

Cùng snapshot pin (md5 lock 06/07/08), sn_min=3 registry, WINDOW harmonize:
- Mine (lib): WINDOW_START=2026-06-21
- Ae5f2a0:    WINDOW_START=2026-06-20 (off-by-1 documented pre-A4(2))

Table format per token:
  ae5f2a0: episodes(start→end, break_at, count_le050) · events(date/trig/sn)
  post-A1: episodes(start→end, count_le050, ep_len) · events(date/trig/sn/rel_ep_kind)
  DIFF: ep_delta, event_delta, sn_delta
  Case-map: A-H hoặc "NEW-CASE" (nếu không match)
"""
from __future__ import annotations
import sys, io, csv, subprocess, hashlib
from pathlib import Path
from datetime import date as _date, timedelta
from statistics import mean, median
from collections import defaultdict

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = Path(r"D:\Data back test\whale_data")
sys.path.insert(0, str(REPO))
from lib.hedge_episode import detect_episodes, calc_div, NaN, ok
from lib.registry_events import (
    _detect_ev, _pos_ok, _px_ok,
    window_prefilter_and_detect, dedup_b_events, CFG_DEFAULT,
)

TMP = Path(r"C:\Users\Hello\AppData\Local\Temp\e_r7_20260819")
AE5_FILE = Path(r"C:\Users\Hello\AppData\Local\Temp\ae5f2a0_task_full.py")

# Snapshot pin md5 (must match fixture)
EXPECTED_MD5 = {
    "freshwatch_daily_2026-06.csv": "f717231a7b3385012459566a908952d2",
    "freshwatch_daily_2026-07.csv": "c7143e37bf98cc11bf171068a2518857",
    "freshwatch_daily_2026-08.csv": "6decfff1dffaedffd202287a209a7129",
}

def _md5(p: Path) -> str:
    h = hashlib.md5()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1<<16), b""): h.update(c)
    return h.hexdigest()

for fname, exp in EXPECTED_MD5.items():
    got = _md5(TMP / fname)
    tag = "OK" if got == exp else "DRIFT"
    print(f"  md5 {fname}: {got} [{tag}]")
    if got != exp:
        print("  ABORT — data drift")
        sys.exit(1)

TARGETS = ["HEMIUSDT","ONUSDT","GUAUSDT","CARVUSDT","ARIAUSDT","SHELLUSDT","SIGNUSDT"]
# A4(2) A-K revision: align mine WINDOW_START to ae5 (06-20 canonical) for match
WINDOW_START_MINE = "2026-06-20"   # was 06-21 pre-A4(2), aligned to ae5f2a0 canonical
WINDOW_END_MINE = "2026-08-19"
WINDOW_START_AE5 = "2026-06-20"
WINDOW_END_AE5 = "2026-08-19"

# Load raw
td = {}
for m in ["06","07","08"]:
    p = TMP / f"freshwatch_daily_2026-{m}.csv"
    with open(p, encoding="utf-8", errors="replace") as f:
        for r in csv.DictReader(f):
            sym = r.get("symbol","")
            if sym not in TARGETS: continue
            def _f(k, r=r):
                try: return float(r[k])
                except: return NaN
            td.setdefault(sym, []).append({
                "date": r.get("date",""), "px": _f("px_avg"),
                "pos": _f("lsr_pos_r"), "acc": _f("lsr_acc_r"),
                "oi": _f("oi_usd"), "vol": _f("vol_quote"),
                "fund": _f("funding_avg"),
            })
for s in td: td[s].sort(key=lambda r: r["date"])
print(f"\n[loaded] {len(td)} targets: {sorted(td)}")

# ── Extract ae5f2a0 analyze_token ──
if not AE5_FILE.exists():
    subprocess.run(["bash","-c",
        f"git -C '{REPO}' show ae5f2a0:_task_registry_c1_c4_20260820.py > '{AE5_FILE}'"],
        check=True)
ae5_src = AE5_FILE.read_text(encoding="utf-8")

# Extract just analyze_token definition
start = ae5_src.find("def analyze_token")
lines = ae5_src[start:].split("\n")
end_idx = 0
for i, ln in enumerate(lines):
    if i == 0: continue
    if ln.startswith("def ") or (ln and not ln[0].isspace() and not ln.startswith("#")):
        end_idx = i; break
if end_idx == 0: end_idx = len(lines)

exec_globals = {
    "defaultdict": defaultdict, "median": median, "timedelta": timedelta,
    "_date": _date, "date": _date,
    "DRIFT_MIN_DEFAULT": 0.15, "STRUCT_N_MIN": 3,
    "WINDOW_START": WINDOW_START_AE5, "WINDOW_END": WINDOW_END_AE5,
    "REARM_MIN_DAYS": 14, "REARM_PX_MULT": 1.10, "REARM_OI_MULT": 1.30,
    "REARM_COOLDOWN_DAYS": 14,
    "POS_GUARD": 0.90, "PX_GUARD": 0.85,
}
exec("\n".join(lines[:end_idx]), exec_globals)
analyze_token_ae5 = exec_globals["analyze_token"]

def _to_dd(arr):
    return {r["date"]: {"pos_r":r["pos"], "acc_r":r["acc"], "oi":r["oi"], "px":r["px"], "vol":r["vol"]} for r in arr}

# ── Ae5f2a0 EPISODE extraction (re-implement to get episodes) ──
def ae5_episodes(sym, days_dict):
    all_dates = sorted(days_dict.keys())
    d0 = _date.fromisoformat(WINDOW_START_AE5) - timedelta(days=5)
    filtered = [d for d in all_dates if _date.fromisoformat(d) >= d0]
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
    eps = []
    cur = None; days_above = 0
    for d in filtered:
        if d not in div_avg3: continue
        v = div_avg3[d]
        if v <= 0.5:
            if cur is None: cur = {"start": d, "end": d, "min_v": v, "min_d": d, "vals": [(d, v)]}
            else:
                cur["end"] = d; cur["vals"].append((d, v))
                if v < cur["min_v"]: cur["min_v"] = v; cur["min_d"] = d
            days_above = 0
        else:
            if cur is not None:
                days_above += 1; cur["vals"].append((d, v))
                if days_above >= 3:
                    cur["break_confirmed_at"] = d
                    eps.append(cur); cur = None; days_above = 0
    if cur: eps.append(cur)
    out = []
    for e in eps:
        count = sum(1 for _, vv in e["vals"] if vv <= 0.5)
        out.append({
            "start": e["start"], "end": e["end"],
            "break_confirmed_at": e.get("break_confirmed_at", "OPEN"),
            "count_le050": count,
            "min_v": e["min_v"], "min_d": e["min_d"],
        })
    return out

# ── Post-A1 episode extraction using window_prefilter ──
def mine_episodes(sym, arr):
    arr_reg, ep_reg = window_prefilter_and_detect(arr, WINDOW_START_MINE)
    out = []
    seen = set()
    for i, e in enumerate(ep_reg):
        eid = e.get("episode_id", 0)
        if eid == 0 or eid in seen: continue
        start_i = i; end_i = i
        for j in range(i, len(ep_reg)):
            if ep_reg[j].get("episode_id") == eid and ep_reg[j]["in_hedge"]:
                end_i = j
            elif ep_reg[j].get("episode_id") == eid: continue
            else: break
        out.append({
            "start": arr_reg[start_i]["date"],
            "end": arr_reg[end_i]["date"],
            "count_le050": ep_reg[end_i].get("sn_count_le050", 0),
            "ep_len": end_i - start_i + 1,
            "hspx": ep_reg[end_i]["hedge_start_px"],
        })
        seen.add(eid)
    return out, arr_reg, ep_reg

# ── Run diff table per token ──
DIV = "═" * 100
print(f"\n{DIV}\n[A4(2)] 7-TOKEN DIFF ae5f2a0 vs post-A1 (lib.registry_events)\n{DIV}")

def _fmt_ev(ev, kind):
    if kind == "ae5":
        return f"{ev['unhedge_date']}/{ev['trigger']} sn={ev['struct_n']} hs={ev['hedge_start']}"
    else:
        return f"{ev['date']}/{ev['trig']} sn={ev['sn']} rel={ev.get('rel_ep_kind','?')}"

def _map_case(sym, ae5_ev, mine_ev, ae5_eps, mine_eps, arr):
    """Map diff to case A-H."""
    diffs = []
    ae5_ev_set = {(e['unhedge_date'], e['trigger']) for e in ae5_ev}
    mine_ev_set = {(e['date'], e['trig']) for e in mine_ev}
    only_ae5 = ae5_ev_set - mine_ev_set
    only_mine = mine_ev_set - ae5_ev_set
    for d, trig in only_ae5:
        # find ae5 event
        ae5e = next(e for e in ae5_ev if e['unhedge_date']==d and e['trigger']==trig)
        # trace which ep the event was
        ep_start = ae5e['hedge_start']
        ep = next((x for x in ae5_eps if x['start']==ep_start), None)
        if ep and ep.get('break_confirmed_at') != 'OPEN':
            # check if event is post-break
            bd = ep['break_confirmed_at']
            gap = (_date.fromisoformat(d) - _date.fromisoformat(bd)).days
            if gap > 0:
                diffs.append(f"ONLY-AE5: {d}/{trig} sn={ae5e['struct_n']} — POST-BREAK gap={gap}d ep({ep['start']}→{bd}) → case F (post-break rel_ep)")
            else:
                diffs.append(f"ONLY-AE5: {d}/{trig} sn={ae5e['struct_n']} — DURING ep({ep['start']}→{bd}) → check case B/C/D/G")
        else:
            diffs.append(f"ONLY-AE5: {d}/{trig} sn={ae5e['struct_n']} — DURING open ep({ep_start}→?)")
    for d, trig in only_mine:
        minee = next(e for e in mine_ev if e['date']==d and e['trig']==trig)
        diffs.append(f"ONLY-MINE: {d}/{trig} sn={minee['sn']} rel={minee.get('rel_ep_kind','?')} — check WINDOW or new-case")
    # sn diffs for shared events
    for e_ae5 in ae5_ev:
        for e_mine in mine_ev:
            if e_ae5['unhedge_date'] == e_mine['date'] and e_ae5['trigger'] == e_mine['trig']:
                if e_ae5['struct_n'] != e_mine['sn']:
                    diffs.append(f"SN-DELTA: {e_ae5['unhedge_date']}/{e_ae5['trigger']} ae5.sn={e_ae5['struct_n']} vs mine.sn={e_mine['sn']} → check ep_len semantics or window scope (case E)")
    return diffs

STATS = {"tokens_ok": 0, "tokens_diff": 0, "total_diffs": 0}
DIFF_DETAIL = []

for sym in TARGETS:
    if sym not in td:
        print(f"\n──── {sym} — NO DATA ────")
        continue
    arr = td[sym]
    dd = _to_dd(arr)

    # Run ae5f2a0
    ae5_evs = analyze_token_ae5(sym, dd, drift_min=0.15, struct_n_min=3)
    ae5_eps = ae5_episodes(sym, dd)

    # Run mine
    mine_eps, arr_reg, ep_reg = mine_episodes(sym, arr)
    mine_evs = []
    for i in range(len(arr_reg)):
        ev = _detect_ev(arr_reg, ep_reg, i, sn_min=3,
                        window_start=WINDOW_START_MINE, window_end=WINDOW_END_MINE)
        if ev:
            mine_evs.append(ev)
    # Case L: dedup (b) per episode
    mine_evs = dedup_b_events(mine_evs, sym=sym)

    print(f"\n──── {sym} ────")
    print(f"  ae5f2a0 window=[{WINDOW_START_AE5}..{WINDOW_END_AE5}] "
          f"cutoff={_date.fromisoformat(WINDOW_START_AE5)-timedelta(days=5)}")
    print(f"    episodes ({len(ae5_eps)}): ")
    for e in ae5_eps:
        print(f"      {e['start']}→{e['end']} break={e['break_confirmed_at']} count={e['count_le050']} min={e['min_v']:.3f}")
    print(f"    events ({len(ae5_evs)}): ")
    for e in ae5_evs:
        print(f"      {_fmt_ev(e, 'ae5')}")

    print(f"  post-A1 window=[{WINDOW_START_MINE}..{WINDOW_END_MINE}] "
          f"cutoff={_date.fromisoformat(WINDOW_START_MINE)-timedelta(days=5)}")
    print(f"    episodes ({len(mine_eps)}): ")
    for e in mine_eps:
        print(f"      {e['start']}→{e['end']} count={e['count_le050']} ep_len={e['ep_len']}")
    print(f"    events ({len(mine_evs)}): ")
    for e in mine_evs:
        print(f"      {_fmt_ev(e, 'mine')}")

    # Diff map
    diffs = _map_case(sym, ae5_evs, mine_evs, ae5_eps, mine_eps, arr)
    if not diffs:
        STATS["tokens_ok"] += 1
        print(f"  DIFF: none — MATCH")
    else:
        STATS["tokens_diff"] += 1
        STATS["total_diffs"] += len(diffs)
        for d in diffs:
            print(f"  {d}")
            DIFF_DETAIL.append((sym, d))

print(f"\n{DIV}\nSUMMARY:  {STATS['tokens_ok']}/{len(TARGETS)} MATCH  ·  {STATS['tokens_diff']} DIFF  ·  {STATS['total_diffs']} total diffs\n{DIV}")
if DIFF_DETAIL:
    print(f"\n[DIFF DETAIL for A4(2) case-map]")
    for sym, d in DIFF_DETAIL:
        print(f"  {sym:>10} · {d}")
