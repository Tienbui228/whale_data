# HOLD-OUT 20/09→20/10: audit-only. Cấm dùng làm input cho bất kỳ
#  quyết định ngưỡng nào trước 21/10. Grid 8 ô đã khoá.
"""B State Tracker · AE1-1 · state cho khối B ba tầng · KHÔNG hardcode.

Đọc trạng thái từ:
  · freshwatch_daily (px, LSR, OI) để chấm cross_today + U1 D+5 + STALE
  · KHÔNG cần jsonl bell (dùng cross detection trực tiếp từ div_avg3)

Trả state per token · tier ∈ {CONFIRMED · CROSS · cand · FAILED · STALE}:
  · CONFIRMED = U1 v2∧v1 pass tại D+5 · còn hiệu lực (≤30d ∨ nến ≥+20% trong 30d)
  · CROSS     = cross_today ∧ U0-CLASS L1 ∧ D+k ≤ 5
  · cand      = div_avg3 ≤ 0.5 tại T · chưa cross gần đây
  · FAILED    = đã cross · qua D+5 · U1 v2∧v1 fail
  · STALE     = D_cross quá 30d không nến ≥+20%
"""
from __future__ import annotations
import os, sys, csv, math
from pathlib import Path
from datetime import datetime, timedelta

_SCRIPTS = Path(__file__).parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from species_tag import _div_avg3, check_B
from u0_bell import delta_bwd

REPO = Path("/root/Data_back_test/whale_data") if os.name != "nt" else Path(r"D:/Data back test/whale_data")
FW_PATH = REPO / "data/config/freshwatch_symbols.txt"

# U0-CLASS L1 threshold (AE1 spec)
L1_DACC_MAX = -0.30
L1_DPOS_MAX_ABS = 0.05

# CONFIRMED / STALE
CONFIRM_TTL_DAYS = 30
STALE_NEN_PCT = 0.20   # nến ≥ +20%
CROSS_D_PLUS_MAX = 5   # D+k ≤ 5 → T2 CROSS
BELL_LOOKBACK = 45     # scan D_cross trong 45d back


def _flt(v):
    if v is None or v == "": return None
    try:
        f = float(v)
        if math.isnan(f): return None
        return f
    except (TypeError, ValueError):
        return None


def _get(rows, dt, field):
    for r in rows:
        if r["date"] == dt: return _flt(r.get(field))
    return None


def _load_fw_rows(target, back_days=90):
    """Load fw_daily · scope tháng có target và 2 tháng trước."""
    td = datetime.strptime(target, "%Y-%m-%d").date()
    months = set()
    for i in range(0, back_days + 60, 15):
        d = td - timedelta(days=i)
        months.add(f"{d.month:02d}")
    by_sym = {}
    for m in sorted(months):
        p = REPO / f"data/export/freshwatch_daily_2026-{m}.csv"
        if not p.exists(): continue
        with p.open(encoding="utf-8", newline="") as f:
            for r in csv.DictReader(f):
                sym = r["symbol"]
                bare = sym[:-4] if sym.endswith("USDT") else sym
                by_sym.setdefault(bare, []).append(r)
    return by_sym


def _load_universe():
    if not FW_PATH.exists(): return []
    return [l.strip()[:-4] if l.strip().endswith("USDT") else l.strip()
            for l in FW_PATH.read_text(encoding="utf-8").splitlines() if l.strip()]


def _find_latest_cross(rows, target, lookback=BELL_LOOKBACK, episode_gap=14):
    """AE4-3 · Trả D_cross ĐẦU của episode gần T nhất (WL-EPISODE gap ≥ episode_gap).

    Thay vì latest raw cross, dùng "earliest of episode" — khớp calibration.
    Cách:
      1. Scan mọi cross trong lookback backward.
      2. Group thành episodes (gap ≥ episode_gap ngày = episode mới).
      3. Trả cross ĐẦU của episode chứa T (episode gần T nhất).
    """
    td = datetime.strptime(target, "%Y-%m-%d").date()
    # Scan all crosses backward
    crosses = []
    for k in range(0, lookback):
        d = (td - timedelta(days=k)).isoformat()
        d_prev = (td - timedelta(days=k+1)).isoformat()
        v = _div_avg3(rows, d)
        vp = _div_avg3(rows, d_prev)
        if v is not None and vp is not None and vp <= 0.5 and v > 0.5:
            crosses.append(d)
    if not crosses: return None
    # crosses list is newest-first (backward scan) · reverse to oldest-first
    crosses.reverse()
    # Group episodes
    episodes = [[crosses[0]]]
    for c in crosses[1:]:
        prev = datetime.strptime(episodes[-1][-1], "%Y-%m-%d").date()
        cur = datetime.strptime(c, "%Y-%m-%d").date()
        if (cur - prev).days >= episode_gap:
            episodes.append([c])
        else:
            episodes[-1].append(c)
    # Return earliest of the LATEST episode (gần T nhất)
    return episodes[-1][0]


