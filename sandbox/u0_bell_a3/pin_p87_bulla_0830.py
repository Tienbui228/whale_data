"""p87 · BULLA 08-30 CONFIRMED với v2∧v1 · bật lại v3 → rớt.

Đen-một-lần:
  p87-a · v2∧v1 → BULLA 08-30 = CONFIRMED
  p87-b · v2∧v1∧v3 (bật v3) → BULLA 08-30 = rớt (vì v3=0.970 < 1.0)
"""
import sys, csv, math
from pathlib import Path
from datetime import datetime, timedelta
try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except: pass  # L-66-OK

by_sym = {}
for m in ["07","08","09"]:
    p = Path(rf"d:\Data back test\whale_data\data\export\freshwatch_daily_2026-{m}.csv")
    if not p.exists(): continue
    with p.open(encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            sym = r["symbol"]
            bare = sym.replace("USDT","") if sym.endswith("USDT") else sym
            by_sym.setdefault(bare, []).append(r)

def _flt(v):
    if v is None or v == "": return None
    try:
        f = float(v)
        return None if math.isnan(f) else f
    except: return None


TOK = "BULLA"
D_CROSS = "2026-08-30"
D_M1 = "2026-08-29"
D_P5 = "2026-09-04"

rows = by_sym[TOK]

def _r(dt, field):
    return _flt(next((r.get(field) for r in rows if r["date"] == dt), None))

acc_p5 = _r(D_P5, "lsr_acc_r"); acc_m1 = _r(D_M1, "lsr_acc_r")
oi_p5 = _r(D_P5, "oi_usd"); oi_m1 = _r(D_M1, "oi_usd")
pos_p5 = _r(D_P5, "lsr_pos_r"); pos_m1 = _r(D_M1, "lsr_pos_r")

v1r = acc_p5 / acc_m1
v2r = oi_p5 / oi_m1
v3r = pos_p5 / pos_m1

print(f"═══ p87 · BULLA 08-30 CONFIRMED · v2∧v1 vs v2∧v1∧v3 ═══\n")
print(f"D_cross={D_CROSS} · D-1={D_M1} · D+5={D_P5}")
print(f"  v1 = acc(D+5)/acc(D-1) = {acc_p5:.4f}/{acc_m1:.4f} = {v1r:.3f}  · threshold ≤ 0.6 · pass={v1r<=0.6}")
print(f"  v2 = OI(D+5)/OI(D-1)   = {oi_p5:.0f}/{oi_m1:.0f} = {v2r:.3f}  · threshold ≥ 1.5 · pass={v2r>=1.5}")
print(f"  v3 = pos(D+5)/pos(D-1) = {pos_p5:.4f}/{pos_m1:.4f} = {v3r:.3f}  · threshold ≥ 1.0 · pass={v3r>=1.0}")

# p87-a
p87_a = (v1r <= 0.6) and (v2r >= 1.5)
print(f"\np87-a · v2∧v1 → BULLA 08-30 CONFIRMED · {'PASS' if p87_a else 'FAIL'}")

# p87-b · bật v3 → rớt
v3_pass = v3r >= 1.0
p87_b = (not v3_pass) and (v1r <= 0.6) and (v2r >= 1.5)
# Chấm v2∧v1∧v3: nếu v3 pass thì confirmed, nếu v3 rớt thì fail
v2v1v3_confirmed = v1r <= 0.6 and v2r >= 1.5 and v3_pass
print(f"p87-b · v2∧v1∧v3 → v3={v3r:.3f} < 1.0 · fail · v2∧v1∧v3 confirmed = {v2v1v3_confirmed} · expect False · {'PASS' if not v2v1v3_confirmed else 'FAIL'}")

fails = sum(1 for p in [p87_a, not v2v1v3_confirmed] if not p)
print(f"\n═══ p87 · TỔNG 2 sub-cases · {fails} FAIL ═══")
sys.exit(0 if fails == 0 else 1)
