#!/usr/bin/env python3
"""B0 verify: git bundle verify 4 bundles trên VPS /root/archive/ (dùng /tmp/verify_repo làm context)."""
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

BUNDLES = [
    "binance-bot-signals_20260731.bundle",
    "whale_data_20260731.bundle",
    "Check_onchain_20260731.bundle",
    "Whales_scan_20260731.bundle",
]

# File sizes
print("=== File sizes /root/archive/ ===")
print(ssh("ls -lh /root/archive/*.bundle 2>/dev/null || echo '(none found)'"))

# Init temp repo for verify context (if not exists)
print("\n=== Init verify context repo ===")
print(ssh("mkdir -p /tmp/verify_repo && git -C /tmp/verify_repo init -q 2>&1 && echo 'init OK'"))

# git bundle verify each
print("\n=== git bundle verify (within /tmp/verify_repo) ===")
for b in BUNDLES:
    path = f"/root/archive/{b}"
    out = ssh(f"git -C /tmp/verify_repo bundle verify {path} 2>&1", 30)
    ok = "is okay" in out or "okay" in out
    first_line = out.splitlines()[0] if out else "(no output)"
    print(f"  [{'PASS' if ok else 'FAIL'}] {b}")
    for line in out.splitlines()[:4]:
        print(f"    {line}")

# Cleanup
ssh("rm -rf /tmp/verify_repo")
print("\nDone.")
