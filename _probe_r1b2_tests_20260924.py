"""R1b2 · P1-P4 test suite · dữ liệu GIẢ trước · calib data sau (theo lệnh)."""
from __future__ import annotations
import sys, io, statistics, hashlib, random
from datetime import date, timedelta
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, ".")

import _probe_r1b2_pseudo_bell_20260924 as pb

CODE_MD5 = hashlib.md5(Path("_probe_r1b2_pseudo_bell_20260924.py").read_bytes()).hexdigest()
print(f"[code md5 R1b2] {CODE_MD5}\n")


# ═══════════════════════════════════════════════════════════════════════════
# Helper: build big synthetic (cho P1, P2, P3 · ~20 tokens · nhiều nights)
# ═══════════════════════════════════════════════════════════════════════════
def _build_big_synth():
    """20 tokens · mỗi token 30-60 in-band nights spread trong 79 days.
    Đảm bảo pool đủ lớn để đạt 50 neo per bucket sau ±14d filter."""
    rng = random.Random(42)
    nights = []
    cross_dates = set()
    base = date(2026, 6, 20)
    for tok_id in range(20):
        tok = f"TOK{tok_id:02d}"
        n_nights = rng.randint(30, 60)
        # Pick random dates in 79-day window
        offsets = rng.sample(range(79), min(n_nights, 79))
        for off in offsets:
            D = base + timedelta(days=off)
            div = round(rng.uniform(0.20, 0.50), 3)
            nights.append((tok, D, div))
        # Random cross events
        for _ in range(rng.randint(5, 15)):
            cd = base + timedelta(days=rng.randint(0, 88))
            cross_dates.add((tok, cd))
    return nights, cross_dates


def _make_cross_check(cross_dates):
    def check(tok, d_start, d_end):
        d = d_start
        while d <= d_end:
            if (tok, d) in cross_dates: return True
            d += timedelta(days=1)
        return False
    return check


def _partition_by_bucket(nights):
    pool = {name: [] for name, _, _ in pb.BUCKETS}
    for tok, D, div in nights:
        b = pb._bucket_of(div)
        if b: pool[b].append((tok, D, div))
    return pool


# ═══════════════════════════════════════════════════════════════════════════
# P1 · 2 seed gốc khác → chuỗi base khác
# ═══════════════════════════════════════════════════════════════════════════
def test_P1():
    print("─── P1 · 2 seed gốc khác → chuỗi base khác ───")
    nights, cross_dates = _build_big_synth()
    pool = _partition_by_bucket(nights)
    check = _make_cross_check(cross_dates)

    def run_with_seed(base_seed):
        result = pb.resample_r1b2(pool, check, r_iterations=100, base_seed=base_seed)
        return result["[0.4,0.5]"]["rates"]

    rates_A = run_with_seed(1000)
    rates_B = run_with_seed(9999)
    min_len = min(len(rates_A), len(rates_B))
    n_diff = sum(1 for i in range(min_len) if abs(rates_A[i] - rates_B[i]) > 1e-9)
    ok = n_diff > 0
    print(f"  seed_base=1000 · n_rates={len(rates_A)}")
    print(f"  seed_base=9999 · n_rates={len(rates_B)}")
    print(f"  Iter positions khác giá trị: {n_diff}/{min_len}")
    print(f"  → {'PASS' if ok else 'FAIL'}\n")
    return ok


# ═══════════════════════════════════════════════════════════════════════════
# P2 · Phương sai 500 lần > 0 (mỗi dải đủ 50)
# ═══════════════════════════════════════════════════════════════════════════
def test_P2():
    print("─── P2 · variance 500 lần > 0 (dải đủ 50) ───")
    nights, cross_dates = _build_big_synth()
    pool = _partition_by_bucket(nights)
    check = _make_cross_check(cross_dates)
    result = pb.resample_r1b2(pool, check, r_iterations=500, base_seed=pb.BASE_SEED)
    all_ok = True
    for name, _, _ in pb.BUCKETS:
        rates = result[name]["rates"]
        n_reached = result[name]["n_reached"]
        if n_reached == 0:
            print(f"  {name:>10s}: n_reached=0/500 · SKIP (N/A · KHÔNG dải này)")
            continue
        if n_reached < 2:
            print(f"  {name:>10s}: n_reached={n_reached}/500 · CANNOT variance")
            all_ok = False
            continue
        var = statistics.variance(rates)
        stdev = statistics.stdev(rates)
        med = statistics.median(rates)
        print(f"  {name:>10s}: n_reached={n_reached}/500 · median={med:.2f}% · variance={var:.4f} · stdev={stdev:.4f}")
        if var <= 0:
            all_ok = False
    print(f"  → {'PASS' if all_ok else 'FAIL'}\n")
    return all_ok


