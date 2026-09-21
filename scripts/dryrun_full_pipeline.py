"""dryrun_full_pipeline.py · X5/21-09 · X6/21-09 · CHẠY TRỌN PIPELINE KHÔ trước SEND.

Luật doctrine (§KỶ-LUẬT #12): mọi thay đổi chạm đường render phải qua
pipeline khô trọn vẹn (tới trước send) trên ≥5 đêm trước khi SCP.
Đo ngân sách một mình không đủ.

Usage:
  python3 scripts/dryrun_full_pipeline.py --targets 2026-09-16,2026-09-17,2026-09-18,2026-09-19,2026-09-20

Steps (dry · trừ send):
  1. rebuild-ledger  (X6-1: backup+restore event_ledger để KHÔNG chạm prod)
  2. render-digest
  3. label-lint
  4. concat-seal
  5. pre-check body len (<4096)
  6. pre-check HTML tags
  + X6-2 · in pre-cap · post-cap · n_cut · vs 4096 mỗi đêm.

KHÔNG: compute_night_verdict (stamp epoch) · KHÔNG send_telegram · KHÔNG journal_append.
Đêm nào ≥1 bước fail → exit 1.
"""
from __future__ import annotations
import sys, os, argparse, shutil, tempfile
from pathlib import Path

_REPO = Path("/root/Data_back_test/whale_data") if os.name != "nt" \
        else Path(r"D:/Data back test/whale_data")
sys.path.insert(0, str(_REPO / "scripts"))

os.environ.setdefault("DIGEST_V1_3", "1")
os.environ.setdefault("DIGEST_U0_BELL_BLOCK", "1")
os.environ.setdefault("DIGEST_B_TIER", "1")

import master_preview_send as mps

LEDGER_DIR = _REPO / "data/logs/event_ledger"


def _backup_ledger_files(target: str) -> dict:
    """X6-1 · snapshot events_<T>.jsonl và stars_<T>.jsonl (nếu có) trước dry-rebuild."""
    saved = {}
    for name in (f"events_{target}.jsonl", f"stars_{target}.jsonl"):
        p = LEDGER_DIR / name
        if p.exists():
            tmp = Path(tempfile.mkdtemp(prefix="dryrun_led_")) / name
            shutil.copy2(p, tmp)
            saved[name] = tmp
        else:
            saved[name] = None   # didn't exist → will delete after dry
    return saved


def _restore_ledger_files(target: str, saved: dict) -> list:
    """X6-1 · phục hồi events/stars từ backup · trả list file đã restore/delete."""
    changed = []
    for name, backup in saved.items():
        p = LEDGER_DIR / name
        if backup is None:
            # Original didn't exist · dry rebuild may have created it · xoá
            if p.exists():
                p.unlink()
                changed.append(f"deleted {name}")
        else:
            # Restore original
            shutil.copy2(backup, p)
            changed.append(f"restored {name}")
            try: backup.parent.rmdir()
            except Exception: pass  # L-66-OK (tempdir cleanup benign)
    return changed


def _prefix_est(target: str) -> int:
    """Ước prefix cho label night_index/master-live (~30 chars)."""
    from datetime import datetime as _dt
    MASTER_LIVE_TARGET = "2026-09-15"
    if target >= MASTER_LIVE_TARGET:
        return len("[MASTER · live từ 2026-09-15]\n")
    return len("[MASTER-PREVIEW đêm 5/2]\n")


