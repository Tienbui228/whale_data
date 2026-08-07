#!/usr/bin/env python3
"""Read funding_8h parquet 2026-07 for BANK 27/07 and related dates.
READ-ONLY.
"""
import sys, subprocess

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except AttributeError:
    pass

VPS = "root@5.223.67.21"

def ssh(cmd, timeout=40):
    args = ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=10", VPS, cmd]
    try:
        r = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
        return r.stdout.strip(), r.stderr.strip(), r.returncode
    except subprocess.TimeoutExpired:
        return "", "TIMEOUT", 1
    except Exception as e:
        return "", str(e), 1

# Write the Python script to VPS via cat heredoc
write_cmd = r"""cat > /tmp/chk_parq.py << 'HEREDOC'
import pandas as pd

def check(path, syms, dates, label):
    try:
        df = pd.read_parquet(path)
    except Exception as e:
        print("  ERROR", path, str(e))
        return
    print("  " + label + ": " + str(len(df)) + " rows cols=" + str(list(df.columns)))
    sym_col  = next((c for c in df.columns if c.lower() in ('symbol','sym')), None)
    date_col = next((c for c in df.columns if 'date' in c.lower() or 'day' in c.lower()), None)
    ts_col   = next((c for c in df.columns if 'time' in c.lower() or c.lower() == 'ts'), None)
    print("    sym_col=" + str(sym_col) + " date_col=" + str(date_col) + " ts_col=" + str(ts_col))
    if not sym_col:
        print("    (no symbol col)")
        return
    for sym in syms:
        mask = df[sym_col].astype(str).str.contains(sym, case=False, na=False)
        sub = df[mask]
        if len(sub) == 0:
            print("    " + sym + ": 0 rows in parquet")
            continue
        for d in dates:
            if date_col:
                dsub = sub[sub[date_col].astype(str).str.startswith(d)]
            elif ts_col:
                dsub = sub
            else:
                dsub = sub
            ts_str = ""
            if ts_col and len(dsub) > 0:
                ts_str = " ts=" + str(sorted(dsub[ts_col].astype(str).tolist())[:8])
            print("    " + sym + " " + d + ": " + str(len(dsub)) + " rows" + ts_str)

check(
    "/root/Data_back_test/whale_data/data/raw/funding_8h/month=2026-07/part-0.parquet",
    ["BANKUSDT","BRUSDT"],
    ["2026-07-24","2026-07-25","2026-07-26","2026-07-27"],
    "Jul-2026"
)
check(
    "/root/Data_back_test/whale_data/data/raw/funding_8h/month=2026-08/part-0.parquet",
    ["BANKUSDT","IDOLUSDT","XPINUSDT"],
    ["2026-08-05"],
    "Aug-2026"
)
df = pd.read_parquet("/root/Data_back_test/whale_data/data/raw/funding_8h/month=2026-07/part-0.parquet")
print("  --- Jul sample (first 2 rows) ---")
print(df.head(2).to_string())
HEREDOC"""

out0, err0, rc0 = ssh(write_cmd)

print("=" * 68)
print("Parquet check: BANK/BR Jul, BANK/IDOL/XPIN Aug-05")
print("=" * 68)

out, err, rc = ssh("python3 /tmp/chk_parq.py", timeout=40)
if out:
    for ln in out.splitlines():
        print(f"  {ln}")
if err:
    print(f"  stderr: {err[:400]}")
