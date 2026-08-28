"""D3 BACKTEST-CSV toàn history 51 token (SPOTCVD-20260901).

Per token per 30d rolling window:
  · CVD_day = (2·taker_buy_pct/100 − 1) × quote_vol   (USDT)
  · cvd_30 = Σ CVD_day trong cửa sổ 30d
  · imb    = cvd_30 / Σvol_30            ∈ [-1, 1]
  · pos_days = count(CVD_day > 0) / 30   ∈ [0, 1]
  · px_min30 = close / min(close cửa sổ 30d)

3-chân đồng thời (SPOTCVD gate PROVISIONAL):
  imb ≥ 0.05 AND pos_days ≥ 0.60 AND px_min30 ≤ 1.30

obs_min = 14: NaN-taker day KHÔNG đếm tử LẪN mẫu. Window ít hơn 14 non-NaN → KHÔNG chấm.

FALSIFIER bản-②: TUT 2026-06-01..09-30 có ≥1 cửa sổ 3-chân không?
  Có → in cửa sổ + giá trị (ứng viên pin D4)
  Không → nguyên văn: "khả năng chân px giết đúng hiện tượng — xử ở bàn" (KHÔNG nới số)

DEV-đề-cử: 1 negative-token (median |imb| ~0 phẳng) cho operator chọn.
"""
import sys, io, json, glob, hashlib, csv
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
from datetime import date, timedelta
import pandas as pd
from statistics import median

ROOT = Path(r"D:\Data back test\whale_data")
STORE = ROOT / "data" / "raw" / "spot_klines_1d"
YAML = ROOT / "screen_thresholds.yaml"
OUT_CSV = ROOT / "docs" / "reports" / "spot_cvd_d3_backtest_20260828.csv"

# Thresholds (PROVISIONAL per SPOTCVD-20260901 spec + bot-signals yaml spot_cvd block)
WINDOW = 30
OBS_MIN = 14
IMB_MIN = 0.05
POS_DAYS_MIN = 0.60
PX_OVER_MIN30_MAX = 1.30

# ── Load full store, filter binance_spot venue ──
files = sorted(glob.glob(str(STORE / "date=*/part-0.parquet")))
print(f"[LOAD] {len(files)} partitions")

frames = []
for f in files:
    df = pd.read_parquet(f, columns=["symbol","date_str","close","quote_vol","taker_buy_pct","venue"])
    df_spot = df[df["venue"] == "binance_spot"].copy()
    if len(df_spot):
        frames.append(df_spot)
all_df = pd.concat(frames, ignore_index=True)
print(f"[LOAD] binance_spot rows: {len(all_df)}")
print(f"[LOAD] unique symbols: {all_df['symbol'].nunique()}")

# Build daily series per symbol
all_df["date"] = pd.to_datetime(all_df["date_str"])
all_df = all_df.sort_values(["symbol","date"]).reset_index(drop=True)

# CVD_day (NaN nếu taker NaN)
def _cvd(row):
    if pd.isna(row["taker_buy_pct"]) or pd.isna(row["quote_vol"]): return None
    tb_frac = row["taker_buy_pct"] / 100.0
    return (2.0 * tb_frac - 1.0) * row["quote_vol"]

all_df["cvd_day"] = all_df.apply(_cvd, axis=1)

# ── Rolling per-symbol 30d windows ──
print(f"\n[BACKTEST] window={WINDOW}d · obs_min={OBS_MIN} · imb≥{IMB_MIN} · pos_days≥{POS_DAYS_MIN} · px_min30≤{PX_OVER_MIN30_MAX}")

records = []
symbols = sorted(all_df["symbol"].unique())
for sym in symbols:
    g = all_df[all_df["symbol"] == sym].sort_values("date").reset_index(drop=True)
    for i in range(len(g)):
        # Window = i-29..i (inclusive both ends → 30 days)
        lo = max(0, i - (WINDOW - 1))
        w = g.iloc[lo:i+1]
        if len(w) < WINDOW: continue  # need full 30 days
        # obs_min gate: number of non-NaN taker days
        w_valid = w.dropna(subset=["cvd_day"])
        n_valid = len(w_valid)
        if n_valid < OBS_MIN: continue
        # Metrics from valid rows only
        cvd_30 = w_valid["cvd_day"].sum()
        vol_30 = w_valid["quote_vol"].sum()
        imb = cvd_30 / vol_30 if vol_30 > 0 else None
        pos_days = (w_valid["cvd_day"] > 0).sum() / n_valid  # normalized by n_valid (obs_min gate)
        min_close_30 = w["close"].min()
        cur_close = w.iloc[-1]["close"]
        px_min30 = cur_close / min_close_30 if min_close_30 > 0 else None
        three_leg = None
        if imb is not None and px_min30 is not None:
            three_leg = (imb >= IMB_MIN) and (pos_days >= POS_DAYS_MIN) and (px_min30 <= PX_OVER_MIN30_MAX)
        records.append({
            "symbol": sym,
            "date": w.iloc[-1]["date_str"],
            "n_valid": n_valid,
            "cvd_30": cvd_30,
            "vol_30": vol_30,
            "imb": imb,
            "pos_days_pct": pos_days,
            "px_min30": px_min30,
            "three_leg_pass": three_leg,
        })

