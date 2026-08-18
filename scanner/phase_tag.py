"""
scanner/phase_tag.py — PHASE-TAG v0.3 stage classifier (SCREEN display layer)

Spec canonical: docs/proposals/phase_tag_spec_v0.3.md
Pure function: tag(days, i, cfg, case_state=None) -> row

Rules:
  · Precedence per §4 cây B1..B6 — dừng ở nhánh đầu khớp
  · Suppressor đè bullish (fix L-19)
  · B2.5 gọi C1 canonical stealth_grind() — KHÔNG re-implement số
  · B2h harvest_drop() = LOCAL helper (§9.1.3, §7 #7) — window 14d stateless,
    KHÔNG gọi chain helper
  · B4 S1 SKIP sạch (D3 feed chưa sống)
  · LSR null → UNKNOWN(DATA) nổ mặt (spec §5, L-49-draft)
  · Display-only, KHÔNG sửa state machine, KHÔNG suppress
"""
from __future__ import annotations

import math
import sys
from pathlib import Path
from statistics import median
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent))
from signals import (
    DayData,
    stealth_grind, hedge_structure, funding_pinned, funding_pinned_strong,
    absorption, crowd_flush, dist_wall, lsr_dist, decay, post_climax,
    funding_neg_div,
)


# ═════════════════════════════════════════════════════════════════════════════
# LOCAL helpers (§9.1.3 — stateless, không đụng chain)
# ═════════════════════════════════════════════════════════════════════════════

def _val(days: list, i: int, field: str) -> float:
    """Get field with fallback aliases (lsr_pos_r ↔ lsr_pos, etc.)."""
    d = days[i]
    v = d.get(field)
    if v is not None and not (isinstance(v, float) and math.isnan(v)):
        return v
    # Aliases: spec §2 uses _r suffix, signals.py uses bare
    alias = {
        "lsr_pos_r": "lsr_pos",   "lsr_pos": "lsr_pos_r",
        "lsr_acc_r": "lsr_acc",   "lsr_acc": "lsr_acc_r",
        "lsr_global_r": "lsr_global", "lsr_global": "lsr_global_r",
    }
    if field in alias:
        v2 = d.get(alias[field])
        if v2 is not None and not (isinstance(v2, float) and math.isnan(v2)):
            return v2
    return float("nan")


def _window(days: list, end_i: int, days_n: int, field: str) -> list:
    """Values of field for last days_n ending at end_i (inclusive)."""
    start = max(0, end_i - days_n + 1)
    return [_val(days, j, field) for j in range(start, end_i + 1)
            if not math.isnan(_val(days, j, field))]


def _rolling_peak14(days: list, i: int, field: str = "lsr_pos") -> float:
    """Rolling max last 14d ending at i. NaN nếu không đủ data."""
    vals = _window(days, i, 14, field)
    return max(vals) if vals else float("nan")


def harvest_drop(days: list, i: int, mag: float = 0.25) -> bool:
    """B2h LOCAL helper (spec §9.1.3, §7 #7).

    pos_r drop ≥ mag (pointer rule-iv, hiện 25%) từ rolling_peak14.
    Window 14d LOCAL — stateless. KHÔNG gọi rule-iv chain helper.
    """
    peak = _rolling_peak14(days, i, field="lsr_pos")
    cur  = _val(days, i, "lsr_pos")
    if math.isnan(peak) or math.isnan(cur) or peak <= 0:
        return False
    drop = (peak - cur) / peak
    return drop >= mag


# ═════════════════════════════════════════════════════════════════════════════
# B2 MARKUP conditions
# ═════════════════════════════════════════════════════════════════════════════

def _breakout_15pct_5d(days: list, i: int) -> bool:
    """price max last 5d ≥ 1.15 × range14d high (range end i-5)."""
    if i < 5:
        return False
    range_end = i - 5
    range_px = _window(days, range_end, 14, "avg_px")
    if len(range_px) < 7:
        return False
    range_hi = max(range_px)
    if range_hi <= 0:
        return False
    target = range_hi * 1.15
    window_px = _window(days, i, 5, "avg_px")
    return any(p >= target for p in window_px)


