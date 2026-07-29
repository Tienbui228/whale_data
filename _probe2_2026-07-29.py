#!/usr/bin/env python3
"""Probe 2 — 2026-07-29:
  A. ledger_daily.py Zone A full section (lines 540-680)
  B. Symbol thực trong ledger_v2.xlsx (Zone B/campaigns sheet)
  C. journalctl screener/snapshot window rộng
  D. oi_scanner.py screener timing (khi nào chạy snapshot)
  E. TAGUSDT + BR rows trong export 29/07 để chuẩn bị T3
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

import paramiko

KEY_FILE = r"D:\Check onchain fresh wallets\sync_key_ed25519"
HOST = "5.223.67.21"
USER = "root"
BOT_DIR = "/root/binance_bot_signals"
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
    ssh = ssh_connect()
    print("Connected.\n")

    # ── A. ledger_daily.py Zone A section lines 540-680 ────────────────────
    banner("A. ledger_daily.py lines 540-680 (Zone A full)")
    out, _ = run(ssh, f"sed -n '540,680p' {WHALE_DIR}/ledger_daily.py 2>&1")
    print(out or "FILE_MISSING")

    # ── B. Ledger symbols thực (openpyxl probe) ─────────────────────────────
    banner("B. Symbol thực trong ledger_v2.xlsx — toàn bộ campaign symbols")
    PROBE_B = (
        "python3 -c \""
        "import openpyxl; "
        "from pathlib import Path; "
        "wb = openpyxl.load_workbook('/root/Data_back_test/whale_data/data/ledger/ledger_v2.xlsx', read_only=True, data_only=True); "
        "print('Sheets:', wb.sheetnames); "
        "for sh in wb.sheetnames: "
        "    ws = wb[sh]; "
        "    header = None; sym_idx = -1; date_idx = -1; "
        "    for i, row in enumerate(ws.iter_rows(values_only=True)): "
        "        vals = [str(v).lower() if v is not None else '' for v in row]; "
        "        if 'symbol' in vals and header is None: "
        "            header = [str(v) if v is not None else '' for v in row]; "
        "            sym_idx = vals.index('symbol'); "
        "            date_idx = next((j for j,v in enumerate(vals) if 'date' in v), -1); "
        "            print(f'Sheet {repr(sh)} header row {i+1}: sym@{sym_idx} date@{date_idx}'); "
        "            break; "
        "    if sym_idx >= 0: "
        "        syms = []; "
        "        for i, row in enumerate(ws.iter_rows(values_only=True, min_row=2)): "
        "            if i > 50: break; "
        "            v = row[sym_idx] if row and sym_idx < len(row) else None; "
        "            if v and str(v).strip() and str(v).strip().upper() != 'EXAMPLE': "
        "                d = row[date_idx] if date_idx >= 0 and row and date_idx < len(row) else '?'; "
        "                syms.append((repr(str(v).strip()), repr(str(d)))); "
        "        print(f'Symbols ({len(syms)}):'); "
        "        [print(f'  sym={s[0]} date={s[1]}') for s in syms] "
        "\" 2>&1 || echo PROBE_B_ERROR"
    )
    out, _ = run(ssh, PROBE_B, timeout=30)
    print(out[:4000])

    # ── C. journalctl oibot — screener/snapshot keywords, wider window ──────
    banner("C. journalctl oibot 2026-07-28 22:00 — 2026-07-29 01:30 | screener/snapshot")
    out, _ = run(ssh, (
        "journalctl -u oibot --since='2026-07-28 22:00' --until='2026-07-29 01:30' "
        "--no-pager 2>&1 | grep -i 'screener\\|snapshot\\|m5\\|pass_1\\|p1\\|daily.*csv\\|0000\\|0005\\|00:0' | head -60"
    ), timeout=30)
    print(out or "NO SCREENER MESSAGES IN WINDOW")

    # Raw last 100 lines of journalctl for oibot
    banner("C2. journalctl oibot 00:00-00:10 UTC raw")
    out, _ = run(ssh, (
        "journalctl -u oibot --since='2026-07-29 00:00' --until='2026-07-29 00:10' "
        "--no-pager 2>&1 | tail -80"
    ), timeout=30)
    print(out or "NO OUTPUT IN 00:00-00:10 WINDOW")

    # ── D. oi_scanner.py — when is snapshot_writer triggered? ───────────────
    banner("D. oi_scanner.py — snapshot_writer call site / cron/schedule trigger")
    out, _ = run(ssh, (
        f"grep -n 'snapshot_writer\\|m5_pass\\|pass_1\\|00:05\\|0005\\|schedule\\|cron\\|daily_pass\\|structural' "
        f"{BOT_DIR}/oi_scanner.py 2>&1 | head -30"
    ))
    print(out or "NOT FOUND")

    # ── E. Export TAG+BR rows ngày 28+29/07 ─────────────────────────────────
    banner("E1. Export TAGUSDT rows 2026-07-28 và 2026-07-29 (tất cả cột)")
    PROBE_E = (
        "python3 -c \""
        "import csv; "
        "rows = list(csv.DictReader(open('/root/Data_back_test/whale_data/data/export/freshwatch_daily_2026-07.csv', 'r', errors='replace'))); "
        "cols = list(rows[0].keys()) if rows else []; "
        "print('Columns:', cols); "
        "tag_rows = [r for r in rows if r.get('symbol','') == 'TAGUSDT' and r.get('date','') in ('2026-07-28','2026-07-29')]; "
        "print(f'\\nTAGUSDT 2026-07-28/29: {len(tag_rows)} rows'); "
        "[print(dict(r)) for r in tag_rows]; "
        "br_rows = [r for r in rows if r.get('symbol','') == 'BRUSDT' and r.get('date','') in ('2026-07-28','2026-07-29')]; "
        "print(f'\\nBRUSDT 2026-07-28/29: {len(br_rows)} rows'); "
        "[print(dict(r)) for r in br_rows]; "
        "\" 2>&1 || echo PROBE_E_ERROR"
    )
    out, _ = run(ssh, PROBE_E, timeout=30)
    print(out[:6000])

    # ── F. MISSING count từ store (T4) ──────────────────────────────────────
    banner("F. missing_july_2026.txt tồn tại chưa + _run_missing_check output")
    out, _ = run(ssh, (
        f"ls -lh {WHALE_DIR}/missing_july_2026.txt 2>&1; "
        f"head -30 {WHALE_DIR}/missing_july_2026.txt 2>&1 || echo 'FILE_MISSING'"
    ))
    print(out)

    # ── G. Cooldown 4 con từ store — PARTI/EVAA/CLO/BLUAI ─────────────────
    banner("G. Export store: PARTI/EVAA/CLO/BLUAI — 10 ngày gần nhất (23–29/07)")
    PROBE_G = (
        "python3 -c \""
        "import csv; "
        "rows = list(csv.DictReader(open('/root/Data_back_test/whale_data/data/export/freshwatch_daily_2026-07.csv', 'r', errors='replace'))); "
        "targets = ['PARTIUSDT', 'EVAAUSDT', 'CLOUSDT', 'BLUAIUSDT']; "
        "start = '2026-07-19'; end = '2026-07-29'; "
        "cols = list(rows[0].keys()) if rows else []; "
        "print('All cols:', cols); "
        "for sym in targets: "
        "    sym_rows = [r for r in rows if r.get('symbol','') == sym and start <= r.get('date','') <= end]; "
        "    print(f'\\n=== {sym}: {len(sym_rows)} rows ({start}–{end}) ==='); "
        "    [print(dict(r)) for r in sym_rows] "
        "\" 2>&1 || echo PROBE_G_ERROR"
    )
    out, _ = run(ssh, PROBE_G, timeout=30)
    print(out[:8000])

    ssh.close()
    print(f"\n{SEP}\nProbe 2 done.\n{SEP}")


if __name__ == "__main__":
    main()
