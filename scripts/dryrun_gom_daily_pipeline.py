"""dryrun_gom_daily_pipeline.py · AG1/21-09 · pipeline khô chân gom_daily.

Steps (dry · trừ send + bell_journal):
  1. render-gomE     · gom_e.py --daily --date <T> --fw-filter · capture stdout
  2. len-before-slice · in raw len
  3. slice-4000       · gome_msg = raw[:4000]
  4. len-after-slice  · in sliced len
  5. html-scan        · U7 gate check (dry · không chặn)
  6. tail-truncated?  · check ranh chữ cuối cùng của Bảng B (còn nguyên?)

KHÔNG: gọi tg_send · KHÔNG log_bell · KHÔNG dump_as_sent · KHÔNG chạm bell_journal.

Usage:
  python3 scripts/dryrun_gom_daily_pipeline.py --targets 2026-09-14,2026-09-15,...

Doctrine §KỶ-LUẬT #12: mọi thay đổi chạm gom_daily (render + slice/gate)
PHẢI qua script này ≥5 đêm xanh trước SCP.
"""
from __future__ import annotations
import sys, os, subprocess, argparse, re
from pathlib import Path

_REPO = Path("/root/Data_back_test/whale_data") if os.name != "nt" \
        else Path(r"D:/Data back test/whale_data")
sys.path.insert(0, str(_REPO / "scripts"))

from master_preview_send import _tg_scan_bad_html   # U7 gate reuse

STORE = _REPO / "data" / "export"
FW_SYM_PATH = _REPO / "data" / "config" / "freshwatch_symbols.txt"
GOM_E_STATE = _REPO / "data" / "gom_e_state.json"
SLICE_CAP = 4000
TG_LIMIT = 4096


def _backup_gom_e_state():
    """AG1/AG2 · backup gom_e state trước dry-run · KHÔNG chạm cooldown/registry prod."""
    import tempfile, shutil
    if GOM_E_STATE.exists():
        tmp = Path(tempfile.mkdtemp(prefix="dryrun_gome_")) / GOM_E_STATE.name
        shutil.copy2(GOM_E_STATE, tmp)
        return tmp
    return None


def _restore_gom_e_state(saved):
    """Restore từ backup hoặc unlink nếu original không có."""
    import shutil
    if saved is None:
        if GOM_E_STATE.exists():
            GOM_E_STATE.unlink()
    else:
        shutil.copy2(saved, GOM_E_STATE)
        try: saved.parent.rmdir()
        except Exception: pass  # L-66-OK (tempdir cleanup benign)