def _oi_15x_med14(days: list, i: int) -> bool:
    """OI ≥ 1.5× med14 in last 5d window."""
    if i < 5:
        return False
    med_end = i - 5
    med_vals = _window(days, med_end, 14, "oi_usd")
    med_vals = [v for v in med_vals if v > 0]
    if not med_vals:
        return False
    med_oi = median(med_vals)
    oi_window = [v for v in _window(days, i, 5, "oi_usd") if v > 0]
    return any(v >= 1.5 * med_oi for v in oi_window)


def _markup_condition(days: list, i: int) -> bool:
    return _breakout_15pct_5d(days, i) and _oi_15x_med14(days, i)


def _taker_max_5d(days: list, i: int) -> float:
    tb = _window(days, i, 5, "taker_buy_pct")
    return max(tb) if tb else float("nan")


# ═════════════════════════════════════════════════════════════════════════════
# B3 TEXTURE S2 conditions
# ═════════════════════════════════════════════════════════════════════════════

def _div_avg3(days: list, i: int) -> float:
    """Rolling avg of div_avg3 over 3d — spec canonical div."""
    vals = _window(days, i, 3, "div_avg3")
    if not vals:
        # Fallback: compute from lsr_pos / lsr_acc
        div_vals = []
        for j in range(max(0, i-2), i+1):
            p = _val(days, j, "lsr_pos"); a = _val(days, j, "lsr_acc")
            if not math.isnan(p) and not math.isnan(a) and a > 0:
                div_vals.append(p / a)
        if not div_vals:
            return float("nan")
        return sum(div_vals) / len(div_vals)
    return sum(vals) / len(vals)


def _avg5_glsr(days: list, i: int) -> float:
    vals = _window(days, i, 5, "lsr_global")
    return sum(vals) / len(vals) if vals else float("nan")


def _hedge_bền_7d(days: list, i: int, cfg: dict) -> bool:
    """hedge_structure bền ≥ 7d liên tiếp (div ≤ 0.5)."""
    if i < 6:
        return False
    for j in range(i - 6, i + 1):
        if not hedge_structure(days, j, cfg):
            return False
    return True


def _d_pos_3d(days: list, i: int) -> float:
    if i < 3:
        return float("nan")
    p_now = _val(days, i, "lsr_pos")
    p_prev = _val(days, i - 3, "lsr_pos")
    if math.isnan(p_now) or math.isnan(p_prev):
        return float("nan")
    return p_now - p_prev


def _div_raw(days: list, i: int) -> float:
    p = _val(days, i, "lsr_pos"); a = _val(days, i, "lsr_acc")
    if math.isnan(p) or math.isnan(a) or a <= 0:
        return float("nan")
    return p / a


# ═════════════════════════════════════════════════════════════════════════════
# B5 S0 conditions
# ═════════════════════════════════════════════════════════════════════════════

def _oi_at_min30d(days: list, i: int, mult: float = 1.1) -> bool:
    """oi ≤ mult × min30d."""
    oi_vals = _window(days, i, 30, "oi_usd")
    oi_vals = [v for v in oi_vals if v > 0]
    if not oi_vals:
        return False
    cur = _val(days, i, "oi_usd")
    if math.isnan(cur):
        return False
    return cur <= mult * min(oi_vals)


def _vol_dry_med7_vs_med30(days: list, i: int, mult: float = 0.5) -> bool:
    v7 = _window(days, i, 7, "vol_quote")
    v30 = _window(days, i, 30, "vol_quote")
    v7 = [v for v in v7 if v > 0]; v30 = [v for v in v30 if v > 0]
    if not v7 or not v30:
        return False
    return median(v7) <= mult * median(v30)


def _glsr_range_neutral(days: list, i: int, lo=0.8, hi=1.3) -> bool:
    g = _val(days, i, "lsr_global")
    if math.isnan(g):
        return False
    return lo <= g <= hi


