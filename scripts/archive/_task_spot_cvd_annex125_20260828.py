"""ANNEX-125 · SPOTCVD-20260901 · zero-call · KÝ 01/09

125 pass-windows (3-leg passed) từ D3 CSV → per-window forward-return + tokens tally
+ base-rate control ALL 30d windows.

Per pass-window:
  token · window_end · imb · pos_days · px_min30
  · fwd_ret_30d = max(close[+1..+30]) / close[window_end] − 1
  · fwd_ret_60d nếu có ≥60d data sau window_end
  · censored = True nếu <30d data sau window_end

Tóm:
  · n theo token (con nào lặp nhiều · concentration)
  · median/p75 fwd_ret_30d/60d
  · %fwd_ret ≥ +50% (runner §5 TP threshold — GÓI-NHẸ ĐÃ KÝ 29/08)
  · Base-rate control: % ALL 30d windows in store có fwd_ret ≥ +50%

CSV + md5 + wc. KHÔNG kết luận — bảng quyết-định cho ANALYSIS.
"""
import sys, io, csv, hashlib, glob
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
from statistics import median
import pandas as pd

ROOT = Path(r"D:\Data back test\whale_data")
STORE = ROOT / "data" / "raw" / "spot_klines_1d"
D3_CSV = ROOT / "docs" / "reports" / "spot_cvd_d3_backtest_20260828.csv"
OUT_CSV = ROOT / "docs" / "reports" / "spot_cvd_annex125_20260828.csv"

TP_THRESHOLD = 0.50  # +50% runner §5 TP threshold

# ── Load D3 CSV, filter 3-leg pass ──
print(f"[LOAD] D3 CSV: {D3_CSV.relative_to(ROOT)}")
d3_rows = []
with open(D3_CSV, encoding="utf-8") as f:
    for line in f:
        if line.startswith("#") or line.startswith("symbol,"): continue
        parts = line.rstrip("\n").split(",")
        if len(parts) < 9: continue
        sym, dt, n_valid, cvd_30, vol_30, imb, pos, px, three_leg = parts[:9]
        if three_leg == "True":
            d3_rows.append({
                "symbol": sym, "date": dt,
                "imb": float(imb) if imb else None,
                "pos_days_pct": float(pos) if pos else None,
                "px_min30": float(px) if px else None,
            })
print(f"[LOAD] pass-windows: {len(d3_rows)}")

# ── Load store binance_spot for all symbols (need close series) ──
print(f"[LOAD] store binance_spot rows for close series")
files = sorted(glob.glob(str(STORE / "date=*/part-0.parquet")))
frames = []
for f in files:
    df = pd.read_parquet(f, columns=["symbol","date_str","close","venue"])
    df_spot = df[df["venue"] == "binance_spot"].copy()
    if len(df_spot):
        frames.append(df_spot)
all_df = pd.concat(frames, ignore_index=True)
all_df["date"] = pd.to_datetime(all_df["date_str"])
all_df = all_df.sort_values(["symbol","date"]).reset_index(drop=True)
print(f"[LOAD] rows: {len(all_df)} · symbols: {all_df['symbol'].nunique()}")

# Build per-symbol lookup: {sym: {date_str: close, sorted_dates: [...]}}
sym_series = {}
for sym in all_df["symbol"].unique():
    g = all_df[all_df["symbol"] == sym].sort_values("date_str").reset_index(drop=True)
    sym_series[sym] = {
        "dates": g["date_str"].tolist(),
        "closes": g["close"].tolist(),
    }
DATA_LAST = max(all_df["date_str"].unique())
print(f"[LOAD] data_last_date: {DATA_LAST}")

# ── Compute fwd_ret per pass-window ──
def _fwd_ret(sym, end_date, n_days):
    """Return (fwd_ret, censored). fwd_ret = max(close[+1..+n_days])/close[end] − 1."""
    s = sym_series.get(sym)
    if not s: return None, True
    try: end_idx = s["dates"].index(end_date)
    except ValueError: return None, True
    end_close = s["closes"][end_idx]
    if end_close <= 0: return None, True
    # Take closes[+1 .. +n_days]
    future_slice = s["closes"][end_idx+1 : end_idx+1+n_days]
    if not future_slice: return None, True
    censored = len(future_slice) < n_days
    max_future = max(future_slice)
    fwd_ret = max_future / end_close - 1.0
    return fwd_ret, censored

for r in d3_rows:
    r["fwd_ret_30d"], r["censored_30d"] = _fwd_ret(r["symbol"], r["date"], 30)
    r["fwd_ret_60d"], r["censored_60d"] = _fwd_ret(r["symbol"], r["date"], 60)

