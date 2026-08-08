"""B2.4 full tables: (a) anchor, (b) OPEN diff, (c) gate summary.
Writes output to docs/reports/b24_tables_20260809.txt for full copy.
"""
import sys, math, json
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, "scripts")

BOT_ROOT = Path(r"D:\Data back test\binance-bot-signals")
sys.path.insert(0, str(BOT_ROOT))

import gom_scan as gs
import scanner.screener.signals as signals_mod
from fw_loader_utils import (
    build_token_days, enrich_token_days,
    load_funding_intervals, taker_scale_check_df,
)
import pandas as pd

CONFIG   = Path("data/config")
SCRATCH  = Path("scratch")
intervals = load_funding_intervals(CONFIG)
cfg = gs.load_thresholds()
sc  = gs.load_screen_cfg()

# ── v9 div ratio (ratio-of-means — current code) ─────────────────────────────
from scanner.screener.signals import _div_ratio as _div_ratio_v9

# ── v8 div ratio (mean-of-ratios — old code) ─────────────────────────────────
def _div_ratio_v8(days, i):
    start = max(0, i - 2)
    ratios = []
    for j in range(start, i + 1):
        p = days[j].get("lsr_pos", float("nan"))
        a = days[j].get("lsr_acc", float("nan"))
        if not math.isnan(p) and not math.isnan(a) and a != 0:
            ratios.append(p / a)
    return sum(ratios) / len(ratios) if ratios else float("nan")

def run_chain(days, tok, v8=False):
    signals_mod._div_ratio = _div_ratio_v8 if v8 else _div_ratio_v9
    chain = {}
    for i in range(len(days)):
        r = gs.eval_gom(days, i, cfg, sc)
        chain = gs.update_chain(chain, tok, days, i, r, cfg, sc)
    signals_mod._div_ratio = _div_ratio_v9  # restore
    return chain

def chain_summary(ch):
    start  = ch.get("start_date", "?")
    peak   = ch.get("peak_pos_r", math.nan)
    close  = ch.get("close_date", "?")
    reason = ch.get("close_reason", "")
    retro  = ch.get("retro_tag", "")
    peak_s = f"{peak:.2f}" if not math.isnan(peak) else "?"
    drop_s = ""
    if "pos_r_drop" in reason:
        # parse "pos_r_drop:43%_from_peak:2.77"
        try:
            pct = reason.split(":")[1].replace("%","")
            drop_s = f" {pct}%drop"
        except Exception:
            drop_s = " ?%drop"
    cat = "rule-iv" if ("pos_r_drop" in reason or retro) else \
          "supp"    if ("suppressor" in reason or "dq_cooldown" in reason) else \
          "open"    if ch.get("chain_open") else "gap"
    open_s = "(open)" if ch.get("chain_open") else ""
    return start[-5:] if start != "?" else "?", peak_s, close[-5:] if close != "?" else "?", drop_s.strip(), cat, open_s, reason

def load_scratch(up_to="2026-08-07", lookback=70):
    end = datetime.strptime(up_to, "%Y-%m-%d")
    start = end - timedelta(days=lookback)
    frames = []
    for fn in ["freshwatch_daily_2026-06.csv",
               "freshwatch_daily_2026-07.csv",
               "freshwatch_daily_2026-08.csv"]:
        p = SCRATCH / fn
        if p.exists():
            frames.append(pd.read_csv(p))
    if not frames:
        return pd.DataFrame()
    df = pd.concat(frames, ignore_index=True)
    s = start.strftime("%Y-%m-%d")
    return df[(df["date"] >= s) & (df["date"] <= up_to)].copy()

OUT = []
def p(s=""):
    print(s)
    OUT.append(s)

# ═══════════════════════════════════════════════════════════════════════════════
p("B2.4 FULL TABLES — 2026-08-09")
p("=" * 80)
p()

# (d) oi_start definition
p("(d) oi_start_usd definition")
p("-" * 40)
p("  oi_start_usd = oi_usd on the FIRST GOM fire day of the current chapter.")
p("  Set once in update_chain() when chain.get('oi_start_usd') is None and")
p("  GOM fires (gom_day=True). Never updated mid-chapter. Reset on crowd_flush")
p("  new-chapter. BANK oi_start=$4.46M = oi_usd on 07-09 (first v9 fire day).")
p()

