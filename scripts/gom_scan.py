#!/usr/bin/env python3
"""gom_scan.py — GOM accumulation screen (gom_detect_spec.md v1.3)

Modes:
  --backfill  : run on 12 calibration case files (backtest §6)
  --daily     : run on latest day from daily store CSV

Outputs report to stdout + appends/updates data/gom_state.json.

Usage:
  python scripts/gom_scan.py --backfill [--token BANK]
  python scripts/gom_scan.py --daily --store <path_to_daily_csv> [--date YYYY-MM-DD]
  python scripts/gom_scan.py --backtest6  # print §6 gate table only
"""
from __future__ import annotations

import sys
import json
import math
import argparse
from pathlib import Path
from datetime import datetime, timezone, timedelta
from collections import defaultdict
from typing import Any

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except AttributeError:
    pass

# ── Canonical imports ────────────────────────────────────────────────────────
BOT_ROOT = Path(__file__).resolve().parent.parent.parent / "binance-bot-signals"
if not BOT_ROOT.exists():
    BOT_ROOT = Path(r"D:\Data back test\binance-bot-signals")
sys.path.insert(0, str(BOT_ROOT))

from scanner.screener.signals import (
    DayData, load_thresholds, SUPPRESSORS,
    lsr_accum, stealth_grind, s3_eve, pos_rerate, funding_unpin,
    hedge_structure, funding_pinned, funding_pinned_strong, absorption, oi_ignition,
    crowd_flush,
    dist_wall, lsr_dist, funding_neg_div, funding_extreme, decay, post_climax,
)
# stealth_grind = auxiliary/display only (not A2); oi_ignition = auxiliary/display only (not B4)

import importlib.util
_replay_spec = importlib.util.spec_from_file_location("replay", BOT_ROOT / "replay.py")
_replay_mod  = importlib.util.module_from_spec(_replay_spec)
_replay_spec.loader.exec_module(_replay_mod)
parse_result_file = _replay_mod.parse_result_file
build_days        = _replay_mod.build_days

CASE_DIR = BOT_ROOT / "docs" / "case study"

# ── Config paths ─────────────────────────────────────────────────────────────
REPO_ROOT    = Path(__file__).resolve().parent.parent
_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

SCREEN_CFG  = REPO_ROOT / "screen_thresholds.yaml"
STATE_PATH  = REPO_ROOT / "data" / "gom_state.json"
HB_PATH     = REPO_ROOT / "data" / "gom_heartbeat.txt"

# ── Load screen thresholds ───────────────────────────────────────────────────

def load_screen_cfg() -> dict:
    if not SCREEN_CFG.exists():
        raise FileNotFoundError(f"screen_thresholds.yaml not found: {SCREEN_CFG}")
    import yaml  # type: ignore
    with open(SCREEN_CFG, encoding="utf-8") as fh:
        return yaml.safe_load(fh)

def _scfg(sc: dict) -> dict:
    return sc.get("gom", sc)

# ── Suspect tokens (án CSV-mutation đang mở) ─────────────────────────────────
SUSPECT_TOKENS: frozenset[str] = frozenset({"BANK"})

# ── M3: A6 price-slope-guard — DISABLED until M3b test PASS (B2.3) ───────────
# After test passes, set True and re-run B2.2 gate to confirm no FAIL regression.
A6_PRICE_SLOPE_GUARD_ENABLED: bool = False

# ── GOM-A/B evaluation ───────────────────────────────────────────────────────

def eval_gom(days: list[DayData], i: int, cfg: dict, sc: dict) -> dict:
    """Evaluate GOM conditions for day i. Returns result dict."""
    g = _scfg(sc)
    hedge_lb = g.get("hedge_lookback_days", 7)
    d = days[i]  # current day (needed early for listing_date toi_dq)

    # GOM-A signals
    a1 = lsr_accum(days, i, cfg)
    # A2: avg5(lsr_global) ≤ 1.1 — inline check (spec v1.3; stealth_grind = SG = auxiliary only)
    a2 = _avg5_glsr(days, i) <= 1.1
    # A3: gLSR slope 5d ≤ 1.15 — "fuel not exhausted" (§1; NaN/early → FAIL-CLOSED → False)
    a3 = _a3_slope_ok(days, i, sc)
    # A4: d_pos_3d ≥ 0 OR pos_rerate sống (spec v1.4; NaN d_pos_3d → only pos_rerate)
    _d3 = d.get("d_pos_3d", float("nan"))
    a4 = (not math.isnan(_d3) and _d3 >= 0) or pos_rerate(days, i, cfg)
    # A5: oi_cycle_pos ≤ 0.5 — OI trong vùng tích lũy 30d rolling (spec v1.4)
    _oicp = d.get("oi_cycle_pos", float("nan"))
    a5 = not math.isnan(_oicp) and _oicp <= 0.5
    # A6: price-slope-guard (M3 — DISABLED flag; same as _a3_slope_ok but formally named A6)
    # Enabled only after M3b 3-case test PASS (B2.3). Does NOT affect GOM firing until enabled.
    a6 = A6_PRICE_SLOPE_GUARD_ENABLED and _a3_slope_ok(days, i, sc)

    gom_a = {"A1": a1, "A2": a2, "A3": a3, "A4": a4, "A5": a5, "A6": a6}
    # §1 structural formula: GOM-A = A1 AND A2 AND A3 AND (A4 OR A5)
    # A6 not yet in formula (PENDING M3b) — computed for audit/trace only
    gom_a_fire = a1 and a2 and a3 and (a4 or a5)

    # GOM-B signals
    # B1: hedge_structure bền ≥ hedge_lookback_days (all days in window must satisfy)
    b1 = all(
        hedge_structure(days, j, cfg)
        for j in range(max(0, i - hedge_lb + 1), i + 1)
    )
    b2 = funding_pinned(days, i, cfg) or funding_pinned_strong(days, i, cfg)
    b3 = absorption(days, i, cfg)
    # B4: NOT funding_neg_div — clean environment. FAIL-CLOSED: funding NaN → B4=False
    _f_avg = days[i].get("funding_avg", float("nan"))
    b4 = (not math.isnan(_f_avg)) and not funding_neg_div(days, i, cfg)
    gom_b = {"B1": b1, "B2": b2, "B3": b3, "B4": b4}

    # §1 structural formula: GOM-B = B1 AND (B2 OR B3) AND B4 (confirmed correct)
    gom_b_fire = b1 and (b2 or b3) and b4

    # Suppressor CỨNG (6 signals — trigger 14d cooldown)
    supp_dq = {
        "dist_wall":       dist_wall(days, i, cfg),
        "lsr_dist":        lsr_dist(days, i, cfg),
        "funding_neg_div": funding_neg_div(days, i, cfg),
        "funding_extreme": funding_extreme(days, i, cfg),
        "decay":           decay(days, i, cfg),
        "post_climax":     post_climax(days, i, cfg),
    }
    any_supp_dq = any(supp_dq.values())

    # Per-day DQ (block today only — NO 14d cooldown)
    # toi_dq: if DayData has "listing_date" (YYYY-MM-DD), use symbol age; else fall back to i<13
    _listing = d.get("listing_date", "")
    if _listing:
        try:
            _d_str = d.get("date", "")
            if len(_d_str) == 5:
                _d_str = "2026-" + _d_str
            _age = (datetime.strptime(_d_str[:10], "%Y-%m-%d") -
                    datetime.strptime(_listing[:10], "%Y-%m-%d")).days
            _toi_dq = _age < 14
        except Exception:
            _toi_dq = i < 13
    else:
        _toi_dq = i < 13  # legacy: data starts at listing date
    perday_dq = {
        "wrong_side": _wrong_side_dq(days, i, sc),   # L-26: price↓ + gLSR↑ (5d + 1d checks)
        "slope_dq":   _slope_dq(days, i, sc),        # glsr_slope_5d > 1.15: distribution phase
        "toi_dq":     _toi_dq,                        # token age <14d; from listing_date if known
    }
    any_perday_dq = any(perday_dq.values())

    # Auxiliary flags
    vol_q   = d.get("vol_quote", float("nan"))
    oi      = d.get("oi_usd", float("nan"))
    lc = (not math.isnan(vol_q) and vol_q < g.get("vol_low_conf_usd", 200_000)) or \
         (not math.isnan(oi)    and oi    < g.get("oi_low_conf_usd",  1_000_000))

    cf_today = crowd_flush(days, i, cfg)

    gom_day = (gom_a_fire or gom_b_fire) and not any_supp_dq and not any_perday_dq

    return {
        "gom_day":       gom_day,
        "gom_a":         gom_a,
        "gom_a_fire":    gom_a_fire,
        "gom_b":         gom_b,
        "gom_b_fire":    gom_b_fire,
        "supp_dq":       supp_dq,
        "perday_dq":     perday_dq,
        "any_supp_dq":   any_supp_dq,
        "any_perday_dq": any_perday_dq,
        "any_dq":        any_supp_dq or any_perday_dq,   # backward-compat
        "disqualifier":  {**supp_dq, **perday_dq},       # backward-compat flat view
        "low_conf":      lc,
        "crowd_flush":   cf_today,
        "struct_alive":  any_supp_dq and a1 and a2 and a3,  # ⏸ A1∧A2∧A3 pass under suppressor
    }