def _crowd_flush_recent(days: list, i: int, cfg: dict, lookback: int = 7) -> bool:
    """Any crowd_flush in last `lookback` days?"""
    for j in range(max(0, i - lookback + 1), i + 1):
        if crowd_flush(days, j, cfg):
            return True
    return False


def _glsr_drop_from_peak14(days: list, i: int, min_drop: float = 0.40) -> bool:
    """gLSR −≥ min_drop from peak in last 14d ending at i."""
    peak = _rolling_peak14(days, i, field="lsr_global")
    cur  = _val(days, i, "lsr_global")
    if math.isnan(peak) or math.isnan(cur) or peak <= 0:
        return False
    return (peak - cur) / peak >= min_drop


def _herd_return(days: list, i: int, threshold: float = 0.80,
                 window: int = 14) -> Optional[bool]:
    """herd_return: gLSR rolling 14d back to ≥ threshold × pre-flush peak.

    Returns None if no flush event found (can't compute)."""
    # Find peak before this window
    peak_start = max(0, i - window - 14)
    peak_vals = [_val(days, j, "lsr_global") for j in range(peak_start, max(0, i - window))]
    peak_vals = [v for v in peak_vals if not math.isnan(v) and v > 0]
    if not peak_vals:
        return None
    peak = max(peak_vals)
    cur = _val(days, i, "lsr_global")
    if math.isnan(cur) or peak <= 0:
        return None
    return cur >= threshold * peak


# ═════════════════════════════════════════════════════════════════════════════
# §3 Event tagger (chạy TRƯỚC cây)
# ═════════════════════════════════════════════════════════════════════════════

def _glsr_pct_change(days: list, i: int, lookback: int) -> float:
    """(now - past) / past for lsr_global. Positive = growth."""
    if i < lookback:
        return float("nan")
    now = _val(days, i, "lsr_global")
    past = _val(days, i - lookback, "lsr_global")
    if math.isnan(now) or math.isnan(past) or past <= 0:
        return float("nan")
    return (now - past) / past


def _glsr_slope_5d(days: list, i: int) -> float:
    """Slope proxy: end/start ratio over 5d."""
    if i < 5:
        return float("nan")
    now = _val(days, i, "lsr_global")
    past = _val(days, i - 5, "lsr_global")
    if math.isnan(now) or math.isnan(past) or past <= 0:
        return float("nan")
    return now / past


def _px_change(days: list, i: int, lookback: int) -> float:
    if i < lookback:
        return float("nan")
    now = _val(days, i, "avg_px")
    past = _val(days, i - lookback, "avg_px")
    if math.isnan(now) or math.isnan(past) or past <= 0:
        return float("nan")
    return (now - past) / past


def _vol_vs_med14(days: list, i: int) -> float:
    """vol / med14(vol). NaN if no baseline."""
    if i < 14:
        return float("nan")
    med_vals = _window(days, i - 1, 14, "vol_quote")
    med_vals = [v for v in med_vals if v > 0]
    if not med_vals:
        return float("nan")
    cur = _val(days, i, "vol_quote")
    if math.isnan(cur):
        return float("nan")
    return cur / median(med_vals)


