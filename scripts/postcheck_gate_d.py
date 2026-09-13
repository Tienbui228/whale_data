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
    """P21 · V1.3 tái định đích: TOKEN có px_now=None PHẢI mang direction WATCH và
    KHÔNG mang PRE, BẤT KỂ nằm khối nào.

    Cơ chế:
    · Scan mọi dòng token trong body (tất cả khối)
    · Detect px_now=None qua marker "⏸" trong dòng hoặc "[PX-PENDING]"
    · Token với px marker "⏸/PX-PENDING" phải KHÔNG có "→ PRE" trong dòng đó
    · N/A khi không có chủ thể (token nào có px marker) trong body
    · Backward-compat V1.2: giữ semantic APR ghim cứng nếu V1.3 markers không có

    FAIL: bất kỳ token nào có "⏸" hoặc "[PX-PENDING]" mà dòng cũng có "→ PRE"
    PASS: tất cả token px-missing đều routing đúng (WATCH direction)
    N/A: không có token px-missing trong body (không có chủ thể chấm)
    """
    lines = body.split("\n")
    px_missing_lines = [l for l in lines
                        if ("⏸" in l or "[PX-PENDING]" in l) and re.search(r"\S+", l)]
    if not px_missing_lines:
        # V1.2 fallback: APR ghim cứng semantic (giữ backward-compat)
        if "APR" not in body:
            return ("N/A", "no px-missing token in body")
        watch_block = _extract_block(body, "WATCH-PX-PENDING")
        apr_in_watch = watch_block is not None and re.search(r"\bAPR\b", watch_block) is not None
        pre_block = _extract_block(body, "⭐-PRE")
        apr_in_pre = pre_block is not None and re.search(r"\bAPR\b.*→\s*PRE\b", pre_block) is not None
        if apr_in_pre:
            return ("FAIL", f"[V1.2-fallback] APR-in-⭐-PRE · APR-in-WATCH={apr_in_watch}")
        if apr_in_watch:
            return ("PASS", f"[V1.2-fallback] APR-in-WATCH-block=True · APR-in-⭐-PRE=False")
        return ("N/A", "[V1.2-fallback] APR-not-in-WATCH-nor-⭐-PRE")

    # V1.3: check every px-missing line has NO "→ PRE"
    violations = []
    for l in px_missing_lines:
        if re.search(r"→\s*PRE\b", l):
            violations.append(l.strip()[:60])
    if violations:
        return ("FAIL",
                f"V1.3: {len(violations)} px-missing token(s) still routing → PRE · sample: {violations[0]}")
    return ("PASS", f"V1.3: {len(px_missing_lines)} px-missing token(s), tất cả routing WATCH (không có → PRE)")


