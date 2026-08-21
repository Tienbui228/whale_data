#!/usr/bin/env python3
"""[E-R7e] GATE trên spec v1.2-FINAL (46db911). Probe → paste raw. KHÔNG chốt.

Spec canonical: proposals/unhedge_registry_spec_v1.0.md §E-R4b v1.2-FINAL
  · r2=1.15 · r3=1.30 · cooldown 3d
  · close: RE-HEDGED / EXPIRED 90d / KHO-RÚT (no MARKUP-GIỮ)
  · RE-ARM-MISS log (auto-tích lũy)
§E-R8 falsifier forward: ① hit<40% · ② noise 25% univ or 40% E-R3 · ③ miss-audit
"""
from __future__ import annotations
import sys, io, csv, math, re, subprocess
from pathlib import Path
from statistics import mean, median
from datetime import date, datetime, timedelta

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = Path(r"D:\Data back test\whale_data")
sys.path.insert(0, str(REPO))
from lib.hedge_episode import detect_episodes, calc_div, NaN, ok

TMP = Path(r"C:\Users\Hello\AppData\Local\Temp\e_r7_20260819")
SPEC_FILE = REPO / "proposals" / "unhedge_registry_spec_v1.0.md"

WINDOW_START = "2026-06-21"
WINDOW_END   = "2026-08-19"

# ─── [E2] HEADER — parse spec + provenance ─────────────────────────────────
spec = SPEC_FILE.read_text(encoding="utf-8")
_m_ver = re.search(r"v1\.2-FINAL", spec)
_m_r2 = re.search(r"\(r2\) px_close / local_low_px ≥ ([\d.]+)", spec)
_m_r3 = re.search(r"\(r3\) oi_usd  / local_low_oi  ≥ ([\d.]+)", spec)
_m_cd = re.search(r"cooldown tối thiểu (\d+)d", spec)
_m_markup_bo = re.search(r"KHÔNG có điều kiện đóng MARKUP-GIỮ — đã BỎ", spec)
_m_er8 = re.search(r"E-R8 — FALSIFIER FORWARD", spec)

try:
    git_commit = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"],
                                          cwd=REPO, text=True).strip()
except Exception:
    git_commit = "?"

R2 = float(_m_r2.group(1)); R3 = float(_m_r3.group(1)); COOLDOWN = int(_m_cd.group(1))

DIV = "═" * 96
print(f"{DIV}\n[E2 HEADER — self-declare per spec v1.2-FINAL]\n{DIV}")
print(f"  spec_version         : v1.2-FINAL {'✓' if _m_ver else '✗ MISSING'}")
print(f"  amendments_applied   : [E-R4b-vA-1.15/1.30, MARKUP-GIỮ-removed, E-R8]")
print(f"  git_commit           : {git_commit}")
print(f"  data-source          : freshwatch_daily_2026-{{06,07,08}}.csv (VPS canonical, /tmp backup)")
print(f"  machine              : local Windows probe (READ-ONLY)")
print(f"  date-range           : {WINDOW_START} → {WINDOW_END}")
print(f"  spec_source          : {SPEC_FILE.name}")
print(f"  parsed r2/r3/cd      : {R2} / {R3} / {COOLDOWN}d")
print(f"  MARKUP-GIỮ removed   : {'✓' if _m_markup_bo else '✗'}")
print(f"  §E-R8 present        : {'✓' if _m_er8 else '✗'}")
if not (_m_ver and _m_r2 and _m_r3 and _m_cd and _m_markup_bo and _m_er8):
    print("\n  ERROR: spec parse fail → BLOCK RUN"); sys.exit(1)

# ─── Load data ─────────────────────────────────────────────────────────────
td: dict[str, list[dict]] = {}
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
                "glsr": _f("lsr_global_r"),
            })
for sym in td:
    td[sym].sort(key=lambda r: r["date"])

sympath = TMP / "freshwatch_symbols_vps.txt"
with open(sympath, encoding="utf-8", errors="replace") as f:
    universe = sorted({l.strip() for l in f if l.strip() and not l.startswith("#")})
td = {s: v for s, v in td.items() if len(v) >= 14 and s in universe}
print(f"\n[fw] universe ≥14d: {len(td)} / {len(universe)}")

