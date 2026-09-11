"""POSTCHECK GATE-D · V3.5s · chạy SAU send · đọc artifact ĐÃ GỬI.

Input: target date (YYYY-MM-DD)
Reads:
  - data/artifacts/master_concat_<target>.txt (body ĐÃ GỬI · persisted by digest_summary_v2)
  - tests/harness/harness_p20_p22_v3_5k.py --only post-ledger (rebuild body live · KHÔNG dùng)
    → thay bằng: chạy p21/p22 logic đơn giản trên body ĐÃ GỬI (đọc file, không rebuild)

Output: dict {postcheck_ok: bool, p21: PASS/FAIL/N/A, p22: PASS/FAIL/N/A, flag: str}
  Ghi vào preview_journal entry của target · thêm cờ [POSTCHECK-FAIL <pin>] nếu fail.

Không tự append journal — caller (master_preview_send.main) append.
"""
from __future__ import annotations
import sys, os, re, json, hashlib
from pathlib import Path
from datetime import datetime, timezone

try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except: pass  # L-66-OK

REPO = Path("/root/Data_back_test/whale_data") if os.name != "nt" else Path(r"D:/Data back test/whale_data")
ART_DIR = REPO / "data/artifacts"
SB_LOG = REPO / "data/logs/harness_sabotage.log"


def _log_sab(pin: str, disan: str, verdict: str, sha: str):
    ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
    SB_LOG.parent.mkdir(parents=True, exist_ok=True)
    with SB_LOG.open("a", encoding="utf-8") as f:
        f.write(f"{ts}\t{pin}\t{disan}\t{verdict}\t{sha}\n")


def _sha8(s: str) -> str:
    return hashlib.md5(s.encode()).hexdigest()[:8]


SECTION_MARKERS_DEFAULT = ("━━", "⭐", "🔻", "POST-DUMP", "⏸ WATCH", "📒", "🚪",
                            "GOM-H:", "HEDGE:", "KHO:", "FRESH:", "RÒNG:", "👁")


def _extract_block(body: str, header_needle: str) -> str | None:
    """Cắt block từ header_needle tới section marker kế tiếp.
    · Header line = line CHỨA header_needle · nội dung block = lines sau header
    · End = line KHÔNG-INDENT bắt đầu bằng section marker (indent-check tránh
      match content của chính block, vd `⏸ WATCH [PX-PENDING]: APR` là content L32,
      không phải header)
    Return None nếu không tìm thấy header."""
    lines = body.split("\n")
    start = -1
    for i, l in enumerate(lines):
        if header_needle in l:
            start = i + 1
            break
    if start < 0: return None
    end = len(lines)
    for j in range(start, len(lines)):
        raw = lines[j]
        stripped = raw.strip()
        if not stripped: continue
        # Section markers CHỈ tính khi line KHÔNG có leading whitespace
        # (content lines thường indented ≥3 spaces · header lines flush-left)
        if raw != raw.lstrip():   # có leading whitespace → content line, skip
            continue
        for mk in SECTION_MARKERS_DEFAULT:
            if stripped.startswith(mk):
                end = j; break
        if end != len(lines): break
    return "\n".join(lines[start:end])


def _check_p21_apr_watch(body: str) -> tuple[str, str]:
    """P21 · F1 block-scope · APR ghim cứng lần này (nợ: chủ thể động).
    Cắt đúng khối WATCH-PX-PENDING · tìm APR TRONG khối đó.
    · APR không có bất kỳ đâu trong body → N/A (không có chủ thể chấm)
    · APR có trong body nhưng chỉ ở KHO/FRESH/⭐-PRE (không ở WATCH block) → tuỳ:
      - Ở ⭐-PRE (→ PRE) → FAIL (APR không được routing PX-PENDING)
      - Ở KHO/FRESH thôi, không WATCH → N/A (chủ thể tồn tại nhưng không ở routing)
    · APR TRONG WATCH block · KHÔNG ở ⭐-PRE → PASS
    """
    if "APR" not in body:
        return ("N/A", "APR-not-in-body")
    # Cắt WATCH-PX-PENDING block
    watch_block = _extract_block(body, "WATCH-PX-PENDING")
    apr_in_watch = watch_block is not None and re.search(r"\bAPR\b", watch_block) is not None
    # APR trong ⭐-PRE block (routing sai)
    pre_block = _extract_block(body, "⭐-PRE")
    apr_in_pre = pre_block is not None and re.search(r"\bAPR\b.*→\s*PRE\b", pre_block) is not None
    if apr_in_pre:
        return ("FAIL", f"APR-still-in-⭐-PRE (routing sai) · APR-in-WATCH={apr_in_watch}")
    if apr_in_watch:
        return ("PASS", f"APR-in-WATCH-block=True · APR-in-⭐-PRE=False")
    # APR có trong body nhưng không WATCH không PRE → chỉ ở KHO/FRESH
    return ("N/A", "APR-in-body-nhưng-không-trong-WATCH-cũng-không-⭐-PRE (KHO/FRESH only)")


