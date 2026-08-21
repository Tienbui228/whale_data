#!/usr/bin/env python3
"""[E-R7e-regress] (1) 5-token diff ae5f2a0 vs 5c2f22d code · (2) n_rearm 31→27 root cause.

Both run on CURRENT data snapshot (freshwatch /tmp/e_r7_20260819/*).
KHÔNG SỬA GÌ. DỪNG.
"""
from __future__ import annotations
import sys, io, csv, math, subprocess
from pathlib import Path
from statistics import mean, median
from datetime import date

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = Path(r"D:\Data back test\whale_data")
TMP = Path(r"C:\Users\Hello\AppData\Local\Temp\e_r7_20260819")

DIV = "═"*96
print(f"{DIV}\n[HEADER] regression probe — data snapshot current /tmp/e_r7_20260819\n{DIV}")

# ─── Load data (current snapshot) ──────────────────────────────────────────
td = {}
for m in ["06","07","08"]:
    p = TMP / f"freshwatch_daily_2026-{m}.csv"
    with open(p, encoding="utf-8", errors="replace") as f:
        for r in csv.DictReader(f):
            sym = r.get("symbol","");
            if not sym: continue
            def _f(k, r=r):
                try: return float(r[k])
                except: return float("nan")
            td.setdefault(sym, []).append({
                "date": r.get("date",""), "px": _f("px_avg"),
                "pos": _f("lsr_pos_r"), "acc": _f("lsr_acc_r"),
                "oi": _f("oi_usd"), "vol": _f("vol_quote"),
            })
for sym in td: td[sym].sort(key=lambda r: r["date"])
with open(TMP / "freshwatch_symbols_vps.txt", encoding="utf-8", errors="replace") as f:
    universe = sorted({l.strip() for l in f if l.strip() and not l.startswith("#")})
td_all = td
td = {s: v for s, v in td.items() if len(v) >= 14 and s in universe}
print(f"[data] {len(td)}/139 tokens · Aug last date = 2026-08-19 (rows 08-18/08-19 included)\n")

# ─── (1) 5 TOKEN DIV_AVG3 series + episode boundaries ─────────────────────
TARGETS = ["ARIAUSDT", "CARVUSDT", "GUAUSDT", "SHELLUSDT", "SIGNUSDT"]
WINDOW_START = "2026-06-21"; WINDOW_END = "2026-08-19"

# Helper functions matching CURRENT 5c2f22d
sys.path.insert(0, str(REPO))
from lib.hedge_episode import detect_episodes, calc_div, NaN, ok as ok_fn

CFG = {"hedge": {"div_ratio_max": 0.5, "episode_break_days": 3}}
DRIFT_THR=0.15; DRIFT_WIN=7; POS_HOLD=0.90; PX_HOLD=0.85

def _pos_ok_new(arr, i):
    cur = arr[i].get("pos", NaN)
    if not ok_fn(cur): return False, cur, NaN
    vs = [arr[j]["pos"] for j in range(max(0,i-5),i) if ok_fn(arr[j]["pos"])]
    if len(vs)<3: return False, cur, NaN
    avg5 = mean(vs); ratio = cur/avg5
    return (ratio >= POS_HOLD, cur, avg5)

def _px_ok_new(arr, i, hspx):
    cur = arr[i].get("px", NaN)
    if not (ok_fn(cur) and hspx and ok_fn(hspx)): return False, cur, hspx
    return (cur >= PX_HOLD * hspx, cur, hspx)

# ─── Import ae5f2a0's analyze_token via checkout git tempcopy ─────────────
ae5_probe = r"C:\Users\Hello\AppData\Local\Temp\ae5f2a0_probe.py"
if not Path(ae5_probe).exists():
    subprocess.run(["bash","-c",
        f"git -C '{REPO}' show ae5f2a0:_task_registry_c1_c4_20260820.py > '{ae5_probe}'"],
        check=True)

# Extract just analyze_token function via exec (minimal deps)
ae5_code = Path(ae5_probe).read_text(encoding="utf-8")
# Find analyze_token def
start = ae5_code.find("def analyze_token")
# find end: next top-level def or line with no leading space+content
lines = ae5_code[start:].split("\n")
end_idx = 0
in_def = False
for i, ln in enumerate(lines):
    if i == 0: continue
    if ln.startswith("def ") or (ln and not ln[0].isspace() and not ln.startswith("#")):
        end_idx = i; break
if end_idx == 0: end_idx = len(lines)
analyze_token_src = "\n".join(lines[:end_idx])

# Also grab helpers
DRIFT_MIN_DEFAULT = 0.15; STRUCT_N_MIN = 3

