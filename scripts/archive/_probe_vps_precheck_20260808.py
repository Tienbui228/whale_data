#!/usr/bin/env python3
"""VPS pre-cron check: UTC time, freshwatch Aug dates, funding_8h rows/day table, gom_state.json open chains."""
import sys, subprocess, json
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

VPS  = "root@5.223.67.21"
BASE = "/root/Data_back_test/whale_data"

def ssh(cmd, timeout=60):
    r = subprocess.run(
        ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=10", VPS, cmd],
        capture_output=True, encoding="utf-8", errors="replace", timeout=timeout,
    )
    return r.stdout.strip(), r.stderr.strip()

# 1. VPS UTC time
print("=== 1. VPS UTC timestamp ===")
out, _ = ssh("date -u '+%Y-%m-%dT%H:%M:%S UTC'")
print(out)

# 2. Freshwatch Aug CSV: distinct dates available
print("\n=== 2. Freshwatch Aug CSV — distinct dates ===")
out, err = ssh(
    f"python3 -c \""
    f"import pandas as pd; "
    f"df = pd.read_csv('{BASE}/data/export/freshwatch_daily_2026-08.csv', "
    f"usecols=['date'], parse_dates=['date']); "
    f"dates = sorted(df['date'].dt.strftime('%Y-%m-%d').unique()); "
    f"print('Dates:', len(dates), '|', dates[0], '→', dates[-1]); "
    f"[print(d) for d in dates]\""
)
print(out or err)

# 3. funding_8h store: rows per day table
print("\n=== 3. funding_8h rows-per-day table (37 days 01/07→06/08) ===")
out, err = ssh(
    f"python3 -c \""
    f"import os, glob; "
    f"from pathlib import Path; "
    f"import pyarrow.parquet as pq; "
    f"base = '{BASE}/data/raw/funding_8h'; "
    f"from datetime import date, timedelta; "
    f"d = date(2026, 7, 1); "
    f"end = date(2026, 8, 6); "
    f"rows = []; "
    f"while d <= end: "
    f"    ds = d.strftime('%Y-%m-%d'); "
    f"    pattern = base + f'/date={ds}/*.parquet'; "
    f"    files = glob.glob(pattern); "
    f"    n = sum(pq.read_table(f).num_rows for f in files) if files else 0; "
    f"    rows.append((ds, n, len(files))); "
    f"    d += timedelta(days=1); "
    f"nonzero = [(d, n, f) for d, n, f in rows if n > 0]; "
    f"print(f'Total dates: {len(rows)} | Dates with rows: {len(nonzero)}'); "
    f"print('date          | rows | files'); "
    f"print('-' * 35); "
    f"for ds, n, f in rows: "
    f"    mark = '<<< HAS DATA' if n > 0 else ''; "
    f"    print(f'{ds} | {n:4d} | {f} {mark}')\""
    , timeout=120
)
print(out or err)

# 4. gom_state.json: open chains with n_days, brk_streak
print("\n=== 4. gom_state.json — open chains ===")
out, err = ssh(
    f"python3 -c \""
    f"import json; "
    f"with open('{BASE}/data/gom_state.json') as f: "
    f"    st = json.load(f); "
    f"open_c = [(t, c) for t, c in st.items() if c.get('chain_open')]; "
    f"print(f'Open chains: {len(open_c)}'); "
    f"print(f'{{\\\"token\\\": \\\"TOKEN\\\", \\\"n_days\\\": N, \\\"brk\\\": B, \\\"start\\\": S, \\\"Q1\\\": Q}}'); "
    f"for t, c in sorted(open_c, key=lambda x: x[1].get('Q1_cum_usd', 0), reverse=True): "
    f"    nd = c.get('n_days', 0); bk = c.get('break_streak', 0); "
    f"    st2 = c.get('start_date', '?')[-5:]; q1 = c.get('Q1_cum_usd', 0); "
    f"    ch = c.get('chapter', 1); "
    f"    flag = '  n=0!' if nd == 0 else ''; "
    f"    print(f'  {t:12s} ch{ch} n={nd} brk={bk} start={st2} Q1=${q1:,.0f}{flag}')\""
)
print(out or err)

# 5. TAIKO specific state
print("\n=== 5. TAIKO state (if exists) ===")
out, err = ssh(
    f"python3 -c \""
    f"import json; "
    f"with open('{BASE}/data/gom_state.json') as f: "
    f"    st = json.load(f); "
    f"taiko = st.get('TAIKO', st.get('TAIKOUSDT', None)); "
    f"print('TAIKO state:', json.dumps(taiko, indent=2) if taiko else 'NOT IN STATE')\""
)
print(out or err)
