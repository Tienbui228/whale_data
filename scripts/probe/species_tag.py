"""SPECIES-TAG · V3.5r offline probe · KHÔNG wire renderer sống.

Rules [A]-[E] draft (không phải gate · cấm tune · cấm dùng để fire).

Input: token + target date T + store df + optional sidecar snapshot dict
Output: {tag: 'A'|'B'|'C'|'D'|'E'|'?', matched: [...], reasons: [...], blind_axes: [...]}

Trục chính · phân loại MÙ:
  A=LSR · B=GOM-E/List-A · C=klines∧LSR · D=OI∨EXCH-BAL · E=klines(T)

Khớp ≥3 loài → giữ 2 ĐẶC HIỆU theo C>D>B>A · in theo chữ cái.
Zero-tag ∧ ≥1 loài có trục chính mù tại T → in [?] (không phải loài).
Token đã có nhãn → không in [?].

Fixture format: sổ-ăn-sự-kiện + sidecar snapshot BẢN SAO — không đọc file gốc.
"""
from __future__ import annotations
import math
from typing import Iterable, Any


# ═════════ HẰNG GÁN-NHÃN (draft · không tune) ═════════
FUNDING_PIN_VALUE = 0.00005
FUNDING_PIN_TOL = 1e-9
FUNDING_PIN_MIN_STREAK = 7   # 7/7 days [T-6, T]
A_POS_RAMP_14D_MIN = 1.25
A_CLOSE_LOW30_MAX_MULT = 1.15
A_OI_OVER14_MAX = 1.15

B_GLSR_MIN = 2.0
B_ACC_MIN = 2.0
B_DIV_RUN_MAX = 0.5
B_DIV_RUN_LEN_MIN = 3
B_DIV_RUN_WINDOW = 30

C_DMIN_WINDOW = 30
C_H_BACK_WINDOW = 30
C_H_MIN_POINTS = 21          # SÀN: cửa sổ H phải có ≥21 close non-null
C_DUMP_MULT = 0.60
C_PLATEAU_WINDOW = 7
C_PLATEAU_MAX_DEV = 0.15
C_MIN_LAG = 7
C_POS_HOLD_MULT = 0.90

D_OI_MULT = 1.5
D_EXCH_MULT = 1.15
D_CLOSE_BAND_LO = 0.90
D_CLOSE_BAND_HI = 1.60

E_SPIKE_MIN = 0.35           # +35% on T-1
E_FOLLOW_MAX = 0.10          # T follow ≤ +10%

TAG_ORDER = {"C": 0, "D": 1, "B": 2, "A": 3}   # ĐẶC HIỆU DESC (số nhỏ = ĐẶC HIỆU HƠN)
CHANNEL_ORDER = {"GOM-H": 0, "HEDGE": 1, "KHO": 2, "FRESH": 3, "RÒNG": 4}


# ═════════ helpers ═════════
def _values_upto(rows: list[dict], target_date: str, field: str, n: int, include_target: bool = True) -> list[float]:
    """Return non-null values for `field` in the most recent n days ≤ target (inclusive)."""
    sorted_rows = sorted(rows, key=lambda r: r["date"])
    if include_target:
        window = [r for r in sorted_rows if r["date"] <= target_date]
    else:
        window = [r for r in sorted_rows if r["date"] < target_date]
    tail = window[-n:]
    out = []
    for r in tail:
        v = r.get(field)
        if v is None: continue
        try:
            v = float(v)
            if not math.isnan(v):
                out.append(v)
        except (TypeError, ValueError):
            continue
    return out


def _get(rows: list[dict], date: str, field: str) -> float | None:
    for r in rows:
        if r["date"] == date:
            v = r.get(field)
            try:
                v = float(v)
                if math.isnan(v): return None
                return v
            except (TypeError, ValueError):
                return None
    return None


def _at_offset(rows: list[dict], target_date: str, field: str, offset_days_back: int) -> float | None:
    """Get value at date exactly (offset_days_back) before target."""
    from datetime import datetime, timedelta
    td = datetime.strptime(target_date, "%Y-%m-%d").date()
    target = (td - timedelta(days=offset_days_back)).isoformat()
    return _get(rows, target, field)


def _min_over(rows: list[dict], target_date: str, field: str, n: int) -> float | None:
    vs = _values_upto(rows, target_date, field, n, include_target=True)
    if not vs: return None
    return min(vs)


