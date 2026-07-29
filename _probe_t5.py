#!/usr/bin/env python3
"""Probe VPS export for T5 cooldown tokens: PARTI/EVAA/CLO/BLUAI Jul 10-29."""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

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

SCRIPT = r"""
import csv, sys
from pathlib import Path

f = Path('/root/Data_back_test/whale_data/data/export/freshwatch_daily_2026-07.csv')
rows = list(csv.DictReader(f.open(encoding='utf-8')))

targets = ['PARTIUSDT', 'EVAA', 'EVAAUSDT', 'CLOUSDT', 'CLO', 'BLUAI', 'BLUAIUSDT']
# normalize
syms = {'PARTIUSDT', 'EVAAUSDT', 'CLOUSDT', 'BLUAIUSDT'}

for sym in ['PARTIUSDT','EVAAUSDT','CLOUSDT','BLUAIUSDT']:
    data = [(r['date'], r['lsr_pos_r'], r['lsr_acc_r'], r['lsr_global_r'],
             r['oi_usd'], r['funding_avg'], r['funding_n'], r['data_ok'])
            for r in rows if r['symbol'] == sym and r['date'] >= '2026-07-10']
    print(f"\n{sym} ({len(data)} rows Jul10-29):")
    print("  date       | pos_r  | acc_r  | glsr   | oi_usd        | f_avg    | fn | ok")
    for d in data:
        print(f"  {d[0]} | {d[1]:6} | {d[2]:6} | {d[3]:6} | {float(d[4]) if d[4] else 0:>13,.0f} | {d[5]:8} | {d[6]} | {d[7]}")
"""

def main():
    ssh = ssh_connect()
    print("Connected.")
    venv_py = f"{WHALE_DIR}/.venv/bin/python3"
    out, err = run(ssh, f"cd {WHALE_DIR} && {venv_py} -c {repr(SCRIPT)}", timeout=30)
    print(out)
    if err.strip():
        print("STDERR:", err[:500])

    # Also check cooldown status in CAMPAIGNS sheet
    PROBE_CAMP = r"""
import openpyxl
wb = openpyxl.load_workbook('/root/Data_back_test/whale_data/data/ledger/ledger_v2.xlsx', read_only=True, data_only=True)
ws = wb['CAMPAIGNS']
header = [str(c) if c is not None else '' for c in next(ws.iter_rows(max_row=1, values_only=True))]
print('CAMPAIGNS cols:', header)
for row in ws.iter_rows(min_row=2, values_only=True):
    sym = str(row[0]).strip() if row else ''
    if sym in ('PARTI','EVAA','CLO','BLUAI'):
        d = {header[i]: row[i] for i in range(min(len(header), len(row))) if row[i] is not None}
        print(f"\n  {sym}: {d}")
"""
    print("\n--- CAMPAIGNS sheet for cooldown tokens ---")
    out, err = run(ssh, f"cd {WHALE_DIR} && {venv_py} -c {repr(PROBE_CAMP)}", timeout=30)
    print(out[:3000])
    if err.strip():
        print("STDERR:", err[:300])

    ssh.close()
    print("Done.")

if __name__ == "__main__":
    main()
