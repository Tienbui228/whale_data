"""R1b2 · Pseudo-bell nền · thuật toán ANALYSIS đã ký 24/09.

Nguồn phán: docs/analysis_rulings_holdout_20260924.md md5 04f2826b884bde92ceb994af75bc849d
  + DEV R1b.2 signed algo (registration mới).

Sửa lỗi R1b-base cec7dc89:
  · CŨ: sort(tok,D) sau shuffle → deterministic + anchor = ep[0] = đêm sớm nhất
  · MỚI: KHÔNG gộp episode trước · duyệt theo thứ tự TRỘN · nhận 1 neo cho tok
         nếu tok chưa có neo trong [D-14, D+14] TRONG DẢI · dừng khi đủ 50 neo.

Thuật toán nguyên văn ANALYSIS ký (mỗi dải b, mỗi lần lặp i):
  seed_i = 20260924 + i
  pool_b = token-night đang hedge (div_avg3(D) ∈ b), cửa sổ 2026-06-19 → 2026-09-05,
           loại outage 24-26/07 (ở đây: loại từ pool BEFORE mixing)
  Trộn pool_b theo seed_i · duyệt theo thứ tự trộn
  Nhận đêm (tok, D) làm neo NẾU:
    tok chưa có neo đã nhận trong [D-14, D+14] TRONG DẢI b
  Dừng khi đủ n_min=50 neo
  KHÔNG đủ 50 → lần lặp N/A cho dải b
  base_b,i = n_hit / 50 · n_hit = số neo có cross-0.5 trong [D+1, D+10]

Báo: median · [5%, 95%] · số lần đủ 50 / 500 per dải.

Code này DÙNG làm thư viện · runner riêng gọi `resample_r1b2()`.
"""
from __future__ import annotations
import csv, math, os, random
from pathlib import Path
from datetime import datetime, timedelta

_REPO = Path("/root/Data_back_test/whale_data") if os.name != "nt" \
        else Path(r"D:/Data back test/whale_data")

# Tham số R1b.2 (ANALYSIS ký · đóng băng tới 2026-10-31)
BASE_SEED = 20260924
R_ITERATIONS = 500
GAP_DAYS = 14
FORWARD_MIN = 1
FORWARD_MAX = 10
N_MIN_PER_BUCKET = 50
OUTAGE_DATES = {(2026, 7, 24), (2026, 7, 25), (2026, 7, 26)}
CALIB_START = "2026-06-19"
CALIB_END = "2026-09-05"
BUCKETS = [("<0.3", 0.0, 0.3), ("[0.3,0.4)", 0.3, 0.4), ("[0.4,0.5]", 0.4, 0.5 + 1e-9)]


def _load_by_sym(months=("05","06","07","08","09")):
    by_sym = {}
    for m in months:
        p = _REPO / f"data/export/freshwatch_daily_2026-{m}.csv"
        if not p.exists(): continue
        with p.open(encoding="utf-8", newline="") as f:
            for r in csv.DictReader(f):
                sym = r["symbol"]
                bare = sym.replace("USDT", "") if sym.endswith("USDT") else sym
                by_sym.setdefault(bare, []).append(r)
    return by_sym


def _load_universe():
    fw_p = _REPO / "data/config/freshwatch_symbols.txt"
    return [l.strip().replace("USDT","") for l in fw_p.read_text(encoding="utf-8").splitlines() if l.strip()]


def _flt(v):
    if v is None or v == "": return None
    try:
        f = float(v)
        return None if math.isnan(f) else f
    except: return None


def _div_avg3(rows, target_date):
    td = datetime.strptime(target_date, "%Y-%m-%d").date()
    ratios = []
    for d in range(2, -1, -1):
        dt = (td - timedelta(days=d)).isoformat()
        pos = None; acc = None
        for r in rows:
            if r["date"] == dt:
                pos = _flt(r.get("lsr_pos_r"))
                acc = _flt(r.get("lsr_acc_r"))
                break
        if pos is None or acc is None or acc <= 0: continue
        ratios.append(pos / acc)
    if len(ratios) < 3: return None
    return sum(ratios) / len(ratios)


def _find_cross(rows, d_start, d_end):
    d = d_start
    while d <= d_end:
        dt = d.isoformat()
        dt_prev = (d - timedelta(days=1)).isoformat()
        v = _div_avg3(rows, dt)
        vp = _div_avg3(rows, dt_prev)
        if v is not None and vp is not None and vp <= 0.5 and v > 0.5:
            return dt
        d += timedelta(days=1)
    return None


def _touches_outage(d):
    for i in range(-2, FORWARD_MAX + 1):
        dd = d + timedelta(days=i)
        if (dd.year, dd.month, dd.day) in OUTAGE_DATES:
            return True
    return False


def _bucket_of(v):
    for name, lo, hi in BUCKETS:
        if lo <= v < hi: return name
    return None


