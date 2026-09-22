"""dryrun_hedge_v2_pipeline · AW-β4 · pipeline khô cho HEDGE v2 renderer.

Steps · KHÔNG gọi tg_send:
  1. compose_body(target) · read events (provenance) · render
  2. U7 gate check (len ≤ 4096 · HTML whitelist)
  3. Write audit CSV + registry_md5 sanity
  4. Write dry artifacts (tg_final_watchlist_<T>.txt/jsonl) · giả lập sender
  5. Đo tg_len · biên tới 4096 (HEDGE là chân master · vượt 4096 → master SKIP)

Usage:
  python3 scripts/dryrun_hedge_v2_pipeline.py --targets 2026-09-15,...,2026-09-20

Doctrine §KỶ-LUẬT #12: dry ≥5 đêm PASS trước khi ràng master (γ).
"""
from __future__ import annotations
import os, sys, argparse
from pathlib import Path

_REPO = Path("/root/Data_back_test/whale_data") if os.name != "nt" \
        else Path(r"D:/Data back test/whale_data")
sys.path.insert(0, str(_REPO / "scripts"))

import hedge_v2 as hv

try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except AttributeError: pass  # L-66-OK

TG_LIMIT = 4096


def dry_one(target: str) -> dict:
    """Chạy 5 bước dry cho target. Trả dict metrics."""
    m = {"target": target, "compose_ok": False, "u7_ok": False,
         "csv_ok": False, "artifact_ok": False,
         "tg_len": 0, "reg": 0, "u7_reason": "", "csv_md5": ""}
    try:
        body, meta = hv.compose_body(target, report_only=True, write_audit=True)
        m["compose_ok"] = True
        m["tg_len"] = meta.get("tg_len", 0)
        m["reg"] = meta.get("n_reg", 0)
        m["csv_md5"] = meta.get("registry_md5", "")
        m["bien_4096"] = TG_LIMIT - m["tg_len"]
    except Exception as e:
        m["error"] = f"compose: {e}"
        return m

    # β2 · U7 gate
    ok, reason = hv.u7_gate(body)
    m["u7_ok"] = ok
    m["u7_reason"] = reason if not ok else ""

    # β-fix4 · CSV must exist + md5 match content
    csv_p = hv.ART_DIR / f"hedge_registry_{target}.csv"
    md5_p = hv.ART_DIR / f"hedge_registry_{target}.md5"
    if csv_p.exists() and md5_p.exists():
        import hashlib
        actual = hashlib.md5(csv_p.read_bytes()).hexdigest()
        expected = md5_p.read_text(encoding="utf-8").strip()
        m["csv_ok"] = actual == expected
    else:
        m["csv_ok"] = False

    # Dry artifact dump via send_hedge_v2(dry_run=True)
    r = hv.send_hedge_v2(target, body, meta, dry_run=True)
    m["artifact_ok"] = (
        r["u7_ok"] and
        (hv.ART_DIR / f"tg_final_watchlist_{target}.txt").exists() and
        (hv.ART_DIR / f"tg_final_watchlist_{target}.jsonl").exists()
    )
    return m


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--targets", required=True)
    args = ap.parse_args()
    targets = [t.strip() for t in args.targets.split(",") if t.strip()]

    print(f"{'target':12s} | {'compose':>7s} | {'u7':>3s} | {'csv':>3s} | "
          f"{'artifact':>8s} | {'tg_len':>6s} | {'bien':>4s} | {'reg':>3s} | csv_md5")
    print(f"{'-'*12} | {'-'*7} | {'-'*3} | {'-'*3} | {'-'*8} | {'-'*6} | {'-'*4} | {'-'*3} | {'-'*12}")

    results = []
    for tgt in targets:
        m = dry_one(tgt)
        results.append(m)
        def s(k, ok_label="OK", bad_label="FAIL"):
            return ok_label if m.get(k) else bad_label
        bien = m.get("bien_4096", 0)
        print(f"{tgt:12s} | {s('compose_ok'):>7s} | {s('u7_ok'):>3s} | "
              f"{s('csv_ok'):>3s} | {s('artifact_ok'):>8s} | "
              f"{m['tg_len']:>6d} | {bien:>4d} | {m['reg']:>3d} | {m.get('csv_md5', '?'):>12s}")
        if not m["u7_ok"] and m["u7_reason"]:
            print(f"   → U7 reason: {m['u7_reason']}")

    n = len(results)
    n_ok = sum(1 for m in results if all([m["compose_ok"], m["u7_ok"], m["csv_ok"], m["artifact_ok"]]))
    max_tg_len = max((m["tg_len"] for m in results), default=0)
    min_bien = min((m.get("bien_4096", 0) for m in results), default=0)
    print()
    print(f"═══ TỔNG {n} đêm · full-OK: {n_ok}/{n} · max tg_len: {max_tg_len} · min biên 4096: {min_bien} ═══")
    sys.exit(0 if n_ok == n else 1)


if __name__ == "__main__":
    main()
