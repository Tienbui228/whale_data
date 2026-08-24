#!/usr/bin/env python3
"""[R4-v2 helper] SSH to VPS, aggregate klines_1h → daily k[10]/k[7] for 12 tokens.
Fetch aggregated CSV back to local.
"""
from __future__ import annotations
import sys, io, subprocess
from pathlib import Path
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

TOKENS = ["BANK", "TAG", "AKE", "BAS", "BASED", "BTW", "BULLA", "CLO", "ESPORTS", "IDOL", "POWER", "TUT"]

# Remote script
REMOTE_SCRIPT = '''
import pandas as pd, glob
from pathlib import Path
tokens = ["BANK","TAG","AKE","BAS","BASED","BTW","BULLA","CLO","ESPORTS","IDOL","POWER","TUT"]
syms = [t + "USDT" for t in tokens]
root = Path("/root/Data_back_test/whale_data/data/raw/klines_1h")
rows = []
for date_dir in sorted(root.glob("date=2026-0[5-8]-*")):
    date_str = date_dir.name.replace("date=", "")
    try:
        df = pd.read_parquet(date_dir)
    except Exception: continue
    df = df[df["symbol"].isin(syms)]
    if df.empty: continue
    # Aggregate 24h → daily per symbol
    for sym, g in df.groupby("symbol"):
        tqv = g["taker_buy_quote_vol"].sum()
        qv = g["quote_volume"].sum()
        if qv > 0:
            taker_pct = float(tqv) / float(qv)
        else:
            taker_pct = float("nan")
        rows.append({"symbol": sym, "date": date_str, "taker_buy_pct_k10k7": taker_pct,
                     "quote_volume_1d": float(qv), "taker_buy_quote_vol_1d": float(tqv)})
out = pd.DataFrame(rows).sort_values(["symbol","date"])
out_path = Path("/tmp/klines_taker_daily_20260824.csv")
out.to_csv(out_path, index=False)
print(f"WROTE {out_path} rows={len(out)} tokens={out['symbol'].nunique()} dates={out['date'].nunique()}")
'''

# Write remote script + execute
Path("/tmp/_remote_agg.py").write_text(REMOTE_SCRIPT) if sys.platform != "win32" else None
# On Windows, use SSH with heredoc via base64 to avoid escaping
import base64
script_b64 = base64.b64encode(REMOTE_SCRIPT.encode()).decode()
ssh_cmd = f'echo {script_b64} | base64 -d > /tmp/_remote_agg.py && python3 /tmp/_remote_agg.py'
result = subprocess.run(
    ["ssh", "-o", "ConnectTimeout=10", "root@5.223.67.21", ssh_cmd],
    capture_output=True, text=True
)
print("STDOUT:", result.stdout)
print("STDERR:", result.stderr[:500] if result.stderr else "")
if result.returncode != 0:
    sys.exit(f"SSH failed rc={result.returncode}")

# SCP down
local_path = Path(r"D:/Data back test/whale_data/data/reference/klines_taker_daily_20260824.csv")
local_path.parent.mkdir(parents=True, exist_ok=True)
scp_result = subprocess.run(
    ["scp", "root@5.223.67.21:/tmp/klines_taker_daily_20260824.csv", str(local_path)],
    capture_output=True, text=True
)
print("SCP STDOUT:", scp_result.stdout)
print("SCP STDERR:", scp_result.stderr[:500] if scp_result.stderr else "")
if local_path.exists():
    import pandas as pd
    df = pd.read_csv(local_path)
    print(f"\nLOCAL {local_path} rows={len(df)} tokens={df['symbol'].nunique()} dates={df['date'].nunique()}")
    print(df.head(3).to_string())
