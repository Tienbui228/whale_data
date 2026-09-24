"""B2-R1b.2 · Chạy nền R1b2 trên calibration data THẬT.

Verify code md5 trước khi chạy · in per bucket median/[5%,95%]/n_reached.
"""
import sys, io, hashlib, statistics
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, ".")

# Verify md5
CODE_PATH = Path("_probe_r1b2_pseudo_bell_20260924.py")
EXPECT_CODE_MD5 = "6940d69da54fa2e87610517086be5195"
actual = hashlib.md5(CODE_PATH.read_bytes()).hexdigest()
print(f"[md5 run-time] R1b2 code: {actual}")
print(f"[md5 expect  ] R1b2 code: {EXPECT_CODE_MD5}")
assert actual == EXPECT_CODE_MD5, "R1b2 code md5 mismatch · DỪNG"
print(f"[md5 verify] MATCH\n")

import _probe_r1b2_pseudo_bell_20260924 as pb

# Load calibration data thật
print(f"[load] fw csv 2026-05..09 · calib {pb.CALIB_START} → {pb.CALIB_END}")
by_sym = pb._load_by_sym()
universe = pb._load_universe()
print(f"[load] universe = {len(universe)} · by_sym cover = {len(by_sym)}\n")

# Build pool per bucket (loại outage)
pool = pb.build_pool_by_bucket(by_sym, universe)
print(f"[pool] pool sizes per bucket (loại outage):")
for name, _, _ in pb.BUCKETS:
    print(f"  {name:>10s}: {len(pool[name])} nights")
print()

# Cross check fn
cross_check = pb.make_cross_check_fn_from_by_sym(by_sym)

# Run resample
print(f"[run] resample_r1b2 R={pb.R_ITERATIONS} · base_seed={pb.BASE_SEED} · n_min={pb.N_MIN_PER_BUCKET}")
result = pb.resample_r1b2(pool, cross_check, r_iterations=pb.R_ITERATIONS,
                           base_seed=pb.BASE_SEED, n_min=pb.N_MIN_PER_BUCKET, gap=pb.GAP_DAYS)
print(f"[run] done\n")

# Compute stats
def _pct(lst, q):
    if not lst: return None
    ss = sorted(lst)
    if len(ss) == 1: return ss[0]
    pos = q / 100 * (len(ss) - 1)
    lo = int(pos); hi = min(lo + 1, len(ss) - 1)
    frac = pos - lo
    return ss[lo] * (1 - frac) + ss[hi] * frac

print(f"═══ R1b.2 kết quả nền · calibration THẬT ═══\n")
print(f"{'bucket':>10s} | {'median':>8s} | {'[5%, 95%]':>18s} | {'variance':>9s} | {'stdev':>7s} | {'n_reached/R':>13s}")
print(f"{'-'*10} | {'-'*8} | {'-'*18} | {'-'*9} | {'-'*7} | {'-'*13}")

results_summary = {}
for name, _, _ in pb.BUCKETS:
    rates = result[name]["rates"]
    n_reached = result[name]["n_reached"]
    n_neo_list = result[name]["n_neo_list"]
    if n_reached == 0:
        row_str = f"{name:>10s} | {'N/A':>8s} | {'N/A':>18s} | {'N/A':>9s} | {'N/A':>7s} | {n_reached:>5d}/{pb.R_ITERATIONS:<7d}"
        results_summary[name] = {"status": "N/A", "n_reached": n_reached,
                                  "median": None, "p5": None, "p95": None,
                                  "variance": None, "stdev": None,
                                  "n_neo_median": statistics.median(n_neo_list) if n_neo_list else None,
                                  "n_neo_max": max(n_neo_list) if n_neo_list else None}
    else:
        m = statistics.median(rates)
        p5 = _pct(rates, 5)
        p95 = _pct(rates, 95)
        var = statistics.variance(rates) if len(rates) >= 2 else 0
        stdev = statistics.stdev(rates) if len(rates) >= 2 else 0
        row_str = (f"{name:>10s} | {m:>7.2f}% | [{p5:>5.2f}%, {p95:>5.2f}%] | {var:>9.4f} | {stdev:>7.4f} | "
                   f"{n_reached:>5d}/{pb.R_ITERATIONS:<7d}")
        results_summary[name] = {"status": "OK", "n_reached": n_reached,
                                  "median": m, "p5": p5, "p95": p95,
                                  "variance": var, "stdev": stdev,
                                  "n_neo_median": statistics.median(n_neo_list),
                                  "n_neo_max": max(n_neo_list)}
    print(row_str)

print(f"\nGhi chú:")
print(f"  - median = median rate qua R iterations (chỉ tính iter có đủ 50 neo)")
print(f"  - [5%, 95%] = 5th/95th percentile của rate")
print(f"  - n_reached = số iter đủ 50 neo / R")
print(f"  - Dải KHÔNG đạt 50 neo trong bất kỳ iter nào → N/A · loại khỏi lift (R1b.3 a)")

# Dump JSON
import json
out = Path("scratch/R1b2_base_result.json")
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps({
    "code_md5": actual,
    "base_seed": pb.BASE_SEED, "R": pb.R_ITERATIONS,
    "gap_days": pb.GAP_DAYS, "n_min": pb.N_MIN_PER_BUCKET,
    "calib_start": pb.CALIB_START, "calib_end": pb.CALIB_END,
    "outage_dates": sorted(str(d) for d in pb.OUTAGE_DATES),
    "pool_sizes": {name: len(pool[name]) for name, _, _ in pb.BUCKETS},
    "results": results_summary,
}, indent=2, ensure_ascii=False), encoding="utf-8")
json_md5 = hashlib.md5(out.read_bytes()).hexdigest()
print(f"\n[out] {out} · md5={json_md5}")
