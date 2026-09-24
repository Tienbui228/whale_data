"""R1b2 · Pseudo-bell nền · NHÁP · CHỜ ANALYSIS R1b.2 KÝ · CHƯA PIN · CHƯA CHẠY DỮ THẬT.

Trạng thái: DRAFT · chưa pin md5 · chưa chạy trên calibration data thật.
Chỉ test trên dữ liệu GIẢ (tổng hợp) để kiểm 3 assertion:
  1. 2 seed khác nhau → median khác nhau (rng có tác dụng)
  2. 500 iterations → phương sai > 0 (không suy sập về single value)
  3. Neo không trùng đêm sớm nhất ở ≥1 episode (random anchor thực sự)

Sửa lỗi R1b-base cec7dc89:
  · CŨ: sort(pool, key=(tok,D)) sau shuffle → episode grouping deterministic
    + anchor = ep[0] = đêm sớm nhất mọi episode (≡ neo R1a đã bị rút)
  · MỚI: giữ episode grouping (dùng sort để group đúng 14d) NHƯNG anchor
    RANDOM per episode qua rng.choice · và (optional) subset sampling.

Thuật toán DRAFT (chờ ANALYSIS R1b.2 ký nguyên văn):

  1. Đầu vào: pool = all hedge nights (div_avg3(D) ≤ 0.5) trong calib window
  2. Group pool → episodes (deterministic 14d rule · sort by tok, D nội bộ)
  3. Filter: giữ episodes có ≥1 member trong bucket b (theo div của anchor sau)
  4. Với mỗi iteration i (i=1..R):
     a. RNG seed = base_seed + i (hoặc rng progression từ base_seed)
     b. Với mỗi episode có ≥1 night in bucket b (candidates_ep):
        · anchor = rng.choice(candidates_ep) · random member (KHÔNG chỉ ep[0])
     c. Cross-check [D_anchor+1, D_anchor+10]
     d. Filter outage · đếm rate
     e. Nếu ≥50 valid episodes → include rate; else skip iter
  5. Sau R iterations: median · [5%, 95%] của rate per bucket

KHÔNG chạy trên dữ liệu calibration thật cho tới khi ANALYSIS R1b.2 ký thuật toán.
File này chỉ test trên dữ liệu GIẢ dưới đây.
"""
from __future__ import annotations
import random, statistics, sys, io, hashlib
from datetime import date, timedelta
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

# ═══════════════════════════════════════════════════════════════════════════
# Thuật toán DRAFT (KHÔNG dùng calibration thật)
# ═══════════════════════════════════════════════════════════════════════════

GAP_DAYS = 14
FORWARD_MIN = 1
FORWARD_MAX = 10


def _group_into_episodes(nights):
    """Group nights = [(tok, D, div_D), ...] into episodes (gap ≤14d cùng token)."""
    if not nights: return []
    sorted_nights = sorted(nights, key=lambda x: (x[0], x[1]))
    episodes = [[sorted_nights[0]]]
    for tok, D, div_D in sorted_nights[1:]:
        prev_tok, prev_D, _ = episodes[-1][-1]
        if tok == prev_tok and (D - prev_D).days <= GAP_DAYS:
            episodes[-1].append((tok, D, div_D))
        else:
            episodes.append([(tok, D, div_D)])
    return episodes


def _bucket_of(v, buckets):
    for name, lo, hi in buckets:
        if lo <= v < hi: return name
    return None


def sample_pseudo_bell_rate(pool_nights, cross_check_fn, outage_fn,
                             bucket_name, buckets,
                             seed, r_iterations, n_min):
    """
    NHÁP thuật toán · rate resample cho 1 bucket.

    · Group pool → episodes (deterministic)
    · Filter episodes có ≥1 member với div ∈ bucket_name
    · Mỗi iteration: rng.choice(members_in_bucket) làm anchor per episode
    · Cross-check + loại outage · đếm rate
    · Trả list of rates (chỉ iterations có n_ep ≥ n_min)
    """
    all_eps = _group_into_episodes(pool_nights)
    # Filter episodes with at least 1 night in target bucket
    eligible = []
    for ep in all_eps:
        members_in_bucket = [n for n in ep if _bucket_of(n[2], buckets) == bucket_name]
        if members_in_bucket:
            eligible.append((ep, members_in_bucket))

    rates = []
    anchor_dates_per_iter = []  # For test 3: track anchor dates
    rng = random.Random(seed)
    for _ in range(r_iterations):
        anchors_this_iter = []
        n_ep_valid = 0
        n_hit_valid = 0
        for ep, candidates in eligible:
            anchor = rng.choice(candidates)  # RANDOM anchor per episode
            anchors_this_iter.append(anchor)
            tok, D_anchor, div_D = anchor
            if outage_fn(D_anchor):
                continue
            n_ep_valid += 1
            if cross_check_fn(tok, D_anchor + timedelta(days=FORWARD_MIN),
                              D_anchor + timedelta(days=FORWARD_MAX)):
                n_hit_valid += 1
        if n_ep_valid >= n_min:
            rates.append(n_hit_valid / n_ep_valid * 100)
        anchor_dates_per_iter.append(anchors_this_iter)
    return rates, anchor_dates_per_iter, eligible