def event_tag(days: list, i: int) -> Optional[str]:
    """Return event tag string or None. Precedence: PHASE-BREAK handled by caller."""
    px_1d  = _px_change(days, i, 1)
    px_5d  = _px_change(days, i, 5)  # for BAIT rejection lookback
    glsr_drop_3d = -1 * _glsr_pct_change(days, i, 3)  # positive = drop
    glsr_growth_3d = _glsr_pct_change(days, i, 3)
    vol_mult = _vol_vs_med14(days, i)
    slope5 = _glsr_slope_5d(days, i)

    # WRONG-SIDE: giá sập + gLSR TĂNG
    if not math.isnan(px_1d) and px_1d <= -0.05:
        if not math.isnan(glsr_growth_3d) and glsr_growth_3d >= 0.10:
            return "WRONG-SIDE"

    # WASH-CRASH: giá −15%+ ∧ gLSR −≥30%/≤3d
    if not math.isnan(px_1d) and px_1d <= -0.15:
        if not math.isnan(glsr_drop_3d) and glsr_drop_3d >= 0.30:
            return "WASH-CRASH"

    # WASH-RALLY: giá +8%+ ∧ gLSR −≥30%/≤3d
    if not math.isnan(px_1d) and px_1d >= 0.08:
        if not math.isnan(glsr_drop_3d) and glsr_drop_3d >= 0.30:
            return "WASH-RALLY"

    # CROWD-CHASE: giá +8%+ ∧ (slope5 >1.15 ∨ gLSR +≥30%/3d)
    if not math.isnan(px_1d) and px_1d >= 0.08:
        chase_cond = (not math.isnan(slope5) and slope5 > 1.15) or \
                     (not math.isnan(glsr_growth_3d) and glsr_growth_3d >= 0.30)
        if chase_cond:
            return "CROWD-CHASE"

    # TEST-BAIT: vol ≥8× med14 + giá bị từ chối ≤2d + gLSR −≥30%/≤3d
    if not math.isnan(vol_mult) and vol_mult >= 8.0:
        # rejection: px_1d bounces down after spike (proxy: current 2d avg lower than spike day)
        # Simplified: check if current px reverted from 1-2d spike
        if i >= 2:
            px_now = _val(days, i, "avg_px")
            px_2d_ago = _val(days, i-2, "avg_px")
            rejected = not math.isnan(px_now) and not math.isnan(px_2d_ago) and \
                       px_now <= px_2d_ago * 1.02  # neutral or below
            if rejected and not math.isnan(glsr_drop_3d) and glsr_drop_3d >= 0.30:
                return "TEST-BAIT"

    return None


# ═════════════════════════════════════════════════════════════════════════════
# MAIN — tag(days, i, cfg, case_state) -> row
# ═════════════════════════════════════════════════════════════════════════════

STAGE_ORDER = ["S0", "S0-POSTFLUSH", "S1", "S2-EARLY", "S2-MID", "S2-LATE",
               "S3-TAKER", "S3-BIDWALK", "S3-GRIND", "S3-HARVEST", "S4", "S5",
               "UNKNOWN"]


