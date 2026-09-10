"""HARNESS CITE-TYPE-MATCH mutate · V3.5r item 5 · đen-rồi-xanh.

Baseline OK case:
  "header-n ≡ printed lines · pointer-integrity [per p22]"
  → p22.loài=count-pointer · claim loài (via hint 'header-n|pointer-integrity') = count-pointer
  → MATCH · lint 0 finding

Mutate case:
  Cùng câu · thay [per p22] → [per p7]
  → p7.loài=seal-integrity ≠ count-pointer
  → PHẢI FAIL · lint 1 finding (cite-type-mismatch)

Ngược lại · baseline seal-integrity:
  "concat-seal footer hash [per p7]" · match seal-integrity ⇒ OK
  Mutate → [per p22] ⇒ mismatch ⇒ FAIL
"""
from __future__ import annotations
import sys, os, hashlib
from pathlib import Path
from datetime import datetime, timezone

try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except: pass  # L-66-OK (benign fallback)

REPO = Path("/root/Data_back_test/whale_data") if os.name != "nt" else Path(r"D:/Data back test/whale_data")
SB_LOG = REPO / "data/logs/harness_sabotage.log"

sys.path.insert(0, str(REPO / "tests/harness"))
from label_claims_lint import lint_file  # noqa: E402


def _log(pin, mutate, verdict, extra):
    ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
    sha = hashlib.md5(f"{pin}{mutate}{verdict}{extra}".encode()).hexdigest()[:8]
    SB_LOG.parent.mkdir(parents=True, exist_ok=True)
    with SB_LOG.open("a", encoding="utf-8") as f:
        f.write(f"{ts}\t{pin}\t{mutate}\t{verdict}\t{sha}\n")


def _write_probe(text: str) -> Path:
    p = REPO / "tests/harness/_probe_cite_mutate.txt"
    p.write_text(text, encoding="utf-8")
    return p


def case_baseline_p22():
    """count-pointer claim citing p22 (count-pointer seal) ⇒ OK."""
    body = (
        "# claim body — count-pointer domain\n"
        "header-n ≡ printed lines · pointer-integrity OK [per p22]\n"
        "n_events=42 md5=abcd1234ef56\n"
    )
    p = _write_probe(body)
    findings = lint_file(p)
    ctm = [f for f in findings if f.get("kind") == "cite-type-mismatch"]
    passed = (len(ctm) == 0)
    return passed, f"n_ctm={len(ctm)} (expect 0) · total={len(findings)}"


def case_mutate_p22_to_p7():
    """MUTATE cite [per p22] → [per p7] · count-pointer claim citing seal-integrity ⇒ FAIL."""
    body = (
        "# claim body — count-pointer domain\n"
        "header-n ≡ printed lines · pointer-integrity OK [per p7]\n"
        "n_events=42 md5=abcd1234ef56\n"
    )
    p = _write_probe(body)
    findings = lint_file(p)
    ctm = [f for f in findings if f.get("kind") == "cite-type-mismatch"]
    passed = (len(ctm) >= 1)
    detail = f"n_ctm={len(ctm)} (expect ≥1) · claim: {ctm[0]['claim'] if ctm else 'NONE'}"
    return passed, detail


def case_baseline_p7_seal():
    """seal-integrity claim citing p7 (seal-integrity seal) ⇒ OK."""
    body = (
        "# claim body — seal-integrity domain\n"
        "concat-seal footer hash matches body md5[:12] · verified [per p7]\n"
        "md5=deadbeef1234\n"
    )
    p = _write_probe(body)
    findings = lint_file(p)
    ctm = [f for f in findings if f.get("kind") == "cite-type-mismatch"]
    passed = (len(ctm) == 0)
    return passed, f"n_ctm={len(ctm)} (expect 0) · total={len(findings)}"


def case_mutate_p7_to_p22():
    """MUTATE cite [per p7] → [per p22] · seal-integrity claim citing count-pointer ⇒ FAIL."""
    body = (
        "# claim body — seal-integrity domain\n"
        "concat-seal footer hash matches body md5[:12] · verified [per p22]\n"
        "md5=deadbeef1234\n"
    )
    p = _write_probe(body)
    findings = lint_file(p)
    ctm = [f for f in findings if f.get("kind") == "cite-type-mismatch"]
    passed = (len(ctm) >= 1)
    return passed, f"n_ctm={len(ctm)} (expect ≥1) · claim: {ctm[0]['claim'] if ctm else 'NONE'}"


def main():
    print("═" * 62)
    print("HARNESS · CITE-TYPE-MATCH mutate · V3.5r item 5 · đen-rồi-xanh")
    print("═" * 62)
    cases = [
        ("baseline-p22-count", case_baseline_p22),
        ("MUTATE-p22→p7", case_mutate_p22_to_p7),
        ("baseline-p7-seal", case_baseline_p7_seal),
        ("MUTATE-p7→p22", case_mutate_p7_to_p22),
    ]
    all_pass = True
    for name, fn in cases:
        ok, detail = fn()
        mark = "✅" if ok else "❌"
        print(f"  {mark} {name}: {detail}")
        _log("cite-type-match", name, "PASS" if ok else "FAIL", detail[:80])
        if not ok: all_pass = False
    overall = "PASS" if all_pass else "FAIL"
    print(f"\n[SUMMARY] cite-type-match mutate overall: {overall}")
    # cleanup
    try: (REPO / "tests/harness/_probe_cite_mutate.txt").unlink(missing_ok=True)
    except Exception: pass  # L-66-OK
    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