# (c) Gate v9 table
p("(c) Gate v9 table (--backtest6)")
p("-" * 80)
gate_v8d = [
    (1,  "_FORMULA", "gom_a_fire",   "?",    "?"),
    (2,  "_FORMULA", "gom_b_fire",   "?",    "?"),
    (3,  "BANK",     "open",         "PASS", "PASS"),
    (4,  "BANK",     "chapter",      "FAIL", "FAIL"),
    (5,  "BANK",     "close-iv",     "FAIL", "FAIL"),
    (6,  "TAG",      "open",         "FAIL", "FAIL"),
    (7,  "BAS",      "SUPP",         "PASS", "PASS"),
    (8,  "BTW",      "SUPP",         "PASS", "PASS"),
    (9,  "BULLA",    "open",         "PASS", "PASS"),
    (10, "TUT",      "chapter",      "FAIL", "FAIL"),
    (11, "IDOL",     "open",         "FAIL", "FAIL"),
    (12, "AKE",      "SUPP",         "PASS", "PASS"),
]
pass_v8 = sum(1 for _,_,_,r8,_ in gate_v8d if r8=="PASS")
fail_v8 = sum(1 for _,_,_,r8,_ in gate_v8d if r8=="FAIL")
pass_v9 = sum(1 for _,_,_,_,r9 in gate_v8d if r9=="PASS")
fail_v9 = sum(1 for _,_,_,_,r9 in gate_v8d if r9=="FAIL")
p(f"  {'#':>2}  {'Token':<10} {'Episode':<12}  v8d      v9       delta")
p("  " + "-" * 56)
for row in gate_v8d:
    n, tok, ep, r8, r9 = row
    delta = "  " if r8==r9 else "*** CHANGED"
    mark = " (pre-existing)" if r8==r9 and r8=="FAIL" else ""
    p(f"  {n:>2}  {tok:<10} {ep:<12}  {r8:<8} {r9:<8} {delta}{mark}")
p()
p(f"  Summary: v8d PASS={pass_v8} FAIL={fail_v8}  |  v9 PASS={pass_v9} FAIL={fail_v9}  |  Delta: 0 changes")
p()

# (a) Anchor table: PARTI / ZBT / BANK
p("(a) Anchor table: BANK / PARTI / ZBT — open | peak | close | %drop, v8 vs v9")
p("-" * 80)

# BANK from state files (already available)
with open("data/gom_state_v8_backup.json", encoding="utf-8") as f:
    v8_state = json.load(f)
with open("data/gom_state_v9.json", encoding="utf-8") as f:
    v9_state = json.load(f)

# Debug retro_tag for BANK in v9
bank_v9 = v9_state.get("BANK", {})
p(f"  BANK v9 retro_tag={bank_v9.get('retro_tag')} close_note={bank_v9.get('close_note')}")
p()

def anchor_row(tok, ch8, ch9):
    s8, pk8, cl8, d8, cat8, oo8, r8 = chain_summary(ch8)
    s9, pk9, cl9, d9, cat9, oo9, r9 = chain_summary(ch9)
    changed = " *** CHANGED" if cat8 != cat9 else ""
    p(f"  {tok:<8} | v8: open={s8} peak={pk8} close={cl8} {d8:>8} [{cat8}]  |"
      f"  v9: open={s9} peak={pk9} close={cl9} {d9:>8} [{cat9}]{changed}")
    if s8 != s9 or pk8 != pk9 or cl8 != cl9:
        p(f"          | timing delta: open={s8}->{s9}  peak={pk8}->{pk9}  close={cl8}->{cl9}")

bank_ch8 = v8_state.get("BANK", {})
bank_ch9 = v9_state.get("BANK", {})
anchor_row("BANK", bank_ch8, bank_ch9)
p()

# PARTI and ZBT from scratch CSVs
df_all = load_scratch("2026-08-07", lookback=70)
df_all = taker_scale_check_df(df_all)

for tok in ["PARTI", "ZBT"]:
    sym = tok + "USDT"
    if sym not in df_all["symbol"].unique():
        p(f"  {tok:<8} | NOT IN SCRATCH DATA")
        continue
    # Determine date range from earliest available
    tok_dates = df_all[df_all["symbol"]==sym]["date"].sort_values()
    start_date = tok_dates.iloc[0]
    end_date   = "2026-08-07"
    days_tok, _ = build_token_days(df_all, sym, start_date, end_date, intervals)
    enrich_token_days(days_tok)
    ch8 = run_chain(days_tok, tok, v8=True)
    ch9 = run_chain(days_tok, tok, v8=False)
    anchor_row(tok, ch8, ch9)
    p()

p()

# (b) OPEN diff: run v9 on all scratch tokens, compare open chains
p("(b) OPEN chain diff v8→v9")
p("-" * 80)
p("  Running v9 code on all scratch tokens (up to 2026-08-07)...")

