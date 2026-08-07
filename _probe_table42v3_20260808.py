#!/usr/bin/env python3
"""Probe: Bảng 4.2-v3 — open series + A/B breakdown top-5 chains on opening day.
universe=fw137 @139, date=2026-08-06, gom_scan v1.4 (A3+B4 fail-closed).
"""
import sys, json, math
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from pathlib import Path
import pandas as pd
import yaml

REPO      = Path(__file__).resolve().parent
STATE     = REPO / "data" / "gom_state.json"
FW137_DIR = REPO / "scratch" / "fw137_test"
FW_SYM    = REPO / "scratch" / "freshwatch_symbols.txt"
BOT_ROOT  = Path(r"D:\Data back test\binance-bot-signals")
SCREEN_CFG = REPO / "screen_thresholds.yaml"

sys.path.insert(0, str(BOT_ROOT))
sys.path.insert(0, str(REPO / "scripts"))

from scanner.screener.signals import (
    DayData, load_thresholds,
    lsr_accum, pos_rerate, funding_unpin,
    hedge_structure, funding_pinned, funding_pinned_strong, absorption,
    funding_neg_div,
    dist_wall, lsr_dist, funding_extreme, decay, post_climax,
    crowd_flush,
)
from fw_loader_utils import taker_scale_check_df, load_fw_csvs, load_funding_intervals, build_token_days
# Import fixed gom_scan helpers
from gom_scan import _avg5_glsr, _slope_dq, _a3_slope_ok, load_screen_cfg

with open(STATE, encoding="utf-8") as f:
    state = json.load(f)

fw_list = [l.strip() for l in FW_SYM.read_text(encoding="utf-8").splitlines() if l.strip()]
fw_base = set(s[:-4] if s.endswith("USDT") else s for s in fw_list)

open_chains = {tok: ch for tok, ch in state.items() if ch.get("chain_open") and tok in fw_base}

print(f"universe=fw137@{len(fw_list)}  date=2026-08-06")
print(f"formula=GOM-A: A1 AND A2 AND A3 AND (A4|A5)  |  GOM-B: B1 AND (B2|B3) AND B4")
print(f"A3+B4: FAIL-CLOSED (NaN → False)")
print(f"Total in state: {len(state)}  Open (fw139): {len(open_chains)}")
print()

# ── OPEN SERIES TABLE ────────────────────────────────────────────────────────
print(f"=== OPEN SERIES TABLE ({len(open_chains)} chains) ===")
print(f"{'TOKEN':<16} {'ch':>3} {'n':>4} {'brk':>4} {'start':>12} {'Q1_cum':>14} {'VWAP':>12} {'peak_r':>8}")
print("-" * 80)

sorted_chains = sorted(open_chains.items(), key=lambda x: x[1].get("Q1_cum_usd", 0), reverse=True)

for tok, ch in sorted_chains:
    chap = ch.get("chapter", 1)
    nd   = ch.get("n_days", 0)
    bk   = ch.get("break_streak", 0)
    st   = ch.get("start_date", "?")
    q1   = ch.get("Q1_cum_usd", 0.0)
    vnum = ch.get("vwap_num", 0.0)
    vden = ch.get("vwap_den", 0.0)
    vwap = vnum / vden if vden > 0 else float("nan")
    peak = ch.get("peak_pos_r", float("nan"))
    peak_s = f"{peak:.2f}" if peak == peak else "N/A"
    vwap_s = f"${vwap:.4f}" if vwap == vwap else "N/A"
    flag = " ★" if q1 > 2_000_000 else ""
    print(f"{tok:<16} {chap:>3} {nd:>4} {bk:>4} {st:>12} {q1:>13,.0f}  {vwap_s:>12} {peak_s:>8}{flag}")

print("-" * 80)
big = [t for t, ch in open_chains.items() if ch.get("Q1_cum_usd", 0) > 2_000_000]
print(f"★ Q1>$2M: {', '.join(sorted(big)) if big else 'NONE'}")
print()

# ── A/B BREAKDOWN TOP-5 ──────────────────────────────────────────────────────
print("=== A/B Breakdown — top-5 Q1 chains — ngày mở ===")

with open(SCREEN_CFG, encoding="utf-8") as f:
    sc = yaml.safe_load(f)
cfg = load_thresholds()
intervals = load_funding_intervals(REPO / "data" / "config")

df_all = load_fw_csvs(FW137_DIR, "2026-08-06", lookback_days=60)
df_all = taker_scale_check_df(df_all)
csv_start = str(df_all["date"].min())