# ═══════════════════════════════════════════════════════════════════════════
# TEST trên DỮ LIỆU GIẢ
# ═══════════════════════════════════════════════════════════════════════════

def _build_synthetic_data():
    """Tổng hợp dữ liệu GIẢ (KHÔNG phải calibration thật).

    · 20 tokens · mỗi token có 1-3 episode hedge · mỗi episode 3-8 nights
    · div_avg3 phân bố trong [0.2, 0.5]
    · Cross event xảy ra tại D=random ngày trong window forward
    """
    rng = random.Random(42)
    nights = []
    cross_dates = {}  # (tok, date) → True if cross day
    base = date(2026, 6, 20)
    n_tokens = 20
    for tok_id in range(n_tokens):
        tok = f"TOK{tok_id:02d}"
        n_episodes = rng.randint(1, 3)
        cursor = base + timedelta(days=rng.randint(0, 10))
        for _ep in range(n_episodes):
            ep_len = rng.randint(3, 8)
            for k in range(ep_len):
                D = cursor + timedelta(days=k)
                # div distribution: prefer [0.35, 0.5]
                div = round(rng.uniform(0.20, 0.50), 3)
                nights.append((tok, D, div))
            # Add cross candidate (some tokens cross within lookahead)
            if rng.random() < 0.45:
                cross_day = cursor + timedelta(days=rng.randint(2, 12))
                cross_dates[(tok, cross_day)] = True
            # next episode gap
            cursor += timedelta(days=ep_len + rng.randint(15, 30))
    return nights, cross_dates


def _make_cross_fn(cross_dates):
    def cross_check(tok, d_start, d_end):
        d = d_start
        while d <= d_end:
            if (tok, d) in cross_dates:
                return True
            d += timedelta(days=1)
        return False
    return cross_check


def _make_outage_fn():
    """Không outage trong test giả."""
    return lambda d: False


BUCKETS = [("<0.3", 0.0, 0.3), ("[0.3,0.4)", 0.3, 0.4), ("[0.4,0.5]", 0.4, 0.5 + 1e-9)]
N_MIN_TEST = 5  # dữ giả nhỏ · dùng n_min nhỏ hơn thực (50) để test


def test_1_two_seeds_differ():
    """Test 1: 2 seed khác nhau → RATE SEQUENCE khác nhau (rng có tác dụng).

    Compare per-iteration rate sequence: seed A vs seed B.
    Nếu cùng iteration 0 khác nhau về rate → RNG khác nhau · PASS.
    Median có thể trùng do discretization (rate = n_hit/n_ep giới hạn giá trị),
    nhưng sequence PHẢI khác.
    """
    nights, cross_dates = _build_synthetic_data()
    cross_fn = _make_cross_fn(cross_dates)
    outage_fn = _make_outage_fn()

    print("\n─── TEST 1 · 2 seed → sequence khác ───")
    rates_seed_A, _, _ = sample_pseudo_bell_rate(
        nights, cross_fn, outage_fn, "[0.4,0.5]", BUCKETS,
        seed=111, r_iterations=100, n_min=N_MIN_TEST)
    rates_seed_B, _, _ = sample_pseudo_bell_rate(
        nights, cross_fn, outage_fn, "[0.4,0.5]", BUCKETS,
        seed=222, r_iterations=100, n_min=N_MIN_TEST)

    med_A = statistics.median(rates_seed_A) if rates_seed_A else None
    med_B = statistics.median(rates_seed_B) if rates_seed_B else None
    mean_A = statistics.mean(rates_seed_A) if rates_seed_A else None
    mean_B = statistics.mean(rates_seed_B) if rates_seed_B else None
    # Count how many iter-positions have different rate between seeds
    min_len = min(len(rates_seed_A), len(rates_seed_B))
    n_diff_positions = sum(1 for i in range(min_len)
                            if abs(rates_seed_A[i] - rates_seed_B[i]) > 1e-9)
    print(f"  seed=111 · n_rate={len(rates_seed_A)} · median={med_A:.2f}% · mean={mean_A:.3f}%")
    print(f"  seed=222 · n_rate={len(rates_seed_B)} · median={med_B:.2f}% · mean={mean_B:.3f}%")
    print(f"  Iter positions có rate khác (A vs B): {n_diff_positions}/{min_len}")
    print(f"  Δ median = {abs(med_A - med_B):.4f}pp · Δ mean = {abs(mean_A - mean_B):.4f}pp")
    ok = n_diff_positions > 0
    print(f"  → RNG khác nhau (≥1 iter position differ): {'PASS' if ok else 'FAIL'}")
    return ok


