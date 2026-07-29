#!/usr/bin/env python3
"""T2: Fix R1 join bug trong ledger_daily.py.
  - Download ledger_daily.py từ VPS
  - Patch line 624: export_data.get(sym_upper,[]) → normalize USDT suffix
  - Upload lại
  - Chạy dry-run để verify 0 no_data
  - Chạy live để cập nhật ledger_v2.xlsx
  - In before/after 3 dòng Zone A
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

import paramiko, pathlib, tempfile, os

KEY_FILE = r"D:\Check onchain fresh wallets\sync_key_ed25519"
HOST = "5.223.67.21"
USER = "root"
WHALE_DIR = "/root/Data_back_test/whale_data"
REMOTE_SCRIPT = f"{WHALE_DIR}/ledger_daily.py"
SEP = "=" * 70

# ── Patch spec ───────────────────────────────────────────────────────────────
OLD_LINE_A = "        sym_upper = symbol.upper()"
OLD_LINE_B = "        sym_rows = export_data.get(sym_upper, [])"

NEW_LINES = """\
        sym_upper = symbol.upper()
        # R1 fix: ledger stores 'TAG', export stores 'TAGUSDT' — normalize one-way
        _exp_key = sym_upper if sym_upper in export_data else (sym_upper + "USDT")
        sym_rows = export_data.get(_exp_key, [])"""

# ── Also check for any other export_data.get(sym_upper ...) calls outside Zone A
GREP_CHECK = "        sym_rows = export_data.get(sym_upper,"


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

    # ── Step 0: grep to verify current state ─────────────────────────────────
    print(f"{SEP}\nStep 0: Verify current line numbers\n{SEP}")
    out, _ = run(ssh, f"grep -n 'sym_upper\\|export_data.get\\|_exp_key' {REMOTE_SCRIPT} 2>&1 | head -20")
    print(out)

    # ── Step 1: Download current ledger_daily.py ──────────────────────────────
    print(f"{SEP}\nStep 1: Download ledger_daily.py\n{SEP}")
    local_tmp = pathlib.Path(tempfile.mktemp(suffix="_ledger_daily.py"))
    sftp.get(REMOTE_SCRIPT, str(local_tmp))
    content = local_tmp.read_text(encoding="utf-8", errors="replace")
    lines = content.splitlines(keepends=True)
    print(f"Downloaded: {len(lines)} lines")

    # ── Step 2: Locate and patch ─────────────────────────────────────────────
    print(f"{SEP}\nStep 2: Apply patch\n{SEP}")
    patch_done = False
    new_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if (OLD_LINE_A in line and
                i + 1 < len(lines) and
                OLD_LINE_B in lines[i + 1]):
            # Check if already patched
            if "_exp_key" in line or (i + 2 < len(lines) and "_exp_key" in lines[i + 2]):
                print("ALREADY PATCHED — skipping")
                new_lines.extend(lines[i:])
                break
            # Print before context
            print(f"  BEFORE line {i+1}: {line.rstrip()}")
            print(f"  BEFORE line {i+2}: {lines[i+1].rstrip()}")
            # Replace both lines with the new block
            new_lines.append(NEW_LINES + "\n")
            i += 2  # skip both old lines
            patch_done = True
            print(f"  AFTER (patch applied):\n{NEW_LINES}")
        else:
            new_lines.append(line)
            i += 1

    if not patch_done:
        print("WARNING: patch target not found! Checking file...")
        # Show lines around export_data.get
        for j, l in enumerate(lines):
            if "export_data.get" in l or "sym_upper" in l:
                print(f"  Line {j+1}: {l.rstrip()}")
        print("ABORTING — patch not applied")
        ssh.close()
        local_tmp.unlink(missing_ok=True)
        return

    # ── Step 3: Also grep for any OTHER export_data.get(sym_upper calls ──────
    print(f"\n{SEP}\nStep 3: Check for other export_data.get calls\n{SEP}")
    other = [(j+1, l.rstrip()) for j, l in enumerate(new_lines) if GREP_CHECK in l]
    if other:
        print(f"Found {len(other)} other occurrences (check if also need fix):")
        for lnum, ltxt in other:
            print(f"  Line {lnum}: {ltxt}")
    else:
        print("No other export_data.get(sym_upper,...) calls found — only one fix needed.")

    # ── Step 4: Write patched content ────────────────────────────────────────
    patched = "".join(new_lines)
    backup_remote = REMOTE_SCRIPT + ".bak_before_r1fix"
    local_patched = local_tmp.with_suffix(".patched.py")
    local_patched.write_text(patched, encoding="utf-8")
    print(f"\n{SEP}\nStep 4: Upload patched version\n{SEP}")

    # Backup original on VPS
    out, _ = run(ssh, f"cp {REMOTE_SCRIPT} {backup_remote} && echo 'backup ok' || echo 'backup FAIL'")
    print(f"Backup: {out.strip()}")

    # Upload patched
    sftp.put(str(local_patched), REMOTE_SCRIPT)
    print("Uploaded patched ledger_daily.py")

    # Verify patch is in file
    out, _ = run(ssh, f"grep -n '_exp_key\\|sym_upper\\|# R1 fix' {REMOTE_SCRIPT} | head -10")
    print("Verify patch in remote file:")
    print(out)

    # ── Step 5: Dry-run ───────────────────────────────────────────────────────
    print(f"{SEP}\nStep 5: Dry-run\n{SEP}")
    VENV_PY = f"{WHALE_DIR}/.venv/bin/python3"
    out, err = run(ssh, f"cd {WHALE_DIR} && {VENV_PY} ledger_daily.py --dry-run 2>&1 | tail -40", timeout=90)
    print(out)
    if err.strip():
        print("STDERR:", err[:500])

    # ── Step 6: Live run ─────────────────────────────────────────────────────
    print(f"{SEP}\nStep 6: Live run (Zone A fix today)\n{SEP}")
    out, err = run(ssh, f"cd {WHALE_DIR} && {VENV_PY} ledger_daily.py --live 2>&1 | tail -50", timeout=120)
    print(out)
    if err.strip():
        print("STDERR:", err[:1000])

    # ── Step 7: Verify ledger_daily.log last 20 lines ─────────────────────────
    print(f"{SEP}\nStep 7: ledger_daily.log last 20 lines\n{SEP}")
    out, _ = run(ssh, f"tail -20 {WHALE_DIR}/ledger_daily.log 2>&1")
    print(out)

    # ── Step 8: Before/after 3 Zone A rows for TAG, BANK, TUT ────────────────
    print(f"{SEP}\nStep 8: 3 sample Zone A rows from CAMPAIGNS (TAG, BANK, CLO)\n{SEP}")
    PROBE_S8 = r"""