CFG = {"hedge": {"div_ratio_max": 0.5, "episode_break_days": 3}}
ep_cache = {sym: detect_episodes(arr, CFG) for sym, arr in td.items()}

# Constants
DRIFT_THR = 0.15; DRIFT_WIN = 7
POS_HOLD = 0.90; PX_HOLD = 0.85
IGNITE_VOL = 5.0; IGNITE_OI = 0.30; IGNITE_BRK = 0.15
REHEDGE_MIN = 5; EXPIRE_DAYS = 90
MISS_WAVE_DAYS = 21

# ─── Helpers ───────────────────────────────────────────────────────────────
def _cur_ep_min(arr, ep, i, lb=30):
    if not ep[i]["in_hedge"]: return None
    eid = ep[i]["episode_id"]; sj = i
    for j in range(i, max(-1, i-lb)-1, -1):
        if ep[j].get("episode_id")==eid and ep[j]["in_hedge"]: sj = j
        else: break
    mn = None; mi = None
    for j in range(sj, i+1):
        d = calc_div(arr, j)
        if ok(d) and (mn is None or d < mn): mn = d; mi = j
    return {"start_i": sj, "min_i": mi, "min_div": mn}

def _pos_ok(arr, i):
    cur = arr[i].get("pos", NaN)
    if not ok(cur): return False
    vs = [arr[j]["pos"] for j in range(max(0,i-5), i) if ok(arr[j]["pos"])]
    if len(vs) < 3: return False
    return cur >= POS_HOLD * mean(vs)

def _px_ok(arr, i, hspx):
    cur = arr[i].get("px", NaN)
    return ok(cur) and hspx and ok(hspx) and cur >= PX_HOLD * hspx

def _detect_ev(arr, ep, i, sn_min):
    d = arr[i]["date"]
    if not (WINDOW_START <= d <= WINDOW_END): return None
    if i < 5: return None
    trig = None; sn = None; hspx = None; ep_min = None
    if i >= 1 and ep[i-1]["in_hedge"] and not ep[i]["in_hedge"]:
        trig = "a"; sn = ep[i-1]["struct_n"]; hspx = ep[i-1]["hedge_start_px"]
        # ep div min
        eid = ep[i-1]["episode_id"]; ds = []
        for j in range(i-1, -1, -1):
            if ep[j].get("episode_id")==eid and ep[j]["in_hedge"]:
                dv = calc_div(arr, j)
                if ok(dv): ds.append(dv)
            else: break
        ep_min = min(ds) if ds else NaN
    if trig is None and ep[i]["in_hedge"]:
        info = _cur_ep_min(arr, ep, i)
        if info and info["min_i"] is not None and info["min_div"] is not None:
            cur = calc_div(arr, i)
            if ok(cur):
                dr = cur - info["min_div"]; ds = i - info["min_i"]
                if dr >= DRIFT_THR and 0 < ds <= DRIFT_WIN:
                    trig = "b"; sn = ep[i]["struct_n"]; hspx = ep[i]["hedge_start_px"]
                    ep_min = info["min_div"]
    if trig is None: return None
    # struct_n filter — only (a) per operator instr
    if trig == "a" and sn is not None and sn < sn_min: return None
    if not (_pos_ok(arr, i) and _px_ok(arr, i, hspx)): return None
    return {"i": i, "date": d, "trig": trig, "sn": sn, "hspx": hspx, "ep_min": ep_min}

def _try_ignite(arr, j):
    vw = [arr[k]["vol"] for k in range(max(0,j-14), j) if ok(arr[k]["vol"])]
    vw = [v for v in vw if v > 0]
    med14 = median(vw) if len(vw) >= 7 else None
    cv = arr[j].get("vol", NaN)
    vol_h = ok(cv) and med14 and cv >= IGNITE_VOL * med14
    on = arr[j].get("oi", NaN); o2 = arr[j-2].get("oi", NaN) if j >= 2 else NaN
    oi_h = (ok(on) and ok(o2) and o2 > 0 and (on-o2)/o2 >= IGNITE_OI)
    pn = arr[j].get("px", NaN)
    pw = [arr[k]["px"] for k in range(max(0,j-14), j) if ok(arr[k]["px"])]
    pw = [p for p in pw if p > 0]
    r14 = max(pw) if pw else None
    brk_h = (ok(pn) and r14 and (pn-r14)/r14 >= IGNITE_BRK)
    if not (vol_h or oi_h or brk_h): return None
    reasons = []
    if vol_h: reasons.append(f"vol {cv/med14:.1f}×")
    if oi_h:  reasons.append(f"OI+{(on-o2)/o2*100:.0f}%/2d")
    if brk_h: reasons.append(f"brk+{(pn-r14)/r14*100:.0f}%/rg14")
    return " · ".join(reasons)

