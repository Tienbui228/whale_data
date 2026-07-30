#!/usr/bin/env python3
"""Tìm định nghĩa derived_1h trong code sinh freshwatch_daily CSV trên VPS."""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
import subprocess

KEY  = r"C:\Users\Hello\.ssh\binance_vps_nopass"
HOST = "root@5.223.67.21"

def ssh(cmd: str, timeout: int = 30) -> str:
    r = subprocess.run(
        ["ssh", "-i", KEY, "-o", "StrictHostKeyChecking=no", HOST, cmd],
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout
    )
    return (r.stdout + r.stderr).strip()

print("=== 1. Tìm file sinh freshwatch_daily CSV ===")
out = ssh("grep -rl 'freshwatch_daily' /root/Data_back_test/whale_data/ 2>/dev/null | grep -v '__pycache__' | grep -v '.pyc' | head -20")
print(out)

print("\n=== 2. Tìm 'derived_1h' trong codebase ===")
out = ssh("grep -rn 'derived_1h' /root/Data_back_test/whale_data/ 2>/dev/null | grep -v '__pycache__' | head -30")
print(out)

print("\n=== 3. Tìm 'lsr_pos' assignment logic ===")
out = ssh("grep -rn 'lsr_pos_r\\|src_ratio\\|keep.last\\|keep_last' /root/Data_back_test/whale_data/ 2>/dev/null | grep -v '__pycache__' | grep -v '.csv' | head -30")
print(out)

print("\n=== 4. Đọc file chứa derived_1h (top hits) ===")
# Find the actual builder file
out2 = ssh("grep -rl 'derived_1h' /root/Data_back_test/whale_data/ 2>/dev/null | grep '.py' | head -5")
for fpath in out2.strip().splitlines():
    if not fpath:
        continue
    print(f"\n--- {fpath} ---")
    # Show lines around derived_1h
    chunk = ssh(f"grep -n 'derived_1h\\|lsr_pos_r\\|src_ratio\\|keep_last\\|top_pos_1h\\|as_of_ts' {fpath} 2>/dev/null | head -40")
    print(chunk)