def _avg5_glsr(days: list[DayData], i: int) -> float:
    """avg5(lsr_global): mean of lsr_global_r over days[i-4:i+1]. NaN if insufficient data."""
    start = max(0, i - 4)
    vals = [days[j].get("lsr_global", float("nan")) for j in range(start, i + 1)]
    vals = [v for v in vals if not math.isnan(v)]
    if not vals:
        return float("nan")
    return sum(vals) / len(vals)


def _ret_1d(days: list[DayData], i: int) -> float:
    """1-day price return: (today.avg_px - prev.avg_px) / prev.avg_px."""
    if i == 0:
        return float("nan")
    p_prev = days[i-1].get("avg_px", float("nan"))
    p_now  = days[i].get("avg_px",  float("nan"))
    if math.isnan(p_prev) or math.isnan(p_now) or p_prev <= 0:
        return float("nan")
    return (p_now - p_prev) / p_prev


def _wrong_side_dq(days: list[DayData], i: int, sc: dict) -> bool:
    """Per-day DQ: distribution signal — price down + crowd longs rising (L-26).
    Two checks (either triggers):
      (A) 5d: px_chg_5d ≤ -px_drop_min AND gLSR_chg_5d ≥ glsr_rise_min
      (B) 1d: ret_1d ≤ -ret_1d_min AND gLSR_1d_chg ≥ glsr_1d_min
    NOT a suppressor — blocks today only, no 14d cooldown.
    """
    g = _scfg(sc)
    c = g.get("wrong_side_dq", {})
    if not c:
        return False

    # (A) 5d check
    n        = c.get("lookback_days", 5)
    px_drop  = c.get("px_drop_min", 0.10)
    glsr_min = c.get("glsr_rise_min", 0.15)
    if i >= n:
        px0  = days[i-n].get("avg_px",     float("nan"))
        px1  = days[i].get("avg_px",       float("nan"))
        g0   = days[i-n].get("lsr_global", float("nan"))
        g1   = days[i].get("lsr_global",   float("nan"))
        if not any(math.isnan(v) for v in (px0, px1, g0, g1)) and px0 > 0 and g0 > 0:
            if (px1 - px0) / px0 <= -px_drop and (g1 - g0) / g0 >= glsr_min:
                return True

    # (B) 1d check: ret_1d ≤ -5% AND gLSR_1d_chg ≥ +5%
    ret_1d_min  = c.get("ret_1d_min", 0.05)
    glsr_1d_min = c.get("glsr_1d_min", 0.05)
    if i >= 1:
        px_prev = days[i-1].get("avg_px",     float("nan"))
        px_now  = days[i].get("avg_px",       float("nan"))
        g_prev  = days[i-1].get("lsr_global", float("nan"))
        g_now   = days[i].get("lsr_global",   float("nan"))
        if not any(math.isnan(v) for v in (px_prev, px_now, g_prev, g_now)):
            if px_prev > 0 and g_prev > 0:
                if (px_now - px_prev) / px_prev <= -ret_1d_min and \
                   (g_now - g_prev) / g_prev >= glsr_1d_min:
                    return True

    return False


def _slope_dq(days: list[DayData], i: int, sc: dict) -> bool:
    """Per-day DQ: glsr_slope_5d = lsr_global(i) / lsr_global(i-5) > 1.15 = distribution phase."""
    g = _scfg(sc)
    slope_max = g.get("slope_5d_max", 1.15)
    n = 5
    if i < n:
        return False
    g0 = days[i-n].get("lsr_global", float("nan"))
    g1 = days[i].get("lsr_global",   float("nan"))
    if math.isnan(g0) or math.isnan(g1) or g0 <= 0:
        return False
    return (g1 / g0) > slope_max


def _a3_slope_ok(days: list[DayData], i: int, sc: dict) -> bool:
    """A3 GOM-A condition: gLSR slope_5d ≤ 1.15 ('fuel not exhausted').
    FAIL-CLOSED: i<5 or g0/g1 NaN → returns False (condition NOT satisfied).
    Distinct from _slope_dq (per-day DQ uses fail-open; GOM-A condition uses fail-closed).
    """
    g = _scfg(sc)
    slope_max = g.get("slope_5d_max", 1.15)
    if i < 5:
        return False
    g0 = days[i-5].get("lsr_global", float("nan"))
    g1 = days[i].get("lsr_global",   float("nan"))
    if math.isnan(g0) or math.isnan(g1) or g0 <= 0:
        return False
    return (g1 / g0) <= slope_max


def _gomc_beta_check(
    days: list[DayData], i: int, cfg: dict, sc: dict, result: dict,
    check_cooldown: bool = True,
) -> bool:
    """GOM-C PROVISIONAL-β per-day check (signed operator 2026-08-08 Q1/Q2/Q3).

    C1(stealth_grind) ∧ C2_quiet(f_avg ≤ 2×neutral per interval) ∧
    C3_lax(taker∈[40,55]) ∧ d_pos≥0(pos_r non-declining) ∧
    NOT(gLSR slope>1.15 for ≥3d) ∧ NOT supp_dq(today) ∧ NOT(supp_dq in prior 13d).

    C2 2×neutral table: 4h→1e-4, 8h→2e-4, 1h→2.5e-5.
    check_cooldown=False: skip 14d backward scan (for suppressed-display detection only).
    result: pre-computed eval_gom dict — reused to avoid double call.
    Display only — no state changes.
    """
    # NOT any supp_dq (today)
    if any(v for v in result.get("supp_dq", {}).values()):
        return False
    # C1: stealth_grind (encodes taker<55% in build window)
    if not stealth_grind(days, i, cfg):
        return False
    # C2_quiet: f_avg ≤ 2×neutral threshold per interval
    # thr_8h = max(2×rate_min, 1e-4) = 1e-4; 2×neutral: thr = thr_8h × (interval_h/4)
    # Table: 4h→1e-4, 8h→2e-4, 1h→2.5e-5
    f_avg = days[i].get("funding_avg", float("nan"))
    if math.isnan(f_avg):
        return False
    interval_h = days[i].get("_interval_h", 8)
    fp = cfg.get("funding_pinned", {})
    c2_thr_8h = max(2.0 * fp.get("rate_min", 4e-5), 1e-4)
    c2_thr = c2_thr_8h * interval_h / 4   # 2×neutral: 4h→1e-4, 8h→2e-4, 1h→2.5e-5
    if f_avg > c2_thr:
        return False
    # C3_lax: taker_buy_pct ∈ [40, 55]
    tkr = days[i].get("taker_buy_pct", float("nan"))
    if math.isnan(tkr) or not (40.0 <= tkr <= 55.0):
        return False
    # d_pos ≥ 0: pos_r (lsr_pos) must not decline day-over-day
    if i == 0:
        return False
    p_now = days[i].get("lsr_pos", float("nan"))
    p_prv = days[i-1].get("lsr_pos", float("nan"))
    if math.isnan(p_now) or math.isnan(p_prv) or (p_now - p_prv) < 0:
        return False
    # C4 slope-close: suppress if gLSR slope > 1.15 sustained ≥3 consecutive days
    slope_bad = sum(
        1 for j in range(max(0, i - 2), i + 1)
        if not _a3_slope_ok(days, j, sc)
    )
    if slope_bad >= 3:
        return False
    # 14d supp cooldown: GOM-C inherits same cooldown as GOM-B (§8.4 rule-i)
    # any supp_dq fire in prior 13 days → today still in cooldown window
    if check_cooldown:
        for j in range(max(0, i - 13), i):
            dj = days[j]
            if dj.get("_skip_eval") or dj.get("_suspect"):
                continue
            rj = eval_gom(days, j, cfg, sc)
            if any(v for v in rj.get("supp_dq", {}).values()):
                return False
    return True