import openpyxl
from pathlib import Path
wb = openpyxl.load_workbook('/root/Data_back_test/whale_data/data/ledger/ledger_v2.xlsx', read_only=True, data_only=True)
ws = wb['CAMPAIGNS']
header = [str(c) if c is not None else '' for c in next(ws.iter_rows(max_row=1, values_only=True))]
sym_idx = header.index('symbol') if 'symbol' in header else -1
print('CAMPAIGNS header:', header[:15])
for row in ws.iter_rows(min_row=2, max_row=35, values_only=True):
    sym = str(row[sym_idx]).strip() if sym_idx >= 0 and row else ''
    if sym in ('TAG', 'BANK', 'CLO'):
        print(f'\n  {sym}:', {header[i]: row[i] for i in range(min(len(header), len(row))) if row[i] is not None and header[i] != ''})
"""
    out, err = run(ssh, f"cd {WHALE_DIR} && {VENV_PY} -c {repr(PROBE_S8)}", timeout=30)
    print(out[:3000])
    if err.strip():
        print("STDERR:", err[:300])

    sftp.close()
    ssh.close()
    local_tmp.unlink(missing_ok=True)
    local_patched.unlink(missing_ok=True)
    print(f"\n{SEP}\nFix R1 done.\n{SEP}")


if __name__ == "__main__":
    main()
