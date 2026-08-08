"""B2.2 pre-check: (1) FF 08-01 div_avg3 + HEI negative test,
(3) BANK VWAP [vw-vol], (4) IDOL gross/net churn.
Uses scratch CSVs (local copies of freshwatch data).
"""
import sys, math
from pathlib import Path
sys.path.insert(0, "scripts")

from fw_loader_utils import (
    load_fw_csvs, build_token_days, enrich_token_days,
    load_funding_intervals, taker_scale_check_df, div_avg3,
)
import gom_scan as gs

CONFIG = Path("data/config")
intervals = load_funding_intervals(CONFIG)

# Use scratch CSVs (local copies)
SCRATCH = Path("scratch")
cfg = gs.load_thresholds()
sc  = gs.load_screen_cfg()

import pandas as pd

def load_scratch(up_to: str, lookback=60) -> pd.DataFrame:
    from datetime import datetime, timedelta
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
    df = df[(df["date"] >= s) & (df["date"] <= up_to)].copy()
    return df.sort_values(["date","symbol"]).reset_index(drop=True)

# ── (1) FF 2026-08-01 div_avg3 ───────────────────────────────────────────────
print("=" * 60)
print("(1) FF 2026-08-01 div_avg3 + HEI negative test")
print("=" * 60)

TARGET_FF = "2026-08-07"
df = load_scratch(TARGET_FF, lookback=60)
df = taker_scale_check_df(df)

if "FFUSDT" not in df["symbol"].unique():
    print("WARN: FFUSDT not in scratch data")
else:
    days_ff, _ = build_token_days(df, "FFUSDT", "2026-07-10", TARGET_FF, intervals)
    enrich_token_days(days_ff)

    def mean_of_ratios(days, i):
        start = max(0, i - 2)
        ratios = []
        for j in range(start, i + 1):
            p = days[j].get("lsr_pos", float("nan"))
            a = days[j].get("lsr_acc", float("nan"))
            if not math.isnan(p) and not math.isnan(a) and a != 0:
                ratios.append(p / a)
        return sum(ratios)/len(ratios) if ratios else float("nan")

    print("  date        ratio-of-means  mean-of-ratios  diff")
    for i, d in enumerate(days_ff):
        dt = d.get("date","")
        if dt < "2026-07-28":
            continue
        new_v = div_avg3(days_ff, i)
        old_v = mean_of_ratios(days_ff, i)
        diff  = abs(new_v - old_v) if not (math.isnan(new_v) or math.isnan(old_v)) else float("nan")
        mark  = " <<< FF 08-01 TARGET" if dt == "2026-08-01" else ""
        print(f"  {dt}   {new_v:>8.4f}          {old_v:>8.4f}       {diff:.4f}{mark}")

    # verify 08-01
    i_0801 = next((i for i,d in enumerate(days_ff) if d.get("date")=="2026-08-01"), None)
    if i_0801 is not None:
        result_0801 = div_avg3(days_ff, i_0801)
        expected = 3.175
        tol = 0.05
        ok = abs(result_0801 - expected) <= tol
        print(f"\n  FF 08-01 div_avg3 = {result_0801:.4f} (expect ~{expected}, tol+-{tol}): {'PASS' if ok else 'FAIL'}")
    else:
        print("  WARN: 08-01 not in days")

# HEI negative test
print("\n  --- HEI negative test ---")
if "HEIUSDT" in df["symbol"].unique():
    days_hei, _ = build_token_days(df, "HEIUSDT", "2026-07-20", TARGET_FF, intervals)
    enrich_token_days(days_hei)
    print("  date        ratio-of-means  mean-of-ratios  diff")
    for i, d in enumerate(days_hei):
        dt = d.get("date","")
        if dt < "2026-07-28" or dt > "2026-08-03":
            continue
        new_v = div_avg3(days_hei, i)
        old_v = mean_of_ratios(days_hei, i)
        diff  = abs(new_v - old_v) if not (math.isnan(new_v) or math.isnan(old_v)) else float("nan")
        print(f"  {dt}   {new_v:>8.4f}          {old_v:>8.4f}       {diff:.4f}")
else:
    print("  HEIUSDT not in scratch — using BANKUSDT as acc_r-volatile substitute")
    if "BANKUSDT" in df["symbol"].unique():
        days_bk, _ = build_token_days(df, "BANKUSDT", "2026-07-01", "2026-07-18", intervals)
        enrich_token_days(days_bk)
        print("  date        ratio-of-means  mean-of-ratios  diff")
        for i, d in enumerate(days_bk):
            dt = d.get("date","")
            if dt < "2026-07-08":
                continue
            new_v = div_avg3(days_bk, i)
            old_v = mean_of_ratios(days_bk, i)
            diff  = abs(new_v - old_v) if not (math.isnan(new_v) or math.isnan(old_v)) else float("nan")
            print(f"  {dt}   {new_v:>8.4f}          {old_v:>8.4f}       {diff:.4f}")

# ── (3) BANK VWAP [vw-vol] via new code ─────────────────────────────────────
print("\n" + "=" * 60)
print("(3) BANK chain VWAP via new code (expect [vw-vol] with number)")
print("=" * 60)

from pathlib import Path as _P
BOT_ROOT = _P(r"D:\Data back test\binance-bot-signals")
import importlib.util
_spec2 = importlib.util.spec_from_file_location("replay", BOT_ROOT / "replay.py")
_replay = importlib.util.module_from_spec(_spec2)
_spec2.loader.exec_module(_replay)

