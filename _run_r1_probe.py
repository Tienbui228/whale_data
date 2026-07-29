#!/usr/bin/env python3
"""Upload and run R1 probe on VPS via paramiko SFTP + exec."""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

import paramiko, pathlib

KEY_FILE = r"D:\Check onchain fresh wallets\sync_key_ed25519"
HOST = "5.223.67.21"
USER = "root"
WHALE_DIR = "/root/Data_back_test/whale_data"
LOCAL_SCRIPT = pathlib.Path(r"D:\Data back test\whale_data\_remote_r1_probe.py")
REMOTE_SCRIPT = f"{WHALE_DIR}/_remote_r1_probe.py"
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

    # Upload probe script
    sftp = ssh.open_sftp()
    sftp.put(str(LOCAL_SCRIPT), REMOTE_SCRIPT)
    sftp.close()
    print(f"Uploaded {LOCAL_SCRIPT.name} → {REMOTE_SCRIPT}")

    # Run it using whale_data venv python
    VENV_PY = f"{WHALE_DIR}/.venv/bin/python3"
    print(f"\nRunning: {VENV_PY} {REMOTE_SCRIPT}\n{SEP}")
    out, err = run(ssh, f"cd {WHALE_DIR} && {VENV_PY} {REMOTE_SCRIPT}", timeout=120)
    print(out)
    if err.strip():
        print("STDERR:", err[:1000])

    # Cleanup remote script
    run(ssh, f"rm -f {REMOTE_SCRIPT}")
    ssh.close()
    print(f"\n{SEP}\nDone.\n{SEP}")


if __name__ == "__main__":
    main()