def build_pool_by_bucket(by_sym, universe, calib_start=CALIB_START, calib_end=CALIB_END):
    """Trả dict {bucket_name: [(tok, D_date, div_D), ...]} · KHÔNG lọc outage ở đây.
    Loại outage áp sau: từ pool BEFORE mixing · theo outage_fn.

    Đọc phán: 'loại outage 24-26/07' — loại các đêm có D ∈ [D-2, D+10] chạm outage
    (tránh trùng với sự kiện outage · giữ tương thích tiêu chuẩn R1a/R1b-base).
    Ở đây loại luôn từ pool để không bao giờ được chọn làm neo.
    """
    from_d = datetime.strptime(calib_start, "%Y-%m-%d").date()
    to_d = datetime.strptime(calib_end, "%Y-%m-%d").date()
    pool = {name: [] for name, _, _ in BUCKETS}
    for tok in universe:
        if tok not in by_sym: continue
        rows = by_sym[tok]
        d = from_d
        while d <= to_d:
            div_D = _div_avg3(rows, d.isoformat())
            if div_D is not None and div_D <= 0.5:
                b = _bucket_of(div_D)
                if b is not None and not _touches_outage(d):
                    pool[b].append((tok, d, div_D))
            d += timedelta(days=1)
    return pool


def resample_iteration_for_bucket(pool_b, bucket_name, seed_i, cross_check_fn,
                                    n_min=N_MIN_PER_BUCKET, gap=GAP_DAYS):
    """Một lần lặp thuật toán R1b.2 cho 1 bucket.

    Args:
      pool_b: list of (tok, D_date, div_D) TRONG dải b (đã lọc outage)
      cross_check_fn: (tok, d_start, d_end) → bool có cross trong [d_start, d_end]
    Returns:
      (rate or None, n_neo, anchors_list) · rate None nếu KHÔNG đủ n_min
    """
    rng = random.Random(seed_i)
    order = pool_b[:]
    rng.shuffle(order)  # thứ tự trộn (mỗi seed_i khác nhau)

    accepted = []  # list (tok, D_date, div_D)
    accepted_by_tok = {}  # tok → list of accepted dates in bucket b
    for tok, D, div_D in order:
        # Reject nếu tok đã có neo đã nhận trong [D-14, D+14] TRONG DẢI b
        conflict = False
        for prev_D in accepted_by_tok.get(tok, []):
            if abs((D - prev_D).days) <= gap:
                conflict = True
                break
        if not conflict:
            accepted.append((tok, D, div_D))
            accepted_by_tok.setdefault(tok, []).append(D)
        if len(accepted) >= n_min:
            break

    if len(accepted) < n_min:
        return None, len(accepted), accepted

    # Đếm cross · KHÔNG cần loại outage lần nữa (pool đã loại)
    n_hit = 0
    for tok, D, _ in accepted:
        if cross_check_fn(tok, D + timedelta(days=FORWARD_MIN), D + timedelta(days=FORWARD_MAX)):
            n_hit += 1
    return n_hit / len(accepted) * 100, len(accepted), accepted


def resample_r1b2(pool_by_bucket, cross_check_fn, r_iterations=R_ITERATIONS,
                    base_seed=BASE_SEED, n_min=N_MIN_PER_BUCKET, gap=GAP_DAYS):
    """Toàn bộ R lần lặp · trả dict per bucket."""
    result = {name: {"rates": [], "n_neo_list": [], "n_reached": 0,
                     "anchors_first_iter": None}
              for name, _, _ in BUCKETS}
    for i in range(r_iterations):
        seed_i = base_seed + i
        for name, _, _ in BUCKETS:
            rate, n_neo, anchors = resample_iteration_for_bucket(
                pool_by_bucket[name], name, seed_i, cross_check_fn, n_min, gap)
            result[name]["n_neo_list"].append(n_neo)
            if rate is not None:
                result[name]["rates"].append(rate)
                result[name]["n_reached"] += 1
            # Save first iter anchors for P4 debugging
            if i == 0:
                result[name]["anchors_first_iter"] = anchors
    return result


def make_cross_check_fn_from_by_sym(by_sym):
    """Wrap _find_cross để dùng cho resample_r1b2."""
    def check(tok, d_start, d_end):
        if tok not in by_sym: return False
        rows = by_sym[tok]
        return _find_cross(rows, d_start, d_end) is not None
    return check


if __name__ == "__main__":
    import sys, io, hashlib
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    self_md5 = hashlib.md5(Path(__file__).read_bytes()).hexdigest()
    print(f"R1b2 pseudo-bell lib · md5={self_md5}")
    print(f"BASE_SEED={BASE_SEED} · R={R_ITERATIONS} · GAP={GAP_DAYS}d · N_MIN={N_MIN_PER_BUCKET}")
    print(f"CALIB {CALIB_START} → {CALIB_END} · BUCKETS={[b[0] for b in BUCKETS]}")
    print("KHÔNG chạy trực tiếp · module import + gọi resample_r1b2()")
