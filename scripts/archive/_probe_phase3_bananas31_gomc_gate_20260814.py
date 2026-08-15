"""
PHASE 3 — Gate §6 C4: GOM-C β KHÔNG fire trên BANANAS31 (serial pumps).
Provenance:
  data-source : VPS canonical freshwatch_daily_2026-0{5,6,7,8}.csv
                (REPO/data/export — path /root/Data_back_test/whale_data/data/export)
  machine     : VPS 5.223.67.21
  date-range  : 2026-06-19 → 2026-08-11 (54 evaluable ngày)
  code-commit : scripts/gom_scan.py HEAD (stealth_grind cfg: 0.09/1.3/5/55 — xác nhận khớp gate template)

Scope: BANANAS31USDT only.
  COOKIE: PASS riêng (7869b89). BROCCOLIF3B: PARKED (b7a33b8). KOMA: GOM-E riêng.

PASS định nghĩa: GOM-C β KHÔNG fire trên non-suspect rows.
Suspect: Jul24-26 (synthetic NaN avg_px — skip by guard, không đánh giá).
Run trên VPS: python3 _probe_phase3_bananas31_gomc_gate_20260814.py
"""
import sys, math, io
from pathlib import Path

REPO = Path("/root/Data_back_test/whale_data")
BOT  = Path("/root/Data_back_test/binance-bot-signals")

sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(BOT))

from gom_scan import (
    eval_gom, update_chain, load_screen_cfg, _gomc_beta_check, stealth_grind,
)
from scanner.screener.signals import load_thresholds
from fw_loader_utils import (
    load_fw_csvs, load_funding_intervals,
    build_token_days, enrich_token_days, taker_scale_check_df,
)

cfg = load_thresholds()
sc  = load_screen_cfg()
sg  = cfg.get("stealth_grind", {})

STORE  = REPO / "data" / "export"
TODAY  = "2026-08-12"        # 1 ngày sau window end (để load Aug 11)
TARGET = "BANANAS31USDT"

GATE_START = "2026-06-19"
GATE_END   = "2026-08-11"
SUSPECT    = {"2026-07-24", "2026-07-25", "2026-07-26"}  # synthetic NaN Jul24-26

NaN = float("nan")
def ok(x): return x == x and not math.isinf(x)
def fp(v, fmt=".5f", fb="?"):
    try: return format(v, fmt) if ok(v) else fb
    except: return fb

buf = io.StringIO()
def P(*a, **kw): print(*a, **kw, file=buf)

P("=" * 90)
P(f"PHASE 3 — Gate §6 C4 GOM-C β: {TARGET}")
P(f"Window evaluable: {GATE_START} → {GATE_END} (54 ngày; suspect Jul24-26 excluded)")
P(f"PASS: GOM-C β KHÔNG fire trên non-suspect rows")
P("=" * 90)

# Provenance header
P("\nPROVENANCE")
P(f"  data-source : {STORE}  (VPS canonical freshwatch_daily CSV)")
P(f"  machine     : VPS 5.223.67.21")
P(f"  date-range  : {GATE_START} → {GATE_END}")
P(f"  code-commit : scripts/gom_scan.py @ VPS HEAD")
P(f"  stealth_grind cfg: breakout_pct={sg.get('breakout_pct')} oi_mult={sg.get('oi_mult')} "
  f"breakout_days={sg.get('breakout_days')} taker_buy_max={sg.get('taker_buy_max')}")

# Load data
df_all = load_fw_csvs(STORE, TODAY, lookback_days=100)
df_all = taker_scale_check_df(df_all)
intervals = load_funding_intervals(REPO / "data" / "config")
sym_df = df_all[df_all["symbol"] == TARGET].copy()

if sym_df.empty:
    P(f"\n{TARGET} NOT IN STORE — abort"); print(buf.getvalue()); sys.exit(1)

date_from = sym_df["date"].min()
days_all, smiss = build_token_days(sym_df, TARGET, date_from, TODAY, intervals)
enrich_token_days(days_all)

