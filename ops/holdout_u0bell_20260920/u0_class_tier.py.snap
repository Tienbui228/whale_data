"""u0_class_tier · shared U0-CLASS tier classifier · α1/22-09.

Nguồn ký: fb30dd88 §3 A2.1 + AO1/22-09.
Rules:
  L1    = Δacc ≤ -15% ∧ |Δpos| ≤ 10%
  L2    = Δacc ≤ -15% ∧ |Δpos| >  10%   (fires nhưng pos đã bật · sát-D-cross)
  L3    = Δacc >  -15%                    (chưa đủ ngưỡng acc)
  BLIND = missing data (dacc/dpos None)

Consumer:
  · events_build.py · classify class events
  · hedge_v2.py · render (L2/L3 tach riêng · · spec AW p102)
  · b_l2_l3_reject.jsonl audit (nếu wire lại)

CẤM: hardcode -0.15 / 0.10 ở nơi khác. Sửa ở đây, mọi consumer thấy cùng luật.
"""
from __future__ import annotations
from typing import Optional

L1_DACC_MAX     = -0.15
L1_DPOS_MAX_ABS =  0.10


def classify_tier(dacc: Optional[float], dpos: Optional[float]) -> str:
    """Trả 'L1' | 'L2' | 'L3' | 'BLIND'."""
    if dacc is None or dpos is None:
        return "BLIND"
    if dacc <= L1_DACC_MAX:
        if abs(dpos) <= L1_DPOS_MAX_ABS:
            return "L1"
        return "L2"
    return "L3"
