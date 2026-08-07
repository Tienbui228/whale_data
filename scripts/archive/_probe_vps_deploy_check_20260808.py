#!/usr/bin/env python3
"""Probe: Check VPS structure for gom_scan deploy — paths, python deps, crontab."""
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

print("=== 1. Export CSV exists? ===")
out, _ = ssh(f"ls {BASE}/data/export/ 2>/dev/null | head -5")
print(out or "(empty)")

print("\n=== 2. binance-bot-signals on VPS? ===")
out, _ = ssh("ls /root/Data_back_test/binance-bot-signals/scanner/screener/signals.py 2>/dev/null || echo MISSING")
print(out)

print("\n=== 3. screen_thresholds.yaml on VPS? ===")
out, _ = ssh(f"ls {BASE}/screen_thresholds.yaml 2>/dev/null || echo MISSING")
print(out)

print("\n=== 4. gom_scan.py already on VPS? ===")
out, _ = ssh(f"ls {BASE}/scripts/gom_scan.py 2>/dev/null || echo MISSING")
print(out)

print("\n=== 5. fw_loader_utils.py on VPS? ===")
out, _ = ssh(f"ls {BASE}/scripts/fw_loader_utils.py 2>/dev/null || echo MISSING")
print(out)

print("\n=== 6. Python packages (yaml, pandas) ===")
out, _ = ssh("python3 -c 'import yaml, pandas; print(\"yaml OK\", \"pandas OK\")'")
print(out or "MISSING")

print("\n=== 7. .env exists? ===")
out, _ = ssh(f"ls {BASE}/.env 2>/dev/null && echo EXISTS || echo MISSING")
print(out)

print("\n=== 8. Current crontab ===")
out, _ = ssh("crontab -l 2>/dev/null || echo (empty)")
print(out or "(empty)")

print("\n=== 9. data/config contents ===")
out, _ = ssh(f"ls {BASE}/data/config/")
print(out)
