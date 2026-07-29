#!/usr/bin/env python3
"""Upload và chạy _remote_probe3.py trên VPS."""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

import paramiko, pathlib

KEY_FILE = r"D:\Check onchain fresh wallets\sync_key_ed25519"
HOST = "5.223.67.21"
USER = "root"
WHALE_DIR = "/root/Data_back_test/whale_data"
LOCAL = pathlib.Path(r"D:\Data back test\whale_data\_remote_probe3.py")
REMOTE = f"{WHALE_DIR}/_remote_probe3.py"
SEP = "=" * 70


def ssh_connect():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    pkey = paramiko.Ed25519Key.from_private_key_file(KEY_FILE)
    ssh.connect(HOST, username=USER, pkey=pkey, timeout=30)
    return ssh


def run(ssh, cmd, timeout=120):
    _, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode("utf-8", errors="replace")
    err = stderr.read().decode("utf-8", errors="replace")
    return out, err


def main():
    ssh = ssh_connect()
    print("Connected.\n")

    sftp = ssh.open_sftp()
    sftp.put(str(LOCAL), REMOTE)
    sftp.close()
    print(f"Uploaded {LOCAL.name} → {REMOTE}")

    VENV_PY = f"{WHALE_DIR}/.venv/bin/python3"
    out, err = run(ssh, f"cd {WHALE_DIR} && {VENV_PY} {REMOTE}", timeout=120)
    print(out)
    if err.strip():
        print("STDERR:", err[:2000])

    run(ssh, f"rm -f {REMOTE}")

    # Thêm: oi_scanner.py lines 3905-3935
    print(f"\n{SEP}\noi_scanner.py lines 3905-3940\n{SEP}")
    out, _ = run(ssh, f"sed -n '3905,3940p' /root/binance_bot_signals/oi_scanner.py 2>&1")
    print(out)

    # journalctl oibot full 00:00-00:30 raw (last 120 lines)
    print(f"\n{SEP}\njournalctl oibot 00:00-00:30 UTC 2026-07-29 (last 120)\n{SEP}")
    out, _ = run(ssh, (
        "journalctl -u oibot --since='2026-07-29 00:00' --until='2026-07-29 00:30' "
        "--no-pager 2>&1 | tail -120"
    ), timeout=30)
    print(out)

    ssh.close()
    print(f"\n{SEP}\nDone.\n{SEP}")


if __name__ == "__main__":
    main()
