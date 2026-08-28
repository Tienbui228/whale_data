"""ANNEX-125b · SPOTCVD-20260901 · zero-call · KÝ 01/09

Hai control trước verdict:
  (1) EPISODE TABLE luật-4: cụm pass-windows cùng token cách <14d = 1 episode
      → {token · episode_start · n_windows · best_fwd_ret_30d · hit≥+50%? · censored?}
      + tổng: n_episodes · hit-rate per-episode (uncensored)
  (2) PX-MATCHED CONTROL: mọi cửa sổ 30d px_min30 ≤ 1.3 (KHÔNG đòi CVD 2 chân)
      → base-rate-quiet fwd≥+50% uncensored, cùng thước §5
  (3) BA SỐ: pass-set · quiet-control · all-control
      Header L-64 khai mẫu số từng con (n, loại trừ gì, censor rule)

CSV + md5 + wc. KHÔNG kết luận.
"""
import sys, io, csv, hashlib, glob
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
from datetime import date, timedelta
from statistics import median
import pandas as pd

ROOT = Path(r"D:\Data back test\whale_data")
STORE = ROOT / "data" / "raw" / "spot_klines_1d"
D3_CSV = ROOT / "docs" / "reports" / "spot_cvd_d3_backtest_20260828.csv"
OUT_CSV = ROOT / "docs" / "reports" / "spot_cvd_annex125b_20260828.csv"

TP_THRESHOLD = 0.50
EPISODE_GAP = 14  # days: <14d gap → same episode (per operator luật-4)
PX_MIN30_MAX = 1.30  # quiet-control filter same as SPOTCVD gate

# ── Load D3 pass-windows ──
print(f"[LOAD] D3 CSV: {D3_CSV.relative_to(ROOT)}")
pass_rows = []
with open(D3_CSV, encoding="utf-8") as f:
    for line in f:
        if line.startswith("#") or line.startswith("symbol,"): continue
        parts = line.rstrip("\n").split(",")
        if len(parts) < 9: continue
        sym, dt, n_valid, cvd_30, vol_30, imb, pos, px, three_leg = parts[:9]
        if three_leg == "True":
            pass_rows.append({"symbol": sym, "date": dt,
                              "imb": float(imb), "pos_days_pct": float(pos),
                              "px_min30": float(px)})
print(f"[LOAD] pass-windows: {len(pass_rows)}")

# ── Load store binance_spot ──
files = sorted(glob.glob(str(STORE / "date=*/part-0.parquet")))
frames = []
for f in files:
    df = pd.read_parquet(f, columns=["symbol","date_str","close","venue"])
    df_spot = df[df["venue"] == "binance_spot"].copy()
    if len(df_spot): frames.append(df_spot)
all_df = pd.concat(frames, ignore_index=True).sort_values(["symbol","date_str"]).reset_index(drop=True)
print(f"[LOAD] binance_spot rows: {len(all_df)} · symbols: {all_df['symbol'].nunique()}")
DATA_LAST = max(all_df["date_str"].unique())
print(f"[LOAD] data_last: {DATA_LAST}")

sym_series = {}
for sym in all_df["symbol"].unique():
    g = all_df[all_df["symbol"] == sym].sort_values("date_str").reset_index(drop=True)
    sym_series[sym] = {"dates": g["date_str"].tolist(), "closes": g["close"].tolist()}

# ── Forward-return helper ──
def _fwd_ret(sym, end_date, n_days=30):
    s = sym_series.get(sym)
    if not s: return None, True
    try: idx = s["dates"].index(end_date)
    except ValueError: return None, True
    end_close = s["closes"][idx]
    if end_close <= 0: return None, True
    future = s["closes"][idx+1:idx+1+n_days]
    if not future: return None, True
    censored = len(future) < n_days
    return max(future) / end_close - 1.0, censored

# Attach fwd_ret_30d to pass_rows
for r in pass_rows:
    r["fwd_ret_30d"], r["censored_30d"] = _fwd_ret(r["symbol"], r["date"], 30)

# ── (1) EPISODE TABLE — cụm cùng token cách <14d = 1 episode ──
print(f"\n[EPISODE] cluster pass-windows cùng token, gap <{EPISODE_GAP}d = 1 episode")
episodes = []
by_sym = {}
for r in pass_rows:
    by_sym.setdefault(r["symbol"], []).append(r)

for sym in sorted(by_sym.keys()):
    rows = sorted(by_sym[sym], key=lambda x: x["date"])
    cur_episode = []
    prev_date = None
    for r in rows:
        cur_date = date.fromisoformat(r["date"])
        if prev_date is not None and (cur_date - prev_date).days >= EPISODE_GAP:
            episodes.append(_build_episode(sym, cur_episode)) if cur_episode else None
            cur_episode = []
        cur_episode.append(r)
        prev_date = cur_date
    if cur_episode:
        episodes.append(_build_episode := None)  # placeholder, real below