def _gomc_c_cooldown_info(
    days: list[DayData], i: int, cfg: dict, sc: dict
) -> tuple[str, str, int]:
    """Find earliest supp_dq fire in prior 13d for GOM-C suppressed display.

    Returns (first_fire_date, cooldown_end_date, days_remaining_inclusive).
    Returns ("", "", 0) if no cooldown active.
    """
    today_str = days[i].get("date", "")
    if len(today_str) == 5:
        today_str = "2026-" + today_str

    first_fire = ""
    for j in range(max(0, i - 13), i):
        dj = days[j]
        if dj.get("_skip_eval") or dj.get("_suspect"):
            continue
        rj = eval_gom(days, j, cfg, sc)
        if any(v for v in rj.get("supp_dq", {}).values()):
            dj_str = dj.get("date", "")
            if len(dj_str) == 5:
                dj_str = "2026-" + dj_str
            if not first_fire:
                first_fire = dj_str[:10]  # earliest fire in window

    if not first_fire:
        return "", "", 0

    try:
        first_dt        = datetime.strptime(first_fire, "%Y-%m-%d")
        cooldown_end_dt = first_dt + timedelta(days=13)  # last blocked day
        today_dt        = datetime.strptime(today_str[:10], "%Y-%m-%d")
        remaining       = (cooldown_end_dt - today_dt).days + 1  # inclusive today
        cooldown_end    = cooldown_end_dt.strftime("%Y-%m-%d")
        return first_fire, cooldown_end, max(0, remaining)
    except Exception:
        return "", "", 0


# ── Chain state machine ───────────────────────────────────────────────────────

def _empty_chain(date_str: str) -> dict:
    return {
        "chain_open":      True,
        "start_date":      date_str,
        "chapter":         1,
        # Q1 / accumulation (M4: gross_adds_usd mirrors Q1_cum_usd)
        "Q1_cum_usd":      0.0,
        "gross_adds_usd":  0.0,   # M4 alias — kept in sync with Q1_cum_usd
        "oi_start_usd":    float("nan"),  # M4: OI snapshot at chain open (first GOM fire)
        "oi_last_usd":     float("nan"),  # M4: OI snapshot at last GOM fire
        "net_oi_delta_usd": float("nan"), # M4: oi_last_usd - oi_start_usd (per-chapter)
        # VWAP Tier 1: ΔOI⁺-weighted (primary)
        "vwap_num":        0.0,   # Σ ΔOI⁺ × avg_px
        "vwap_den":        0.0,   # Σ ΔOI⁺
        # VWAP Tier 2: chain-level vol-weighted (fallback when vwap_den=0 — seat-rotation)
        "vwap_vol_num":    0.0,   # Σ vol_quote × avg_px (all GOM fire days)
        "vwap_vol_den":    0.0,   # Σ vol_quote (all GOM fire days)
        "vwap_type":       None,  # "oi_weighted" | "vol_weighted" | null
        "n_days":          0,
        "peak_pos_r":      float("nan"),
        "break_streak":    0,
        "last_gom_date":   date_str,
        "last_flush_date": "",    # §8.2 rule (ii): track last crowd_flush for gap check
        "chapter_hist":    [],
        "suspect_flag":    False,
        "updated_at":      "",
    }


def _close_chain(st: dict, reason: str, date_str: str) -> dict:
    st["chain_open"] = False
    st["close_date"] = date_str
    st["close_reason"] = reason
    return st


def _new_chapter(st: dict, date_str: str) -> dict:
    """Archive current chapter, start fresh Q1/VWAP accumulation (§8.2)."""
    vwap_current = (st["vwap_num"] / st["vwap_den"]) if st["vwap_den"] > 0 else float("nan")
    st["chapter_hist"].append({
        "chapter":  st["chapter"],
        "start":    st["start_date"],
        "end":      date_str,
        "vwap":     vwap_current,
        "Q1_cum":   st["Q1_cum_usd"],
    })
    st["chapter"]          += 1
    st["start_date"]       = date_str
    st["Q1_cum_usd"]       = 0.0
    st["gross_adds_usd"]   = 0.0
    st["oi_start_usd"]     = float("nan")  # reset per new chapter
    st["oi_last_usd"]      = float("nan")
    st["net_oi_delta_usd"] = float("nan")
    st["vwap_num"]         = 0.0
    st["vwap_den"]         = 0.0
    st["vwap_vol_num"]     = 0.0
    st["vwap_vol_den"]     = 0.0
    st["vwap_type"]        = None
    st["n_days"]           = 0
    return st


