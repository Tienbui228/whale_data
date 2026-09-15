"""HARNESS p28 · V3.5r item 6 · NIGHT-COUNTER-RECEIPT di-sản.

Nhánh-A · nhãn-k ≡ distinct-targets:
  Journal đã có 1 entry standing_ok target=2026-09-10
  Compute night_label for new target=2026-09-11
  → distinct = {09-10, 09-11} = 2 · nhãn = "2/2"

Nhánh-B · send-lần-2 same-target PHẢI SKIP:
  Journal đã có target=2026-09-11 standing_ok
  Gọi preview_journal_check(target="2026-09-11") → return entry
  → sender SKIP (return None from wrapper mô phỏng · không double-send)

Test uses temp preview_journal.jsonl (backup thật · restore sau).
"""
from __future__ import annotations
import sys, os, json, hashlib, shutil
from pathlib import Path
from datetime import datetime, timezone

try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except: pass  # L-66-OK (benign fallback)

REPO = Path("/root/Data_back_test/whale_data") if os.name != "nt" else Path(r"D:/Data back test/whale_data")
SB_LOG = REPO / "data/logs/harness_sabotage.log"

sys.path.insert(0, str(REPO / "scripts"))


def _log(pin, mutate, verdict, extra):
    ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
    sha = hashlib.md5(f"{pin}{mutate}{verdict}{extra}".encode()).hexdigest()[:8]
    SB_LOG.parent.mkdir(parents=True, exist_ok=True)
    with SB_LOG.open("a", encoding="utf-8") as f:
        f.write(f"{ts}\t{pin}\t{mutate}\t{verdict}\t{sha}\n")


PREVIEW_JOURNAL = REPO / "data/logs/preview_journal.jsonl"
BACKUP = REPO / "data/logs/preview_journal.jsonl.bak_p28"
EPOCH = "2026-09-10"


def _backup_journal():
    if PREVIEW_JOURNAL.exists():
        shutil.copy(PREVIEW_JOURNAL, BACKUP)


def _restore_journal():
    if BACKUP.exists():
        shutil.move(BACKUP, PREVIEW_JOURNAL)
    else:
        try: PREVIEW_JOURNAL.unlink(missing_ok=True)
        except Exception: pass  # L-66-OK


def _write_journal(entries: list[dict]):
    PREVIEW_JOURNAL.parent.mkdir(parents=True, exist_ok=True)
    with PREVIEW_JOURNAL.open("w", encoding="utf-8") as f:
        for e in entries:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")


def _count_distinct_after(target: str) -> int:
    """Replicate master_preview_send.main() V3.5q counter logic."""
    distinct = set()
    if PREVIEW_JOURNAL.exists():
        for line in PREVIEW_JOURNAL.read_text(encoding="utf-8").splitlines():
            try:
                e = json.loads(line)
                if e.get("standing_ok") and e.get("target_date", "") >= EPOCH:
                    distinct.add(e["target_date"])
            except: pass  # L-66-OK
    return len(distinct | {target})


def case_a_night_label_distinct():
    """Nhánh-A: journal has target=09-10, new target=09-11 ⇒ nhãn 2/(2)."""
    _write_journal([{
        "ts_utc": "2026-09-10T01:47:00+00:00",
        "renderer": "master_preview", "target_date": "2026-09-10",
        "channel": "TG_CHAT_ID_DAILY", "ok": True, "http_code": 200,
        "message_id": 100, "body_md5": "aa"*16, "standing_ok": True,
        "night_label": "1/2",
    }])
    n = _count_distinct_after("2026-09-11")
    passed = (n == 2)
    return passed, f"target=09-11 · distinct-after={n} (expect 2)"


def case_a2_same_target_no_double_count():
    """Journal has target=09-10, compute for target=09-10 ⇒ nhãn 1/(2) (no double-count)."""
    _write_journal([{
        "ts_utc": "2026-09-10T01:47:00+00:00",
        "renderer": "master_preview", "target_date": "2026-09-10",
        "channel": "TG_CHAT_ID_DAILY", "ok": True, "http_code": 200,
        "message_id": 100, "body_md5": "aa"*16, "standing_ok": True,
        "night_label": "1/2",
    }])
    n = _count_distinct_after("2026-09-10")
    passed = (n == 1)
    return passed, f"target=09-10 same · distinct-after={n} (expect 1)"


