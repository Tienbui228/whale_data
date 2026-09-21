# HOLD-OUT 20/09→20/10: audit-only. Cấm dùng làm input cho bất kỳ
#  quyết định ngưỡng nào trước 21/10. Grid 8 ô đã khoá.
"""B State Tracker · M1-M3/19-09 · AO1/22-09 · L1 THAY check_B · relapse BỎ.

M0(a)=1 đã ký: L1 (fb30dd88 §3 · A2.1 · Δacc ≤ -15% ∧ |Δpos| ≤ 10% trên W3
{D-1, D+2}) THAY check_B làm cổng vào tầng B. AO1/22-09: đổi từ -30/5 (M commit
đặt sai, không có nguồn ký) → -15/10 (ký) · ERRATA_AO. check_B/v_run/v_ratio
là cấu hình CŨ, KHÔNG chồng lên A3.

Đọc trạng thái từ:
  · freshwatch_daily (px, LSR, OI) để chấm cross_today + L1 + U1 D+5 + STALE
  · KHÔNG cần jsonl bell

Trả state per token · tier ∈ {CONFIRMED · CROSS · cand · FAILED · STALE}:
  · CONFIRMED = L1(D_cross) ∧ U1 v2∧v1 pass tại D+5 ∧ (T − D_cross) ≤ 30d
  · CROSS     = cross_today (D+k ≤ 5) ∧ L1(D_cross)
  · cand      = div_avg3(T) ≤ 0.5 (đang hedge) · khớp cổng U0-BELL
  · FAILED    = L1(D_cross) ∧ D+k > 5 ∧ U1 fail
  · STALE     = L1(D_cross) ∧ U1 pass ∧ D+k > 30d ∧ không nến ≥+20% trong 30d

L2/L3 (không đạt L1 tại D_cross) → KHÔNG vào tầng B · append audit:
  data/logs/b_l2_l3_reject.jsonl per token · KHÔNG hiển thị trong render.
"""
from __future__ import annotations
import os, sys, csv, math, json
from pathlib import Path
from datetime import datetime, timezone, timedelta

_SCRIPTS = Path(__file__).parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from species_tag import _div_avg3
from u0_bell import delta_bwd

REPO = Path("/root/Data_back_test/whale_data") if os.name != "nt" else Path(r"D:/Data back test/whale_data")
FW_PATH = REPO / "data/config/freshwatch_symbols.txt"
L2L3_AUDIT = REPO / "data/logs/b_l2_l3_reject.jsonl"

# U0-CLASS L1 threshold · fb30dd88 §3 A2.1 · Δacc ≤ -15% ∧ |Δpos| ≤ 10% trên W3.
# AO1/22-09: sửa từ -30/5 (M commit đặt sai) → -15/10 (nguồn ký). ERRATA_AO.
L1_DACC_MAX = -0.15
L1_DPOS_MAX_ABS = 0.10

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
    """Trả D_cross ĐẦU của episode gần T nhất (WL-EPISODE gap ≥ episode_gap)."""
    td = datetime.strptime(target, "%Y-%m-%d").date()
    crosses = []
    for k in range(0, lookback):
        d = (td - timedelta(days=k)).isoformat()
        d_prev = (td - timedelta(days=k+1)).isoformat()
        v = _div_avg3(rows, d)
        vp = _div_avg3(rows, d_prev)
        if v is not None and vp is not None and vp <= 0.5 and v > 0.5:
            crosses.append(d)
    if not crosses: return None
    crosses.reverse()
    episodes = [[crosses[0]]]
    for c in crosses[1:]:
        prev = datetime.strptime(episodes[-1][-1], "%Y-%m-%d").date()
        cur = datetime.strptime(c, "%Y-%m-%d").date()
        if (cur - prev).days >= episode_gap:
            episodes.append([c])
        else:
            episodes[-1].append(c)
    return episodes[-1][0]


def _check_u0_class_L1(rows, d_cross):
    """L1 threshold · Δacc ≤ -15% ∧ |Δpos| ≤ 10% (fb30dd88 §3 A2.1 · W3 {D-1, D+2}).
    Trả (is_L1, dacc, dpos). None nếu blind."""
    dacc, _, _ = delta_bwd(rows, d_cross, "lsr_acc_r")
    dpos, _, _ = delta_bwd(rows, d_cross, "lsr_pos_r")
    if dacc is None or dpos is None:
        return (False, dacc, dpos)
    return (dacc <= L1_DACC_MAX and abs(dpos) <= L1_DPOS_MAX_ABS, dacc, dpos)


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
    td = datetime.strptime(target, "%Y-%m-%d").date()
    best = (None, None)
    for k in range(0, 5):
        d = (td - timedelta(days=k)).isoformat()
        v = _div_avg3(rows, d)
        if v is not None and (best[1] is None or v < best[1]):
            best = (d, v)
    return best


