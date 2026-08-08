#!/usr/bin/env python3
import sys, math, json
from pathlib import Path
from datetime import datetime, timedelta
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
REPO     = Path("/root/Data_back_test/whale_data")
BOT_ROOT = Path("/root/Data_back_test/binance-bot-signals")
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(BOT_ROOT))
from scanner.screener.signals import load_thresholds
from gom_scan import load_screen_cfg
from fw_loader_utils import taker_scale_check_df, load_fw_csvs, load_funding_intervals, build_token_days
cfg = load_thresholds()
sc  = load_screen_cfg()
STORE      = REPO / "data" / "export"
CONFIG_DIR = REPO / "data" / "config"
intervals  = load_funding_intervals(CONFIG_DIR)
def load_days(sym, target_date, lb=30):
    df = load_fw_csvs(STORE, target_date, lookback_days=lb)
    if df.empty: return [], []
    df = taker_scale_check_df(df)
    d_fr_dt = datetime.strptime(target_date, "%Y-%m-%d") - timedelta(days=lb)
    d_fr = max(d_fr_dt.strftime("%Y-%m-%d"), str(df["date"].min()))
    return build_token_days(df, sym, d_fr, target_date, intervals)

days, _ = load_days("TUTUSDT", "2026-07-23")
if days:
    for d in days:
        if d.get("date","") == "2026-07-13":
            print("ALL KEYS in TUT 2026-07-13:")
            for k,v in sorted(d.items()):
                print(f"  {k}: {v!r}")
            break
else:
    print("No data")
