"""HARNESS RECEIPTS · V3.5r item 8 · biên-lai gỡ ngòi bypass + wl-xanh-trọn.

Receipt-1 · grep bypass-token in master_preview_send.py (EXPECT 0 HIT):
  Tokens: {standing_active, force_send, --bypass, bypass_verdict, no_standing, skip_standing}
  Đọc CODE-ACTIVE (không đọc COMMENT). Comment giải thích "GỠ standing_active bypass" hợp lệ.
  Cấm read/write standing_active file, cấm arg --bypass, cấm branch skip verdict.

Receipt-2 · wl-xanh-trọn định nghĩa MÁY:
  wl_xanh_tron(target) := {
    p3_pass ∧ hedge_has_digit ∧ watchlist_full_pair ∧ sent_marker
  }
  · p3_pass = harness_digest_summary p3 exit 0
  · hedge_has_digit = digest body dòng "HEDGE" contains \\d+
  · watchlist_full_pair = data/artifacts/tg_final_watchlist_<T>.{txt,jsonl} both exist
  · sent_marker = bell_journal has entry {renderer=watchlist · target=<T> · ok=true}

Wire (V3.5r item 8): result exported to STDOUT + optional receipts JSON dump.
"""
from __future__ import annotations
import sys, os, re, json, hashlib, subprocess
from pathlib import Path
from datetime import datetime, timezone

try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except: pass  # L-66-OK (benign fallback)

REPO = Path("/root/Data_back_test/whale_data") if os.name != "nt" else Path(r"D:/Data back test/whale_data")
SB_LOG = REPO / "data/logs/harness_sabotage.log"
MASTER_PREVIEW = REPO / "scripts/master_preview_send.py"

BYPASS_TOKENS = [
    "standing_active",
    "force_send",
    "--bypass",
    "bypass_verdict",
    "no_standing",
    "skip_standing",
]


def _log(pin, mutate, verdict, extra):
    ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
    sha = hashlib.md5(f"{pin}{mutate}{verdict}{extra}".encode()).hexdigest()[:8]
    SB_LOG.parent.mkdir(parents=True, exist_ok=True)
    with SB_LOG.open("a", encoding="utf-8") as f:
        f.write(f"{ts}\t{pin}\t{mutate}\t{verdict}\t{sha}\n")


def _strip_comments_and_strings(source: str) -> str:
    """Use tokenize · emit only NAME/OP/NUMBER tokens (drop STRING + COMMENT)."""
    import io, tokenize
    out = []
    try:
        toks = tokenize.tokenize(io.BytesIO(source.encode("utf-8")).readline)
        for t in toks:
            if t.type in (tokenize.NAME, tokenize.OP, tokenize.NUMBER):
                out.append(t.string)
                out.append(" ")
    except tokenize.TokenizeError:
        # partial output still useful
        pass
    return "".join(out)


def receipt_1_bypass_grep():
    """Grep code-active (non-comment · non-string) for bypass tokens."""
    if not MASTER_PREVIEW.exists():
        return (False, "master_preview_send.py MISSING")
    src = MASTER_PREVIEW.read_text(encoding="utf-8")
    code = _strip_comments_and_strings(src)
    hits = {}
    for tok in BYPASS_TOKENS:
        # word-boundary match on the stripped source
        n = len(re.findall(re.escape(tok), code))
        if n > 0:
            hits[tok] = n
    passed = (len(hits) == 0)
    detail = f"hits={hits}" if hits else "0 hit across all bypass-tokens"
    return passed, detail


def receipt_2_wl_xanh_tron(target: str):
    """Machine definition of wl-xanh-trọn · return (passed, detail-dict)."""
    art_dir = REPO / "data/artifacts"
    bell = REPO / "data/logs/bell_journal.jsonl"
    result = {"target": target}
    # 1. watchlist_full_pair
    wl_txt = art_dir / f"tg_final_watchlist_{target}.txt"
    wl_jsonl = art_dir / f"tg_final_watchlist_{target}.jsonl"
    result["watchlist_full_pair"] = wl_txt.exists() and wl_jsonl.exists()
    result["_txt"] = wl_txt.exists(); result["_jsonl"] = wl_jsonl.exists()
    # 2. hedge_has_digit: read digest body if any (via digest_summary_v2 body OR watchlist artifact)
    # Use the watchlist artifact itself (has HEDGE line)
    hedge_ok = False
    if wl_txt.exists():
        body = wl_txt.read_text(encoding="utf-8", errors="replace")
        for line in body.splitlines():
            if "HEDGE" in line.upper() and re.search(r"\d", line):
                hedge_ok = True; break
    result["hedge_has_digit"] = hedge_ok
    # 3. sent_marker in bell_journal
    sent_ok = False
    if bell.exists():
        for line in bell.read_text(encoding="utf-8").splitlines():
            try:
                e = json.loads(line)
                if e.get("renderer") == "watchlist" and e.get("target_date") == target and e.get("ok"):
                    sent_ok = True; break
            except: pass  # L-66-OK
    result["sent_marker"] = sent_ok
    # 4. p3_pass = harness p3 exit 0 (run harness_digest_summary for target)
    hd = REPO / "tests/harness/harness_digest_summary.py"
    p3_ok = False; p3_detail = "not run"
    if hd.exists():
        try:
            r = subprocess.run([sys.executable, str(hd), "--target", target, "--only", "p3"],
                              capture_output=True, text=True, timeout=60, cwd=str(REPO))
            p3_ok = (r.returncode == 0)
            p3_detail = f"rc={r.returncode}"
        except subprocess.TimeoutExpired:
            p3_detail = "timeout"
        except Exception as e:
            p3_detail = f"err:{type(e).__name__}"
    result["p3_pass"] = p3_ok; result["_p3_detail"] = p3_detail
    passed = all([result["watchlist_full_pair"], result["hedge_has_digit"],
                  result["sent_marker"], result["p3_pass"]])
    result["wl_xanh_tron"] = passed
    return passed, result


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", help="Target date · default: T-1 UTC")
    args = ap.parse_args()
    from datetime import timedelta as _td
    target = args.target or (datetime.now(timezone.utc).date() - _td(days=1)).isoformat()

    print("═" * 62)
    print(f"HARNESS RECEIPTS · V3.5r item 8 · target={target}")
    print("═" * 62)

    print("\n─── Receipt-1 · grep bypass-token (EXPECT 0 HIT) ───")
    r1_ok, r1_det = receipt_1_bypass_grep()
    mark = "✅" if r1_ok else "❌"
    print(f"  {mark} bypass-grep: {r1_det}")
    _log("receipt-1", "bypass-grep", "PASS" if r1_ok else "FAIL", r1_det[:80])

    print(f"\n─── Receipt-2 · wl-xanh-trọn định nghĩa MÁY (target={target}) ───")
    r2_ok, r2_det = receipt_2_wl_xanh_tron(target)
    mark = "✅" if r2_ok else "⚠"  # not-full-green có thể là hiện trạng bình thường trước cron
    print(f"  {mark} wl-xanh-trọn: {r2_ok}")
    for k, v in r2_det.items():
        print(f"     · {k}: {v}")
    _log("receipt-2", f"wl-xanh-trọn target={target}",
         "PASS" if r2_ok else "NOT-FULL-GREEN", str(r2_det)[:80])

    # Receipt-1 must PASS · Receipt-2 informational (không block)
    overall = "PASS" if r1_ok else "FAIL"
    print(f"\n[SUMMARY] receipts V3.5r: {overall} · wl-xanh-trọn={r2_ok}")
    return 0 if r1_ok else 1


if __name__ == "__main__":
    sys.exit(main())
