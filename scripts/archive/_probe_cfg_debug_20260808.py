#!/usr/bin/env python3
"""Debug screen_thresholds.yaml structure on VPS."""
import sys, subprocess
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

VPS  = "root@5.223.67.21"
BASE = "/root/Data_back_test/whale_data"

def ssh(cmd, timeout=60):
    r = subprocess.run(
        ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=10", VPS, cmd],
        capture_output=True, encoding="utf-8", errors="replace", timeout=timeout,
    )
    return r.stdout.strip(), r.stderr.strip()

out, _ = ssh(r"""python3 - <<'PYEOF'
import sys, yaml
sys.path.insert(0, '/root/Data_back_test/whale_data/scripts')
sys.path.insert(0, '/root/Data_back_test/binance-bot-signals')
from gom_scan import load_screen_cfg, _scfg

cfg = load_screen_cfg()
print("Top-level keys:", sorted(cfg.keys()))
g = _scfg(cfg)
print("_scfg keys:", sorted(g.keys())[:15])
print("has lsr_accum at top:", 'lsr_accum' in cfg)
print("has lsr_accum in gom:", 'lsr_accum' in g)
if 'lsr_accum' in g:
    print("lsr_accum config:", g['lsr_accum'])
PYEOF
""")
print(out)