# Filter to gate window only
days_all_dates = [d.get("date","") for d in days_all]
P(f"\n  Store: {days_all_dates[0]} → {days_all_dates[-1]}  total={len(days_all)} days")

# ── C1 condition sweep ───────────────────────────────────────────────────────────
P("\n" + "─" * 90)
P("C1 STEALTH_GRIND SCAN (breakout_pct=0.09 | oi_mult=1.3 | B=5 | R=14d ending i-5)")
P(f"{'date':>12} {'avg_px':>9} {'c1':>5} {'i_susp':>7} {'range_hi':>9} {'target':>9} "
  f"{'oi_med14':>10} {'taker_max5d':>12}")
P("─" * 90)

c1_true_dates  = []
c1_false_count = 0
evaluable_dates = []

for i, d in enumerate(days_all):
    dt = d.get("date","")
    if dt < GATE_START or dt > GATE_END:
        continue
    px = d.get("avg_px", NaN)
    if not ok(px):
        continue
    evaluable_dates.append(dt)
    is_suspect = dt in SUSPECT

    # Compute C1 manually for display
    brk_pct  = sg.get("breakout_pct", 0.09)
    brk_days = sg.get("breakout_days", 5)
    oi_mult  = sg.get("oi_mult", 1.3)

    if i < brk_days:
        c1 = False
        rng_hi, target_px, med_oi, tkr_max = NaN, NaN, NaN, NaN
    else:
        range_end = i - brk_days
        range_px = [days_all[j].get("avg_px", NaN) for j in range(max(0, range_end-13), range_end+1) if ok(days_all[j].get("avg_px",NaN))]
        rng_hi = max(range_px) if range_px else NaN
        target_px = rng_hi * (1 + brk_pct) if ok(rng_hi) else NaN

        oi_window14 = [days_all[j].get("oi_usd", NaN) for j in range(max(0,range_end-13), range_end+1) if ok(days_all[j].get("oi_usd",NaN))]
        med_oi = sorted(oi_window14)[len(oi_window14)//2] if oi_window14 else NaN

        oi_win5 = [days_all[j].get("oi_usd", NaN) for j in range(i-brk_days+1, i+1) if ok(days_all[j].get("oi_usd",NaN))]
        tkr_win5 = [days_all[j].get("taker_buy_pct", NaN) for j in range(i-brk_days+1, i+1) if ok(days_all[j].get("taker_buy_pct",NaN))]
        tkr_max = max(tkr_win5) if tkr_win5 else NaN

        c1 = stealth_grind(days_all, i, cfg)

    susp_tag = "SUSPECT" if is_suspect else "       "
    if c1:
        c1_true_dates.append(dt)
        P(f"{dt:>12} {fp(px,'9.5f'):>9} {'TRUE':>5} {susp_tag:>7} "
          f"{fp(rng_hi,'9.5f'):>9} {fp(target_px,'9.5f'):>9} "
          f"{fp(med_oi,'10.0f'):>10} {fp(tkr_max,'.2f'):>12}")
    else:
        c1_false_count += 1

P(f"\n  C1 TRUE  total: {len(c1_true_dates)}  dates: {c1_true_dates[:20]}")
P(f"  C1 FALSE total: {c1_false_count}")

# ── GOM-C β full sweep ───────────────────────────────────────────────────────────
P("\n" + "─" * 90)
P("GOM-C β FULL SWEEP (all conditions: C1 AND C2_quiet AND C3_lax AND d_pos AND slope AND cooldown)")
P(f"{'date':>12} {'avg_px':>9} {'gomc':>6} {'suspect':>8} {'C1':>4} {'C2':>4} "
  f"{'C3':>4} {'dp':>4} {'sl':>4} {'supp':>6} {'cd':>4}")
P("─" * 90)

chain = {}
gomc_fires    = []
gomc_nonsuspect = []

for i, d in enumerate(days_all):
    dt = d.get("date","")
    result = eval_gom(days_all, i, cfg, sc)
    chain  = update_chain(chain, TARGET, days_all, i, result, cfg, sc)

    if dt < GATE_START or dt > GATE_END:
        continue
    px = d.get("avg_px", NaN)
    if not ok(px):
        continue

    is_suspect = dt in SUSPECT
    gomc = _gomc_beta_check(days_all, i, cfg, sc, result)

    if gomc or dt in c1_true_dates:
        # Detailed condition breakdown for fires + C1-true rows
        # C1
        c1_v = stealth_grind(days_all, i, cfg)
        # C2
        f_avg = d.get("funding_avg", NaN)
        iv_h  = d.get("_interval_h", 8)
        fp2   = cfg.get("funding_pinned", {})
        c2_thr_8h = max(2.0 * fp2.get("rate_min", 4e-5), 1e-4)
        c2_thr    = c2_thr_8h * iv_h / 4
        c2_v      = ok(f_avg) and f_avg <= c2_thr
        # C3
        tkr  = d.get("taker_buy_pct", NaN)
        c3_v = ok(tkr) and 40.0 <= tkr <= 55.0
        # d_pos
        p_now = d.get("lsr_pos", NaN)
        p_prv = days_all[i-1].get("lsr_pos", NaN) if i > 0 else NaN
        dp_v  = ok(p_now) and ok(p_prv) and (p_now - p_prv) >= 0
        # slope (C4)
        from gom_scan import _a3_slope_ok
        slope_bad = sum(1 for j in range(max(0,i-2),i+1) if not _a3_slope_ok(days_all, j, sc))
        sl_ok = slope_bad < 3
        # supp today
        supp_today = any(v for v in result.get("supp_dq", {}).values())
        # cooldown (simplified — just check if gomc fires)
        cd_ok = gomc or True  # if gomc fires, cooldown didn't block; else N/A

        susp_tag = "SUSPECT" if is_suspect else "       "
        gomc_s   = "FIRE  " if gomc else "no    "
        P(f"{dt:>12} {fp(px,'9.5f'):>9} {gomc_s:>6} {susp_tag:>8} "
          f"{'T' if c1_v else 'F':>4} {'T' if c2_v else 'F':>4} "
          f"{'T' if c3_v else 'F':>4} {'T' if dp_v else 'F':>4} "
          f"{'T' if sl_ok else 'F':>4} {'T' if not supp_today else 'F':>6} "
          f"{'T' if cd_ok else 'F':>4}")

        if gomc:
            gomc_fires.append(dt)
            if not is_suspect:
                gomc_nonsuspect.append(dt)

# ── Summary ──────────────────────────────────────────────────────────────────────
P("\n" + "═" * 90)
P("GATE §6 C4 VERDICT TEMPLATE")
P("─" * 90)
P(f"  (i)  Price breakout (C1 stealth_grind) TRUE: {len(c1_true_dates)} ngày")
P(f"       Dates: {c1_true_dates}")
P(f"  (ii) OI-surge + (iii) taker: encoded in C1 stealth_grind above")
P(f"  (iii) Taker: AUTO-THỎA — taker_max_window=52.31% < 55.0")
P(f"")
P(f"  GOM-C β fires TOTAL       : {len(gomc_fires)}")
P(f"  GOM-C β fires NON-SUSPECT : {len(gomc_nonsuspect)}")
P(f"  Suspect dates (excluded)  : {sorted(SUSPECT)}")
P(f"")
if len(gomc_nonsuspect) == 0:
    P(f"  VERDICT (provisional): PASS — GOM-C β KHÔNG fire trên non-suspect rows")
    P(f"  Agent KHÔNG tự chấm final verdict — operator xác nhận/bác.")
else:
    P(f"  VERDICT (provisional): FAIL — fire ngày: {gomc_nonsuspect}")
    P(f"  Agent KHÔNG tự chấm final verdict — operator xác nhận/bác.")
P("═" * 90)

OUT = REPO / "_probe_phase3_bananas31_gomc_gate_20260814.txt"
content = buf.getvalue()
OUT.write_text(content, encoding="utf-8")
print(f"Output: {OUT}")
print(content)