def _check_u0_class_L1(rows, d_cross):
    """L1 threshold tại D_cross: Δacc_bwd ≤ -30% ∧ |Δpos_bwd| ≤ 5%."""
    dacc, _, _ = delta_bwd(rows, d_cross, "lsr_acc_r")
    dpos, _, _ = delta_bwd(rows, d_cross, "lsr_pos_r")
    if dacc is None or dpos is None: return False
    return dacc <= L1_DACC_MAX and abs(dpos) <= L1_DPOS_MAX_ABS


def _check_u1_v2v1(rows, d_cross):
    """U1 v2∧v1 tại D+5. Trả (pass, ratios)."""
    dc = datetime.strptime(d_cross, "%Y-%m-%d").date()
    d_p5 = (dc + timedelta(days=5)).isoformat()
    d_m1 = (dc - timedelta(days=1)).isoformat()
    acc_p5 = _get(rows, d_p5, "lsr_acc_r"); acc_m1 = _get(rows, d_m1, "lsr_acc_r")
    oi_p5 = _get(rows, d_p5, "oi_usd"); oi_m1 = _get(rows, d_m1, "oi_usd")
    v1r = acc_p5 / acc_m1 if (acc_p5 is not None and acc_m1 not in (None, 0)) else None
    v2r = oi_p5 / oi_m1 if (oi_p5 is not None and oi_m1 not in (None, 0)) else None
    v1p = v1r is not None and v1r <= 0.6
    v2p = v2r is not None and v2r >= 1.5
    return (v1p and v2p, {"v1": v1r, "v2": v2r})


def _has_candle_up_pct(rows, target, back_days, pct):
    """Có nến D-1 → D nào ≥ pct trong back_days không?"""
    td = datetime.strptime(target, "%Y-%m-%d").date()
    for k in range(0, back_days):
        d = (td - timedelta(days=k)).isoformat()
        d_prev = (td - timedelta(days=k+1)).isoformat()
        px = _get(rows, d, "px_avg"); px_p = _get(rows, d_prev, "px_avg")
        if px is None or px_p is None or px_p <= 0: continue
        if (px - px_p) / px_p >= pct:
            return True
    return False


def _div_min_5d(rows, target):
    """Trả (date, div_min) trong 5d gần T."""
    td = datetime.strptime(target, "%Y-%m-%d").date()
    best = (None, None)
    for k in range(0, 5):
        d = (td - timedelta(days=k)).isoformat()
        v = _div_avg3(rows, d)
        if v is not None and (best[1] is None or v < best[1]):
            best = (d, v)
    return best


# AE5-1 · Proven-13 per PATTERN_BOOK v1.3 §2 · ca proven bị check_B rớt cổng
# → nhãn [relapse] · KHÔNG mất truy vết
PROVEN_13 = {"BTR","BULLA","UAI","AKE","HEMI","ON","BANK","TUT","CYS","PROM","BTW","CAP","龙虾"}