# ═══════════════════════════════════════════════════════════════════════════
# P3 · offset = D_neo − ngày đầu đoạn liên tục trong dải chứa neo
#      median offset > 0
# ═══════════════════════════════════════════════════════════════════════════
def _find_run_containing(all_nights_bucket_for_tok, D_neo, gap_days=pb.GAP_DAYS):
    """Trả list of dates trong 'đoạn liên tục' (gap ≤14d) TRONG DẢI b chứa D_neo."""
    dates_sorted = sorted(d for _t, d, _v in all_nights_bucket_for_tok)
    # Group into runs by gap ≤ gap_days
    runs = []
    if not dates_sorted: return []
    cur = [dates_sorted[0]]
    for d in dates_sorted[1:]:
        if (d - cur[-1]).days <= gap_days:
            cur.append(d)
        else:
            runs.append(cur)
            cur = [d]
    runs.append(cur)
    # Find run containing D_neo
    for run in runs:
        if D_neo in run:
            return run
    return [D_neo]  # fallback


def test_P3():
    print("─── P3 · offset median > 0 (neo không luôn = ngày đầu run) ───")
    nights, cross_dates = _build_big_synth()
    pool = _partition_by_bucket(nights)
    check = _make_cross_check(cross_dates)
    result = pb.resample_r1b2(pool, check, r_iterations=100, base_seed=pb.BASE_SEED)

    # Collect offsets across iterations · use anchors_first_iter for simplicity
    # But P3 requires median offset > 0 across many samples → aggregate all iters
    all_ok = True
    for name, _, _ in pb.BUCKETS:
        if result[name]["n_reached"] == 0:
            print(f"  {name:>10s}: n_reached=0 · SKIP (N/A)")
            continue
        # Build per-tok in-band nights (pool_b)
        pool_b = pool[name]
        by_tok = {}
        for tok, D, div in pool_b:
            by_tok.setdefault(tok, []).append((tok, D, div))
        # Run more iters, collect anchors, compute offset
        offsets = []
        for i in range(500):
            seed_i = pb.BASE_SEED + i + 10000  # different range
            _, _, anchors = pb.resample_iteration_for_bucket(
                pool_b, name, seed_i, check, pb.N_MIN_PER_BUCKET, pb.GAP_DAYS)
            for tok, D_neo, _ in anchors:
                run = _find_run_containing(by_tok[tok], D_neo)
                if run:
                    off = (D_neo - min(run)).days
                    offsets.append(off)
        if not offsets:
            print(f"  {name:>10s}: no offsets · SKIP")
            continue
        offsets.sort()
        med_off = statistics.median(offsets)
        max_off = max(offsets)
        n_pos = sum(1 for x in offsets if x > 0)
        print(f"  {name:>10s}: n_anchors={len(offsets)} · median_offset={med_off:.1f} · max={max_off} · n_off>0={n_pos}/{len(offsets)}")
        if med_off <= 0:
            print(f"    ⚠ median offset ≤ 0 · KHÔNG PASS")
            all_ok = False
    print(f"  → {'PASS' if all_ok else 'FAIL'}\n")
    return all_ok


