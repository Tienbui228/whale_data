#!/usr/bin/env python3
# D4 verify TG format: push run_gom_daily, run with --date 2026-08-07 (no TG send), capture report
import sys, subprocess
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

VPS  = "root@5.223.67.21"
BASE = "/root/Data_back_test/whale_data"

def ssh(cmd, timeout=300):
    r = subprocess.run(
        ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=10", VPS, cmd],
        capture_output=True, encoding="utf-8", errors="replace", timeout=timeout,
    )
    return r.stdout.strip(), r.stderr.strip()

# run_gom_daily with --dry-run or capture its built report (no TG send)
# run_gom_daily.py exports format_tg_report — call it directly
cmd = f"""cd {BASE} && python3 - <<'PYEOF'
import sys
sys.path.insert(0, "{BASE}/scripts")
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from run_gom_daily import format_tg_report, _load_gom_scan_output
stdout = _load_gom_scan_output("2026-08-07")
msg = format_tg_report(stdout, "2026-08-07", "01:25")
# Print CAMPAIGN-TRACK section only
lines = msg.splitlines()
in_ct = False
for l in lines:
    if "CAMPAIGN-TRACK" in l:
        in_ct = True
    if in_ct:
        print(l)
        if l.strip() == "" and in_ct:
            break
PYEOF"""

out, err = ssh(cmd, timeout=120)
print(out or "(empty)")
if err and ("Error" in err or "Traceback" in err):
    print("--- STDERR ---")
    print(err[:800])
