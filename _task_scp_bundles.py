#!/usr/bin/env python3
"""SCP 4 git bundles lên VPS /root/archive/ và verify."""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import subprocess

KEY  = r"C:\Users\Hello\.ssh\binance_vps_nopass"
HOST = "root@5.223.67.21"
REMOTE_DIR = "/root/archive"

BUNDLES = [
    r"C:\Users\Hello\OneDrive\Máy tính\Binance_bot\binance-bot-signals_20260731.bundle",
    r"D:\Data back test\whale_data_20260731.bundle",
    r"D:\Check onchain fresh wallets_20260731.bundle",
    r"D:\Whales_scan_20260731.bundle",
]

def ssh(cmd: str, timeout: int = 30) -> tuple[int, str]:
    r = subprocess.run(
        ["ssh", "-i", KEY, "-o", "StrictHostKeyChecking=no",
         "-o", "ConnectTimeout=10", HOST, cmd],
        capture_output=True, text=True, timeout=timeout
    )
    out = (r.stdout + r.stderr).strip()
    return r.returncode, out

def scp(local: str, remote: str, timeout: int = 120) -> tuple[int, str]:
    r = subprocess.run(
        ["scp", "-i", KEY, "-o", "StrictHostKeyChecking=no",
         "-o", "ConnectTimeout=10", local, remote],
        capture_output=True, text=True, timeout=timeout
    )
    out = (r.stdout + r.stderr).strip()
    return r.returncode, out

# Ensure archive dir exists
rc, out = ssh(f"mkdir -p {REMOTE_DIR}")
print(f"mkdir /root/archive: rc={rc} {out or 'OK'}")

# SCP each bundle
print()
for bundle_path in BUNDLES:
    from pathlib import Path
    bundle_name = Path(bundle_path).name
    remote_path = f"{HOST}:{REMOTE_DIR}/{bundle_name}"
    print(f"SCP {bundle_name} ...")
    rc, out = scp(bundle_path, remote_path, timeout=180)
    if rc == 0:
        print(f"  → OK")
    else:
        print(f"  → FAIL rc={rc}: {out}")

# Verify each bundle on VPS
print()
print("=== Verify bundles on VPS ===")
rc, out = ssh(f"ls -lh {REMOTE_DIR}/*.bundle 2>/dev/null")
print(out or "(no bundles found)")

print()
for bundle_path in BUNDLES:
    from pathlib import Path
    bundle_name = Path(bundle_path).name
    rc, out = ssh(f"git bundle verify {REMOTE_DIR}/{bundle_name} 2>&1 | head -3", 30)
    status = "OK" if rc == 0 and "okay" in out else "FAIL"
    print(f"  {bundle_name}: [{status}] {out.splitlines()[0] if out else ''}")

print("\nDone.")
