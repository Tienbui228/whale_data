#!/usr/bin/env python3
"""Probe: S-MISSING date breakdown — which dates are missing for sample tokens?
Operator Q: is missing = 2026-08-07 (today's target) or historical dates?
If 08-07 missing → possible race: export 01:20 UTC vs scan 01:25 UTC."""
import sys, subprocess
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

VPS  = "root@5.223.67.21"
BASE = "/root/Data_back_test/whale_data"

def ssh(cmd, timeout=120):
    r = subprocess.run(
        ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=10", VPS, cmd],
        capture_output=True, encoding="utf-8", errors="replace", timeout=timeout,
    )
    return r.stdout.strip(), r.stderr.strip()

# === STEP 1: Which dates does the Aug CSV cover right now? ===
print("=== 1. Aug CSV dates currently on VPS ===")
out, _ = ssh(r"""python3 - <<'PYEOF'
import pandas as pd
fn = '/root/Data_back_test/whale_data/data/export/freshwatch_daily_2026-08.csv'
df = pd.read_csv(fn)
dates = sorted(df['date'].unique())
print(f"Aug CSV: {len(dates)} dates -> {dates[0]} to {dates[-1]}")
print("All dates:", dates)
# How many symbols per date?
for d in dates:
    n = len(df[df['date']==d])
    print(f"  {d}: {n} rows")
PYEOF
""")
print(out)

# === STEP 2: Run gom_scan --daily with verbose S-MISSING output ===
print("\n=== 2. Run gom_scan --daily (date=2026-08-07) and capture S-MISSING lines ===")
out, err = ssh(
    f"cd {BASE} && python3 scripts/gom_scan.py --daily --store data/export --date 2026-08-07 "
    f"--fw-filter data/config/freshwatch_symbols.txt 2>&1 | grep -E 'S-MISSING|suspect|missing date|MISSING' | head -30",
    timeout=180,
)
print(out or "(no matching lines)")
if err:
    print("ERR:", err[:200])

# === STEP 3: Sample 10 tokens — check their date coverage in Aug CSV ===
print("\n=== 3. Sample 10 tokens: date coverage in Aug CSV ===")
out, _ = ssh(r"""python3 - <<'PYEOF'
import pandas as pd
fn = '/root/Data_back_test/whale_data/data/export/freshwatch_daily_2026-08.csv'
fw = '/root/Data_back_test/whale_data/data/config/freshwatch_symbols.txt'
df = pd.read_csv(fn)

fw_syms = [l.strip() for l in open(fw).readlines() if l.strip()]
sample = fw_syms[:10]  # first 10 symbols from freshwatch list

target = '2026-08-07'
all_dates = sorted(df['date'].unique())

print(f"Checking {len(sample)} sample tokens against {len(all_dates)} dates in Aug CSV")
print(f"Target date: {target}")
print()

for sym in sample:
    sym_rows = df[df['symbol'] == sym]
    sym_dates = sorted(sym_rows['date'].unique())
    has_target = target in sym_dates
    print(f"  {sym}: {len(sym_dates)} dates | has {target}: {has_target} | dates: {sym_dates}")
PYEOF
""")
print(out)

# === STEP 4: Check fw_loader_utils S-MISSING logic ===
print("\n=== 4. S-MISSING definition in fw_loader_utils — what triggers it? ===")
out, _ = ssh(f"grep -n 'S-MISSING\\|_suspect\\|missing\\|smissing' {BASE}/scripts/fw_loader_utils.py | head -20")
print(out or "(nothing)")

# === STEP 5: Check export timing vs scan timing ===
print("\n=== 5. Export log timing vs gom_daily.log ===")
out, _ = ssh(f"tail -20 {BASE}/data/logs/gom_daily.log")
print("--- gom_daily.log ---")
print(out)
out, _ = ssh(f"ls -la {BASE}/data/export/freshwatch_daily_2026-08.csv")
print("\n--- Aug CSV mtime ---")
print(out)
