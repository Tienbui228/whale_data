"""
PHASE 3 supplemental: condition trace chi tiết Aug 10-11 (C1=T nhưng GOM-C không fire).
Run trên VPS: python3 _probe_phase3_trace_aug11_20260814.py
"""
import sys, math
from pathlib import Path

REPO = Path("/root/Data_back_test/whale_data")
BOT  = Path("/root/Data_back_test/binance-bot-signals")

sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(BOT))

from gom_scan import eval_gom, load_screen_cfg, _gomc_beta_check, stealth_grind, _a3_slope_ok
from scanner.screener.signals import load_thresholds
from fw_loader_utils import load_fw_csvs, load_funding_intervals, build_token_days, enrich_token_days, taker_scale_check_df

cfg = load_thresholds()
sc  = load_screen_cfg()
TARGET = "BANANAS31USDT"
STORE  = REPO / "data" / "export"
TODAY  = "2026-08-12"

df_all = load_fw_csvs(STORE, TODAY, lookback_days=100)
df_all = taker_scale_check_df(df_all)
intervals = load_funding_intervals(REPO / "data" / "config")
sym_df = df_all[df_all["symbol"] == TARGET].copy()
days, _ = build_token_days(sym_df, TARGET, sym_df["date"].min(), TODAY, intervals)
enrich_token_days(days)

NaN = float("nan")
def ok(x): return x == x and not math.isinf(x)
fp2 = cfg.get("funding_pinned", {})

# Find Aug 10 and Aug 11 indices
for i, d in enumerate(days):
    dt = d.get("date","")
    if dt not in ("2026-08-10", "2026-08-11"):
        continue

    result = eval_gom(days, i, cfg, sc)
    c1 = stealth_grind(days, i, cfg)
    f_avg = d.get("funding_avg", NaN)
    iv_h  = d.get("_interval_h", 8)
    c2_thr_8h = max(2.0 * fp2.get("rate_min", 4e-5), 1e-4)
    c2_thr    = c2_thr_8h * iv_h / 4
    c2 = ok(f_avg) and f_avg <= c2_thr

    tkr = d.get("taker_buy_pct", NaN)
    c3 = ok(tkr) and 40.0 <= tkr <= 55.0

    p_now = d.get("lsr_pos", NaN)
    p_prv = days[i-1].get("lsr_pos", NaN) if i > 0 else NaN
    d_pos = ok(p_now) and ok(p_prv) and (p_now - p_prv) >= 0

    slope_bad = sum(1 for j in range(max(0,i-2),i+1) if not _a3_slope_ok(days, j, sc))
    sl_ok = slope_bad < 3

    supp_today = any(v for v in result.get("supp_dq", {}).values())

    # Cooldown: scan prior 13d for supp_dq
    cd_blocked_by = []
    for j in range(max(0, i-13), i):
        dj = days[j]
        if dj.get("_skip_eval") or dj.get("_suspect"):
            continue
        rj = eval_gom(days, j, cfg, sc)
        if any(v for v in rj.get("supp_dq", {}).values()):
            cd_blocked_by.append(dj.get("date","?"))

    # GOM-C without cooldown
    gomc_no_cd = _gomc_beta_check(days, i, cfg, sc, result, check_cooldown=False)
    gomc_with_cd = _gomc_beta_check(days, i, cfg, sc, result, check_cooldown=True)

    print(f"\n{'='*60}")
    print(f"DATE: {dt}")
    print(f"  avg_px      = {d.get('avg_px', NaN):.6f}")
    print(f"  taker_pct   = {tkr:.2f}%")
    print(f"  funding_avg = {f_avg:.6f}  c2_thr={c2_thr:.6f}")
    print(f"  lsr_pos now = {p_now:.4f}  prev = {p_prv:.4f}")
    print(f"  interval_h  = {iv_h}")
    print(f"")
    print(f"  C1 stealth_grind      = {c1}")
    print(f"  C2 funding quiet      = {c2}  (f_avg={f_avg:.6f} <= thr={c2_thr:.6f}: {c2})")
    print(f"  C3 taker [40,55]      = {c3}  (tkr={tkr:.2f})")
    print(f"  d_pos (pos non-decl)  = {d_pos}  (now={p_now:.4f} prev={p_prv:.4f} delta={p_now-p_prv:.4f})")
    print(f"  slope C4 ok           = {sl_ok}  (slope_bad={slope_bad})")
    print(f"  supp_today (DQ)       = {supp_today}  → NOT supp = {not supp_today}")
    print(f"  cooldown blocked by   = {cd_blocked_by if cd_blocked_by else 'NONE'}")
    print(f"")
    print(f"  GOM-C β (no cooldown) = {gomc_no_cd}")
    print(f"  GOM-C β (with cd)     = {gomc_with_cd}")
    print(f"  → FIRE? {'YES — UNEXPECTED' if gomc_with_cd else 'NO — expected'}")

print("\nDONE")