def build_b_state(target, universe=None, by_sym=None,
                   failed_display_window: int = 14):
    """Trả dict {token: {tier, ...}} cho khối B.

    AE2-1/AE3-1 · SPECIES-B FILTER:
      · CONFIRMED / CROSS / FAILED / STALE → check_B tại D_CROSS của token
      · cand → check_B tại HÔM NAY (nhóm này mới thật sự đang hedge)

    AE3-4 · FAILED display cutoff: chỉ giữ FAILED có D_cross trong
    ≤ `failed_display_window` days (default 14). Ca cũ hơn không hiển thị
    (vẫn append jsonl audit qua nguồn khác).
    """
    if universe is None: universe = _load_universe()
    if by_sym is None: by_sym = _load_fw_rows(target)
    td = datetime.strptime(target, "%Y-%m-%d").date()

    result = {}
    for tok in universe:
        rows = by_sym.get(tok, [])
        if not rows: continue

        d_cross = _find_latest_cross(rows, target)

        # AE3-1 · Species-B filter tại LAST HEDGE DAY (D_cross - 1) · hoặc tại T (cho cand)
        # Lý do: AT D_cross acc đã rớt (transition day) · v_ratio fail
        # D_cross - 1 là ngày cuối cùng còn hedge → check_B đọc structure đúng
        if d_cross:
            dc_d = datetime.strptime(d_cross, "%Y-%m-%d").date()
            gate_date = (dc_d - timedelta(days=1)).isoformat()
        else:
            gate_date = target
        b_matched, reasons, _b_blind = check_B(rows, gate_date)
        if not b_matched:
            # AE5-1 · Proven token rớt cổng → nhãn [relapse] · không mất truy vết
            if tok in PROVEN_13 and d_cross:
                # Xác định vế FAIL: v_run hay v_ratio
                reason_str = reasons[0] if reasons else ""
                fail_reason = ""
                if "gLSR_or_acc≥2=False" in reason_str:
                    fail_reason = "v_ratio FAIL"
                elif "div_run≤" in reason_str and "=False" in reason_str.split("div_run≤")[1]:
                    fail_reason = "v_run FAIL"
                else:
                    fail_reason = "check_B FAIL"
                dc_d2 = datetime.strptime(d_cross, "%Y-%m-%d").date()
                result[tok] = {"tier": "RELAPSE", "d_cross": d_cross,
                               "fail_reason": fail_reason,
                               "dd_mm": f"{dc_d2.day:02d}/{dc_d2.month:02d}"}
            continue   # Không B tại gate_date → (RELAPSE nếu proven) · không vào T1/T2/T3

        if d_cross is None:
            # Không cross gần đây · xem đang hedge không → cand
            div_T = _div_avg3(rows, target)
            if div_T is not None and div_T <= 0.5:
                _, div_min = _div_min_5d(rows, target)
                result[tok] = {"tier": "cand", "div_min_5d": div_min}
            continue

        # Có D_cross gần đây
        dc = datetime.strptime(d_cross, "%Y-%m-%d").date()
        d_plus_k = (td - dc).days

        # T2 CROSS: D+k ≤ 5 AND U0-CLASS L1
        if d_plus_k <= CROSS_D_PLUS_MAX:
            is_L1 = _check_u0_class_L1(rows, d_cross)
            if is_L1:
                result[tok] = {"tier": "CROSS", "d_cross": d_cross, "d_plus_k": d_plus_k}
                continue
            # KHÔNG L1 → vẫn cand (không lên T2)
            div_T = _div_avg3(rows, target)
            if div_T is not None and div_T <= 0.5:
                _, div_min = _div_min_5d(rows, target)
                result[tok] = {"tier": "cand", "div_min_5d": div_min}
            continue

        # D+k > 5 → chấm U1 v2∧v1
        u1_pass, ratios = _check_u1_v2v1(rows, d_cross)

        if u1_pass:
            # STALE check: nếu D+k > 30d và không nến ≥+20% trong 30d → STALE
            if d_plus_k > CONFIRM_TTL_DAYS:
                has_nen = _has_candle_up_pct(rows, target, 30, STALE_NEN_PCT)
                if not has_nen:
                    result[tok] = {"tier": "STALE", "d_cross": d_cross, "d_plus_k": d_plus_k}
                    continue
            result[tok] = {"tier": "CONFIRMED", "d_cross": d_cross, "d_plus_k": d_plus_k, "u1_ratios": ratios}
        else:
            result[tok] = {"tier": "FAILED", "d_cross": d_cross, "d_plus_k": d_plus_k, "u1_ratios": ratios}

    # AE3-4 · FAILED display cutoff · chỉ giữ FAILED với D_cross trong ≤N days
    # (Không xoá khỏi jsonl audit qua nguồn khác; chỉ ẩn khỏi khối render)
    result_filtered = {}
    for tok, state in result.items():
        if state["tier"] == "FAILED":
            if state.get("d_plus_k") is not None and state["d_plus_k"] > failed_display_window:
                continue   # cũ hơn window → không hiển thị
        result_filtered[tok] = state
    return result_filtered