bank_path = BOT_ROOT / "docs" / "case study" / "BANK_result.txt"
funding, oi, ratio, klines = _replay.parse_result_file(bank_path)
days_bank = _replay.build_days(funding, oi, ratio, klines)

chain = {}
for i, d in enumerate(days_bank):
    result = gs.eval_gom(days_bank, i, cfg, sc)
    chain  = gs.update_chain(chain, "BANK", days_bank, i, result, cfg, sc)

vn  = chain.get("vwap_num", 0.0)
vd  = chain.get("vwap_den", 0.0)
vvn = chain.get("vwap_vol_num", 0.0)
vvd = chain.get("vwap_vol_den", 0.0)
vt  = chain.get("vwap_type")

print(f"  BANK final state:")
print(f"    chain_open     = {chain.get('chain_open')}")
print(f"    close_reason   = {chain.get('close_reason','')}")
print(f"    vwap_den (T1)  = {vd:,.2f}")
print(f"    vwap_vol_den   = {vvd:,.2f}")
print(f"    vwap_type      = {vt}")
print(f"    Q1_cum_usd     = {chain.get('Q1_cum_usd', 0):,.2f}")

if vd > 0:
    vwap_t1 = vn / vd
    print(f"    VWAP Tier 1    = {vwap_t1:.6f} (oi_weighted)")
elif vvd > 0:
    vwap_t2 = vvn / vvd
    print(f"    VWAP Tier 2    = {vwap_t2:.6f} [vw-vol - seat-rotation chain]")
else:
    print(f"    VWAP           = N/A (no accumulation)")

# ── (4) IDOL 28/07 gross/net churn ──────────────────────────────────────────
print("\n" + "=" * 60)
print("(4) IDOL gross vs net + [churn] tag")
print("=" * 60)

if "IDOLUSDT" in df["symbol"].unique():
    days_idol, _ = build_token_days(df, "IDOLUSDT", "2026-07-01", "2026-08-07", intervals)
    enrich_token_days(days_idol)
    chain_idol = {}
    for i, d in enumerate(days_idol):
        result = gs.eval_gom(days_idol, i, cfg, sc)
        chain_idol = gs.update_chain(chain_idol, "IDOL", days_idol, i, result, cfg, sc)

    gross = chain_idol.get("Q1_cum_usd", 0.0)
    net   = chain_idol.get("net_oi_delta_usd", float("nan"))
    oi_s  = chain_idol.get("oi_start_usd", float("nan"))
    oi_l  = chain_idol.get("oi_last_usd", float("nan"))
    churn = (not math.isnan(gross) and not math.isnan(net)
             and net > 0 and gross > 2 * net)
    print(f"  IDOL state:")
    print(f"    chain_open     = {chain_idol.get('chain_open')}")
    print(f"    oi_start_usd   = {oi_s:,.0f}" if not math.isnan(oi_s) else "    oi_start_usd   = N/A")
    print(f"    oi_last_usd    = {oi_l:,.0f}" if not math.isnan(oi_l) else "    oi_last_usd    = N/A")
    print(f"    gross_adds_usd = {gross:,.0f}")
    print(f"    net_oi_delta   = {net:,.0f}" if not math.isnan(net) else "    net_oi_delta   = N/A")
    if churn:
        print(f"    [churn] tag    = YES (gross={gross:,.0f} > 2*net={2*net:,.0f})")
    else:
        print(f"    [churn] tag    = NO")
    print(f"    vwap_type      = {chain_idol.get('vwap_type')}")

    # show per-day firing for context around 07-28
    print("\n  Per-day GOM check (07-25 to 07-31):")
    for i, d in enumerate(days_idol):
        dt = d.get("date","")
        if dt < "2026-07-25" or dt > "2026-07-31":
            continue
        r = gs.eval_gom(days_idol, i, cfg, sc)
        gom  = r.get("gom_day", False)
        supp = r.get("any_supp_dq", False)
        oi_v = d.get("oi_usd", float("nan"))
        pos  = d.get("lsr_pos", float("nan"))
        print(f"    {dt}: GOM={'Y' if gom else 'N'} supp={'Y' if supp else 'N'} "
              f"OI={oi_v:,.0f}" if not math.isnan(oi_v) else f"    {dt}: GOM={'Y' if gom else 'N'} supp={'Y' if supp else 'N'} OI=N/A")
else:
    print("  IDOLUSDT not in scratch data")
    # Use IDOL calibration case
    idol_path = BOT_ROOT / "docs" / "case study" / "IDOL_result.txt"
    if idol_path.exists():
        f2, o2, r2, k2 = _replay.parse_result_file(idol_path)
        days_idol_c = _replay.build_days(f2, o2, r2, k2)
        chain_idol_c = {}
        for i, d in enumerate(days_idol_c):
            result = gs.eval_gom(days_idol_c, i, cfg, sc)
            chain_idol_c = gs.update_chain(chain_idol_c, "IDOL", days_idol_c, i, result, cfg, sc)
        gross = chain_idol_c.get("Q1_cum_usd", 0.0)
        net   = chain_idol_c.get("net_oi_delta_usd", float("nan"))
        churn = (not math.isnan(gross) and not math.isnan(net)
                 and net > 0 and gross > 2 * net)
        print(f"  IDOL calib state: gross={gross:,.0f}  net={net:,.0f}"
              if not math.isnan(net) else f"  IDOL calib state: gross={gross:,.0f}  net=N/A")
        print(f"  [churn]: {'YES' if churn else 'NO'}")
    else:
        print("  IDOL calib file not found either")

print("\nDone.")
