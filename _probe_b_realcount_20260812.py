"""
Xác nhận: B real-count cho i∈[Jul26..Jul30].
Câu: min real j trong B = bao nhiêu? Phải ≥ 2 để khe (ii) không FALSE-by-toàn-synthetic.
"""
import sys, math, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent / "scripts"))
from fw_loader_utils import load_fw_csvs, taker_scale_check_df, build_token_days, load_funding_intervals

EXPORT_DIR = pathlib.Path("data/export")
CONFIG_DIR = pathlib.Path("data/config")

df_all = load_fw_csvs(EXPORT_DIR, up_to_date="2026-08-11", lookback_days=90)
df_all = taker_scale_check_df(df_all)
intervals = load_funding_intervals(CONFIG_DIR)
days, _ = build_token_days(df_all, "BANANAS31USDT", "2026-06-01", "2026-08-11", intervals)

BRK_DAYS = 5
print("=== B real-count for i∈[Jul26..Jul30] ===")
print(f"Synthetic NaN days: Jul24=i53, Jul25=i54, Jul26=i55")
print(f"{'i':>4} {'date(i)':>12}  {'B window dates':>50}  {'real_oi':>8}  {'real_px':>8}")
print("-" * 90)

for i, d in enumerate(days):
    date_i = d.get("date", "?")
    if date_i < "2026-07-26":
        continue
    if date_i > "2026-07-30":
        break
    b_range = range(i - BRK_DAYS + 1, i + 1)
    b_dates = [days[j].get("date", "?") for j in b_range]
    real_oi = sum(1 for j in b_range if not math.isnan(days[j].get("oi_usd", float("nan"))))
    real_px = sum(1 for j in b_range if not math.isnan(days[j].get("avg_px", float("nan"))))
    b_dates_str = " ".join(d[-5:] for d in b_dates)  # MM-DD format
    print(f"{i:>4} {date_i:>12}  [{b_dates_str:>48}]  {real_oi:>8}  {real_px:>8}")

print()
print("min real_oi in B across Jul26-30 → (ii) never FALSE-by-toàn-synthetic if ≥ 2")