print(f"[ANNEX] fwd_ret computed for {len(d3_rows)} windows")

# ── Tokens tally ──
token_count = {}
for r in d3_rows:
    token_count[r["symbol"]] = token_count.get(r["symbol"], 0) + 1
token_sorted = sorted(token_count.items(), key=lambda x: -x[1])

# ── Distribution stats ──
def _pct(vals, thr): return sum(1 for v in vals if v is not None and v >= thr) / len(vals) if vals else 0

fwd30 = [r["fwd_ret_30d"] for r in d3_rows if r["fwd_ret_30d"] is not None]
fwd60 = [r["fwd_ret_60d"] for r in d3_rows if r["fwd_ret_60d"] is not None]

# Censored counts
n_cens_30 = sum(1 for r in d3_rows if r["censored_30d"])
n_cens_60 = sum(1 for r in d3_rows if r["censored_60d"])

print(f"\n[TALLY] pass-windows per token (top-10):")
for tok, cnt in token_sorted[:10]:
    print(f"  {tok:<14}  n={cnt}")
print(f"  ... TỔNG: {len(token_count)} tokens · {sum(token_count.values())} windows")

print(f"\n[DISTRIBUTION pass-windows]:")
print(f"  fwd_ret_30d: n={len(fwd30)}  median={median(fwd30):+.2%}  p75={sorted(fwd30)[int(len(fwd30)*0.75)]:+.2%}  min={min(fwd30):+.2%}  max={max(fwd30):+.2%}")
print(f"  %fwd_ret_30d ≥ +50%: {_pct(fwd30, TP_THRESHOLD):.2%}")
print(f"  censored_30d: {n_cens_30}/{len(d3_rows)}")
if fwd60:
    print(f"  fwd_ret_60d: n={len(fwd60)}  median={median(fwd60):+.2%}  p75={sorted(fwd60)[int(len(fwd60)*0.75)]:+.2%}")
    print(f"  %fwd_ret_60d ≥ +50%: {_pct(fwd60, TP_THRESHOLD):.2%}")
    print(f"  censored_60d: {n_cens_60}/{len(d3_rows)}")

# ── BASE-RATE control: ALL 30d windows in store (not just 3-leg pass) ──
print(f"\n[BASE-RATE control] ALL 30d windows fwd_ret ≥ +50%")
base_fwd30 = []
for sym, s in sym_series.items():
    n = len(s["closes"])
    for i in range(n):
        end_close = s["closes"][i]
        if end_close <= 0: continue
        future = s["closes"][i+1 : i+31]
        if len(future) < 30: continue  # exclude censored for fair base-rate
        max_fut = max(future)
        base_fwd30.append(max_fut / end_close - 1.0)
n_base_50 = sum(1 for v in base_fwd30 if v >= TP_THRESHOLD)
base_rate = n_base_50 / len(base_fwd30) if base_fwd30 else 0
print(f"  base_n: {len(base_fwd30)}")
print(f"  base_rate fwd≥+50%: {n_base_50}/{len(base_fwd30)} = {base_rate:.2%}")
print(f"  base median: {median(base_fwd30):+.2%}  p75: {sorted(base_fwd30)[int(len(base_fwd30)*0.75)]:+.2%}")

# For fair comparison, pass-window rate (uncensored only)
fwd30_uncens = [r["fwd_ret_30d"] for r in d3_rows if r["fwd_ret_30d"] is not None and not r["censored_30d"]]
n_pass_50 = sum(1 for v in fwd30_uncens if v >= TP_THRESHOLD)
pass_rate = n_pass_50 / len(fwd30_uncens) if fwd30_uncens else 0
print(f"\n[UNCENSORED COMPARE]")
print(f"  pass-window uncens rate fwd≥+50%: {n_pass_50}/{len(fwd30_uncens)} = {pass_rate:.2%}")
print(f"  base uncens rate fwd≥+50%:        {n_base_50}/{len(base_fwd30)} = {base_rate:.2%}")
print(f"  lift: {pass_rate - base_rate:+.2%} ({pass_rate/base_rate:.2f}x)" if base_rate else "  lift: N/A")

