#!/usr/bin/env python3
"""Đọc hàm _build_derived_1h trong export_freshwatch_daily.py trên VPS."""
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

F = "/root/Data_back_test/whale_data/scripts/export_freshwatch_daily.py"

# Read lines 1-15 (docstring/header with derived_1h definition)
print("=== Header docstring (lines 1-20) ===")
print(ssh(f"sed -n '1,20p' {F}"))

# Read _build_derived_1h function (around line 219)
print("\n=== _build_derived_1h function (lines 218-300) ===")
print(ssh(f"sed -n '218,300p' {F}"))

# Check midnight_ms definition specifically
print("\n=== midnight_ms definition search ===")
print(ssh(f"grep -n 'midnight_ms\\|midnight\\|next.*day\\|00:00' {F} | head -30"))

# Also read the lsr_pos assignment in derived_1h
print("\n=== lsr_pos_map build in derived_1h ===")
print(ssh(f"sed -n '225,295p' {F}"))
