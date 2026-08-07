#!/usr/bin/env python3
"""Check .env key names only (no values)."""
import sys, subprocess
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
VPS = "root@5.223.67.21"
BASE = "/root/Data_back_test/whale_data"

def ssh(cmd, timeout=15):
    r = subprocess.run(
        ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=10", VPS, cmd],
        capture_output=True, encoding="utf-8", errors="replace", timeout=timeout,
    )
    return r.stdout.strip(), r.stderr.strip()

out, _ = ssh(f"grep -v '^#' {BASE}/.env | grep '=' | cut -d= -f1")
print("Keys in .env:", out)
