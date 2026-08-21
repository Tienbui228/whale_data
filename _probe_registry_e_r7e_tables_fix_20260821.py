#!/usr/bin/env python3
"""[E-R7e-tables-fix] T3 gap-split · T2 m? detail + strict m3 · T0 5 token lệch.

Spec v1.2-FINAL 46db911 · probe d98c170 · [local_low=D-1]. No CSV output.
"""
from __future__ import annotations
import sys, io, csv, math, re, subprocess
from pathlib import Path
from statistics import mean, median
from datetime import date, timedelta

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = Path(r"D:\Data back test\whale_data")
sys.path.insert(0, str(REPO))
from lib.hedge_episode import detect_episodes, calc_div, NaN, ok

TMP = Path(r"C:\Users\Hello\AppData\Local\Temp\e_r7_20260819")
WINDOW_START = "2026-06-21"; WINDOW_END = "2026-08-19"

# Constants (from spec v1.2-FINAL)
R2=1.15; R3=1.30; COOLDOWN=3
DRIFT_THR=0.15; DRIFT_WIN=7; POS_HOLD=0.90; PX_HOLD=0.85
IGNITE_VOL=5.0; IGNITE_OI=0.30; IGNITE_BRK=0.15
REHEDGE_MIN=5; EXPIRE_DAYS=90; MISS_WAVE_DAYS=21

DIV = "═"*96
print(f"{DIV}\n[HEADER] spec v1.2-FINAL 46db911 · probe d98c170 [local_low=D-1]\n"
      f"          date-range {WINDOW_START} → {WINDOW_END}\n{DIV}")

# ─── Load data ─────────────────────────────────────────────────────────────
td = {}
for m in ["06","07","08"]:
    p = TMP / f"freshwatch_daily_2026-{m}.csv"
    with open(p, encoding="utf-8", errors="replace") as f:
        for r in csv.DictReader(f):
            sym = r.get("symbol","");
            if not sym: continue
            def _f(k):
                try: return float(r[k])
                except: return NaN
            td.setdefault(sym, []).append({
                "date": r.get("date",""), "px": _f("px_avg"),
                "pos": _f("lsr_pos_r"), "acc": _f("lsr_acc_r"),
                "oi": _f("oi_usd"), "vol": _f("vol_quote"),
            })
for sym in td: td[sym].sort(key=lambda r: r["date"])
with open(TMP / "freshwatch_symbols_vps.txt", encoding="utf-8", errors="replace") as f:
    universe = sorted({l.strip() for l in f if l.strip() and not l.startswith("#")})
td = {s: v for s, v in td.items() if len(v) >= 14 and s in universe}
UNI_N = len(td)
CFG = {"hedge": {"div_ratio_max": 0.5, "episode_break_days": 3}}
ep_cache = {sym: detect_episodes(arr, CFG) for sym, arr in td.items()}

# ─── Reuse logic (compact) ─────────────────────────────────────────────────
def _cur_ep_min(arr, ep, i, lb=30):
    if not ep[i]["in_hedge"]: return None
    eid = ep[i]["episode_id"]; sj = i
    for j in range(i, max(-1, i-lb)-1, -1):
        if ep[j].get("episode_id")==eid and ep[j]["in_hedge"]: sj=j
        else: break
    mn=None; mi=None
    for j in range(sj, i+1):
        d = calc_div(arr, j)
        if ok(d) and (mn is None or d<mn): mn=d; mi=j
    return {"start_i":sj,"min_i":mi,"min_div":mn}

def _pos_ok(arr, i):
    cur = arr[i].get("pos", NaN)
    if not ok(cur): return False
    vs = [arr[j]["pos"] for j in range(max(0,i-5),i) if ok(arr[j]["pos"])]
    if len(vs)<3: return False
    return cur >= POS_HOLD * mean(vs)

def _px_ok(arr, i, hspx):
    cur = arr[i].get("px", NaN)
    return ok(cur) and hspx and ok(hspx) and cur >= PX_HOLD * hspx