# Inject required constants
from datetime import date as _date, timedelta as _timedelta
exec_globals = {"defaultdict": __import__("collections").defaultdict,
                "date": date, "_date": _date, "timedelta": _timedelta, "_timedelta": _timedelta,
                "median": median,
                "DRIFT_MIN_DEFAULT": DRIFT_MIN_DEFAULT, "STRUCT_N_MIN": STRUCT_N_MIN,
                "WINDOW_START": WINDOW_START, "WINDOW_END": WINDOW_END,
                "REARM_MIN_DAYS": 14, "REARM_PX_MULT": 1.10, "REARM_OI_MULT": 1.30,
                "REARM_COOLDOWN_DAYS": 14,
                "POS_GUARD": 0.90, "PX_GUARD": 0.85}
exec(analyze_token_src, exec_globals)
analyze_token_old = exec_globals["analyze_token"]

# Convert current td format → ae5f2a0's days_dict format
def _to_days_dict(arr):
    """Convert list[dict] → {date_str: {pos_r, acc_r, oi, px, vol}} — matches ae5f2a0."""
    d = {}
    for r in arr:
        d[r["date"]] = {"pos_r": r["pos"], "acc_r": r["acc"],
                        "oi": r["oi"], "px": r["px"], "vol": r["vol"]}
    return d

# Compare 5 tokens
print(f"{DIV}\n[Q1] 5-TOKEN CODE-vs-DATA regression\n{DIV}")
print(f"  Both codes run on CURRENT data (Aug last 2026-08-19)")
print(f"  ae5f2a0 = analyze_token(inline episode detection)  ·  5c2f22d = lib/hedge_episode + _detect_ev\n")

for sym in TARGETS:
    if sym not in td:
        print(f"\n──── {sym} — NOT IN td (universe filter) ────"); continue
    arr = td[sym]
    ep = detect_episodes(arr, CFG)
    print(f"\n──── {sym} ({len(arr)} rows, {arr[0]['date']}→{arr[-1]['date']}) ────")

    # div_avg3 series (window only, sample sparse for readability)
    print(f"  div_avg3 series (window {WINDOW_START}→{WINDOW_END}, sample every 5d):")
    for i, r in enumerate(arr):
        d = r["date"]
        if not (WINDOW_START <= d <= WINDOW_END): continue
        if i % 5 != 0: continue
        div = calc_div(arr, i)
        in_hd = ep[i]["in_hedge"]; ep_id = ep[i]["episode_id"]; sn = ep[i]["struct_n"]
        print(f"    {d}  div={div:.3f}  in_hedge={in_hd}  ep_id={ep_id}  sn={sn}  "
              f"pos={r['pos']:.3f} acc={r['acc']:.3f} px={r['px']:.5f}")

    # Episode boundaries (all)
    print(f"  episode boundaries (in_hedge transitions):")
    prev_hd = False; ep_start = None
    for i, e in enumerate(ep):
        d = arr[i]["date"]
        if e["in_hedge"] and not prev_hd:
            ep_start = d
        if not e["in_hedge"] and prev_hd:
            print(f"    episode {ep_start} → {arr[i-1]['date']} (n={i-1 - next(k for k, x in enumerate(arr) if x['date']==ep_start)+1})")
            ep_start = None
        prev_hd = e["in_hedge"]
    if ep_start:
        print(f"    episode {ep_start} → OPEN (still in_hedge at {arr[-1]['date']})")

    # ae5f2a0 events on current data
    dd = _to_days_dict(arr)
    try:
        ae5_events = analyze_token_old(sym, dd, drift_min=0.15, struct_n_min=3)
    except Exception as e:
        ae5_events = None
        print(f"  ae5f2a0 analyze_token EXCEPTION: {type(e).__name__}: {e}")
    if ae5_events is not None:
        print(f"  ae5f2a0 code events (on current data): {len(ae5_events)}")
        for e in ae5_events:
            print(f"    {e.get('event_date','?')}  trig={e.get('trigger','?')}  "
                  f"sn={e.get('struct_n','?')}  hedge_start={e.get('hedge_start_date','?')}")

    # 5c2f22d events on current data
    curr_events = []
    for i, r in enumerate(arr):
        d = r["date"]
        if not (WINDOW_START <= d <= WINDOW_END): continue
        if not ok_fn(r.get("pos", NaN)) or not ok_fn(r.get("acc", NaN)): continue
        if i < 5: continue
        # (a) break
        trig = None; sn_ev = None; hspx = None
        if i>=1 and ep[i-1]["in_hedge"] and not ep[i]["in_hedge"]:
            trig="a"; sn_ev=ep[i-1]["struct_n"]; hspx=ep[i-1]["hedge_start_px"]
        # (b) drift
        if trig is None and ep[i]["in_hedge"]:
            eid=ep[i]["episode_id"]; sj=i
            for j in range(i, max(-1, i-30)-1, -1):
                if ep[j].get("episode_id")==eid and ep[j]["in_hedge"]: sj=j
                else: break
            mn=None; mi=None
            for j in range(sj, i+1):
                dv = calc_div(arr, j)
                if ok_fn(dv) and (mn is None or dv<mn): mn=dv; mi=j
            if mn is not None:
                cur = calc_div(arr, i)
                if ok_fn(cur):
                    dr = cur-mn; ds = i-mi
                    if dr>=DRIFT_THR and 0<ds<=DRIFT_WIN:
                        trig="b"; sn_ev=ep[i]["struct_n"]; hspx=ep[i]["hedge_start_px"]
        if trig is None: continue
        # sn filter
        if trig=="a" and sn_ev is not None and sn_ev<3:
            curr_events.append({"date":d, "trig":trig, "sn":sn_ev, "block":f"sn={sn_ev}<3"}); continue
        pos_ok, pos_cur, pos_avg5 = _pos_ok_new(arr, i)
        px_ok, px_cur, px_ref = _px_ok_new(arr, i, hspx)
        if not pos_ok:
            curr_events.append({"date":d, "trig":trig, "sn":sn_ev,
                                "block":f"pos {pos_cur:.3f}/{pos_avg5:.3f}={pos_cur/pos_avg5 if pos_avg5 else 0:.2f}<0.90"})
            continue
        if not px_ok:
            curr_events.append({"date":d, "trig":trig, "sn":sn_ev,
                                "block":f"px {px_cur:.5f}/{px_ref:.5f}={px_cur/px_ref if px_ref else 0:.2f}<0.85"})
            continue
        curr_events.append({"date":d, "trig":trig, "sn":sn_ev, "block":"PASS ✓"})

    print(f"  5c2f22d code events (candidates trước sn/pos/px filter):")
    for e in curr_events:
        print(f"    {e['date']}  trig={e['trig']}  sn={e['sn']}  {e['block']}")