# ── Write CSV ──
OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
with open(OUT_CSV, "w", encoding="utf-8", newline="") as f:
    f.write(f"# ANNEX-125 · SPOTCVD-20260901 · zero-call · KÝ 01/09\n")
    f.write(f"# Source: docs/reports/spot_cvd_d3_backtest_20260828.csv md5 7154bcd0806248ba1687d08391b415b9 (D3 3-leg pass rows)\n")
    f.write(f"# Store: data/raw/spot_klines_1d venue=binance_spot ({len(all_df)} rows · {all_df['symbol'].nunique()} sym · last={DATA_LAST})\n")
    f.write(f"# fwd_ret_{{30d,60d}} = max(close[+1..+N]) / close[window_end] − 1\n")
    f.write(f"# censored_{{30d,60d}} = True nếu <N ngày data sau window_end\n")
    f.write(f"# TP threshold = {TP_THRESHOLD:+.0%} (runner §5 GÓI-NHẸ ĐÃ KÝ 29/08)\n")
    f.write(f"#\n")
    # Tokens tally
    f.write(f"# ─── TOKENS TALLY (n pass-windows per token, top-10) ───\n")
    for tok, cnt in token_sorted[:10]:
        f.write(f"#   {tok:<14}  n={cnt}\n")
    f.write(f"#   ... TỔNG: {len(token_count)} tokens · {sum(token_count.values())} windows\n")
    f.write(f"#\n")
    # Distribution
    f.write(f"# ─── DISTRIBUTION pass-windows ───\n")
    f.write(f"#   fwd_ret_30d: n={len(fwd30)} · median={median(fwd30):+.2%} · p75={sorted(fwd30)[int(len(fwd30)*0.75)]:+.2%} · min={min(fwd30):+.2%} · max={max(fwd30):+.2%}\n")
    f.write(f"#   %fwd_ret_30d ≥ +50%: {_pct(fwd30, TP_THRESHOLD):.2%}\n")
    f.write(f"#   censored_30d: {n_cens_30}/{len(d3_rows)}\n")
    if fwd60:
        f.write(f"#   fwd_ret_60d: n={len(fwd60)} · median={median(fwd60):+.2%} · p75={sorted(fwd60)[int(len(fwd60)*0.75)]:+.2%}\n")
        f.write(f"#   %fwd_ret_60d ≥ +50%: {_pct(fwd60, TP_THRESHOLD):.2%}\n")
        f.write(f"#   censored_60d: {n_cens_60}/{len(d3_rows)}\n")
    f.write(f"#\n")
    # Base-rate control
    f.write(f"# ─── BASE-RATE CONTROL (ALL 30d windows, uncensored) ───\n")
    f.write(f"#   base_n: {len(base_fwd30)}\n")
    f.write(f"#   base_rate fwd≥+50%: {n_base_50}/{len(base_fwd30)} = {base_rate:.2%}\n")
    f.write(f"#   base median: {median(base_fwd30):+.2%} · p75: {sorted(base_fwd30)[int(len(base_fwd30)*0.75)]:+.2%}\n")
    f.write(f"#\n")
    # Uncensored compare
    f.write(f"# ─── UNCENSORED COMPARE (fair rate vs base) ───\n")
    f.write(f"#   pass-window uncens rate fwd≥+50%: {n_pass_50}/{len(fwd30_uncens)} = {pass_rate:.2%}\n")
    f.write(f"#   base uncens rate fwd≥+50%:        {n_base_50}/{len(base_fwd30)} = {base_rate:.2%}\n")
    if base_rate > 0:
        f.write(f"#   lift: {pass_rate - base_rate:+.2%} ({pass_rate/base_rate:.2f}x)\n")
    f.write(f"# KHÔNG kết luận — bảng quyết-định cho ANALYSIS\n")
    f.write(f"#\n")
    # Records
    w = csv.DictWriter(f, fieldnames=["symbol","window_end","imb","pos_days_pct","px_min30",
                                       "fwd_ret_30d","censored_30d","fwd_ret_60d","censored_60d"])
    w.writeheader()
    for r in d3_rows:
        w.writerow({
            "symbol": r["symbol"], "window_end": r["date"],
            "imb": f"{r['imb']:.6f}", "pos_days_pct": f"{r['pos_days_pct']:.6f}",
            "px_min30": f"{r['px_min30']:.6f}",
            "fwd_ret_30d": f"{r['fwd_ret_30d']:.6f}" if r['fwd_ret_30d'] is not None else "",
            "censored_30d": r["censored_30d"],
            "fwd_ret_60d": f"{r['fwd_ret_60d']:.6f}" if r['fwd_ret_60d'] is not None else "",
            "censored_60d": r["censored_60d"],
        })

md5_out = hashlib.md5(OUT_CSV.read_bytes()).hexdigest()
n_lines = sum(1 for _ in open(OUT_CSV, encoding="utf-8"))
print(f"\n[OUT] {OUT_CSV.relative_to(ROOT)}")
print(f"[MD5] {md5_out}")
print(f"[WC ] {n_lines}")
