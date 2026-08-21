#!/usr/bin/env python3
"""[doctrine-pack HEMI verify] Re-verify HEMI re-arm 08-06 + ⚡ 15/08 giữ nguyên
với inclusive-D (range j+1) v1.2-FINAL+doctrine-pack.
"""
from __future__ import annotations
import sys, io, csv
from pathlib import Path
from statistics import mean, median

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = Path(r"D:\Data back test\whale_data")
sys.path.insert(0, str(REPO))
from lib.hedge_episode import detect_episodes, calc_div, NaN, ok

TMP = Path(r"C:\Users\Hello\AppData\Local\Temp\e_r7_20260819")

# Load HEMI
hemi = []
for m in ["06","07","08"]:
    p = TMP / f"freshwatch_daily_2026-{m}.csv"
    with open(p, encoding="utf-8", errors="replace") as f:
        for r in csv.DictReader(f):
            if r["symbol"] != "HEMIUSDT": continue
            def _f(k, r=r):
                try: return float(r[k])
                except: return NaN
            hemi.append({
                "date": r.get("date",""), "px": _f("px_avg"),
                "pos": _f("lsr_pos_r"), "acc": _f("lsr_acc_r"),
                "oi": _f("oi_usd"), "vol": _f("vol_quote"),
            })
hemi.sort(key=lambda r: r["date"])

CFG = {"hedge": {"div_ratio_max": 0.5, "episode_break_days": 3}}
ep = detect_episodes(hemi, CFG)

# Constants (per v1.2-FINAL+doctrine-pack)
R2 = 1.15; R3 = 1.30; COOLDOWN = 3

def try_ignite(arr, j):
    vw = [arr[k]["vol"] for k in range(max(0,j-14),j) if ok(arr[k]["vol"]) and arr[k]["vol"]>0]
    med14 = median(vw) if len(vw)>=7 else None
    cv = arr[j].get("vol", NaN)
    vol_h = ok(cv) and med14 and cv >= 5.0 * med14
    on = arr[j].get("oi", NaN); o2 = arr[j-2].get("oi", NaN) if j>=2 else NaN
    oi_h = (ok(on) and ok(o2) and o2>0 and (on-o2)/o2 >= 0.30)
    pn = arr[j].get("px", NaN)
    pw = [arr[k]["px"] for k in range(max(0,j-14),j) if ok(arr[k]["px"]) and arr[k]["px"]>0]
    r14 = max(pw) if pw else None
    brk_h = (ok(pn) and r14 and (pn-r14)/r14 >= 0.15)
    if not (vol_h or oi_h or brk_h): return None
    r = []
    if vol_h: r.append(f"vol {cv/med14:.1f}×")
    if oi_h:  r.append(f"OI+{(on-o2)/o2*100:.0f}%/2d")
    if brk_h: r.append(f"brk+{(pn-r14)/r14*100:.0f}%/rg14")
    return " · ".join(r)

def idx_for(d):
    for i, r in enumerate(hemi):
        if r["date"] == d: return i
    return None

i_event = idx_for("2026-07-12")

# Wave-1 ignite
wave1_i = None
for j in range(i_event+1, len(hemi)):
    r = try_ignite(hemi, j)
    if r:
        wave1_i = j
        print(f"[wave-1 IGNITE] {hemi[j]['date']} idx={j}: {r}")
        break

# RE-ARM trace with inclusive-D (range i_ig, j+1)
DIV = "═"*90
print(f"\n{DIV}\n[v1.2-FINAL+doctrine-pack RE-ARM trace] inclusive-D (range j+1) · r2≥{R2} r3≥{R3} cd={COOLDOWN}d\n{DIV}")
print(f"  {'date':>12}  {'d_since':>7}  {'px':>10}  {'px_low':>10}  {'r2':>6}  "
      f"{'oi':>12}  {'oi_low':>12}  {'r3':>5}  {'PASS?':>8}")
print("  " + "─"*90)

first_rearm = None
for j in range(wave1_i+1, len(hemi)):
    d = hemi[j]["date"]
    if d > "2026-08-19": break
    ds = j - wave1_i
    # inclusive-D per doctrine-pack: range(wave1_i, j+1)
    pw = [hemi[k]["px"] for k in range(wave1_i, j+1) if ok(hemi[k]["px"]) and hemi[k]["px"]>0]
    ow = [hemi[k]["oi"] for k in range(wave1_i, j+1) if ok(hemi[k]["oi"]) and hemi[k]["oi"]>0]
    if not pw or not ow: continue
    px_low = min(pw); oi_low = min(ow)
    px_now = hemi[j]["px"]; oi_now = hemi[j]["oi"]
    r2 = px_now/px_low; r3 = oi_now/oi_low
    r1_ok = ds >= COOLDOWN
    r2_ok = r2 >= R2
    r3_ok = r3 >= R3
    passed = r1_ok and r2_ok and r3_ok
    if passed and first_rearm is None:
        first_rearm = d
        flag = "RE-ARM ✓"
    elif passed:
        flag = "(rearm-ok)"
    else:
        fails = []
        if not r1_ok: fails.append(f"cd<{COOLDOWN}")
        if not r2_ok: fails.append(f"r2={r2:.2f}")
        if not r3_ok: fails.append(f"r3={r3:.2f}")
        flag = "·".join(fails)[:15]
    if d in ("2026-07-25","2026-07-31","2026-08-05","2026-08-06","2026-08-15","2026-08-19") or passed:
        print(f"  {d:>12}  {ds:>7}  {px_now:>10.5f}  {px_low:>10.5f}  {r2:>6.3f}  "
              f"{oi_now:>12.0f}  {oi_low:>12.0f}  {r3:>5.2f}  {flag:>8}")

# Wave-2 ignite
wave2_hit = None
if first_rearm:
    i_ra = idx_for(first_rearm)
    for j in range(i_ra, len(hemi)):
        if hemi[j]["date"] > "2026-08-19": break
        r = try_ignite(hemi, j)
        if r:
            wave2_hit = {"day": hemi[j]["date"], "reasons": r}
            break

print(f"\n[GATE(i) 3-vế v1.2-FINAL+doctrine-pack verify]:")
v1 = (hemi[wave1_i]['date'] == "2026-07-20")
v2 = (first_rearm is not None and first_rearm <= "2026-08-15")
v3 = (wave2_hit and wave2_hit["day"] == "2026-08-15")
print(f"  wave-1 07-20                     : {'✓' if v1 else '✗'} (got {hemi[wave1_i]['date']})")
print(f"  re-arm ≤ 08-15                   : {'✓' if v2 else '✗'} (first_rearm = {first_rearm})")
print(f"  wave-2 15/08                     : {'✓' if v3 else '✗'} (got {wave2_hit['day'] if wave2_hit else 'none'})")
print(f"  → GATE(i) {'PASS ✓✓✓' if (v1 and v2 and v3) else 'FAIL'}")
print(f"\n  Expected per operator: re-arm 08-06 · ⚡ 15/08 GIỮ NGUYÊN so trước inclusive-D fix")