# ─── RE-ARM check — variant D0 (inclusive) vs D-1 (exclusive) ────────────
def _try_rearm(arr, i_ig, j, variant="D-1"):
    ds = j - i_ig
    if ds < COOLDOWN: return False, f"cd<{COOLDOWN}"
    # local_low window
    if variant == "D0":  # inclusive today
        end = j + 1
    else:                # D-1 exclusive (code before spec text)
        end = j
    pw = [arr[k]["px"] for k in range(i_ig, end) if ok(arr[k]["px"])]
    ow = [arr[k]["oi"] for k in range(i_ig, end) if ok(arr[k]["oi"])]
    pw = [p for p in pw if p > 0]; ow = [o for o in ow if o > 0]
    if not pw or not ow: return False, "no-data"
    pl = min(pw); ol = min(ow)
    pn = arr[j].get("px", NaN); on = arr[j].get("oi", NaN)
    if not (ok(pn) and ok(on)): return False, "nan"
    r2 = pn/pl; r3 = on/ol
    if r2 < R2: return False, f"r2={r2:.2f}"
    if r3 < R3: return False, f"r3={r3:.2f}"
    return True, {"r1_d": ds, "r2": r2, "r3": r3, "px_low": pl, "oi_low": ol}

# ─── Outcome scan (with re-arm + variant) ─────────────────────────────────
def _outcome(arr, ep, ev, variant, rearm_on):
    """Return dict: ignites list, rearm_days list, close_reason, close_day."""
    i0 = ev["i"]
    max_scan = min(len(arr)-1, i0 + EXPIRE_DAYS)
    ignites = []           # list of dicts {day, i, reasons, wave_n}
    rearms = []            # list of {day, i, r2, r3, r1_d}
    close_reason = None; close_day = None
    scan_start = i0 + 1
    current_wave = 1
    wave_ig_i = None       # last wave ignite idx (for r1 cooldown reference)

    for j in range(scan_start, max_scan+1):
        # 1) RE-HEDGED close (new episode struct_n ≥ 5, different from event's episode)
        if ep[j]["in_hedge"]:
            eid_j = ep[j].get("episode_id")
            eid_ev = ep[i0].get("episode_id") if i0 < len(ep) else 0
            if eid_j != eid_ev and ep[j]["struct_n"] >= REHEDGE_MIN:
                close_reason = "RE-HEDGED"; close_day = arr[j]["date"]
                break
        # 2) IGNITE
        ig = _try_ignite(arr, j)
        if ig:
            if not ignites:
                ignites.append({"day": arr[j]["date"], "i": j, "reasons": ig, "wave_n": 1})
                wave_ig_i = j
                continue
            if rearm_on and wave_ig_i is not None:
                # Require NEW re-arm AFTER last wave ignite for new wave (spec §E-R4b)
                new_rearm = [ra for ra in rearms if ra["i"] > wave_ig_i]
                if new_rearm and j > new_rearm[0]["i"]:
                    current_wave += 1
                    ignites.append({"day": arr[j]["date"], "i": j, "reasons": ig, "wave_n": current_wave})
                    wave_ig_i = j
                    continue
        # 3) RE-ARM (if enabled + wave-1 already fired + not yet re-armed for THIS wave)
        if rearm_on and ignites and wave_ig_i is not None:
            # check re-arm gate from LAST wave ignite
            already_rearmed_this_wave = any(ra["i"] > wave_ig_i for ra in rearms)
            if not already_rearmed_this_wave:
                ok_ra, info = _try_rearm(arr, wave_ig_i, j, variant=variant)
                if ok_ra:
                    rearms.append({"day": arr[j]["date"], "i": j, **info, "for_wave_n": current_wave})

    if close_reason is None:
        if (max_scan - i0) >= EXPIRE_DAYS:
            close_reason = "EXPIRED"; close_day = arr[max_scan]["date"]
        else:
            close_reason = "STILL-OPEN"

    return {
        "ignites": ignites, "rearms": rearms,
        "close_reason": close_reason, "close_day": close_day,
        "n_waves": len(ignites), "n_rearms": len(rearms),
    }

