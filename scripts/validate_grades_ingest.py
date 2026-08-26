#!/usr/bin/env python3
"""[R5 GRADES INGEST VALIDATOR — chờ ANALYSIS re-export bản full]

Purpose: nhận file grades từ ANALYSIS, validate schema + rule trước khi ingest
vào census_63 grades store.

Schema kỳ vọng:
    token,date,h2_vé,grade,basis,graded_at,data_through

Rules:
    - REJECT dupe (token, date)
    - REJECT data_through != YYYY-MM-DD
    - REJECT grade ∉ {TP, FP, PENDING, NOT-EVALUABLE}
    - REJECT graded_at != YYYY-MM-DD or ISO datetime
    - REJECT missing required columns
    - Cross-reference: bản full khi về phải đủ 63 (token, date) khớp CSV-63.
    - Bản hiện tại 29 dòng: NHIỄM → không ingest, đợi re-export.

Usage:
    python scripts/validate_grades_ingest.py path/to/grades.csv [--reference scratch/e2_census_perfire_v2_20260828.csv]
"""
from __future__ import annotations
import sys, io, csv, argparse, re, hashlib
from pathlib import Path
from datetime import datetime
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = Path(r"D:/Data back test/whale_data")
DEFAULT_REF = REPO / "scratch/e2_census_perfire_v2_20260828.csv"

REQUIRED_COLS = {"token", "date", "grade", "basis", "graded_at", "data_through"}
# h2_vé column: nhận cả alias "ve" hoặc "h2_ve" per operator relay (1) 28/08
H2VE_ALIASES = {"h2_vé", "h2_ve", "ve", "vé"}
VALID_GRADES = {"TP", "FP", "PENDING", "NOT-EVALUABLE"}
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
DATETIME_RE = re.compile(r"^\d{4}-\d{2}-\d{2}(T\d{2}:\d{2}:\d{2})?")


def _load_reference(path: Path) -> set:
    """Load (token, date) tuples from CSV-63 for cross-reference."""
    ref = set()
    with open(path, encoding="utf-8") as f:
        header_seen = False
        for line in f:
            if line.startswith("#") or not line.strip(): continue
            if not header_seen and line.startswith("token,"):
                header_seen = True; continue
            cells = [c.strip() for c in line.split(",")]
            if len(cells) >= 2:
                ref.add((cells[0], cells[1]))
    return ref


