#!/usr/bin/env python3
"""Probe: AKE (AKEUSDT) data from freshwatch for MM-ECON."""
import csv, io, sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

EXP_DIR = Path(r"D:\Check onchain fresh wallets\data\export")

def gv(r, k):
    v = r.get(k, "")
    if v in ("", None): return None
    try: return float(v)
    except: return None

ake_rows = {}
for f in sorted(EXP_DIR.glob("freshwatch_daily_2026-*.csv")):
    for r in csv.DictReader(open(f, encoding="utf-8-sig")):
        if r.get("symbol", "") == "AKEUSDT":
            ake_rows[r["date"]] = r

print(f"AKEUSDT rows: {len(ake_rows)}")
if not ake_rows:
    # Try other names
    all_syms = set()
    for f in sorted(EXP_DIR.glob("freshwatch_daily_2026-*.csv"))[:2]:
        for r in csv.DictReader(open(f, encoding="utf-8-sig")):
            s = r.get("symbol","")
            if "AK" in s.upper():
                all_syms.add(s)
    print(f"Symbols with AK: {sorted(all_syms)}")
else:
    dates = sorted(ake_rows.keys())
    print(f"Date range: {dates[0]} → {dates[-1]}")

    series = []
    for d in dates:
        r = ake_rows[d]
        series.append({
            'd': d,
            'px': gv(r,'px_avg'),
            'vol': gv(r,'vol_quote'),
            'oi': gv(r,'oi_usd'),
            'pr': gv(r,'lsr_pos_r'),
            'ar': gv(r,'lsr_acc_r'),
            'gl': gv(r,'lsr_global_r'),
            'fav': gv(r,'funding_avg'),
        })

    oi_vals = [(x['d'], x['oi']) for x in series if x['oi']]
    px_vals = [(x['d'], x['px']) for x in series if x['px']]
    pr_vals = [(x['d'], x['pr']) for x in series if x['pr']]
    gl_vals = [(x['d'], x['gl']) for x in series if x['gl']]
    vol_vals = [(x['d'], x['vol']) for x in series if x['vol']]

    if oi_vals:
        oi_min = min(oi_vals, key=lambda x: x[1])
        oi_max = max(oi_vals, key=lambda x: x[1])
        print(f"OI: min={oi_min[1]/1e6:.3f}M ({oi_min[0]}) → max={oi_max[1]/1e6:.3f}M ({oi_max[0]})")
        print(f"OI_mult: {oi_max[1]/oi_min[1]:.2f}×")
    if px_vals:
        px_min = min(px_vals, key=lambda x: x[1])
        px_max = max(px_vals, key=lambda x: x[1])
        print(f"px: min={px_min[1]:.6f} ({px_min[0]}) → max={px_max[1]:.6f} ({px_max[0]})")
        print(f"px_mult: {px_max[1]/px_min[1]:.1f}×")
    if pr_vals:
        pr_min = min(pr_vals, key=lambda x: x[1])
        pr_max = max(pr_vals, key=lambda x: x[1])
        print(f"pos_r: min={pr_min[1]:.3f} ({pr_min[0]}) → max={pr_max[1]:.3f} ({pr_max[0]})")
    if gl_vals:
        gl_min = min(gl_vals, key=lambda x: x[1])
        gl_max = max(gl_vals, key=lambda x: x[1])
        print(f"gLSR: min={gl_min[1]:.4f} ({gl_min[0]}) → max={gl_max[1]:.4f} ({gl_max[0]})")
    if vol_vals:
        vol_max = max(vol_vals, key=lambda x: x[1])
        print(f"Vol peak: {vol_max[1]/1e6:.1f}M ({vol_max[0]})")

    # Drops
    drops = []
    for i in range(1, len(series)):
        if series[i]['pr'] and series[i-1]['pr']:
            drop = (series[i]['pr'] - series[i-1]['pr']) / series[i-1]['pr']
            if drop < -0.10:
                drops.append((series[i]['d'], series[i-1]['pr'], series[i]['pr'], drop))
    if drops:
        print(f"Large pos_r drops:")
        for d, p0, p1, dr in drops[:8]:
            print(f"  {d}: {p0:.3f}→{p1:.3f} ({dr*100:+.1f}%)")

    print(f"\nFull series (last 20):")
    for x in series[-20:]:
        px_s  = f"{x['px']:.5f}" if x['px'] else "—"
        oi_s  = f"{x['oi']/1e6:.2f}M" if x['oi'] else "—"
        pr_s  = f"{x['pr']:.3f}" if x['pr'] else "—"
        gl_s  = f"{x['gl']:.4f}" if x['gl'] else "—"
        vol_s = f"{x['vol']/1e6:.1f}M" if x['vol'] else "—"
        print(f"  {x['d']}: px={px_s} OI={oi_s} pos_r={pr_s} gLSR={gl_s} vol={vol_s}")

    print(f"\nFirst 10 rows (T0 context):")
    for x in series[:10]:
        px_s  = f"{x['px']:.5f}" if x['px'] else "—"
        oi_s  = f"{x['oi']/1e6:.2f}M" if x['oi'] else "—"
        pr_s  = f"{x['pr']:.3f}" if x['pr'] else "—"
        gl_s  = f"{x['gl']:.4f}" if x['gl'] else "—"
        print(f"  {x['d']}: px={px_s} OI={oi_s} pos_r={pr_s} gLSR={gl_s}")