def test_2_variance_positive():
    """Test 2: 500 iterations · phương sai > 0."""
    nights, cross_dates = _build_synthetic_data()
    cross_fn = _make_cross_fn(cross_dates)
    outage_fn = _make_outage_fn()

    print("\n─── TEST 2 · variance > 0 qua 500 iterations ───")
    rates, _, _ = sample_pseudo_bell_rate(
        nights, cross_fn, outage_fn, "[0.4,0.5]", BUCKETS,
        seed=20260924, r_iterations=500, n_min=N_MIN_TEST)
    if len(rates) < 2:
        print(f"  n_rate={len(rates)} · CANNOT compute variance · FAIL")
        return False
    var = statistics.variance(rates)
    stdev = statistics.stdev(rates)
    mn, mx = min(rates), max(rates)
    print(f"  n_rate={len(rates)} · variance={var:.4f} · stdev={stdev:.4f}")
    print(f"  min={mn:.2f}% · max={mx:.2f}% · range={mx-mn:.2f}pp")
    ok = var > 0
    print(f"  → variance > 0: {'PASS' if ok else 'FAIL'}")
    return ok


def test_3_anchor_not_always_earliest():
    """Test 3: Neo không trùng đêm sớm nhất ở ≥1 episode."""
    nights, cross_dates = _build_synthetic_data()
    cross_fn = _make_cross_fn(cross_dates)
    outage_fn = _make_outage_fn()

    print("\n─── TEST 3 · anchor ≠ earliest ở ≥1 episode ───")
    _, anchor_dates_per_iter, eligible = sample_pseudo_bell_rate(
        nights, cross_fn, outage_fn, "[0.4,0.5]", BUCKETS,
        seed=42, r_iterations=100, n_min=N_MIN_TEST)

    # For each iteration, count how many anchors ≠ ep[0] (earliest in candidates)
    total_diff_anchors = 0
    n_iters_with_diff = 0
    ep_indices_with_diff = set()
    for iter_idx, anchors in enumerate(anchor_dates_per_iter):
        has_diff_this_iter = False
        for ep_idx, ((ep, candidates), anchor) in enumerate(zip(eligible, anchors)):
            earliest_in_bucket = min(candidates, key=lambda x: x[1])
            if anchor != earliest_in_bucket:
                total_diff_anchors += 1
                ep_indices_with_diff.add(ep_idx)
                has_diff_this_iter = True
        if has_diff_this_iter:
            n_iters_with_diff += 1

    print(f"  n eligible episodes: {len(eligible)}")
    print(f"  n episodes có size ≥2: {sum(1 for _, c in eligible if len(c) >= 2)}")
    print(f"  total (ep × iter) với anchor ≠ earliest: {total_diff_anchors}")
    print(f"  iters có ≥1 anchor ≠ earliest: {n_iters_with_diff}/100")
    print(f"  distinct episodes có ≥1 anchor ≠ earliest: {len(ep_indices_with_diff)}")
    ok = len(ep_indices_with_diff) >= 1
    print(f"  → ≥1 episode có anchor ≠ earliest: {'PASS' if ok else 'FAIL'}")
    return ok


if __name__ == "__main__":
    self_md5 = hashlib.md5(Path(__file__).read_bytes()).hexdigest()
    print("═" * 75)
    print(" R1b2 · Pseudo-bell nền · DRAFT · CHỜ ANALYSIS R1b.2 KÝ")
    print("═" * 75)
    print(f"[self md5] {self_md5}")
    print(f"[status] NHÁP · CHƯA PIN · CHƯA CHẠY DỮ THẬT")
    print(f"[algorithm] group 14d (deterministic) + RANDOM anchor per episode (rng.choice)")
    print(f"[test data] SYNTHETIC (20 tokens · 1-3 episode each · 3-8 nights each)")

    ok1 = test_1_two_seeds_differ()
    ok2 = test_2_variance_positive()
    ok3 = test_3_anchor_not_always_earliest()

    print()
    print("═" * 75)
    print(f" SUMMARY · {'ALL PASS' if (ok1 and ok2 and ok3) else 'FAIL'}")
    print("═" * 75)
    print(f"  Test 1 (2 seed khác):                        {'PASS' if ok1 else 'FAIL'}")
    print(f"  Test 2 (variance > 0):                       {'PASS' if ok2 else 'FAIL'}")
    print(f"  Test 3 (anchor ≠ earliest ở ≥1 episode):     {'PASS' if ok3 else 'FAIL'}")
    print()
    print("Ranh giới: DRAFT · chưa pin · chưa chạy dữ thật · chờ ANALYSIS R1b.2")