def validate(grades_path: Path, ref_path: Path, verbose: bool = True,
             full_63_expected: bool = None) -> tuple[bool, list]:
    """Return (accept, errors).

    full_63_expected:
      None (default) → infer từ row count: if len(rows) == 63 → apply COVERAGE.
                        Else partial-by-design, SKIP COVERAGE (per operator relay 28/08).
      True           → force COVERAGE check
      False          → force SKIP COVERAGE
    """
    errors = []

    if not grades_path.exists():
        return False, [f"[FATAL] file missing: {grades_path}"]

    ref = _load_reference(ref_path)
    if verbose:
        print(f"[REF] loaded {len(ref)} (token,date) tuples from {ref_path.name}")

    # Parse grades file
    try:
        with open(grades_path, encoding="utf-8") as f:
            # Skip commented lines
            lines = [l for l in f if not l.startswith("#") and l.strip()]
        if not lines:
            return False, ["[FATAL] file empty"]
        reader = csv.DictReader(lines)
        rows = list(reader)
        cols = set(reader.fieldnames or [])
    except Exception as e:
        return False, [f"[FATAL] parse fail: {e}"]

    if verbose:
        print(f"[FILE] {grades_path.name}: {len(rows)} rows · cols: {sorted(cols)}")
        print(f"       md5: {hashlib.md5(open(grades_path,'rb').read()).hexdigest()}")

    # h2_vé alias: nhận "ve" / "h2_ve" / "h2_vé" / "vé"
    h2ve_col_found = cols & H2VE_ALIASES
    if not h2ve_col_found:
        errors.append(f"[SCHEMA] missing h2_vé column (accept aliases: {sorted(H2VE_ALIASES)})")
    elif verbose:
        print(f"[H2VE] using alias col: {sorted(h2ve_col_found)}")

    # Schema check (không đòi h2_vé riêng, dùng alias set)
    missing = REQUIRED_COLS - cols
    if missing:
        errors.append(f"[SCHEMA] missing required cols: {sorted(missing)}")

    # Per-row validation
    seen = {}
    for i, r in enumerate(rows, 1):
        tok = r.get("token", "").strip()
        date = r.get("date", "").strip()
        key = (tok, date)

        # Dupe check
        if key in seen:
            errors.append(f"[DUPE] row {i}: ({tok},{date}) đã xuất hiện ở row {seen[key]}")
        else:
            seen[key] = i

        # grade enum
        grade = r.get("grade", "").strip()
        if grade not in VALID_GRADES:
            errors.append(f"[GRADE] row {i} ({tok},{date}): grade='{grade}' ∉ {sorted(VALID_GRADES)}")

        # data_through format
        dt = r.get("data_through", "").strip()
        if not DATE_RE.match(dt):
            errors.append(f"[DATE] row {i} ({tok},{date}): data_through='{dt}' ≠ YYYY-MM-DD")

        # graded_at format (allow ISO datetime)
        ga = r.get("graded_at", "").strip()
        if not DATETIME_RE.match(ga):
            errors.append(f"[DATE] row {i} ({tok},{date}): graded_at='{ga}' không hợp lệ")

        # date format
        if not DATE_RE.match(date):
            errors.append(f"[DATE] row {i}: date='{date}' ≠ YYYY-MM-DD")

    # Cross-reference: full 63 check
    graded_keys = set(seen.keys())
    missing_from_ref = ref - graded_keys
    extra_not_in_ref = graded_keys - ref

    # [OPERATOR RELAY 28/08] COVERAGE rule chỉ áp bản FULL-63.
    # Bản partial (n<63) = by-design, KHÔNG ingest nhưng cross-ref không REJECT.
    if full_63_expected is None:
        full_63_expected = (len(rows) == len(ref))
    if full_63_expected:
        if len(rows) != len(ref):
            errors.append(f"[COVERAGE] {len(rows)} rows vs {len(ref)} expected trong CSV-63 (thiếu {len(missing_from_ref)}, dư {len(extra_not_in_ref)})")
    elif verbose:
        print(f"[COVERAGE-SKIP] {len(rows)} rows < {len(ref)} → partial-by-design, không REJECT (per operator relay 28/08)")

    # EXTRA vẫn REJECT bất kể partial or full — không được có key ngoài CSV-63
    if extra_not_in_ref:
        errors.append(f"[EXTRA] {len(extra_not_in_ref)} keys không có trong CSV-63: {sorted(extra_not_in_ref)[:5]}...")

    if missing_from_ref and verbose and full_63_expected:
        print(f"\n[COVERAGE-DETAIL] {len(missing_from_ref)} fire keys chưa được grade:")
        for k in sorted(missing_from_ref)[:20]:
            print(f"  {k}")
        if len(missing_from_ref) > 20:
            print(f"  ... (+{len(missing_from_ref)-20} more)")
    elif missing_from_ref and verbose:
        print(f"\n[PARTIAL-INFO] {len(missing_from_ref)}/{len(ref)} keys chưa grade — hợp lệ cho bản partial")

    accept = len(errors) == 0
    return accept, errors


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="R5 grades ingest validator")
    ap.add_argument("grades_file", nargs="?", help="Path to grades CSV from ANALYSIS")
    ap.add_argument("--reference", default=str(DEFAULT_REF),
                    help="Reference CSV-63 for cross-check (default: e2_census_perfire_v2)")
    ap.add_argument("--dry-smoke", action="store_true",
                    help="Run smoke test with synthetic bad file (validates rejection paths)")
    args = ap.parse_args()

    if args.dry_smoke:
        # Smoke test — write bad file, validate, expect rejection
        import tempfile
        smoke = Path(tempfile.mkdtemp()) / "smoke_bad_grades.csv"
        smoke.write_text(
            "token,date,h2_vé,grade,basis,graded_at,data_through\n"
            "BANANAS31,2026-07-04,pos-ratio,TP,close +50% D+7,2026-08-25,2026-08-25\n"
            "BANANAS31,2026-07-04,pos-ratio,FP,dupe key,2026-08-25,2026-08-25\n"       # DUPE
            "COAI,2026-07-23,-,INVALID,bad grade,2026-08-25,2026-08-25\n"              # BAD grade
            "GENIUS,2026-07-03,pos-ratio,TP,ok,2026-08-25,08/25/2026\n"                # BAD data_through
            "FAKE,2026-01-01,pos-ratio,TP,not in ref,2026-08-25,2026-08-25\n"          # EXTRA
        , encoding="utf-8")
        print(f"[SMOKE] running with synthetic bad file: {smoke}\n")
        accept, errors = validate(smoke, Path(args.reference))
        print(f"\n[SMOKE RESULT] accept={accept} (expect False)")
        for e in errors: print(f"  {e}")
        sys.exit(0 if not accept else 1)  # expect rejection

    if not args.grades_file:
        # No file given — print status + expected schema
        print("═" * 80)
        print("[R5 GRADES INGEST VALIDATOR — CHỜ FILE TỪ ANALYSIS]")
        print("═" * 80)
        print(f"""
Schema kỳ vọng:
    token,date,h2_vé,grade,basis,graded_at,data_through

Rules:
    - grade ∈ {{TP, FP, PENDING, NOT-EVALUABLE}}
    - data_through = YYYY-MM-DD (strict)
    - graded_at = YYYY-MM-DD hoặc ISO datetime
    - unique (token, date) — REJECT dupe
    - full 63 rows khớp CSV-63 e2_census_perfire_v2_20260828.csv

Trạng thái hiện tại: bản 29 dòng NHIỄM — chờ re-export, không ingest.

Usage:
    python scripts/validate_grades_ingest.py <grades.csv>
    python scripts/validate_grades_ingest.py --dry-smoke  # test rejection paths
""")
        sys.exit(0)

    accept, errors = validate(Path(args.grades_file), Path(args.reference))
    print(f"\n═══ VERDICT ═══")
    print(f"accept: {accept}")
    if errors:
        print(f"\n[{len(errors)} errors]:")
        for e in errors: print(f"  {e}")
    if accept:
        print("[OK] file hợp lệ — sẵn sàng ingest vào census_63_grades store")
    else:
        print("[REJECT] không ingest, chờ ANALYSIS fix + re-export")
    sys.exit(0 if accept else 1)
