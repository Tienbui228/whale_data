"""
Scale verify: taker_buy_pct at point of comparison in stealth_grind.
1) Load BANANAS31 via fw_loader (same path as gom_scan) → print tb_window BEFORE < 55.0 check
2) Find high-taker token (raw > 0.55) → verify (iii) BLOCKS it
"""
import sys, math, pathlib, statistics

sys.path.insert(0, str(pathlib.Path(__file__).parent / "scripts"))

from fw_loader_utils import load_fw_csvs, taker_scale_check_df, build_token_days, load_funding_intervals

EXPORT_DIR = pathlib.Path("data/export")
CONFIG_DIR = pathlib.Path("data/config")

# ── Load freshwatch_daily (same as gom_scan run_full_rebuild) ──────────────────
df_all = load_fw_csvs(EXPORT_DIR, up_to_date="2026-08-11", lookback_days=90)
print(f"Loaded {len(df_all)} rows from freshwatch_daily, {df_all['symbol'].nunique()} symbols")

# ── Step 1: taker_scale_check_df (line 1138 in gom_scan) ─────────────────────
raw_b31 = df_all[df_all["symbol"] == "BANANAS31USDT"]["taker_buy_pct"].dropna()
print(f"\nBANANAS31 raw (pre-scale): min={raw_b31.min():.4f}  max={raw_b31.max():.4f}")

df_all = taker_scale_check_df(df_all)

b31_post = df_all[df_all["symbol"] == "BANANAS31USDT"]["taker_buy_pct"].dropna()
print(f"BANANAS31 post-scale:      min={b31_post.min():.2f}  max={b31_post.max():.2f}")

# ── Step 2: build_token_days for BANANAS31 ────────────────────────────────────
intervals = load_funding_intervals(CONFIG_DIR)
days_b31, _ = build_token_days(df_all, "BANANAS31USDT", "2026-06-01", "2026-08-11", intervals)
print(f"\nBANANAS31 DayData rows: {len(days_b31)}")

# ── Step 3: Print taker_buy_pct[j] INSIDE tb_window (B = days[i-4..i]) for several i ──
BRK_DAYS = 5
TB_MAX = 55.0

print("\n--- Actual taker_buy_pct[j] at stealth_grind (iii) comparison ---")
print(f"{'i':>4} {'date':>12}  {'tb_window values':>45}  {'max':>6}  {'<55?':>5}")
print("-" * 80)

for i in range(18, len(days_b31)):
    b_range = range(i - BRK_DAYS + 1, i + 1)
    tb_window = [days_b31[j]["taker_buy_pct"] for j in b_range
                 if not math.isnan(days_b31[j]["taker_buy_pct"])]
    if not tb_window:
        continue
    mx = max(tb_window)
    date = days_b31[i].get("date", "?")
    vals_str = ", ".join(f"{v:.2f}" for v in tb_window)
    flag = "PASS" if mx < TB_MAX else "BLOCK"
    print(f"{i:>4} {date:>12}  [{vals_str:>43}]  {mx:>6.2f}  {flag:>5}")
    if i >= 25:  # show first 8 evaluable, then skip to last 3
        break

# last 3
for i in range(len(days_b31)-3, len(days_b31)):
    b_range = range(i - BRK_DAYS + 1, i + 1)
    tb_window = [days_b31[j]["taker_buy_pct"] for j in b_range
                 if not math.isnan(days_b31[j]["taker_buy_pct"])]
    if not tb_window:
        continue
    mx = max(tb_window)
    date = days_b31[i].get("date", "?")
    vals_str = ", ".join(f"{v:.2f}" for v in tb_window)
    flag = "PASS" if mx < TB_MAX else "BLOCK"
    print(f"{i:>4} {date:>12}  [{vals_str:>43}]  {mx:>6.2f}  {flag:>5}")

# ── Step 4: Find high-taker tokens (raw > 0.55 before scale) ─────────────────
print("\n--- High-taker token cross-check ---")
# reload raw to find high-taker
df_raw = load_fw_csvs(EXPORT_DIR, up_to_date="2026-08-11", lookback_days=90)
by_sym = df_raw.groupby("symbol")["taker_buy_pct"].max()
high_taker = by_sym[by_sym > 0.55].sort_values(ascending=False)
print(f"Tokens with max raw taker > 0.55 (=55% after ×100): {len(high_taker)}")
print(high_taker.head(10).to_string())

if not high_taker.empty:
    test_tok = high_taker.index[0]
    raw_max = high_taker.iloc[0]
    print(f"\nTest token: {test_tok}, raw_max={raw_max:.4f} → post×100={raw_max*100:.2f}%")
    days_test, _ = build_token_days(df_all, test_tok, "2026-06-01", "2026-08-11", intervals)
    print(f"DayData rows: {len(days_test)}")
    blocked = 0
    for i in range(BRK_DAYS, len(days_test)):
        b_range = range(i - BRK_DAYS + 1, i + 1)
        tb_window = [days_test[j]["taker_buy_pct"] for j in b_range
                     if not math.isnan(days_test[j]["taker_buy_pct"])]
        if not tb_window:
            continue
        mx = max(tb_window)
        if mx >= TB_MAX:
            blocked += 1
            date = days_test[i].get("date", "?")
            print(f"  BLOCKED i={i} {date}: max_taker={mx:.2f}% >= 55.0")
            if blocked >= 3:
                break
    if blocked == 0:
        print(f"  WARNING: {test_tok} never blocked by (iii) — check scale!")
    else:
        print(f"  → (iii) IS blocking {test_tok} (scale correct)")
