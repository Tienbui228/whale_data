r"""HARNESS p3 di-sản · V3.5r item 2 · đen-rồi-xanh · body 09-09 format shift.

Di-sản: body watchlist 09-09 dùng format "TOP K/N" thay vì "(N tokens)".
Trước-fix: regex đơn `\((\d+) tokens` không match TOP → n_artifact=None → p3 FAIL.
Sau-fix: dual regex fallback `TOP\s+\d+/(\d+)` → match → n_artifact=N → p3 PASS.

Tuyển-dụng chay: synthesize 2 fake watchlist bodies:
  · legacy_body: "=== LIST A — 45 tokens ==="  → OLD parser PASS · NEW parser PASS
  · new_body:    "=== LIST A — TOP 20/69 ==="  → OLD parser FAIL · NEW parser PASS

Cả 2 vế đen-xanh in ra 4-field log.
"""
from __future__ import annotations
import sys, os, re, hashlib
from pathlib import Path
from datetime import datetime, timezone

try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except: pass  # L-66-OK (benign fallback)

REPO = Path("/root/Data_back_test/whale_data") if os.name != "nt" else Path(r"D:/Data back test/whale_data")
SB_LOG = REPO / "data/logs/harness_sabotage.log"


def _log(pin, disan, verdict, extra):
    ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
    sha = hashlib.md5(f"{pin}{disan}{verdict}{extra}".encode()).hexdigest()[:8]
    SB_LOG.parent.mkdir(parents=True, exist_ok=True)
    with SB_LOG.open("a", encoding="utf-8") as f:
        f.write(f"{ts}\t{pin}\t{disan}\t{verdict}\t{sha}\n")


OLD_REGEX = r"=== LIST A —.*?\((\d+) tokens"
NEW_REGEX = r"=== LIST A — TOP\s+\d+/(\d+)"


def _extract_n(body, regexes):
    """Try each regex in order · return first (n, regex_used) or (None, None)."""
    for r in regexes:
        m = re.search(r, body)
        if m: return int(m.group(1)), r
    return None, None


def case_legacy_body():
    """Body format cũ '=== LIST A — hedge watchlist (45 tokens) ===' — cả OLD lẫn NEW parser PASS."""
    body = (
        "hedge watchlist header\n"
        "=== LIST A — hedge watchlist (45 tokens) ===\n"
        "SYM1 SYM2 SYM3 ...\n"
    )
    n_old, _ = _extract_n(body, [OLD_REGEX])
    n_new, r_new = _extract_n(body, [OLD_REGEX, NEW_REGEX])
    return {
        "body": "legacy '(N tokens)'",
        "OLD_parser": n_old, "NEW_parser": n_new,
        "OLD_pass": n_old == 45, "NEW_pass": n_new == 45,
    }


def case_new_body():
    """Body format mới 'TOP 20/69' — OLD parser FAIL · NEW parser PASS."""
    body = (
        "hedge watchlist header · V3.5q format shift\n"
        "=== LIST A — TOP 20/69 ===\n"
        "SYM1 SYM2 SYM3 ...\n"
    )
    n_old, _ = _extract_n(body, [OLD_REGEX])
    n_new, r_new = _extract_n(body, [OLD_REGEX, NEW_REGEX])
    return {
        "body": "new 'TOP K/N'",
        "OLD_parser": n_old, "NEW_parser": n_new,
        "OLD_pass": n_old == 69, "NEW_pass": n_new == 69,
    }


def check_real_body_09_09():
    """Check REAL body of watchlist artifact for 2026-09-09 if exists."""
    art_dir = REPO / "data/artifacts"
    p = art_dir / "tg_final_watchlist_2026-09-09.txt"
    if not p.exists(): return None
    body = p.read_text(encoding="utf-8", errors="replace")
    n_old, _ = _extract_n(body, [OLD_REGEX])
    n_new, r_new = _extract_n(body, [OLD_REGEX, NEW_REGEX])
    return {
        "path": str(p), "size": len(body),
        "OLD_parser": n_old, "NEW_parser": n_new, "regex_used": r_new,
    }


def main():
    print("═" * 62)
    print("HARNESS p3 di-sản · V3.5r item 2 · đen-rồi-xanh format shift")
    print("═" * 62)

    print("\n─── Case A · legacy body '(N tokens)' ───")
    a = case_legacy_body()
    for k, v in a.items(): print(f"  · {k}: {v}")
    _log("p3-disan", "case-A legacy", "PASS" if a["OLD_pass"] and a["NEW_pass"] else "FAIL", str(a)[:80])

    print("\n─── Case B · new body 'TOP K/N' — đen-rồi-xanh ───")
    b = case_new_body()
    for k, v in b.items(): print(f"  · {k}: {v}")
    # Đen-rồi-xanh: OLD must FAIL (n=None) · NEW must PASS (n=69)
    disan_ok = (b["OLD_parser"] is None) and b["NEW_pass"]
    print(f"  · ĐEN (OLD FAIL): {b['OLD_parser'] is None}")
    print(f"  · XANH (NEW PASS): {b['NEW_pass']}")
    _log("p3-disan", "case-B new TOP · đen-xanh",
         "PASS" if disan_ok else "FAIL", f"OLD_None={b['OLD_parser'] is None} NEW_pass={b['NEW_pass']}")

    print("\n─── Case C · REAL body watchlist 09-09 (if exists) ───")
    c = check_real_body_09_09()
    if c is None:
        print("  ⚠ artifact tg_final_watchlist_2026-09-09.txt MISSING locally (VPS-only)")
        _log("p3-disan", "case-C real 09-09", "N/A-MISS-LOCAL", "artifact not on local")
    else:
        for k, v in c.items(): print(f"  · {k}: {v}")
        _log("p3-disan", "case-C real 09-09", "OBSERVED", str(c)[:80])

    overall = "PASS" if disan_ok else "FAIL"
    print(f"\n[SUMMARY] p3 di-sản đen-xanh: {overall}")
    return 0 if disan_ok else 1


if __name__ == "__main__":
    sys.exit(main())
