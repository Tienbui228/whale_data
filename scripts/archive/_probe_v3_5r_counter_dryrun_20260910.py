"""V3.5r item 3 · night-counter DRY-RUN trên preview_journal THẬT (VPS).

SSH pull /root/Data_back_test/whale_data/data/logs/preview_journal.jsonl
→ apply master_preview_send.main() V3.5q counter logic for target=2026-09-10
→ print {n_entries · entries_dump · distinct_targets · night_label}

Kỳ vọng: journal 0-byte (chưa cron nào chạy V3.5q) ⇒ distinct=∅ ⇒ nhãn "đêm 1/2".
Nếu ra 2/2 ⇒ giải phẫu entry nào (V3.5q chưa deploy đêm nay).
"""
from __future__ import annotations
import sys, os, json, subprocess
from pathlib import Path

try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except: pass  # L-66-OK (benign fallback)

REPO = Path("/root/Data_back_test/whale_data") if os.name != "nt" else Path(r"D:/Data back test/whale_data")
LOCAL_MIRROR = REPO / "data/logs/preview_journal.jsonl.vps_pull"
EPOCH = "2026-09-10"


def pull_vps_journal():
    """SCP fetch VPS preview_journal to local mirror."""
    r = subprocess.run(
        ["ssh", "-o", "ConnectTimeout=8", "root@5.223.67.21",
         "cat /root/Data_back_test/whale_data/data/logs/preview_journal.jsonl 2>/dev/null || echo ''"],
        capture_output=True, text=True, timeout=15)
    LOCAL_MIRROR.parent.mkdir(parents=True, exist_ok=True)
    LOCAL_MIRROR.write_text(r.stdout, encoding="utf-8")
    return r.stdout


def counter_logic(journal_path: Path, target: str, epoch: str):
    """Replicate scripts/master_preview_send.py main() V3.5q counter logic."""
    entries = []
    distinct_targets = set()
    if journal_path.exists():
        for i, line in enumerate(journal_path.read_text(encoding="utf-8").splitlines(), 1):
            line = line.strip()
            if not line: continue
            try:
                e = json.loads(line)
                entries.append({"line": i, "entry": e})
                if e.get("standing_ok") and e.get("target_date", "") >= epoch:
                    distinct_targets.add(e["target_date"])
            except Exception as ex:
                entries.append({"line": i, "parse_error": str(ex), "raw": line[:80]})
    n_after_this = len(distinct_targets | {target})
    return entries, distinct_targets, n_after_this


def main():
    print("═" * 62)
    print("V3.5r · night-counter DRY-RUN on REAL preview_journal (VPS pull)")
    print("═" * 62)

    print("\n─── STEP 1 · SCP pull VPS preview_journal.jsonl ───")
    content = pull_vps_journal()
    print(f"  mirror: {LOCAL_MIRROR}")
    print(f"  size: {len(content)} bytes")
    n_lines = len([l for l in content.splitlines() if l.strip()])
    print(f"  non-empty lines: {n_lines}")

    print("\n─── STEP 2 · counter logic per master_preview_send V3.5q ───")
    target = "2026-09-10"
    entries, distinct, n_label = counter_logic(LOCAL_MIRROR, target, EPOCH)
    print(f"  target={target} · epoch={EPOCH}")
    print(f"  entries parsed: {len(entries)}")
    for e in entries[:5]:  # dump first 5
        print(f"    · line{e['line']}: {json.dumps(e['entry'], ensure_ascii=False)[:120] if 'entry' in e else e}")
    if len(entries) > 5:
        print(f"    · ... ({len(entries)-5} more)")
    print(f"  distinct_targets (standing_ok · ≥{EPOCH}): {sorted(distinct)}")
    print(f"  distinct count: {len(distinct)}")
    print(f"  night_label after adding target={target}: '{n_label}/2'")

    print("\n─── STEP 3 · verdict ───")
    expected = "1/2" if len(distinct) == 0 or (len(distinct) == 1 and target in distinct) else f"{n_label}/2"
    print(f"  expected (VPS empty · V3.5q chưa cron nào chạy): 1/2")
    print(f"  observed: {n_label}/2")
    ok = (n_label == 1)
    marker = "✅" if ok else "❌"
    print(f"  {marker} match: {ok}")
    if not ok:
        print(f"\n  ⚠ GIẢI PHẪU · entry lọt filter · REVIEW ABOVE dump")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
