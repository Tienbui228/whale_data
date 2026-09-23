"""S1 · shadow harness · diff U0-BELL shadow vs prod (legacy ledger + artifacts).

Bảng cột: target · nguồn · n_bell_shadow · n_bell_prod · n_diff · tên lệch (bên thắng).

Match key = (tok, D) · ignore computed_at (mỗi run có ts mới).
"""
import sys, os, json
from pathlib import Path

_REPO = Path("/root/Data_back_test/whale_data")
SHADOW_DIR = _REPO / "ops/holdout_u0bell_20260920/shadow_run/data_out"
LEGACY_DIR = _REPO / "data/logs/event_ledger"
ART_DIR    = _REPO / "data/artifacts"

TARGETS = ["2026-09-20", "2026-09-21", "2026-09-22"]

try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except AttributeError: pass  # L-66-OK


def _load_jsonl(p):
    if not p.exists(): return []
    rows = []
    for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.strip(): continue
        try: rows.append(json.loads(line))
        except json.JSONDecodeError: continue
    return rows


def _bell_keys_from_new_schema(rows):
    """Extract set of (tok, D) tuples from events_build schema."""
    return {(r.get("tok"), r.get("D")) for r in rows
            if r.get("type") == "bell" and r.get("tok") and r.get("D")}


def _bell_keys_from_legacy_schema(rows):
    """Legacy event ledger schema · tìm U0-BELL rows.
    Fields: {ts_utc, event_type, axis, symbol, target_date, source, source_tag, source_line}.
    U0-BELL indicator: event_type match U0-BELL pattern hoặc source_line contains U0-BELL.
    """
    keys = set()
    for r in rows:
        et = str(r.get("event_type", ""))
        sl = str(r.get("source_line", ""))
        if "U0-BELL" in et or "U0-BELL" in sl:
            sym = r.get("symbol")
            td = r.get("target_date")
            if sym and td:
                keys.add((sym, td))
    return keys


print("═══ S1 · shadow harness · U0-BELL diff ═══")
print(f"{'target':12s} | {'source':20s} | {'shadow':>7s} | {'prod':>5s} | {'diff':>5s} | tên lệch")
print(f"{'-'*12} | {'-'*20} | {'-'*7} | {'-'*5} | {'-'*5} | {'-'*30}")

for tgt in TARGETS:
    shadow_p = SHADOW_DIR / f"events_{tgt}.jsonl"
    shadow_rows = _load_jsonl(shadow_p)
    shadow_bells = _bell_keys_from_new_schema(shadow_rows)

    # Diff vs artifacts (prod events_build output)
    prod_art_p = ART_DIR / f"events_{tgt}.jsonl"
    prod_art_rows = _load_jsonl(prod_art_p)
    prod_art_bells = _bell_keys_from_new_schema(prod_art_rows)
    only_shadow = shadow_bells - prod_art_bells
    only_prod   = prod_art_bells - shadow_bells
    diff_art    = only_shadow | only_prod
    tên_lệch_art = sorted([f"{t}(shadow-only)" for t, _ in only_shadow] +
                          [f"{t}(prod-only)" for t, _ in only_prod])
    print(f"{tgt:12s} | {'data/artifacts':20s} | {len(shadow_bells):>7d} | {len(prod_art_bells):>5d} | {len(diff_art):>5d} | {', '.join(tên_lệch_art)[:30] or '(none)'}")

    # Diff vs legacy ledger
    prod_leg_p = LEGACY_DIR / f"events_{tgt}.jsonl"
    prod_leg_rows = _load_jsonl(prod_leg_p)
    prod_leg_bells = _bell_keys_from_legacy_schema(prod_leg_rows)
    only_shadow_leg = shadow_bells - prod_leg_bells
    only_leg        = prod_leg_bells - shadow_bells
    diff_leg = only_shadow_leg | only_leg
    tên_lệch_leg = sorted([f"{t}(shadow-only)" for t, _ in only_shadow_leg] +
                          [f"{t}(leg-only)" for t, _ in only_leg])
    print(f"{tgt:12s} | {'data/logs/legacy':20s} | {len(shadow_bells):>7d} | {len(prod_leg_bells):>5d} | {len(diff_leg):>5d} | {', '.join(tên_lệch_leg)[:30] or '(none)'}")

print()
print("NGUỒN:")
print(f"  shadow:   ops/holdout_u0bell_20260920/shadow_run/data_out/events_<T>.jsonl (run 23/09)")
print(f"  artifact: data/artifacts/events_<T>.jsonl (prod events_build)")
print(f"  legacy:   data/logs/event_ledger/events_<T>.jsonl (star ledger · pre-events_build split)")
print(f"  match key = (tok, D) · ignore computed_at")