def dry_one(target: str) -> tuple[bool, list[tuple[str, bool, str]], dict]:
    """Chạy 6 bước dry cho target · X6-1 backup+restore ledger · X6-2 đo pre/post-cap.
    Trả (all_ok, [(step, ok, msg), ...], {pre_cap, post_cap, n_cut, cap_ganh})."""
    results = []
    metrics = {"pre_cap": None, "post_cap": None, "n_cut": None, "cap_ganh": False}

    # X6-1 · backup event_ledger trước rebuild
    saved = _backup_ledger_files(target)
    try:
        # STEP 1
        ok, msg = mps.step_rebuild_ledger(target)
        results.append(("rebuild-ledger", ok, str(msg)[:80]))
        if not ok:
            return (False, results, metrics)

        # STEP 2
        ok, res = mps.step_render_digest(target)
        results.append(("render-digest", ok, str(res)[:80]))
        if not ok:
            return (False, results, metrics)
        body = res
        metrics["post_cap"] = len(body)   # body đã qua cap trong build_v2_digest

        # STEP 3
        ok, msg = mps.step_label_lint(body)
        results.append(("label-lint", ok, str(msg)[:100]))
        if not ok:
            return (False, results, metrics)

        # STEP 4
        ok, msg = mps.step_concat_seal(body)
        results.append(("concat-seal", ok, str(msg)[:80]))
        if not ok:
            return (False, results, metrics)

        # STEP 5 · pre-check body len (with prefix estimate)
        # AH4/22-09 · đo bằng tg_len (UTF-16 code unit sau strip HTML)
        try:
            from lib.tg_len import tg_len as _tg_len_dry
        except ImportError:
            _tg_len_dry = len
        prefix_len = _prefix_est(target)
        body_u = _tg_len_dry(body)
        full_len = body_u + prefix_len
        ok = full_len <= 4096
        msg = f"body={body_u} + prefix~{prefix_len} = {full_len} utf16-u vs 4096"
        results.append(("pre-check-len", ok, msg))
        if not ok:
            return (False, results, metrics)

        # STEP 6 · HTML scan (U7 gate)
        prefix = "[DRY-RUN · target=" + target + "]\n"
        full_msg = prefix + body
        bad = mps._tg_scan_bad_html(full_msg)
        ok = bad is None
        msg = "OK" if ok else f"BAD-HTML tag={bad[0]} pos={bad[1]}"
        results.append(("pre-check-html", ok, msg))

        # X6-2 · đo pre-cap SAU khi 6 steps xong (backup master_concat + master_body
        # trước monkey-patch · restore sau · KHÔNG break seal check ở lần dry kế tiếp).
        _ART_DIR = _REPO / "data/artifacts"
        _concat_p = _ART_DIR / f"master_concat_{target}.txt"
        _body_p = _ART_DIR / f"master_body_{target}.txt"
        _bak_concat = _concat_p.read_bytes() if _concat_p.exists() else None
        _bak_body = _body_p.read_bytes() if _body_p.exists() else None
        try:
            import digest_summary_v2 as _dsv
            _orig_cap = _dsv._v1_3_apply_3tier_cap
            try:
                _dsv._v1_3_apply_3tier_cap = lambda b, budget=3680: b
                body_nocap = _dsv.build_v2_digest(target)
                metrics["pre_cap"] = len(body_nocap)
            except Exception:
                metrics["pre_cap"] = None
            finally:
                _dsv._v1_3_apply_3tier_cap = _orig_cap
        finally:
            # Restore artifacts (build_v2_digest ghi đè khi monkey-patch)
            if _bak_concat is not None: _concat_p.write_bytes(_bak_concat)
            if _bak_body is not None: _body_p.write_bytes(_bak_body)
        if metrics["pre_cap"] is not None and metrics["post_cap"] is not None:
            metrics["n_cut"] = metrics["pre_cap"] - metrics["post_cap"]
            metrics["cap_ganh"] = metrics["pre_cap"] > 4096

        return (ok, results, metrics)
    finally:
        # X6-1 · restore event_ledger về nguyên trạng
        _restore_ledger_files(target, saved)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--targets", required=True,
                    help="comma-separated YYYY-MM-DD list")
    args = ap.parse_args()
    targets = [t.strip() for t in args.targets.split(",") if t.strip()]

    print(f"{'target':12s} | {'step':16s} | {'ok':>4s} | msg")
    print(f"{'-'*12} | {'-'*16} | {'-'*4} | {'-'*60}")

    fails = []
    all_metrics = []
    for tgt in targets:
        all_ok, results, metrics = dry_one(tgt)
        for step, ok, msg in results:
            print(f"{tgt:12s} | {step:16s} | {'PASS' if ok else 'FAIL':>4s} | {msg}")
        if not all_ok:
            fails.append(tgt)
        all_metrics.append((tgt, metrics))
        print(f"{'-'*12}")

    # X6-2 · bảng ngân sách
    print()
    print(f"{'target':12s} | {'pre-cap':>8s} | {'post-cap':>8s} | {'n_cut':>5s} | {'note':<12s}")
    print(f"{'-'*12} | {'-'*8} | {'-'*8} | {'-'*5} | {'-'*12}")
    for tgt, m in all_metrics:
        pre = f"{m['pre_cap']}" if m['pre_cap'] is not None else "?"
        post = f"{m['post_cap']}" if m['post_cap'] is not None else "?"
        cut = f"{m['n_cut']}" if m['n_cut'] is not None else "?"
        note = "[CAP-GÁNH]" if m['cap_ganh'] else ""
        print(f"{tgt:12s} | {pre:>8s} | {post:>8s} | {cut:>5s} | {note:<12s}")

    print()
    if fails:
        print(f"═══ DRY-RUN · {len(fails)}/{len(targets)} FAIL: {', '.join(fails)} ═══")
        sys.exit(1)
    else:
        print(f"═══ DRY-RUN · {len(targets)}/{len(targets)} PASS · sẵn sàng SCP ═══")
        sys.exit(0)


if __name__ == "__main__":
    main()