print(f"[BACKTEST] records: {len(records)}")

# ── FALSIFIER TUT bản-② ──
print(f"\n[FALSIFIER] TUT 2026-06-01..09-30 tìm cửa sổ 3-chân")
tut_records = [r for r in records if r["symbol"] == "TUTUSDT"
               and "2026-06-01" <= r["date"] <= "2026-09-30"]
tut_pass = [r for r in tut_records if r["three_leg_pass"]]
print(f"  TUT rows in window: {len(tut_records)}")
print(f"  TUT 3-leg pass count: {len(tut_pass)}")
if tut_pass:
    print(f"  Ứng viên pin D4 (top 5 by imb DESC):")
    tut_pass_sorted = sorted(tut_pass, key=lambda r: -r["imb"])
    for r in tut_pass_sorted[:5]:
        print(f"    {r['date']}: imb={r['imb']:+.4f} · pos_days={r['pos_days_pct']:.2%} · px_min30={r['px_min30']:.3f} · n_valid={r['n_valid']}")
    falsifier_verdict = f"FALSIFIER PASS: TUT có {len(tut_pass)} cửa sổ 3-chân trong 06-09/2026 (ứng viên pin D4)"
else:
    print(f"  TUT NO 3-leg window in 06-09/2026")
    print(f"  → Nguyên văn: 'khả năng chân px đang giết đúng hiện tượng — xử ở bàn' (KHÔNG nới số)")
    # Debug: show TUT best window (highest imb) with breakdown
    tut_by_imb = sorted([r for r in tut_records if r["imb"] is not None], key=lambda r: -r["imb"])
    if tut_by_imb:
        print(f"  TUT best-imb window (debug):")
        for r in tut_by_imb[:3]:
            legs = f"imb≥0.05={r['imb']>=IMB_MIN} · pos_days≥60%={r['pos_days_pct']>=POS_DAYS_MIN} · px_min30≤1.3={r['px_min30']<=PX_OVER_MIN30_MAX}"
            print(f"    {r['date']}: imb={r['imb']:+.4f} · pos_days={r['pos_days_pct']:.2%} · px_min30={r['px_min30']:.3f} · legs=[{legs}]")
    falsifier_verdict = "FALSIFIER FAIL: TUT KHÔNG cửa sổ 3-chân · chân px giết đúng hiện tượng — xử ở bàn (KHÔNG nới số)"

# ── DEV-đề-cử negative-token (median |imb| ~0 phẳng) ──
print(f"\n[DEV-ĐỀ-CỬ] negative-token (median |imb| ~0 phẳng)")
neg_stats = {}
for sym in symbols:
    sr = [r for r in records if r["symbol"] == sym and r["imb"] is not None]
    if len(sr) < 100: continue  # need enough history to be candidate
    abs_imb = [abs(r["imb"]) for r in sr]
    neg_stats[sym] = {"n": len(sr), "med_abs_imb": median(abs_imb),
                       "pass_count": sum(1 for r in sr if r["three_leg_pass"])}
# Sort by lowest median |imb|
neg_sorted = sorted(neg_stats.items(), key=lambda x: x[1]["med_abs_imb"])
print(f"  Top-5 flattest CVD (candidate negative-pin):")
for sym, s in neg_sorted[:5]:
    print(f"    {sym:<14}  n={s['n']}  med|imb|={s['med_abs_imb']:.5f}  3-leg_pass={s['pass_count']}")
neg_pick = neg_sorted[0][0] if neg_sorted else "N/A"

# ── Distribution stats for ANALYSIS ──
print(f"\n[DISTRIBUTION] phân bố cho ANALYSIS (all symbols)")
all_imb = [r["imb"] for r in records if r["imb"] is not None]
all_pos = [r["pos_days_pct"] for r in records if r["pos_days_pct"] is not None]
all_px = [r["px_min30"] for r in records if r["px_min30"] is not None]
n_pass = sum(1 for r in records if r["three_leg_pass"])
print(f"  n_records (valid, ≥14 obs): {len(records)}")
print(f"  imb        median={median(all_imb):+.4f}  min={min(all_imb):+.4f}  max={max(all_imb):+.4f}")
print(f"  pos_days   median={median(all_pos):.2%}  min={min(all_pos):.2%}  max={max(all_pos):.2%}")
print(f"  px_min30   median={median(all_px):.3f}  min={min(all_px):.3f}  max={max(all_px):.3f}")
print(f"  3-leg pass rate: {n_pass}/{len(records)} = {n_pass/len(records):.2%}")