# ═══════════════════════════════════════════════════════════════════════════
# P4 · Kiểm thuật toán tay: bộ giả nhỏ (≤10 token) · in danh sách neo · verify từng bước
# ═══════════════════════════════════════════════════════════════════════════
def test_P4():
    print("─── P4 · Hand-verify thuật toán trên bộ giả nhỏ ───")
    # Bộ giả: 5 tokens · in-band nights trong 40 days · đủ ít để in ra
    base = date(2026, 6, 20)
    nights = [
        ("A", base + timedelta(days=0),  0.42),
        ("A", base + timedelta(days=5),  0.44),
        ("A", base + timedelta(days=25), 0.41),
        ("A", base + timedelta(days=30), 0.43),
        ("B", base + timedelta(days=2),  0.45),
        ("B", base + timedelta(days=10), 0.46),
        ("C", base + timedelta(days=8),  0.40),
        ("D", base + timedelta(days=1),  0.48),
        ("D", base + timedelta(days=20), 0.47),
        ("E", base + timedelta(days=15), 0.49),
    ]
    print(f"  Bộ giả 5 tokens · 10 nights · tất cả bucket [0.4, 0.5]")
    for n in nights:
        print(f"    {n[0]} · {n[1].isoformat()} · div={n[2]}")

    # Fix n_min tiny for hand-check
    N_MIN_TEST = 5
    pool_b = nights
    check = lambda tok, d_s, d_e: False  # dummy cross (not needed for anchor test)

    seed_fix = 12345
    # In shuffle order
    rng = random.Random(seed_fix)
    order = pool_b[:]
    rng.shuffle(order)
    print(f"\n  Với seed={seed_fix} · thứ tự trộn:")
    for i, (tok, D, div) in enumerate(order):
        print(f"    [{i}] {tok} · {D.isoformat()} · div={div}")

    # Run algorithm
    _, _, anchors = pb.resample_iteration_for_bucket(
        pool_b, "[0.4,0.5]", seed_fix, check, N_MIN_TEST, pb.GAP_DAYS)
    print(f"\n  Neo đã nhận (n_min={N_MIN_TEST}):")
    for tok, D, div in anchors:
        print(f"    ✓ {tok} · {D.isoformat()} · div={div}")

    # Verify hand-check: trace step-by-step
    print(f"\n  Trace từng bước:")
    accepted = []
    accepted_by_tok = {}
    for i, (tok, D, div) in enumerate(order):
        conflict = False
        for prev in accepted_by_tok.get(tok, []):
            if abs((D - prev).days) <= pb.GAP_DAYS:
                conflict = True
                break
        reason = "ACCEPT" if not conflict else f"REJECT (conflict với {[d.isoformat() for d in accepted_by_tok[tok]]})"
        print(f"    [{i}] {tok} · {D.isoformat()} → {reason}")
        if not conflict:
            accepted.append((tok, D, div))
            accepted_by_tok.setdefault(tok, []).append(D)
        if len(accepted) >= N_MIN_TEST:
            print(f"    → ĐỦ {N_MIN_TEST} neo · dừng")
            break

    # Verify matches
    matches = [a == b for a, b in zip(anchors, accepted)]
    ok = all(matches) and len(anchors) == len(accepted)
    print(f"\n  Anchors từ code == trace tay: {ok}")
    print(f"  → {'PASS' if ok else 'FAIL'}\n")
    return ok


if __name__ == "__main__":
    print("═" * 75)
    print(" R1b2 · P1-P4 · dữ liệu GIẢ (khớp thuật toán ANALYSIS ký)")
    print("═" * 75)
    ok1 = test_P1()
    ok2 = test_P2()
    ok3 = test_P3()
    ok4 = test_P4()
    print("═" * 75)
    print(f" P1 (2 seed khác):                     {'PASS' if ok1 else 'FAIL'}")
    print(f" P2 (variance > 0):                    {'PASS' if ok2 else 'FAIL'}")
    print(f" P3 (median offset > 0):               {'PASS' if ok3 else 'FAIL'}")
    print(f" P4 (hand-verify thuật toán):          {'PASS' if ok4 else 'FAIL'}")
    print("═" * 75)
    if ok1 and ok2 and ok3 and ok4:
        print(" OVERALL: ALL PASS · thuật toán khớp ANALYSIS ký")
    else:
        print(" OVERALL: FAIL · thuật toán CHƯA khớp · DỪNG")
