#!/usr/bin/env python3
"""Deploy rule-iv-first sort + peak_pos_r + build-type display fix to VPS. Verify TG message."""
import sys, subprocess
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

VPS  = "root@5.223.67.21"
BASE = "/root/Data_back_test/whale_data"
LOCAL = r"D:\Data back test\whale_data"

def scp(local, remote):
    r = subprocess.run(
        ["scp", "-o", "StrictHostKeyChecking=no", local, f"{VPS}:{remote}"],
        capture_output=True, encoding="utf-8", errors="replace", timeout=60,
    )
    print(f"SCP {'OK' if r.returncode==0 else 'FAIL'}: {local.split(chr(92))[-1]}")

def ssh(cmd, timeout=240):
    r = subprocess.run(
        ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=10", VPS, cmd],
        capture_output=True, encoding="utf-8", errors="replace", timeout=timeout,
    )
    return r.stdout.strip(), r.stderr.strip()

scp(f"{LOCAL}\\scripts\\run_gom_daily.py", f"{BASE}/scripts/run_gom_daily.py")

# Verify TG message format
script = r"""
python3 - <<'PYEOF'
import sys, subprocess
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE    = Path('/root/Data_back_test/whale_data')
SCRIPTS = BASE / 'scripts'
STORE   = BASE / 'data' / 'export'
CONFIG  = BASE / 'data' / 'config'

result = subprocess.run(
    [sys.executable, str(SCRIPTS / 'gom_scan.py'),
     '--daily', '--store', str(STORE),
     '--date', '2026-08-07',
     '--fw-filter', str(CONFIG / 'freshwatch_symbols.txt')],
    capture_output=True, encoding='utf-8', errors='replace', timeout=180
)

import importlib.util
spec = importlib.util.spec_from_file_location("run_gom_daily", str(SCRIPTS / 'run_gom_daily.py'))
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

msg = mod.format_tg_report(result.stdout, '2026-08-07', '03:00')
print(msg)
PYEOF
"""
out, err = ssh(script, timeout=300)
print(out)
if err:
    print("ERR:", err[:300])