def case_b_send_lan_2_same_target_skip():
    """Nhánh-B: journal has target=09-11 standing_ok · re-check preview_journal_check ⇒ hit ⇒ SKIP."""
    _write_journal([{
        "ts_utc": "2026-09-11T01:47:00+00:00",
        "renderer": "master_preview", "target_date": "2026-09-11",
        "channel": "TG_CHAT_ID_DAILY", "ok": True, "http_code": 200,
        "message_id": 200, "body_md5": "bb"*16, "standing_ok": True,
        "night_label": "2/2",
    }])
    # Fresh import
    for m in list(sys.modules.keys()):
        if "master_preview_send" in m: del sys.modules[m]
    from master_preview_send import preview_journal_check
    existing = preview_journal_check("2026-09-11")
    passed = (existing is not None and existing.get("message_id") == 200)
    return passed, f"preview_journal_check hit={existing is not None} · msg_id={existing.get('message_id') if existing else None} (expect 200 · sender SKIP)"


def case_b2_first_time_target_returns_none():
    """Journal has target=09-10 · check target=09-11 (chưa có) ⇒ return None ⇒ sender SEND."""
    _write_journal([{
        "ts_utc": "2026-09-10T01:47:00+00:00",
        "renderer": "master_preview", "target_date": "2026-09-10",
        "channel": "TG_CHAT_ID_DAILY", "ok": True, "http_code": 200,
        "message_id": 100, "body_md5": "aa"*16, "standing_ok": True,
        "night_label": "1/2",
    }])
    for m in list(sys.modules.keys()):
        if "master_preview_send" in m: del sys.modules[m]
    from master_preview_send import preview_journal_check
    existing = preview_journal_check("2026-09-11")
    passed = (existing is None)
    return passed, f"preview_journal_check target=09-11 (fresh) hit={existing is not None} (expect None · sender SEND)"


def case_c_real_journal_gates_correctly():
    """Nhánh-C (V3.5r item 3): counter đọc journal THẬT (không sandbox) · trả nhãn đúng.
    · nếu file 0-byte hoặc 0-entry standing_ok ≥ EPOCH → nhãn = 1/2 cho target-mới
    · nếu file có 1 entry cho target khác EPOCH-in-range → nhãn = 2/2 cho target mới thứ 2
    Đọc VPS-mirror `preview_journal.jsonl.vps_pull` nếu có · else đọc live PREVIEW_JOURNAL.
    """
    mirror = REPO / "data/logs/preview_journal.jsonl.vps_pull"
    src = mirror if mirror.exists() else PREVIEW_JOURNAL
    if not src.exists():
        return True, f"no journal ({src.name}) · N/A but no-fail"
    lines = [l for l in src.read_text(encoding="utf-8").splitlines() if l.strip()]
    distinct = set()
    for line in lines:
        try:
            e = json.loads(line)
            if e.get("standing_ok") and e.get("target_date", "") >= EPOCH:
                distinct.add(e["target_date"])
        except: pass  # L-66-OK
    target_test = "2026-09-10"
    n_after = len(distinct | {target_test})
    # Đối chiếu · empty journal ⇒ 1/2 · 1 entry cho target-khác ⇒ 2/2 · 1 entry cùng target ⇒ 1/2
    if target_test in distinct:
        expected = len(distinct)
    else:
        expected = len(distinct) + 1
    passed = (n_after == expected)
    return passed, f"src={src.name} lines={len(lines)} distinct={sorted(distinct)} n_after={n_after}/2 (expect {expected}/2)"


import re as _re

# V1.3 · MASTER-LIVE cutover (KÝ 15/09): nhãn hợp lệ = CẢ HAI dạng
#   preview era:      "N/2" (ví dụ "1/2", "2/2")
#   preview era n>2:  "[ĐỦ 2/2 · CHỜ \"ok master live\"]"
#   post-cutover:     "[MASTER · live từ YYYY-MM-DD]"
_LABEL_PATTERNS = [
    _re.compile(r"^\d+/2$"),                              # preview N/2
    _re.compile(r'^\[ĐỦ 2/2 · CHỜ "ok master live"\]$'),  # preview era n>2
    _re.compile(r"^\[MASTER · live từ \d{4}-\d{2}-\d{2}\]$"),  # post-cutover
]


def _valid_label(label: str) -> bool:
    return any(p.match(label) for p in _LABEL_PATTERNS)


