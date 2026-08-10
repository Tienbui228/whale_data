"""MD5 snapshot of closed chapters — reference before first incremental cron.

Run BEFORE cron on 08-11 (01:25 UTC). Compare after to verify "khong viet lai so".
Closed chapter = chain_open=False AND close_date is set AND last_eval_date exists.

data-source: /root/Data_back_test/whale_data/data/gom_state.json (VPS canonical)
machine: VPS via SSH
date-range: 2026-08-10 snapshot
code-commit: see git log
"""
from __future__ import annotations
import sys, io, json, hashlib, subprocess
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

VPS = "root@5.223.67.21"
STATE_PATH = "/root/Data_back_test/whale_data/data/gom_state.json"
OUT = Path(r"D:\Data back test\whale_data\scratch\md5_closed_chapters_20260810.json")

result = subprocess.run(
    ["ssh", VPS, f"cat {STATE_PATH}"],
    capture_output=True, text=True, encoding="utf-8", errors="replace"
)
if result.returncode != 0:
    print(f"SSH ERROR: {result.stderr}")
    sys.exit(1)

state = json.loads(result.stdout)

# Closed chapters: chain_open=False, has close_date
closed = {}
for tok, v in state.items():
    if not v.get("chain_open") and v.get("close_date"):
        # Exclude ephemeral fields that legitimately change (updated_at, last_eval_date)
        snap = {k: val for k, val in v.items()
                if k not in ("updated_at", "last_eval_date", "dq_last_fire")}
        closed[tok] = snap

# Compute per-token hash + aggregate
per_tok_hash = {}
for tok in sorted(closed):
    canonical = json.dumps(closed[tok], sort_keys=True, ensure_ascii=False, default=str)
    per_tok_hash[tok] = hashlib.md5(canonical.encode("utf-8")).hexdigest()

agg_str = json.dumps(per_tok_hash, sort_keys=True)
agg_md5 = hashlib.md5(agg_str.encode("utf-8")).hexdigest()

snapshot = {
    "snapshot_date": "2026-08-10",
    "purpose": "md5 reference before first incremental cron (08-11 01:25 UTC)",
    "n_closed": len(closed),
    "aggregate_md5": agg_md5,
    "per_token": per_tok_hash,
}

OUT.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False), encoding="utf-8")

print(f"Closed chapters snapshot: {len(closed)} tokens")
print(f"Aggregate MD5: {agg_md5}")
print(f"Saved to: {OUT}")
print()
print("After tomorrow's cron run, re-run this script → compare aggregate_md5.")
print("If IDENTICAL → closed chapters not rewritten = §8.2 PASS.")