def _detect_ev(arr, ep, i, sn_min, no_cd_filter=False):
    d = arr[i]["date"]
    if not (WINDOW_START <= d <= WINDOW_END): return None
    if i<5: return None
    trig=None; sn=None; hspx=None
    if i>=1 and ep[i-1]["in_hedge"] and not ep[i]["in_hedge"]:
        trig="a"; sn=ep[i-1]["struct_n"]; hspx=ep[i-1]["hedge_start_px"]
    if trig is None and ep[i]["in_hedge"]:
        info = _cur_ep_min(arr, ep, i)
        if info and info["min_i"] is not None and info["min_div"] is not None:
            cur=calc_div(arr,i)
            if ok(cur):
                dr=cur-info["min_div"]; ds=i-info["min_i"]
                if dr>=DRIFT_THR and 0<ds<=DRIFT_WIN:
                    trig="b"; sn=ep[i]["struct_n"]; hspx=ep[i]["hedge_start_px"]
    if trig is None: return None
    if not no_cd_filter and trig=="a" and sn is not None and sn<sn_min: return None
    if not (_pos_ok(arr,i) and _px_ok(arr,i,hspx)): return None
    return {"i":i, "date":d, "trig":trig, "sn":sn}

def _try_ignite(arr, j):
    vw = [arr[k]["vol"] for k in range(max(0,j-14),j) if ok(arr[k]["vol"]) and arr[k]["vol"]>0]
    med14 = median(vw) if len(vw)>=7 else None
    cv = arr[j].get("vol", NaN)
    vol_h = ok(cv) and med14 and cv>=IGNITE_VOL*med14
    on = arr[j].get("oi", NaN); o2 = arr[j-2].get("oi", NaN) if j>=2 else NaN
    oi_h = (ok(on) and ok(o2) and o2>0 and (on-o2)/o2>=IGNITE_OI)
    pn = arr[j].get("px", NaN)
    pw = [arr[k]["px"] for k in range(max(0,j-14),j) if ok(arr[k]["px"]) and arr[k]["px"]>0]
    r14 = max(pw) if pw else None
    brk_h = (ok(pn) and r14 and (pn-r14)/r14>=IGNITE_BRK)
    return (vol_h or oi_h or brk_h)

def _try_rearm(arr, i_ig, j):
    ds = j-i_ig
    if ds<COOLDOWN: return False
    pw = [arr[k]["px"] for k in range(i_ig,j) if ok(arr[k]["px"]) and arr[k]["px"]>0]
    ow = [arr[k]["oi"] for k in range(i_ig,j) if ok(arr[k]["oi"]) and arr[k]["oi"]>0]
    if not pw or not ow: return False
    pn=arr[j].get("px",NaN); on=arr[j].get("oi",NaN)
    if not (ok(pn) and ok(on)): return False
    return pn/min(pw)>=R2 and on/min(ow)>=R3

def _outcome(arr, ep, ev):
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
                    rearms.append({"day":arr[j]["date"], "i":j, "for_wave":current_wave})
    if close_reason is None:
        if (max_scan-i0)>=EXPIRE_DAYS:
            close_reason="EXPIRED"; close_day=arr[max_scan]["date"]
        else:
            close_reason="STILL-OPEN"
    return {"ignites":ignites, "rearms":rearms, "close_reason":close_reason,
            "close_day":close_day, "n_waves":len(ignites), "n_rearms":len(rearms)}

def run_bf(sn_min):
    rows=[]
    for sym,arr in td.items():
        ep=ep_cache[sym]
        for i,r in enumerate(arr):
            d=r["date"]
            if not (WINDOW_START<=d<=WINDOW_END): continue
            if not ok(r.get("pos",NaN)) or not ok(r.get("acc",NaN)): continue
            ev = _detect_ev(arr, ep, i, sn_min)
            if ev is None: continue
            ev["sym"]=sym; ev["outcome"]=_outcome(arr, ep, ev)
            rows.append(ev)
    return rows

# ═══ [T0] 5 tokens lệch 36→41 (ae5f2a0 vs d98c170) ═══════════════════════
print(f"\n{DIV}\n[T0] 5 tokens lệch sn=3: ae5f2a0 (36 unique) → d98c170 (41 unique)\n{DIV}")

# ae5f2a0 token list extracted từ commit CSV (grep '^\+[A-Z0-9]+USDT,')
AE5F2A0_TOKENS = {
    "4","ACU","AIN","AIO","ARIA","BMT","BTR","BULLA","CARV","COLLECT","COOKIE","DOOD",
    "FHE","GUA","HEMI","INX","IRYS","KOMA","MERL","MIRA","NEWT","ON","POWER","PTB",
    "RAVE","SHELL","SIGN","SPACE","SQD","STAR","TAIKO","TAKE","TRADOOR","TURTLE","UAI","XAN"
}  # n=36
print(f"  ae5f2a0 baseline (E-R7c 20/08): {len(AE5F2A0_TOKENS)} tokens")
for t in sorted(AE5F2A0_TOKENS): print(f"    ae5f2a0: {t}USDT")

