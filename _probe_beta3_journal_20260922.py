"""β3 · KÍCH-vì-chân-HEDGE journal marker · giả lập U7 block.

1. Compose body 09-20
2. Force body length over 4096 (add padding)
3. Call send_hedge_v2(body, meta, dry_run=True)
4. Check U7 blocks · journal marker ghi label "KÍCH-vì-chân-HEDGE"
5. Cleanup journal
"""
import sys, os, json, shutil, tempfile
from pathlib import Path

_REPO = Path("/root/Data_back_test/whale_data") if os.name != "nt" \
        else Path(r"D:/Data back test/whale_data")
sys.path.insert(0, str(_REPO / "scripts"))

try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except AttributeError: pass  # L-66-OK

import hedge_v2 as hv

# Backup journal
HEDGE_JOURNAL = hv.HEDGE_JOURNAL
backup_p = None
if HEDGE_JOURNAL.exists():
    backup_p = Path(tempfile.mkdtemp(prefix="hedge_journal_backup_")) / HEDGE_JOURNAL.name
    shutil.copy2(HEDGE_JOURNAL, backup_p)

try:
    # Compose body
    body, meta = hv.compose_body("2026-09-20", report_only=True)
    print(f"baseline body tg_len={meta['tg_len']}")

    # Force overflow: pad body >4096 chars
    padded = body + "\n" + "PADDING " * 500  # ~4000 chars extra
    tg_len_padded = len(padded.encode("utf-16-le")) // 2
    print(f"padded body tg_len={tg_len_padded}")

    # Track journal size before
    n_before = 0
    if HEDGE_JOURNAL.exists():
        n_before = sum(1 for _ in HEDGE_JOURNAL.read_text(encoding="utf-8").splitlines())
    print(f"journal lines before: {n_before}")

    # Call send in dry mode
    result = hv.send_hedge_v2("2026-09-20", padded, {"tg_len": tg_len_padded}, dry_run=True)
    print()
    print(f"send result: {json.dumps(result, ensure_ascii=False, indent=2)}")

    # Check journal has new fail entry
    n_after = sum(1 for _ in HEDGE_JOURNAL.read_text(encoding="utf-8").splitlines())
    print(f"journal lines after: {n_after}")

    # Verify last entry has correct label
    lines = HEDGE_JOURNAL.read_text(encoding="utf-8").strip().split("\n")
    last_entry = json.loads(lines[-1])
    print(f"last journal entry: {json.dumps(last_entry, ensure_ascii=False, indent=2)}")

    checks = {
        "u7_blocked":          not result["u7_ok"],
        "u7_reason_LEN":       "LEN" in result["u7_reason"],
        "journal_line_added":  n_after > n_before,
        "journal_ok_False":    last_entry.get("ok") is False,
        "journal_label_correct": last_entry.get("leg_fail_label") == "KÍCH-vì-chân-HEDGE",
        "journal_fail_reason": "U7-BLOCKED" in last_entry.get("fail_reason", ""),
        "journal_renderer_watchlist": last_entry.get("renderer") == "watchlist",
        "journal_product_hedge_v2": last_entry.get("product") == "hedge_v2",
    }
    print()
    for k, v in checks.items():
        print(f"  {k}: {'PASS' if v else 'FAIL'}")
    all_ok = all(checks.values())
    print()
    print(f"═══ β3 · {'PASS' if all_ok else 'FAIL'} ═══")

finally:
    # Restore journal
    if backup_p and backup_p.exists():
        shutil.copy2(backup_p, HEDGE_JOURNAL)
        try: backup_p.parent.rmdir()
        except OSError: pass  # L-66-OK
    else:
        if HEDGE_JOURNAL.exists():
            HEDGE_JOURNAL.unlink()

sys.exit(0 if all_ok else 1)
