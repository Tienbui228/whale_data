#!/usr/bin/env python3
"""Mega probe 2026-07-29:
  A. Tìm handover_addendum_A_2026-07-28.md trên VPS
  B. Kiểm cả hai path screener + mtime daily_2026-07.csv
  C. Export: dòng 2026-07-29 có chưa?
  D. R1 probe: symbol format export vs ledger_daily.py join logic
  E. Tìm p0_5b_report.md trên VPS
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

    # ── A. Handover A1 ──────────────────────────────────────────────────────
    banner("A. Tìm handover_addendum_A_2026-07-28.md trên VPS")
    out, _ = run(ssh, "find / -name 'handover_addendum_A*' 2>/dev/null | head -10")
    print(out or "NOT FOUND")

    # Đọc nội dung nếu tìm được
    out2, _ = run(ssh, (
        "F=$(find / -name 'handover_addendum_A_2026-07-28.md' 2>/dev/null | head -1); "
        "if [ -n \"$F\" ]; then echo \"PATH: $F\"; cat \"$F\"; else echo 'FILE_NOT_FOUND'; fi"
    ), timeout=30)
    print(out2[:8000])

    # ── B. Cả hai path screener ─────────────────────────────────────────────
    banner("B1. Path BOT: ls + mtime daily_2026-07.csv")
    out, _ = run(ssh, f"ls -lh {BOT_DIR}/data/screener/ 2>&1 || echo 'DIR_MISSING'")
    print(out)
    out, _ = run(ssh, (
        f"stat {BOT_DIR}/data/screener/daily_2026-07.csv 2>&1 || echo 'FILE_MISSING'; "
        f"wc -l {BOT_DIR}/data/screener/daily_2026-07.csv 2>&1 || true"
    ))
    print(out)

    banner("B2. Path WHALE: ls + mtime daily_2026-07.csv")
    out, _ = run(ssh, f"ls -lh {WHALE_DIR}/data/screener/ 2>&1 || echo 'DIR_MISSING'")
    print(out)
    out, _ = run(ssh, (
        f"stat {WHALE_DIR}/data/screener/daily_2026-07.csv 2>&1 || echo 'FILE_MISSING'; "
        f"wc -l {WHALE_DIR}/data/screener/daily_2026-07.csv 2>&1 || true"
    ))
    print(out)

    banner("B3. Header (schema §9) — từ path tồn tại")
    for path in [f"{BOT_DIR}/data/screener/daily_2026-07.csv",
                 f"{WHALE_DIR}/data/screener/daily_2026-07.csv"]:
        out, _ = run(ssh, f"head -1 {path} 2>&1 | head -c 500")
        tag = "BOT" if "binance" in path else "WHALE"
        print(f"  [{tag}] {out.strip()[:300] or 'EMPTY/MISSING'}")

    banner("B4. TAGUSDT 2026-07-29 — từ cả hai path")
    for path in [f"{BOT_DIR}/data/screener/daily_2026-07.csv",
                 f"{WHALE_DIR}/data/screener/daily_2026-07.csv"]:
        tag = "BOT" if "binance" in path else "WHALE"
        out, _ = run(ssh, f"grep '^2026-07-29,TAGUSDT' {path} 2>&1 || echo 'ROW_MISSING'")
        print(f"  [{tag}] {out.strip()}")

    # ── C. Export dòng 29/07 ────────────────────────────────────────────────
    banner("C. Export freshwatch_daily_2026-07.csv — dòng 2026-07-29")
    for exp_dir in [f"{BOT_DIR}/data/export", f"{WHALE_DIR}/data/export"]:
        tag = "BOT" if "binance" in exp_dir else "WHALE"
        out, _ = run(ssh, (
            f"grep '2026-07-29' {exp_dir}/freshwatch_daily_2026-07.csv 2>&1 | head -3 || echo 'MISSING'"
        ))
        print(f"  [{tag}] {out.strip()[:400] or 'EMPTY'}")

    # Ngày cuối cùng có trong export
    banner("C2. Ngày cuối cùng trong export (max date)")
    for exp_dir in [f"{BOT_DIR}/data/export", f"{WHALE_DIR}/data/export"]:
        tag = "BOT" if "binance" in exp_dir else "WHALE"
        out, _ = run(ssh, (
            f"tail -5 {exp_dir}/freshwatch_daily_2026-07.csv 2>&1 | cut -d',' -f1,2 || echo 'MISSING'"
        ))
        print(f"  [{tag}] {out.strip()[:300]}")

    # ── D. R1 probe — ledger_daily.py join logic ────────────────────────────
    banner("D1. ledger_daily.py — grep symbol/join/TAG/no_export (first 40 hits)")
    out, _ = run(ssh, (
        f"grep -n 'symbol\\|join\\|TAG\\|no.*export\\|no.*data\\|merge\\|export_data\\|by_symbol' "
        f"{WHALE_DIR}/ledger_daily.py 2>&1 | head -40"
    ))
    print(out or "FILE_MISSING")

    banner("D2. ledger_daily.py — dòng xung quanh 'no export data' (±5 lines)")
    out, _ = run(ssh, (
        f"grep -n 'no export\\|no_export\\|export data\\|export_data' "
        f"{WHALE_DIR}/ledger_daily.py 2>&1 | head -20"
    ))
    print(out or "NOT FOUND")

    banner("D3. Export symbol format — first 3 rows repr")
    PROBE_D3 = (
        "python3 -c \""
        "import csv; "
        "rows=list(csv.DictReader(open('/root/Data_back_test/whale_data/data/export/freshwatch_daily_2026-07.csv','r',errors='replace'))); "
        "print('total rows:', len(rows)); "
        "[print('  sym=', repr(r.get('symbol','?')), 'date=', repr(r.get('date','?'))) for r in rows[:3]]; "
        "tags=[r for r in rows if 'TAG' in r.get('symbol','').upper()]; "
        "print('TAG* rows:', len(tags)); "
        "[print('  TAG sym=', repr(r.get('symbol','?')), 'date=', repr(r.get('date','?'))) for r in tags[:3]]"
        "\" 2>&1 || echo PROBE_ERROR"
    )
    out, _ = run(ssh, PROBE_D3, timeout=30)
    print(out[:2000])

    banner("D4. ledger_daily.py — dòng build export_data / by_symbol dict (full join key)")
    out, _ = run(ssh, (
        f"grep -n 'by_symbol\\|export_data\\|sym_upper\\|sym\\.upper\\|strip\\(\\.\\)\\|\\.upper' "
        f"{WHALE_DIR}/ledger_daily.py 2>&1 | head -30"
    ))
    print(out or "NOT FOUND")

    banner("D5. ledger_daily.log — key messages (no export / TAG / Zone A / loaded)")
    out, _ = run(ssh, (
        f"grep -E 'no export|loaded|TAG|Zone A|skipped|TAGUSDT|matched|28 rows' "
        f"{WHALE_DIR}/ledger_daily.log 2>&1 | tail -40 || echo 'LOG_MISSING'"
    ))
    print(out[:3000])

    # ── E. Tìm p0_5b ────────────────────────────────────────────────────────
    banner("E. Tìm p0_5b_report.md trên VPS")
    out, _ = run(ssh, "find / -name '*p0_5b*' -o -name '*p0.5*' -o -name '*cooldown*' 2>/dev/null | grep -v proc | head -20")
    print(out or "NOT FOUND")

    # ── F. Bot config — screener output path ────────────────────────────────
    banner("F. Bot config — screener_output_path / snapshot path (oi_scanner.py grep)")
    out, _ = run(ssh, (
        f"grep -n 'screener\\|snapshot.*path\\|output.*path\\|data/screener' "
        f"{BOT_DIR}/oi_scanner.py 2>&1 | head -30"
    ))
    print(out[:2000] or "NOT FOUND")

    # ── G. journalctl p1/screener 00:00–01:00 UTC hôm nay ──────────────────
    banner("G. journalctl oibot 00:00–01:00 UTC 2026-07-29")
    out, _ = run(ssh, (
        "journalctl -u oibot --since='2026-07-29 00:00' --until='2026-07-29 01:00' "
        "--no-pager 2>&1 | tail -60"
    ), timeout=30)
    print(out[:3000] or "NO OUTPUT")

    ssh.close()
    print(f"\n{SEP}\nMega probe done.\n{SEP}")


if __name__ == "__main__":
    main()
