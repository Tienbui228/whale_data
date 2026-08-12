"""
[1] median14_oi cho i∈[Jul29..Aug11]: số thật hay NaN?
    _window skips NaN → effectively nanmedian. Cần confirm bằng số chạy thật.
[2] avg_px[i] cho i∈{Jul24,25,26}: NaN → skip-by-guard confirmed.
[3] Jul 24-26 gap: universal (VPS/API) hay BANANAS31-riêng (halt/delist)?
"""
import sys, math, pathlib, datetime
sys.path.insert(0, str(pathlib.Path(__file__).parent / "scripts"))

from fw_loader_utils import load_fw_csvs, taker_scale_check_df, build_token_days, load_funding_intervals

def _window(days, i, n, field):
    """Replicate signals._window: last n days ending at i, skip NaN."""
    start = max(0, i - n + 1)
    return [days[j][field] for j in range(start, i + 1)
            if not math.isnan(days[j].get(field, float("nan")))]

EXPORT_DIR = pathlib.Path("data/export")
CONFIG_DIR = pathlib.Path("data/config")

df_all = load_fw_csvs(EXPORT_DIR, up_to_date="2026-08-11", lookback_days=90)
df_all = taker_scale_check_df(df_all)
intervals = load_funding_intervals(CONFIG_DIR)
days, _ = build_token_days(df_all, "BANANAS31USDT", "2026-06-01", "2026-08-11", intervals)

BRK_DAYS = 5
from statistics import median as _median

def median14_oi(days, i):
    """Replicates signals._median14(days, i-brk_days, 'oi_usd') — same as _window skip-NaN."""
    anchor = i - BRK_DAYS  # i-5
    vals = _window(days, anchor, 14, "oi_usd")
    return _median(vals) if vals else float("nan")

# ── [1] median14_oi for i in Jul 29..Aug 11 ─────────────────────────────────
print("=== median14_oi at stealth_grind (iii) for i∈[Jul29..Aug11] ===")
print(f"R window = days[i-18..i-5]; synthetic NaN Jul24/25/26 = days[53,54,55]")
print(f"{'i':>4} {'date':>12} {'R_start':>10} {'R_end':>10} {'R_len(real)':>11} {'median14_oi':>13} {'NaN?':>6}")
print("-"*75)

for i, d in enumerate(days):
    date = d.get("date", "?")
    if date < "2026-07-29":
        continue
    anchor = i - BRK_DAYS
    r_start_idx = max(0, anchor - 14 + 1)
    r_end_idx   = anchor
    r_start_date = days[r_start_idx].get("date", "?")
    r_end_date   = days[r_end_idx].get("date", "?") if r_end_idx < len(days) else "?"
    vals = _window(days, anchor, 14, "oi_usd")
    med = _median(vals) if vals else float("nan")
    is_nan = math.isnan(med)
    print(f"{i:>4} {date:>12} {r_start_date:>10} {r_end_date:>10} {len(vals):>11} {med:>13,.0f} {'NaN' if is_nan else 'OK':>6}")

# ── [2] avg_px for synthetic days Jul 24/25/26 ───────────────────────────────
print("\n=== avg_px[i] for Jul 24/25/26 (synthetic NaN days) ===")
for i, d in enumerate(days):
    date = d.get("date", "?")
    if date in ("2026-07-24", "2026-07-25", "2026-07-26"):
        px = d.get("avg_px", float("nan"))
        oi = d.get("oi_usd", float("nan"))
        print(f"  i={i} {date}: avg_px={px}  oi_usd={oi}  _synthetic={d.get('_suspect','?')}")

# ── [3] Jul 24-26 gap: how many tokens also absent those dates? ──────────────
print("\n=== Jul 24-26 gap: universal vs BANANAS31-specific ===")
import csv
gap_dates = {"2026-07-24", "2026-07-25", "2026-07-26"}
found_by_date = {d: set() for d in gap_dates}  # date → set of tokens present

# First pass: collect gap dates presence
for fpath in sorted(EXPORT_DIR.glob("freshwatch_daily_2026-07.csv")):
    with open(fpath) as f:
        reader = csv.DictReader(f)
        for row in reader:
            dt = row.get("date", "")
            sym = row.get("symbol", "")
            if dt in gap_dates:
                found_by_date[dt].add(sym)

adj_dates = {"2026-07-23", "2026-07-27"}
total_tokens_by_date = {d: set() for d in adj_dates}

for fpath in sorted(EXPORT_DIR.glob("freshwatch_daily_2026-07.csv")):
    with open(fpath) as f:
        reader = csv.DictReader(f)
        for row in reader:
            dt = row.get("date", "")
            sym = row.get("symbol", "")
            if dt in gap_dates:
                found_by_date[dt].add(sym)
            if dt in adj_dates:
                total_tokens_by_date[dt].add(sym)

adj_tokens = total_tokens_by_date.get("2026-07-23", set()) | total_tokens_by_date.get("2026-07-27", set())
print(f"Tokens present Jul 23 or Jul 27 (adjacent): {len(adj_tokens)}")
for gd in sorted(gap_dates):
    present = found_by_date[gd]
    absent_count = len(adj_tokens) - len(present)
    print(f"  {gd}: {len(present)} tokens present, ~{absent_count} absent")
    if present:
        print(f"    tokens present: {sorted(present)[:5]}{'...' if len(present)>5 else ''}")

b31_gap = {d for d in gap_dates if "BANANAS31USDT" not in found_by_date[d]}
print(f"  BANANAS31USDT absent on: {sorted(b31_gap)}")
if len(found_by_date.get("2026-07-24", set())) == 0:
    print("  → UNIVERSAL GAP (0 tokens on Jul 24-26) = VPS/API collection issue")
else:
    print("  → PARTIAL gap = BANANAS31 may have had token-specific event")