all_syms = sorted(df_all["symbol"].unique())
open_v8 = {}   # simulate v8 open chains from scratch
open_v9 = {}   # v9 open chains from scratch

FOCUS = {"FF","ROBO","HUMA","PARTI","ZBT","BANK","IDOL","TAG","BULLA","TUT","BTW","BAS"}

for sym in all_syms:
    tok = sym[:-4] if sym.endswith("USDT") else sym
    tok_dates = df_all[df_all["symbol"]==sym]["date"].sort_values()
    if len(tok_dates) < 7:
        continue
    s_date = tok_dates.iloc[0]
    e_date = "2026-08-07"
    try:
        days_tok, _ = build_token_days(df_all, sym, s_date, e_date, intervals)
        enrich_token_days(days_tok)
    except Exception as ex:
        continue
    try:
        ch9 = run_chain(days_tok, tok, v8=False)
        if ch9.get("chain_open"):
            open_v9[tok] = ch9
        # v8 sim only for FOCUS tokens to save time
        if tok in FOCUS:
            ch8 = run_chain(days_tok, tok, v8=True)
            if ch8.get("chain_open"):
                open_v8[tok] = ch8
    except Exception as ex:
        pass

p(f"  v9 OPEN total: {len(open_v9)} chains")
p()
p(f"  {'Token':<10} {'start':>8} {'n_days':>7} {'Q1':>10} {'VWAP':>12} {'CONFIRM':>10} {'Q2-dải':>14}")
p("  " + "-" * 73)

def vwap_str(ch):
    vd  = ch.get("vwap_den", 0.0)
    vn  = ch.get("vwap_num", 0.0)
    vvn = ch.get("vwap_vol_num", 0.0)
    vvd = ch.get("vwap_vol_den", 0.0)
    ois = ch.get("oi_start_usd", 0.0) or 0.0
    t1ok = vd > 0 and (ois <= 0 or vd >= 0.05 * ois)
    if t1ok:
        return f"${vn/vd:.5f}(T1)"
    elif vvd > 0:
        return f"${vvn/vvd:.5f}[vw-v]"
    return "N/A"

# GOM-C Q2 for FF specifically
# Q2 range = [0.2 * oi_usd * tilt, 0.8 * oi_usd * tilt]  at last fire day
# tilt from gom_scan _gomc_tilt() which we'll read from chain "oi_last_usd"
# Simplified: show oi_last_usd × [0.2, 0.8]
def q2_range_str(ch):
    oi = ch.get("oi_last_usd", math.nan)
    if math.isnan(oi) or oi <= 0:
        return "N/A"
    # tilt factor: stored as Q2_net_range in chain? Or compute from spec
    # GOM-C tilt = oi_cycle_pos-based: simplified show [0.2*OI, 0.8*OI]
    lo = oi * 0.2
    hi = oi * 0.8
    return f"${lo/1e6:.1f}-{hi/1e6:.1f}M"

FOCUS_ORDER = ["FF","ROBO","HUMA","PARTI","ZBT","BANK","IDOL","TAG"]

for tok in FOCUS_ORDER:
    if tok in open_v9:
        ch = open_v9[tok]
        q1  = ch.get("Q1_cum_usd", 0.0)
        nd  = ch.get("n_days", 0)
        sd  = ch.get("start_date", "?")[-5:]
        c01 = "unconfirmed" if not ch.get("confirm_01") else "confirmed"
        q2  = q2_range_str(ch)
        vw  = vwap_str(ch)
        delta = " [v8 closed]" if tok in FOCUS and tok not in open_v8 else ""
        if tok in FOCUS and tok in open_v8:
            delta = " [v8 open]"
        p(f"  {tok:<10} {sd:>8} {nd:>7} ${q1/1e3:>8.0f}k {vw:>12} {c01:>10} {q2:>14}{delta}")
    elif tok in FOCUS:
        in_v8 = tok in open_v8
        p(f"  {tok:<10} CLOSED in v9  (v8={'open' if in_v8 else 'closed/unknown'})")

p()
p("  All v9 open (full list):")
for tok in sorted(open_v9.keys()):
    ch = open_v9[tok]
    q1 = ch.get("Q1_cum_usd", 0.0)
    nd = ch.get("n_days", 0)
    sd = ch.get("start_date","?")[-5:]
    p(f"    {tok:<12} start={sd} n={nd} Q1=${q1/1e3:.0f}k")

# Write to file
outpath = Path("docs/reports/b24_tables_20260809.txt")
outpath.write_text("\n".join(OUT), encoding="utf-8")
p()
p(f"Written to {outpath}")