# ─── MISS-WAVE audit (spec §E-R4b): row IGNITED closed, ≤21d after vol≥5×med14 → miss ──
def _miss_wave_audit(arr, ev, outcome):
    """Only for rows CLOSED (RE-HEDGED/EXPIRED). Scan ≤21d after close for vol spike."""
    if outcome["close_reason"] not in ("RE-HEDGED", "EXPIRED"): return []
    if not outcome["close_day"]: return []
    # find close index
    c_i = next((k for k, r in enumerate(arr) if r["date"] == outcome["close_day"]), None)
    if c_i is None: return []
    end = min(len(arr)-1, c_i + MISS_WAVE_DAYS)
    misses = []
    for j in range(c_i+1, end+1):
        ig = _try_ignite(arr, j)
        if ig and "vol" in ig:
            # get ratio
            vw = [arr[k]["vol"] for k in range(max(0,j-14), j) if ok(arr[k]["vol"]) and arr[k]["vol"] > 0]
            med = median(vw) if vw else 0
            ratio = arr[j]["vol"] / med if med > 0 else 0
            # min px_ratio since ignite (edge of miss)
            pw = [arr[k]["px"] for k in range(c_i, j+1) if ok(arr[k]["px"]) and arr[k]["px"] > 0]
            base_p = arr[c_i].get("px", NaN)
            px_ratio_min = min(pw)/base_p if pw and ok(base_p) and base_p > 0 else NaN
            misses.append({"day": arr[j]["date"], "vol_mult": ratio, "px_ratio_min": px_ratio_min})
    return misses

# ─── hit_k7 metric (§E-R8① — per-wave ret_k7 > 0) ────────────────────────
def _hit_k7(arr, ig_day_idx):
    end = min(len(arr)-1, ig_day_idx + 7)
    p0 = arr[ig_day_idx].get("px", NaN)
    p7 = arr[end].get("px", NaN)
    if not (ok(p0) and ok(p7) and p0 > 0): return None
    return (p7 - p0) / p0

# ─── Run backfill parametrized ─────────────────────────────────────────────
def run_bf(sn_min, variant="D-1", rearm_on=True):
    rows = []
    for sym, arr in td.items():
        ep = ep_cache[sym]
        for i, r in enumerate(arr):
            d = r["date"]
            if not (WINDOW_START <= d <= WINDOW_END): continue
            if not ok(r.get("pos", NaN)) or not ok(r.get("acc", NaN)): continue
            ev = _detect_ev(arr, ep, i, sn_min)
            if ev is None: continue
            ev["sym"] = sym
            oc = _outcome(arr, ep, ev, variant, rearm_on)
            ev["outcome"] = oc
            ev["miss_wave"] = _miss_wave_audit(arr, ev, oc)
            rows.append(ev)
    return rows

# ═══ [E2b] DUAL VARIANT probe D0 vs D-1 ══════════════════════════════════
print(f"\n{DIV}\n[E2b] DUAL local_low VARIANT probe (D0 inclusive vs D-1 exclusive)\n{DIV}")
rows_d0  = run_bf(sn_min=3, variant="D0",  rearm_on=True)
rows_dm1 = run_bf(sn_min=3, variant="D-1", rearm_on=True)

print(f"\n  variant D0 (inclusive)   : {len(rows_d0)} events")
print(f"  variant D-1 (exclusive)  : {len(rows_dm1)} events (code hiện tại)")