# Current sn=3
rows_sn3 = run_bf(sn_min=3)
current_tokens = sorted({r["sym"][:-4] if r["sym"].endswith("USDT") else r["sym"] for r in rows_sn3})
current_set = set(current_tokens)
print(f"\n  d98c170 current sn=3: {len(current_set)} tokens")

added = sorted(current_set - AE5F2A0_TOKENS)
removed = sorted(AE5F2A0_TOKENS - current_set)
common = sorted(AE5F2A0_TOKENS & current_set)

print(f"\n  common: {len(common)} tokens")
print(f"  ADDED in d98c170: {len(added)} → {added}")
print(f"  REMOVED (in ae5f2a0 but NOT in d98c170): {len(removed)} → {removed}")

# For each ADDED, print sn of first event
print(f"\n  Detail ADDED tokens (sn of first event, likely reason):")
for tok in added:
    sym = tok + "USDT" if not tok.endswith("USDT") else tok
    ev_rows = [r for r in rows_sn3 if r["sym"] == sym]
    if not ev_rows: continue
    first = min(ev_rows, key=lambda x: x["date"])
    print(f"    {tok:<12} first_event {first['date']} trig={first['trig']} sn={first['sn']}"
          f"  (sn=3 filter passed with sn={first['sn']}≥3)")

# For each REMOVED, why now missing
print(f"\n  Detail REMOVED tokens (why not in current sn=3):")
for tok in removed:
    sym = tok + "USDT" if not tok.endswith("USDT") else tok
    if sym not in td:
        print(f"    {tok:<12} NOT IN td (universe filter or missing history)")
        continue
    # Run detect with no sn filter
    ep = ep_cache[sym]; arr = td[sym]
    found = []
    for i, r in enumerate(arr):
        d = r["date"]
        if not (WINDOW_START <= d <= WINDOW_END): continue
        if not ok(r.get("pos", NaN)) or not ok(r.get("acc", NaN)): continue
        ev_nofilter = _detect_ev(arr, ep, i, sn_min=1, no_cd_filter=True)
        if ev_nofilter: found.append(ev_nofilter)
    if not found:
        print(f"    {tok:<12} 0 events even sn=1 (drift/pos/px fail hoặc episode logic)")
    else:
        for f in found[:2]:
            print(f"    {tok:<12} event {f['date']} trig={f['trig']} sn={f['sn']}"
                  f" — {'BLOCKED sn<3' if f['trig']=='a' and (f['sn'] or 0)<3 else 'other'}")

# ═══ [T2] m?=10 detail + STILL-OPEN bug + strict m3 rerun ══════════════════
print(f"\n{DIV}\n[T2] MISSED-WAVE m? detail + STILL-OPEN bug + strict m3 rerun\n{DIV}")
print(f"  ANALYSIS strict m3: 'không hedged ∧ không event vào'")
print(f"  Trước fix: chỉ classify m3 nếu row.close_reason=RE-HEDGED. STILL-OPEN → lỡ.")

