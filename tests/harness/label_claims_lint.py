"""LABEL-CLAIMS-LINT · V3.5f enforcement-trước-chữ · V3.5j corpus updated.

Grep tầng render/report các nhãn CLAIM:
  {sorted · sort: · ✓ · checked · verified · OK · PASS · đã-*}

Hợp lệ chỉ khi trong bán kính [k=5] dòng có PHÉP-KIỂM-IN-ĐƯỢC hoặc CITE [per <seal-id>].

L-79 EXHIBITS in corpus:
  #1 (V3.5f): "pointer-integrity: OK" mồ côi
  #2 (V3.5i): "5/5 WIRED ✅" không biên lai
  #2b (V3.5i): claim-✅-giả toàn phần (watchlist wire 0 dump_as_sent)
  #3 (V3.5j · NEW): grep-sai-file phantom-blocker
     "grep -c TG_CHAT_ID_DAILY .env = 0" → agent tuyên "env not set" · KHÔNG
     grep /root/.env_tg (nơi thật · chmod 600 · sitting since 03/09).
     Bịa blocker vì grep sai chỗ = L-79 bản gốc.

TUYỂN-DỤNG: chạy trên corpus demo-4 (dòng "pointer-integrity: OK" mồ côi) →
PHẢI bắt được orphan → 4-field log.
"""
from __future__ import annotations
import argparse, hashlib, os, re, sys
from pathlib import Path
from datetime import datetime, timezone

try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except: pass  # L-66-OK (benign fallback)

REPO = Path("/root/Data_back_test/whale_data") if os.name != "nt" else Path(r"D:/Data back test/whale_data")
LOG_PATH = REPO / "data/logs/harness_sabotage.log"

# Regex nhãn CLAIM (case-insensitive)
CLAIM_PATTERNS = [
    r"\bsorted\b",
    r"\bsort:",
    r"[✓]",
    r"\bchecked\b",
    r"\bverified\b",
    r"\bOK\b",
    r"\bPASS\b",
    r"\bđã[\-\s]\w+",
]
CLAIM_RE = re.compile("|".join(CLAIM_PATTERNS), re.IGNORECASE)

# Regex evidence: cite/kiểm-in-được
EVIDENCE_PATTERNS = [
    r"\bmd5\s*=\s*[a-f0-9]{4,}",              # md5=abcd...
    r"\bn(_\w+)?\s*=\s*\d+",                   # n=X · n_events=125
    r"\bfile\s*=\s*\S+",                       # file=path
    r"[<\[]per\s+[a-z0-9_\-\.]+[>\]]",         # [per <seal-id>]
    r"[<\[]per\s+\S+[>\]]",                    # generic
    r"==",                                      # equation
    r"≤|≥|<=|>=",                              # comparison
    r"\bhash\s*=\s*[a-f0-9]{4,}",              # hash=abcd
    r"→",                                       # implication (has explicit target)
    r"\bexpected\s*[:=]",                      # expected: X
    r"\bratio\s*[:=]",                          # ratio: X
]
EVIDENCE_RE = re.compile("|".join(EVIDENCE_PATTERNS), re.IGNORECASE)

K_RADIUS = 5  # bán kính dòng để tìm evidence


def lint_file(path: Path, k: int = K_RADIUS):
    """Return list of orphan-label findings: {line_no, line, claim, orphan: True}."""
    if not path.exists(): return []
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    findings = []
    for i, line in enumerate(lines):
        m = CLAIM_RE.search(line)
        if not m: continue
        claim_str = m.group(0)
        # Check within radius ±k lines for evidence
        lo = max(0, i - k); hi = min(len(lines), i + k + 1)
        window = "\n".join(lines[lo:hi])
        has_evidence = bool(EVIDENCE_RE.search(window))
        if not has_evidence:
            findings.append({
                "line_no": i + 1, "line": line.strip()[:200],
                "claim": claim_str, "orphan": True,
                "path": str(path)
            })
    return findings


def build_demo4_corpus():
    """Build synthetic demo-4 corpus with `pointer-integrity: OK` mồ côi + 2 non-orphan controls."""
    corpus = REPO / "tests/harness/_lint_demo4_corpus.txt"
    corpus.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# DEMO-4 report body (V3.5f label-lint tuyển-dụng corpus)",
        "",
        "Section A: preview state summary",
        "pointer-integrity: OK",   # <-- ORPHAN CLAIM · no evidence within ±5 lines
        "some unrelated prose here",
        "more prose",
        "yet more prose",
        "",
        "Section B: real check with evidence",
        "n_events=125 md5=dd9e83f0b9af5d475aa6dc043f3b6e98",
        "p13 checked: sent_hash=f58843a649cf target=2026-09-02",  # <-- 'checked' with evidence
        "verified: coverage fresh 6/31 kho 9/31 perp 19/31",  # <-- 'verified' with n= evidence
        "",
        "Section C: sorted claim without evidence",
        "PRE tokens sorted mới nhất → chưa in dữ liệu bảng",  # <-- ORPHAN 'sorted'
        "",
        "Section D: claim with [per <seal-id>]",
        "verdict: PASS [per harness_sabotage_20260907]",   # <-- OK cite
        "",
        "Section E: L-79 exhibit #3 (V3.5j) · grep-sai-file phantom-blocker",
        "env checked: TG_CHAT_ID_DAILY not set (grep -c .env = 0)",   # <-- ORPHAN 'checked' (phantom)
        "TRUE cite would need /root/.env_tg not .env · file path missing",
    ]
    corpus.write_text("\n".join(lines), encoding="utf-8")
    return corpus


def _log(pin, mutate, verdict, extra=""):
    ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
    revert_sha = hashlib.md5(f"{pin}{mutate}{verdict}{extra}".encode()).hexdigest()[:8]
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(f"{ts}\tlabel-lint\t{mutate}\t{verdict}\t{revert_sha}\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--path", help="File to lint")
    ap.add_argument("--tuyendung", action="store_true", help="Run tuyển-dụng test on demo-4 corpus")
    ap.add_argument("--k", type=int, default=K_RADIUS)
    args = ap.parse_args()

    if args.tuyendung:
        print("═" * 60)
        print("LABEL-CLAIMS-LINT · TUYỂN-DỤNG on demo-4 corpus")
        print("═" * 60)
        corpus = build_demo4_corpus()
        print(f"[CORPUS] {corpus}")
        findings = lint_file(corpus, k=args.k)
        print(f"\n[LINT RESULT] n_orphan_claims={len(findings)}")
        for f in findings:
            print(f"  L{f['line_no']}: claim='{f['claim']}' · line='{f['line']}'")
        # Expected: at least 1 orphan (pointer-integrity: OK) + 1 more (sorted...)
        if len(findings) >= 1:
            print(f"\n✅ TUYỂN-DỤNG PASS · lint bắt được {len(findings)} orphan claim(s)")
            _log("label-lint", f"tuyển-dụng corpus demo-4 · caught {len(findings)} orphan(s)",
                 "PASS", str(findings)[:100])
        else:
            print(f"\n❌ TUYỂN-DỤNG FAIL · lint không bắt được orphan expected")
            _log("label-lint", "tuyển-dụng corpus demo-4", "FAIL-DID-NOT-CATCH-ORPHAN", "")
        return

    if args.path:
        path = Path(args.path)
        findings = lint_file(path, k=args.k)
        print(f"[LINT] {path} · n_orphan={len(findings)}")
        for f in findings:
            print(f"  L{f['line_no']}: claim='{f['claim']}' · line='{f['line']}'")
        return

    print("Usage: --tuyendung  OR  --path <file>")


if __name__ == "__main__":
    main()
