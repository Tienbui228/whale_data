"""fund_state · shared funding-state classifier · α2/22-09 · leg4'.

Rules (ANALYSIS AW-α'):
  PIN       = f_min ≈ 5e-5 (round 8 chữ số → same bucket) ≥ 5/7 days
  SHORT-TRẢ = f_avg ≤ 0 ≥ 3/7 days
  NONE      = còn lại

Consumer:
  · hedge_v2.render_registry_block
  · gom_e (H2 gate độc lập · giữ; fund_state chỉ dùng cho display)

CẤM: dùng ngưỡng khác ở nơi khác cho display. Sửa ở đây → nhất quán 2 bên.
"""
from __future__ import annotations
import math
from typing import Optional

PIN_F_MIN_BUCKET = 5e-5   # ≈ 5e-5 · round 8 chữ số
PIN_MIN_DAYS     = 5      # ≥ 5/7
SHORT_MIN_DAYS   = 3      # ≥ 3/7


def _bucket_5e5(v: Optional[float]) -> bool:
    """f_min ≈ 5e-5 · round 8 chữ số → cùng bucket."""
    if v is None or (isinstance(v, float) and math.isnan(v)): return False
    return round(float(v), 8) == round(PIN_F_MIN_BUCKET, 8)


def fund_state_7d(days: list[dict]) -> str:
    """days: list ≤7 phần tử [{"f_min": float, "f_avg": float}, ...]

    Trả 'PIN' | 'SHORT-TRẢ' | 'NONE'.
    """
    if not days: return "NONE"
    days = days[-7:]  # 7 ngày gần nhất
    n_pin = sum(1 for d in days if _bucket_5e5(d.get("f_min")))
    n_short = 0
    for d in days:
        fa = d.get("f_avg")
        if fa is None or (isinstance(fa, float) and math.isnan(fa)): continue
        if fa <= 0: n_short += 1
    if n_pin >= PIN_MIN_DAYS:
        return "PIN"
    if n_short >= SHORT_MIN_DAYS:
        return "SHORT-TRẢ"
    return "NONE"
