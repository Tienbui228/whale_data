#!/usr/bin/env python3
"""gom_scan.py — GOM accumulation screen (gom_detect_spec.md v1.1)

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

import importlib.util
_replay_spec = importlib.util.spec_from_file_location("replay", BOT_ROOT / "replay.py")
_replay_mod  = importlib.util.module_from_spec(_replay_spec)
_replay_spec.loader.exec_module(_replay_mod)
parse_result_file = _replay_mod.parse_result_file
build_days        = _replay_mod.build_days

CASE_DIR = BOT_ROOT / "docs" / "case study"

# ── Config paths ─────────────────────────────────────────────────────────────
REPO_ROOT   = Path(__file__).resolve().parent.parent
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

# ── GOM-A/B evaluation ───────────────────────────────────────────────────────

def eval_gom(days: list[DayData], i: int, cfg: dict, sc: dict) -> dict:
    """Evaluate GOM conditions for day i. Returns result dict."""
    g = _scfg(sc)
    hedge_lb = g.get("hedge_lookback_days", 7)

    # GOM-A signals
    a1 = lsr_accum(days, i, cfg)
    a2 = stealth_grind(days, i, cfg)
    a3 = s3_eve(days, i, cfg)
    # A4: pos_rerate + hedge_structure alive in hedge_lb days
    hedge_alive = any(
        hedge_structure(days, j, cfg)
        for j in range(max(0, i - hedge_lb + 1), i + 1)
    )
    a4 = pos_rerate(days, i, cfg) and hedge_alive
    a5 = funding_unpin(days, i, cfg)

    gom_a = {"A1": a1, "A2": a2, "A3": a3, "A4": a4, "A5": a5}
    any_a  = any(gom_a.values())

    # GOM-B signals
    b1 = hedge_structure(days, i, cfg)
    b2 = funding_pinned(days, i, cfg) or funding_pinned_strong(days, i, cfg)
    b3 = absorption(days, i, cfg)
    b4 = oi_ignition(days, i, cfg)
    gom_b = {"B1": b1, "B2": b2, "B3": b3, "B4": b4}
    b_count = sum(gom_b.values())

    gom_b_min = g.get("gom_b_min_count", 2)

    # Disqualifiers
    dq = {
        "dist_wall":        dist_wall(days, i, cfg),
        "lsr_dist":         lsr_dist(days, i, cfg),
        "funding_neg_div":  funding_neg_div(days, i, cfg),
        "funding_extreme":  funding_extreme(days, i, cfg),
        "decay":            decay(days, i, cfg),
        "post_climax":      post_climax(days, i, cfg),
    }
    any_dq = any(dq.values())

    # Auxiliary flags
    d = days[i]
    vol_q   = d.get("vol_quote", float("nan"))
    oi      = d.get("oi_usd", float("nan"))
    lc = (not math.isnan(vol_q) and vol_q < g.get("vol_low_conf_usd", 200_000)) or \
         (not math.isnan(oi)    and oi    < g.get("oi_low_conf_usd",  1_000_000))

    cf_today = crowd_flush(days, i, cfg)

    gom_day = (any_a or b_count >= gom_b_min) and not any_dq

    return {
        "gom_day":      gom_day,
        "gom_a":        gom_a,
        "gom_b":        gom_b,
        "disqualifier": dq,
        "any_dq":       any_dq,
        "low_conf":     lc,
        "crowd_flush":  cf_today,
    }


def _ret_1d(days: list[DayData], i: int) -> float:
    """1-day price return: (today.avg_px - prev.avg_px) / prev.avg_px."""
    if i == 0:
        return float("nan")
    p_prev = days[i-1].get("avg_px", float("nan"))
    p_now  = days[i].get("avg_px",  float("nan"))
    if math.isnan(p_prev) or math.isnan(p_now) or p_prev <= 0:
        return float("nan")
    return (p_now - p_prev) / p_prev


# ── Chain state machine ───────────────────────────────────────────────────────

def _empty_chain(date_str: str) -> dict:
    return {
        "chain_open":    True,
        "start_date":    date_str,
        "chapter":       1,
        "Q1_cum_usd":    0.0,
        "vwap_num":      0.0,   # Σ ΔOI⁺ × avg_px
        "vwap_den":      0.0,   # Σ ΔOI⁺
        "n_days":        0,
        "peak_pos_r":    float("nan"),
        "break_streak":  0,
        "last_gom_date": date_str,
        "chapter_hist":  [],
        "suspect_flag":  False,
        "updated_at":    "",
    }


def _close_chain(st: dict, reason: str, date_str: str) -> dict:
    st["chain_open"] = False
    st["close_date"] = date_str
    st["close_reason"] = reason
    return st


def _new_chapter(st: dict, date_str: str) -> dict:
    """Archive current chapter, start fresh Q1 accumulation (VWAP preserved per §8.2)."""
    vwap_current = (st["vwap_num"] / st["vwap_den"]) if st["vwap_den"] > 0 else float("nan")
    st["chapter_hist"].append({
        "chapter":  st["chapter"],
        "start":    st["start_date"],
        "end":      date_str,
        "vwap":     vwap_current,
        "Q1_cum":   st["Q1_cum_usd"],
    })
    st["chapter"]      += 1
    st["start_date"]   = date_str
    st["Q1_cum_usd"]   = 0.0
    st["vwap_num"]     = 0.0
    st["vwap_den"]     = 0.0
    st["n_days"]       = 0
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

    gom = result["gom_day"]
    dq  = result["any_dq"]
    cf  = result["crowd_flush"]

    # Initialise state if empty
    if not state:
        state = {}

    chain = state  # top-level dict is the chain (we pass token's chain state)

    # ── Rule (i): disqualifier = reset/close ─────────────────────────────────
    if dq:
        if chain.get("chain_open"):
            fired = [k for k, v in result["disqualifier"].items() if v]
            state = _close_chain(chain, f"disqualifier:{'+'.join(fired)}", date_str)
        return state

    # ── If no GOM and chain open: break_streak logic ─────────────────────────
    if not gom:
        if chain.get("chain_open"):
            chain["break_streak"] = chain.get("break_streak", 0) + 1
            if chain["break_streak"] > g.get("break_gap_max", 2):
                # ── Rule (iii): gap >2d → close ──────────────────────────────
                state = _close_chain(chain, "gom_gap>2d", date_str)
        return state

    # ── GOM fires today ───────────────────────────────────────────────────────

    # Open new chain if none open
    if not chain.get("chain_open", False):
        state = _empty_chain(date_str)
        chain = state

    chain["break_streak"] = 0
    chain["last_gom_date"] = date_str

    # ── Rule (ii): crowd_flush → new chapter ────────────────────────────────
    if cf and chain.get("n_days", 0) > 0:
        state = _new_chapter(chain, date_str)
        chain = state

    # ── Update peak pos_r ────────────────────────────────────────────────────
    pos_r = d.get("lsr_pos", float("nan"))
    if math.isnan(pos_r):
        pos_r = d.get("lsr_pos_r", float("nan"))
    if not math.isnan(pos_r):
        peak = chain.get("peak_pos_r", float("nan"))
        if math.isnan(peak) or pos_r > peak:
            chain["peak_pos_r"] = pos_r

    # ── Rule (iv): pos_r sập ≥30% từ peak → close immediately ──────────────
    peak = chain.get("peak_pos_r", float("nan"))
    if not math.isnan(peak) and not math.isnan(pos_r) and peak > 0:
        drop = (peak - pos_r) / peak
        if drop >= g.get("pos_r_drop_close", 0.30):
            state = _close_chain(chain, f"pos_r_drop:{drop:.0%}_from_peak:{peak:.2f}", date_str)
            state["close_note"] = "chuyển pha phân phối"
            return state

    # ── Q1 counting ──────────────────────────────────────────────────────────
    ret = _ret_1d(days, i)
    ret_max = g.get("ret_1d_max", 0.01)
    counts_q1 = not math.isnan(ret) and ret <= ret_max

    if counts_q1:
        # ΔOI⁺ = max(OI_today - OI_prev, 0)
        oi_now  = d.get("oi_usd", float("nan"))
        oi_prev = days[i-1].get("oi_usd", float("nan")) if i > 0 else float("nan")
        if not math.isnan(oi_now) and not math.isnan(oi_prev):
            delta_oi = max(oi_now - oi_prev, 0.0)
        else:
            delta_oi = 0.0

        chain["Q1_cum_usd"] = chain.get("Q1_cum_usd", 0.0) + delta_oi
        chain["n_days"]     = chain.get("n_days", 0) + 1

        # VWAP: ΔOI⁺-weighted
        px = d.get("avg_px", float("nan"))
        if not math.isnan(px) and delta_oi > 0:
            chain["vwap_num"] = chain.get("vwap_num", 0.0) + delta_oi * px
            chain["vwap_den"] = chain.get("vwap_den", 0.0) + delta_oi
        elif not math.isnan(px) and delta_oi == 0 and g.get("vwap_fallback_seats", True):
            # fallback vol-weighted for seat-rotation days
            vol = d.get("vol_quote", float("nan"))
            if not math.isnan(vol) and vol > 0:
                chain["vwap_num"] = chain.get("vwap_num", 0.0) + vol * px
                chain["vwap_den"] = chain.get("vwap_den", 0.0) + vol
                chain.setdefault("vwap_fallback_used", True)

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
        lines.append(f"══ {token} ══ CHAIN CLOSED ({closed}) reason={reason}")
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

    q1    = chain.get("Q1_cum_usd", 0.0)
    vnum  = chain.get("vwap_num", 0.0)
    vden  = chain.get("vwap_den", 0.0)
    vwap  = vnum / vden if vden > 0 else float("nan")

    # ΔOI_net
    lines.append(f"")
    lines.append(f" Q1_cum:  ${q1:>12,.0f}  (ΔOI⁺-weighted)")
    if not math.isnan(vwap):
        fb_tag = " [vol-weighted fallback]" if chain.get("vwap_fallback_used") else ""
        lines.append(f" VWAP_gom: ${vwap:.6f}{fb_tag}  [chương hiện tại]")

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
        "ZBT: DELISTED (alpha endpoint 400, không có data)",
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
    ("BANK",   "open",    "Chain mở 06-29 (lsr_accum onset)"),
    ("BANK",   "chapter", "crowd_flush 07-02 → chapter mới"),
    ("BANK",   "close-iv","Chain ĐÓNG 07-19~21 (pos_r sập ≥30% từ peak), KHÔNG sống 07-24"),
    ("TAG",    "open",    "Chain mở 07-12 (lsr_accum + crowd_flush)"),
    ("BAS",    "SUPP",    "07-02→07-15: post_climax → disqualifier → GOM không fire"),
    ("BTW",    "SUPP",    "06-21→07-05: post_climax → disqualifier → GOM không fire"),
    ("BULLA",  "open",    "stealth_grind 07-17 → GOM-A fires (A2)"),
    ("TUT",    "chapter", "07-11: stealth_grind + crowd_flush → chapter mới"),
    ("IDOL",   "open",    "07-06: lsr_accum + pos_rerate → GOM-A fires (A1+A4)"),
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


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="GOM accumulation scanner")
    grp = parser.add_mutually_exclusive_group(required=True)
    grp.add_argument("--backfill",  action="store_true", help="Run on 12 calibration cases")
    grp.add_argument("--daily",     action="store_true", help="Run on daily store CSV")
    grp.add_argument("--backtest6", action="store_true", help="Print §6 gate table")
    parser.add_argument("--token",  help="Filter to single token (--backfill only)")
    parser.add_argument("--store",  help="Path to daily store CSV (--daily only)")
    parser.add_argument("--date",   help="Target date YYYY-MM-DD (--daily, default=latest)")
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
            print("ERROR: --daily requires --store <path>", file=sys.stderr)
            sys.exit(1)
        store = Path(args.store)
        if not store.exists():
            print(f"ERROR: store not found: {store}", file=sys.stderr)
            sys.exit(1)
        print("--daily mode: not yet implemented (awaiting VPS daily CSV path)", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