def _audit_l2_l3(token, target, d_cross, dacc, dpos, u1_ratios, reason):
    """Append audit reject cho L2/L3 (không đạt L1) · KHÔNG vào tầng B."""
    L2L3_AUDIT.parent.mkdir(parents=True, exist_ok=True)
    with L2L3_AUDIT.open("a", encoding="utf-8") as f:
        f.write(json.dumps({
            "target": target, "token": token, "d_cross": d_cross,
            "dacc_bwd": dacc, "dpos_bwd": dpos,
            "u1_v1": u1_ratios.get("v1") if u1_ratios else None,
            "u1_v2": u1_ratios.get("v2") if u1_ratios else None,
            "reason": reason,
            "computed_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }, ensure_ascii=False) + "\n")


def build_b_state(target, universe=None, by_sym=None,
                   failed_display_window: int = 14):
    """Trả dict {token: {tier, ...}} cho khối B · M1-M3/19-09.

    M1: CONFIRMED := L1 ∧ U1(v2∧v1) ∧ (T − D_cross) ≤30d
    M2: BỎ relapse tag · BỎ mọi tham chiếu v_run
    M3: cand = div_avg3(T) ≤ 0.5 · L1/L2/L3 gate tại D_cross (KHÔNG check_B)

    L2/L3 (không đạt L1) → append audit `b_l2_l3_reject.jsonl` · KHÔNG vào tầng B.
    """
    if universe is None: universe = _load_universe()
    if by_sym is None: by_sym = _load_fw_rows(target)
    td = datetime.strptime(target, "%Y-%m-%d").date()

    result = {}
    for tok in universe:
        rows = by_sym.get(tok, [])
        if not rows: continue

        d_cross = _find_latest_cross(rows, target)
        div_T = _div_avg3(rows, target)

        # No D_cross recent · chỉ cand nếu đang hedge tại T
        if d_cross is None:
            if div_T is not None and div_T <= 0.5:
                _, div_min = _div_min_5d(rows, target)
                result[tok] = {"tier": "cand", "div_min_5d": div_min}
            continue

        dc = datetime.strptime(d_cross, "%Y-%m-%d").date()
        d_plus_k = (td - dc).days

        # M3 · L1 gate tại D_cross (THAY check_B)
        is_L1, dacc, dpos = _check_u0_class_L1(rows, d_cross)

        # T2 CROSS: D+k ≤ 5 AND L1
        if d_plus_k <= CROSS_D_PLUS_MAX:
            if is_L1:
                result[tok] = {"tier": "CROSS", "d_cross": d_cross, "d_plus_k": d_plus_k}
            else:
                # L2/L3 tại D_cross ≤5d → chưa audit reject (chưa qua U1) · nếu hedge → cand
                if div_T is not None and div_T <= 0.5:
                    _, div_min = _div_min_5d(rows, target)
                    result[tok] = {"tier": "cand", "div_min_5d": div_min}
            continue

        # D+k > 5 → chấm U1 v2∧v1
        u1_pass, ratios = _check_u1_v2v1(rows, d_cross)

        # M1 · L2/L3 (không L1) → KHÔNG BAO GIỜ CONFIRMED · audit reject
        if not is_L1:
            reason = ("L2_or_L3_dacc={:.3f}_dpos={:.3f}_u1={}".format(
                dacc if dacc is not None else float('nan'),
                dpos if dpos is not None else float('nan'),
                'pass' if u1_pass else 'fail'))
            _audit_l2_l3(tok, target, d_cross, dacc, dpos, ratios, reason)
            continue

        # L1 pass · chấm U1
        if u1_pass:
            if d_plus_k > CONFIRM_TTL_DAYS:
                has_nen = _has_candle_up_pct(rows, target, 30, STALE_NEN_PCT)
                if not has_nen:
                    result[tok] = {"tier": "STALE", "d_cross": d_cross, "d_plus_k": d_plus_k}
                    continue
            result[tok] = {"tier": "CONFIRMED", "d_cross": d_cross, "d_plus_k": d_plus_k, "u1_ratios": ratios}
        else:
            result[tok] = {"tier": "FAILED", "d_cross": d_cross, "d_plus_k": d_plus_k, "u1_ratios": ratios}

    # FAILED display cutoff · chỉ giữ FAILED có D_cross trong ≤N days
    result_filtered = {}
    for tok, state in result.items():
        if state["tier"] == "FAILED":
            if state.get("d_plus_k") is not None and state["d_plus_k"] > failed_display_window:
                continue
        result_filtered[tok] = state
    return result_filtered