def dry_one(target: str) -> dict:
    """Chạy 6 bước dry cho target. Trả dict metrics."""
    gom_e_script = _REPO / "scripts/gom_e.py"
    cmd = [
        sys.executable, str(gom_e_script),
        "--daily", "--store", str(STORE), "--date", target,
        "--fw-filter", str(FW_SYM_PATH),
    ]
    try:
        r = subprocess.run(cmd, capture_output=True, encoding="utf-8",
                           errors="replace", timeout=180)
        raw = r.stdout or ""
        stderr = r.stderr or ""
        rc = r.returncode
    except subprocess.TimeoutExpired:
        return {"target": target, "step": "render-gomE", "ok": False,
                "err": "TIMEOUT 180s", "raw_len": 0, "sliced_len": 0}

    metrics = {
        "target": target,
        "gomE_rc": rc,
        "raw_len": len(raw),
        "sliced_len": 0,
        "html_ok": None,
        "tail_last_60": "",
        "sliced_tail_cut_mid_word": None,
        "bang_b_in_sliced": None,
        "stderr_head": stderr[:120] if stderr else "",
    }
    if rc != 0:
        return metrics

    # AG2/21-09 · smart-truncate (khớp run_gom_daily wire)
    if len(raw) > SLICE_CAP:
        _tail = raw[SLICE_CAP:]
        _remaining_a = len([l for l in _tail.split("\n") if re.match(r"^  [A-Z0-9]+USDT?\s+\|", l)])
        _tail_note = f"\n(+{_remaining_a} token Bảng A · đủ ở audit)"
        _max_body = SLICE_CAP - len(_tail_note)
        _cut_at = raw.rfind("\n", 0, _max_body)
        if _cut_at < 0: _cut_at = _max_body
        gome_msg = raw[:_cut_at] + _tail_note
    else:
        gome_msg = raw
    metrics["sliced_len"] = len(gome_msg)

    # HTML scan · dry · không chặn, chỉ báo
    bad = _tg_scan_bad_html(gome_msg)
    metrics["html_ok"] = (bad is None)
    if bad is not None:
        metrics["html_bad"] = f"{bad[0]} @ pos {bad[1]}"

    # Tail check: last 60 chars của sliced
    metrics["tail_last_60"] = gome_msg[-60:].replace("\n", "⏎")

    # Cắt giữa chữ? Nếu sliced_len == SLICE_CAP AND raw_len > SLICE_CAP AND ký tự cuối alnum
    if len(gome_msg) == SLICE_CAP and len(raw) > SLICE_CAP:
        last_char = gome_msg[-1]
        next_char = raw[SLICE_CAP] if len(raw) > SLICE_CAP else ""
        cut_mid = (last_char.isalnum() and next_char.isalnum())
        metrics["sliced_tail_cut_mid_word"] = cut_mid

    # Bảng B có nguyên vẹn trong sliced? "— BẢNG B" marker + có ≥1 dòng alert sau
    m = re.search(r"— BẢNG B MODE-SWITCH ALERTS \d{4}-\d{2}-\d{2} \((\d+) fires\) —", gome_msg)
    if m:
        n_fires = int(m.group(1))
        # Đếm số dòng alert đã xuất hiện: dòng bắt đầu bằng 2 space + sym
        b_start = gome_msg.find(m.group(0)) + len(m.group(0))
        b_body = gome_msg[b_start:]
        # Alert lines format: "  SYM ..." (2 spaces + symbol)
        alerts_in = len([ln for ln in b_body.split("\n") if re.match(r"^  [A-Z0-9]+", ln)])
        metrics["bang_b_in_sliced"] = f"{alerts_in}/{n_fires}"
    else:
        metrics["bang_b_in_sliced"] = "0/? (Bảng B header MISSING trong sliced)"

    return metrics


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--targets", required=True, help="comma-separated YYYY-MM-DD list")
    args = ap.parse_args()
    targets = [t.strip() for t in args.targets.split(",") if t.strip()]

    print(f"{'target':12s} | {'rc':>3s} | {'raw':>5s} | {'sliced':>6s} | {'html':>4s} | {'tail-cut':>8s} | {'BảngB in':>10s}")
    print(f"{'-'*12} | {'-'*3} | {'-'*5} | {'-'*6} | {'-'*4} | {'-'*8} | {'-'*10}")

    # AG1/AG2 · backup gom_e state 1 lần trước tất cả · restore sau
    _saved = _backup_gom_e_state()
    all_metrics = []
    try:
        for tgt in targets:
            m = dry_one(tgt)
            all_metrics.append(m)
    finally:
        _restore_gom_e_state(_saved)

    for m in all_metrics:
        tgt = m["target"]
        cut_str = "YES" if m.get("sliced_tail_cut_mid_word") else "no"
        html_str = "OK" if m["html_ok"] else "BAD"
        print(f"{tgt:12s} | {m['gomE_rc']:>3d} | {m['raw_len']:>5d} | {m['sliced_len']:>6d} | {html_str:>4s} | {cut_str:>8s} | {m.get('bang_b_in_sliced', '?'):>10s}")

    print()
    print(f"{'target':12s} | tail_last_60")
    print(f"{'-'*12} | {'-'*80}")
    for m in all_metrics:
        print(f"{m['target']:12s} | {m['tail_last_60'][:80]}")

    # Kết luận
    n = len(all_metrics)
    n_ok_render = sum(1 for m in all_metrics if m["gomE_rc"] == 0)
    n_html_ok = sum(1 for m in all_metrics if m["html_ok"])
    n_bang_b_intact = sum(1 for m in all_metrics
                          if m.get("bang_b_in_sliced", "").split("/")[0].isdigit()
                          and m.get("bang_b_in_sliced", "").split("/")[0] != "0")
    n_cut_mid = sum(1 for m in all_metrics if m.get("sliced_tail_cut_mid_word"))

    print()
    print(f"═══ TỔNG {n} đêm · render OK: {n_ok_render}/{n} · html OK: {n_html_ok}/{n}")
    print(f"═══ Bảng B trong sliced: {n_bang_b_intact}/{n} · tail cut giữa chữ: {n_cut_mid}/{n}")
    sys.exit(0 if (n_ok_render == n and n_html_ok == n) else 1)


if __name__ == "__main__":
    main()