def _div_avg3(rows: list[dict], target_date: str) -> float | None:
    """div_avg3(T) = mean of last 3 days pos_r/acc_r (both non-null, acc_r > 0)."""
    from datetime import datetime, timedelta
    td = datetime.strptime(target_date, "%Y-%m-%d").date()
    ratios = []
    for d in range(2, -1, -1):
        dt = (td - timedelta(days=d)).isoformat()
        pos = _get(rows, dt, "lsr_pos_r")
        acc = _get(rows, dt, "lsr_acc_r")
        if pos is None or acc is None or acc <= 0: continue
        ratios.append(pos / acc)
    if len(ratios) < 3: return None
    return sum(ratios) / len(ratios)


def _has_run_div_le(rows: list[dict], target_date: str, threshold: float, min_len: int, window: int) -> bool:
    from datetime import datetime, timedelta
    td = datetime.strptime(target_date, "%Y-%m-%d").date()
    # For each day in [T-window+1, T], compute div_avg3
    divs_per_day = []
    for d in range(window - 1, -1, -1):
        dt = (td - timedelta(days=d)).isoformat()
        v = _div_avg3(rows, dt)
        divs_per_day.append((dt, v))
    # Find consecutive runs where div ≤ threshold
    cur_len = 0
    max_last_day = None
    best_end = None
    for dt, v in divs_per_day:
        if v is not None and v <= threshold:
            cur_len += 1
            if cur_len >= min_len:
                best_end = dt   # keep updating end
        else:
            cur_len = 0
    return best_end is not None


# ═════════ rules [A]-[E] ═════════
def check_A(rows: list[dict], target_date: str) -> tuple[bool, list[str], bool]:
    """Return (matched, reasons, blind).
    Blind = trục chính LSR mù tại T (pos_r None at T)."""
    reasons = []
    pos_T = _get(rows, target_date, "lsr_pos_r")
    if pos_T is None:
        return (False, ["A-blind: pos_r(T) missing"], True)
    pos_14 = _at_offset(rows, target_date, "lsr_pos_r", 14)
    pos_7 = _at_offset(rows, target_date, "lsr_pos_r", 7)
    if pos_14 is None or pos_7 is None:
        return (False, ["A-blind: pos_r(T-14 or T-7) missing"], True)
    close_T = _get(rows, target_date, "px_avg")
    oi_T = _get(rows, target_date, "oi_usd")
    oi_14 = _at_offset(rows, target_date, "oi_usd", 14)
    low_30 = _min_over(rows, target_date, "px_avg", 30)
    fund_7 = _values_upto(rows, target_date, "funding_avg", 7)
    # ZA1: any vế-required value missing → BLIND (not silent-False)
    if close_T is None or low_30 is None:
        return (False, ["A-blind: close(T) or low_30 missing"], True)
    if oi_T is None or oi_14 is None:
        return (False, ["A-blind: oi(T) or oi(T-14) missing"], True)
    if len(fund_7) < FUNDING_PIN_MIN_STREAK:
        return (False, [f"A-blind: funding_avg 7d-tail has {len(fund_7)}<{FUNDING_PIN_MIN_STREAK}"], True)
    v_pos_ramp_14 = pos_T >= A_POS_RAMP_14D_MIN * pos_14
    v_pos_ge_7 = pos_T >= pos_7
    v_close = close_T <= A_CLOSE_LOW30_MAX_MULT * low_30
    v_oi = oi_T <= A_OI_OVER14_MAX * oi_14
    v_fund = all(abs(f - FUNDING_PIN_VALUE) <= FUNDING_PIN_TOL for f in fund_7[-FUNDING_PIN_MIN_STREAK:])
    reasons.append(f"pos_ramp_14d={v_pos_ramp_14} pos_ge_7={v_pos_ge_7} close_low30={v_close} oi_flat={v_oi} fund_pin_7d={v_fund}")
    matched = v_pos_ramp_14 and v_pos_ge_7 and v_close and v_oi and v_fund
    return (matched, reasons, False)


def check_B(rows: list[dict], target_date: str) -> tuple[bool, list[str], bool]:
    reasons = []
    glsr_T = _get(rows, target_date, "lsr_global_r")
    acc_T = _get(rows, target_date, "lsr_acc_r")
    # Trục chính B = GOM-E/List-A — for probe, we use LSR ratios as proxy (no sidecar-derived signal)
    if glsr_T is None and acc_T is None:
        return (False, ["B-blind: gLSR and acc_r both missing at T"], True)
    v_ratio = (glsr_T is not None and glsr_T >= B_GLSR_MIN) or (acc_T is not None and acc_T >= B_ACC_MIN)
    v_run = _has_run_div_le(rows, target_date, B_DIV_RUN_MAX, B_DIV_RUN_LEN_MIN, B_DIV_RUN_WINDOW)
    reasons.append(f"gLSR_or_acc≥2={v_ratio} div_run≤0.5×{B_DIV_RUN_LEN_MIN}d_in_{B_DIV_RUN_WINDOW}d={v_run}")
    return (v_ratio and v_run, reasons, False)


