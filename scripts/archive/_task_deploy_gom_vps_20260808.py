#!/usr/bin/env python3
"""Task: Deploy gom_scan --daily to VPS + cron 01:00 UTC.

Steps:
  1. Create VPS directory structure (binance-bot-signals stub + scripts/)
  2. SCP: signals.py, thresholds.yaml, replay_stub.py, gom_scan.py,
          fw_loader_utils.py, screen_thresholds.yaml, run_gom_daily.py
  3. Verify import on VPS
  4. Set cron 01:00 UTC
  5. Ping test (verify Telegram creds from .env)
"""
import sys, subprocess
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from pathlib import Path

REPO     = Path(__file__).resolve().parent
VPS      = "root@5.223.67.21"
BASE     = "/root/Data_back_test/whale_data"
BOT_VPS  = "/root/Data_back_test/binance-bot-signals"

BOT_LOCAL = Path(r"D:\Data back test\binance-bot-signals")

def ssh(cmd, timeout=60):
    r = subprocess.run(
        ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=10", VPS, cmd],
        capture_output=True, encoding="utf-8", errors="replace", timeout=timeout,
    )
    return r.stdout.strip(), r.stderr.strip()

def scp(local, remote, timeout=30):
    r = subprocess.run(
        ["scp", "-o", "StrictHostKeyChecking=no", str(local), f"{VPS}:{remote}"],
        capture_output=True, encoding="utf-8", timeout=timeout,
    )
    ok = r.returncode == 0
    print(f"  SCP {'OK' if ok else 'FAIL'} {Path(local).name} → {remote}")
    if not ok:
        print(f"    {r.stderr.decode()[:100]}")
    return ok

# ── Step 1: Directory structure ───────────────────────────────────────────────
print("=== Step 1: VPS directory structure ===")
cmds = [
    f"mkdir -p {BOT_VPS}/scanner/screener",
    f"mkdir -p {BOT_VPS}/docs",
    f"mkdir -p {BASE}/scripts",
    f"mkdir -p {BASE}/data/logs",
]
for c in cmds:
    out, err = ssh(c)
    print(f"  {c}: {'OK' if not err else err[:60]}")

# ── Step 2: SCP files ─────────────────────────────────────────────────────────
print("\n=== Step 2: SCP files ===")

# 2a. signals.py + thresholds.yaml
scp(BOT_LOCAL / "scanner" / "screener" / "signals.py",
    f"{BOT_VPS}/scanner/screener/signals.py")
scp(BOT_LOCAL / "scanner" / "screener" / "thresholds.yaml",
    f"{BOT_VPS}/scanner/screener/thresholds.yaml")

# 2b. __init__.py stubs
for pkg_path in [
    f"{BOT_VPS}/__init__.py",
    f"{BOT_VPS}/scanner/__init__.py",
    f"{BOT_VPS}/scanner/screener/__init__.py",
]:
    out, err = ssh(f"touch {pkg_path}")

# 2c. replay stub (--daily doesn't use backfill; stub satisfies import)
REPLAY_STUB = """\
# replay.py stub — VPS daily mode only. backfill not supported on VPS.
def _token_from_path(p):
    from pathlib import Path
    return Path(p).stem.replace('_result', '')

def parse_result_file(p):
    raise NotImplementedError("--backfill not supported on VPS")

def build_days(*a, **kw):
    raise NotImplementedError("--backfill not supported on VPS")
"""
stub_local = REPO / "_replay_stub_vps.py"
stub_local.write_text(REPLAY_STUB, encoding="utf-8")
scp(stub_local, f"{BOT_VPS}/replay.py")

# 2d. gom_scan.py, fw_loader_utils.py, run_gom_daily.py
scp(REPO / "scripts" / "gom_scan.py",        f"{BASE}/scripts/gom_scan.py")
scp(REPO / "scripts" / "fw_loader_utils.py", f"{BASE}/scripts/fw_loader_utils.py")
scp(REPO / "scripts" / "run_gom_daily.py",   f"{BASE}/scripts/run_gom_daily.py")