main = rows_sn3
def audit_v3(r):
    """Fixed classifier: all closed OR still-open rows scanned; strict m3."""
    close_reason = r["outcome"]["close_reason"]
    # STILL-OPEN row: still audit MISS after ignite (spec says row IGNITED closed = miss;
    # but if STILL-OPEN and no new wave detected, later pump = miss too — CHỌN "audit all")
    if close_reason == "STILL-OPEN":
        # miss audit starts from LAST ignite (if any) OR from event day
        if r["outcome"]["ignites"]:
            start_idx = r["outcome"]["ignites"][-1]["i"]
            audit_reason = "STILL-OPEN post-last-ignite"
        else:
            start_idx = r["i"]
            audit_reason = "STILL-OPEN no-ignite"
    else:
        close_d = r["outcome"]["close_day"]
        if not close_d: return []
        arr = td[r["sym"]]
        start_idx = next((k for k,x in enumerate(arr) if x["date"]==close_d), None)
        if start_idx is None: return []
        audit_reason = f"post-{close_reason}"

    arr = td[r["sym"]]; ep = ep_cache[r["sym"]]
    end = min(len(arr)-1, start_idx+MISS_WAVE_DAYS)
    misses = []
    for j in range(start_idx+1, end+1):
        vw = [arr[k]["vol"] for k in range(max(0,j-14),j) if ok(arr[k]["vol"]) and arr[k]["vol"]>0]
        med14 = median(vw) if len(vw)>=7 else None
        cv = arr[j].get("vol", NaN)
        if not (ok(cv) and med14 and cv>=IGNITE_VOL*med14): continue

        # STRICT m3 per ANALYSIS: không hedged ∧ không event vào registry
        div_at = calc_div(arr, j)
        hedged = ok(div_at) and div_at <= 0.5
        # scan 7d before miss for event candidate
        ev_candidates = []
        for jj in range(max(0, j-7), j+1):
            ec = _detect_ev(arr, ep, jj, sn_min=1, no_cd_filter=True)
            if ec: ev_candidates.append(ec)
        # would sn=3 catch any?
        got_sn3 = any(_detect_ev(arr, ep, ec["i"], sn_min=3) is not None for ec in ev_candidates)

        if hedged:
            cat = "m1"; block = f"hedged div={div_at:.3f}"
        elif close_reason == "EXPIRED":
            cat = "m2"; block = "EXPIRED-then-pump"
        elif not got_sn3:
            # không event sn=3 vào = m3 THẬT
            cat = "m3"
            if ev_candidates:
                ec = ev_candidates[0]
                if ec["trig"]=="a" and (ec["sn"] or 0)<3:
                    block = f"sn={ec['sn']}<3 blocked"
                else:
                    block = f"pos/px fail trig={ec['trig']}"
            else:
                block = "no event candidate (drift/pos/px all fail)"
        else:
            cat = "m?"; block = "sn=3 CAUGHT event but STILL-OPEN"

        misses.append({"sym":r["sym"], "row_ev":r["date"], "close_reason":close_reason,
                       "close_day":r["outcome"]["close_day"], "audit_start":audit_reason,
                       "miss_day":arr[j]["date"], "div_at":div_at, "vol_mult":cv/med14,
                       "hedged":hedged, "cat":cat, "block":block, "n_candidates":len(ev_candidates)})
    return misses

all_miss = []
for r in main:
    for m in audit_v3(r): all_miss.append(m)

from collections import Counter
cat_ct = Counter(m["cat"] for m in all_miss)

# STILL-OPEN bug detection
still_open_misses = [m for m in all_miss if m["close_reason"] == "STILL-OPEN"]
print(f"\n  STILL-OPEN rows in MISSED-WAVE log = {len(still_open_misses)} (audit v3 fixed classify)")
print(f"  before-fix (audit v1): STILL-OPEN skipped entirely → 29 miss (only closed rows)")
print(f"  after-fix (audit v3):  STILL-OPEN also audited → {len(all_miss)} miss total")

print(f"\n  Strict m3 rerun (không hedged ∧ không event sn=3 vào):")
for cat in ["m1","m2","m3","m?"]:
    n = cat_ct.get(cat, 0)
    label = {"m1":"pump WHILE hedged (out-of-scope, GOM-D)",
             "m2":"EXPIRED then pump (calib 90d)",
             "m3":"registry miss THẬT (không hedged ∧ event sn=3 không bắt)",
             "m?":"STILL-OPEN + sn=3 CAUGHT event nhưng vẫn miss (bug row hay double-count)"}[cat]
    print(f"    {cat}: {n:>2}  — {label}")

# Detail m? rows
mq = [m for m in all_miss if m["cat"] == "m?"]
if mq:
    print(f"\n  Detail m? = {len(mq)} rows (STILL-OPEN + sn=3 caught but miss logged):")
    for m in mq[:15]:
        print(f"    {m['sym']:<14} row_ev={m['row_ev']} close={m['close_reason']:<12} "
              f"miss@{m['miss_day']} div={m['div_at']:.3f} vol×{m['vol_mult']:.1f} n_cand={m['n_candidates']}")

# Detail m3 THẬT rows (strict miss)
m3_rows = [m for m in all_miss if m["cat"] == "m3"]
if m3_rows:
    print(f"\n  Detail m3 THẬT ({len(m3_rows)} strict miss):")
    for m in m3_rows[:20]:
        print(f"    {m['sym']:<14} row_ev={m['row_ev']} close={m['close_reason']:<12} "
              f"miss@{m['miss_day']} vol×{m['vol_mult']:.1f} n_cand={m['n_candidates']} block={m['block']}")

# ═══ [T3] gap-split ≤1d vs ≥2d + row vs event ══════════════════════════
print(f"\n{DIV}\n[T3] Re-arm gap split (≤1d = ignite tự-arm vs ≥2d = re-arm đứng riêng)\n{DIV}")
print(f"  Notation: n_rearm-EVENTS = tổng re-arm events across rows (multi-rearm possible)")
print(f"            n_rearm-ROWS   = rows có ≥1 re-arm (unique row count)")

