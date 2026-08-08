#!/usr/bin/env python3
"""Check Aug CSV column names and avg_px for sample closed tokens."""
import sys, subprocess
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

VPS  = "root@5.223.67.21"
BASE = "/root/Data_back_test/whale_data"

def ssh(cmd, timeout=60):
    r = subprocess.run(
        ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=10", VPS, cmd],
        capture_output=True, encoding="utf-8", errors="replace", timeout=timeout,
    )
    return r.stdout.strip(), r.stderr.strip()

out, _ = ssh(r"""python3 - <<'PYEOF'
import pandas as pd
fn = '/root/Data_back_test/whale_data/data/export/freshwatch_daily_2026-08.csv'
df = pd.read_csv(fn, nrows=5)
print("Columns:", list(df.columns))
print()
# Check price-related columns for MYXUSDT on 2026-08-07
df_all = pd.read_csv(fn)
row = df_all[(df_all['symbol']=='MYXUSDT') & (df_all['date']=='2026-08-07')]
if not row.empty:
    print("MYX 2026-08-07:", dict(row.iloc[0]))
else:
    print("MYXUSDT not found on 2026-08-07")
PYEOF
""")
print(out)