def update_chain(
    state:     dict,    # mutable per-token state dict (or {})
    token:     str,
    days:      list[DayData],
    i:         int,
    result:    dict,    # from eval_gom
    cfg:       dict,
    sc:        dict,
) -> dict:
    """Update per-token chain state for day i. Returns updated state dict."""
    g   = _scfg(sc)
    d   = days[i]
    date_str = d.get("date", "??")
    # Normalise to YYYY-MM-DD if MM-DD
    if len(date_str) == 5:
        date_str = "2026-" + date_str

    gom      = result["gom_day"]
    supp_dq  = result["any_supp_dq"]   # only suppressors trigger 14d cooldown
    cf       = result["crowd_flush"]

    # Initialise state if empty
    if not state:
        state = {}

    chain = state  # top-level dict is the chain (we pass token's chain state)

    # ── Retro-tag: display-only label post-gom_gap close (operator signed 08/08/2026) ──
    # If chain closed via gom_gap AND pos_r drops >=30% from peak within <=3d of close_date
    # → label state with retro_tag (no state change, display only).
    if (not chain.get("chain_open")
            and chain.get("close_reason", "").startswith("gom_gap")
            and not chain.get("retro_tag")
            and chain.get("close_date", "")):
        _close_d = chain.get("close_date", "")
        try:
            _gap_d = (datetime.strptime(date_str[:10], "%Y-%m-%d") -
                      datetime.strptime(_close_d[:10], "%Y-%m-%d")).days
            if 0 < _gap_d <= 3:
                _rt_pos = d.get("lsr_pos", float("nan"))
                if math.isnan(_rt_pos):
                    _rt_pos = d.get("lsr_pos_r", float("nan"))
                _rt_peak = chain.get("peak_pos_r", float("nan"))
                if not math.isnan(_rt_pos) and not math.isnan(_rt_peak) and _rt_peak > 0:
                    _rt_drop = (_rt_peak - _rt_pos) / _rt_peak
                    if _rt_drop >= g.get("pos_r_drop_close", 0.30):
                        chain["retro_tag"] = date_str
                        chain["retro_tag_drop"] = f"{_rt_drop:.0%}"
                        chain["retro_tag_note"] = f"gap→chuyển pha phân phối (retro {date_str})"
        except (ValueError, TypeError):
            pass

    # ── Rule (i): Suppressor CỨNG → close chain + update DQ episode + cooldown
    # Per-day DQ (wrong_side/slope/toi) does NOT trigger cooldown — handled via gom_day=False
    DQ_EP_GAP = 3  # ≥3d clean = new suppressor episode (same rule as flush gap)
    if supp_dq:
        last_fire = state.get("dq_last_fire", "")
        if last_fire:
            try:
                gap_dq = (datetime.strptime(date_str[:10], "%Y-%m-%d") -
                          datetime.strptime(last_fire[:10], "%Y-%m-%d")).days
            except ValueError:
                gap_dq = 0
        else:
            gap_dq = 99
        if gap_dq >= DQ_EP_GAP or not last_fire:
            # New DQ episode — cooldown starts from today
            state["dq_episode_start"] = date_str
            state["dq_cooldown_end"]  = (datetime.strptime(date_str[:10], "%Y-%m-%d")
                                          + timedelta(days=13)).strftime("%Y-%m-%d")
        # 13 = window-1: fire_day(day0) + days 1..13 = 14 days total. clear from day14 = fire+14.
        # Matches G1 formula: clear when idx - ep_start_idx >= 14.
        state["dq_last_fire"] = date_str
        if chain.get("chain_open"):
            # Rule (iv) wins label when both suppressor + pos_r_drop fire same day
            _pos_r = d.get("lsr_pos", float("nan"))
            if math.isnan(_pos_r):
                _pos_r = d.get("lsr_pos_r", float("nan"))
            _peak = chain.get("peak_pos_r", float("nan"))
            if not math.isnan(_pos_r) and not math.isnan(_peak) and _peak > 0:
                _drop = (_peak - _pos_r) / _peak
                if _drop >= g.get("pos_r_drop_close", 0.30):
                    state = _close_chain(chain,
                        f"pos_r_drop:{_drop:.0%}_from_peak:{_peak:.2f}", date_str)
                    state["close_note"] = "chuyển pha phân phối"
                    return state
            fired = [k for k, v in result["supp_dq"].items() if v]
            state = _close_chain(chain, f"suppressor:{'+'.join(fired)}", date_str)
        return state

    # ── Cooldown block: within 14d of DQ episode first-fire ─────────────────
    cooldown_end = state.get("dq_cooldown_end", "")
    if cooldown_end and date_str <= cooldown_end:
        if chain.get("chain_open"):
            state = _close_chain(chain, f"dq_cooldown_until:{cooldown_end}", date_str)
        return state

    # ── Rule (iv): check pos_r drop on ALL open days — including gap days ────
    # §8.4(iv) "ĐÓNG NGAY" = close immediately whenever chain is open, not just GOM days.
    # Rule (iv) wins over rule (iii): same day → label "chuyển pha phân phối", not "hết tín hiệu".
    if chain.get("chain_open"):
        _pos_r = d.get("lsr_pos", float("nan"))
        if math.isnan(_pos_r):
            _pos_r = d.get("lsr_pos_r", float("nan"))
        _peak = chain.get("peak_pos_r", float("nan"))
        if not math.isnan(_pos_r) and not math.isnan(_peak) and _peak > 0:
            _drop = (_peak - _pos_r) / _peak
            if _drop >= g.get("pos_r_drop_close", 0.30):
                state = _close_chain(chain,
                    f"pos_r_drop:{_drop:.0%}_from_peak:{_peak:.2f}", date_str)
                state["close_note"] = "chuyển pha phân phối"
                return state  # rule (iv) wins — return before rule (iii) gap check

    # ── If no GOM and chain open: break_streak logic ─────────────────────────
    if not gom:
        if chain.get("chain_open"):
            chain["break_streak"] = chain.get("break_streak", 0) + 1
            if chain["break_streak"] > g.get("break_gap_max", 2):
                # ── Rule (iii): gap >2d → close ──────────────────────────────
                state = _close_chain(chain, "gom_gap>2d", date_str)
        return state

    # ── GOM fires today ───────────────────────────────────────────────────────

    # Open new chain if none open — preserve DQ episode fields across open
    if not chain.get("chain_open", False):
        dq_save = {k: state.get(k, "") for k in
                   ("dq_episode_start", "dq_last_fire", "dq_cooldown_end")}
        state = _empty_chain(date_str)
        state.update(dq_save)
        # M4: oi_start_usd set on first open (will be set again in OI tracking block below)
        chain = state

    chain["break_streak"] = 0
    chain["last_gom_date"] = date_str

    # ── Rule (ii): crowd_flush → new chapter (gap ≥ crowd_flush_gap_min_days) ──
    if cf:
        cf_gap_min = g.get("crowd_flush_gap_min_days", 3)
        last_flush = chain.get("last_flush_date", "")
        if last_flush:
            try:
                d0 = datetime.strptime(last_flush[:10], "%Y-%m-%d")
                d1 = datetime.strptime(date_str[:10], "%Y-%m-%d")
                gap_days = (d1 - d0).days
            except ValueError:
                gap_days = 99
        else:
            gap_days = 99  # no prior flush → always eligible
        if gap_days >= cf_gap_min:
            state = _new_chapter(chain, date_str)
            chain = state
        chain["last_flush_date"] = date_str

    # ── Update peak pos_r (on GOM days only — non-GOM gaps don't set new highs) ─
    pos_r = d.get("lsr_pos", float("nan"))
    if math.isnan(pos_r):
        pos_r = d.get("lsr_pos_r", float("nan"))
    if not math.isnan(pos_r):
        peak = chain.get("peak_pos_r", float("nan"))
        if math.isnan(peak) or pos_r > peak:
            chain["peak_pos_r"] = pos_r
    # (rule iv already handled above for all open days, before this GOM section)

    # ── M4: OI tracking (oi_start on first fire; oi_last every GOM fire) ────
    _oi_now = d.get("oi_usd", float("nan"))
    if not math.isnan(_oi_now):
        if math.isnan(chain.get("oi_start_usd", float("nan"))):
            chain["oi_start_usd"] = _oi_now   # first GOM fire in this chapter
        chain["oi_last_usd"] = _oi_now
        _oi_start = chain.get("oi_start_usd", float("nan"))
        chain["net_oi_delta_usd"] = _oi_now - _oi_start if not math.isnan(_oi_start) else float("nan")

    # ── Q1 counting ──────────────────────────────────────────────────────────
    ret = _ret_1d(days, i)
    ret_max = g.get("ret_1d_max", 0.01)
    counts_q1 = not math.isnan(ret) and ret <= ret_max
    # S1: PARTIAL_DAY (insufficient funding settlements) → skip Q1 this day
    if d.get("_partial_day"):
        counts_q1 = False

    if counts_q1:
        # ΔOI⁺ = max(OI_today - OI_prev, 0)
        oi_prev = days[i-1].get("oi_usd", float("nan")) if i > 0 else float("nan")
        if not math.isnan(_oi_now) and not math.isnan(oi_prev):
            delta_oi = max(_oi_now - oi_prev, 0.0)
        else:
            delta_oi = 0.0

        chain["Q1_cum_usd"]     = chain.get("Q1_cum_usd", 0.0) + delta_oi
        chain["gross_adds_usd"] = chain["Q1_cum_usd"]   # M4: alias in sync
        chain["n_days"]         = chain.get("n_days", 0) + 1

        # VWAP Tier 1: ΔOI⁺-weighted (M2 primary)
        px = d.get("avg_px", float("nan"))
        if not math.isnan(px) and delta_oi > 0:
            chain["vwap_num"] = chain.get("vwap_num", 0.0) + delta_oi * px
            chain["vwap_den"] = chain.get("vwap_den", 0.0) + delta_oi
            chain["vwap_type"] = "oi_weighted"
        # M2: NO per-day vol-fallback here — Tier 2 accumulated separately below

    # ── M2 VWAP Tier 2: vol-weighted accumulation on ALL GOM fire days ───────
    # Used as chain-level fallback when vwap_den=0 (seat-rotation build).
    # Accumulated regardless of Q1 counting or ΔOI.
    _px_t2 = d.get("avg_px", float("nan"))
    _vol_t2 = d.get("vol_quote", float("nan"))
    if not math.isnan(_px_t2) and not math.isnan(_vol_t2) and _vol_t2 > 0:
        chain["vwap_vol_num"] = chain.get("vwap_vol_num", 0.0) + _vol_t2 * _px_t2
        chain["vwap_vol_den"] = chain.get("vwap_vol_den", 0.0) + _vol_t2
        # vwap_type stays "oi_weighted" if Tier 1 already set; only fallback if still None
        if chain.get("vwap_type") is None:
            chain["vwap_type"] = "vol_weighted"   # tentative until vwap_den possibly fills

    # suspect flag
    if token in SUSPECT_TOKENS:
        chain["suspect_flag"] = True

    chain["updated_at"] = datetime.now(timezone.utc).isoformat()
    return chain


