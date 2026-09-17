"""J3 · Dry-run full pipeline · stub send · KHÔNG gửi TG."""
from __future__ import annotations
import sys, os, hashlib, re, subprocess
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

REPO = Path('/root/Data_back_test/whale_data')
os.environ['DIGEST_V1_3'] = '1'
os.environ['TG_BOT_TOKEN'] = 'FAKE_STUB'
os.environ['TG_CHAT_ID_DAILY'] = '00000'
sys.path.insert(0, str(REPO / 'scripts'))

MASTER_LIVE = '2026-09-15'
TARGETS = ['2026-09-11','2026-09-12','2026-09-13','2026-09-14','2026-09-15','2026-09-16']

# Stub urllib.urlopen so send_telegram doesn't actually hit TG
import urllib.request as _ur
_original_urlopen = _ur.urlopen
def _stub_urlopen(*a, **kw):
    raise Exception('STUB: send blocked in dry-run')
_ur.urlopen = _stub_urlopen

print('=' * 78)
print('J3 · Dry-run full pipeline · compute_verdict + rebuild_ledger + seal · stub send')
print('=' * 78)
print(f'\n{"target":12s}  {"body":>6s} {"full":>6s} {"vs4096":>7s} {"vs3800":>7s}  {"tier":>4s}  audit')
print('-' * 110)

# Import required
for m in list(sys.modules.keys()):
    if 'digest_summary' in m or 'postcheck' in m: del sys.modules[m]
from digest_summary_v2 import build_v2_digest
from postcheck_gate_d import postcheck

for t in TARGETS:
    body = build_v2_digest(t)   # actual render + persist artifact + body files
    prefix = '[MASTER · live từ 2026-09-15]\n' if t >= MASTER_LIVE else '[MASTER-PREVIEW đêm N/2]\n'
    full = prefix + body

    n_body = len(body); n_full = len(full)
    tier = 0; audit = 'none'
    if '[BUDGET-EXCEEDED:' in body:
        tier = 2
        m = re.search(r'\[BUDGET-EXCEEDED: [^\]]+\]', body)
        audit = m.group(0) if m else 'audit-parse'
    elif '[BUDGET-CAP:' in body:
        tier = 1
        m = re.search(r'\[BUDGET-CAP: cắt \d+ dòng · còn \d+/\d+\]', body)
        audit = m.group(0) if m else 'audit-parse'

    over_4096 = n_full - 4096
    over_3800 = n_full - 3800
    icon = '✅' if n_full <= 3800 else ('⚠' if n_full <= 4096 else '❌')

    # p27 verify
    pc = postcheck(t)

    print(f'{t:12s}  {n_body:>6d} {n_full:>6d} {over_4096:>+7d} {over_3800:>+7d}  T{tier:>2}   {audit[:52]}')
    print(f'{"":12s}  p21={pc["p21"]} p22={pc["p22"]} p27={pc["p27"]} · {pc.get("p27_detail","")[:70]}')

_ur.urlopen = _original_urlopen
