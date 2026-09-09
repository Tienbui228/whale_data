"""HARNESS p20-p22 · V3.5k directive item 5 · TUYỂN BẰNG DI-SẢN (đen-có-sẵn).

p20 SIDECAR-MISSING → N/A-ERROR
  Legacy evidence: 09-08 · watchlist artifact missing (V3.5i Path bug) · pre-fix
  code rendered "HEDGE: A=0 · B-top: - · 🎓0" (số 0 GIẢ).
  Post-fix: "HEDGE: N/A-ERROR (sidecar missing — xem log)" · CẤM ký tự số.
  Ledger skip seed from that source that day (D8 signed).

p21 PX-NA → WATCH direction
  Legacy evidence: APR 09-08 star with px_now=None · pre-fix rendered "PRE".
  Post-fix: "⏸ WATCH [PX-PENDING]: APR" · direction=WATCH · CẤM PRE/POST/XẢ.

p22 COUNT ≡ PRINTED
  Legacy evidence: demo-5 header claimed "⭐-PRE (11):" but only 8 lines printed
  (slice [:8] · "(+3 more)" style).
  Post-fix: header-n ≡ printed lines · top-K=6 + tail "(+N nữa: SYM·SYM·SYM)"
  · tail lists ALL remaining names ĐỦ (pointer-integrity).

Log 4-field: {pin · di-sản · FAIL-msg · fix-sha}
Fixture master md5 wired into footer digest = signal các pin thật niêm.
"""
from __future__ import annotations
import sys, os, re, json, hashlib
from pathlib import Path
from datetime import datetime, timezone

try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except: pass  # L-66-OK (benign fallback)

REPO = Path("/root/Data_back_test/whale_data") if os.name != "nt" else Path(r"D:/Data back test/whale_data")
SB_LOG = REPO / "data/logs/harness_sabotage.log"


def _log(pin, disan, fail_msg, fix_sha):
    ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
    SB_LOG.parent.mkdir(parents=True, exist_ok=True)
    with SB_LOG.open("a", encoding="utf-8") as f:
        f.write(f"{ts}\t{pin}\t{disan}\t{fail_msg}\t{fix_sha}\n")


def _sha8(s): return hashlib.md5(str(s).encode()).hexdigest()[:8]


# ═════ p20 SIDECAR-MISSING → N/A-ERROR ═════
def p20_sidecar_missing():
    """Test _hedge_line with empty text (sidecar missing) → must contain 'N/A-ERROR' NOT digit."""
    sys.path.insert(0, str(REPO / "scripts"))
    from digest_summary_v2 import _hedge_line
    # Legacy evidence · empty sidecar
    empty_result = _hedge_line("")
    # POST-FIX expected: contains N/A-ERROR AND no digit
    has_na = "N/A-ERROR" in empty_result
    has_digit = any(c.isdigit() for c in empty_result)
    ok = has_na and not has_digit
    detail = f"empty-sidecar result='{empty_result}' · has_N/A-ERROR={has_na} · has_digit={has_digit}"
    if ok:
        return ("PASS", detail)
    return ("FAIL", detail)


# ═════ p21 PX-NA → WATCH ═════
def p21_px_na_watch():
    """Verify APR 09-08 star (px_now=None) → WATCH direction in digest body."""
    sys.path.insert(0, str(REPO / "scripts"))
    from digest_summary_v2 import build_v2_digest
    body = build_v2_digest("2026-09-08")
    # APR should NOT be in ⭐-PRE block · SHOULD be in WATCH-PX-PENDING block
    has_apr_watch = "WATCH-PX-PENDING" in body and "APR" in body
    # Also check no APR line with "→ PRE" in body
    apr_pre_line = re.search(r"APR.*→\s*PRE\b", body)
    is_still_pre = apr_pre_line is not None
    ok = has_apr_watch and not is_still_pre
    detail = f"APR-in-WATCH-block={has_apr_watch} · APR-still-PRE={is_still_pre}"
    return ("PASS" if ok else "FAIL", detail)