# ─── (2) n_rearm 31→27 root cause ══════════════════════════════════════════
print(f"\n{DIV}\n[Q2] n_rearm 31→27 root cause\n{DIV}")
print(f"  Both probes call same _outcome() function. Δ counts phải từ HOW COUNTED, không _outcome.\n")

# Reproduce sn=3 rearm count with truth _outcome
IGNITE_VOL=5.0; IGNITE_OI=0.30; IGNITE_BRK=0.15
REHEDGE_MIN=5; EXPIRE_DAYS=90; COOLDOWN=3; R2=1.15; R3=1.30

def _try_ignite(arr, j):
    vw = [arr[k]["vol"] for k in range(max(0,j-14),j) if ok_fn(arr[k]["vol"]) and arr[k]["vol"]>0]
    med14 = median(vw) if len(vw)>=7 else None
    cv = arr[j].get("vol", NaN)
    vol_h = ok_fn(cv) and med14 and cv>=IGNITE_VOL*med14
    on = arr[j].get("oi", NaN); o2 = arr[j-2].get("oi", NaN) if j>=2 else NaN
    oi_h = (ok_fn(on) and ok_fn(o2) and o2>0 and (on-o2)/o2>=IGNITE_OI)
    pn = arr[j].get("px", NaN)
    pw = [arr[k]["px"] for k in range(max(0,j-14),j) if ok_fn(arr[k]["px"]) and arr[k]["px"]>0]
    r14 = max(pw) if pw else None
    brk_h = (ok_fn(pn) and r14 and (pn-r14)/r14>=IGNITE_BRK)
    return (vol_h or oi_h or brk_h)

def _try_rearm(arr, i_ig, j):
    if j-i_ig<COOLDOWN: return False
    pw = [arr[k]["px"] for k in range(i_ig,j) if ok_fn(arr[k]["px"]) and arr[k]["px"]>0]
    ow = [arr[k]["oi"] for k in range(i_ig,j) if ok_fn(arr[k]["oi"]) and arr[k]["oi"]>0]
    if not pw or not ow: return False
    pn=arr[j].get("px",NaN); on=arr[j].get("oi",NaN)
    if not (ok_fn(pn) and ok_fn(on)): return False
    return pn/min(pw)>=R2 and on/min(ow)>=R3

