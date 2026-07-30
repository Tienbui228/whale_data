#!/usr/bin/env python3
"""Probe VPS top_pos_1d parquet for BULLA topLongShortPositionRatio on 2026-07-20."""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import subprocess
KEY  = r"C:\Users\Hello\.ssh\binance_vps_nopass"
HOST = "root@5.223.67.21"

def ssh(cmd: str, timeout: int = 30) -> str:
    r = subprocess.run(
        ["ssh", "-i", KEY, "-o", "StrictHostKeyChecking=no", HOST, cmd],
        capture_output=True, text=True, timeout=timeout
    )
    return (r.stdout + r.stderr).strip()

probe_script = '''
import pandas as pd
from pathlib import Path

DATA = Path("/root/Data_back_test/whale_data/data")

# top_pos_1d: topLongShortPositionRatio canonical
top_pos = DATA / "raw" / "top_pos_1d"
print(f"top_pos_1d exists: {top_pos.exists()}")
if top_pos.exists():
    print(f"  dates available: {sorted([d.name for d in top_pos.iterdir()])}")
    # Find 2026-07-20 partition
    date_dir = top_pos / "date=2026-07-20"
    if date_dir.exists():
        pf = list(date_dir.glob("*.parquet"))
        print(f"  date=2026-07-20 parquets: {pf}")
        if pf:
            df = pd.read_parquet(pf[0])
            print(f"  columns: {list(df.columns)}")
            bulla = df[df["symbol"] == "BULLAUSDT"]
            print(f"  BULLA rows: {len(bulla)}")
            print(bulla.sort_values("timestamp" if "timestamp" in bulla.columns else bulla.columns[0]).tail(5).to_string())
    else:
        print("  date=2026-07-20 not found — trying adjacent")
        # Check 2026-07-21 (which captures 00:00 UTC 21/07)
        date_dir2 = top_pos / "date=2026-07-21"
        if date_dir2.exists():
            pf2 = list(date_dir2.glob("*.parquet"))
            if pf2:
                df2 = pd.read_parquet(pf2[0])
                bulla2 = df2[df2["symbol"] == "BULLAUSDT"]
                # snapshot closest to 00:00 UTC 2026-07-21
                bulla2 = bulla2.sort_values("timestamp" if "timestamp" in bulla2.columns else bulla2.columns[0])
                print(f"  date=2026-07-21 BULLA rows (first entry = 00:00 UTC 21/07):")
                print(bulla2.head(3).to_string())

# Also check top_pos_1h for keep-last at 2026-07-21 00:00 UTC (= timestamp 1753056000000)
top_pos_1h = DATA / "raw" / "top_pos_1h"
if top_pos_1h.exists():
    # 00:00 UTC 21/07 = timestamp 1753056000000
    target_ts = 1753056000000
    date_dir_21 = top_pos_1h / "date=2026-07-21"
    if date_dir_21.exists():
        pf_21 = list(date_dir_21.glob("*.parquet"))
        if pf_21:
            df_21 = pd.read_parquet(pf_21[0])
            bulla_21 = df_21[(df_21["symbol"] == "BULLAUSDT")]
            if "timestamp" in bulla_21.columns:
                snap = bulla_21[bulla_21["timestamp"] == target_ts]
                if snap.empty:
                    snap = bulla_21.sort_values("timestamp").head(1)
                print(f"\\n1h store 00:00 UTC 21/07 BULLA:")
                print(snap.to_string())
            else:
                print(f"\\n1h store 07-21 BULLA cols: {list(df_21.columns)}")

# Check freshwatch_daily_2026-07.csv for dedup keep-last
csv = DATA / "export" / "freshwatch_daily_2026-07.csv"
if csv.exists():
    df_csv = pd.read_csv(csv)
    bulla_csv = df_csv[(df_csv["symbol"] == "BULLAUSDT") & (df_csv["date"] == "2026-07-20")]
    print(f"\\nexport CSV BULLA 07-20:")
    print(bulla_csv[["symbol","date","lsr_pos_r","lsr_acc_r","lsr_global_r","taker_ratio","low_conf","src_ratio"]].to_string())
'''

# Write and run probe on VPS
write_cmd = f"python3 - << 'PYEOF'\n{probe_script}\nPYEOF"
print("=== Probe top_pos_1d + 1h for BULLA 07-20 ===")
print(ssh(f"cd /root/Data_back_test/whale_data && python3 /tmp/probe_bulla.py 2>&1", 5))  # re-use last
# Write new probe
import tempfile, os
with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
    f.write(probe_script)
    tmp_path = f.name

# SCP probe to VPS
r = subprocess.run(
    ["scp", "-i", KEY, "-o", "StrictHostKeyChecking=no", tmp_path, f"root@5.223.67.21:/tmp/probe_bulla2.py"],
    capture_output=True, text=True
)
os.unlink(tmp_path)
print(f"SCP probe: {'OK' if r.returncode == 0 else r.stderr}")

print(ssh("cd /root/Data_back_test/whale_data && python3 /tmp/probe_bulla2.py 2>&1", 30))