# Compare re-arm dates
lookup_d0 = {(r["sym"], r["date"]): r for r in rows_d0}
lookup_dm1 = {(r["sym"], r["date"]): r for r in rows_dm1}
diff_rows = []
for k in sorted(set(lookup_d0.keys()) | set(lookup_dm1.keys())):
    a = lookup_d0.get(k); b = lookup_dm1.get(k)
    if not a or not b:
        diff_rows.append({"key": k, "reason": "only in one variant"})
        continue
    a_ra = [x["day"] for x in a["outcome"]["rearms"]]
    b_ra = [x["day"] for x in b["outcome"]["rearms"]]
    if a_ra != b_ra:
        diff_rows.append({"key": k, "D0_rearm": a_ra, "D-1_rearm": b_ra})

print(f"  rows re-arm LỆCH between D0/D-1: {len(diff_rows)}")
if diff_rows:
    print(f"  detail (first 15):")
    for x in diff_rows[:15]:
        if "reason" in x:
            print(f"    {x['key']}: {x['reason']}")
        else:
            print(f"    {x['key']}: D0={x['D0_rearm']}  D-1={x['D-1_rearm']}")

print(f"\n  → Không tự chọn variant. ANALYSIS phân xử.")
print(f"  → E3/E4/E5 chạy trên D-1 (code hiện tại). Label [local_low=D-1] mọi bảng.")

# ═══ [E3] HEMI RE-ARM-MISS log ══════════════════════════════════════════
print(f"\n{DIV}\n[E3] HEMI RE-ARM-MISS log (kỳ vọng RỖNG vì row không đóng)\n{DIV}")
hemi_rows = [r for r in rows_dm1 if r["sym"] == "HEMIUSDT"]
for r in hemi_rows:
    print(f"  HEMI event {r['date']} trig={r['trig']} sn={r['sn']} → outcome={r['outcome']['close_reason']}"
          f" wave_n={r['outcome']['n_waves']} rearm_n={r['outcome']['n_rearms']}")
    print(f"    ignites: {[i['day'] for i in r['outcome']['ignites']]}")
    print(f"    rearms:  {[i['day'] for i in r['outcome']['rearms']]}")
    print(f"    miss_wave: {r['miss_wave']} (rỗng = expected)")

# ═══ [E4] GATE ON fw-139 (window E-R7, re-arm ON, sn=3, D-1) ══════════════
print(f"\n{DIV}\n[E4] GATE fw-139 · window {WINDOW_START}→{WINDOW_END} · sn=3 · re-arm ON · [local_low=D-1]\n{DIV}")
main = rows_dm1  # sn=3, D-1, rearm ON

# (a) per-row table
print(f"\n[E4a] Registry rows ({len(main)}), no MARKUP-GIỮ close (must=0 rows with markup-close):")
markup_close = sum(1 for r in main if r["outcome"]["close_reason"] == "MARKUP-GIỮ")
print(f"  rows với close=MARKUP-GIỮ: {markup_close} (kỳ vọng 0 per v1.2)")

print(f"\n  {'sym':>12}  {'event':>10}  {'w_n':>3}  {'ignites':>25}  {'rearms':>15}  {'close':>10}  {'close_day':>10}")
print("  " + "─" * 100)
for r in sorted(main, key=lambda x: (x["date"], x["sym"])):
    igs = "|".join([f"{ig['day']}(w{ig['wave_n']})" for ig in r["outcome"]["ignites"]])[:25]
    ras = "|".join([ra["day"] for ra in r["outcome"]["rearms"]])[:15]
    print(f"  {r['sym'][:12]:>12}  {r['date']:>10}  {r['outcome']['n_waves']:>3}  "
          f"{igs:>25}  {ras:>15}  {r['outcome']['close_reason']:>10}  "
          f"{str(r['outcome']['close_day'] or '-'):>10}")

# (b) Compare no-re-arm (v1.0 semantics)
print(f"\n[E4b] Compare re-arm ON vs OFF (sn=3, D-1):")
rows_norearm = run_bf(sn_min=3, variant="D-1", rearm_on=False)
n_alert_on  = sum(r["outcome"]["n_waves"] for r in main)     # each wave = alert
n_alert_off = sum(r["outcome"]["n_waves"] for r in rows_norearm)
print(f"  rows              : ON={len(main)}  OFF={len(rows_norearm)}  Δ={len(main)-len(rows_norearm)}")
print(f"  total alerts      : ON={n_alert_on}  OFF={n_alert_off}  Δ={n_alert_on-n_alert_off}")

