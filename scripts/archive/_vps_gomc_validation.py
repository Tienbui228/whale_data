#!/usr/bin/env python3
# GOM-C data validation -- G1-G6. ANALYSIS ONLY, no state changes.
import sys, math, json
from pathlib import Path
from datetime import datetime, timedelta

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

REPO     = Path('/root/Data_back_test/whale_data')
BOT_ROOT = Path('/root/Data_back_test/binance-bot-signals')
sys.path.insert(0, str(REPO / 'scripts'))
sys.path.insert(0, str(BOT_ROOT))

from scanner.screener.signals import (
    load_thresholds, lsr_accum, stealth_grind,
    funding_pinned, funding_pinned_strong, absorption,
    funding_neg_div,
)
from gom_scan import (eval_gom, load_screen_cfg, _scfg, _false_result,
                      _slope_dq, _a3_slope_ok, _avg5_glsr)
from fw_loader_utils import (taker_scale_check_df, load_fw_csvs,
                             load_funding_intervals, build_token_days)

cfg = load_thresholds()
sc  = load_screen_cfg()
g   = _scfg(sc)

STORE      = REPO / 'data' / 'export'
CONFIG_DIR = REPO / 'data' / 'config'
intervals  = load_funding_intervals(CONFIG_DIR)
STATE      = REPO / 'data' / 'gom_state.json'

def load_days(sym, target_date, lb=60):
    df = load_fw_csvs(STORE, target_date, lookback_days=lb)
    if df.empty: return [], []
    df = taker_scale_check_df(df)
    d_to = target_date
    d_fr_dt = datetime.strptime(target_date, "%Y-%m-%d") - timedelta(days=lb)
    d_fr = max(d_fr_dt.strftime("%Y-%m-%d"), str(df["date"].min()))
    return build_token_days(df, sym, d_fr, d_to, intervals)

def nan_s(v, fmt=".3f"): return f"{v:{fmt}}" if not math.isnan(v) else "NaN"
def bool_s(v): return "T" if v else "."

# GOM-C condition checkers (per-day)
def c1_sg(days, i): return stealth_grind(days, i, cfg)
def c2_fp(days, i): return funding_pinned(days, i, cfg) or funding_pinned_strong(days, i, cfg)
def c3_taker(days, i):
    return absorption(days, i, cfg)
def c3_loose(days, i):
    # Loose: taker_buy_pct in [40, 55] at least 5 of last 7 days
    takers = [days[j].get("taker_buy_pct", math.nan)
              for j in range(max(0,i-6), i+1)]
    takers = [t for t in takers if not math.isnan(t)]
    ok = [40 <= t <= 55 for t in takers]
    return sum(ok) >= 5
def c4_slope(days, i): return _a3_slope_ok(days, i, sc)  # gLSR slope <= 1.15
def d_pos(days, i):
    if i == 0: return math.nan
    p_now  = days[i].get("lsr_pos_r", math.nan) or days[i].get("lsr_pos", math.nan)
    p_prev = days[i-1].get("lsr_pos_r", math.nan) or days[i-1].get("lsr_pos", math.nan)
    if math.isnan(p_now) or math.isnan(p_prev): return math.nan
    return p_now - p_prev

def gomc_draft(days, i):
    # GOM-C draft: C1 AND C2 AND C4 AND NOT supp_dq (C3 informational)
    skip = days[i].get("_skip_eval") or days[i].get("_suspect")
    if skip: return False, False
    res = eval_gom(days, i, cfg, sc)
    any_supp = any(v for k, v in res.get("supp_dq", {}).items())
    c1 = c1_sg(days, i)
    c2 = c2_fp(days, i)
    c4 = c4_slope(days, i)
    fired = c1 and c2 and c4 and not any_supp
    return fired, any_supp

print("=" * 85)
print("GOM-C DATA VALIDATION -- G1 through G6")
print("=" * 85)

# ---------------------------------------------------------------------------
# G1: TUT 13-23/07 -- verify 4 conditions C per-day
# ---------------------------------------------------------------------------
print("\n" + "-"*85)
print("G1 -- TUT (TUTUSDT) 2026-07-13 to 2026-07-23: verify GOM-C conditions")
print("-"*85)