def tag(days: list, i: int, cfg: dict, case_state: Optional[dict] = None) -> dict:
    """Classify day i into stage per §4 tree. Return row dict.

    Args:
        days: list[DayData] sorted chronologically
        i: current day index (closed candle)
        cfg: thresholds dict (signals.py cfg + screen_thresholds.yaml)
        case_state: {"state": str, "ngay_ky": str, "verdict_ref": str} or None

    Returns:
        {stage, stage_conf, stage_evidence, stage_flags, event_tag,
         wash_count_30d, herd_return, case_state, state_conflict, ...}
    """
    d = days[i]
    date_str = d.get("date", "??")
    evidence = []
    flags = []

    # ── Guards §5 ──────────────────────────────────────────────────────────
    lsr_pos = _val(days, i, "lsr_pos")
    lsr_acc = _val(days, i, "lsr_acc")
    lsr_glo = _val(days, i, "lsr_global")

    if math.isnan(lsr_pos) or math.isnan(lsr_acc) or math.isnan(lsr_glo):
        return {"date": date_str, "stage": "UNKNOWN(DATA)", "stage_conf": "LOW",
                "stage_evidence": "LSR null — L-49-draft nổ mặt",
                "stage_flags": ["LSR-NULL"], "event_tag": None,
                "wash_count_30d": None, "herd_return": None,
                "case_state": case_state["state"] if case_state else None,
                "state_conflict": False}

    if i < 14:
        return {"date": date_str, "stage": "UNKNOWN", "stage_conf": "LOW",
                "stage_evidence": "symbol <14d",
                "stage_flags": ["YOUNG"], "event_tag": None,
                "wash_count_30d": None, "herd_return": None,
                "case_state": case_state["state"] if case_state else None,
                "state_conflict": False}

    vol_q = _val(days, i, "vol_quote")
    oi    = _val(days, i, "oi_usd")
    if (not math.isnan(vol_q) and vol_q < 200_000) or (not math.isnan(oi) and oi < 1_000_000):
        flags.append("low_conf")

    fn = d.get("funding_n", 6)
    if fn is not None and fn < 6:
        flags.append("SUSPECT")

    # ── Event tagger §3 (chạy TRƯỚC cây) ───────────────────────────────────
    ev = event_tag(days, i)

    # ══════════════════════════════════════════════════════════════════════
    # §4 CÂY B1..B6 — precedence, dừng ở nhánh đầu
    # ══════════════════════════════════════════════════════════════════════

    stage = None
    conf = "MED"

    # B1. SUPPRESSOR ─────────────────────────────────────────────────────────
    dw = dist_wall(days, i, cfg)
    ld = lsr_dist(days, i, cfg)
    pc = post_climax(days, i, cfg)
    dc = decay(days, i, cfg)
    fnd = funding_neg_div(days, i, cfg)

    if dw or ld:
        stage = "S4"
        evidence.append(f"suppressor: dist_wall={dw} lsr_dist={ld}")
        conf = "HIGH"
    elif pc or dc or fnd:
        stage = "S5"
        parts = []
        if fnd: parts.append("funding_neg_div")
        if pc:  parts.append("post_climax")
        if dc:  parts.append("decay")
        evidence.append(f"suppressor: {'+'.join(parts)}")
        conf = "HIGH"

    # B2. MARKUP ─────────────────────────────────────────────────────────────
    if stage is None and _markup_condition(days, i):
        # B2h harvest_drop (thắng trong markup)
        if harvest_drop(days, i):
            stage = "S3-HARVEST"
            peak = _rolling_peak14(days, i, "lsr_pos")
            cur = _val(days, i, "lsr_pos")
            drop = (peak - cur) / peak if peak > 0 else 0
            evidence.append(f"harvest: pos_r {cur:.2f} vs peak14 {peak:.2f} drop {drop:.0%}")
            evidence.append("[two-legged-kho: harvest=CHUYỂN PHA, campaign chưa chắc hết (kho spot quyết)]")
            conf = "HIGH"
        else:
            tb_max = _taker_max_5d(days, i)
            if not math.isnan(tb_max) and tb_max >= 55.0:
                stage = "S3-TAKER"
                evidence.append(f"markup + taker max5d={tb_max:.1f}%")
                conf = "HIGH"
            else:
                stage = "S3-BIDWALK"
                evidence.append(f"markup + taker max5d={tb_max:.1f}% <55%")
                conf = "HIGH"

    # B2.5 GRIND (chỉ khi chưa vào B2 markup)
    if stage is None:
        try:
            if stealth_grind(days, i, cfg):
                # B2h chồng: harvest thắng
                if harvest_drop(days, i):
                    stage = "S3-HARVEST"
                    evidence.append("grind+harvest → harvest wins")
                    conf = "HIGH"
                else:
                    stage = "S3-GRIND"
                    evidence.append("C1 stealth_grind fires")
                    conf = "MED"
        except Exception:
            pass

    # B3. TEXTURE S2 (không markup ∧ oi_cycle_pos ≤ 0.5)
    if stage is None:
        oi_cp = _val(days, i, "oi_cycle_pos")
        oi_cp_ok = math.isnan(oi_cp) or oi_cp <= 0.5   # NaN = permissive per spec convention

        if oi_cp_ok:
            div = _div_avg3(days, i)
            avg5_g = _avg5_glsr(days, i)

            # S2-LATE
            if not math.isnan(div) and div >= 1.5 and \
               not math.isnan(avg5_g) and avg5_g <= 1.1:
                stage = "S2-LATE"
                evidence.append(f"div_avg3={div:.2f}≥1.5 avg5(gLSR)={avg5_g:.2f}≤1.1")
                conf = "HIGH"

            # S2-EARLY
            elif _hedge_bền_7d(days, i, cfg) and \
                 (funding_pinned(days, i, cfg) or absorption(days, i, cfg)):
                stage = "S2-EARLY"
                evidence.append("hedge_structure bền ≥7d + (pinned|absorption)")
                conf = "HIGH"

            # S2-MID
            elif (funding_pinned(days, i, cfg) or absorption(days, i, cfg)) and \
                 not math.isnan(div) and 0.5 < div < 1.5:
                stage = "S2-MID"
                evidence.append(f"div_avg3={div:.2f} ∈ (0.5,1.5) + (pinned|absorption)")
                conf = "MED"
                # Sub S2-MID↑
                d_pos = _d_pos_3d(days, i)
                d_raw = _div_raw(days, i)
                if not math.isnan(d_pos) and d_pos > 0 and \
                   not math.isnan(d_raw) and d_raw >= 1.5:
                    stage = "S2-MID↑"
                    evidence.append(f"[sub-up] d_pos_3d={d_pos:+.2f}>0 div_raw={d_raw:.2f}≥1.5 [raw=cảnh-báo-sớm]")

    # B4. S1 — SKIP sạch (§9.1 D3 chưa sống)
    # KHÔNG proxy per spec §4 B4

    # B5. S0
    if stage is None:
        # B5.b S0-POSTFLUSH
        if _crowd_flush_recent(days, i, cfg, lookback=7) and \
           _glsr_drop_from_peak14(days, i, min_drop=0.40):
            hr = _herd_return(days, i, threshold=0.80, window=14)
            if hr is not True:
                stage = "S0-POSTFLUSH"
                evidence.append("crowd_flush ≤7d + gLSR −≥40%/peak14 + herd_return≠TRUE")
                conf = "HIGH"

        # B5.a S0
        if stage is None and _oi_at_min30d(days, i) and \
           _vol_dry_med7_vs_med30(days, i) and _glsr_range_neutral(days, i):
            stage = "S0"
            evidence.append("oi≤1.1×min30 + vol dried + gLSR∈[0.8,1.3]")
            conf = "MED"

    # B6. UNKNOWN + FUEL-STANDING flag
    if stage is None:
        stage = "UNKNOWN"
        conf = "LOW"
        # FUEL-STANDING: avg30(gLSR) ≤0.90 ∧ không texture S2
        g_vals = _window(days, i, 30, "lsr_global")
        if g_vals and sum(g_vals) / len(g_vals) <= 0.90:
            flags.append("FUEL-STANDING")

    # ── Sub-annotations S2 ─────────────────────────────────────────────────
    if stage and stage.startswith("S2"):
        # RIPE: wash_count_30d ≥ 2 ∧ herd_return=FALSE
        # (Simplified: skip wash_count for now, requires historical event log)
        # CAPTIVE?: div<1 ∧ funding âm/pin ∧ OI-kệ lớn
        div_r = _div_raw(days, i)
        if not math.isnan(div_r) and div_r < 1.0:
            fund_avg = _val(days, i, "funding_avg")
            if not math.isnan(fund_avg) and fund_avg < 0:
                flags.append("CAPTIVE?")

    # ── §6.3 STATE-CONFLICT ────────────────────────────────────────────────
    state_conflict = False
    if case_state and stage:
        state_str = str(case_state.get("state", "")).upper()
        distribution_states = ["DISTRIBUTION", "SUPPRESSED", "COLLAPSED", "STAND_ASIDE"]
        is_dist = any(s in state_str for s in distribution_states)
        is_bullish_stage = stage.startswith("S2") or stage.startswith("S3")
        if is_dist and is_bullish_stage:
            state_conflict = True
            flags.append("STATE-CONFLICT")

    # ── OWNERSHIP-UNVERIFIED (§1 non-goal) ─────────────────────────────────
    if stage and (stage.startswith("S1") or stage.startswith("S2")):
        flags.append("OWNERSHIP-UNVERIFIED")

    return {
        "date":            date_str,
        "stage":           stage,
        "stage_conf":      conf,
        "stage_evidence":  " · ".join(evidence) if evidence else "",
        "stage_flags":     flags,
        "event_tag":       ev,
        "wash_count_30d":  None,   # TODO: requires historical event log
        "herd_return":     None,   # TODO: needs previous flush anchor
        "case_state":      case_state["state"] if case_state else None,
        "state_conflict":  state_conflict,
    }
