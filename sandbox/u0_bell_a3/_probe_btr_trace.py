"""Trace BTR div + Δacc_bwd quanh 08-12 để chọn đúng D_bell."""
import sys, csv, importlib, math
from pathlib import Path
from datetime import datetime, timedelta
try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except: pass  # L-66-OK
sys.path.insert(0, r"d:\Data back test\whale_data\scripts")
sys.path.insert(0, r"d:\Data back test\whale_data\sandbox\u0_bell_a3")
import species_tag; importlib.reload(species_tag)
from species_tag import _div_avg3
from u0_bell import u0_bell, delta_bwd

by_sym = {}
for m in ["07","08"]:
    p = Path(rf"d:\Data back test\whale_data\data\export\freshwatch_daily_2026-{m}.csv")
    if not p.exists(): continue
    with p.open(encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            sym = r["symbol"]
            bare = sym.replace("USDT","") if sym.endswith("USDT") else sym
            by_sym.setdefault(bare, []).append(r)

rows = by_sym["BTR"]
def _flt(v):
    try: return float(v)
    except: return None

print(f"{'date':<12} {'div_avg3':>10} {'acc_r':>8} {'pos_r':>8} {'Δacc_bwd':>10} {'Δpos_bwd':>10} {'u0_bell_status':<15}")
print("─" * 82)
for d_str in ["2026-08-08","2026-08-09","2026-08-10","2026-08-11","2026-08-12","2026-08-13","2026-08-14"]:
    div = _div_avg3(rows, d_str)
    acc = _flt(next((r.get("lsr_acc_r") for r in rows if r["date"] == d_str), None))
    pos = _flt(next((r.get("lsr_pos_r") for r in rows if r["date"] == d_str), None))
    dacc, _, _ = delta_bwd(rows, d_str, "lsr_acc_r")
    dpos, _, _ = delta_bwd(rows, d_str, "lsr_pos_r")
    res = u0_bell(rows, d_str, _div_avg3)
    div_s = f"{div:.3f}" if div else "N/A"
    dacc_s = f"{dacc*100:+.1f}%" if dacc is not None else "N/A"
    dpos_s = f"{dpos*100:+.1f}%" if dpos is not None else "N/A"
    print(f"  {d_str:<10} {div_s:>10} {acc:>8.3f} {pos:>8.3f} {dacc_s:>10} {dpos_s:>10} {res['status']:<15}")