days_tut, _ = load_days("TUTUSDT", "2026-07-23")
if days_tut:
    print(f"  {'Date':<12} {'px':<9} {'tkr%':<6} {'f_avg':>7} {'OI_M':>6} "
          f"{'pos_r':>6} {'gLSR':>5} {'Dpos':>6} "
          f"{'C1_SG':<6} {'C2_FP':<6} {'C3_abs':<7} {'C3_lax':<7} {'C4_slp':<7} {'GOMC':<6} SUPP")
    print(f"  {'-'*120}")
    for i, d in enumerate(days_tut):
        date = d.get("date","")
        if date < "2026-07-13" or date > "2026-07-23": continue
        if d.get("_suspect"):
            print(f"  {date:<12} [SUSPECT]"); continue
        px   = d.get("px_avg", math.nan)
        tkr  = d.get("taker_buy_pct", math.nan)
        favg = d.get("funding_avg", math.nan)
        oi   = d.get("oi_usd", math.nan)
        pr   = d.get("lsr_pos_r", math.nan) or d.get("lsr_pos", math.nan)
        glsr = d.get("lsr_global_r", math.nan)
        dp   = d_pos(days_tut, i)
        c1   = bool_s(c1_sg(days_tut, i))
        c2   = bool_s(c2_fp(days_tut, i))
        c3a  = bool_s(c3_taker(days_tut, i))
        c3l  = bool_s(c3_loose(days_tut, i))
        c4   = bool_s(c4_slope(days_tut, i))
        gc, supp = gomc_draft(days_tut, i)
        tkr_pct = tkr*100 if not math.isnan(tkr) else math.nan
        favg_pct = favg*100 if not math.isnan(favg) else math.nan
        oi_m = oi/1e6 if not math.isnan(oi) else math.nan
        print(f"  {date:<12} {nan_s(px,'<9.5f')} {nan_s(tkr_pct,'>5.1f')}% "
              f"{nan_s(favg_pct,'>7.4f')}% "
              f"{nan_s(oi_m,'>6.1f')}M "
              f"{nan_s(pr,'>6.3f')} {nan_s(glsr,'>5.3f')} {nan_s(dp,'>+6.3f')} "
              f"{c1:<6} {c2:<6} {c3a:<7} {c3l:<7} {c4:<7} {'GOM-C' if gc else '     ':<6} {'SUPP' if supp else ''}")
else:
    print("  TUT: no data")

# ---------------------------------------------------------------------------
# G2: BANANAS31 -- negative test (serial pumps)
# ---------------------------------------------------------------------------
print("\n" + "-"*85)
print("G2 -- BANANAS31 (BANANAS31USDT): negative test -- serial pump periods")
print("-"*85)

days_ban, _ = load_days("BANANAS31USDT", "2026-08-07")
if days_ban:
    print(f"  {'Date':<12} {'px':<9} {'Dpx%':>6} {'tkr%':<6} {'f_avg':>7} "
          f"{'pos_r':>6} {'gLSR':>5} {'Dpos':>6} "
          f"{'C1':<4} {'C2':<4} {'C4':<4} {'GOM-C':<6} {'SUPP':<5} flag")
    print(f"  {'-'*110}")
    prev_px = math.nan
    for i, d in enumerate(days_ban):
        date = d.get("date","")
        if date < "2026-07-01": prev_px = d.get("px_avg", math.nan); continue
        if d.get("_suspect"):
            print(f"  {date:<12} [SUSPECT]"); prev_px = math.nan; continue
        px   = d.get("px_avg", math.nan)
        tkr  = d.get("taker_buy_pct", math.nan)
        favg = d.get("funding_avg", math.nan)
        pr   = d.get("lsr_pos_r", math.nan) or d.get("lsr_pos", math.nan)
        glsr = d.get("lsr_global_r", math.nan)
        dp   = d_pos(days_ban, i)
        dpx_pct = (px - prev_px)/prev_px if not math.isnan(prev_px) and not math.isnan(px) and prev_px>0 else math.nan
        c1   = bool_s(c1_sg(days_ban, i))
        c2   = bool_s(c2_fp(days_ban, i))
        c4   = bool_s(c4_slope(days_ban, i))
        gc, supp = gomc_draft(days_ban, i)
        pump_flag = " <-PUMP" if (not math.isnan(dpx_pct) and dpx_pct > 0.08) else ""
        dump_flag = " <-DUMP" if (not math.isnan(dpx_pct) and dpx_pct < -0.08) else ""
        flag = pump_flag or dump_flag
        # Only show interesting rows: pumps, grind-up, or GOM-C fires
        if gc or pump_flag or dump_flag or (not math.isnan(dpx_pct) and 0.01 < dpx_pct < 0.08):
            tkr_pct = tkr*100 if not math.isnan(tkr) else math.nan
            favg_pct = favg*100 if not math.isnan(favg) else math.nan
            dpx_pct_d = dpx_pct*100 if not math.isnan(dpx_pct) else math.nan
            print(f"  {date:<12} {nan_s(px,'<9.5f')} {nan_s(dpx_pct_d,'>+6.1f')}% "
                  f"{nan_s(tkr_pct,'>5.1f')}% "
                  f"{nan_s(favg_pct,'>7.4f')}% "
                  f"{nan_s(pr,'>6.3f')} {nan_s(glsr,'>5.3f')} {nan_s(dp,'>+6.3f')} "
                  f"{c1:<4} {c2:<4} {c4:<4} {'GOM-C!' if gc else '     ':<6} {'SUPP' if supp else '':<5}{flag}")
        prev_px = px
    # Check if any GOM-C fire existed
    gomc_fires = []
    prev_px2 = math.nan
    for i, d in enumerate(days_ban):
        date = d.get("date","")
        if date < "2026-07-01": prev_px2 = d.get("px_avg", math.nan); continue
        if d.get("_suspect"): prev_px2 = math.nan; continue
        gc, _ = gomc_draft(days_ban, i)
        if gc: gomc_fires.append(date)
        prev_px2 = d.get("px_avg", math.nan)
    if gomc_fires:
        print(f"\n  *** RED ALERT: GOM-C fires on BANANAS31: {gomc_fires} ***")
        print(f"  *** Draft missing a guard -- investigate C conditions! ***")
    else:
        print(f"\n  OK: No GOM-C fire on BANANAS31 (negative test passed)")
