#!/usr/bin/env python3
"""T1: Check P1 deploy status — files, mtime, service start vs deploy."""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
import paramiko

KEY_FILE = r"D:\Check onchain fresh wallets\sync_key_ed25519"
HOST = "5.223.67.21"
USER = "root"
BOT_DIR = "/root/binance_bot_signals"
SEP = "=" * 60

def ssh_connect():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    pkey = paramiko.Ed25519Key.from_private_key_file(KEY_FILE)
    ssh.connect(HOST, username=USER, pkey=pkey, timeout=30)
    return ssh

def run(ssh, cmd, timeout=30):
    _, o, e = ssh.exec_command(cmd, timeout=timeout)
    return o.read().decode("utf-8", errors="replace"), e.read().decode("utf-8", errors="replace")

def main():
    ssh = ssh_connect()
    print("Connected.\n")

    # 1. Service status + start time
    print(f"{SEP}\n1. oibot service status\n{SEP}")
    out, _ = run(ssh, "systemctl status oibot --no-pager 2>&1 | head -20")
    print(out)

    # 2. oi_scanner.py mtime + size
    print(f"{SEP}\n2. oi_scanner.py file info\n{SEP}")
    out, _ = run(ssh, f"ls -la {BOT_DIR}/oi_scanner.py 2>&1")
    print(out)
    out, _ = run(ssh, f"stat {BOT_DIR}/oi_scanner.py 2>&1 | grep -E 'Modify|Size'")
    print(out)

    # 3. Search for m5 / screener-related function defs in oi_scanner.py
    print(f"{SEP}\n3. Screener/m5 function defs in oi_scanner.py\n{SEP}")
    out, _ = run(ssh, f"grep -n 'def.*scree\\|def.*m5\\|def.*snap\\|_snapshot\\|m5_struct\\|screener_pass' {BOT_DIR}/oi_scanner.py 2>&1 | head -20")
    print(out)

    # 4. List ALL Python files in BOT_DIR with mtime (sorted newest first)
    print(f"{SEP}\n4. Python files in bot dir (mtime order)\n{SEP}")
    out, _ = run(ssh, f"ls -lt {BOT_DIR}/*.py 2>&1 | head -20")
    print(out)

    # 5. Any modules subdirs?
    print(f"{SEP}\n5. Subdirectories / modules\n{SEP}")
    out, _ = run(ssh, f"ls -la {BOT_DIR}/ 2>&1 | head -30")
    print(out)

    # 6. Check if there's an 'Item 5' or deploy log on VPS
    print(f"{SEP}\n6. Any deploy/scp log\n{SEP}")
    out, _ = run(ssh, "ls -la /root/*.sh /root/*.log /root/deploy* 2>&1 | head -20")
    print(out)
    out, _ = run(ssh, "ls -la /root/binance_bot_signals/DEPLOY* /root/binance_bot_signals/deploy* 2>&1 | head -10")
    print(out)

    # 7. journalctl oibot last start + screener around 00:05-00:10 today
    print(f"{SEP}\n7. journalctl oibot: last restart + today 00:00-00:15\n{SEP}")
    out, _ = run(ssh, (
        "journalctl -u oibot --no-pager -n 5 --output=short-iso 2>&1"
    ), timeout=15)
    print("Last 5 lines:\n", out)
    out, _ = run(ssh, (
        "journalctl -u oibot --since='2026-07-29 00:00' --until='2026-07-29 00:15' "
        "--no-pager 2>&1 | grep -i 'screen\\|m5\\|start\\|stop\\|restart\\|snapshot' | head -20"
    ), timeout=20)
    print("Today screener/start filtered:\n", out)

    # 8. Full oi_scanner.py _snapshot_writer section (confirm code exists)
    print(f"{SEP}\n8. _snapshot_writer code (confirm exists + show trigger logic)\n{SEP}")
    out, _ = run(ssh, f"grep -n '_snapshot_writer\\|snapshot_writer\\|screener_dir\\|daily_' {BOT_DIR}/oi_scanner.py 2>&1 | head -20")
    print(out)

    ssh.close()
    print(f"\n{SEP}\nDone.\n{SEP}")

if __name__ == "__main__":
    main()
