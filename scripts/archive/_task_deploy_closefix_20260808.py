#!/usr/bin/env python3
"""Deploy closed_today fix + re-run dry-run to show corrected output."""
import sys, subprocess
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from pathlib import Path

REPO = Path(__file__).resolve().parent
VPS  = "root@5.223.67.21"
BASE = "/root/Data_back_test/whale_data"

def ssh(cmd, timeout=60):
    r = subprocess.run(
        ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=10", VPS, cmd],
        capture_output=True, encoding="utf-8", errors="replace", timeout=timeout,
    )
    return r.stdout.strip(), r.stderr.strip()

def scp(local, remote, timeout=20):
    r = subprocess.run(
        ["scp", "-o", "StrictHostKeyChecking=no", str(local), f"{VPS}:{remote}"],
        capture_output=True, encoding="utf-8", timeout=timeout,
    )
    ok = r.returncode == 0
    print(f"  SCP {'OK' if ok else 'FAIL'} {Path(local).name} -> {remote}")
    return ok

print("=== Deploy closed_today fix ===")
scp(REPO / "scripts" / "gom_scan.py", f"{BASE}/scripts/gom_scan.py")

print("\n=== Verify fix on VPS ===")
out, _ = ssh(f"grep -c 'prev_open_tokens' {BASE}/scripts/gom_scan.py")
print(f"  prev_open_tokens lines: {out} (expected 2)")

print("\n=== Aug CSV date range + gom_state chains ===")
# Write a temp script on VPS
check_cmd = (
    "python3 - <<'PYEOF'\n"
    "import pandas as pd, json\n"
    "df = pd.read_csv('/root/Data_back_test/whale_data/data/export/freshwatch_daily_2026-08.csv', usecols=['date'])\n"
    "dates = sorted(df['date'].unique())\n"
    "print('Aug CSV dates:', len(dates), '|', dates[0], '->', dates[-1])\n"
    "st = json.load(open('/root/Data_back_test/whale_data/data/gom_state.json'))\n"
    "oc = [(t, c) for t, c in st.items() if c.get('chain_open')]\n"
    "print(f'State open chains before re-run: {len(oc)}')\n"
    "for t, c in oc:\n"
    "    print(f'  {t}: n={c.get(\"n_days\",0)} brk={c.get(\"break_streak\",0)} start={c.get(\"start_date\",\"?\")[-5:]}')\n"
    "PYEOF"
)
out, err = ssh(check_cmd)
print(out or err)

print("\n=== Re-run dry-run with fixed code (2nd Telegram) ===")
out, err = ssh(
    f"cd {BASE} && python3 scripts/run_gom_daily.py 2>&1",
    timeout=300,
)
print(out[:5000])
if err:
    print("STDERR:", err[:200])

print("\n=== gom_daily.log last 10 lines ===")
out, _ = ssh(f"tail -10 {BASE}/data/logs/gom_daily.log")
print(out)