# ── Report formatting ─────────────────────────────────────────────────────────

def format_chain_report(token: str, chain: dict, result: dict | None, date_str: str) -> str:
    lines = []
    if not chain.get("chain_open"):
        reason = chain.get("close_reason", "?")
        closed = chain.get("close_date", "?")
        retro  = chain.get("retro_tag_note", "")
        retro_str = f"  [{retro}]" if retro else ""
        lines.append(f"══ {token} ══ CHAIN CLOSED ({closed}) reason={reason}{retro_str}")
        return "\n".join(lines)

    ch = chain.get("chapter", 1)
    nd = chain.get("n_days", 0)
    bk = chain.get("break_streak", 0)
    start = chain.get("start_date", "?")
    lines.append(f"══ {token} {'='*(max(0,56-len(token)))}")
    lines.append(f" Chuỗi: [chương {ch}] start={start}  n_days={nd}  break_streak={bk}")

    if result:
        active_a = [k for k, v in result["gom_a"].items() if v]
        active_b = [k for k, v in result["gom_b"].items() if v]
        dq_list  = [k for k, v in result["disqualifier"].items() if v]
        cond_str = " ".join(active_a) + (" " if active_a and active_b else "") + " ".join(active_b)
        if not cond_str:
            cond_str = "(break day)"
        lc = "low_conf" if result.get("low_conf") else ""
        lines.append(f" Điều kiện hôm nay: {cond_str}  {lc}")
        if dq_list:
            lines.append(f" !! DISQUALIFIER: {', '.join(dq_list)}")

    q1   = chain.get("Q1_cum_usd", 0.0)
    vnum = chain.get("vwap_num", 0.0)
    vden = chain.get("vwap_den", 0.0)
    ois  = chain.get("oi_start_usd", 0.0) or 0.0
    # M2 rep-threshold: 5% of oi_start (hardcoded here — tunable via screen_thresholds in TG report)
    _t1_ok = vden > 0 and (ois <= 0 or vden >= 0.05 * ois)
    if _t1_ok:
        vwap     = vnum / vden
        vwap_tag = ""
    else:
        _vvn = chain.get("vwap_vol_num", 0.0)
        _vvd = chain.get("vwap_vol_den", 0.0)
        vwap     = _vvn / _vvd if _vvd > 0 else float("nan")
        vwap_tag = " [vw-vol — seat-rotation chain]" if _vvd > 0 else ""

    lines.append(f"")
    lines.append(f" Q1_cum:  ${q1:>12,.0f}  (ΔOI⁺-weighted)")
    if not math.isnan(vwap):
        lines.append(f" VWAP_gom: ${vwap:.6f}{vwap_tag}  [chương hiện tại]")

    for prev in chain.get("chapter_hist", []):
        pv = prev.get("vwap", float("nan"))
        pv_str = f"${pv:.6f}" if not math.isnan(pv) else "N/A"
        lines.append(f" VWAP cũ:  chương {prev['chapter']}: {pv_str} ({prev['start']}→{prev['end']})  Q1=${prev['Q1_cum']:,.0f}")

    peak = chain.get("peak_pos_r", float("nan"))
    if not math.isnan(peak):
        lines.append(f" peak_pos_r: {peak:.2f}")

    suspect = chain.get("suspect_flag", False)
    lines.append(f"")
    lines.append(f" LAYER COVERAGE: perp ✓ / spot ? / on-chain ?")
    if suspect:
        lines.append(f" ⚠ SUSPECT: token trong án CSV-mutation — số cộng dồn mang cờ đến khi án đóng")

    return "\n".join(lines)


def format_footer(all_states: dict, sc: dict) -> str:
    g = _scfg(sc)
    big = g.get("q1_cum_big_usd", 2_000_000)
    any_big = any(
        st.get("chain_open") and st.get("Q1_cum_usd", 0) > big
        for st in all_states.values()
    )
    lines = [
        "",
        "── NOTES CHUNG " + "─" * 55,
        "PARTI: [status chưa cập nhật — VPS probe cần refresh]",
        "ZBT: perp sống (CASE_ZBT active); alpha-spot endpoint 400 = không liên quan",
    ]
    if any_big:
        lines.append('"số lớn ≠ kèo gần — chuỗi dài nhất sổ (ZBT 3 tuần) vẫn cần tell + suppressor sạch"')
    lines.append("SCREEN-only report. CONFIRM C1-C5 là tầng tay/ANALYSIS.")
    return "\n".join(lines)


# ── Load/save state ───────────────────────────────────────────────────────────

def load_state() -> dict:
    if STATE_PATH.exists():
        with open(STATE_PATH, encoding="utf-8") as fh:
            return json.load(fh)
    return {}


def save_state(state: dict) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_PATH, "w", encoding="utf-8") as fh:
        json.dump(state, fh, indent=2, ensure_ascii=False)


# ── Backfill mode (12 case files) ────────────────────────────────────────────

TOKEN_ORDER = ["BANK", "AKE", "TAG", "BAS", "POWER", "BASED",
               "CLO", "BTW", "TUT", "BULLA", "ESPORTS", "IDOL"]

def run_backfill(cfg: dict, sc: dict, token_filter: str | None = None) -> dict:
    """Process all 12 calibration cases chronologically. Returns final state dict."""
    all_days: dict[str, list[DayData]] = {}
    for fpath in sorted(CASE_DIR.glob("*_result.txt")):
        token = _replay_mod._token_from_path(fpath)
        if token_filter and token != token_filter:
            continue
        funding, oi, ratio, klines = parse_result_file(fpath)
        all_days[token] = build_days(funding, oi, ratio, klines)

    all_state: dict[str, dict] = {}

    for token, days in all_days.items():
        chain: dict = {}
        print(f"\n{'='*70}")
        print(f"Token: {token}  ({len(days)} days)")
        print(f"{'='*70}")

        for i, d in enumerate(days):
            result = eval_gom(days, i, cfg, sc)
            chain  = update_chain(chain, token, days, i, result, cfg, sc)

            date = d.get("date", "??")
            gom  = result["gom_day"]
            dq   = result["any_dq"]
            cf   = result["crowd_flush"]
            ret  = _ret_1d(days, i)
            active_a = [k for k, v in result["gom_a"].items() if v]
            active_b = [k for k, v in result["gom_b"].items() if v]
            dq_list  = [k for k, v in result["disqualifier"].items() if v]

            sig_str = " ".join(active_a + active_b)
            dq_str  = " DQ:"+"+".join(dq_list) if dq_list else ""
            cf_str  = " CF↑chapter" if cf else ""
            ret_str = f" ret={ret:+.1%}" if not math.isnan(ret) else ""
            q1_str  = f" Q1_cum=${chain.get('Q1_cum_usd',0):,.0f}" if chain.get("chain_open") else ""
            closed  = "" if chain.get("chain_open", False) else f" [CLOSED:{chain.get('close_reason','')}]"

            print(f"  {date}: {'GOM' if gom else '   '}  {sig_str}{dq_str}{cf_str}{ret_str}{q1_str}{closed}")

        # Final state
        all_state[token] = chain
        if chain.get("chain_open"):
            print(format_chain_report(token, chain, None, "END"))

    return all_state


# ── Backtest §6 gate table ────────────────────────────────────────────────────