# 2e. screen_thresholds.yaml
scp(REPO / "screen_thresholds.yaml", f"{BASE}/screen_thresholds.yaml")

# ── Step 3: Verify import on VPS ──────────────────────────────────────────────
print("\n=== Step 3: Verify import ===")
verify_cmd = (
    f"cd {BASE} && python3 -c \""
    f"import sys; sys.path.insert(0, 'scripts'); "
    f"import gom_scan; "
    f"print('gom_scan import OK'); "
    f"from gom_scan import eval_gom, _a3_slope_ok; "
    f"print('eval_gom+_a3_slope_ok OK')\""
)
out, err = ssh(verify_cmd, timeout=30)
print(out or err or "(no output)")

# ── Step 4: Set up cron ───────────────────────────────────────────────────────
print("\n=== Step 4: Cron 01:00 UTC ===")

# Check existing crontab
cur_cron, _ = ssh("crontab -l 2>/dev/null || echo ''")

GOM_CRON_COMMENT = "# GOM daily scan — L-44"
GOM_CRON_LINE = (
    f"0 1 * * * cd {BASE} && "
    f"python3 scripts/run_gom_daily.py "
    f">> {BASE}/data/logs/gom_daily.log 2>&1"
)

if GOM_CRON_LINE in (cur_cron or ""):
    print("  Cron already set (idempotent, no change)")
else:
    new_cron = (cur_cron.rstrip() + "\n" if cur_cron and cur_cron.strip() else "")
    new_cron += GOM_CRON_COMMENT + "\n" + GOM_CRON_LINE + "\n"
    # Write crontab via heredoc
    import tempfile, os
    tmpf = REPO / "_tmp_crontab.txt"
    tmpf.write_text(new_cron, encoding="utf-8", newline="\n")
    scp(tmpf, "/tmp/_gom_crontab.txt")
    out, err = ssh("crontab /tmp/_gom_crontab.txt && echo 'crontab installed'")
    print(out or err or "(no output)")
    tmpf.unlink(missing_ok=True)

# Verify cron
cur_cron2, _ = ssh("crontab -l")
print("  Crontab now:")
for line in (cur_cron2 or "").splitlines():
    print(f"    {line}")

# ── Step 5: Telegram ping test ────────────────────────────────────────────────
print("\n=== Step 5: Telegram ping test ===")
ping_cmd = (
    f"cd {BASE} && python3 -c \""
    f"import os, urllib.request, urllib.parse, json; "
    f"from pathlib import Path; "
    f"env = Path('.env').read_text(); "
    f"kv = {{k.strip():v.strip() for line in env.splitlines() "
    f"for k,_,v in [line.partition('=')] "
    f"if line.strip() and not line.startswith('#')}}; "
    f"tok = kv.get('TELEGRAM_BOT_TOKEN',''); "
    f"cid = kv.get('TELEGRAM_CHAT_ID',''); "
    f"url = f'https://api.telegram.org/bot{{tok}}/sendMessage'; "
    f"data = urllib.parse.urlencode({{'chat_id':cid,'text':'GOM ping OK — deploy 2026-08-08'}}).encode(); "
    f"r = urllib.request.urlopen(urllib.request.Request(url,data=data,method='POST'),timeout=10); "
    f"resp = json.loads(r.read()); "
    f"print('Telegram ping:', 'OK' if resp.get('ok') else 'FAIL', resp.get('description',''))\""
)
out, err = ssh(ping_cmd, timeout=30)
print(out or err or "(no output)")

# ── Heartbeat file init ───────────────────────────────────────────────────────
print("\n=== Step 4b: Heartbeat file init ===")
out, err = ssh(
    f"python3 -c \"from datetime import datetime,timezone; "
    f"open('{BASE}/data/gom_heartbeat.txt','w').write("
    f"datetime.now(timezone.utc).isoformat())\" && echo 'HB written'"
)
print(out or err)

print("\n=== Deploy complete ===")
print(f"Cron: 01:00 UTC daily → scripts/run_gom_daily.py")
print(f"First natural fire: tomorrow 01:00 UTC → report for {__import__('datetime').date.today()}")
