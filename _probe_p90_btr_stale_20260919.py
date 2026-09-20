"""p90 · pin M1 · D+k>30 · L1 pass · U1 pass · no candle +20% → STALE.

Fixture design:
  · pos_r=0.30 constant (|Δpos_bwd|=0 → L1 pos check PASS)
  · acc_r=2.0 pre-cross (k>=41) · acc=0.4 post-cross (k<41)
  · div_avg3 = mean(pos/acc) trên window 3d → cross UP tại D-39
  · L1 Δacc_bwd(D_cross=D-39) = (0.4-2.0)/2.0 = -80% ≤-30% PASS
  · U1 tại D+5 = D-34 · set acc(D-34)=0.2, oi(D-34)=2e6, oi(D-40)=1e6 → v1=0.5, v2=2 PASS
  · px=1.0 constant → không nến +20%
"""
import sys
from pathlib import Path
from datetime import datetime, timedelta
try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except: pass  # L-66-OK (stdout reconfigure benign)
sys.path.insert(0, r"d:\Data back test\whale_data\scripts")

import b_state_tracker as bst

TARGET = "2026-09-19"
td = datetime.strptime(TARGET, "%Y-%m-%d").date()

def _row(d, pos_r, acc_r, oi, px):
    return {
        "date": d.isoformat(), "lsr_pos_r": str(pos_r), "lsr_acc_r": str(acc_r),
        "lsr_global_r": str(acc_r), "oi_usd": str(oi), "px_avg": str(px),
    }

rows = []
for k in range(45, -1, -1):
    d = td - timedelta(days=k)
    pos = 0.30   # constant
    acc = 2.0 if k >= 41 else 0.4
    oi = 1e6
    px = 1.0
    rows.append(_row(d, pos, acc, oi, px))

# Override for U1 pass at D+5 (D-34) · D_cross expected = D-39
def _set(d_iso, field, value):
    for r in rows:
        if r["date"] == d_iso:
            r[field] = str(value)

# U1: acc(D+5=D-34)/acc(D-1=D-40) ≤ 0.6
D_M40 = (td - timedelta(days=40)).isoformat()   # D_cross-1 (k=40 < 41 → acc=0.4 default)
D_M34 = (td - timedelta(days=34)).isoformat()   # D_cross+5
_set(D_M34, "lsr_acc_r", 0.2)   # v1 = 0.2/0.4 = 0.5 ≤0.6 PASS
_set(D_M40, "oi_usd", 1e6)
_set(D_M34, "oi_usd", 2e6)      # v2 = 2 PASS

state = bst.build_b_state(TARGET, universe=["BTR"], by_sym={"BTR": rows})

print(f"═══ p90 · BTR D+k>30 · L1+U1 pass · no candle +20% → STALE ═══")
d_cross_detected = bst._find_latest_cross(rows, TARGET)
print(f"  D_cross detected = {d_cross_detected}")
if d_cross_detected:
    print(f"  L1 = {bst._check_u0_class_L1(rows, d_cross_detected)}")
    print(f"  U1 = {bst._check_u1_v2v1(rows, d_cross_detected)}")
    dpk = (td - datetime.strptime(d_cross_detected, "%Y-%m-%d").date()).days
    print(f"  D+k = {dpk}")
print(f"  has_candle_up_20%_30d = {bst._has_candle_up_pct(rows, TARGET, 30, 0.20)}")
print(f"  state BTR = {state.get('BTR')}")

tier = state.get("BTR", {}).get("tier")
d_plus_k = state.get("BTR", {}).get("d_plus_k")
p90 = (tier == "STALE" and d_plus_k is not None and d_plus_k > 30)
print(f"  → BTR tier={tier} d_plus_k={d_plus_k} · {'PASS' if p90 else 'FAIL'}")

sys.exit(0 if p90 else 1)
