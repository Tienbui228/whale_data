#!/usr/bin/env python3
"""P1 deploy verify probe — read-only.
Checks: data/screener/ exists, daily_2026-07.csv line count, schema, TAGUSDT row.
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

import paramiko

KEY_FILE = r"D:\Check onchain fresh wallets\sync_key_ed25519"
HOST = "5.223.67.21"
USER = "root"
WHALE_DIR = "/root/Data_back_test/whale_data"
SEP = "=" * 70


def ssh_connect():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    pkey = paramiko.Ed25519Key.from_private_key_file(KEY_FILE)
    ssh.connect(HOST, username=USER, pkey=pkey, timeout=30)
    return ssh


def run(ssh, cmd, timeout=60):
    _, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode("utf-8", errors="replace")
    err = stderr.read().decode("utf-8", errors="replace")
    return out, err


def banner(t):
    print(f"\n{SEP}\n  {t}\n{SEP}")


def main():
    print("Connecting to VPS...")
    ssh = ssh_connect()
    print("Connected.\n")

    # 1. ls data/screener/
    banner("1. ls data/screener/")
    out, err = run(ssh, f"ls -lh {WHALE_DIR}/data/screener/ 2>&1 || echo 'DIR_MISSING'")
    print(out or err)

    # 2. Line count daily_2026-07.csv
    banner("2. wc -l daily_2026-07.csv")
    out, err = run(ssh, f"wc -l {WHALE_DIR}/data/screener/daily_2026-07.csv 2>&1 || echo 'FILE_MISSING'")
    print(out or err)

    # 3. Schema — header row
    banner("3. Header (schema §9 check)")
    out, err = run(ssh, f"head -1 {WHALE_DIR}/data/screener/daily_2026-07.csv 2>&1 || echo 'FILE_MISSING'")
    print(out or err)

    # 4. TAGUSDT row for 2026-07-29
    banner("4. TAGUSDT 2026-07-29 row")
    out, err = run(ssh, f"grep '^2026-07-29,TAGUSDT' {WHALE_DIR}/data/screener/daily_2026-07.csv 2>&1 || echo 'ROW_MISSING'")
    print(out or err)

    # 5. Total row count excluding header (should be 525 symbols per day)
    banner("5. Unique symbols in latest date")
    out, err = run(ssh, (
        f"python3 -c \""
        f"import csv; rows=list(csv.DictReader(open('{WHALE_DIR}/data/screener/daily_2026-07.csv')));"
        f"dates=sorted(set(r['date'] for r in rows)); last=dates[-1] if dates else 'NONE';"
        f"syms=[r for r in rows if r['date']==last];"
        f"print(f'last_date={{last}} count={{len(syms)}}')\""
        f" 2>&1 || echo 'PARSE_ERROR'"
    ))
    print(out or err)

    # 6. journalctl last 30 lines for whale_data service
    banner("6. journalctl whale_data last 30 lines")
    out, err = run(ssh, (
        "journalctl -u whale_data -n 30 --no-pager 2>&1 || "
        "journalctl -u oi_scanner -n 30 --no-pager 2>&1 || "
        "echo 'SERVICE_UNKNOWN'"
    ), timeout=30)
    print(out or err)

    # 7. systemctl status
    banner("7. systemctl status")
    out, err = run(ssh, (
        "systemctl status whale_data --no-pager 2>&1 || "
        "systemctl status oi_scanner --no-pager 2>&1 || "
        "echo 'SERVICE_UNKNOWN'"
    ), timeout=20)
    print(out or err)

    ssh.close()
    print(f"\n{SEP}\nProbe done.\n{SEP}")


if __name__ == "__main__":
    main()