# Redo cleanly
episodes = []
for sym in sorted(by_sym.keys()):
    rows = sorted(by_sym[sym], key=lambda x: x["date"])
    cur = []; prev_date = None
    for r in rows:
        cur_date = date.fromisoformat(r["date"])
        if prev_date is not None and (cur_date - prev_date).days >= EPISODE_GAP:
            if cur: episodes.append(cur); cur = []
        cur.append(r); prev_date = cur_date
    if cur: episodes.append(cur)

print(f"[EPISODE] n_episodes: {len(episodes)}")

# Build episode summary
ep_records = []
for ep in episodes:
    sym = ep[0]["symbol"]
    ep_start = ep[0]["date"]
    ep_end = ep[-1]["date"]
    n_win = len(ep)
    # best_fwd_ret_30d = max across windows in episode
    fwds = [(w["fwd_ret_30d"], w["censored_30d"]) for w in ep if w["fwd_ret_30d"] is not None]
    if fwds:
        best_fwd, _ = max(fwds, key=lambda x: x[0])
        # censored: True if best window is censored (last window matters for horizon)
        # More conservative: any window censored = episode censored (data cắt trước 30d)
        ep_censored = any(c for _, c in fwds) or any(w["censored_30d"] for w in ep)
    else:
        best_fwd = None; ep_censored = True
    hit_50 = (best_fwd is not None and best_fwd >= TP_THRESHOLD)
    ep_records.append({
        "symbol": sym, "episode_start": ep_start, "episode_end": ep_end,
        "n_windows": n_win, "best_fwd_ret_30d": best_fwd,
        "hit_ge_50pct": hit_50, "censored": ep_censored,
    })

# Episode stats
uncens_eps = [e for e in ep_records if not e["censored"]]
n_uncens = len(uncens_eps)
n_hit_uncens = sum(1 for e in uncens_eps if e["hit_ge_50pct"])
hit_rate_uncens = n_hit_uncens / n_uncens if n_uncens else 0.0
print(f"[EPISODE] uncensored episodes: {n_uncens}/{len(episodes)}")
print(f"[EPISODE] hit-rate ≥+50% per-episode (uncens): {n_hit_uncens}/{n_uncens} = {hit_rate_uncens:.2%}")

# ── (2) PX-MATCHED CONTROL — mọi cửa sổ 30d với px_min30 ≤ 1.3 ──
print(f"\n[PX-MATCHED CONTROL] mọi cửa sổ 30d px_min30 ≤ {PX_MIN30_MAX}")
quiet_windows = []
all_windows_30d = []  # for all-control base
for sym, s in sym_series.items():
    closes = s["closes"]
    dates = s["dates"]
    n = len(closes)
    for i in range(29, n):  # i = window_end index (0-indexed), min i=29 for 30d window
        window_closes = closes[i-29:i+1]  # 30 days inclusive
        if len(window_closes) < 30: continue
        end_close = closes[i]
        min_close = min(window_closes)
        if min_close <= 0 or end_close <= 0: continue
        px_min30 = end_close / min_close
        # Forward return uncensored only (need 30d ahead)
        future = closes[i+1:i+31]
        if len(future) < 30: continue  # uncensored
        fwd = max(future) / end_close - 1.0
        all_windows_30d.append(fwd)
        if px_min30 <= PX_MIN30_MAX:
            quiet_windows.append(fwd)

n_all = len(all_windows_30d)
n_all_hit = sum(1 for v in all_windows_30d if v >= TP_THRESHOLD)
rate_all = n_all_hit / n_all if n_all else 0

n_quiet = len(quiet_windows)
n_quiet_hit = sum(1 for v in quiet_windows if v >= TP_THRESHOLD)
rate_quiet = n_quiet_hit / n_quiet if n_quiet else 0

# Pass-set uncensored (same rule) — from D3 pass_rows
pass_uncens = [r["fwd_ret_30d"] for r in pass_rows if r["fwd_ret_30d"] is not None and not r["censored_30d"]]
n_pass = len(pass_uncens)
n_pass_hit = sum(1 for v in pass_uncens if v >= TP_THRESHOLD)
rate_pass = n_pass_hit / n_pass if n_pass else 0

print(f"\n[BA SỐ · uncensored 30d fwd ≥ +{TP_THRESHOLD:.0%}]")
print(f"  pass-set       (3-leg CVD): {n_pass_hit}/{n_pass}  = {rate_pass:.2%}")
print(f"  quiet-control  (px_min30 ≤ {PX_MIN30_MAX}): {n_quiet_hit}/{n_quiet}  = {rate_quiet:.2%}")
print(f"  all-control    (ALL 30d): {n_all_hit}/{n_all}  = {rate_all:.2%}")
print(f"  lift pass vs quiet: {rate_pass - rate_quiet:+.2%} ({rate_pass/rate_quiet:.2f}x)" if rate_quiet else "")
print(f"  lift pass vs all:   {rate_pass - rate_all:+.2%} ({rate_pass/rate_all:.2f}x)" if rate_all else "")