else:
    print("  BANANAS31: no data")

# ---------------------------------------------------------------------------
# G3: BULLA 17-21/07 -- cover-driven branch (px+/OI-)
# ---------------------------------------------------------------------------
print("\n" + "-"*85)
print("G3 -- BULLA (BULLAUSDT) 2026-07-17 to 2026-07-21: cover-driven (px+/OI-)")
print("-"*85)

days_bul, _ = load_days("BULLAUSDT", "2026-07-21")
if days_bul:
    print(f"  {'Date':<12} {'px':<10} {'OI_M':>6} {'DOI_M':>7} {'tkr%':<6} "
          f"{'pos_r':>6} {'Dpos':>6} {'C1':<4} {'C2':<4} {'C4':<4} {'GOM-C':<6} note")
    print(f"  {'-'*100}")
    prev_oi = math.nan
    for i, d in enumerate(days_bul):
        date = d.get("date","")
        if date < "2026-07-15": prev_oi = d.get("oi_usd", math.nan); continue
        if date > "2026-07-21": break
        if d.get("_suspect"):
            print(f"  {date:<12} [SUSPECT]"); prev_oi=math.nan; continue
        px   = d.get("px_avg", math.nan)
        oi   = d.get("oi_usd", math.nan)
        tkr  = d.get("taker_buy_pct", math.nan)
        pr   = d.get("lsr_pos_r", math.nan) or d.get("lsr_pos", math.nan)
        dp   = d_pos(days_bul, i)
        doi  = (oi - prev_oi)/1e6 if not math.isnan(oi) and not math.isnan(prev_oi) else math.nan
        c1   = bool_s(c1_sg(days_bul, i))
        c2   = bool_s(c2_fp(days_bul, i))
        c4   = bool_s(c4_slope(days_bul, i))
        gc, supp = gomc_draft(days_bul, i)
        note = "OI%s" % ("v" if not math.isnan(doi) and doi<0 else "^")
        if not math.isnan(doi) and doi < -0.5: note += " cover"
        tkr_pct = tkr*100 if not math.isnan(tkr) else math.nan
        oi_m = oi/1e6 if not math.isnan(oi) else math.nan
        print(f"  {date:<12} {nan_s(px,'<10.6f')} {nan_s(oi_m,'>6.1f')}M "
              f"{nan_s(doi,'>+7.2f')}M {nan_s(tkr_pct,'>5.1f')}% "
              f"{nan_s(pr,'>6.3f')} {nan_s(dp,'>+6.3f')} "
              f"{c1:<4} {c2:<4} {c4:<4} {'GOM-C' if gc else '     ':<6} {note}")
        prev_oi = oi
else:
    print("  BULLA: no data")

# ---------------------------------------------------------------------------
# G4: BANK 14-19/07 -- pos_r harvest evidence
# ---------------------------------------------------------------------------
print("\n" + "-"*85)
print("G4 -- BANK (BANKUSDT) 2026-07-10 to 2026-07-20: pos_r harvest evidence")
print("-"*85)