def _slope_s(days, i, sc):
    g = sc.get("gom", sc)
    slope_max = g.get("slope_5d_max", 1.15)
    if i < 5:
        return float("nan")
    g0 = days[i-5].get("lsr_global", float("nan"))
    g1 = days[i].get("lsr_global", float("nan"))
    if math.isnan(g0) or math.isnan(g1) or g0 <= 0:
        return float("nan")
    return g1 / g0

top5 = sorted_chains[:5]

for tok, chain in top5:
    sym = tok + "USDT"
    start_date = chain.get("start_date", "")
    q1 = chain.get("Q1_cum_usd", 0.0)
    chap = chain.get("chapter", 1)
    print(f"\n── {tok} ch{chap} (start={start_date}, Q1=${q1:,.0f}) ──")

    if sym not in df_all["symbol"].values:
        print(f"  {sym} not in filtered CSV — skip")
        continue

    date_from = max(csv_start,
        (pd.Timestamp(start_date) - pd.Timedelta(days=20)).strftime("%Y-%m-%d"))
    days, _ = build_token_days(df_all, sym, date_from, "2026-08-06", intervals)

    idx = next((i for i, d in enumerate(days) if d.get("date","") == start_date), None)
    if idx is None:
        print(f"  start_date {start_date} not found in days array")
        continue

    d = days[idx]
    avg5g = _avg5_glsr(days, idx)
    slope = _slope_s(days, idx, sc)
    slope_s = f"{slope:.4f}" if not math.isnan(slope) else "NaN(i<5 or g0 NaN)"

    print(f"  Date: {start_date}")
    print(f"  lsr_pos={d.get('lsr_pos', float('nan')):.3f}  lsr_acc={d.get('lsr_acc', float('nan')):.3f}  lsr_global={d.get('lsr_global', float('nan')):.3f}")
    print(f"  avg_px={d.get('avg_px', float('nan')):.4f}  oi_usd={d.get('oi_usd', 0):,.0f}  taker_buy_pct={d.get('taker_buy_pct', float('nan')):.2f}")
    print(f"  funding_avg={d.get('funding_avg', float('nan')):.6f}  funding_n={d.get('funding_n', 'N/A')}  _partial={d.get('_partial_day', False)}")
    print(f"  avg5gLSR={avg5g:.3f}  slope_5d={slope_s}")

    g = sc.get("gom", sc)
    hl = g.get("hedge_lookback_days", 7)

    a1 = lsr_accum(days, idx, cfg)
    a2 = _avg5_glsr(days, idx) <= 1.1
    a3 = _a3_slope_ok(days, idx, sc)
    slope_dq_val = _slope_dq(days, idx, sc)

    hedge_alive = any(hedge_structure(days, j, cfg) for j in range(max(0, idx-hl+1), idx+1))
    a4 = pos_rerate(days, idx, cfg) and hedge_alive
    a5 = funding_unpin(days, idx, cfg)
    gom_a_fire = a1 and a2 and a3 and (a4 or a5)

    b1 = all(hedge_structure(days, j, cfg) for j in range(max(0, idx-hl+1), idx+1))
    b2 = funding_pinned(days, idx, cfg) or funding_pinned_strong(days, idx, cfg)
    b3 = absorption(days, idx, cfg)
    _f_avg = d.get("funding_avg", float("nan"))
    b4 = (not math.isnan(_f_avg)) and not funding_neg_div(days, idx, cfg)
    gom_b_fire = b1 and (b2 or b3) and b4

    print(f"  GOM-A: A1={a1} A2={a2}(avg5g={avg5g:.3f}) A3={a3}(slope={slope_s}, dq={slope_dq_val}) A4={a4} A5={a5}  FIRE={gom_a_fire}")
    print(f"  GOM-B: B1={b1} B2={b2} B3={b3} B4={b4}(funding_avg={'NaN' if math.isnan(_f_avg) else f'{_f_avg:.6f}'})  FIRE={gom_b_fire}")

    dq = {
        "dist_wall": dist_wall(days, idx, cfg),
        "lsr_dist": lsr_dist(days, idx, cfg),
        "f_neg_div": funding_neg_div(days, idx, cfg),
        "f_extreme": funding_extreme(days, idx, cfg),
        "decay": decay(days, idx, cfg),
        "post_climax": post_climax(days, idx, cfg),
    }
    fired_supp = [k for k, v in dq.items() if v]
    print(f"  SUPP: {fired_supp if fired_supp else 'CLEAN'}")
    print(f"  CF={crowd_flush(days, idx, cfg)}  perday_slope_dq={slope_dq_val}")

print()
print("=== DỪNG — duyệt bảng 4.2-v3 ===")