def check_C(rows: list[dict], target_date: str) -> tuple[bool, list[str], bool]:
    """C requires close∧LSR both non-mute."""
    from datetime import datetime, timedelta
    reasons = []
    td = datetime.strptime(target_date, "%Y-%m-%d").date()
    # Find D_min in [T-30, T]
    window = []
    for d in range(C_DMIN_WINDOW, -1, -1):
        dt = (td - timedelta(days=d)).isoformat()
        v = _get(rows, dt, "px_avg")
        if v is not None: window.append((dt, v))
    if not window:
        return (False, ["C-blind: no close in [T-30,T]"], True)
    d_min_dt, d_min_close = min(window, key=lambda x: x[1])
    d_min_date = datetime.strptime(d_min_dt, "%Y-%m-%d").date()
    # H window: [D_min-30, D_min-1]
    h_window = []
    for d in range(1, C_H_BACK_WINDOW + 1):
        dt = (d_min_date - timedelta(days=d)).isoformat()
        v = _get(rows, dt, "px_avg")
        if v is not None: h_window.append(v)
    if len(h_window) < C_H_MIN_POINTS:
        return (False, [f"C-blind: H-window has {len(h_window)}<{C_H_MIN_POINTS} points"], True)
    H = max(h_window)
    # close(D_min) ≤ 0.60*H
    v_dump = d_min_close <= C_DUMP_MULT * H
    # plateau [T-7, T]: |close(d)/close(D_min) - 1| ≤ 15%
    plateau_vals = []
    for d in range(C_PLATEAU_WINDOW - 1, -1, -1):
        dt = (td - timedelta(days=d)).isoformat()
        v = _get(rows, dt, "px_avg")
        if v is not None: plateau_vals.append(v)
    v_plateau = (len(plateau_vals) >= C_PLATEAU_WINDOW and
                 all(abs(x / d_min_close - 1) <= C_PLATEAU_MAX_DEV for x in plateau_vals))
    # T - D_min ≥ 7
    lag = (td - d_min_date).days
    v_lag = lag >= C_MIN_LAG
    # pos_r(T) ≥ 0.90*pos_r(D_min)
    pos_T = _get(rows, target_date, "lsr_pos_r")
    pos_dmin = _get(rows, d_min_dt, "lsr_pos_r")
    if pos_T is None or pos_dmin is None:
        return (False, [f"C-blind: LSR mù at T or D_min={d_min_dt}"], True)
    v_pos = pos_T >= C_POS_HOLD_MULT * pos_dmin
    reasons.append(f"D_min={d_min_dt} close={d_min_close:.6f} H={H:.6f} lag={lag} dump={v_dump} plateau={v_plateau} lag_ok={v_lag} pos_hold={v_pos}")
    return (v_dump and v_plateau and v_lag and v_pos, reasons, False)


def check_D(rows: list[dict], target_date: str, exch_bal: dict | None = None) -> tuple[bool, list[str], bool]:
    """D-trục chính = OI ∨ EXCH-BAL. exch_bal={date: bal} optional."""
    reasons = []
    oi_T = _get(rows, target_date, "oi_usd")
    oi_14 = _at_offset(rows, target_date, "oi_usd", 14)
    oi_ok = (oi_T is not None and oi_14 is not None and oi_T >= D_OI_MULT * oi_14)
    exch_ok = False
    if exch_bal:
        from datetime import datetime, timedelta
        td = datetime.strptime(target_date, "%Y-%m-%d").date()
        dt14 = (td - timedelta(days=14)).isoformat()
        bal_T = exch_bal.get(target_date)
        bal_14 = exch_bal.get(dt14)
        exch_ok = (bal_T is not None and bal_14 is not None and bal_T >= D_EXCH_MULT * bal_14)
    # Trục mù nếu OI None AND EXCH-BAL None
    if oi_T is None and (not exch_bal or exch_bal.get(target_date) is None):
        return (False, ["D-blind: OI and EXCH-BAL both mù at T"], True)
    close_T = _get(rows, target_date, "px_avg")
    close_14 = _at_offset(rows, target_date, "px_avg", 14)
    # ZA1: close(T) or close(T-14) missing → BLIND (not silent-False)
    if close_T is None or close_14 is None:
        return (False, ["D-blind: close(T) or close(T-14) missing"], True)
    v_close = D_CLOSE_BAND_LO <= close_T / close_14 <= D_CLOSE_BAND_HI
    v_norun = not _has_run_div_le(rows, target_date, B_DIV_RUN_MAX, B_DIV_RUN_LEN_MIN, B_DIV_RUN_WINDOW)
    reasons.append(f"oi_x1.5={oi_ok} exch_x1.15={exch_ok} close_band={v_close} no_div_run={v_norun}")
    return ((oi_ok or exch_ok) and v_close and v_norun, reasons, False)


