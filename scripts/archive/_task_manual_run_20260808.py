#!/usr/bin/env python3
"""Manual run theo lệnh operator: kiểm tra CSV date → chạy run_gom_daily.py → đọc state.json.
NOTE: Run này KHÔNG thay chân L-44 (natural cron 01:25 UTC vẫn là chân verify thứ ba)."""
import sys, subprocess, json
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

VPS  = "root@5.223.67.21"
BASE = "/root/Data_back_test/whale_data"

def ssh(cmd, timeout=300):
    r = subprocess.run(
        ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=10", VPS, cmd],
        capture_output=True, encoding="utf-8", errors="replace", timeout=timeout,
    )
    return r.stdout.strip(), r.stderr.strip()

# === STEP 1: Kiểm tra CSV dates + log ===
print("=== 1. VPS UTC + CSV dates + cron log ===")
check = r"""
python3 - <<'PYEOF'
import pandas as pd, subprocess
from datetime import datetime, timezone
now = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S UTC')
print(f"VPS UTC: {now}")

import os
for fn in ['/root/Data_back_test/whale_data/data/export/freshwatch_daily_2026-08.csv']:
    if os.path.exists(fn):
        df = pd.read_csv(fn, usecols=['date'])
        dates = sorted(df['date'].unique())
        print(f"Aug CSV: {len(dates)} dates | {dates[0]} → {dates[-1]}")
    else:
        print(f"NOT FOUND: {fn}")
PYEOF
"""
out, err = ssh(check)
print(out or err)

# Log check (cron tự nhiên đã chạy chưa?)
print("\n--- gom_daily.log (last 6 lines) ---")
out, _ = ssh(f"tail -6 {BASE}/data/logs/gom_daily.log")
print(out)

# === STEP 2: Chạy run_gom_daily.py ===
print("\n=== 2. Manual run: run_gom_daily.py (gửi Telegram thật) ===")
out, err = ssh(
    f"cd {BASE} && python3 scripts/run_gom_daily.py 2>&1",
    timeout=300,
)
# Print stdout up to 8000 chars
print(out[:8000])
if err:
    print("\n--- STDERR ---")
    print(err[:300])

# === STEP 3: Đọc state.json → open chains ===
print("\n=== 3. gom_state.json — open chains sau run ===")
state_script = r"""
python3 - <<'PYEOF'
import json, math
from pathlib import Path

BASE = Path('/root/Data_back_test/whale_data')
STATE = BASE / 'data' / 'gom_state.json'
FW_PATH = BASE / 'data' / 'config' / 'freshwatch_symbols.txt'

st = json.load(open(STATE))
fw_list = [l.strip() for l in FW_PATH.read_text().splitlines() if l.strip()]
fw_base = {s[:-4] if s.endswith('USDT') else s for s in fw_list}

open_c = {t: c for t, c in st.items() if c.get('chain_open') and t in fw_base}
sorted_c = sorted(open_c.items(), key=lambda x: x[1].get('Q1_cum_usd', 0), reverse=True)

print(f"Open chains (fw-filtered): {len(sorted_c)}")
print(f"{'TOKEN':<12} {'ch':>3} {'n':>3} {'brk':>4} {'start':>7} {'Q1_cum':>12} {'note'}")
print('-' * 65)
for t, c in sorted_c:
    nd = c.get('n_days', 0)
    bk = c.get('break_streak', 0)
    st_d = c.get('start_date', '?')[-5:]
    q1 = c.get('Q1_cum_usd', 0)
    ch = c.get('chapter', 1)
    q1s = f'${q1/1000:.0f}k' if q1 >= 1000 else '$0'
    flag = 'STAR' if q1 > 2_000_000 else ''
    note = f'n=0!' if nd == 0 else ''
    note += f' brk={bk}' if bk > 0 else ''
    print(f"{t:<12} {ch:>3} {nd:>3} {bk:>4} {st_d:>7} {q1s:>12}  {flag} {note}")

print()
q1_big = [(t, c) for t, c in sorted_c if c.get('Q1_cum_usd', 0) > 2_000_000]
print(f"★ Q1>$2M: {', '.join(t for t, _ in q1_big) if q1_big else 'NONE'}")
PYEOF
"""
out, err = ssh(state_script)
print(out or err)

# === STEP 4: Log entry ===
print("\n=== 4. Log xác nhận (last 4 lines) ===")
out, _ = ssh(f"tail -4 {BASE}/data/logs/gom_daily.log")
print(out)
