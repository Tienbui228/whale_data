"""hedge_v2_postcheck · γ7 · sáng D+1 đọc 4 dấu chân của chân watchlist.

Đọc:
  1. artifact: data/artifacts/tg_final_watchlist_<T>.txt + .jsonl
  2. cron log: [SENT] watchlist ok=True target=<T> trong data/export/watchlist_cron.log
     (nếu không có · check data/logs/*.log · watchlist_daily invocations)
  3. bell_journal: renderer="watchlist" · target_date=<T> · ok=True
  4. LEG-SENT trong log nếu có

+ đọc hedge_v2_journal.jsonl · nếu có ok=False → KÍCH-vì-chân-HEDGE fail

Usage:
  python3 scripts/hedge_v2_postcheck.py --target 2026-09-22

Exit code:
  0 · tất cả 4 dấu chân + hedge_v2_journal ok (no U7 block)
  1 · thiếu 1+ dấu chân hoặc journal có KÍCH-vì-chân-HEDGE

If exit 1 · operator can revert: đặt HEDGE_V2=0 trong .env → chạy tay watchlist_daily
tối tối đó. Không sửa artifact tay.
"""
from __future__ import annotations
import os, sys, json, argparse, re
from pathlib import Path

_REPO = Path("/root/Data_back_test/whale_data") if os.name != "nt" \
        else Path(r"D:/Data back test/whale_data")

try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except AttributeError: pass  # L-66-OK

ART_DIR = _REPO / "data/artifacts"
BELL_JOURNAL = _REPO / "data/logs/bell_journal.jsonl"
HEDGE_JOURNAL = _REPO / "data/logs/hedge_v2_journal.jsonl"
CRON_LOG = _REPO / "data/export/watchlist_cron.log"


def check_footprint(target: str) -> dict:
    """Đo 4 dấu chân của chân watchlist tại target."""
    results = {}

    # 1. Artifact pair
    art_txt = ART_DIR / f"tg_final_watchlist_{target}.txt"
    art_jsonl = ART_DIR / f"tg_final_watchlist_{target}.jsonl"
    results["artifact_txt"] = art_txt.exists()
    results["artifact_jsonl"] = art_jsonl.exists()
    if art_txt.exists():
        results["artifact_size"] = art_txt.stat().st_size
    if art_jsonl.exists():
        try:
            entries = [json.loads(l) for l in art_jsonl.read_text(encoding="utf-8").splitlines() if l.strip()]
            results["artifact_jsonl_rows"] = len(entries)
            results["artifact_product"] = entries[0].get("product", "?") if entries else "?"
        except Exception as e:
            results["artifact_jsonl_err"] = str(e)

    # 2. Cron log [SENT] pattern
    if CRON_LOG.exists():
        content = CRON_LOG.read_text(encoding="utf-8", errors="replace")
        pat = rf"\[SENT\] watchlist ok=True.*target={re.escape(target)}"
        m = re.search(pat, content)
        results["log_sent_found"] = bool(m)
        if m:
            results["log_sent_line"] = m.group(0)[:100]
    else:
        results["log_sent_found"] = False
        results["log_sent_err"] = f"cron log missing: {CRON_LOG}"

    # 3. Bell journal
    if BELL_JOURNAL.exists():
        found_bell = False
        found_bell_hedge = False
        for ln in BELL_JOURNAL.read_text(encoding="utf-8").splitlines():
            if not ln.strip(): continue
            try: e = json.loads(ln)
            except json.JSONDecodeError: continue
            if e.get("renderer") == "watchlist" and e.get("target_date") == target and e.get("ok"):
                found_bell = True
                if e.get("product") == "hedge_v2":
                    found_bell_hedge = True
        results["bell_journal_ok"] = found_bell
        results["bell_journal_product_hedge_v2"] = found_bell_hedge
    else:
        results["bell_journal_ok"] = False

    # 4. hedge_v2_journal check · KÍCH-vì-chân-HEDGE
    results["hedge_journal_ok"] = True
    results["hedge_journal_kich_label"] = False
    if HEDGE_JOURNAL.exists():
        for ln in HEDGE_JOURNAL.read_text(encoding="utf-8").splitlines():
            if not ln.strip(): continue
            try: e = json.loads(ln)
            except json.JSONDecodeError: continue
            if e.get("target_date") != target: continue
            if not e.get("ok"):
                results["hedge_journal_ok"] = False
                if e.get("leg_fail_label") == "KÍCH-vì-chân-HEDGE":
                    results["hedge_journal_kich_label"] = True
                    results["hedge_journal_fail_reason"] = e.get("fail_reason", "")

    return results


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", required=True, help="YYYY-MM-DD")
    args = ap.parse_args()

    r = check_footprint(args.target)

    print(f"═══ hedge_v2 postcheck · target={args.target} ═══")
    print()
    print(f"1. artifact_txt:                     {'OK' if r.get('artifact_txt') else 'MISSING'}"
          f" ({r.get('artifact_size', '?')} bytes)")
    print(f"   artifact_jsonl:                  {'OK' if r.get('artifact_jsonl') else 'MISSING'}"
          f" ({r.get('artifact_jsonl_rows', '?')} rows · product={r.get('artifact_product', '?')})")
    print(f"2. log [SENT] watchlist ok=True:    {'OK' if r.get('log_sent_found') else 'MISSING'}")
    if r.get("log_sent_line"): print(f"   → {r['log_sent_line']}")
    print(f"3. bell_journal renderer=watchlist:  {'OK' if r.get('bell_journal_ok') else 'MISSING'}"
          f" (product=hedge_v2: {'yes' if r.get('bell_journal_product_hedge_v2') else 'no'})")
    print(f"4. hedge_v2_journal ok:              {'OK' if r.get('hedge_journal_ok') else 'FAIL'}")
    if r.get("hedge_journal_kich_label"):
        print(f"   ⚠ KÍCH-vì-chân-HEDGE fail_reason: {r.get('hedge_journal_fail_reason')}")

    ok_all = all([
        r.get("artifact_txt"), r.get("artifact_jsonl"),
        r.get("log_sent_found"), r.get("bell_journal_ok"),
        r.get("hedge_journal_ok"),
    ])

    print()
    print(f"═══ {'PASS · sẵn sàng chạy đêm sau' if ok_all else 'FAIL · xem lại + revert HEDGE_V2=0 nếu cần'} ═══")
    sys.exit(0 if ok_all else 1)


if __name__ == "__main__":
    main()
