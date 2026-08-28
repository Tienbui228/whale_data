"""MA-SHADOW backtest-phân-bố · consumer đầu tiên của backfill spot-51 · KÝ 01/09

Per bot-signals gom_detect_spec §1-H MA-SHADOW block + yaml ma_shadow:
  vol_spot ≥ [1.0]×med14 AND |ret| ≤ [3%] AND taker_spot ≤ [45%]
  → dòng shadow "MA?" cạnh alert (SHADOW · không compose · không conf)

Same D3 khuôn:
  · yaml-source (đọc ma_shadow block bot-signals)
  · sentinel 3-giá-trị (N/A-COVERAGE nếu <14 obs · N/A-DATA nếu store thiếu)
  · KHÔNG kết luận · bảng phân bố cho ANALYSIS 27/09

Metrics per token per day (window_end):
  · med14_vol = median(quote_vol) 14d trailing
  · vol_ratio = quote_vol_today / med14_vol
  · ret_1d    = close_today / close_yest - 1
  · taker     = taker_buy_pct (fraction * 100 → %)
  · MA-fire   = vol_ratio ≥ 1.0 AND |ret_1d| ≤ 3% AND taker ≤ 45%

Output: phân bố MA-fire per token · rate global · per-token n_fire · YAML source pin.
"""
import sys, io, csv, hashlib, glob
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
from statistics import median
import pandas as pd
import yaml

ROOT = Path(r"D:\Data back test\whale_data")
BOT_YAML = Path(r"D:/Data back test/binance-bot-signals/screen_thresholds.yaml")
STORE = ROOT / "data" / "raw" / "spot_klines_1d"
OUT_CSV = ROOT / "docs" / "reports" / "ma_shadow_backtest_20260828.csv"

# Load yaml ma_shadow (source of truth)
with open(BOT_YAML, encoding="utf-8") as f:
    yaml_data = yaml.safe_load(f)
ma_cfg = yaml_data["ma_shadow"]
VOL_X = ma_cfg["vol_x"]           # ≥ 1.0 × med14
RET_ABS = ma_cfg["ret_abs"]        # |ret| ≤ 0.03
TAKER_MAX = ma_cfg["taker_max"]    # ≤ 0.45 (fraction) — but store uses percentage 0-100
OBS_MIN = 14
print(f"[YAML SOURCE] bot-signals ma_shadow: vol_x={VOL_X} · ret_abs={RET_ABS} · taker_max={TAKER_MAX} (frac) → convert to pct * 100")
TAKER_MAX_PCT = TAKER_MAX * 100  # 45

# Load store binance_spot
files = sorted(glob.glob(str(STORE / "date=*/part-0.parquet")))
frames = [pd.read_parquet(f, columns=["symbol","date_str","close","quote_vol","taker_buy_pct","venue"]) for f in files]
all_df = pd.concat(frames, ignore_index=True)
all_df = all_df[all_df["venue"]=="binance_spot"].sort_values(["symbol","date_str"]).reset_index(drop=True)
print(f"[LOAD] binance_spot rows: {len(all_df)} · sym: {all_df['symbol'].nunique()}")

# Per-symbol series
records = []
symbols = sorted(all_df["symbol"].unique())
for sym in symbols:
    g = all_df[all_df["symbol"]==sym].sort_values("date_str").reset_index(drop=True)
    n = len(g)
    if n < OBS_MIN + 1:  # need at least 14 for med14 + 1 for ret
        continue
    for i in range(1, n):
        # med14 vol over trailing 14 days (i-13..i-0 = last 14 days including today · or i-14..i-1 = trailing 14)
        # Use i-14..i-1 (trailing, not including today) for med14
        if i < 14: continue
        vols = g["quote_vol"].iloc[i-14:i].tolist()  # 14 days before today
        vols_valid = [v for v in vols if v is not None and v > 0]
        if len(vols_valid) < OBS_MIN:
            continue  # N/A-COVERAGE
        med14 = median(vols_valid)
        if med14 <= 0: continue
        today_vol = g["quote_vol"].iloc[i]
        today_close = g["close"].iloc[i]
        yest_close = g["close"].iloc[i-1]
        today_taker = g["taker_buy_pct"].iloc[i]
        if today_vol is None or today_close is None or yest_close is None or today_taker is None: continue
        if today_vol <= 0 or today_close <= 0 or yest_close <= 0: continue
        vol_ratio = today_vol / med14
        ret_1d = today_close / yest_close - 1.0
        ma_fire = (vol_ratio >= VOL_X) and (abs(ret_1d) <= RET_ABS) and (today_taker <= TAKER_MAX_PCT)
        records.append({
            "symbol": sym, "date": g["date_str"].iloc[i],
            "vol_ratio": vol_ratio, "ret_1d": ret_1d,
            "taker_pct": today_taker, "med14_vol": med14, "quote_vol": today_vol,
            "ma_fire": ma_fire,
        })

n_all = len(records)
n_fire = sum(1 for r in records if r["ma_fire"])
rate_global = n_fire / n_all if n_all else 0
print(f"\n[MA-FIRE global] {n_fire}/{n_all} = {rate_global:.2%}")

