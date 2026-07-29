#!/usr/bin/env python3
"""Commit fix R1 trên VPS git repo."""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
import paramiko

KEY_FILE = r"D:\Check onchain fresh wallets\sync_key_ed25519"
HOST = "5.223.67.21"
USER = "root"
WHALE_DIR = "/root/Data_back_test/whale_data"

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

    # Check git status on VPS
    out, _ = run(ssh, f"cd {WHALE_DIR} && git status --short 2>&1 | head -20")
    print("VPS git status:\n", out)

    out, _ = run(ssh, f"cd {WHALE_DIR} && git log --oneline -5 2>&1")
    print("VPS git log:\n", out)

    # Check if ledger_daily.py is tracked
    out, _ = run(ssh, f"cd {WHALE_DIR} && git ls-files ledger_daily.py 2>&1")
    print("tracked?", repr(out.strip()))

    if out.strip():
        # ledger_daily.py is tracked — stage and commit
        out, err = run(ssh, f"cd {WHALE_DIR} && git add ledger_daily.py && git diff --cached --stat 2>&1")
        print("Staged:\n", out)
        out, err = run(ssh, (
            f"cd {WHALE_DIR} && git commit -m 'fix R1: normalize symbol USDT suffix join Zone A' 2>&1"
        ))
        print("Commit:\n", out, err[:200] if err.strip() else "")
    else:
        print("ledger_daily.py NOT tracked in VPS git — checking BOT repo...")
        BOT_DIR = "/root/binance_bot_signals"
        out, _ = run(ssh, f"cd {BOT_DIR} && git ls-files ledger_daily.py 2>&1")
        print("bot repo tracked?", repr(out.strip()))
        out, _ = run(ssh, f"ls {BOT_DIR}/ledger_daily.py 2>&1")
        print("bot ledger_daily?", out.strip())

    ssh.close()

if __name__ == "__main__":
    main()