BACKTEST_GATE = [
    # ── Compose-level conformance (§1 formula) — verified in code, not by case date ──
    ("_FORMULA", "gom_a_fire", "GOM-A = A1 AND A2 AND A3 AND (A4 OR A5) — tất cả 3 điều kiện đầu bắt buộc đồng thời + ≥1 trong A4/A5"),
    ("_FORMULA", "gom_b_fire", "GOM-B = B1 AND (B2 OR B3) AND B4 — structural entry only"),
    # ── Case-level conformance (verified by replay date match) ───────────────────────
    ("BANK",   "open",    "Chain mở 06-29 (lsr_accum onset)"),
    ("BANK",   "chapter", "crowd_flush 07-02 → chapter mới"),
    ("BANK",   "close-iv","Chain ĐÓNG 07-19~21 (pos_r sập ≥30% từ peak), KHÔNG sống 07-24"),
    ("TAG",    "open",    "Chain mở 07-12 (lsr_accum + crowd_flush)"),
    ("BAS",    "SUPP",    "07-02→07-15: post_climax → disqualifier → GOM không fire"),
    ("BTW",    "SUPP",    "06-21→07-05: post_climax → disqualifier → GOM không fire"),
    ("BULLA",  "open",    "stealth_grind + B-path 07-17 → GOM fires (B1+B3+B4 path)"),
    ("TUT",    "chapter", "07-11: stealth_grind + crowd_flush → chapter mới"),
    ("IDOL",   "open",    "07-06: lsr_accum + pos_rerate + A3-ok → GOM-A fires (A1+A2+A3+A4)"),
    ("AKE",    "SUPP",    "07-08→07-20: decay SUPP → GOM không fire"),
]


def run_backtest6(cfg: dict, sc: dict) -> None:
    """Run backfill and check §6 gate conditions. Print PASS/FAIL table."""
    print("\nRunning backfill for §6 gate check...")

    # Run backfill and capture per-token day-by-day events
    events: dict[str, list[tuple[str, str]]] = defaultdict(list)

    for fpath in sorted(CASE_DIR.glob("*_result.txt")):
        token = _replay_mod._token_from_path(fpath)
        funding, oi, ratio, klines = parse_result_file(fpath)
        days = build_days(funding, oi, ratio, klines)
        chain: dict = {}
        prev_open = False
        prev_chapter = 0

        for i, d in enumerate(days):
            result = eval_gom(days, i, cfg, sc)
            was_open = chain.get("chain_open", False)
            was_chap = chain.get("chapter", 1)
            chain    = update_chain(chain, token, days, i, result, cfg, sc)
            date     = d.get("date", "??")

            # Detect chain open
            if not was_open and chain.get("chain_open"):
                events[token].append((date, "chain_open"))
            # Detect chapter change
            if was_open and chain.get("chain_open") and chain.get("chapter", 1) > was_chap:
                events[token].append((date, f"new_chapter_{chain['chapter']}"))
            # Detect chain close
            if was_open and not chain.get("chain_open"):
                reason = chain.get("close_reason", "?")
                events[token].append((date, f"chain_closed:{reason}"))
            # GOM fires + DQ
            if result["gom_day"]:
                events[token].append((date, "gom"))
            if result["any_dq"]:
                dq_list = [k for k, v in result["disqualifier"].items() if v]
                events[token].append((date, f"dq:{'+'.join(dq_list)}"))

    # Print §6 table
    print(f"\n{'='*90}")
    print(f"§6 Backtest Gate — gom_detect_spec v1.1")
    print(f"{'='*90}")
    print(f"{'#':>2} {'Token':<7} {'Episode':<12} {'Kỳ vọng':<55} {'Result'}")
    print("-"*90)

    all_pass = True
    for row_i, (token, episode, expect) in enumerate(BACKTEST_GATE, 1):
        tok_events = events.get(token, [])
        tok_event_strs = [f"{d}:{e}" for d, e in tok_events]

        # Check conditions
        result_label = "?"
        note = ""

        if episode == "open":
            opened = [d for d, e in tok_events if e == "chain_open"]
            if opened:
                result_label = f"PASS ({opened[0]})"
            else:
                result_label = "FAIL (no open)"
                all_pass = False

        elif episode == "chapter":
            chapters = [d for d, e in tok_events if e.startswith("new_chapter_")]
            if chapters:
                result_label = f"PASS ({chapters[0]})"
            else:
                result_label = "FAIL (no chapter)"
                all_pass = False

        elif episode == "close-iv":
            # Rule iv close: pos_r_drop in reason, date 07-19..07-21
            close_dates_iv = [(d, e) for d, e in tok_events
                              if "chain_closed" in e and "pos_r_drop" in e]
            if close_dates_iv:
                # Check date is ≤ 07-21 (YYYY-MM-DD or MM-DD)
                cd = close_dates_iv[0][0]
                cd_day = cd[-5:]  # last 5 chars = MM-DD
                if cd_day <= "07-21":
                    result_label = f"PASS ({cd})"
                else:
                    result_label = f"FAIL (closed too late: {cd})"
                    all_pass = False
            else:
                result_label = "FAIL (no iv close)"
                all_pass = False

        elif episode == "SUPP":
            # GOM should NOT fire during expected suppression window
            # Extract window from expect string
            # Check that no "chain_open" event occurred in the window
            opened = [d for d, e in tok_events if e == "chain_open"]
            # For suppressed tokens, check dq fires
            dq_fires = [d for d, e in tok_events if e.startswith("dq:")]
            if dq_fires and not opened:
                result_label = f"PASS (dq fired, no open)"
            elif dq_fires and opened:
                # Chain opened after suppression period ended?
                first_dq = dq_fires[0]
                first_open = opened[0]
                if first_open > first_dq:
                    result_label = f"PASS (dq then open {first_open})"
                else:
                    result_label = f"FAIL (open {first_open} before dq {first_dq})"
                    all_pass = False
            elif not dq_fires:
                result_label = "WARN (no dq fires — check data)"
            else:
                result_label = "PASS"

        print(f"{row_i:>2} {token:<7} {episode:<12} {expect[:53]:<55} {result_label}")

    print("-"*90)
    print(f"OVERALL: {'ALL PASS ✓' if all_pass else 'HAS FAILURES — see above'}")
    print(f"\nToken events detail:")
    for token in [t for t, _, _ in BACKTEST_GATE]:
        evs = events.get(token, [])
        if evs:
            print(f"  {token}: {evs}")


# ── Daily mode helpers ────────────────────────────────────────────────────────

def _false_result() -> dict:
    """Synthetic eval_gom result for S2/S-missing days: gom=False, no suppressors fired."""
    dq_keys = ["dist_wall", "lsr_dist", "funding_neg_div",
               "funding_extreme", "decay", "post_climax"]
    pd_keys = ["wrong_side", "slope_dq", "toi_dq"]
    return {
        "gom_day":       False,
        "gom_a":         {k: False for k in ["A1", "A2", "A3", "A4", "A5"]},
        "gom_a_fire":    False,
        "gom_b":         {k: False for k in ["B1", "B2", "B3", "B4"]},
        "gom_b_fire":    False,
        "supp_dq":       {k: False for k in dq_keys},
        "perday_dq":     {k: False for k in pd_keys},
        "any_supp_dq":   False,
        "any_perday_dq": False,
        "any_dq":        False,
        "disqualifier":  {k: False for k in dq_keys + pd_keys},
        "low_conf":      True,
        "crowd_flush":   False,
    }


