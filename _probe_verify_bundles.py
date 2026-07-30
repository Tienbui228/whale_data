#!/usr/bin/env python3
"""Verify bundles on VPS — check header bytes và verify trong repo context."""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import subprocess

KEY  = r"C:\Users\Hello\.ssh\binance_vps_nopass"
HOST = "root@5.223.67.21"

def ssh(cmd: str, timeout: int = 30) -> str:
    r = subprocess.run(
        ["ssh", "-i", KEY, "-o", "StrictHostKeyChecking=no", HOST, cmd],
        capture_output=True, text=True, timeout=timeout
    )
    return (r.stdout + r.stderr).strip()

REPO = "/root/Whales\\ watching/Whales_scan"
bundles = [
    "binance-bot-signals_20260731.bundle",
    "whale_data_20260731.bundle",
    "Check_onchain_20260731.bundle",
    "Whales_scan_20260731.bundle",
]

print("=== Bundle header check (first 10 bytes hex) ===")
for b in bundles:
    out = ssh(f"xxd /root/archive/{b} 2>/dev/null | head -1")
    print(f"  {b}: {out[:60]}")

print("\n=== Verify in Whales_scan repo context ===")
for b in bundles:
    out = ssh(f"cd '{REPO}' && git bundle verify /root/archive/{b} 2>&1 | head -3", 20)
    ok = "okay" in out
    print(f"  [{'OK' if ok else 'FAIL'}] {b}")
    print(f"    {out.splitlines()[0] if out else '?'}")

print("\n=== File sizes on VPS ===")
print(ssh("ls -lh /root/archive/*.bundle"))
