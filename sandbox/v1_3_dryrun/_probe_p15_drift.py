"""T2 · Pin p15 · crontab drift guard đen-một-lần.

Three-way test:
  XANH: crontab khớp baseline → exit 0 · no flag · log OK
  ĐEN: crontab đổi 1 dòng → exit 1 · flag · log DRIFT
  ĐEN2: expected file vắng → exit 1 · flag NO-BASELINE · KHÔNG tự sinh baseline
"""
from __future__ import annotations
import sys, os, subprocess, hashlib, tempfile, shutil, json
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

REPO_REAL = Path(r"D:/Data back test/whale_data")
SCRIPT = REPO_REAL / "scripts/check_crontab_drift.sh"

# Create isolated sandbox for testing
TEST_DIR = Path(tempfile.mkdtemp(prefix="drift_pin_"))
(TEST_DIR / "data/state").mkdir(parents=True, exist_ok=True)
(TEST_DIR / "data/logs").mkdir(parents=True, exist_ok=True)

FLAG = TEST_DIR / "data/state/crontab_drift.flag"
EXPECTED = TEST_DIR / "data/state/crontab_expected.md5"

# Fake crontab commands (bash echo · deterministic)
CRON_ORIG = "05 01 * * * cmd_spot\n30 01 * * * cmd_alpha\n46 01 * * * cmd_master\n"
CRON_MUTATED = "05 01 * * * cmd_spot\n00 02 * * * cmd_alpha\n46 01 * * * cmd_master\n"   # alpha đổi lịch

def _run_script(fake_crontab_content):
    """Run script with fake `crontab -l` output."""
    # Write fake crontab to a file and set env CRONTAB_DRIFT_CMD to cat it
    # IMPORTANT: use write_bytes to preserve LF (Windows write_text may CRLF)
    tmp = TEST_DIR / f"fake_crontab_{hashlib.md5(fake_crontab_content.encode()).hexdigest()[:6]}.txt"
    tmp.write_bytes(fake_crontab_content.encode("utf-8"))
    env = os.environ.copy()
    env["CRONTAB_DRIFT_CMD"] = f"cat {tmp.as_posix()}"
    env["CRONTAB_DRIFT_REPO"] = str(TEST_DIR).replace("\\", "/")
    # Windows: bash via git-bash / WSL fallback — use `sh` if available
    for bash_cmd in ["bash", "sh"]:
        try:
            r = subprocess.run([bash_cmd, str(SCRIPT)], env=env, capture_output=True,
                              text=True, timeout=20)
            return r
        except FileNotFoundError:
            continue
    print("  (skip: no bash/sh available on Windows — test on VPS)")
    return None


# ═════ TEST 1 · XANH (khớp baseline · dùng ĐÚNG lệnh production) ═════
print("═══ T2 · Pin p15 · drift guard đen-một-lần ═══\n")
print("── TEST 1 · XANH · baseline sinh bởi `crontab-fake | md5sum | cut -d' ' -f1` ──")
# Write CRON_ORIG to file first, then generate baseline via SAME PATH as step (c)
cron_orig_file = TEST_DIR / "cron_orig.txt"
cron_orig_file.write_bytes(CRON_ORIG.encode("utf-8"))
# Emulate: `crontab -l | md5sum | cut -d' ' -f1 > EXPECTED`
gen_cmd = f"cat {cron_orig_file.as_posix()} | md5sum | cut -d' ' -f1"
for bash_cmd in ["bash", "sh"]:
    try:
        r_gen = subprocess.run([bash_cmd, "-c", gen_cmd], capture_output=True, text=True, timeout=10)
        baseline_md5 = r_gen.stdout.strip()
        break
    except FileNotFoundError: continue
EXPECTED.write_bytes((baseline_md5 + "\n").encode("utf-8"))
print(f"  baseline generated via prod-path: {baseline_md5}")
# Reset flag
if FLAG.exists(): FLAG.unlink()
r1 = _run_script(CRON_ORIG)
xanh_ok = False
if r1 is not None:
    print(f"  exit_code={r1.returncode}  stdout='{r1.stdout.strip()}'  stderr='{r1.stderr.strip()[:80]}'")
    xanh_ok = (r1.returncode == 0 and "OK" in r1.stdout and not FLAG.exists())
    print(f"  ★ XANH đúng (exit 0 · no flag · log OK)? {'✅' if xanh_ok else '❌'}")

