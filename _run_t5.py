#!/usr/bin/env python3
"""Upload and run _remote_t5.py on VPS."""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

import paramiko, pathlib

KEY_FILE = r"D:\Check onchain fresh wallets\sync_key_ed25519"
HOST = "5.223.67.21"
USER = "root"
WHALE_DIR = "/root/Data_back_test/whale_data"
LOCAL = pathlib.Path(r"D:\Data back test\whale_data\_remote_t5.py")
REMOTE = f"{WHALE_DIR}/_remote_t5.py"

def ssh_connect():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    pkey = paramiko.Ed25519Key.from_private_key_file(KEY_FILE)
    ssh.connect(HOST, username=USER, pkey=pkey, timeout=30)
    return ssh

def run(ssh, cmd, timeout=60):
    _, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    return stdout.read().decode("utf-8", errors="replace"), stderr.read().decode("utf-8", errors="replace")

def main():
    ssh = ssh_connect()
    print("Connected.")
    sftp = ssh.open_sftp()
    sftp.put(str(LOCAL), REMOTE)
    sftp.close()
    print(f"Uploaded {LOCAL.name}")

    venv_py = f"{WHALE_DIR}/.venv/bin/python3"
    out, err = run(ssh, f"cd {WHALE_DIR} && {venv_py} {REMOTE}", timeout=60)
    print(out)
    if err.strip():
        print("STDERR:", err[:1000])

    run(ssh, f"rm -f {REMOTE}")
    ssh.close()
    print("Done.")

if __name__ == "__main__":
    main()
