"""BẢNG-CHẤM-⭐ manager · KÝ 07/09 V3.5.

Ledger: data/state/star_grades.jsonl (append-only, L-74 header)
View:   data/state/star_grades.md (regen từ jsonl)

Usage:
  python star_grades_manage.py append --symbol COLLECT --outcome-recall TP --outcome-direction FP --note "verbatim ..."
  python star_grades_manage.py regen-view
"""
from __future__ import annotations
import argparse, json, hashlib, os, sys, tempfile
from pathlib import Path
from datetime import datetime, timezone

try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except: pass  # L-66-OK (benign fallback)

REPO = Path("/root/Data_back_test/whale_data") if os.name != "nt" else Path(r"D:/Data back test/whale_data")
LEDGER = REPO / "data/state/star_grades.jsonl"
VIEW = REPO / "data/state/star_grades.md"
LEDGER.parent.mkdir(parents=True, exist_ok=True)

L74_HEADER = f"""# BẢNG-CHẤM-⭐ · view sinh từ star_grades.jsonl (L-74)
# Regen: python scripts/star_grades_manage.py regen-view
# CẤM edit .md trực tiếp · edit chỉ .jsonl (append-only)
"""


def _write_atomic(p, content):
    tmp_fd, tmp_name = tempfile.mkstemp(dir=str(p.parent), suffix=".tmp")
    try:
        with os.fdopen(tmp_fd, "wb") as f: f.write(content)
        os.replace(tmp_name, p)
    except:
        try: os.unlink(tmp_name)
        except: pass  # L-66-OK (benign fallback)
        raise


def append_entry(symbol, outcome_recall, outcome_direction, note, target_date=None, cite=None):
    ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
    entry = {
        "ts_utc": ts,
        "symbol": symbol,
        "target_date": target_date,
        "outcome_recall": outcome_recall,      # TP · FP · FN · TN
        "outcome_direction": outcome_direction,  # TP · FP · FN · TN
        "note": note,
        "cite": cite or {},
    }
    with LEDGER.open("ab") as f:
        f.write((json.dumps(entry, ensure_ascii=False) + "\n").encode("utf-8"))
    print(f"[APPEND] {LEDGER.name} · {symbol} · recall={outcome_recall} · direction={outcome_direction}")


def regen_view():
    entries = []
    if LEDGER.exists():
        for line in LEDGER.read_text(encoding="utf-8").splitlines():
            if line.strip():
                try: entries.append(json.loads(line))
                except: pass  # L-66-OK (benign fallback)
    n = len(entries)
    tp_r = sum(1 for e in entries if e.get("outcome_recall") == "TP")
    fp_d = sum(1 for e in entries if e.get("outcome_direction") == "FP")
    lines = [L74_HEADER, ""]
    lines.append(f"# BẢNG-CHẤM-⭐ · {n} entries · TP-recall={tp_r} · FP-direction={fp_d}")
    lines.append("")
    lines.append("| # | ts_utc | symbol | target | recall | direction | note |")
    lines.append("|---:|---|---|---|:---:|:---:|---|")
    for i, e in enumerate(entries, 1):
        note = (e.get("note","") or "").replace("|", "\\|").replace("\n"," ")
        lines.append(f"| {i} | {e['ts_utc']} | {e['symbol']} | {e.get('target_date') or '-'} | {e.get('outcome_recall','-')} | {e.get('outcome_direction','-')} | {note} |")
    content = ("\n".join(lines) + "\n").encode("utf-8")
    _write_atomic(VIEW, content)
    md5 = hashlib.md5(content).hexdigest()
    print(f"[REGEN] {VIEW} · n={n} · md5={md5}")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    ap_a = sub.add_parser("append")
    ap_a.add_argument("--symbol", required=True)
    ap_a.add_argument("--outcome-recall", required=True, choices=["TP","FP","FN","TN"])
    ap_a.add_argument("--outcome-direction", required=True, choices=["TP","FP","FN","TN"])
    ap_a.add_argument("--note", required=True)
    ap_a.add_argument("--target-date", default=None)
    ap_a.add_argument("--cite", default=None)
    sub.add_parser("regen-view")
    args = ap.parse_args()
    if args.cmd == "append":
        append_entry(args.symbol, args.outcome_recall, args.outcome_direction,
                     args.note, args.target_date, args.cite)
        regen_view()
    elif args.cmd == "regen-view":
        regen_view()


if __name__ == "__main__":
    main()