# Per-symbol tally
per_sym = {}
for r in records:
    s = per_sym.setdefault(r["symbol"], {"n":0, "n_fire":0})
    s["n"] += 1
    if r["ma_fire"]: s["n_fire"] += 1
per_sym_sorted = sorted(per_sym.items(), key=lambda x: -x[1]["n_fire"])
print(f"\n[PER-SYMBOL top-10 by n_fire]:")
for sym, s in per_sym_sorted[:10]:
    r = s["n_fire"]/s["n"] if s["n"] else 0
    print(f"  {sym:<14} n={s['n']:>4} n_fire={s['n_fire']:>4} rate={r:.2%}")

# Distribution stats
fires = [r for r in records if r["ma_fire"]]
if fires:
    vr = [r["vol_ratio"] for r in fires]
    ret = [abs(r["ret_1d"]) for r in fires]
    tk = [r["taker_pct"] for r in fires]
    print(f"\n[FIRE-DAYS DISTRIBUTION]:")
    print(f"  vol_ratio: median={median(vr):.2f} · p75={sorted(vr)[int(len(vr)*0.75)]:.2f} · max={max(vr):.2f}")
    print(f"  |ret_1d|:  median={median(ret):.2%} · p75={sorted(ret)[int(len(ret)*0.75)]:.2%} · max={max(ret):.2%}")
    print(f"  taker_pct: median={median(tk):.2f} · p75={sorted(tk)[int(len(tk)*0.75)]:.2f} · min={min(tk):.2f}")

# ── Write CSV ──
OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
with open(OUT_CSV, "w", encoding="utf-8", newline="") as f:
    f.write(f"# MA-SHADOW backtest-phân-bố · consumer đầu tiên backfill spot-51 · KÝ 01/09\n")
    f.write(f"# YAML source (bot-signals canonical): ma_shadow · vol_x={VOL_X} · ret_abs={RET_ABS} · taker_max={TAKER_MAX} (frac)\n")
    f.write(f"# obs_min={OBS_MIN} · sentinel 3-giá-trị (fire · no-fire · N/A-COVERAGE if <14 obs)\n")
    f.write(f"# Store: data/raw/spot_klines_1d venue=binance_spot ({len(all_df)} rows · {all_df['symbol'].nunique()} sym)\n")
    f.write(f"# Metrics: vol_ratio = quote_vol_today / med14(trailing 14d) · ret_1d = close/close_yest − 1 · taker = taker_buy_pct\n")
    f.write(f"# MA-fire = vol_ratio ≥ {VOL_X} AND |ret_1d| ≤ {RET_ABS} AND taker ≤ {TAKER_MAX_PCT:.0f}%\n")
    f.write(f"#\n")
    f.write(f"# ─── GLOBAL RATE ───\n")
    f.write(f"#   MA-fire: {n_fire}/{n_all} = {rate_global:.2%}\n")
    f.write(f"#\n")
    f.write(f"# ─── PER-SYMBOL n_fire (top 20 by n_fire) ───\n")
    for sym, s in per_sym_sorted[:20]:
        r = s["n_fire"]/s["n"] if s["n"] else 0
        f.write(f"#   {sym:<14} n={s['n']:>4} n_fire={s['n_fire']:>4} rate={r:.2%}\n")
    if fires:
        vr = [r["vol_ratio"] for r in fires]
        ret = [abs(r["ret_1d"]) for r in fires]
        tk = [r["taker_pct"] for r in fires]
        f.write(f"#\n")
        f.write(f"# ─── FIRE-DAYS DISTRIBUTION ───\n")
        f.write(f"#   vol_ratio: median={median(vr):.2f} · p75={sorted(vr)[int(len(vr)*0.75)]:.2f} · max={max(vr):.2f}\n")
        f.write(f"#   |ret_1d|:  median={median(ret):.2%} · p75={sorted(ret)[int(len(ret)*0.75)]:.2%} · max={max(ret):.2%}\n")
        f.write(f"#   taker_pct: median={median(tk):.2f} · p75={sorted(tk)[int(len(tk)*0.75)]:.2f} · min={min(tk):.2f}\n")
    f.write(f"#\n")
    f.write(f"# KHÔNG kết luận — phân bố cho ANALYSIS 27/09 (bundle MA-only 3 ô review)\n")
    f.write(f"#\n")
    w = csv.DictWriter(f, fieldnames=["symbol","date","vol_ratio","ret_1d","taker_pct","med14_vol","quote_vol","ma_fire"])
    w.writeheader()
    for r in records:
        w.writerow({
            "symbol":r["symbol"], "date":r["date"],
            "vol_ratio":f"{r['vol_ratio']:.4f}",
            "ret_1d":f"{r['ret_1d']:.6f}",
            "taker_pct":f"{r['taker_pct']:.4f}",
            "med14_vol":f"{r['med14_vol']:.2f}",
            "quote_vol":f"{r['quote_vol']:.2f}",
            "ma_fire":r["ma_fire"],
        })

md5_out = hashlib.md5(OUT_CSV.read_bytes()).hexdigest()
n_lines = sum(1 for _ in open(OUT_CSV, encoding="utf-8"))
print(f"\n[OUT] {OUT_CSV.relative_to(ROOT)}")
print(f"[MD5] {md5_out}")
print(f"[WC ] {n_lines}")
