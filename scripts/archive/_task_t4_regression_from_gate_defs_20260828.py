#!/usr/bin/env python3
"""[T-④ REGRESSION per §4 D0-table + §2 window · TREO chờ operator ký]

Reads D0 canonical from docs/proposals/gom_h_gate_defs_20260828.md (§4 markdown table).
KHÔNG hardcode D0 values.

Per operator relay (4) 28/08: "T-④ REGRESSION TREO thêm một nhịp: chạy trên §4 D0-table
+ §2 window CHỈ SAU khi operator ký dòng xung đột D0. Chuẩn bị sẵn script đọc D0 từ
file, không hardcode."

Usage (post-ký):
  python scripts/archive/_task_t4_regression_from_gate_defs_20260828.py
"""
from __future__ import annotations
import sys, io, json, hashlib, re
from pathlib import Path
from datetime import datetime, timedelta
from statistics import median
import pandas as pd
import yaml
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = Path(r"D:/Data back test/whale_data")
YAML_PATH = REPO / "screen_thresholds.yaml"
GATE_DEFS = REPO / "docs/proposals/gom_h_gate_defs_20260828.md"
SNAPSHOTS_DIR = Path(r"D:/Check onchain fresh wallets/snapshots")

# Guard TREO
if not GATE_DEFS.exists():
    print(f"[TREO] gate_defs file MISSING: {GATE_DEFS}")
    sys.exit(0)

# Optional CLI flag to unlock TREO (operator ký D0 conflict)
if "--operator-signed-d0" not in sys.argv:
    print("═" * 80)
    print("[TREO] T-④ regression WAITING operator ký dòng xung đột D0 canonical.")
    print(f"       gate_defs md5 : {hashlib.md5(open(GATE_DEFS,'rb').read()).hexdigest()}")
    print(f"       Run với --operator-signed-d0 để unlock (after chat KÝ).")
    print("═" * 80)
    # Still parse + print D0 table for visibility
    txt = GATE_DEFS.read_text(encoding="utf-8")
    m = re.search(r"## §4\..*?\n(\|.*?\n)(?=\n##|\Z)", txt, re.DOTALL)
    if m:
        print("\nD0 canonical table §4 (parsed từ file):\n")
        print(m.group(0)[:1200])
    sys.exit(0)

# ─── Parse D0 from §4 markdown table ───
def _parse_d0_table(path: Path) -> dict:
    """Extract D0 dates from §4 markdown table."""
    txt = path.read_text(encoding="utf-8")
    m = re.search(r"## §4\..*?\n\|.*?\|.*?\n\|[-|\s]+\|.*?\n((?:\|.*?\n)+)", txt, re.DOTALL)
    if not m: return {}
    out = {}
    for line in m.group(1).strip().split("\n"):
        cells = [c.strip() for c in line.split("|")[1:-1]]
        if len(cells) < 2: continue
        token = cells[0]; d0 = cells[1]
        if re.match(r"\d{4}-\d{2}-\d{2}", d0):
            out[token] = d0
    return out

d0_table = _parse_d0_table(GATE_DEFS)
print("═" * 100)
print(f"[T-④ REGRESSION · post-KÝ · §4 D0-table + §2 window]")
print(f"  gate_defs md5: {hashlib.md5(open(GATE_DEFS,'rb').read()).hexdigest()}")
print(f"  D0 canonical ({len(d0_table)} tokens): {d0_table}")
print("═" * 100)

# ─── Standard T-④ regression logic below (post-ký) ───
# ... (identical semantic to _task_v_verdict_tables_20260828.py T-④ block,
#      but với D0 từ file, evaluation window = [max(data_start, D0-30) .. D0-1])
# TODO: chạy sau operator ký + kết hợp CSV bản mới V④-RT backfill.

print("\n[TODO after ký] regression body — reuse _task_v_verdict_tables T-④ logic with:")
print("  - D0 from d0_table (parsed above)")
print("  - eval window = [max(data_start, D0-30) .. D0-1] per §2")
print("  - substrate STORE, V④-RT cooldown applied (per per-token first-lane-fire history)")
print("  - PASS = ≥1 compose fire lead ≥1d before D0")
print("  - passes/evaluable, IGN-MISSING removed từ mẫu số")
