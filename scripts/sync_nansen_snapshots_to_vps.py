#!/usr/bin/env python3
"""[H1-đường-(a) KÝ 28/08] Local Windows Task Scheduler sync Nansen snapshots → VPS.

Chạy local 01:10 UTC (post Nansen 01:00 UTC = 08:10 VN):
  1. Đọc last_run.json.last_success
  2. Kiểm tra = ngày kỳ vọng (D-1 UTC) → sync; khác/thiếu → skip + log
  3. SCP snapshots/*.json + last_run.json → VPS data/raw/nansen_snapshots/
  4. Retention 30d rotate trên VPS (xóa file >30d)
  5. Máy tắt/bot fail → cron miss → H1=N/A ngày đó (adapter graceful)

Windows Task Scheduler entry đề xuất:
  Trigger: Daily 01:10 UTC (08:10 VN)
  Action:  python "D:\\Data back test\\whale_data\\scripts\\sync_nansen_snapshots_to_vps.py"
"""
from __future__ import annotations
import sys, io, json, subprocess, hashlib
from pathlib import Path
from datetime import datetime, timezone, timedelta
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

LOCAL_SNAPSHOTS = Path(r"D:/Check onchain fresh wallets/snapshots")
LOCAL_LAST_RUN = Path(r"D:/Check onchain fresh wallets/last_run.json")
VPS_HOST = "root@5.223.67.21"
VPS_PATH = "/root/Data_back_test/whale_data/data/raw/nansen_snapshots/"
LOG_PATH = Path(r"D:/Data back test/whale_data/data/logs/sync_nansen_snapshots.log")
RETENTION_DAYS = 30


def _log(msg):
    ts = datetime.now(timezone.utc).isoformat()
    line = f"[{ts}] {msg}"
    print(line)
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def main():
    today_utc = datetime.now(timezone.utc)
    expected_last = today_utc.strftime("%Y-%m-%d")  # bot filename = today (T)

    _log(f"[SYNC] START local nansen → VPS · expected last_success={expected_last}")

    if not LOCAL_LAST_RUN.exists():
        _log(f"[SKIP] last_run.json missing at {LOCAL_LAST_RUN}")
        sys.exit(0)

    try:
        last_run = json.loads(LOCAL_LAST_RUN.read_text(encoding="utf-8"))
    except Exception as e:
        _log(f"[SKIP] last_run.json parse fail: {e}")
        sys.exit(0)

    last_success = last_run.get("last_success", "")
    # [FIX 28/08] last_success = ISO datetime "YYYY-MM-DDThh:mm:ss"; expected_last = date "YYYY-MM-DD"
    # → compare date portion only (last_success[:10]) không compare full string.
    last_success_date = last_success[:10] if last_success else ""
    if last_success_date != expected_last:
        _log(f"[SKIP] last_success_date={last_success_date} ≠ expected={expected_last} (raw={last_success}) — máy tắt/bot fail; H1 sẽ N/A ngày đó (adapter cờ)")
        sys.exit(0)

    # Guard passed — sync snapshots + last_run.json
    _log(f"[GUARD-PASS] last_success={last_success} matches expected. Proceed sync.")

    # Sync new-only via SCP (rsync unavailable on Windows OpenSSH by default)
    # [FIX 28/08] Windows OpenSSH scp KHÔNG expand glob *.json → phải liệt file explicit.
    snapshot_files = sorted(LOCAL_SNAPSHOTS.glob("*.json"))
    if not snapshot_files:
        _log(f"[SKIP] snapshots dir empty: {LOCAL_SNAPSHOTS}")
        sys.exit(0)
    # Pass explicit file list (scp accept multiple sources + 1 dest)
    scp_args = ["scp", "-p"] + [str(p) for p in snapshot_files] + [f"{VPS_HOST}:{VPS_PATH}"]
    r = subprocess.run(scp_args, capture_output=True, text=True, shell=False)
    _log(f"[SCP snapshots] rc={r.returncode}  n_files={len(snapshot_files)}  stderr={r.stderr[:200]}")

    r2 = subprocess.run(
        ["scp", "-p", str(LOCAL_LAST_RUN), f"{VPS_HOST}:{VPS_PATH}"],
        capture_output=True, text=True,
    )
    _log(f"[SCP last_run.json] rc={r2.returncode}  stderr={r2.stderr[:200]}")

    # Retention 30d rotate on VPS
    cutoff = (today_utc - timedelta(days=RETENTION_DAYS)).strftime("%Y-%m-%d")
    cleanup_cmd = (
        f"cd {VPS_PATH} && "
        f"for f in $(ls *.json 2>/dev/null | grep -oP '^\\d{{4}}-\\d{{2}}-\\d{{2}}' | sort); do "
        f"  if [ \"$f\" \\< \"{cutoff}\" ]; then rm -f \"$f.json\"; fi; "
        f"done"
    )
    r3 = subprocess.run(
        ["ssh", VPS_HOST, cleanup_cmd],
        capture_output=True, text=True,
    )
    _log(f"[RETENTION cleanup <{cutoff}] rc={r3.returncode}")

    _log(f"[SYNC] DONE")


if __name__ == "__main__":
    main()
