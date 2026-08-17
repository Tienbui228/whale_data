"""
_probe_spot_analysis_20260817.py
S-6: Analysis numbers for _spot_venue_patch_20260817.md
"""
import sys, io, csv
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path

SCRATCH = Path(r"D:\Data back test\whale_data\scratch")

def load_csv(path):
    rows = list(csv.DictReader(open(path, encoding="utf-8")))
    for r in rows:
        r["_qv"] = float(r["quote_vol"]) if r["quote_vol"] else 0
        r["_close"] = float(r["close"]) if r["close"] else 0
    return rows

ain = load_csv(SCRATCH / "spot_klines_AIN_20260817.csv")
gua = load_csv(SCRATCH / "spot_klines_GUA_20260817.csv")
apr = load_csv(SCRATCH / "spot_klines_APR_20260817.csv")

print("="*60)
print("AIN analysis (ALPHA_260, venue=binance_alpha)")
print("="*60)

ain_jul  = [r for r in ain if "2026-07" in r["date"]]
ain_aug4 = [r for r in ain if "2026-08-04" <= r["date"] <= "2026-08-15"]  # Aug16 partial
ain_aug16 = next((r for r in ain if r["date"] == "2026-08-16"), None)

jul_avg = sum(r["_qv"] for r in ain_jul) / len(ain_jul) if ain_jul else 0
aug4_avg = sum(r["_qv"] for r in ain_aug4) / len(ain_aug4) if ain_aug4 else 0

print(f"Jul avg vol: {jul_avg:,.0f} USD/day ({len(ain_jul)} days)")
print(f"Aug04-15 avg vol: {aug4_avg:,.0f} USD/day ({len(ain_aug4)} days)")
vol_change_pct = (aug4_avg - jul_avg) / jul_avg * 100 if jul_avg else 0
print(f"Vol change Jul→Aug04+: {vol_change_pct:+.1f}%")

# Exit days at current price
price_aug16 = ain_aug16["_close"] if ain_aug16 else float(ain[-1]["_close"])
print(f"Price Aug16: {price_aug16:.6f}")

supply_tokens = 30_000_000
supply_usd = supply_tokens * price_aug16
print(f"Deposit estimate: {supply_tokens:,} tokens × {price_aug16:.6f} = ${supply_usd:,.0f}")

# Use MEXC 24h vol for CEX exit calc (WASH flagged, but best CEX estimate)
mexc_vol_24h = 88_553
print(f"\nExit days (MEXC top CEX vol 88,553 USD/day — WASH 31.3x):")
for pct in [0.10, 0.30]:
    days = supply_usd / (mexc_vol_24h * pct)
    print(f"  {pct*100:.0f}% participation: {days:.1f} days")

# Use Alpha vol (more reliable)
alpha_vol = aug4_avg
print(f"\nExit days (Alpha 02:00 vol {alpha_vol:,.0f} USD/day):")
for pct in [0.10, 0.30]:
    days = supply_usd / (alpha_vol * pct)
    print(f"  {pct*100:.0f}% participation: {days:.1f} days")

print(f"\nTop 3 dates by vol:")
for r in sorted(ain, key=lambda x: x["_qv"], reverse=True)[:3]:
    print(f"  {r['date']}: {r['_qv']:,.0f} USD")

print()
print("="*60)
print("GUA analysis (ALPHA_483, venue=binance_alpha)")
print("="*60)

gua_jul  = [r for r in gua if "2026-07" in r["date"]]
gua_aug5 = [r for r in gua if "2026-08-05" <= r["date"] <= "2026-08-11"]

gua_jul_avg  = sum(r["_qv"] for r in gua_jul)  / len(gua_jul)  if gua_jul  else 0
gua_aug5_avg = sum(r["_qv"] for r in gua_aug5) / len(gua_aug5) if gua_aug5 else 0

print(f"Jul avg vol: {gua_jul_avg:,.0f} USD/day ({len(gua_jul)} days)")
print(f"Aug05-11 avg vol: {gua_aug5_avg:,.0f} USD/day ({len(gua_aug5)} days)")
gua_chg = (gua_aug5_avg - gua_jul_avg) / gua_jul_avg * 100 if gua_jul_avg else 0
print(f"Vol change: {gua_chg:+.1f}%")

print(f"\nTop 5 dates by vol:")
for r in sorted(gua, key=lambda x: x["_qv"], reverse=True)[:5]:
    print(f"  {r['date']}: {r['_qv']:,.0f} USD close={r['_close']:.6f}")

print()
print("="*60)
print("APR analysis (venue=kucoin, wash_suspect_flag=True)")
print("="*60)

apr_jul  = [r for r in apr if "2026-07" in r["date"]]
apr_aug  = [r for r in apr if r["date"] >= "2026-08-01"]

apr_jul_avg = sum(r["_qv"] for r in apr_jul) / len(apr_jul) if apr_jul else 0
apr_aug_avg = sum(r["_qv"] for r in apr_aug) / len(apr_aug) if apr_aug else 0
print(f"Jul avg vol: {apr_jul_avg:,.0f} USD/day ({len(apr_jul)} days)")
print(f"Aug01-16 avg vol: {apr_aug_avg:,.0f} USD/day ({len(apr_aug)} days)")

print(f"\nTop 5 dates by vol:")
for r in sorted(apr, key=lambda x: x["_qv"], reverse=True)[:5]:
    print(f"  {r['date']}: {r['_qv']:,.0f} USD close={r['_close']:.4f}")

# Aug14-16 spike
aug14_16 = [r for r in apr if "2026-08-14" <= r["date"] <= "2026-08-16"]
if aug14_16:
    print(f"\nAug14-16 spike: {sum(r['_qv'] for r in aug14_16):,.0f} total")
    for r in aug14_16:
        print(f"  {r['date']}: {r['_qv']:,.0f} USD close={r['_close']:.4f}")

claim_usd = 42_600_000
kucoin_today = 1_509_837
print(f"\nClaim vs reality: $42.6M/day claim vs KuCoin {kucoin_today:,} USD (ratio={claim_usd/kucoin_today:.0f}x off)")
print("Note: DEX BSC vol={$758} negligible. APR is CEX-only market.")

print("\n[DONE S-6 analysis]")
