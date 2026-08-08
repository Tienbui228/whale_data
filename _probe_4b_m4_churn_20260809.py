"""4b: M4 gross/net/churn arithmetic test.
Tests (direct arithmetic, NOT through eval_gom pipeline):
  1. IDOL fixture: OI series from scratch 07-27 to 07-31
     gross = sum(max(delta_oi, 0)) = ~4.11M
     net   = oi_end - oi_start = ~2.2M
     churn = gross > 2*net? -> NO (borderline)
  2. Synthetic positive churn: (+3,-2.5,+3,-2.5) relative to 10M base
     gross = 6M, net = 1M, churn = YES
"""
import sys, math
from pathlib import Path
sys.path.insert(0, "scripts")

import pandas as pd

SCRATCH = Path("scratch")

def load_idol_oi():
    frames = []
    for fn in ["freshwatch_daily_2026-06.csv",
               "freshwatch_daily_2026-07.csv",
               "freshwatch_daily_2026-08.csv"]:
        p = SCRATCH / fn
        if p.exists():
            frames.append(pd.read_csv(p))
    if not frames:
        return []
    df = pd.concat(frames, ignore_index=True)
    df = df[df["symbol"] == "IDOLUSDT"].copy()
    df = df[(df["date"] >= "2026-07-26") & (df["date"] <= "2026-07-31")]
    df = df.sort_values("date").reset_index(drop=True)
    return df[["date", "oi_usd"]].to_dict("records")

def churn_arithmetic(oi_series):
    """
    oi_series: list of float (daily OI USD values)
    Returns: gross_adds, net_delta, churn_flag
    gross_adds = sum(max(delta_oi, 0)) for all consecutive pairs
    net_delta  = oi_last - oi_start
    churn      = gross_adds > 2 * net_delta (and net > 0)
    """
    if len(oi_series) < 2:
        return 0.0, float("nan"), False
    oi_start = oi_series[0]
    oi_last  = oi_series[-1]
    gross = sum(max(oi_series[j] - oi_series[j-1], 0.0)
                for j in range(1, len(oi_series)))
    net   = oi_last - oi_start
    churn = (net > 0 and gross > 2 * net)
    return gross, net, churn

print("=" * 60)
print("(1) IDOL fixture: OI series 07-27 to 07-31")
print("=" * 60)

rows = load_idol_oi()
if rows:
    print("  date         oi_usd         delta_oi")
    prev = None
    oi_vals = []
    for r in rows:
        oi = r["oi_usd"]
        if math.isnan(float(oi if oi is not None else "nan")):
            print(f"  {r['date']}   N/A")
            continue
        oi = float(oi)
        oi_vals.append(oi)
        delta = oi - prev if prev is not None else 0.0
        sign = "+" if delta >= 0 else ""
        print(f"  {r['date']}   ${oi:>12,.0f}   {sign}{delta/1e6:.3f}M")
        prev = oi

    if len(oi_vals) >= 2:
        gross, net, churn = churn_arithmetic(oi_vals)
        print(f"\n  gross_adds = ${gross/1e6:.3f}M  (sum of max(deltaOI,0))")
        print(f"  net_delta  = ${net/1e6:.3f}M   (oi_end - oi_start)")
        print(f"  2 * net    = ${2*net/1e6:.3f}M")
        print(f"  churn?     = {'YES' if churn else 'NO'} (gross {'>' if gross > 2*net else '<='} 2*net)")

        ok_gross = 4.0e6 < gross < 4.5e6
        ok_net   = 2.0e6 < net   < 2.5e6
        ok_churn = not churn  # expect NO
        print(f"\n  gross in [4.0M,4.5M]: {'PASS' if ok_gross else 'FAIL'}")
        print(f"  net   in [2.0M,2.5M]: {'PASS' if ok_net   else 'FAIL'}")
        print(f"  churn = NO:           {'PASS' if ok_churn else 'FAIL'}")
    else:
        print("  WARN: not enough OI data rows")
else:
    print("  WARN: IDOLUSDT not in scratch data")
    print("  Using hardcoded values from probe_b22 output:")
    # From probe_b22: 07-27=6,602,997  07-28=10,710,506  07-29=9,909,666  07-30=8,867,578  07-31=8,805,698
    oi_vals = [6_602_997, 10_710_506, 9_909_666, 8_867_578, 8_805_698]
    gross, net, churn = churn_arithmetic(oi_vals)
    print(f"  gross_adds = ${gross/1e6:.3f}M")
    print(f"  net_delta  = ${net/1e6:.3f}M")
    print(f"  churn? = {'YES' if churn else 'NO'}")

print()
print("=" * 60)
print("(2) Synthetic positive churn: +3,-2.5,+3,-2.5 relative to 10M")
print("=" * 60)

synth_oi = [10_000_000, 13_000_000, 10_500_000, 13_500_000, 11_000_000]
print("  OI series (M): " + ", ".join(f"{v/1e6:.1f}" for v in synth_oi))
gross_s, net_s, churn_s = churn_arithmetic(synth_oi)
print(f"  gross_adds = ${gross_s/1e6:.1f}M")
print(f"  net_delta  = ${net_s/1e6:.1f}M")
print(f"  2 * net    = ${2*net_s/1e6:.1f}M")
print(f"  churn? = {'YES' if churn_s else 'NO'} (gross {'>' if gross_s > 2*net_s else '<='} 2*net)")

ok_gross_s = abs(gross_s - 6.5e6) < 0.5e6   # 6.5M gross (3M + 3.5M)
ok_net_s   = abs(net_s - 1e6) < 0.1e6       # 1M net
ok_churn_s = churn_s                          # expect YES
print(f"\n  gross ~6.5M:  {'PASS' if ok_gross_s else 'FAIL'} (got {gross_s/1e6:.1f}M)")
print(f"  net ~1M:      {'PASS' if ok_net_s else 'FAIL'} (got {net_s/1e6:.1f}M)")
print(f"  churn = YES:  {'PASS' if ok_churn_s else 'FAIL'}")

print("\nDone.")
