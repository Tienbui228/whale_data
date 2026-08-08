#!/usr/bin/env python3
# Quick field-name probe: print all keys in days dict for TUT on 2026-07-13
import sys, subprocess
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

VPS  = "root@5.223.67.21"
BASE = "/root/Data_back_test/whale_data"

INNER = b'''#!/usr/bin/env python3
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
'''

with open("_probe_gomc_fields_inner.py", "wb") as f:
    f.write(INNER)

import subprocess

def scp(local, remote):
    r = subprocess.run(
        ["scp", "-o", "StrictHostKeyChecking=no", local, f"{VPS}:{remote}"],
        capture_output=True, encoding="utf-8", errors="replace", timeout=60,
    )
    return r.returncode == 0

def ssh(cmd, timeout=120):
    r = subprocess.run(
        ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=10", VPS, cmd],
        capture_output=True, encoding="utf-8", errors="replace", timeout=timeout,
    )
    return r.stdout.strip(), r.stderr.strip()

scp("_probe_gomc_fields_inner.py", f"{BASE}/_probe_gomc_fields_inner.py")
out, err = ssh(f"python3 {BASE}/_probe_gomc_fields_inner.py 2>&1", timeout=120)
print(out)
if err and "Error" in err:
    print(err[:600])
