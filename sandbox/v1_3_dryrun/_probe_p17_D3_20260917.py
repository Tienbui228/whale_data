"""p17 · D3 đen-một-lần · pre-check độ dài · body 5000 → too-long không gọi API."""
from __future__ import annotations
import sys, os, tempfile, shutil
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

REPO_REAL = Path(r"D:/Data back test/whale_data")
SB = Path(tempfile.mkdtemp(prefix='p17_D3_'))
(SB / "data/logs").mkdir(parents=True, exist_ok=True)

sys.path.insert(0, str(REPO_REAL / "scripts"))
import master_preview_send as mps
import importlib
importlib.reload(mps)
mps.REPO = SB
mps.LOG_P = SB / "data/logs/master_preview.log"

# Set fake env for API call attempt path (nếu qua pre-check)
os.environ["TG_BOT_TOKEN"] = "FAKE_TOKEN_DO_NOT_USE"
os.environ["TG_CHAT_ID_DAILY"] = "12345"

# Track API calls by monkey-patching urllib.request.urlopen
import urllib.request as _ur
api_call_count = 0
def _tracker(*a, **kw):
    global api_call_count
    api_call_count += 1
    raise Exception("MOCK: API call attempted")
_original = _ur.urlopen

print("═" * 74)
print("p17 · D3 đen-một-lần · pre-check độ dài text > 4096 → không gọi API")
print("═" * 74)

results = []

# ═════ TEST ĐEN · body 5000 chars ═════
_ur.urlopen = _tracker
api_call_count = 0
body_den = "A" * 5000
ok, det = mps.send_telegram(body_den)
called_api = api_call_count > 0
print(f"\nĐEN · len=5000")
print(f"  ok={ok} · det={det[:60]}")
print(f"  API called: {called_api}")
den_ok = (not ok and "BODY-TOO-LONG" in det and not called_api)
print(f"  ★ ĐEN đúng (return False · BODY-TOO-LONG · KHÔNG gọi API): {'✅' if den_ok else '❌'}")
results.append(('ĐEN 5000', den_ok))

# ═════ TEST WARN · body 3900 chars · vẫn gửi ═════
_ur.urlopen = _tracker
api_call_count = 0
body_warn = "B" * 3900
ok, det = mps.send_telegram(body_warn)
called_api = api_call_count > 0
print(f"\nWARN · len=3900")
print(f"  ok={ok} · det={det[:60]}")
print(f"  API called: {called_api}")
# Body 3900 should go through pre-check (warn log) THEN try to call API (which mock raises)
warn_ok = called_api   # API was attempted (means pre-check let it through)
# Check log for WARN
log_content = mps.LOG_P.read_text() if mps.LOG_P.exists() else ""
has_warn_log = "[WARN:BODY-NEAR-LIMIT len=3900]" in log_content
print(f"  Log has [WARN:BODY-NEAR-LIMIT]: {has_warn_log}")
warn_ok_full = called_api and has_warn_log
print(f"  ★ WARN đúng (log WARN + vẫn gọi API): {'✅' if warn_ok_full else '❌'}")
results.append(('WARN 3900', warn_ok_full))

# ═════ TEST XANH · body 3000 chars · im ═════
_ur.urlopen = _tracker
api_call_count = 0
body_xanh = "C" * 3000
ok, det = mps.send_telegram(body_xanh)
called_api = api_call_count > 0
log_content_after = mps.LOG_P.read_text() if mps.LOG_P.exists() else ""
new_lines = log_content_after[len(log_content):]
has_new_warn = "[WARN:BODY-NEAR-LIMIT" in new_lines
has_new_toolong = "[N/A-ERROR:BODY-TOO-LONG" in new_lines
print(f"\nXANH · len=3000")
print(f"  ok={ok} · det={det[:60]}")
print(f"  API called: {called_api}")
print(f"  Log has WARN or TOO-LONG for this call: WARN={has_new_warn} TOO-LONG={has_new_toolong}")
xanh_ok = called_api and not has_new_warn and not has_new_toolong
print(f"  ★ XANH đúng (im · vẫn gọi API): {'✅' if xanh_ok else '❌'}")
results.append(('XANH 3000', xanh_ok))

# Restore
_ur.urlopen = _original

print()
print("═" * 74)
all_ok = all(r[1] for r in results)
for name, ok in results:
    print(f"  {name}: {'✅' if ok else '❌'}")
print(f"VERDICT · {'✅ p17 PASS' if all_ok else '❌ p17 FAIL'}")

shutil.rmtree(SB, ignore_errors=True)
