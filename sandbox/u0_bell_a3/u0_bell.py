"""U0-BELL detector · A3.1' · sandbox · CALIBRATION-ONLY · KHÔNG WIRE.

Định nghĩa (A5-0 · A3.1'):
  Điều kiện:
    · div_avg3(D) ≤ 0.5              (đang hedge)
    · Δacc_bwd(D) ≤ −T                (crowd rời acc mạnh, backward window)
  Trong đó:
    Δacc_bwd(D) = (acc(D) − acc(D−3)) / acc(D−3)

  BỎ cap |Δpos_bwd| (per A5-0): Δpos_bwd chỉ in làm MÔ TẢ trong dòng,
  KHÔNG tham gia chấm. Lý do: A4 cho thấy cap 10% loại BTR proven mà không
  giữ được specificity (BROCCOLIF3B nhiễu vào).

  Blind rule:
    · acc(D) hoặc acc(D−3) is None → NO BELL · in [U0-BLIND] vào audit
    · Tuyệt đối KHÔNG coi thiếu data = thoả điều kiện

  NEAR:
    · −T < Δacc_bwd(D) ≤ −T_near (mặc định −15%) → [U0-NEAR] · chỉ audit

  Line format (khi wire live):
    UNHEDGE: <tok> [U0-BELL D=dd/mm · Δacc_bwd=<as-printed>] [Δpos_bwd=<as-printed> · desc] [CALIBRATION-ONLY]

D_known = D · lead thực = D_cross − D (không anchor offset).
"""
from __future__ import annotations
from datetime import datetime, timedelta
from typing import Optional, Tuple, Literal

# ── Constants (pre-registered · A5-0 A3.1') ──
DIV_HEDGE_MAX = 0.5
DACC_BELL_MAX_DEFAULT = -0.20   # Δacc_bwd ≤ threshold → BELL
DACC_NEAR_MAX_DEFAULT = -0.15   # -threshold < Δacc_bwd ≤ -0.15 → NEAR
BWD_WINDOW    = 3               # (X(D) - X(D-3)) / X(D-3)


def _get_field(rows, date_str, field):
    for r in rows:
        if r["date"] == date_str:
            v = r.get(field)
            if v is None or v == "": return None
            try:
                f = float(v)
                import math
                if math.isnan(f): return None
                return f
            except (TypeError, ValueError):
                return None
    return None


def delta_bwd(rows, target_date: str, field: str) -> Tuple[Optional[float], Optional[float], Optional[float]]:
    """Trả (delta_bwd, X(D), X(D-3)). None nếu D hoặc D-3 blind."""
    td = datetime.strptime(target_date, "%Y-%m-%d").date()
    d_m3 = (td - timedelta(days=BWD_WINDOW)).isoformat()
    x_D = _get_field(rows, target_date, field)
    x_m3 = _get_field(rows, d_m3, field)
    if x_D is None or x_m3 is None or x_m3 == 0:
        return (None, x_D, x_m3)
    return ((x_D - x_m3) / x_m3, x_D, x_m3)


BellStatus = Literal["BELL", "NEAR", "BLIND", "MISS"]


def u0_bell(rows, target_date: str, div_avg3_fn,
            dacc_bell_max: float = DACC_BELL_MAX_DEFAULT,
            dacc_near_max: float = DACC_NEAR_MAX_DEFAULT) -> dict:
    """Trả dict:
      {status: 'BELL'|'NEAR'|'BLIND'|'MISS',
       reason: str, dacc_bwd, dpos_bwd, div_D, acc_D, acc_m3, pos_D, pos_m3,
       audit: line for audit log if applicable}

    A5-0 · BỎ cap |Δpos_bwd| · pos_bwd chỉ MÔ TẢ.
    Blind trước NEAR trước BELL. Chỉ cần acc data để chấm BELL.
    """
    div_D = div_avg3_fn(rows, target_date)

    # Compute deltas
    dacc, acc_D, acc_m3 = delta_bwd(rows, target_date, "lsr_acc_r")
    dpos, pos_D, pos_m3 = delta_bwd(rows, target_date, "lsr_pos_r")

    result = {
        "div_D": div_D, "acc_D": acc_D, "acc_m3": acc_m3,
        "pos_D": pos_D, "pos_m3": pos_m3,
        "dacc_bwd": dacc, "dpos_bwd": dpos,
    }

    # BLIND check (Δacc)
    if acc_D is None or acc_m3 is None:
        result["status"] = "BLIND"
        result["reason"] = f"acc(D)={acc_D} · acc(D-3)={acc_m3}"
        result["audit"] = f"[U0-BLIND] {target_date} · {result['reason']}"
        return result

    # BLIND check (div)
    if div_D is None:
        result["status"] = "BLIND"
        result["reason"] = f"div_avg3(D) is None"
        result["audit"] = f"[U0-BLIND] {target_date} · {result['reason']}"
        return result

    # Not in hedge
    if div_D > DIV_HEDGE_MAX:
        result["status"] = "MISS"
        result["reason"] = f"div(D)={div_D:.3f} > {DIV_HEDGE_MAX} (không hedge)"
        return result

    # Δacc filter · A5-0 · NO Δpos cap
    if dacc > dacc_near_max:
        result["status"] = "MISS"
        result["reason"] = f"Δacc_bwd={dacc*100:+.1f}% > {dacc_near_max*100:.0f}% (không đủ rơi)"
        return result

    # In NEAR band?
    if dacc > dacc_bell_max:  # -T < dacc ≤ -T_near
        result["status"] = "NEAR"
        result["reason"] = f"NEAR: {dacc_bell_max*100:.0f}% < Δacc_bwd={dacc*100:+.1f}% ≤ {dacc_near_max*100:.0f}%"
        result["audit"] = f"[U0-NEAR] {target_date} · Δacc_bwd={dacc*100:+.1f}%"
        return result

    # BELL! (dacc ≤ dacc_bell_max)
    result["status"] = "BELL"
    dpos_str = f"{dpos*100:+.1f}%" if dpos is not None else "N/A"
    result["reason"] = (f"Δacc_bwd={dacc*100:+.1f}% ≤ {dacc_bell_max*100:.0f}% ∧ "
                       f"div(D)={div_D:.3f} ≤ {DIV_HEDGE_MAX} "
                       f"[Δpos_bwd={dpos_str} · desc-only]")
    return result


def format_bell_line(tok: str, target_date: str, res: dict) -> str:
    """UNHEDGE: <tok> [U0-BELL D=dd/mm · Δacc_bwd=<±X%>] [Δpos_bwd=<±X%> · desc] [CALIBRATION-ONLY]

    A5-0: pos_bwd trong khối [desc], không trong khối chấm.
    """
    td = datetime.strptime(target_date, "%Y-%m-%d").date()
    dd_mm = f"{td.day:02d}/{td.month:02d}"
    dacc = res["dacc_bwd"]
    dpos = res["dpos_bwd"]
    dacc_s = f"{dacc*100:+.1f}%" if dacc is not None else "N/A"
    dpos_s = f"{dpos*100:+.1f}%" if dpos is not None else "N/A"
    return (f"UNHEDGE: {tok} [U0-BELL D={dd_mm} · Δacc_bwd={dacc_s}] "
            f"[Δpos_bwd={dpos_s} · desc] [CALIBRATION-ONLY]")