# ═════ p22 COUNT ≡ PRINTED (V3.5l parser fix) ═════
def p22_count_printed():
    """Verify ⭐-PRE header-N matches printed lines + tail names if >TOP_K.
    V3.5l fix: proper block extraction stops at next section marker (⭐-PRE ends
    when 🔻/POST-DUMP/⏸/📒/🚪/━━ appears · not on double-newline).
    """
    sys.path.insert(0, str(REPO / "scripts"))
    from digest_summary_v2 import build_v2_digest
    body = build_v2_digest("2026-09-08")
    lines = body.split("\n")
    # Find ⭐-PRE header line
    header_idx = None; header_n = None
    for i, l in enumerate(lines):
        m = re.match(r"⭐-PRE\s+\((\d+)\):", l)
        if m: header_idx = i; header_n = int(m.group(1)); break
    if header_idx is None:
        return ("N/A", "no ⭐-PRE block found")
    # Collect block until next section marker OR blank-then-new-section
    SECTION_MARKERS = ("🔻", "POST-DUMP", "⏸", "📒", "🚪", "━━", "GOM-H:", "HEDGE:", "KHO:", "FRESH:", "RÒNG:", "👁")
    star_lines = []; tail_syms = []; tail_n = 0
    for l in lines[header_idx+1:]:
        stripped = l.strip()
        if not stripped: continue  # skip blank
        # Next section marker → block ended
        if any(stripped.startswith(m) for m in SECTION_MARKERS): break
        # Tail line "(+N nữa: SYM·SYM·SYM)"
        m_tail = re.match(r"\(\+(\d+) nữa:\s+([^)]+)\)", stripped)
        if m_tail:
            tail_n = int(m_tail.group(1))
            tail_syms = m_tail.group(2).split("·")
            continue
        # Otherwise a star line (has symbol at start of stripped)
        star_lines.append(stripped)
    printed_n = len(star_lines)
    TOP_K = 6
    if header_n <= TOP_K:
        ok = (printed_n == header_n) and (tail_n == 0)
        detail = f"header={header_n} printed={printed_n} · no-tail (≤{TOP_K}) · match={ok}"
    else:
        ok = (printed_n == TOP_K) and (tail_n == header_n - TOP_K) and (len(tail_syms) == tail_n)
        detail = f"header={header_n} shown={printed_n}+tail={tail_n} names={len(tail_syms)} · match={ok}"
    return ("PASS" if ok else "FAIL", detail)


def main():
    print("═" * 60)
    print("HARNESS p20-p22 · V3.5k · TUYỂN BẰNG DI-SẢN")
    print("═" * 60)
    results = []
    for pin, disan, fn in [
        ("p20", "09-08 watchlist artifact missing (V3.5i Path bug)", p20_sidecar_missing),
        ("p21", "09-08 APR px_now=None (loài mới không có klines)", p21_px_na_watch),
        ("p22", "demo-5 header=11 vs printed=8 (slice-[:8])", p22_count_printed),
    ]:
        status, detail = fn()
        marker = "✅" if status == "PASS" else ("⚠" if status == "N/A" else "❌")
        print(f"  {marker} {pin} · {disan}")
        print(f"      {detail}")
        _log(pin, disan, f"{status}:{detail[:80]}", _sha8(f"{pin}{disan}{status}"))
        results.append((pin, status))

    n_pass = sum(1 for _, s in results if s == "PASS")
    print(f"\n[SUMMARY] {n_pass}/{len(results)} PASS")

    # NIÊM fixture_master_md5
    fix_p = REPO / "tests/fixtures/parity/FIXTURE_MASTER_MD5.md"
    if fix_p.exists():
        md5 = hashlib.md5(fix_p.read_bytes()).hexdigest()[:12]
        print(f"[FIXTURE-MASTER] md5={md5} · path={fix_p}")
    else:
        # Create fixture master file listing p20/p21/p22 expected outcomes
        fix_p.parent.mkdir(parents=True, exist_ok=True)
        content = f"""# FIXTURE MASTER · V3.5k · KÝ {datetime.now(timezone.utc).date()}

## p20 SIDECAR-MISSING → N/A-ERROR
Expected: `_hedge_line("")` returns string containing "N/A-ERROR" · NO digit chars.
Legacy evidence: 09-08 watchlist Path-bug crash → sidecar missing.

## p21 PX-NA → WATCH
Expected: APR target=09-08 rendered as `⏸ WATCH [PX-PENDING]` NOT `→ PRE`.
Legacy evidence: APR (new loài · no klines) picked up as star 09-08.

## p22 COUNT ≡ PRINTED
Expected: ⭐-PRE header N = printed_lines + tail (+K nữa: ...) with K=N-TOP_K.
TOP_K = 6 · tail lists ALL remaining names.
Legacy evidence: demo-5 body 09-08 header=11 printed=8 (slice [:8]).

## FIXTURE MD5 NIÊM
This file's md5 = fixture_master · in footer digest as `fixture_master=<md5[:12]>`.
"""
        fix_p.write_text(content, encoding="utf-8")
        md5 = hashlib.md5(fix_p.read_bytes()).hexdigest()[:12]
        print(f"[FIXTURE-MASTER CREATED] md5={md5} · path={fix_p}")
    return 0 if n_pass == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
