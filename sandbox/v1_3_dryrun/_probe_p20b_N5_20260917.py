"""p20b · N5 refresh_universe_weekly · đen-một-lần fail-closed."""
from __future__ import annotations
import sys, os, json, tempfile, shutil, subprocess, hashlib
from pathlib import Path
from unittest.mock import patch

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

REPO_REAL = Path(r"D:/Data back test/whale_data")
SB = Path(tempfile.mkdtemp(prefix='p20b_'))
(SB / 'data/config').mkdir(parents=True, exist_ok=True)
(SB / 'data/logs').mkdir(parents=True, exist_ok=True)

# Seed sandbox with current fw + sidecar
INITIAL_FW = ['AAAUSDT', 'BBBUSDT', 'CCCUSDT']
(SB / 'data/config/freshwatch_symbols.txt').write_text('\n'.join(INITIAL_FW) + '\n', encoding='utf-8')
INITIAL_SIDECAR = {s: {'src': 'curated', 'date': '<pre-tracking>'} for s in INITIAL_FW}
(SB / 'data/config/freshwatch_source.json').write_text(json.dumps(INITIAL_SIDECAR, indent=2), encoding='utf-8')

# Import refresh_universe_weekly with sandbox paths
sys.path.insert(0, str(REPO_REAL / 'scripts'))
import refresh_universe_weekly as ruw
import importlib
importlib.reload(ruw)
ruw.REPO = SB
ruw.FW_PATH = SB / 'data/config/freshwatch_symbols.txt'
ruw.SIDECAR_PATH = SB / 'data/config/freshwatch_source.json'
ruw.LOG_PATH = SB / 'data/logs/refresh_universe.log'

print("═" * 74)
print("p20b · N5 refresh_universe_weekly · fail-closed đen-một-lần")
print("═" * 74)

results = []

# ═════ CASE ĐEN 1: Alpha endpoint rỗng ═════
print("\n[ĐEN 1: Alpha endpoint rỗng]")
def _fetch_empty(url, name):
    if 'ALPHA' in name.upper() or 'alpha' in url:
        return []
    # return valid fapi
    return {'symbols': [{'symbol': 'AAAUSDT', 'onboardDate': 1600000000000, 'status': 'TRADING'}]}

initial_md5 = hashlib.md5(ruw.FW_PATH.read_bytes()).hexdigest()
try:
    with patch.object(ruw, '_fetch', side_effect=_fetch_empty):
        result = subprocess.run([sys.executable, '-c', f'''
import sys
sys.path.insert(0, {str(REPO_REAL / "scripts")!r})
import refresh_universe_weekly as ruw
from pathlib import Path
ruw.REPO = Path({str(SB)!r})
ruw.FW_PATH = ruw.REPO / "data/config/freshwatch_symbols.txt"
ruw.SIDECAR_PATH = ruw.REPO / "data/config/freshwatch_source.json"
ruw.LOG_PATH = ruw.REPO / "data/logs/refresh_universe.log"
def _fetch_empty(url, name):
    if "ALPHA" in name.upper():
        import sys; ruw._log("[N/A-ERROR:ALPHA-EMPTY] empty response"); sys.exit(1)
    return {{"symbols": [{{"symbol": "AAAUSDT", "onboardDate": 1600000000000, "status": "TRADING"}}]}}
ruw._fetch = _fetch_empty
ruw.main()
'''], capture_output=True, text=True)
    exit_code = result.returncode
except SystemExit as e:
    exit_code = e.code

final_md5 = hashlib.md5(ruw.FW_PATH.read_bytes()).hexdigest()
den1_ok = (exit_code != 0 and initial_md5 == final_md5)
print(f"  exit={exit_code} (expect ≠0) · fw md5 changed={initial_md5 != final_md5} (expect False)")
print(f"  ★ ĐEN 1 {'PASS' if den1_ok else 'FAIL'}")
results.append(('ĐEN 1 alpha empty', den1_ok))

