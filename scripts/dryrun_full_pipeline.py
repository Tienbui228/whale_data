"""dryrun_full_pipeline.py · X5/21-09 · CHẠY TRỌN PIPELINE KHÔ trước SEND.

Luật doctrine (§KỶ-LUẬT #12): mọi thay đổi chạm đường render phải qua
pipeline khô trọn vẹn (tới trước send) trên ≥5 đêm trước khi SCP.
Đo ngân sách một mình không đủ.

Usage:
  python3 scripts/dryrun_full_pipeline.py --targets 2026-09-16,2026-09-17,2026-09-18,2026-09-19,2026-09-20

Steps (dry · trừ send):
  1. rebuild-ledger        · step_rebuild_ledger(target)
  2. render-digest         · step_render_digest(target)
  3. label-lint            · step_label_lint(body)
  4. concat-seal           · step_concat_seal(body)
  5. pre-check body len    · <4096 chars
  6. pre-check HTML tags   · _tg_scan_bad_html

KHÔNG: compute_night_verdict (stamp epoch) · KHÔNG send_telegram · KHÔNG journal_append.
Đêm nào ≥1 bước fail → exit 1 với danh sách fail.
"""
from __future__ import annotations
import sys, os, argparse
from pathlib import Path

_REPO = Path("/root/Data_back_test/whale_data") if os.name != "nt" \
        else Path(r"D:/Data back test/whale_data")
sys.path.insert(0, str(_REPO / "scripts"))

os.environ.setdefault("DIGEST_V1_3", "1")
os.environ.setdefault("DIGEST_U0_BELL_BLOCK", "1")
os.environ.setdefault("DIGEST_B_TIER", "1")

import master_preview_send as mps


def _prefix_est(target: str) -> int:
    """Ước prefix cho label night_index/master-live (~30 chars)."""
    from datetime import datetime as _dt
    MASTER_LIVE_TARGET = "2026-09-15"
    if target >= MASTER_LIVE_TARGET:
        return len("[MASTER · live từ 2026-09-15]\n")
    return len("[MASTER-PREVIEW đêm 5/2]\n")


def dry_one(target: str) -> tuple[bool, list[tuple[str, bool, str]]]:
    """Chạy 6 bước dry cho target. Trả (all_ok, [(step, ok, msg), ...])."""
    results = []
    # STEP 1
    ok, msg = mps.step_rebuild_ledger(target)
    results.append(("rebuild-ledger", ok, str(msg)[:80]))
    if not ok:
        return (False, results)

    # STEP 2
    ok, res = mps.step_render_digest(target)
    results.append(("render-digest", ok, str(res)[:80]))
    if not ok:
        return (False, results)
    body = res

    # STEP 3
    ok, msg = mps.step_label_lint(body)
    results.append(("label-lint", ok, str(msg)[:100]))
    if not ok:
        return (False, results)

    # STEP 4
    ok, msg = mps.step_concat_seal(body)
    results.append(("concat-seal", ok, str(msg)[:80]))
    if not ok:
        return (False, results)

    # STEP 5 · pre-check body len (with prefix estimate)
    prefix_len = _prefix_est(target)
    full_len = len(body) + prefix_len
    ok = full_len <= 4096
    msg = f"body={len(body)} + prefix~{prefix_len} = {full_len} vs 4096"
    results.append(("pre-check-len", ok, msg))
    if not ok:
        return (False, results)

    # STEP 6 · HTML scan (U7 gate)
    prefix = "[DRY-RUN · target=" + target + "]\n"
    full_msg = prefix + body
    bad = mps._tg_scan_bad_html(full_msg)
    ok = bad is None
    msg = "OK" if ok else f"BAD-HTML tag={bad[0]} pos={bad[1]}"
    results.append(("pre-check-html", ok, msg))
    return (ok, results)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--targets", required=True,
                    help="comma-separated YYYY-MM-DD list")
    args = ap.parse_args()
    targets = [t.strip() for t in args.targets.split(",") if t.strip()]

    print(f"{'target':12s} | {'step':16s} | {'ok':>4s} | msg")
    print(f"{'-'*12} | {'-'*16} | {'-'*4} | {'-'*60}")

    fails = []
    for tgt in targets:
        all_ok, results = dry_one(tgt)
        for step, ok, msg in results:
            print(f"{tgt:12s} | {step:16s} | {'PASS' if ok else 'FAIL':>4s} | {msg}")
        if not all_ok:
            fails.append(tgt)
        print(f"{'-'*12}")

    print()
    if fails:
        print(f"═══ DRY-RUN · {len(fails)}/{len(targets)} FAIL: {', '.join(fails)} ═══")
        sys.exit(1)
    else:
        print(f"═══ DRY-RUN · {len(targets)}/{len(targets)} PASS · sẵn sàng SCP ═══")
        sys.exit(0)


if __name__ == "__main__":
    main()