# ═════ TEST 2 · ĐEN (mutate crontab · lệch baseline) ═════
print("\n── TEST 2 · ĐEN · crontab đổi 1 dòng · baseline giữ nguyên ──")
if FLAG.exists(): FLAG.unlink()
r2 = _run_script(CRON_MUTATED)
den_ok = False
if r2 is not None:
    print(f"  exit_code={r2.returncode}  stdout='{r2.stdout.strip()}'  stderr='{r2.stderr.strip()[:80]}'")
    den_ok = (r2.returncode == 1 and "DRIFT" in r2.stdout and FLAG.exists())
    if FLAG.exists():
        flag_content = FLAG.read_text(encoding="utf-8").strip()
        print(f"  flag content: {flag_content}")
        try:
            flag_json = json.loads(flag_content)
            has_reason = flag_json.get("reason") == "DRIFT"
        except: has_reason = False
        den_ok = den_ok and has_reason
    print(f"  ★ ĐEN đúng (exit 1 · flag DRIFT · log DRIFT)? {'✅' if den_ok else '❌'}")

# ═════ TEST 3 · ĐEN2 (baseline file vắng · KHÔNG tự sinh) ═════
print("\n── TEST 3 · ĐEN2 · baseline file vắng · KHÔNG tự sinh ──")
if FLAG.exists(): FLAG.unlink()
if EXPECTED.exists(): EXPECTED.unlink()
r3 = _run_script(CRON_ORIG)
den2_ok = False
if r3 is not None:
    print(f"  exit_code={r3.returncode}  stdout='{r3.stdout.strip()}'  stderr='{r3.stderr.strip()[:80]}'")
    baseline_still_missing = not EXPECTED.exists()
    flag_created = FLAG.exists()
    den2_ok = (r3.returncode == 1 and "NO-BASELINE" in r3.stdout
               and flag_created and baseline_still_missing)
    print(f"  baseline still missing (không tự sinh)? {'✅' if baseline_still_missing else '❌ TỰ SINH'}")
    print(f"  flag created NO-BASELINE? {'✅' if flag_created else '❌'}")
    print(f"  ★ ĐEN2 đúng (exit 1 · flag NO-BASELINE · KHÔNG sinh baseline)? {'✅' if den2_ok else '❌'}")

# ═════ TEST 4 · ĐEN3 FORMAT (baseline lưu kiểu cũ `<hash>  -` từ md5sum stdin) ═════
print("\n── TEST 4 · ĐEN3 FORMAT · baseline `<hash>  -\\n` (kiểu cũ, không cut) ──")
if FLAG.exists(): FLAG.unlink()
# Baseline format: md5sum stdin output = "<hash>  -\n"
baseline_old_format = f"{baseline_md5}  -\n"
EXPECTED.write_bytes(baseline_old_format.encode("utf-8"))
print(f"  baseline lưu: {repr(baseline_old_format)}")
r4 = _run_script(CRON_ORIG)   # CRON_ORIG khớp baseline_md5
den3_ok = False
if r4 is not None:
    print(f"  exit_code={r4.returncode}  stdout='{r4.stdout.strip()}'  stderr='{r4.stderr.strip()[:80]}'")
    den3_ok = (r4.returncode == 0 and "OK" in r4.stdout and not FLAG.exists())
    print(f"  ★ ĐEN3 đúng (format cũ vẫn compare pass · không kêu oan)? {'✅' if den3_ok else '❌ KÊU OAN'}")

# ═════ VERDICT ═════
print(f"\n══ Pin p15 verdict ══")
print(f"  · TEST 1 XANH:         {xanh_ok}")
print(f"  · TEST 2 ĐEN mutate:   {den_ok}")
print(f"  · TEST 3 ĐEN2 vắng:    {den2_ok}")
print(f"  · TEST 4 ĐEN3 format:  {den3_ok}")
if xanh_ok and den_ok and den2_ok and den3_ok:
    print(f"  ★ p15 pin PASS · guard đủ răng · không tự khoét cửa hậu · không kêu oan format")
else:
    print(f"  ★ p15 pin FAIL · không cài lên VPS trước khi sửa")

# Cleanup
shutil.rmtree(TEST_DIR, ignore_errors=True)