for sn in [3,4,5]:
    rows = run_bf(sn_min=sn)
    gap_le1 = []; gap_ge2 = []
    dead_le1 = 0; dead_ge2 = 0
    prod_le1 = 0; prod_ge2 = 0
    dead_le1_close = {"RE-HEDGED":0,"EXPIRED":0,"STILL-OPEN":0}
    dead_ge2_close = {"RE-HEDGED":0,"EXPIRED":0,"STILL-OPEN":0}
    not_ripe_le1 = 0; not_ripe_ge2 = 0
    n_rearm_rows = 0
    for r in rows:
        arr = td[r["sym"]]
        rearms = r["outcome"]["rearms"]
        if rearms: n_rearm_rows += 1
        for ra in rearms:
            # find NEXT ignite for this row that has i > ra_i
            next_ig = [ig for ig in r["outcome"]["ignites"] if ig["i"] > ra["i"]]
            gap_ig = (next_ig[0]["i"] - ra["i"]) if next_ig else None

            # SPLIT BY re-arm → next-ignite GAP per operator
            #   gap≤1 = "ignite tự-arm" (re-arm ngay hoặc D+1 có ignite)
            #   gap≥2 = "re-arm đứng riêng" (bounces first, ignites later)
            if gap_ig is not None and gap_ig <= 1:
                bucket = "le1"
            else:
                bucket = "ge2"

            if gap_ig is not None and gap_ig <= MISS_WAVE_DAYS:
                if bucket == "le1":
                    gap_le1.append(gap_ig); prod_le1 += 1
                else:
                    gap_ge2.append(gap_ig); prod_ge2 += 1
            else:
                # dead or not-ripe (no ignite ≤21d)
                last_i = len(arr)-1
                if last_i - ra["i"] < MISS_WAVE_DAYS:
                    # not enough time to judge
                    not_ripe_ge2 += 1
                else:
                    dead_ge2 += 1
                    dead_ge2_close[r["outcome"]["close_reason"]] = dead_ge2_close.get(r["outcome"]["close_reason"], 0) + 1

    n_ev_total = len(gap_le1) + len(gap_ge2) + dead_le1 + dead_ge2 + not_ripe_le1 + not_ripe_ge2
    denom_le1 = len(gap_le1) + dead_le1
    denom_ge2 = len(gap_ge2) + dead_ge2

    print(f"\n  sn={sn}:")
    print(f"    n_rearm-EVENTS: {n_ev_total}  ·  n_rearm-ROWS: {n_rearm_rows} (rows unique có ≥1 rearm)")
    print(f"    {'group':>10}  {'n_events':>8}  {'productive':>10}  {'%':>6}  {'gap min/med/max':>18}  "
          f"{'dead':>5}  {'chưa đủ 21d':>12}")
    if denom_le1 > 0:
        pct_le1 = prod_le1 / denom_le1 * 100
        gs = gap_le1
        gm = (min(gs) if gs else "-", int(median(gs)) if gs else "-", max(gs) if gs else "-")
        print(f"    {'gap≤1d':>10}  {denom_le1+not_ripe_le1:>8}  {prod_le1:>10}  {pct_le1:>5.1f}%  "
              f"{gm[0]}/{gm[1]}/{gm[2]:<10}  {dead_le1:>5}  {not_ripe_le1:>12}")
    else:
        print(f"    {'gap≤1d':>10}  {not_ripe_le1:>8}  0  -  -  -  {not_ripe_le1:>12}")
    if denom_ge2 > 0:
        pct_ge2 = prod_ge2 / denom_ge2 * 100
        gs = gap_ge2
        gm = (min(gs) if gs else "-", int(median(gs)) if gs else "-", max(gs) if gs else "-")
        print(f"    {'gap≥2d':>10}  {denom_ge2+not_ripe_ge2:>8}  {prod_ge2:>10}  {pct_ge2:>5.1f}%  "
              f"{gm[0]}/{gm[1]}/{gm[2]:<10}  {dead_ge2:>5}  {not_ripe_ge2:>12}")
    else:
        print(f"    {'gap≥2d':>10}  {not_ripe_ge2:>8}  0  -  -  -  {not_ripe_ge2:>12}")

print(f"\n{DIV}\nDONE. DỪNG.\n{DIV}")