def _check_p22_star_pre_count(body: str) -> tuple[str, str]:
    """P22 · ⭐-PRE header-N ≡ printed lines + tail names."""
    lines = body.split("\n")
    header_idx = None; header_n = None
    for i, l in enumerate(lines):
        m = re.match(r"⭐-PRE\s+\((\d+)\):", l)
        if m: header_idx = i; header_n = int(m.group(1)); break
    if header_idx is None:
        return ("N/A", "no ⭐-PRE block found in body ĐÃ GỬI")
    SECTION_MARKERS = ("🔻", "POST-DUMP", "⏸", "📒", "🚪", "━━",
                       "GOM-H:", "HEDGE:", "KHO:", "FRESH:", "RÒNG:", "👁")
    star_lines = []; tail_syms = []; tail_n = 0
    for l in lines[header_idx+1:]:
        stripped = l.strip()
        if not stripped: continue
        if any(stripped.startswith(m) for m in SECTION_MARKERS): break
        m_tail = re.match(r"\(\+(\d+) nữa:\s+([^)]+)\)", stripped)
        if m_tail:
            tail_n = int(m_tail.group(1))
            tail_syms = m_tail.group(2).split("·")
            continue
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


def postcheck(target: str) -> dict:
    """Run p21+p22 postcheck on ART_DIR/master_concat_<target>.txt · return summary dict."""
    concat_p = ART_DIR / f"master_concat_{target}.txt"
    if not concat_p.exists():
        # V3.5s F2 · artifact vắng (đêm KÍCH không send) = vacuous OK
        # Không có gì để hậu-kiểm ≠ hậu-kiểm fail. Cờ N/A riêng để log.
        return {
            "postcheck_ok": True,
            "target": target,
            "reason": f"artifact missing (đêm KÍCH/SKIP · không hậu-kiểm được): {concat_p.name}",
            "p21": "N/A", "p22": "N/A",
            "flag": "[POSTCHECK-N/A artifact-missing]",
        }
    body = concat_p.read_bytes().decode("utf-8", errors="replace")
    body_md5 = hashlib.md5(concat_p.read_bytes()).hexdigest()[:12]

    p21_status, p21_detail = _check_p21_apr_watch(body)
    p22_status, p22_detail = _check_p22_star_pre_count(body)

    _log_sab("p21-post", f"target={target} · postcheck body ĐÃ GỬI",
             f"{p21_status}:{p21_detail[:80]}", _sha8(f"p21-post-{target}-{p21_status}"))
    _log_sab("p22-post", f"target={target} · postcheck body ĐÃ GỬI",
             f"{p22_status}:{p22_detail[:80]}", _sha8(f"p22-post-{target}-{p22_status}"))

    # V3.5s D3: postcheck_ok = tất cả pin PASS · N/A cũng OK (thiếu chủ thể không phải fail)
    fails = []
    if p21_status == "FAIL": fails.append("p21")
    if p22_status == "FAIL": fails.append("p22")
    postcheck_ok = len(fails) == 0
    flag = "" if postcheck_ok else f"[POSTCHECK-FAIL {','.join(fails)}]"

    return {
        "postcheck_ok": postcheck_ok,
        "target": target,
        "body_md5": body_md5,
        "p21": p21_status, "p21_detail": p21_detail,
        "p22": p22_status, "p22_detail": p22_detail,
        "flag": flag,
    }


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", required=True)
    args = ap.parse_args()
    result = postcheck(args.target)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["postcheck_ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