def run_daily(
    cfg: dict,
    sc: dict,
    store: Path,
    target_date: str | None = None,
    token_filter: str | None = None,
    lookback_days: int = 60,
    fw_filter_path: Path | None = None,
) -> dict:
    """Run daily GOM scan from freshwatch CSV store.

    Strategy: re-run chain state from scratch over trailing window per token.
    This is idempotent and avoids state divergence issues.

    S-rules applied (via fw_loader_utils.build_token_days):
      S1: _partial_day → skip Q1 (handled in update_chain)
      S2: _skip_eval   → _false_result() (no eval_gom call)
      S-missing        → _false_result() (break_streak increments naturally)

    Returns all_state dict (also saved to STATE_PATH).
    """
    from fw_loader_utils import (
        taker_scale_check_df, load_fw_csvs,
        load_funding_intervals, build_token_days,
        enrich_token_days, div_avg3,   # M1: canonical ratio-of-means
    )

    if target_date is None:
        target_date = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")

    # ── Load CSV data ─────────────────────────────────────────────────────────
    df_all = load_fw_csvs(store, target_date, lookback_days=lookback_days)
    if df_all.empty:
        print(f"ERROR: no freshwatch CSV data found in {store} up to {target_date}",
              file=sys.stderr)
        sys.exit(1)

    # Apply taker scale check on whole dataset (raise if mixed)
    df_all = taker_scale_check_df(df_all)

    # ── Funding intervals (for S1) ────────────────────────────────────────────
    config_dir = REPO_ROOT / "data" / "config"
    if store.is_dir():
        candidate = store.parent / "config"
        if candidate.exists():
            config_dir = candidate
    intervals = load_funding_intervals(config_dir)

    # ── Symbol list ───────────────────────────────────────────────────────────
    all_symbols = sorted(df_all["symbol"].unique())
    if fw_filter_path and fw_filter_path.exists():
        fw_syms = {l.strip() for l in fw_filter_path.read_text(encoding="utf-8").splitlines() if l.strip()}
        all_symbols = [s for s in all_symbols if s in fw_syms]
        if not all_symbols:
            print(f"ERROR: --fw-filter {fw_filter_path} matched 0 symbols in store", file=sys.stderr)
            sys.exit(1)
    if token_filter:
        # Accept "BANK" → "BANKUSDT", or exact match
        tf = token_filter.upper()
        matched = [s for s in all_symbols
                   if s == tf or s == tf + "USDT" or s.startswith(tf)]
        if not matched:
            print(f"ERROR: no symbols matching '{token_filter}' in store", file=sys.stderr)
            sys.exit(1)
        all_symbols = matched

    date_from = (datetime.strptime(target_date, "%Y-%m-%d")
                 - timedelta(days=lookback_days)).strftime("%Y-%m-%d")
    date_to   = target_date

    # Clamp date_from to actual CSV coverage (avoids synthetic NaN noise from pre-store period)
    if not df_all.empty:
        csv_start = str(df_all["date"].min())
        if csv_start > date_from:
            date_from = csv_start

    # ── Header ────────────────────────────────────────────────────────────────
    print(f"GOM Daily — {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}")
    print(f"Date: {target_date}  Window: {date_from}→{date_to}  "
          f"Symbols: {len(all_symbols)}  Store: {store}")
    print()

    # ── Load existing state (carry over DQ episode fields if any) ─────────────
    all_state = load_state()
    # Capture tokens that were open BEFORE this run — used to filter CLOSED TODAY
    prev_open_tokens: set[str] = {t for t, c in all_state.items() if c.get("chain_open")}

    open_chains:   list[tuple[str, dict, dict | None]] = []  # (token, chain, last_result)
    closed_today:  list[str] = []
    opened_today:  list[str] = []
    smissing_today_summary: list[str] = []  # target_date itself missing → possible race/fresh issue
    smissing_hist_summary:  list[str] = []  # only historical dates missing → normal short-history
    gomc_beta_fires:      list[dict] = []    # GOM-C PROVISIONAL-β fires
    gomc_beta_suppressed: list[dict] = []    # GOM-C tokens in 14d cooldown but otherwise passing

    for sym in all_symbols:
        token = sym[:-4] if sym.endswith("USDT") else sym

        days, suspect_dates = build_token_days(df_all, sym, date_from, date_to, intervals)
        if not days:
            continue
        enrich_token_days(days)

        chain: dict     = {}
        last_result     = None
        prev_open       = False
        event_on_target = False

        for i, d in enumerate(days):
            was_open = chain.get("chain_open", False)
            skip     = d.get("_skip_eval") or d.get("_suspect")

            if skip:
                result = _false_result()
            else:
                result = eval_gom(days, i, cfg, sc)

            chain = update_chain(chain, token, days, i, result, cfg, sc)

            if d.get("date", "") == target_date:
                last_result = result
                event_on_target = (
                    chain.get("chain_open") != was_open  # open↔close transition
                    or (chain.get("chain_open") and result.get("gom_day"))
                )
                # GOM-C β check — display only, no state change
                if not skip:
                    fires_today = _gomc_beta_check(days, i, cfg, sc, result,
                                                   check_cooldown=True)
                    if fires_today:
                        d_now  = days[i]
                        oi_now = d_now.get("oi_usd", math.nan)
                        pos_r  = d_now.get("lsr_pos", math.nan)
                        px_now = d_now.get("avg_px", math.nan)
                        # n_days: consecutive GOM-C β fire days ending today
                        n_ct = 1
                        for j in range(i - 1, -1, -1):
                            dj = days[j]
                            if dj.get("_suspect") or dj.get("_skip_eval"):
                                break
                            rj = eval_gom(days, j, cfg, sc)
                            if _gomc_beta_check(days, j, cfg, sc, rj):
                                n_ct += 1
                            else:
                                break
                        # Q2_net range [INFERENCE]: OI × s_top × (pos_r−1)/(pos_r+1)
                        # Gate (signed rule): div_avg3 ≥ 3 AND lsr_acc(today) ≤ 1
                        # M1: use canonical div_avg3 (ratio-of-means avg3) instead of single-day
                        _div = div_avg3(days, i)   # M1 canonical
                        _lsr_acc_now = d_now.get("lsr_acc", math.nan)
                        _q2_gate = (not math.isnan(_div) and _div >= 3
                                    and not math.isnan(_lsr_acc_now) and _lsr_acc_now <= 1)
                        if _q2_gate and not math.isnan(pos_r) and pos_r > 0 and not math.isnan(oi_now):
                            tilt  = (pos_r - 1) / (pos_r + 1)
                            q2_lo = oi_now * 0.5 * tilt
                            q2_hi = oi_now * 0.8 * tilt
                        else:
                            q2_lo = q2_hi = math.nan
                        # ΔOI_net vs start of consecutive streak
                        first_i  = i - n_ct + 1
                        oi_first = (days[first_i].get("oi_usd", math.nan)
                                    if 0 <= first_i < len(days) else math.nan)
                        doi = (oi_now - oi_first
                               if not (math.isnan(oi_now) or math.isnan(oi_first))
                               else math.nan)
                        # M2: Tier 1 VWAP; fall to Tier 2 if vwap_den=0 or below rep threshold;
                        # Tier 3 fallback: vol-VWAP from GOM-C fire days (covers TUT/CYS no-chain case)
                        _vwap_num   = chain.get("vwap_num", 0.0)
                        _vwap_den   = chain.get("vwap_den", 0.0)
                        _oi_start_c = chain.get("oi_start_usd", 0.0) or 0.0
                        _rep_frac_c = _scfg(sc).get("vwap_t1_min_rep_frac", 0.05)
                        _t1_ok_c    = (_vwap_den > 0
                                       and (_oi_start_c <= 0
                                            or _vwap_den >= _rep_frac_c * _oi_start_c))
                        if _t1_ok_c:
                            _vwap_c    = _vwap_num / _vwap_den
                            _vwap_type = "oi_weighted"
                        else:
                            _vvn = chain.get("vwap_vol_num", 0.0)
                            _vvd = chain.get("vwap_vol_den", 0.0)
                            _vwap_c    = _vvn / _vvd if _vvd > 0 else math.nan
                            _vwap_type = "vol_weighted" if _vvd > 0 else None
                        if math.isnan(_vwap_c):
                            # Tier 3: compute vol-VWAP directly from consecutive GOM-C fire days
                            _c_vn, _c_vd = 0.0, 0.0
                            for _j in range(first_i, i + 1):
                                if 0 <= _j < len(days):
                                    _pj = days[_j].get("avg_px", math.nan)
                                    _vj = days[_j].get("vol_quote", math.nan)
                                    if not math.isnan(_pj) and not math.isnan(_vj) and _vj > 0:
                                        _c_vn += _pj * _vj
                                        _c_vd += _vj
                            if _c_vd > 0:
                                _vwap_c    = _c_vn / _c_vd
                                _vwap_type = "vol_weighted"
                        # M4: gross/net for CAMPAIGN-TRACK
                        _gross = chain.get("Q1_cum_usd", math.nan)
                        _net   = chain.get("net_oi_delta_usd", math.nan)
                        gomc_beta_fires.append({
                            "token": token, "n": n_ct,
                            "q2_lo": q2_lo, "q2_hi": q2_hi,
                            "px": px_now, "doi": doi,
                            "vwap": _vwap_c,
                            "vwap_type": _vwap_type,
                            "gross": _gross, "net": _net,
                        })
                    else:
                        # base conditions (no cooldown check) pass → token is in cooldown
                        base_ok = _gomc_beta_check(days, i, cfg, sc, result,
                                                   check_cooldown=False)
                        if base_ok:
                            first_ff, cd_end, cd_rem = _gomc_c_cooldown_info(
                                days, i, cfg, sc)
                            if first_ff:
                                gomc_beta_suppressed.append({
                                    "token": token, "first_fire": first_ff,
                                    "cooldown_end": cd_end, "days_remaining": cd_rem,
                                })

        all_state[token] = chain

        if suspect_dates:
            entry = (
                f"  {token}: {len(suspect_dates)} suspect/missing date(s) "
                f"({', '.join(suspect_dates[:3])}{'…' if len(suspect_dates) > 3 else ''})"
            )
            if target_date in suspect_dates:
                smissing_today_summary.append(entry)
            else:
                smissing_hist_summary.append(entry)

        if chain.get("chain_open"):
            open_chains.append((token, chain, last_result))
        elif event_on_target:
            closed_today.append(token)

    # Filter CLOSED TODAY to only tokens that were open in the PREVIOUS state.
    # Re-run-from-scratch sees ALL chain events in 60d window; without this filter,
    # tokens that opened+closed in June-July all appear as "closed today" — noise.
    closed_today = [t for t in closed_today if t in prev_open_tokens]

    # ── Output ────────────────────────────────────────────────────────────────
    if open_chains:
        print(f"━━ OPEN CHAINS ({len(open_chains)}) ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        for token, chain, result in open_chains:
            print(format_chain_report(token, chain, result, target_date))
            print()
    else:
        print("(no open chains)")

    if closed_today:
        print(f"\n━━ CLOSED TODAY: {', '.join(closed_today)}")

    if smissing_today_summary:
        print(f"\n━━ S-MISSING TODAY ({len(smissing_today_summary)}) ⚠ target_date absent — check export timing:")
        for s in smissing_today_summary:
            print(s)
    else:
        print(f"\n━━ S-MISSING TODAY: 0 ✓")

    if smissing_hist_summary:
        print(f"\n━━ S-MISSING HIST ({len(smissing_hist_summary)}) — historical only (short history/regen gap, normal):")
        for s in smissing_hist_summary:
            print(s)

    # GOM-C PROVISIONAL-β
    if gomc_beta_fires or gomc_beta_suppressed:
        n_f = len(gomc_beta_fires)
        n_s = len(gomc_beta_suppressed)
        toks      = " ".join(sorted(f["token"] for f in gomc_beta_fires))
        supp_toks = " ".join(sorted(f["token"] for f in gomc_beta_suppressed))
        if n_s:
            print(f"\n━━ GOM-C β ({n_f} fires + {n_s} ⏸ — PROVISIONAL ⚡ sign-off 15/08): "
                  f"{toks}  ⏸{supp_toks}")
        else:
            print(f"\n━━ GOM-C β ({n_f} fires — PROVISIONAL ⚡ sign-off 15/08): {toks}")
        for f in sorted(gomc_beta_fires, key=lambda x: x["token"]):
            q2_s  = (f"${f['q2_lo']/1e6:.1f}-{f['q2_hi']/1e6:.1f}M"
                     if not math.isnan(f["q2_lo"]) else "N/A [ngoài heuristic]")
            _vwap_f = f.get("vwap", math.nan)
            # M2: Tier 2 label when vol-weighted fallback
            _vt = f.get("vwap_type")
            _vwap_tag = "[vw-vol — seat-rotation chain]" if _vt == "vol_weighted" else ""
            vwap_s = (f"${_vwap_f:.5f}{_vwap_tag}"
                      if not math.isnan(_vwap_f) else "N/A")
            px_s  = f"${f['px']:.5f}" if not math.isnan(f["px"]) else "NaN"
            doi_s = (f"{'+' if f['doi'] >= 0 else ''}{f['doi']/1e6:.2f}M"
                     if not math.isnan(f["doi"]) else "NaN")
            # M4: gross/net
            _gross = f.get("gross", math.nan)
            _net   = f.get("net",   math.nan)
            gross_s = (f"${_gross/1e3:.0f}k" if not math.isnan(_gross) and _gross >= 1000
                       else f"${_gross:.0f}" if not math.isnan(_gross) else "N/A")
            net_s   = (f"${_net/1e3:.0f}k"  if not math.isnan(_net)   and abs(_net) >= 1000
                       else f"${_net:.0f}" if not math.isnan(_net) else "N/A")
            if not math.isnan(_gross) and not math.isnan(_net) and _gross > 0:
                if _net <= 0:
                    _churn_tag = " [churn-net<=0]"
                elif _gross > 2 * _net:
                    _churn_tag = " [churn]"
                else:
                    _churn_tag = ""
            else:
                _churn_tag = ""
            print(f"━━ GOM-C β STAT: {f['token']}|n={f['n']}|gross={gross_s}|net={net_s}{_churn_tag}"
                  f"|q2={q2_s}|vwap={vwap_s}|px={px_s}|doi={doi_s}")
        for s in sorted(gomc_beta_suppressed, key=lambda x: x["token"]):
            print(f"━━ GOM-C β SUPP: {s['token']}|cooldown={s['days_remaining']}d"
                  f"|first={s['first_fire']}")
    else:
        print(f"\n━━ GOM-C β: 0 fires")

    print(format_footer(all_state, sc))
    print(f"\n[{len(open_chains)} open / {len(all_symbols)} symbols scanned]")
    print(f"State → {STATE_PATH}")

    return all_state


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="GOM accumulation scanner")
    grp = parser.add_mutually_exclusive_group(required=True)
    grp.add_argument("--backfill",  action="store_true", help="Run on 12 calibration cases")
    grp.add_argument("--daily",     action="store_true", help="Run on daily store CSV")
    grp.add_argument("--backtest6", action="store_true", help="Print §6 gate table")
    parser.add_argument("--token",     help="Filter to single token (--backfill / --daily)")
    parser.add_argument("--store",     help="Path to daily store CSV (--daily only)")
    parser.add_argument("--date",      help="Target date YYYY-MM-DD (--daily, default=latest)")
    parser.add_argument("--fw-filter", help="Path to freshwatch_symbols.txt — restrict --daily to listed symbols")
    args = parser.parse_args()

    # Dependency gate: screen_thresholds.yaml must exist
    if not SCREEN_CFG.exists():
        print(f"ERROR: screen_thresholds.yaml not found: {SCREEN_CFG}", file=sys.stderr)
        sys.exit(1)

    cfg = load_thresholds()
    sc  = load_screen_cfg()

    if args.backfill:
        print(f"GOM Backfill — {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}")
        print(f"Signals: signals.py canonical  |  Thresholds: screen_thresholds.yaml")
        final_state = run_backfill(cfg, sc, token_filter=args.token)
        save_state(final_state)
        print(format_footer(final_state, sc))
        print(f"\nState → {STATE_PATH}")
        # Heartbeat
        HB_PATH.parent.mkdir(parents=True, exist_ok=True)
        HB_PATH.write_text(datetime.now(timezone.utc).isoformat())

    elif args.backtest6:
        cfg = load_thresholds()
        run_backtest6(cfg, sc)

    elif args.daily:
        if not args.store:
            print("ERROR: --daily requires --store <path_to_export_dir_or_csv>",
                  file=sys.stderr)
            sys.exit(1)
        store = Path(args.store)
        if not store.exists():
            print(f"ERROR: store not found: {store}", file=sys.stderr)
            sys.exit(1)
        fw_filter_path = Path(args.fw_filter) if args.fw_filter else None
        final_state = run_daily(cfg, sc, store,
                                target_date=args.date,
                                token_filter=args.token,
                                fw_filter_path=fw_filter_path)
        save_state(final_state)
        HB_PATH.parent.mkdir(parents=True, exist_ok=True)
        HB_PATH.write_text(datetime.now(timezone.utc).isoformat())


if __name__ == "__main__":
    main()