# hit_k7 comparison
def hit_stats(rows):
    hits = []
    for r in rows:
        for ig in r["outcome"]["ignites"]:
            h = _hit_k7(td[r["sym"]], ig["i"])
            if h is not None: hits.append(h > 0)
    if not hits: return (0, 0, 0.0)
    n_pos = sum(hits); n = len(hits)
    return (n_pos, n, n_pos/n*100)

h_on = hit_stats(main); h_off = hit_stats(rows_norearm)
print(f"  hit_k7 (>0 pct)   : ON={h_on[0]}/{h_on[1]}={h_on[2]:.1f}%  OFF={h_off[0]}/{h_off[1]}={h_off[2]:.1f}%")

# (c) Noise §E-R8②
print(f"\n[E4c] NOISE §E-R8② + re-arm rate:")
# registry_share weekly
open_by_week = {}
for r in main:
    d0 = date.fromisoformat(r["date"])
    close_d = date.fromisoformat(r["outcome"]["close_day"]) if r["outcome"]["close_day"] else date.fromisoformat(WINDOW_END)
    cur = d0
    while cur <= close_d and cur <= date.fromisoformat(WINDOW_END):
        wk = cur.strftime("%Y-W%V")
        open_by_week.setdefault(wk, set()).add(r["sym"])
        cur += timedelta(days=1)
print(f"  registry_share weekly (rows sống unique / {len(td)}):")
for wk in sorted(open_by_week):
    n = len(open_by_week[wk]); pct = n/len(td)*100
    flag = "FAIL >25%" if pct > 25 else "PASS"
    print(f"    {wk}: {n}/{len(td)} = {pct:>5.1f}%  {flag}")

# E-R3 share: alerts REGISTRY-IGNITE / total Telegram alerts (unknown baseline — skip absolute)
alerts_er3 = n_alert_on
print(f"  E-R3 alerts total : {alerts_er3} (ngưỡng 40% cần baseline total Telegram alert cho cùng window — unknown, skip absolute PASS/FAIL)")

# Re-arm rate
n_ignited = sum(1 for r in main if r["outcome"]["n_waves"] >= 1)
n_rearmed = sum(1 for r in main if r["outcome"]["n_rearms"] >= 1)
ra_rate = n_rearmed / n_ignited * 100 if n_ignited > 0 else 0
flag = "FAIL >50% quá lỏng" if ra_rate > 50 else "PASS"
print(f"  re-arm rate       : {n_rearmed}/{n_ignited} = {ra_rate:.1f}%  {flag}")

# MISS-WAVE count
miss_ct = sum(len(r["miss_wave"]) for r in main)
print(f"  MISSED-WAVE total : {miss_ct} (§E-R4b RE-ARM-MISS log)")

# (d) hit_k7 §E-R8① per-wave
print(f"\n[E4d] §E-R8① hit_k7 per-wave (ngưỡng 40%):")
w1_hits = []; w2_hits = []
for r in main:
    for ig in r["outcome"]["ignites"]:
        h = _hit_k7(td[r["sym"]], ig["i"])
        if h is None: continue
        if ig["wave_n"] == 1: w1_hits.append(h > 0)
        else: w2_hits.append(h > 0)
def pct(v): return sum(v)/len(v)*100 if v else 0
print(f"  wave-1: {sum(w1_hits)}/{len(w1_hits)} = {pct(w1_hits):.1f}%  {'PASS ≥40%' if pct(w1_hits) >= 40 else 'FAIL <40%'}")
print(f"  wave-2: {sum(w2_hits)}/{len(w2_hits)} = {pct(w2_hits):.1f}%  {'PASS ≥40%' if pct(w2_hits) >= 40 else 'FAIL <40%'}")

# ═══ [E5] BẢNG struct_n sweep sn=3/4/5 ═══════════════════════════════════
print(f"\n{DIV}\n[E5] SWEEP struct_n sn={{3,4,5}} · re-arm ON · [local_low=D-1] · driver (a), (b)-drift giữ 0.15\n{DIV}")
print(f"  {'sn':>3}  {'n_rows':>7}  {'reg%':>10}  {'HEMI?':>6}  {'ON?':>4}  "
      f"{'hit_k7':>10}  {'alerts':>7}  {'MISSED':>7}")
