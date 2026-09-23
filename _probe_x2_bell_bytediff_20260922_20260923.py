"""X2 · V5a chuẩn hoá byte diff U0-BELL rows 09-22 · shadow ee71db39 vs prod 5a5f4d8c."""
import sys, os, json, hashlib, difflib
from pathlib import Path

_REPO = Path("/root/Data_back_test/whale_data")

try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except AttributeError: pass  # L-66-OK

TARGET = "2026-09-22"
SHADOW_P = _REPO / "ops/holdout_u0bell_20260920/shadow_run/data_out" / f"events_{TARGET}.jsonl"
PROD_P   = _REPO / "data/artifacts" / f"events_{TARGET}.jsonl"


def _bell_lines(p):
    """Extract U0-BELL rows (type='bell' hoặc 'bell_blind' hoặc 'bell_near').
    Trả list of canonical JSON strings (drop computed_at) sorted by (tok, D)."""
    if not p.exists(): return []
    rows = []
    for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.strip(): continue
        try: r = json.loads(line)
        except json.JSONDecodeError: continue
        t = r.get("type", "")
        if t not in ("bell", "bell_blind", "bell_near"): continue
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

# File-level md5 for reference
shadow_file_md5 = hashlib.md5(SHADOW_P.read_bytes()).hexdigest() if SHADOW_P.exists() else "N/A"
prod_file_md5   = hashlib.md5(PROD_P.read_bytes()).hexdigest() if PROD_P.exists() else "N/A"

print(f"═══ X2 · V5a chuẩn hoá byte diff U0-BELL rows target={TARGET} ═══\n")
print("NGUỒN:")
print(f"  shadow file: {SHADOW_P}")
print(f"    file md5:  {shadow_file_md5}")
print(f"  prod file:   {PROD_P}")
print(f"    file md5:  {prod_file_md5}")
print(f"  filter: type ∈ {{bell, bell_blind, bell_near}} · sort (tok, D, type) · drop computed_at\n")

print(f"{'source':>8s} | n_rows | md5 canonical (sorted, no computed_at)")
print(f"{'-'*8} | {'-'*6} | {'-'*36}")
print(f"{'shadow':>8s} | {len(shadow_lines):>6d} | {shadow_md5}")
print(f"{'prod':>8s}   | {len(prod_lines):>6d} | {prod_md5}")
print(f"{'match':>8s}  | {'yes' if shadow_md5 == prod_md5 else 'no ':>6s} | (md5 canonical bytes match: {shadow_md5 == prod_md5})")

print()
print("─── diff -u nguyên văn (shadow → prod) ───")
diff = list(difflib.unified_diff(shadow_lines, prod_lines,
                                  fromfile=f"shadow_{TARGET}", tofile=f"prod_{TARGET}",
                                  lineterm=""))
if not diff:
    print("(empty diff · byte-identical)")
else:
    for line in diff: print(line)