def check_E(rows: list[dict], target_date: str) -> tuple[bool, list[str], bool, bool]:
    """Return (matched, reasons, blind, e_pending).
    e_pending = klines(T) chưa có → in `[E] no-follow draft`, KHÔNG gán."""
    reasons = []
    close_T = _get(rows, target_date, "px_avg")
    close_T1 = _at_offset(rows, target_date, "px_avg", 1)
    close_T2 = _at_offset(rows, target_date, "px_avg", 2)
    if close_T1 is None or close_T2 is None:
        return (False, ["E-blind: T-1 or T-2 close missing"], True, False)
    spike_ok = (close_T2 > 0 and (close_T1 / close_T2 - 1) >= E_SPIKE_MIN)
    if not spike_ok:
        return (False, [f"spike_T-1_vs_T-2={close_T1/close_T2-1:.3f} < {E_SPIKE_MIN}"], False, False)
    # spike present · check T follow
    if close_T is None:
        return (False, ["E-pending: klines(T) chưa có"], False, True)
    follow_ok = (close_T1 > 0 and (close_T / close_T1 - 1) <= E_FOLLOW_MAX)
    reasons.append(f"spike={close_T1/close_T2-1:.3f} follow={close_T/close_T1-1:.3f}")
    return (spike_ok and follow_ok, reasons, False, False)


# ═════════ orchestrator ═════════
def tag_species(rows: list[dict], target_date: str, exch_bal: dict | None = None) -> dict:
    """Return {tags: [str], matched_all: [str], blind_axes: [str], reasons: {tag: [str]}, e_pending: bool}."""
    matched = []
    reasons = {}
    blind = []
    ma, ra, bla = check_A(rows, target_date)
    reasons["A"] = ra
    if ma: matched.append("A")
    if bla: blind.append("A")
    mb, rb, blb = check_B(rows, target_date)
    reasons["B"] = rb
    if mb: matched.append("B")
    if blb: blind.append("B")
    mc, rc, blc = check_C(rows, target_date)
    reasons["C"] = rc
    if mc: matched.append("C")
    if blc: blind.append("C")
    md, rd, bld = check_D(rows, target_date, exch_bal=exch_bal)
    reasons["D"] = rd
    if md: matched.append("D")
    if bld: blind.append("D")
    me, re_, ble, e_pend = check_E(rows, target_date)
    reasons["E"] = re_ + (["E-pending"] if e_pend else [])
    if me: matched.append("E")
    if ble: blind.append("E")

    # Trim to 2 ĐẶC HIỆU NHẤT if ≥3 matched (C>D>B>A order · E is standalone spike-tag)
    trimmable = [t for t in matched if t in TAG_ORDER]
    if len(trimmable) >= 3:
        trimmable.sort(key=lambda t: TAG_ORDER[t])
        keep = set(trimmable[:2]) | ({"E"} if "E" in matched else set())
        final = sorted([t for t in matched if t in keep])
        audit_line = f"matched {'·'.join(matched)} → in [{'·'.join(final)}]"
    else:
        final = sorted(matched)
        audit_line = f"matched {'·'.join(matched) if matched else '-'} → in [{'·'.join(final) if final else '-'}]"

    # Zero-tag ∧ ≥1 loài có trục chính mù tại T → in [?]
    if not final and blind:
        display = "[?]"
    elif not final:
        display = ""
    else:
        display = "[" + "·".join(final) + "]"

    return {
        "tags": final,
        "matched_all": matched,
        "blind_axes": blind,
        "reasons": reasons,
        "e_pending": e_pend,
        "display": display + " draft" if final or display == "[?]" else "",
        "audit": audit_line,
    }