def _check_p22_star_pre_count(body: str) -> tuple[str, str]:
    """P22 · V1.3 tái định đích: MỌI khối có header đếm, header ≡ số dòng token in
    + số tên trong `(+k nữa: …)`. Lệch bất kỳ khối nào = FAIL.

    Khối có header đếm:
    - ⭐-PRE (n): (V1.2)
    - 🔻 XẢ-WATCH+XẢ (n): (V1.2 + V1.3)
    - POST-DUMP+🌊 (n): (V1.2 + V1.3)
    - ⏸ WATCH-PX-PENDING (n): (V1.2)
    - ── X · ... ── (n) (V1.3 species blocks: A/B/C/D/E/? /CHƯA XẾP)

    Không tính:
    - Dòng nhắc `(→ xem B)` không phải dòng token
    - Dòng "(none)" là placeholder khi block rỗng
    """
    lines = body.split("\n")
    SECTION_MARKERS = ("🔻", "POST-DUMP", "⏸", "📒", "🚪", "━━", "──",
                       "GOM-H:", "HEDGE:", "KHO:", "FRESH:", "RÒNG:", "👁",
                       "⭐-PRE", "🎯", "⛔", "[loài", "[DẢI-NỢ", "[DAO-DEFERRED",
                       "cites:", "concat-seal", "ledger_state")

    # Patterns for header-with-count
    HEADER_PATTERNS = [
        (r"⭐-PRE\s+\((\d+)\):", "⭐-PRE"),
        (r"🔻\s*XẢ-WATCH.*?\((\d+)\):", "🔻 XẢ-WATCH"),
        (r"POST-DUMP.*?\((\d+)\):", "POST-DUMP"),
        (r"⏸\s*WATCH-PX-PENDING\s+\((\d+)\):", "⏸ WATCH-PX-PENDING"),
        # V1.3 species headers
        (r"──\s*A\s+·.*──\s*\((\d+)\)", "── A ──"),
        (r"──\s*B\s+·.*──\s*\((\d+)\)", "── B ──"),
        (r"──\s*C\s+·.*──\s*\((\d+)\)", "── C ──"),
        (r"──\s*D\s+·.*──\s*\((\d+)\)", "── D ──"),
        (r"──\s*E\s+·.*──\s*\((\d+)\)", "── E ──"),
        (r"──\s*\?\s+CHƯA NHÌN ĐƯỢC\s*──\s*\((\d+)\)", "── ? ──"),
        (r"──\s*CHƯA XẾP LOÀI\s*──\s*\((\d+)\)", "── CHƯA XẾP ──"),
    ]

    all_blocks = []   # (header_label, header_n, header_idx)
    for i, l in enumerate(lines):
        for pat, label in HEADER_PATTERNS:
            m = re.search(pat, l)
            if m:
                all_blocks.append((label, int(m.group(1)), i)); break

    if not all_blocks:
        return ("N/A", "no counted-header block found in body")

    fails = []
    details = []
    TOP_K = 6
    for label, header_n, header_idx in all_blocks:
        # Extract token lines + tail syms until next section marker
        block_lines = []; tail_syms = []; tail_n = 0
        for l in lines[header_idx+1:]:
            stripped = l.strip()
            if not stripped: continue
            # Check for another header (any pattern)
            is_header = any(re.search(pat, l) for pat, _ in HEADER_PATTERNS)
            if is_header: break
            # Check for section marker
            if any(stripped.startswith(m) for m in SECTION_MARKERS): break
            # Skip "(none)" placeholder for empty blocks
            if stripped == "(none)":
                continue
            # Skip "→ xem X" hint lines (not counted per p72)
            if stripped.startswith("(→"): continue
            m_tail = re.match(r"\(\+(\d+) nữa:\s+([^)]+)\)", stripped)
            if m_tail:
                tail_n = int(m_tail.group(1))
                tail_syms = m_tail.group(2).split("·")
                continue
            block_lines.append(stripped)
        printed_n = len(block_lines)
        # V1.3 p22: TOP_K-AGNOSTIC · yêu cầu header_n = printed_n + tail_n
        # (Blocks CÓ THỂ truncate to TOP_K + tail, HOẶC print-all — cả hai đều OK
        #  miễn là header đếm ≡ tổng số token in + tail names)
        if header_n == 0:
            ok = (printed_n == 0) and (tail_n == 0)
            det = f"[{label}] header=0 printed={printed_n} ok={ok}"
        else:
            # Case 1: block truncated · printed=TOP_K + tail names
            # Case 2: block print-all · printed=header_n · no tail
            # Rule chung: printed + tail == header AND (if tail_n > 0, tail_syms count matches)
            total_accounted = printed_n + tail_n
            tail_names_ok = (tail_n == 0) or (len(tail_syms) == tail_n)
            ok = (total_accounted == header_n) and tail_names_ok
            det = f"[{label}] header={header_n} printed={printed_n}+tail={tail_n} names={len(tail_syms)} ok={ok}"
        details.append(det)
        if not ok: fails.append(label)

    if fails:
        return ("FAIL", f"V1.3: {len(fails)} block(s) fail: {','.join(fails)} · " + " | ".join(details[:5]))

    # X3 · p22 phải có RĂNG: nếu MỌI khối loài (── X ──) rỗng → trả N/A, KHÔNG PASS
    # (Rỗng-hết = không có chủ thể chấm, không phải "đúng"). Direction blocks
    # (⭐-PRE, 🔻, POST-DUMP, ⏸) không tính vào rule này.
    species_labels = {"── A ──","── B ──","── C ──","── D ──","── E ──","── ? ──","── CHƯA XẾP ──"}
    species_blocks_all = [(lb, hn) for lb, hn, _ in all_blocks if lb in species_labels]
    if species_blocks_all and all(hn == 0 for _, hn in species_blocks_all):
        return ("N/A",
                f"V1.3: mọi khối loài rỗng ({len(species_blocks_all)} khối header=0) — không có chủ thể chấm")

    return ("PASS", f"V1.3: {len(all_blocks)} block(s) all match · " + " | ".join(details[:5]))


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