days_bank, _ = load_days("BANKUSDT", "2026-07-20")
if days_bank:
    st_data = json.load(open(str(STATE)))
    bank_st = st_data.get("BANK", {})
    chain_close = bank_st.get("close_date","")
    chain_reason = bank_st.get("close_reason","")
    peak_pr = bank_st.get("peak_pos_r", math.nan)
    print(f"  State: chain_close={chain_close} reason={chain_reason} peak_pr={peak_pr:.3f}")
    print()
    print(f"  {'Date':<12} {'px':<10} {'DOI_M':>7} {'pos_r':>6} {'Dpos':>6} "
          f"{'gLSR':>5} {'GOM_fire':<9} Chain")
    print(f"  {'-'*90}")
    from gom_scan import update_chain
    chain = {}
    prev_oi = math.nan
    for i, d in enumerate(days_bank):
        date = d.get("date","")
        skip = d.get("_skip_eval") or d.get("_suspect")
        if skip:
            result = _false_result()
        else:
            result = eval_gom(days_bank, i, cfg, sc)
        chain = update_chain(chain, "BANK", days_bank, i, result, cfg, sc)
        if date < "2026-07-10" or date > "2026-07-20":
            prev_oi = d.get("oi_usd", math.nan); continue
        if skip:
            print(f"  {date:<12} [SUSPECT]"); prev_oi=math.nan; continue
        px   = d.get("px_avg", math.nan)
        oi   = d.get("oi_usd", math.nan)
        pr   = d.get("lsr_pos_r", math.nan) or d.get("lsr_pos", math.nan)
        dp   = d_pos(days_bank, i)
        glsr = d.get("lsr_global_r", math.nan)
        doi  = (oi - prev_oi)/1e6 if not math.isnan(oi) and not math.isnan(prev_oi) else math.nan
        gom  = result.get("gom_day", False)
        if chain.get("chain_open"):
            cst = f"OPEN n={chain.get('n_days',0)} brk={chain.get('break_streak',0)}"
        elif chain.get("close_date","") == date:
            cst = f"CLOSED[{chain.get('close_reason','')[:20]}]"
        else:
            cst = "closed"
        oi_m = oi/1e6 if not math.isnan(oi) else math.nan
        print(f"  {date:<12} {nan_s(px,'<10.6f')} {nan_s(doi,'>+7.2f')}M "
              f"{nan_s(pr,'>6.3f')} {nan_s(dp,'>+6.3f')} {nan_s(glsr,'>5.3f')} "
              f"{'GOM' if gom else '   ':<9} {cst}")
        prev_oi = oi
else:
    print("  BANK: no data")

# ---------------------------------------------------------------------------
# G5: Re-accum after crash -- BAS / ZBT / ARX + scan fw for others
# ---------------------------------------------------------------------------
print("\n" + "-"*85)
print("G5 -- Re-accum after crash: BAS / ZBT / ARX (+ all rule-iv fw closed)")
print("-"*85)

st_data = json.load(open(str(STATE)))
fw_raw  = [l.strip() for l in open(str(REPO/'data'/'config'/'freshwatch_symbols.txt')).readlines() if l.strip()]
fw_syms = [s for s in fw_raw]
fw_base = {s[:-4] if s.endswith('USDT') else s for s in fw_syms}

# Get rule-iv closed tokens in fw
ruleiv_toks = []
for tok, ch in st_data.items():
    if tok not in fw_base: continue
    if ch.get("chain_open"): continue
    cr = ch.get("close_reason","")
    if "pos_r_drop" in cr or ch.get("close_note","") == "chuyyen pha phan phoi":
        ruleiv_toks.append((tok, ch.get("close_date",""), ch))

# Focus on BAS, ZBT, ARX first, then top rule-iv
focus = ["BAS","ZBT","ARX"]
all_check = [(t,cd,ch) for t,cd,ch in ruleiv_toks if t in focus]
all_check += [(t,cd,ch) for t,cd,ch in ruleiv_toks if t not in focus and cd >= "2026-06-08"][:8]

print(f"  {'Token':<12} {'CloseDate':<12} {'ClosePx':>9} {'ReaccumDate':<14} {'Gap_d':>6} note")
print(f"  {'-'*70}")

