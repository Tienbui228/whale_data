"""V5a · byte-level diff U0-BELL rows 09-21 · shadow R0 vs prod artifacts."""
import sys, os, json, hashlib, difflib
from pathlib import Path

_REPO = Path("/root/Data_back_test/whale_data")

try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except AttributeError: pass  # L-66-OK

TARGET = "2026-09-21"
SHADOW_P = _REPO / "ops/holdout_u0bell_20260920/shadow_run/data_out" / f"events_{TARGET}.jsonl"
PROD_P   = _REPO / "data/artifacts" / f"events_{TARGET}.jsonl"


def _bell_lines(p):
    """Extract U0-BELL rows (type='bell' hoặc 'bell_blind' hoặc 'bell_near').
    Trả list of canonical JSON strings (drop computed_at) sorted by (tok, D).
    """
    if not p.exists(): return []
    rows = []
    for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.strip(): continue
        try: r = json.loads(line)
        except json.JSONDecodeError: continue
        t = r.get("type", "")
        if t not in ("bell", "bell_blind", "bell_near"): continue
        # drop computed_at (varies per run)
        rc = {k: v for k, v in r.items() if k != "computed_at"}
        rows.append(rc)
    rows.sort(key=lambda r: (r.get("tok", ""), r.get("D", ""), r.get("type", "")))
    return [json.dumps(r, ensure_ascii=False, sort_keys=True) for r in rows]


shadow_lines = _bell_lines(SHADOW_P)
prod_lines   = _bell_lines(PROD_P)

shadow_body = "\n".join(shadow_lines) + "\n"
prod_body   = "\n".join(prod_lines) + "\n"

shadow_md5 = hashlib.md5(shadow_body.encode("utf-8")).hexdigest()
prod_md5   = hashlib.md5(prod_body.encode("utf-8")).hexdigest()

print("═══ V5a · 09-21 byte-level diff U0-BELL rows ═══\n")
print("NGUỒN:")
print(f"  shadow: {SHADOW_P}")
print(f"  prod:   {PROD_P}")
print(f"  filter: type ∈ {{bell, bell_blind, bell_near}} · sort (tok, D, type) · drop computed_at\n")

print(f"{'source':>8s} | n_rows | md5 canonical (sorted, no computed_at)")
print(f"{'-'*8} | {'-'*6} | {'-'*36}")
print(f"{'shadow':>8s} | {len(shadow_lines):>6d} | {shadow_md5}")
print(f"{'prod':>8s} | {len(prod_lines):>6d} | {prod_md5}")
print(f"{'match':>8s} | {'yes' if shadow_md5 == prod_md5 else 'no ':>6s} | (md5 canonical bytes match: {shadow_md5 == prod_md5})")

print()
print("─── diff -u nguyên văn (shadow → prod) ───")
diff = list(difflib.unified_diff(shadow_lines, prod_lines,
                                  fromfile="shadow_09-21", tofile="prod_09-21",
                                  lineterm=""))
if not diff:
    print("(empty diff · byte-identical)")
else:
    for line in diff: print(line)