# ── Per-symbol summary ──
per_sym_summary = {}
for sym in symbols:
    sr = [r for r in records if r["symbol"] == sym]
    imbs = [r["imb"] for r in sr if r["imb"] is not None]
    if not imbs: continue
    per_sym_summary[sym] = {"n": len(sr),
                             "med_imb": median(imbs),
                             "n_3leg": sum(1 for r in sr if r["three_leg_pass"])}

# ── Write CSV ──
OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
with open(OUT_CSV, "w", encoding="utf-8", newline="") as f:
    f.write(f"# SPOT-CVD D3 BACKTEST · SPOTCVD-20260901 · KÝ 01/09\n")
    f.write(f"# Window={WINDOW}d · obs_min={OBS_MIN} · imb_min={IMB_MIN} · pos_days_min={POS_DAYS_MIN} · px_over_min30_max={PX_OVER_MIN30_MAX}\n")
    f.write(f"# Source: data/raw/spot_klines_1d venue=binance_spot ({len(all_df)} rows · {all_df['symbol'].nunique()} symbols)\n")
    f.write(f"# CVD_day = (2·taker_buy_frac − 1) × quote_vol · NaN-taker day KHÔNG đếm tử lẫn mẫu\n")
    f.write(f"# imb = cvd_30 / vol_30 · pos_days = count(cvd_day>0)/n_valid · px_min30 = close/min(close_30d)\n")
    f.write(f"# 3-leg pass = imb≥{IMB_MIN} AND pos_days≥{POS_DAYS_MIN} AND px_min30≤{PX_OVER_MIN30_MAX}\n")
    f.write(f"#\n")
    f.write(f"# ─── FALSIFIER TUT bản-② (2026-06-01..09-30) ───\n")
    f.write(f"# {falsifier_verdict}\n")
    if tut_pass:
        f.write(f"# Top ứng viên pin D4:\n")
        for r in sorted(tut_pass, key=lambda x: -x["imb"])[:5]:
            f.write(f"#   {r['date']}: imb={r['imb']:+.4f} · pos_days={r['pos_days_pct']:.2%} · px_min30={r['px_min30']:.3f}\n")
    f.write(f"#\n")
    f.write(f"# ─── DEV-ĐỀ-CỬ negative-token (top-5 flattest CVD) ───\n")
    for sym, s in neg_sorted[:5]:
        f.write(f"#   {sym:<14}  n={s['n']}  med|imb|={s['med_abs_imb']:.5f}  3-leg_pass={s['pass_count']}\n")
    f.write(f"# ĐỀ CỬ: {neg_pick} (operator chọn cuối)\n")
    f.write(f"#\n")
    f.write(f"# ─── DISTRIBUTION (all valid records) ───\n")
    f.write(f"#   n_records: {len(records)}\n")
    f.write(f"#   imb        median={median(all_imb):+.4f}  min={min(all_imb):+.4f}  max={max(all_imb):+.4f}\n")
    f.write(f"#   pos_days   median={median(all_pos):.2%}  min={min(all_pos):.2%}  max={max(all_pos):.2%}\n")
    f.write(f"#   px_min30   median={median(all_px):.3f}  min={min(all_px):.3f}  max={max(all_px):.3f}\n")
    f.write(f"#   3-leg pass rate: {n_pass}/{len(records)} = {n_pass/len(records):.2%}\n")
    f.write(f"#\n")
    # Per-symbol summary
    f.write(f"# ─── PER-SYMBOL SUMMARY (median imb · n 3-leg pass) ───\n")
    for sym in sorted(per_sym_summary.keys()):
        s = per_sym_summary[sym]
        f.write(f"#   {sym:<14}  n={s['n']:>4}  med_imb={s['med_imb']:+.4f}  n_3leg={s['n_3leg']}\n")
    f.write(f"#\n")
    # Records
    w = csv.DictWriter(f, fieldnames=["symbol","date","n_valid","cvd_30","vol_30","imb","pos_days_pct","px_min30","three_leg_pass"])
    w.writeheader()
    for r in records:
        w.writerow({
            "symbol": r["symbol"],
            "date": r["date"],
            "n_valid": r["n_valid"],
            "cvd_30": f"{r['cvd_30']:.2f}",
            "vol_30": f"{r['vol_30']:.2f}",
            "imb": f"{r['imb']:.6f}" if r["imb"] is not None else "",
            "pos_days_pct": f"{r['pos_days_pct']:.6f}" if r["pos_days_pct"] is not None else "",
            "px_min30": f"{r['px_min30']:.6f}" if r["px_min30"] is not None else "",
            "three_leg_pass": r["three_leg_pass"],
        })

md5_out = hashlib.md5(OUT_CSV.read_bytes()).hexdigest()
n_lines = sum(1 for _ in open(OUT_CSV, encoding="utf-8"))
print(f"\n[OUT] {OUT_CSV.relative_to(ROOT)}")
print(f"[MD5] {md5_out}")
print(f"[WC ] {n_lines}")
