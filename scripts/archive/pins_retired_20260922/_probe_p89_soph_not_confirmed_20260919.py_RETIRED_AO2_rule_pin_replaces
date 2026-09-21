"""p89 · pin M1 · SOPH (L2 loài-E per sổ) KHÔNG được vào CONFIRMED.

Fixture (D+k>5 để trigger U1 check):
  · Cross UP tại D-10 (D_cross)
  · L1 FAIL tại D_cross (Δacc_bwd chỉ -20%, không đủ -30%)
  · U1 PASS tại D+5 (D-5)
  · Kết quả: KHÔNG CONFIRMED · phải append audit reject (L2/L3 branch)

div_avg3(D) = mean(pos/acc) qua D-2, D-1, D. Cần thao tác pos_r để tạo cross UP.
"""
import sys, json
from pathlib import Path
from datetime import datetime, timedelta
try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except: pass  # L-66-OK (stdout reconfigure benign)
sys.path.insert(0, r"d:\Data back test\whale_data\scripts")

import b_state_tracker as bst

TARGET = "2026-09-19"
td = datetime.strptime(TARGET, "%Y-%m-%d").date()

# Muốn cross UP tại D-10. Set pos_r:
# D-12, D-11, D-10 window → mean = div(D-10) > 0.5
# D-13, D-12, D-11 window → mean = div(D-11) ≤ 0.5
# Đơn giản: pos_r = 0.40 cho D-13..D-12, pos_r = 0.55 cho D-11..now
# Actually cleaner: pos_r = 0.45 cho tất cả OLD (D-45..D-11), pos_r = 0.55 cho D-10..now
# → div(D-10) = mean(pos(D-12),pos(D-11),pos(D-10)) = (0.45+0.45+0.55)/3 = 0.483 KHÔNG >0.5
# Cần lag lớn hơn. pos = 0.40 cho D-45..D-11, pos = 0.65 cho D-10..now:
# → div(D-11) = (0.40+0.40+0.40)/3 = 0.40 ≤0.5 OK
# → div(D-10) = (0.40+0.40+0.65)/3 = 0.483 KHÔNG >0.5
# Cần thẳng thắn hơn. pos = 0.30 cho old, pos = 0.80 cho D-10 và sau:
# → div(D-11) = (0.30+0.30+0.30)/3 = 0.30 ≤0.5 OK
# → div(D-10) = (0.30+0.30+0.80)/3 = 0.467 KHÔNG >0.5
# → div(D-9)  = (0.30+0.80+0.80)/3 = 0.633 >0.5 OK
# → But cross detection từ D-10 → D-9 (vp=D-10 0.467 ≤0.5, v=D-9 0.633 >0.5). D_cross = D-9.
# OK — D_cross = D-9 → D+k = 9 (>5, sẽ trigger U1 check).

def _row(d, pos_r, acc_r, oi, px):
    return {
        "date": d.isoformat(),
        "lsr_pos_r": str(pos_r), "lsr_acc_r": str(acc_r),
        "lsr_global_r": str(acc_r), "oi_usd": str(oi), "px_avg": str(px),
    }

rows = []
for k in range(45, -1, -1):
    d = td - timedelta(days=k)
    if k >= 10:
        pos = 0.30   # pre-cross low
    else:
        pos = 0.80   # post-cross high
    acc = 1.0
    oi = 1e6
    px = 1.0
    rows.append(_row(d, pos, acc, oi, px))

# D_cross should be D-9 (td - 9 days)
D_CROSS = (td - timedelta(days=9)).isoformat()
D_CROSS_M3 = (td - timedelta(days=12)).isoformat()

# L1 FAIL tại D_cross · Δacc_bwd(D_cross) = (acc(D_cross)-acc(D_cross-3))/acc(D_cross-3)
# Muốn -20% (không đủ -30%): acc(D_cross-3)=1.5, acc(D_cross)=1.2
def _set(d_iso, field, value):
    for r in rows:
        if r["date"] == d_iso:
            r[field] = str(value)

_set(D_CROSS_M3, "lsr_acc_r", 1.5)
_set(D_CROSS, "lsr_acc_r", 1.2)   # Δacc_bwd = -20%
# pos stay same → |Δpos_bwd| = 0

# U1 PASS tại D+5 = D_cross+5 = td-4
D_M1 = (td - timedelta(days=10)).isoformat()   # D_cross-1
D_P5 = (td - timedelta(days=4)).isoformat()    # D_cross+5
_set(D_M1, "lsr_acc_r", 1.0)
_set(D_P5, "lsr_acc_r", 0.5)     # v1 = 0.5 ≤ 0.6 PASS
_set(D_M1, "oi_usd", 1e6)
_set(D_P5, "oi_usd", 2e6)        # v2 = 2 ≥ 1.5 PASS

# Clear existing audit
if bst.L2L3_AUDIT.exists():
    bst.L2L3_AUDIT.unlink()

state = bst.build_b_state(TARGET, universe=["SOPH"], by_sym={"SOPH": rows})

print(f"═══ p89 · SOPH L2 (L1 fail) + U1 pass · KHÔNG được CONFIRMED ═══")
d_cross_detected = bst._find_latest_cross(rows, TARGET)
print(f"  D_cross detected = {d_cross_detected}")
if d_cross_detected:
    l1_result = bst._check_u0_class_L1(rows, d_cross_detected)
    print(f"  L1 check at D_cross = {l1_result}")
    u1_result = bst._check_u1_v2v1(rows, d_cross_detected)
    print(f"  U1 check at D+5 = {u1_result}")
print(f"  state SOPH = {state.get('SOPH', 'NOT_IN_STATE')}")

tier = state.get("SOPH", {}).get("tier") if "SOPH" in state else None
p89_a = tier != "CONFIRMED"
print(f"  → SOPH tier = {tier} · KHÔNG CONFIRMED: {'PASS' if p89_a else 'FAIL'}")

audit_lines = []
if bst.L2L3_AUDIT.exists():
    audit_lines = [json.loads(l) for l in bst.L2L3_AUDIT.read_text(encoding="utf-8").splitlines() if l.strip()]
soph_audits = [a for a in audit_lines if a.get("token") == "SOPH"]
p89_b = len(soph_audits) >= 1
print(f"  audit reject entries for SOPH = {len(soph_audits)} · {'PASS' if p89_b else 'FAIL'}")
if soph_audits:
    a = soph_audits[-1]
    print(f"    reason={a.get('reason')}")

fails = sum(1 for p in [p89_a, p89_b] if not p)
print(f"\n═══ p89 · TỔNG 2 sub-cases · {fails} FAIL ═══")
sys.exit(0 if fails == 0 else 1)
