"""p92 · pin N3 · CROSS tier phải mang nhãn [B-CROSS], KHÔNG BAO GIỜ [B-cand].

Token có D_cross ≤5d ∧ L1 pass → tier=CROSS → prefix `[B-CROSS]`.
KHÔNG bao giờ dùng `[B-cand]` cho token đã cross.
"""
import sys, re
from pathlib import Path
from datetime import datetime, timedelta
try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except: pass  # L-66-OK (stdout reconfigure benign)
sys.path.insert(0, r"d:\Data back test\whale_data\scripts")

import b_state_tracker as bst
from b_block_renderer import render_b_block

TARGET = "2026-09-19"
td = datetime.strptime(TARGET, "%Y-%m-%d").date()

# Fixture: FOO có cross D-2 (D+k=2, ≤5) · L1 pass → tier=CROSS
def _row(d, pos_r, acc_r, oi, px):
    return {
        "date": d.isoformat(), "lsr_pos_r": str(pos_r), "lsr_acc_r": str(acc_r),
        "lsr_global_r": str(acc_r), "oi_usd": str(oi), "px_avg": str(px),
    }

rows = []
for k in range(45, -1, -1):
    d = td - timedelta(days=k)
    pos = 0.30   # constant → |Δpos_bwd|=0 (L1 pos check PASS)
    # acc flip tại k<4 · div_avg3 cross UP tại D-3 (D+k=3, ≤5 → CROSS tier)
    acc = 2.0 if k >= 4 else 0.2
    oi = 1e6
    px = 1.0
    rows.append(_row(d, pos, acc, oi, px))

state = bst.build_b_state(TARGET, universe=["FOO"], by_sym={"FOO": rows})
print(f"═══ p92 · CROSS tier prefix [B-CROSS] ═══")
print(f"  state FOO = {state.get('FOO', 'NOT_IN_STATE')}")

tier = state.get("FOO", {}).get("tier")
if tier != "CROSS":
    print(f"  FIXTURE ERR: expected tier=CROSS, got tier={tier}")
    print(f"  D_cross = {bst._find_latest_cross(rows, TARGET)}")
    print(f"  L1 = {bst._check_u0_class_L1(rows, bst._find_latest_cross(rows, TARGET))}")
    sys.exit(1)

body = render_b_block(TARGET, universe=["FOO"], by_sym={"FOO": rows})
print(f"─── body ───")
print(body)
print(f"─── end body ───")

# Verify: có `[B-CROSS] FOO` line · KHÔNG có `[B-cand] FOO`
p92_a = bool(re.search(r"\[B-CROSS\]\s+FOO", body))
p92_b = not bool(re.search(r"\[B-cand\]\s+FOO", body))

print(f"\np92-a · [B-CROSS] FOO trong body: {'PASS' if p92_a else 'FAIL'}")
print(f"p92-b · KHÔNG [B-cand] FOO trong body: {'PASS' if p92_b else 'FAIL'}")

fails = sum(1 for p in [p92_a, p92_b] if not p)
print(f"\n═══ p92 · TỔNG 2 sub-cases · {fails} FAIL ═══")
sys.exit(0 if fails == 0 else 1)