# ═════ CASE ĐEN 2: rule không có bất kỳ token nào (0 candidate) ═════
print("\n[ĐEN 2: rule match 0 tokens (candidates rỗng)]")
initial_md5 = hashlib.md5(ruw.FW_PATH.read_bytes()).hexdigest()
try:
    result = subprocess.run([sys.executable, '-c', f'''
import sys
sys.path.insert(0, {str(REPO_REAL / "scripts")!r})
import refresh_universe_weekly as ruw
from pathlib import Path
ruw.REPO = Path({str(SB)!r})
ruw.FW_PATH = ruw.REPO / "data/config/freshwatch_symbols.txt"
ruw.SIDECAR_PATH = ruw.REPO / "data/config/freshwatch_source.json"
ruw.LOG_PATH = ruw.REPO / "data/logs/refresh_universe.log"
def _fetch_stub(url, name):
    # Alpha: 1 token, listing 5 days ago (fail >14d rule)
    if "ALPHA" in name.upper():
        return [{{"symbol": "XYZ", "listingTime": (__import__("time").time() - 5*86400) * 1000}}]
    return {{"symbols": [{{"symbol": "XYZUSDT", "onboardDate": (__import__("time").time() - 5*86400) * 1000, "status": "TRADING"}}]}}
ruw._fetch = _fetch_stub
ruw.main()
'''], capture_output=True, text=True)
    exit_code = result.returncode
except SystemExit as e:
    exit_code = e.code

final_md5 = hashlib.md5(ruw.FW_PATH.read_bytes()).hexdigest()
den2_ok = (exit_code != 0 and initial_md5 == final_md5)
print(f"  exit={exit_code} (expect ≠0 · NO-CANDIDATES=2) · fw md5 changed={initial_md5 != final_md5} (expect False)")
print(f"  ★ ĐEN 2 {'PASS' if den2_ok else 'FAIL'}")
results.append(('ĐEN 2 no-candidates', den2_ok))

# ═════ CASE XANH: endpoint ok · thêm đúng số ═════
print("\n[XANH: endpoint ok · thêm 2 tokens hợp lệ]")
initial_fw = ruw._load_freshwatch()
initial_md5 = hashlib.md5(ruw.FW_PATH.read_bytes()).hexdigest()
initial_len = len(initial_fw)
try:
    import time
    ok_ts_ms = (time.time() - 30 * 86400) * 1000   # 30 days ago
    result = subprocess.run([sys.executable, '-c', f'''
import sys
sys.path.insert(0, {str(REPO_REAL / "scripts")!r})
import refresh_universe_weekly as ruw
from pathlib import Path
ruw.REPO = Path({str(SB)!r})
ruw.FW_PATH = ruw.REPO / "data/config/freshwatch_symbols.txt"
ruw.SIDECAR_PATH = ruw.REPO / "data/config/freshwatch_source.json"
ruw.LOG_PATH = ruw.REPO / "data/logs/refresh_universe.log"
def _fetch_stub(url, name):
    ts_ms = {ok_ts_ms}
    if "ALPHA" in name.upper():
        # Alpha has AAA (already in fw), NEW1, NEW2, and NEW3 (only 5d, fail rule)
        return [
            {{"symbol": "AAA", "listingTime": ts_ms}},
            {{"symbol": "NEW1", "listingTime": ts_ms}},
            {{"symbol": "NEW2", "listingTime": ts_ms}},
            {{"symbol": "NEW3", "listingTime": (__import__("time").time() - 5*86400)*1000}},
        ]
    return {{"symbols": [
        {{"symbol": "AAAUSDT", "onboardDate": ts_ms, "status": "TRADING"}},
        {{"symbol": "NEW1USDT", "onboardDate": ts_ms, "status": "TRADING"}},
        {{"symbol": "NEW2USDT", "onboardDate": ts_ms, "status": "TRADING"}},
        {{"symbol": "NEW3USDT", "onboardDate": ts_ms, "status": "TRADING"}},
    ]}}
ruw._fetch = _fetch_stub
# stub _tg_notify to avoid actual send
ruw._tg_notify = lambda x: None
ruw.main()
'''], capture_output=True, text=True)
    exit_code = result.returncode