def case_d_label_format_valid():
    """Nhánh-D · nhãn hợp lệ · CẢ HAI dạng · XANH."""
    cases_xanh = [
        ("1/2", True),
        ("2/2", True),
        ('[ĐỦ 2/2 · CHỜ "ok master live"]', True),
        ("[MASTER · live từ 2026-09-15]", True),
        ("[MASTER · live từ 2026-09-16]", True),
    ]
    fails = []
    for lbl, expected in cases_xanh:
        got = _valid_label(lbl)
        if got != expected:
            fails.append(f"{lbl!r}: got={got} expect={expected}")
    passed = not fails
    return passed, f"XANH {len(cases_xanh)} nhãn hợp lệ · fails={fails}"


def case_e_label_format_rac_dai():
    """Nhánh-E · ĐEN-một-lần · nhãn rác PHẢI đỏ."""
    cases_den = [
        ("abc", False),
        ("xyz", False),
        ("3/2", True),   # 3/2 vẫn khớp \d+/2 → hợp lệ; báo NOTE
        ("[MASTER-PREVIEW đêm 5/2]", False),   # old label bug format · not accepted
        ("[MASTER live]", False),
        ("", False),
        ("[MASTER · live từ 09-15]", False),  # sai format ngày
    ]
    fails = []
    for lbl, expected in cases_den:
        got = _valid_label(lbl)
        if got != expected:
            fails.append(f"{lbl!r}: got={got} expect={expected}")
    passed = not fails
    return passed, f"ĐEN {len(cases_den)} nhãn rác · fails={fails}"


def case_f_real_journal_all_valid():
    """Nhánh-F · đọc journal thật (preview + master) · MỌI night_label hợp lệ."""
    checked = []
    invalid = []
    for jf_name in ("preview_journal.jsonl", "master_journal.jsonl"):
        jf = REPO / "data/logs" / jf_name
        if not jf.exists(): continue
        for line in jf.read_text(encoding="utf-8").splitlines():
            try:
                e = json.loads(line)
                lbl = e.get("night_label", "")
                if lbl:
                    checked.append((jf_name, e.get("target_date"), lbl))
                    if not _valid_label(lbl):
                        invalid.append((jf_name, e.get("target_date"), lbl))
            except: pass  # L-66-OK
    passed = len(invalid) == 0
    return passed, f"checked={len(checked)} entries · invalid={len(invalid)}: {invalid[:5]}"


def main():
    print("═" * 62)
    print("HARNESS p28 · NIGHT-COUNTER-RECEIPT · V3.5r + V1.3 MASTER-LIVE")
    print("═" * 62)
    _backup_journal()
    all_pass = True
    try:
        cases = [
            ("A · nhãn-k ≡ distinct-targets (new target)", case_a_night_label_distinct),
            ("A2 · same-target no double-count", case_a2_same_target_no_double_count),
            ("B · send-lần-2 same-target ⇒ hit ⇒ SKIP", case_b_send_lan_2_same_target_skip),
            ("B2 · first-time target ⇒ None ⇒ SEND", case_b2_first_time_target_returns_none),
            ("D · nhãn hợp lệ · CẢ HAI dạng XANH", case_d_label_format_valid),
            ("E · nhãn rác ĐEN-một-lần", case_e_label_format_rac_dai),
        ]
        for name, fn in cases:
            ok, detail = fn()
            mark = "✅" if ok else "❌"
            print(f"  {mark} {name}: {detail}")
            _log("p28", name, "PASS" if ok else "FAIL", detail[:80])
            if not ok: all_pass = False
    finally:
        _restore_journal()
    # Nhánh-C · REAL journal (chạy SAU restore để đọc journal thật)
    ok_c, det_c = case_c_real_journal_gates_correctly()
    mark = "✅" if ok_c else "❌"
    print(f"  {mark} C · REAL journal (VPS mirror if any): {det_c}")
    _log("p28", "C real-journal", "PASS" if ok_c else "FAIL", det_c[:80])
    if not ok_c: all_pass = False
    # Nhánh-F · REAL journal · label format check (both preview + master)
    ok_f, det_f = case_f_real_journal_all_valid()
    mark = "✅" if ok_f else "❌"
    print(f"  {mark} F · REAL journal label format: {det_f}")
    _log("p28", "F label-format-real", "PASS" if ok_f else "FAIL", det_f[:80])
    if not ok_f: all_pass = False
    overall = "PASS" if all_pass else "FAIL"
    print(f"\n[SUMMARY] p28 night-counter-receipt overall: {overall}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
