#!/usr/bin/env python3
"""Check what lsr_accum expects from cfg on VPS."""
import sys, subprocess
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

VPS  = "root@5.223.67.21"

def ssh(cmd, timeout=60):
    r = subprocess.run(
        ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=10", VPS, cmd],
        capture_output=True, encoding="utf-8", errors="replace", timeout=timeout,
    )
    return r.stdout.strip(), r.stderr.strip()

# Print lsr_accum source
out, _ = ssh(r"""python3 - <<'PYEOF'
import sys
sys.path.insert(0, '/root/Data_back_test/binance-bot-signals')
import inspect
from scanner.screener.signals import lsr_accum, load_thresholds
print("=== lsr_accum source ===")
print(inspect.getsource(lsr_accum)[:800])
print("\n=== load_thresholds source (first 300 chars) ===")
print(inspect.getsource(load_thresholds)[:300])
PYEOF
""")
print(out)
