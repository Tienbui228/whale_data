"""Điều tra vì sao 5 ca đích danh KHÔNG kêu.
Print div/acc/pos/Δacc_bwd/Δpos_bwd/status cho ±10d quanh target."""
import sys, csv, importlib, math
from pathlib import Path
from datetime import datetime, timedelta
try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except: pass  # L-66-OK
sys.path.insert(0, r"d:\Data back test\whale_data\scripts")
sys.path.insert(0, r"d:\Data back test\whale_data\sandbox\u0_bell_a3")
import u0_bell as u0mod; importlib.reload(u0mod)
import species_tag; importlib.reload(species_tag)
from species_tag import _div_avg3
from u0_bell import u0_bell

by_sym = {}
for m in ["05","06","07","08","09"]:
    p = Path(rf"d:\Data back test\whale_data\data\export\freshwatch_daily_2026-{m}.csv")
    if not p.exists(): continue
    with p.open(encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            sym = r["symbol"]
            bare = sym.replace("USDT","") if sym.endswith("USDT") else sym
            d_iso = r["date"]
            d_row = datetime.strptime(d_iso, "%Y-%m-%d").date()
            if d_row < datetime(2026,9,20).date():
                by_sym.setdefault(bare, []).append(r)

def _flt(v):
    try: return float(v) if v not in (None,"") else None
    except: return None
def _get(rows,dt,f):
    for r in rows:
        if r["date"]==dt: return _flt(r.get(f))
    return None

CASES = [
    ("MITO",     "2026-09-08", "2026-09-13"),
    ("MARSCOIN", "2026-09-05", "2026-09-12"),
    ("UAI",      "2026-08-03", "2026-08-24"),
    ("BULLA",    "2026-09-01", "2026-09-08"),
    ("HEMI",     "2026-08-13", "2026-08-19"),
]

for tok, d_s, d_e in CASES:
    rows = by_sym.get(tok, [])
    if not rows:
        print(f"── {tok} [NO-DATA]\n"); continue
    print(f"── {tok} · window {d_s} → {d_e} ──")
    print(f"  {'date':<12} {'div':>6} {'acc':>7} {'acc(D-3)':>9} {'Δacc%':>7} {'pos':>6} {'Δpos%':>7} {'status':<7}")
    ds = datetime.strptime(d_s,"%Y-%m-%d").date()
    de = datetime.strptime(d_e,"%Y-%m-%d").date()
    d = ds
    while d <= de:
        dt = d.isoformat()
        res = u0_bell(rows, dt, _div_avg3, dacc_bell_max=-0.20)
        div = res.get("div_D"); acc = res.get("acc_D"); acc_m3 = res.get("acc_m3")
        pos = res.get("pos_D"); dacc = res.get("dacc_bwd"); dpos = res.get("dpos_bwd")
        div_s = f"{div:.3f}" if div is not None else "N/A"
        acc_s = f"{acc:.3f}" if acc is not None else "N/A"
        acc_m3_s = f"{acc_m3:.3f}" if acc_m3 is not None else "N/A"
        dacc_s = f"{dacc*100:+.1f}%" if dacc is not None else "N/A"
        pos_s = f"{pos:.3f}" if pos is not None else "N/A"
        dpos_s = f"{dpos*100:+.1f}%" if dpos is not None else "N/A"
        print(f"  {dt:<12} {div_s:>6} {acc_s:>7} {acc_m3_s:>9} {dacc_s:>7} {pos_s:>6} {dpos_s:>7} {res['status']:<7}")
        d += timedelta(days=1)
    print()
