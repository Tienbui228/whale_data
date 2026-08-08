#!/usr/bin/env python3
"""Show exact Telegram message from format_tg_report after S-MISSING fix."""
import sys, subprocess
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

VPS  = "root@5.223.67.21"
BASE = "/root/Data_back_test/whale_data"

def ssh(cmd, timeout=240):
    r = subprocess.run(
        ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=10", VPS, cmd],
        capture_output=True, encoding="utf-8", errors="replace", timeout=timeout,
    )
    return r.stdout.strip(), r.stderr.strip()

# Run gom_scan --daily and capture stdout, then run format_tg_report on it
script = r"""
python3 - <<'PYEOF'
import sys, json, math, subprocess
from pathlib import Path
from datetime import datetime, timezone, timedelta
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = Path('/root/Data_back_test/whale_data')
SCRIPTS = BASE / 'scripts'
STORE = BASE / 'data' / 'export'
CONFIG = BASE / 'data' / 'config'

# Run gom_scan to get stdout
import subprocess as sp
result = sp.run(
    [sys.executable, str(SCRIPTS / 'gom_scan.py'),
     '--daily', '--store', str(STORE),
     '--date', '2026-08-07',
     '--fw-filter', str(CONFIG / 'freshwatch_symbols.txt')],
    capture_output=True, encoding='utf-8', errors='replace', timeout=180
)
gom_stdout = result.stdout

# Now run format_tg_report
sys.path.insert(0, str(SCRIPTS))
import importlib.util
spec = importlib.util.spec_from_file_location("run_gom_daily", str(SCRIPTS / 'run_gom_daily.py'))
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

msg = mod.format_tg_report(gom_stdout, '2026-08-07', '02:42')
print("=== TG MESSAGE ===")
print(msg)
PYEOF
"""
out, err = ssh(script, timeout=300)
print(out)
if err:
    print("ERR:", err[:500])
