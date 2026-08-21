#!/usr/bin/env python3
"""[E-R7e-tables] T0/T1/T2/T3 tables (spec v1.2-FINAL, probe commit 382fd61).

Reuse logic from _probe_registry_backfill_e_r7e_20260821.py — call via import.
KHÔNG chữ ký mới, KHÔNG đổi spec, KHÔNG chấm. Bảng số + tử/mẫu + flag biên.
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
SPEC_FILE = REPO / "proposals" / "unhedge_registry_spec_v1.0.md"

WINDOW_START = "2026-06-21"
WINDOW_END   = "2026-08-19"

# ─── HEADER (self-declare) ──────────────────────────────────────────────────
spec = SPEC_FILE.read_text(encoding="utf-8")
_m_r2 = re.search(r"\(r2\) px_close / local_low_px ≥ ([\d.]+)", spec)
_m_r3 = re.search(r"\(r3\) oi_usd  / local_low_oi  ≥ ([\d.]+)", spec)
_m_cd = re.search(r"cooldown tối thiểu (\d+)d", spec)
R2 = float(_m_r2.group(1)); R3 = float(_m_r3.group(1)); COOLDOWN = int(_m_cd.group(1))

try:
    git_commit = subprocess.check_output(["git","rev-parse","--short","HEAD"],
                                          cwd=REPO, text=True).strip()
except: git_commit = "?"

DIV = "═"*96
print(f"{DIV}\n[HEADER] spec v1.2-FINAL · commit 46db911 · probe 382fd61+tables ({git_commit})\n"
      f"          date-range {WINDOW_START} → {WINDOW_END} · [local_low=D-1]\n{DIV}")

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
sympath = TMP / "freshwatch_symbols_vps.txt"
with open(sympath, encoding="utf-8", errors="replace") as f:
    universe = sorted({l.strip() for l in f if l.strip() and not l.startswith("#")})
td = {s: v for s, v in td.items() if len(v) >= 14 and s in universe}
UNI_N = len(td)

CFG = {"hedge": {"div_ratio_max": 0.5, "episode_break_days": 3}}
ep_cache = {sym: detect_episodes(arr, CFG) for sym, arr in td.items()}

# Constants
DRIFT_THR=0.15; DRIFT_WIN=7; POS_HOLD=0.90; PX_HOLD=0.85
IGNITE_VOL=5.0; IGNITE_OI=0.30; IGNITE_BRK=0.15
REHEDGE_MIN=5; EXPIRE_DAYS=90; MISS_WAVE_DAYS=21

def _cur_ep_min(arr, ep, i, lb=30):
    if not ep[i]["in_hedge"]: return None
    eid = ep[i]["episode_id"]; sj = i
    for j in range(i, max(-1, i-lb)-1, -1):
        if ep[j].get("episode_id")==eid and ep[j]["in_hedge"]: sj = j
        else: break
    mn=None; mi=None
    for j in range(sj, i+1):
        d = calc_div(arr, j)
        if ok(d) and (mn is None or d < mn): mn=d; mi=j
    return {"start_i":sj, "min_i":mi, "min_div":mn}

def _pos_ok(arr, i):
    cur = arr[i].get("pos", NaN)
    if not ok(cur): return False
    vs = [arr[j]["pos"] for j in range(max(0,i-5),i) if ok(arr[j]["pos"])]
    if len(vs)<3: return False
    return cur >= POS_HOLD * mean(vs)

def _px_ok(arr, i, hspx):
    cur = arr[i].get("px", NaN)
    return ok(cur) and hspx and ok(hspx) and cur >= PX_HOLD * hspx

def _detect_ev(arr, ep, i, sn_min):
    d = arr[i]["date"]
    if not (WINDOW_START <= d <= WINDOW_END): return None
    if i < 5: return None
    trig=None; sn=None; hspx=None
    if i>=1 and ep[i-1]["in_hedge"] and not ep[i]["in_hedge"]:
        trig="a"; sn=ep[i-1]["struct_n"]; hspx=ep[i-1]["hedge_start_px"]
    if trig is None and ep[i]["in_hedge"]:
        info = _cur_ep_min(arr, ep, i)
        if info and info["min_i"] is not None and info["min_div"] is not None:
            cur = calc_div(arr, i)
            if ok(cur):
                dr = cur-info["min_div"]; ds = i-info["min_i"]
                if dr>=DRIFT_THR and 0<ds<=DRIFT_WIN:
                    trig="b"; sn=ep[i]["struct_n"]; hspx=ep[i]["hedge_start_px"]
    if trig is None: return None
    if trig=="a" and sn is not None and sn<sn_min: return None
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
    i0 = ev["i"]; max_scan = min(len(arr)-1, i0+EXPIRE_DAYS)
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
                new_rearm = [ra for ra in rearms if ra["i"]>wave_ig_i]
                if new_rearm and j>new_rearm[0]["i"]:
                    current_wave+=1
                    ignites.append({"day":arr[j]["date"], "i":j, "wave_n":current_wave}); wave_ig_i=j; continue
        if wave_ig_i is not None:
            new_rearm = [ra for ra in rearms if ra["i"]>wave_ig_i]
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
            ev["sym"]=sym
            oc = _outcome(arr, ep, ev)
            ev["outcome"]=oc
            rows.append(ev)
    return rows

# ═══ [T0a] PROVENANCE truy "25.9%" ═══════════════════════════════════════
print(f"\n{DIV}\n[T0a] PROVENANCE '25.9%' baseline sn=3\n{DIV}")
print(f"  git commit ae5f2a0 (E-R7c 2026-08-20) body:")
print(f"    'Baseline (drift=0.15, struct_n≥3): 50 entries · 36 tokens · 25.9% universe'")
print(f"    '0.15   39   11   50     36      25.9%  74.0%   25.9%  ←baseline'")
print(f"  → 25.9% = 36 tokens (unique) / 139 universe = 25.9%")
print(f"  công thức = unique_tokens_with_events / universe (KHÔNG rows, KHÔNG week-peak)")
print(f"  [DATA] ae5f2a0 commit body")

# ═══ [T0b] SWEEP sn={3,4,5} với reg%_weekpeak + reg%_cum ═════════════════
print(f"\n{DIV}\n[T0b] SWEEP sn={{3,4,5}} · reg%_weekpeak (§E-R8②) + reg%_cum (unique/universe)\n{DIV}")

def compute_reg_metrics(rows):
    # reg%_cum = unique tokens with any row / universe
    uniq_tok = {r["sym"] for r in rows}
    cum_pct = len(uniq_tok) / UNI_N * 100
    # reg%_weekpeak: for each ISO week, unique symbols with "row sống" trong tuần đó
    open_by_wk = {}
    for r in rows:
        d0 = date.fromisoformat(r["date"])
        close_d = date.fromisoformat(r["outcome"]["close_day"]) if r["outcome"]["close_day"] else date.fromisoformat(WINDOW_END)
        cur = d0
        while cur <= close_d and cur <= date.fromisoformat(WINDOW_END):
            wk = cur.strftime("%Y-W%V")
            open_by_wk.setdefault(wk, set()).add(r["sym"])
            cur += timedelta(days=1)
    if not open_by_wk: return cum_pct, 0.0, None, len(uniq_tok)
    peak_wk = max(open_by_wk.items(), key=lambda x: len(x[1]))
    peak_pct = len(peak_wk[1]) / UNI_N * 100
    return cum_pct, peak_pct, peak_wk[0], len(uniq_tok)

sweeps = {}
print(f"  {'sn':>3}  {'n_rows':>6}  {'uniq_tok':>8}  {'reg%_cum':>18}  {'reg%_weekpeak':>25}  {'peak_wk':>10}")
print("  " + "─"*80)
for sn in [3,4,5]:
    rows = run_bf(sn_min=sn)
    cum_pct, peak_pct, peak_wk, n_uniq = compute_reg_metrics(rows)
    sweeps[sn] = {"rows":rows, "cum_pct":cum_pct, "peak_pct":peak_pct, "peak_wk":peak_wk, "n_uniq":n_uniq}
    print(f"  {sn:>3}  {len(rows):>6}  {n_uniq:>8}  {n_uniq}/{UNI_N} = {cum_pct:>5.1f}%  "
          f"{peak_pct:>5.1f}% at {peak_wk} ({sum(1 for _r in rows if peak_wk == '?' or True):>3}/tuần?)")

# reprint peak count exactly
print(f"\n  peak-week detail (tokens tuần đông nhất):")
for sn in [3,4,5]:
    s = sweeps[sn]
    print(f"    sn={sn}: peak {s['peak_wk']} = {int(s['peak_pct']*UNI_N/100)}/{UNI_N} = {s['peak_pct']:.1f}%")

# ═══ [T0c] PRE-FIX vs POST-FIX wave_n bug ═══════════════════════════════
print(f"\n{DIV}\n[T0c] PRE-FIX vs POST-FIX wave_n (inline fix earlier turn)\n{DIV}")
print(f"  Bug: pre-fix đếm mọi ignite-continuation là wave riêng (không cần re-arm mới)")
print(f"  Fix: yêu cầu NEW re-arm > last wave_ig_i mới count wave mới\n")
print(f"  {'metric':>30}  {'pre-fix':>10}  {'post-fix':>10}  {'Δ':>7}")
print("  " + "─"*72)
# Pre-fix numbers từ probe run đầu (đã có trong /tmp/e_r7e_out.txt)
# Post-fix from _out2.txt
prefix = {
    "E4b alerts ON": (98, 57, 98-57),
    "E4b hit_k7 ON pct": (37.8, 35.1, 37.8-35.1),
    "E4d wave-1 hit_k7 pct": (32.4, 32.4, 0),
    "E4d wave-2 hit_k7 pct": (41.0, 40.0, 1.0),
    "E5 sn=3 alerts": (98, 57, 41),
    "E5 sn=4 alerts": (97, 56, 41),
    "E5 sn=5 alerts": (96, 55, 41),
    "HEMI wave_n": (6, 2, 4),
}
for k,(pre,post,d) in prefix.items():
    print(f"  {k:>30}  {pre:>10}  {post:>10}  {d:>+7}")

# ═══ [T1] MFE_k7 per-alert ═══════════════════════════════════════════════
print(f"\n{DIV}\n[T1] MFE_k7 per-alert (close-basis vì freshwatch không expose high)\n{DIV}")
print(f"  Công thức: MFE_k7 = max(close_{{D+1..D+7}}) / close_D − 1  [close-basis-MFE]")
print(f"  Song song: ret_k7 = close_{{D+7}} / close_D − 1 (baseline cũ)")

def wave_alerts(rows):
    """List of (sym, ignite_idx, wave_n)."""
    out = []
    for r in rows:
        arr = td[r["sym"]]
        for ig in r["outcome"]["ignites"]:
            out.append({"sym":r["sym"], "i":ig["i"], "wave_n":ig["wave_n"], "arr":arr})
    return out

def calc_mfe_ret(alerts):
    """Return list of (mfe, ret) per alert."""
    out = []
    for a in alerts:
        arr = a["arr"]; i = a["i"]
        p0 = arr[i].get("px", NaN)
        if not ok(p0) or p0<=0: continue
        end = min(len(arr)-1, i+7)
        forwards = [arr[k].get("px", NaN) for k in range(i+1, end+1) if ok(arr[k].get("px", NaN)) and arr[k].get("px", NaN)>0]
        if not forwards: continue
        mfe = max(forwards)/p0 - 1
        ret = arr[end].get("px", NaN)/p0 - 1 if ok(arr[end].get("px", NaN)) else NaN
        out.append({"wave_n":a["wave_n"], "mfe":mfe, "ret":ret, "sym":a["sym"]})
    return out

alerts_sn3 = wave_alerts(sweeps[3]["rows"])
mfe_data = calc_mfe_ret(alerts_sn3)
print(f"\n  All alerts sn=3: n={len(mfe_data)}")
print(f"  {'wave':>6}  {'n':>3}  {'MFE≥+10%':>12}  {'%':>7}  {'med_MFE':>10}  {'ret_k7>0':>10}  {'%':>7}  {'med_ret':>10}")
print("  " + "─"*90)
for w in [1, 2]:
    w_alerts = [x for x in mfe_data if x["wave_n"] == w]
    if not w_alerts:
        print(f"  {w:>6}  0  no alerts")
        continue
    n = len(w_alerts)
    n_mfe10 = sum(1 for x in w_alerts if x["mfe"] >= 0.10)
    pct_mfe = n_mfe10/n*100
    med_mfe = median(x["mfe"] for x in w_alerts)
    n_ret_pos = sum(1 for x in w_alerts if ok(x["ret"]) and x["ret"]>0)
    pct_ret = n_ret_pos/n*100
    valid_rets = [x["ret"] for x in w_alerts if ok(x["ret"])]
    med_ret = median(valid_rets) if valid_rets else NaN
    print(f"  {w:>6}  {n:>3}  {n_mfe10}/{n:<3}  {pct_mfe:>5.1f}%  {med_mfe*100:>+6.1f}%  "
          f"{n_ret_pos}/{n:<3}  {pct_ret:>5.1f}%  {med_ret*100:>+6.1f}%")
w2plus = [x for x in mfe_data if x["wave_n"] >= 2]
if w2plus:
    n = len(w2plus)
    n_mfe10 = sum(1 for x in w2plus if x["mfe"] >= 0.10)
    med_mfe = median(x["mfe"] for x in w2plus)
    print(f"  {'wave-2+':>6}  {n:>3}  {n_mfe10}/{n:<3}  {n_mfe10/n*100:>5.1f}%  {med_mfe*100:>+6.1f}%  (aggregate)")
print(f"  Ngưỡng 40% CHƯA ký — chỉ in.")

# ═══ [T2] 29 MISSED-WAVE breakdown (m1/m2/m3) ══════════════════════════
print(f"\n{DIV}\n[T2] MISSED-WAVE breakdown 3 nguyên nhân (m1/m2/m3)\n{DIV}")
print(f"  Định nghĩa 'đang hedged' tại ngày pump: div_avg3 tại D ≤ 0.5 (canonical)")
print(f"  Cửa sổ audit: sau close-day 21d, xét pump vol ≥ 5×med14")
print()

# Recompute MISSED-WAVE for sn=3
main = sweeps[3]["rows"]
def audit_miss_wave_v2(r):
    """For each closed row, scan 21d after close for vol ≥5×med14 → miss."""
    if r["outcome"]["close_reason"] not in ("RE-HEDGED", "EXPIRED"): return []
    close_d = r["outcome"]["close_day"]
    if not close_d: return []
    arr = td[r["sym"]]
    ep = ep_cache[r["sym"]]
    c_i = next((k for k,x in enumerate(arr) if x["date"]==close_d), None)
    if c_i is None: return []
    end = min(len(arr)-1, c_i+MISS_WAVE_DAYS)
    misses = []
    for j in range(c_i+1, end+1):
        vw = [arr[k]["vol"] for k in range(max(0,j-14),j) if ok(arr[k]["vol"]) and arr[k]["vol"]>0]
        med14 = median(vw) if len(vw)>=7 else None
        cv = arr[j].get("vol", NaN)
        if not (ok(cv) and med14 and cv>=IGNITE_VOL*med14): continue
        # Classify:
        # m1: pump WHILE hedged at pump day
        div_at_pump = calc_div(arr, j)
        hedged = ok(div_at_pump) and div_at_pump <= 0.5
        # m2: close was EXPIRED (90d timeout, then pumped)
        expired_then_pump = (r["outcome"]["close_reason"] == "EXPIRED")
        # m3: close was RE-HEDGED, un-hedge again (new episode ended by pump day) but no event
        if r["outcome"]["close_reason"] == "RE-HEDGED":
            # check: at pump day j, was there a NEW un-hedge event that got blocked?
            new_ev_i = None
            for jj in range(c_i+1, j+1):
                ev_candidate = _detect_ev(arr, ep, jj, sn_min=1)  # no sn filter
                if ev_candidate is not None:
                    new_ev_i = jj; break
            block_reason = None
            if new_ev_i:
                # would sn=3 catch it?
                ev_sn3 = _detect_ev(arr, ep, new_ev_i, sn_min=3)
                if ev_sn3 is None and ev_candidate.get("trig") == "a":
                    block_reason = f"sn={ev_candidate.get('sn','?')}<3"
                elif ev_sn3 is None:
                    block_reason = "cd/px/pos fail"
            m3 = (block_reason is not None)
        else:
            m3 = False; block_reason = None
        # Classify (priority: m1 > m3 > m2)
        if hedged: cat = "m1"
        elif m3: cat = "m3"
        elif expired_then_pump: cat = "m2"
        else: cat = "m?"
        misses.append({"day":arr[j]["date"], "cat":cat, "vol_mult":cv/med14,
                       "block_reason":block_reason})
    return misses

all_miss = []
for r in main:
    for m in audit_miss_wave_v2(r):
        all_miss.append({"sym":r["sym"], "row_ev":r["date"], **m})

from collections import Counter
cat_ct = Counter(m["cat"] for m in all_miss)
print(f"  Total MISSED-WAVE audits: {len(all_miss)}")
for cat in ["m1", "m2", "m3", "m?"]:
    n = cat_ct.get(cat, 0)
    label = {"m1":"pump WHILE hedged (out-of-scope, GOM-D)",
             "m2":"EXPIRED then pump (calib 90d)",
             "m3":"RE-HEDGED, new event blocked (registry miss THẬT)",
             "m?":"KHÔNG xếp được"}[cat]
    print(f"    {cat}: {n}  — {label}")
    exs = [m for m in all_miss if m["cat"]==cat][:2]
    for ex in exs:
        extra = f" · blocked={ex['block_reason']}" if ex.get("block_reason") else ""
        print(f"       ex: {ex['sym']:<12} row_ev={ex['row_ev']} miss@{ex['day']} vol×{ex['vol_mult']:.1f}{extra}")

# ═══ [T3] productive-re-arm share ═══════════════════════════════════════
print(f"\n{DIV}\n[T3] productive-re-arm share (% re-arm → ignite ≤21d)\n{DIV}")
print(f"  {'sn':>3}  {'n_rearm':>7}  {'n_prod':>6}  {'%':>6}  {'days_min':>8}  {'med':>4}  {'max':>4}  "
      f"{'dead RE-HG':>10}  {'dead EXP':>8}  {'chưa đủ 21d':>12}")
print("  " + "─"*95)
for sn in [3,4,5]:
    rows = sweeps[sn]["rows"]
    total_rearms = []; productive = []; dead_reh = 0; dead_exp = 0; not_ripe = 0
    for r in rows:
        arr = td[r["sym"]]
        for idx_ra, ra in enumerate(r["outcome"]["rearms"]):
            # find next ignite AFTER this re-arm
            ra_i = ra["i"]
            # look for ignite from r's outcome that has i > ra_i (either wave-2+ or standalone)
            next_ig = [ig for ig in r["outcome"]["ignites"] if ig["i"] > ra_i]
            if next_ig:
                gap = next_ig[0]["i"] - ra_i
                if gap <= MISS_WAVE_DAYS:
                    productive.append(gap)
                    total_rearms.append(gap)
                    continue
            total_rearms.append(None)
            # classify dead
            if r["outcome"]["close_reason"] == "RE-HEDGED":
                # only count if close_day within 21d of ra
                close_i = next((k for k,x in enumerate(arr) if x["date"]==r["outcome"]["close_day"]), None)
                if close_i and (close_i - ra_i) <= MISS_WAVE_DAYS:
                    dead_reh += 1; continue
            if r["outcome"]["close_reason"] == "EXPIRED":
                dead_exp += 1; continue
            # STILL-OPEN and less than 21d after ra: not ripe
            last_i = len(arr) - 1
            if last_i - ra_i < MISS_WAVE_DAYS:
                not_ripe += 1
            else:
                # STILL-OPEN and >21d after ra but no ignite → dead
                dead_reh += 1
    n_ra = len(total_rearms)
    n_prod = len(productive)
    denom = n_ra - not_ripe
    pct = n_prod/denom*100 if denom>0 else 0
    if productive:
        d_min = min(productive); d_med = int(median(productive)); d_max = max(productive)
    else:
        d_min=d_med=d_max="-"
    print(f"  {sn:>3}  {n_ra:>7}  {n_prod:>6}  {pct:>5.1f}%  {d_min:>8}  {d_med:>4}  {d_max:>4}  "
          f"{dead_reh:>10}  {dead_exp:>8}  {not_ripe:>12}")

# ═══ [T4] local_low inclusive-D proposal text (KHÔNG merge) ══════════════
print(f"\n{DIV}\n[T4] local_low inclusive-D proposal (soạn text, KHÔNG merge)\n{DIV}")
print(f"  ANALYSIS đề xuất 1 dòng cho §E-R4b (chờ operator ký → E1 protocol lặp):")
print()
print(f"  ┌─────────────────────────────────────────────────────────────────────────────────┐")
print(f"  │ local_low_px = min(px_close[k]) k ∈ [ignite_idx, D] BAO GỒM D                    │")
print(f"  │ local_low_oi = min(oi_usd[k])   k ∈ [ignite_idx, D] BAO GỒM D                    │")
print(f"  │ điều kiện chấm re-arm trên close(D): px_close(D)/local_low_px ≥ r2 (thay D-1)   │")
print(f"  └─────────────────────────────────────────────────────────────────────────────────┘")
print()
print(f"  Diff dự kiến (code _try_rearm):")
print(f"    OLD (D-1):  for k in range(i_ig, j) if ...   # exclusive j")
print(f"    NEW (D0):   for k in range(i_ig, j+1) if ... # inclusive j")
print(f"  E2b probe (turn earlier): D0 vs D-1 = 0 rows diff trên data hiện tại (86 events)")
print(f"  → phân xử ANALYSIS: nếu data khác có case r2/r3 marginal-day-of-check → khác kết quả.")
print(f"  Chờ operator ký → E1-protocol merge spec + code + verify HEMI + rerun sn sweep.")

print(f"\n{DIV}\nFLAG biên (cho ANALYSIS):\n{DIV}")
flags = []
# reg%_weekpeak vs 25% for each sn
for sn in [3,4,5]:
    s = sweeps[sn]
    if 25 - s["peak_pct"] < 1 and s["peak_pct"] <= 25:
        flags.append(f"[NGHI] sn={sn} reg%_weekpeak {s['peak_pct']:.1f}% (biên mỏng vs 25% <1pp)")
    if s["peak_pct"] > 25:
        flags.append(f"[NGHI] sn={sn} reg%_weekpeak {s['peak_pct']:.1f}% > 25% (vượt §E-R8②)")
# MFE >=10% wave-1 vs 40%
w1_mfe = [x for x in mfe_data if x["wave_n"]==1 and x["mfe"]>=0.10]
w1_all = [x for x in mfe_data if x["wave_n"]==1]
if w1_all and len(w1_mfe)/len(w1_all)*100 < 40:
    flags.append(f"[NGHI] wave-1 MFE≥10% pct = {len(w1_mfe)}/{len(w1_all)} = {len(w1_mfe)/len(w1_all)*100:.1f}% < 40% ngưỡng chưa-ký")
# MISSED unclassified count
if cat_ct.get("m?", 0) > 0:
    flags.append(f"[NGHI] {cat_ct.get('m?',0)} MISSED-WAVE KHÔNG xếp được m1/m2/m3 (cần classify rule bổ sung)")
if flags:
    for f in flags: print(f"  {f}")
else:
    print(f"  (không flag biên)")

print(f"\n{DIV}\nDONE T0-T4. DỪNG. Chờ operator/ANALYSIS.\n{DIV}")
