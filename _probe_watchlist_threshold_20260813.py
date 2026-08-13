"""
Probe: test pos_trend_threshold sweep (0.02 vs 0.03 vs 0.04) trên data thực.
Mục tiêu List B ~10-20/ngày.
"""
import sys, pathlib, math
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent / "scripts"))
import watchlist_daily as wl

cfg = wl.load_config()
td  = wl.load_token_data(wl.EXPORT_DIR, cfg["data"]["min_history_rows"])
print(f"Loaded {len(td)} tokens. YAML pos_thr={cfg['trends']['pos_trend_threshold']}")

all_dates = sorted({r["date"] for arr in td.values() for r in arr})
dates_30  = all_dates[-30:]

ep_cache = {sym: wl.detect_episodes(arr, cfg) for sym, arr in td.items()}

for thr in (0.02, 0.03, 0.04):
    cfg_t = {k: dict(v) for k, v in cfg.items()}
    cfg_t["trends"]["pos_trend_threshold"] = thr
    daily_b = []
    for dt in dates_30:
        _, sb = wl.run_date(dt, td, cfg_t, ep_cache)
        daily_b.append(len(sb))
    avg_b = sum(daily_b) / len(daily_b)
    max_b = max(daily_b)
    print(f"pos_thr={thr:.2f}  List B avg={avg_b:.1f}  max={max_b}  "
          f"last5={'|'.join(str(x) for x in daily_b[-5:])}")

print("Done.")
