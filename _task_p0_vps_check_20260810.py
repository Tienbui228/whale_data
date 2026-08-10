"""
_task_p0_vps_check_20260810.py
P0: Check VPS gom_state.json — open chains + FF/BTW/PARTI status.
Run on VPS via SSH: python _task_p0_vps_check_20260810.py
"""
from __future__ import annotations
import sys, io, json, hashlib
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = Path("/root/Data_back_test/whale_data")
STATE = ROOT / "data" / "gom_state.json"

print("=== VPS P0 STATE CHECK ===")

if not STATE.exists():
    print(f"CRITICAL: gom_state.json NOT FOUND at {STATE}")
    sys.exit(1)

raw = STATE.read_bytes()
md5 = hashlib.md5(raw).hexdigest()
st = json.loads(raw.decode("utf-8"))
open_ch = {t: c for t, c in st.items() if c.get("chain_open")}

print(f"Path: {STATE}")
print(f"MD5:  {md5}")
print(f"Tokens: {len(st)}")
print(f"Open chains: {len(open_ch)}")
print(f"Open list: {sorted(open_ch.keys())}")
print()

for sym in ["FF", "BTW", "PARTI", "BULLA", "TAG"]:
    ch = st.get(sym, {})
    print(f"{sym}: in_state={sym in st}  chain_open={ch.get('chain_open')}  "
          f"close_date={ch.get('close_date','N/A')}  Q1={ch.get('Q1_cum_usd',0):,.0f}")

# Log crontab
print("\n=== CRONTAB ===")
import subprocess
result = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
print(result.stdout)
print(result.stderr)

# Log last 20 lines of gom_daily log
LOG = ROOT / "data" / "logs" / "gom_daily.log"
if LOG.exists():
    lines = LOG.read_text(encoding="utf-8", errors="replace").splitlines()
    print(f"\n=== gom_daily.log last 30 lines ===")
    for l in lines[-30:]:
        print(l)
else:
    print(f"\ngom_daily.log NOT FOUND at {LOG}")
