#!/usr/bin/env python3
"""Probe: (1) freshwatch export TAG 07-27..07-29 glsr vs CAMPAIGNS value
(2) script nào update CAMPAIGNS (3) check ledger_daily.py logic."""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import csv, subprocess
from pathlib import Path

# --- A: freshwatch export TAG glsr 07-27..07-29 ---
EXPORT = Path(r"D:\Check onchain fresh wallets\data\export")
csv_path = EXPORT / "freshwatch_daily_2026-07.csv"

print("=== freshwatch_daily_2026-07.csv — TAG lsr_global_r 07-27..07-30 ===")
if csv_path.exists():
    with open(csv_path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row.get("symbol") == "TAGUSDT" and row.get("date","") >= "2026-07-27":
                print(f"  {row['date']}  lsr_pos_r={row.get('lsr_pos_r','?')}  "
                      f"lsr_global_r={row.get('lsr_global_r','?')}  "
                      f"fn={row.get('fn','?')}  src_ratio={row.get('src_ratio','?')}")
else:
    print(f"  NOT FOUND: {csv_path}")

print("\n=== CAMPAIGNS glsr_r for TAG (for comparison) ===")
print("  Backup 29/07: glsr_r=1.6059 (zoneA_updated=2026-07-29T07:36:18Z)")
print("  Current 30/07: glsr_r=1.7022 (zoneA_updated=2026-07-30T01:00:02Z)")

# --- B: find script that writes to CAMPAIGNS ---
print("\n=== Scripts referencing CAMPAIGNS / ledger_v2 ===")
KEY  = r"C:\Users\Hello\.ssh\binance_vps_nopass"
HOST = "root@5.223.67.21"

def ssh(cmd: str, timeout: int = 20) -> str:
    r = subprocess.run(
        ["ssh", "-i", KEY, "-o", "StrictHostKeyChecking=no", HOST, cmd],
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout
    )
    return (r.stdout + r.stderr).strip()

# Check VPS ledger_daily.py for CAMPAIGNS / glsr
print("\n[VPS] grep ledger_daily.py for glsr/CAMPAIGNS/keep_last:")
print(ssh("grep -n 'glsr\\|CAMPAIGNS\\|keep.last\\|keep_last\\|lsr_global' "
          "/root/Data_back_test/whale_data/ledger_daily.py 2>/dev/null | head -30"))

# Check if there's an update_ledger or zone_a script on VPS
print("\n[VPS] find scripts touching ledger_v2 or CAMPAIGNS:")
print(ssh("grep -rl 'ledger_v2\\|CAMPAIGNS\\|zoneA' /root/Data_back_test/ 2>/dev/null "
          "| grep '.py' | grep -v __pycache__ | head -10"))

# Check local scripts
print("\n[LOCAL] grep for CAMPAIGNS in whale_data scripts:")
local_grep = subprocess.run(
    ["grep", "-rn", "CAMPAIGNS", r"D:\Data back test\whale_data\scripts"],
    capture_output=True, text=True, encoding="utf-8", errors="replace"
)
print(local_grep.stdout[:1000] or "(none found)")

# --- C: read ledger_daily.py lsr_global / avg logic ---
print("\n=== ledger_daily.py avg/glsr logic (lines 240-280) ===")
print(ssh("sed -n '240,285p' /root/Data_back_test/whale_data/ledger_daily.py"))