print("  " + "─" * 78)
sweep = {}
for sn in [3, 4, 5]:
    rows_sn = run_bf(sn_min=sn, variant="D-1", rearm_on=True)
    n_r = len(rows_sn)
    # unique tokens sống toàn window (approx = rows count with unique sym)
    uniq = len({r["sym"] for r in rows_sn})
    reg_pct = uniq / len(td) * 100
    hemi_in = any(r["sym"] == "HEMIUSDT" for r in rows_sn)
    on_in = any(r["sym"] == "ONUSDT" for r in rows_sn)
    alerts = sum(r["outcome"]["n_waves"] for r in rows_sn)
    miss = sum(len(r["miss_wave"]) for r in rows_sn)
    # hit_k7
    hits = []
    for r in rows_sn:
        for ig in r["outcome"]["ignites"]:
            h = _hit_k7(td[r["sym"]], ig["i"])
            if h is not None: hits.append(h > 0)
    hk7 = sum(hits)/len(hits)*100 if hits else 0
    sweep[sn] = {"rows": n_r, "reg_pct": reg_pct, "hemi": hemi_in, "on": on_in,
                 "alerts": alerts, "miss": miss, "hk7": hk7, "hit_n": f"{sum(hits)}/{len(hits)}"}
    print(f"  {sn:>3}  {n_r:>7}  {uniq}/{len(td)}={reg_pct:>5.1f}%  "
          f"{'YES' if hemi_in else 'NO':>6}  {'YES' if on_in else 'NO':>4}  "
          f"{sum(hits)}/{len(hits)}={hk7:>5.1f}%  {alerts:>7}  {miss:>7}")

print(f"\n  Tiêu chí operator (KHÔNG tự chấm): reg% ≤25% ∧ HEMI+ON sống ∧ hit_k7 ≥72%")
qualifiers = [sn for sn, v in sweep.items()
              if v["reg_pct"] <= 25 and v["hemi"] and v["on"] and v["hk7"] >= 72]
if qualifiers:
    print(f"  sn thỏa 3 tiêu chí: {qualifiers}")
else:
    print(f"  no sn thỏa 3 tiêu chí (bảng in y nguyên trên, DỪNG).")

# ═══ FLAG BIÊN ═══════════════════════════════════════════════════════════
print(f"\n{DIV}\nFLAG biên (số lạ/mỏng — không giải thích, cho ANALYSIS):\n{DIV}")
flags = []
# 1. Diff D0/D-1 nếu >5 rows lệch
if len(diff_rows) > 5:
    flags.append(f"[NGHI] {len(diff_rows)} rows re-arm LỆCH D0 vs D-1 (>5 threshold)")
# 2. Re-arm rate > 50%
if ra_rate > 50:
    flags.append(f"[NGHI] re-arm rate {ra_rate:.1f}% > 50% (§E-R4b siết ngưỡng)")
# 3. hit_k7 <40%
if pct(w1_hits) < 40 or pct(w2_hits) < 40:
    flags.append(f"[NGHI] hit_k7 <40% (§E-R8①: registry xuống ANALYSIS-ONLY nếu vượt ngưỡng)")
# 4. Registry_share >25% any week
peak_wk = max(open_by_week.items(), key=lambda x: len(x[1])) if open_by_week else None
if peak_wk and len(peak_wk[1])/len(td)*100 > 25:
    flags.append(f"[NGHI] registry_share peak {len(peak_wk[1])/len(td)*100:.1f}% >25% tại {peak_wk[0]} (§E-R8②)")
# 5. sn=3/4/5 all fail tiêu chí
if not qualifiers:
    flags.append(f"[NGHI] không sn nào thỏa 3 tiêu chí operator — biến đo có thể sai OR calib chưa đúng anchor")

if flags:
    for f in flags: print(f"  {f}")
else:
    print(f"  (không flag biên)")

print(f"\n{DIV}\nDONE E2-E5. DỪNG. Chờ ANALYSIS/operator ký chấm chỉ.\n{DIV}")