except SystemExit as e:
    exit_code = e.code

final_fw = ruw._load_freshwatch()
final_md5 = hashlib.md5(ruw.FW_PATH.read_bytes()).hexdigest()
added = [s for s in final_fw if s not in initial_fw]
xanh_ok = (exit_code == 0 and set(added) == {'NEW1USDT', 'NEW2USDT'}
           and len(final_fw) == initial_len + 2)
print(f"  exit={exit_code} (expect 0) · added={added} (expect [NEW1USDT, NEW2USDT])")
print(f"  fw {initial_len} → {len(final_fw)} · md5 {initial_md5[:12]} → {final_md5[:12]}")
print(f"  ★ XANH {'PASS' if xanh_ok else 'FAIL'}")
results.append(('XANH add 2', xanh_ok))

# Print sidecar to verify auto-tagging
sidecar_after = json.loads(ruw.SIDECAR_PATH.read_text())
print(f"  Sidecar new entries: {{k:v for k,v in sidecar_after.items() if k in added}}")

# ═════ CASE ĐEN 3 · P3/17-09 · Partial-fetch (60/656 = <80% floor) ═════
print("\n[ĐEN 3: Alpha trả 60 tokens (< 80% × 656 last-fetch) · sàn 80%]")
# Seed last_stats với 656 (typical fetch size)
(SB / 'data/state').mkdir(parents=True, exist_ok=True)
(SB / 'data/state/refresh_universe_last_stats.json').write_text(
    json.dumps({"n_alpha": 656, "n_fapi": 900, "n_candidates": 200, "run_ts": "2026-09-10"}),
    encoding='utf-8'
)
initial_md5 = hashlib.md5(ruw.FW_PATH.read_bytes()).hexdigest()
try:
    result = subprocess.run([sys.executable, '-c', f'''
import sys
sys.path.insert(0, {str(REPO_REAL / "scripts")!r})
import refresh_universe_weekly as ruw
from pathlib import Path
ruw.REPO = Path({str(SB)!r})
ruw.FW_PATH = ruw.REPO / "data/config/freshwatch_symbols.txt"
ruw.SIDECAR_PATH = ruw.REPO / "data/config/freshwatch_source.json"
ruw.LOG_PATH = ruw.REPO / "data/logs/refresh_universe.log"
ruw.LAST_FETCH_STATS = ruw.REPO / "data/state/refresh_universe_last_stats.json"
def _fetch_partial(url, name):
    if "ALPHA" in name.upper():
        # Return 60 tokens (< 80% × 656 = 524)
        import time
        ts_ms = (time.time() - 30*86400) * 1000
        return [{{"symbol": f"TOK{{i}}", "listingTime": ts_ms}} for i in range(60)]
    return {{"symbols": [{{"symbol": f"TOK{{i}}USDT", "onboardDate": 1600000000000, "status": "TRADING"}} for i in range(60)]}}
ruw._fetch = _fetch_partial
ruw._tg_notify = lambda x: None
ruw.main()
'''], capture_output=True, text=True)
    exit_code = result.returncode
except SystemExit as e:
    exit_code = e.code

final_md5 = hashlib.md5(ruw.FW_PATH.read_bytes()).hexdigest()
den3_ok = (exit_code == 3 and initial_md5 == final_md5)
print(f"  exit={exit_code} (expect 3 · ALPHA-PARTIAL) · fw md5 changed={initial_md5 != final_md5} (expect False)")
print(f"  ★ ĐEN 3 {'PASS' if den3_ok else 'FAIL'}")
results.append(('ĐEN 3 alpha-partial', den3_ok))


# ═════ Verdict ═════
print()
print("═" * 74)
all_ok = all(r[1] for r in results)
for name, ok in results: print(f"  {name}: {'✅' if ok else '❌'}")
print(f"★ p20b {'PASS ✅' if all_ok else 'FAIL ❌'}")

shutil.rmtree(SB, ignore_errors=True)