def _outcome_truth(arr, ep, ev):
    i0=ev["i"]; max_scan=min(len(arr)-1, i0+EXPIRE_DAYS)
    ignites=[]; rearms=[]; close_reason=None; close_day=None
    wave_ig_i=None; current_wave=1
    for j in range(i0+1, max_scan+1):
        if ep[j]["in_hedge"]:
            eid_j=ep[j].get("episode_id"); eid_ev=ep[i0].get("episode_id") if i0<len(ep) else 0
            if eid_j!=eid_ev and ep[j]["struct_n"]>=REHEDGE_MIN:
                close_reason="RE-HEDGED"; close_day=arr[j]["date"]; break
        ig = _try_ignite(arr, j)
        if ig:
            if not ignites:
                ignites.append({"day":arr[j]["date"], "i":j, "wave_n":1}); wave_ig_i=j; continue
            if wave_ig_i is not None:
                new_rearm=[ra for ra in rearms if ra["i"]>wave_ig_i]
                if new_rearm and j>new_rearm[0]["i"]:
                    current_wave+=1
                    ignites.append({"day":arr[j]["date"], "i":j, "wave_n":current_wave}); wave_ig_i=j; continue
        if wave_ig_i is not None:
            new_rearm=[ra for ra in rearms if ra["i"]>wave_ig_i]
            if not new_rearm:
                if _try_rearm(arr, wave_ig_i, j):
                    rearms.append({"day":arr[j]["date"], "i":j})
    if close_reason is None:
        close_reason="STILL-OPEN" if (max_scan-i0)<EXPIRE_DAYS else "EXPIRED"
    return {"ignites":ignites, "rearms":rearms, "close_reason":close_reason,
            "n_rearms":len(rearms)}

# Run for sn=3 fw-139
ep_cache = {sym: detect_episodes(arr, CFG) for sym, arr in td.items()}

def _detect_ev(arr, ep, i, sn_min):
    d = arr[i]["date"]
    if not (WINDOW_START <= d <= WINDOW_END): return None
    if i<5: return None
    trig=None; sn=None; hspx=None
    if i>=1 and ep[i-1]["in_hedge"] and not ep[i]["in_hedge"]:
        trig="a"; sn=ep[i-1]["struct_n"]; hspx=ep[i-1]["hedge_start_px"]
    if trig is None and ep[i]["in_hedge"]:
        eid=ep[i]["episode_id"]; sj=i
        for j in range(i, max(-1, i-30)-1, -1):
            if ep[j].get("episode_id")==eid and ep[j]["in_hedge"]: sj=j
            else: break
        mn=None; mi=None
        for j in range(sj, i+1):
            dv = calc_div(arr, j)
            if ok_fn(dv) and (mn is None or dv<mn): mn=dv; mi=j
        if mn is not None:
            cur = calc_div(arr, i)
            if ok_fn(cur):
                dr=cur-mn; ds=i-mi
                if dr>=DRIFT_THR and 0<ds<=DRIFT_WIN:
                    trig="b"; sn=ep[i]["struct_n"]; hspx=ep[i]["hedge_start_px"]
    if trig is None: return None
    if trig=="a" and sn is not None and sn<sn_min: return None
    if not _pos_ok_new(arr, i)[0]: return None
    if not _px_ok_new(arr, i, hspx)[0]: return None
    return {"i":i, "date":d, "trig":trig, "sn":sn}

truth_rearms_per_sn = {}
for sn in [3, 4, 5]:
    total = 0
    per_row_counts = []
    for sym, arr in td.items():
        ep = ep_cache[sym]
        for i in range(len(arr)):
            r = arr[i]
            d = r["date"]
            if not (WINDOW_START<=d<=WINDOW_END): continue
            if not ok_fn(r.get("pos",NaN)) or not ok_fn(r.get("acc",NaN)): continue
            ev = _detect_ev(arr, ep, i, sn)
            if ev is None: continue
            oc = _outcome_truth(arr, ep, ev)
            total += oc["n_rearms"]
            if oc["n_rearms"] > 0:
                per_row_counts.append((sym, d, oc["n_rearms"]))
    truth_rearms_per_sn[sn] = {"total": total, "rows": per_row_counts}
    print(f"  sn={sn} truth n_rearms (Σ across rows): {total}  ·  rows với >0 rearm: {len(per_row_counts)}")

# Report
print(f"\n  d98c170 T3 reported: sn=3 → 31, sn=4/5 → 27")
print(f"  5c2f22d T3 reported: sn=3/4/5 → 27")
print(f"  truth (this probe):  sn=3 → {truth_rearms_per_sn[3]['total']}, "
      f"sn=4 → {truth_rearms_per_sn[4]['total']}, sn=5 → {truth_rearms_per_sn[5]['total']}")
print()
print(f"  → Nếu truth = 27 cả 3 sn: d98c170 T3 counting BUG (over-count 4). 5c2f22d fix.")
print(f"  → Nếu truth = 31 (sn=3): 5c2f22d probe DROP một số rearms (counting bug ngược lại).")

print(f"\n{DIV}\nDONE. KHÔNG SỬA GÌ. DỪNG.\n{DIV}")
