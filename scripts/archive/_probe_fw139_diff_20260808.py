#!/usr/bin/env python3
# Item 5: diff freshwatch_symbols.txt (fw139) vs universe_master.csv (VPS)
import sys, subprocess
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

VPS  = "root@5.223.67.21"
BASE = "/root/Data_back_test/whale_data"

def ssh(cmd, timeout=30):
    r = subprocess.run(
        ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=10", VPS, cmd],
        capture_output=True, encoding="utf-8", errors="replace", timeout=timeout,
    )
    return r.stdout.strip(), r.stderr.strip()

# 1. Get universe_master.csv columns + active symbols
print("=== universe_master.csv header + active count ===")
out, _ = ssh(f"head -3 {BASE}/data/config/universe_master.csv")
print(out)
out2, _ = ssh(f"wc -l {BASE}/data/config/universe_master.csv")
print("lines:", out2)

# Active symbols only
print()
print("=== universe_master active symbols (col1=symbol, filter active) ===")
out3, _ = ssh(f"awk -F',' '$2==\"active\" {{print $1}}' {BASE}/data/config/universe_master.csv | sort > /tmp/_um_active.txt && wc -l /tmp/_um_active.txt && head -5 /tmp/_um_active.txt")
print(out3)

# 2. Get freshwatch_symbols.txt
print()
print("=== freshwatch_symbols.txt on VPS ===")
out4, _ = ssh(f"ls -la {BASE}/data/config/freshwatch_symbols.txt 2>/dev/null || echo MISSING")
print(out4)

# Local freshwatch_symbols.txt
import os
local_fw = "D:\\Check onchain fresh wallets\\data\\config\\freshwatch_symbols.txt"
scratch_fw = "D:\\Data back test\\whale_data\\scratch\\freshwatch_symbols.txt"
for p in [local_fw, scratch_fw]:
    if os.path.exists(p):
        with open(p, encoding="utf-8") as f:
            fw_lines = [l.strip() for l in f if l.strip()]
        print(f"\nLocal fw file: {p} ({len(fw_lines)} entries)")
        # Normalize: strip USDT suffix if present
        fw_base = []
        for s in fw_lines:
            if s.endswith("USDT"): fw_base.append(s[:-4])
            else: fw_base.append(s)
        print(f"  Sample: {fw_base[:5]}...{fw_base[-3:]}")
        break

# 3. Get universe_master active set, compare
print()
print("=== Diff fw139 vs universe_master active ===")
# Get universe_master active symbols as set
out5, _ = ssh(f"awk -F',' 'NR>1 && $2==\"active\" {{print $1}}' {BASE}/data/config/universe_master.csv")
um_active = set(s.strip() for s in out5.strip().splitlines() if s.strip())
print(f"universe_master active: {len(um_active)} symbols")

# Load local fw list
fw_set = set(fw_base) if 'fw_base' in dir() else set()
print(f"fw list base (no USDT): {len(fw_set)}")

# In fw but not in UM
fw_not_um = sorted(fw_set - um_active)
print(f"\nIn fw-filter NOT in universe_master: {len(fw_not_um)}")
for s in fw_not_um:
    print(f"  {s}")

# In UM but not in fw
um_not_fw = sorted(um_active - fw_set)
print(f"\nIn universe_master NOT in fw-filter: {len(um_not_fw)}")
for s in um_not_fw[:20]:
    print(f"  {s}")
if len(um_not_fw) > 20:
    print(f"  ... ({len(um_not_fw) - 20} more)")

# 4. Also diff fw139 vs alpha_id_map
print()
print("=== alpha_id_map.json: known diff summary ===")
out6, _ = ssh(f"python3 -c \"import json; d=json.load(open('{BASE}/data/config/alpha_id_map.json')); print(len(d), 'entries'); syms=set(d.keys()); print('sample:', list(syms)[:5])\"")
print(out6)
