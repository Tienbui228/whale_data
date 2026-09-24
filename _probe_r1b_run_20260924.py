"""B2 · Chạy nền R1b bằng code đã pin cec7dc89 · in md5 lúc chạy.

- Verify md5 pseudo-bell code lúc chạy · phải khớp `cec7dc892a3a969e343289b16a2fb267`
- Load fw data · run resample_pseudo_bells_rate
- Per bucket in: median · [5%, 95%] · n_episode · n_reached / R
- Bucket không đủ 50 → N/A (theo phán · KHÔNG hạ n · KHÔNG nới rút)
- Ghi addendum + pin qua G2 lib

KHÔNG chạy B3.
"""
import sys, io, os, hashlib
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, ".")

# ─── 1. Verify code md5 at run time ───
PSEUDO_BELL_PATH = Path("_probe_r1b_pseudo_bell_20260924.py")
EXPECT_PSEUDO_MD5 = "cec7dc892a3a969e343289b16a2fb267"
actual_md5 = hashlib.md5(PSEUDO_BELL_PATH.read_bytes()).hexdigest()
print(f"[md5 run-time] pseudo-bell: {actual_md5}")
print(f"[md5 expect  ] pseudo-bell: {EXPECT_PSEUDO_MD5}")
assert actual_md5 == EXPECT_PSEUDO_MD5, f"md5 mismatch · code changed · DỪNG"
print(f"[md5 verify] MATCH · code đóng băng OK\n")

# Also verify detector (paired freeze)
DETECTOR_PATH = Path("_probe_r1b_detector_20260924.py")
EXPECT_DETECTOR_MD5 = "72b880021f2662d9d7d0deeeaf9819d9"
det_md5 = hashlib.md5(DETECTOR_PATH.read_bytes()).hexdigest()
print(f"[md5 run-time] detector:    {det_md5}")
assert det_md5 == EXPECT_DETECTOR_MD5, f"detector md5 mismatch"
print(f"[md5 verify] MATCH · detector freeze OK\n")

# ─── 2. Import pseudo-bell module + run ───
import _probe_r1b_pseudo_bell_20260924 as pb

print(f"NGUỒN: fw csv 2026-05..09 · calib window {pb.CALIB_START} → {pb.CALIB_END}")
print(f"SEED={pb.SEED} · R={pb.R_ITERATIONS} · GAP={pb.GAP_DAYS}d · N_MIN={pb.N_MIN_PER_BUCKET}")
print(f"BUCKETS: {[b[0] for b in pb.BUCKETS]}")
print(f"OUTAGE: {sorted(pb.OUTAGE_DATES)}\n")

by_sym = pb._load_by_sym()
universe = pb._load_universe()
print(f"[load] universe = {len(universe)} · by_sym coverage = {len(by_sym)} bare-syms\n")

# ─── 3. Also count "all-hedge nights" pool per bucket (context) ───
all_nights = pb.scan_all_hedge_nights(by_sym, universe, pb.CALIB_START, pb.CALIB_END)
nights_by_bucket = {name: 0 for name, _, _ in pb.BUCKETS}
for tok, D, div_D in all_nights:
    b = pb._bucket_of(div_D)
    if b: nights_by_bucket[b] += 1
print(f"[pool] total token-night trong calib = {len(all_nights)}")
for name, _, _ in pb.BUCKETS:
    print(f"  {name:>10s}: {nights_by_bucket[name]} nights")
print()

# ─── 4. Run resample ───
print(f"[run] resample_pseudo_bells_rate ... (R={pb.R_ITERATIONS} iterations)")
result, _pool = pb.resample_pseudo_bells_rate(by_sym, universe, pb.SEED, pb.R_ITERATIONS)
print(f"[run] done\n")

# ─── 5. Statistics per bucket ───
import statistics

def _pct(lst, q):
    """Quantile · linear interpolation."""
    if not lst: return None
    ss = sorted(lst)
    if len(ss) == 1: return ss[0]
    pos = q / 100 * (len(ss) - 1)
    lo = int(pos); hi = min(lo + 1, len(ss) - 1)
    frac = pos - lo
    return ss[lo] * (1 - frac) + ss[hi] * frac

print(f"═══ B2 · R1b-base per dải ═══\n")
print(f"{'bucket':>10s} | {'median':>8s} | {'[5%, 95%]':>18s} | {'n_reached/R':>13s} | {'ep_median':>10s} | {'ep_min':>7s} | {'ep_max':>7s}")
print(f"{'-'*10} | {'-'*8} | {'-'*18} | {'-'*13} | {'-'*10} | {'-'*7} | {'-'*7}")

results_json = {}
for name, _, _ in pb.BUCKETS:
    rates = result[name]["rates"]
    ep_list = result[name]["n_ep_list"]
    n_reached = result[name]["n_reached"]
    if n_reached == 0:
        row_str = f"{name:>10s} | {'N/A':>8s} | {'N/A':>18s} | {n_reached:>5d}/{pb.R_ITERATIONS:<7d} | {'-':>10s} | {'-':>7s} | {'-':>7s}"
        results_json[name] = {"median": None, "p5": None, "p95": None, "n_reached": n_reached,
                              "ep_median": None, "ep_min": min(ep_list) if ep_list else None,
                              "ep_max": max(ep_list) if ep_list else None,
                              "status": "N/A · dải không đạt n≥50"}
    else:
        m = statistics.median(rates)
        p5 = _pct(rates, 5)
        p95 = _pct(rates, 95)
        ep_med = statistics.median(ep_list) if ep_list else 0
        ep_min = min(ep_list) if ep_list else 0
        ep_max = max(ep_list) if ep_list else 0
        row_str = (f"{name:>10s} | {m:>7.2f}% | [{p5:>5.2f}%, {p95:>5.2f}%] | {n_reached:>5d}/{pb.R_ITERATIONS:<7d} | "
                   f"{ep_med:>10.1f} | {ep_min:>7d} | {ep_max:>7d}")
        results_json[name] = {"median": m, "p5": p5, "p95": p95, "n_reached": n_reached,
                              "ep_median": ep_med, "ep_min": ep_min, "ep_max": ep_max,
                              "status": "OK"}
    print(row_str)

print()
print(f"Ghi chú: rate% = n_hit / n_ep trong dải · [5%, 95%] = 5th & 95th percentile qua {pb.R_ITERATIONS} iterations (chỉ tính iterations có n_ep≥{pb.N_MIN_PER_BUCKET})")

# ─── 6. Dump JSON ───
import json
out = Path("scratch/R1b_base_result.json")
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps({
    "code_md5_pseudo": actual_md5,
    "code_md5_detector": det_md5,
    "seed": pb.SEED, "R": pb.R_ITERATIONS, "gap_days": pb.GAP_DAYS,
    "n_min": pb.N_MIN_PER_BUCKET,
    "calib_start": pb.CALIB_START, "calib_end": pb.CALIB_END,
    "outage_dates": sorted(str(d) for d in pb.OUTAGE_DATES),
    "results": results_json,
    "pool_nights_per_bucket": nights_by_bucket,
    "total_hedge_nights": len(all_nights),
}, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"\n[out] {out} · md5={hashlib.md5(out.read_bytes()).hexdigest()}")