for tok, close_date, ch_st in all_check:
    if not close_date:
        print(f"  {tok:<12} no close_date"); continue
    sym = tok+"USDT"
    try:
        close_dt = datetime.strptime(close_date, "%Y-%m-%d")
    except:
        print(f"  {tok:<12} bad close_date={close_date}"); continue
    scan_end = (close_dt + timedelta(days=45)).strftime("%Y-%m-%d")
    scan_end = min(scan_end, "2026-08-07")
    days_t, _ = load_days(sym, scan_end, lb=90)
    if not days_t:
        print(f"  {tok:<12} {close_date:<12} no data"); continue
    # Find close px
    close_px = math.nan
    for d in days_t:
        if d.get("date","") == close_date:
            close_px = d.get("px_avg", math.nan)
    # Find first day after close where A1+A2+A3=True (ignoring DQ)
    reaccum_date = None
    for i, d in enumerate(days_t):
        date = d.get("date","")
        if date <= close_date: continue
        if d.get("_suspect") or d.get("_skip_eval"): continue
        try:
            a1 = lsr_accum(days_t, i, cfg)
            a2 = _avg5_glsr(days_t, i) <= 1.1
            a3 = _a3_slope_ok(days_t, i, sc)
            if a1 and a2 and a3:
                reaccum_date = date
                break
        except:
            continue
    if reaccum_date:
        rd = datetime.strptime(reaccum_date, "%Y-%m-%d")
        gap = (rd - close_dt).days
        print(f"  {tok:<12} {close_date:<12} {nan_s(close_px,'>9.5f')} {reaccum_date:<14} {gap:>6}d")
    else:
        print(f"  {tok:<12} {close_date:<12} {nan_s(close_px,'>9.5f')} no-reaccum-by-{scan_end} {'---':>6}")

# ---------------------------------------------------------------------------
# G6: Q2 heuristic -- share = Q1_cum / OI_at_last_gom for IDOL/ZBT/TUT/BANK
# ---------------------------------------------------------------------------
print("\n" + "-"*85)
print("G6 -- Q2 heuristic: share = Q1_cum_usd / OI_at_last_gom for IDOL/ZBT/TUT/BANK")
print("-"*85)

q2_tokens = {
    "IDOL": ("IDOLUSDT", "2026-07-12"),
    "ZBT":  ("ZBTUSDT",  "2026-07-01"),
    "TUT":  ("TUTUSDT",  "2026-07-11"),
    "BANK": ("BANKUSDT", "2026-07-15"),
}

print(f"  {'Token':<8} {'Q1_cum_usd':>14} {'OI_at_gom':>14} {'share%':>8} "
      f"{'peak_pr':>8} {'implied_B':>14} note")
print(f"  {'-'*85}")

for tok, (sym, gom_date) in q2_tokens.items():
    ch = st_data.get(tok, {})
    q1 = ch.get("Q1_cum_usd", 0.0)
    peak_pr = ch.get("peak_pos_r", math.nan)

    days_q, _ = load_days(sym, gom_date, lb=5)
    oi_gom = math.nan
    for d in days_q:
        if d.get("date","") == gom_date:
            oi_gom = d.get("oi_usd", math.nan)
    if math.isnan(oi_gom) and days_q:
        oi_gom = days_q[-1].get("oi_usd", math.nan)

    share_pct = q1 / oi_gom * 100 if not math.isnan(oi_gom) and oi_gom > 0 and q1 > 0 else math.nan
    if not math.isnan(peak_pr) and not math.isnan(oi_gom) and peak_pr > 0:
        long_oi = oi_gom * peak_pr / (1 + peak_pr)
    else:
        long_oi = math.nan
    if q1 < 1000:
        note = "Q1=0 seat-rot"
    elif not math.isnan(share_pct) and 35 <= share_pct <= 50:
        note = "in 35-50%"
    elif not math.isnan(share_pct):
        note = "OUTLIER"
    else:
        note = "no OI"

    oi_gom_m = oi_gom/1e6 if not math.isnan(oi_gom) else math.nan
    long_oi_m = long_oi/1e6 if not math.isnan(long_oi) else math.nan
    print(f"  {tok:<8} ${q1:>13,.0f} {nan_s(oi_gom_m,'>13.1f')}M "
          f"{nan_s(share_pct,'>7.1f')}% {nan_s(peak_pr,'>8.3f')} "
          f"{nan_s(long_oi_m,'>13.1f')}M {note}")

print()
print("  Note: share = delta_OI+ accumulated during GOM window / OI at last gom date")
print("  implied_B = peak_pr/(1+peak_pr) x OI = estimated long-side OI at peak")
print()
print("=" * 85)
print("END GOM-C VALIDATION")
print("=" * 85)