# ── Write CSV ──
OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
with open(OUT_CSV, "w", encoding="utf-8", newline="") as f:
    f.write(f"# ANNEX-125b · SPOTCVD-20260901 · zero-call · KÝ 01/09\n")
    f.write(f"# Source: D3 CSV md5 7154bcd0806248ba1687d08391b415b9 (125 pass-windows)\n")
    f.write(f"# Store: data/raw/spot_klines_1d venue=binance_spot ({len(all_df)} rows · {all_df['symbol'].nunique()} sym · last={DATA_LAST})\n")
    f.write(f"# TP threshold: fwd_ret_30d ≥ +{TP_THRESHOLD:.0%} (runner §5)\n")
    f.write(f"# Episode rule (luật-4): cụm pass-windows cùng token gap <{EPISODE_GAP}d = 1 episode\n")
    f.write(f"# Quiet-control filter: px_min30 ≤ {PX_MIN30_MAX} (KHÔNG đòi 2 chân CVD)\n")
    f.write(f"# Censor rule: window có <30d data ngày SAU window_end → censored\n")
    f.write(f"#\n")
    # L-64 header: khai mẫu số từng con
    f.write(f"# ─── L-64 mẫu-số ĐO GÌ / LOẠI TRỪ GÌ / CENSOR ───\n")
    f.write(f"#   pass-set    : ĐO = pass-window 3-leg CVD (D3) · LOẠI = censored (fwd<30d) · CENSOR = data-edge\n")
    f.write(f"#                 n_all={len(pass_rows)} · n_uncens={n_pass}\n")
    f.write(f"#   quiet-control: ĐO = mọi cửa sổ 30d px_min30 ≤ {PX_MIN30_MAX} (không đòi CVD) · LOẠI = censored · CENSOR = data-edge\n")
    f.write(f"#                 n_all_30d_windows_calc={n_all} · n_quiet={n_quiet}\n")
    f.write(f"#   all-control : ĐO = mọi cửa sổ 30d TOÀN store (không lọc) · LOẠI = censored · CENSOR = data-edge\n")
    f.write(f"#                 n_uncens={n_all}\n")
    f.write(f"#\n")
    # BA SỐ
    f.write(f"# ─── BA SỐ · uncensored 30d fwd ≥ +{TP_THRESHOLD:.0%} ───\n")
    f.write(f"#   pass-set       (3-leg CVD)       : {n_pass_hit}/{n_pass}  = {rate_pass:.2%}\n")
    f.write(f"#   quiet-control  (px_min30 ≤ {PX_MIN30_MAX}): {n_quiet_hit}/{n_quiet}  = {rate_quiet:.2%}\n")
    f.write(f"#   all-control    (ALL 30d)         : {n_all_hit}/{n_all}  = {rate_all:.2%}\n")
    if rate_quiet > 0:
        f.write(f"#   lift pass vs quiet: {rate_pass - rate_quiet:+.2%} ({rate_pass/rate_quiet:.2f}x)\n")
    if rate_all > 0:
        f.write(f"#   lift pass vs all:   {rate_pass - rate_all:+.2%} ({rate_pass/rate_all:.2f}x)\n")
    f.write(f"#\n")
    # Episode stats
    f.write(f"# ─── EPISODE STATS (luật-4 · gap <{EPISODE_GAP}d) ───\n")
    f.write(f"#   n_episodes: {len(episodes)}\n")
    f.write(f"#   uncensored episodes: {n_uncens}/{len(episodes)}\n")
    f.write(f"#   hit-rate ≥+50% per-episode (uncens): {n_hit_uncens}/{n_uncens} = {hit_rate_uncens:.2%}\n")
    f.write(f"# KHÔNG kết luận — bảng quyết-định cho ANALYSIS\n")
    f.write(f"#\n")
    # Episodes table
    w = csv.DictWriter(f, fieldnames=["symbol","episode_start","episode_end","n_windows",
                                       "best_fwd_ret_30d","hit_ge_50pct","censored"])
    w.writeheader()
    for e in ep_records:
        w.writerow({
            "symbol": e["symbol"],
            "episode_start": e["episode_start"],
            "episode_end": e["episode_end"],
            "n_windows": e["n_windows"],
            "best_fwd_ret_30d": f"{e['best_fwd_ret_30d']:.6f}" if e["best_fwd_ret_30d"] is not None else "",
            "hit_ge_50pct": e["hit_ge_50pct"],
            "censored": e["censored"],
        })

md5_out = hashlib.md5(OUT_CSV.read_bytes()).hexdigest()
n_lines = sum(1 for _ in open(OUT_CSV, encoding="utf-8"))
print(f"\n[OUT] {OUT_CSV.relative_to(ROOT)}")
print(f"[MD5] {md5_out}")
print(f"[WC ] {n_lines}")

# Print episode records for terminal review
print(f"\n[EPISODES TABLE]")
print(f"  {'token':<14} {'start':<12} {'end':<12} {'n_win':>5} {'best_fwd':>10} {'hit':>4} {'cens':>5}")
for e in ep_records:
    fwd = f"{e['best_fwd_ret_30d']:+.2%}" if e['best_fwd_ret_30d'] is not None else "N/A"
    print(f"  {e['symbol']:<14} {e['episode_start']:<12} {e['episode_end']:<12} {e['n_windows']:>5} {fwd:>10} {str(e['hit_ge_50pct']):>4} {str(e['censored']):>5}")
