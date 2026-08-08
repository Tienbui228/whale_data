#!/usr/bin/env python3
"""Check BANK/PARTI actual state values."""
import sys, subprocess
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
VPS = "root@5.223.67.21"

def ssh(cmd, timeout=60):
    r = subprocess.run(
        ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=10", VPS, cmd],
        capture_output=True, encoding="utf-8", errors="replace", timeout=timeout,
    )
    return r.stdout.strip(), r.stderr.strip()

out, err = ssh(r"""python3 - <<'PYEOF'
import json
st = json.load(open('/root/Data_back_test/whale_data/data/gom_state.json'))

for tok in ['BANK','PARTI']:
    ch = st.get(tok, {})
    print(f"\n=== {tok} ===")
    for k, v in ch.items():
        if k not in ('chapter_hist', 'vwap_num', 'vwap_den'):
            print(f"  {k}: {v}")
    hist = ch.get('chapter_hist',[])
    print(f"  chapter_hist: {len(hist)} entries")
PYEOF
""")
print(out or "(empty)")
if err:
    print("ERR:", err[:300])
