"""R1b · PSEUDO-BELL đo NỀN · code đóng băng tới 31/10.

Nguồn phán: docs/analysis_rulings_holdout_20260924.md · md5 04f2826b884bde92ceb994af75bc849d
  · mục 1 point 2 (pseudo-bell design)
  · mục 2 R1b-1 (tham số nguyên văn)

Tham số R1b-1 (đã ANALYSIS ký):
  · SEED = 20260924
  · R = 500 lần lặp
  · Rút token-night đang hedge (div_avg3(D) ≤ 0.5) trong dải b · KHÔNG hoàn lại
  · Gộp episode 14d Y HỆT chuông
  · Loại outage 24-26/07 (episode có [D_anchor-2, D_anchor+10] chạm outage → bỏ)
  · Cửa sổ calibration <20/09 (trước hold-out): 06-19 → 09-05 (per V3)
  · n≥50 episode/dải · dải không đủ 50 → N/A · KHÔNG hạ n · KHÔNG nới cách rút
  · Báo: trung vị + [5%, 95%] cho rate per dải · lift chấm dùng median(base_b)

Vật đo:
  · TỪNG lần lặp: rút R token-night ngẫu nhiên trong dải b (không hoàn lại)
  · Gộp thành episodes 14d
  · Với mỗi episode: neo D_anchor = ngày đầu (per gộp 14d)
  · Cross-check [D_anchor+1, D_anchor+10]
  · Loại outage
  · Lấy episodes trong dải b (>50 hoặc N/A)
  · Rate = n_hit / n_episode trong dải
  · Sau R lần lặp: median · [5%, 95%] percentile của rate

KHÔNG chạy trong file này · file được import bởi _probe_r1b_run_20260924.py để chạy.
"""
from __future__ import annotations
import csv, math, os, random
from pathlib import Path
from datetime import datetime, timedelta

_REPO = Path("/root/Data_back_test/whale_data") if os.name != "nt" \
        else Path(r"D:/Data back test/whale_data")

# Tham số R1b-1 (đã ANALYSIS ký · KHÔNG sửa cho tới 31/10)
SEED = 20260924
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
    """Load freshwatch csv per month · trả dict {sym_bare: [row_dict, ...]}."""
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
    """Copy species_tag._div_avg3 · pos_r/acc_r mean 3d (target-2, target-1, target).
    KHÔNG import prod để đóng băng · pin md5 file này."""
    td = datetime.strptime(target_date, "%Y-%m-%d").date()
    ratios = []
    for d in range(2, -1, -1):
        dt = (td - timedelta(days=d)).isoformat()
        # find row for dt
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
    """Trả date-str đầu tiên có vp≤0.5 · v>0.5 trong [d_start, d_end], None nếu không."""
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
    """[D-2, D+10] chạm outage → True."""
    for i in range(-2, FORWARD_MAX + 1):
        dd = d + timedelta(days=i)
        if (dd.year, dd.month, dd.day) in OUTAGE_DATES:
            return True
    return False


def _bucket_of(div_val):
    for name, lo, hi in BUCKETS:
        if lo <= div_val < hi:
            return name
    return None


def scan_all_hedge_nights(by_sym, universe, calib_start, calib_end):
    """Trả list of (tok, D_date, div_D) cho mọi token-night đang hedge (div_avg3 ≤ 0.5)
    trong cửa sổ calibration."""
    all_nights = []
    d_start = datetime.strptime(calib_start, "%Y-%m-%d").date()
    d_end = datetime.strptime(calib_end, "%Y-%m-%d").date()
    for tok in universe:
        if tok not in by_sym: continue
        rows = by_sym[tok]
        d = d_start
        while d <= d_end:
            div_D = _div_avg3(rows, d.isoformat())
            if div_D is not None and div_D <= 0.5:
                all_nights.append((tok, d, div_D))
            d += timedelta(days=1)
    return all_nights


def group_into_episodes(nights_sorted_by_tok):
    """Nhận list (tok, D, div_D) đã sort theo (tok, D).
    Gộp consecutive (cùng tok · gap ≤14d) thành episode.
    Trả list of episodes, each = list of (tok, D, div_D)."""
    if not nights_sorted_by_tok: return []
    episodes = [[nights_sorted_by_tok[0]]]
    for tok, D, div_D in nights_sorted_by_tok[1:]:
        prev_tok, prev_D, _ = episodes[-1][-1]
        if tok == prev_tok and (D - prev_D).days <= GAP_DAYS:
            episodes[-1].append((tok, D, div_D))
        else:
            episodes.append([(tok, D, div_D)])
    return episodes


def bucket_episodes_by_first_div(episodes):
    """Bucket episodes theo div tại D_first (chuông ĐẦU episode)."""
    buckets_ep = {name: [] for name, _, _ in BUCKETS}
    for ep in episodes:
        tok, D_first, div_first = ep[0]
        b = _bucket_of(div_first)
        if b is not None:
            buckets_ep[b].append((tok, D_first, div_first, ep))
    return buckets_ep


def score_episode(rows, D_first):
    """Cross-check [D_first+1, D_first+10] · trả (has_cross: bool, excl: bool)."""
    cross = _find_cross(rows, D_first + timedelta(days=FORWARD_MIN), D_first + timedelta(days=FORWARD_MAX))
    excl = _touches_outage(D_first)
    return (cross is not None, excl)


def resample_pseudo_bells_rate(by_sym, universe, seed, r_iterations):
    """Vòng chính: R lần lặp resample.
    Mỗi lần: rút không hoàn lại token-night trong dải b · gộp episode 14d · đo rate.
    Trả dict per bucket: {rate list · n_iterations reaching n_min · n_iterations total}.
    """
    rng = random.Random(seed)
    # 1. Lấy tất cả token-night hedge
    all_nights = scan_all_hedge_nights(by_sym, universe, CALIB_START, CALIB_END)
    # 2. Phân dải theo div_D
    nights_by_bucket = {name: [] for name, _, _ in BUCKETS}
    for tok, D, div_D in all_nights:
        b = _bucket_of(div_D)
        if b: nights_by_bucket[b].append((tok, D, div_D))

    result = {name: {"rates": [], "n_ep_list": [], "n_reached": 0} for name, _, _ in BUCKETS}

    for iteration in range(r_iterations):
        # Với mỗi bucket: rút NGẪU NHIÊN KHÔNG HOÀN LẠI · gộp 14d · đo rate
        for name, _, _ in BUCKETS:
            pool = nights_by_bucket[name][:]  # copy
            rng.shuffle(pool)  # random order (uniform draw without replacement)
            # Gộp thành episodes 14d
            # Tokens có thể xuất hiện nhiều lần · gộp theo (tok, D)
            pool_sorted = sorted(pool, key=lambda x: (x[0], x[1]))
            episodes = group_into_episodes(pool_sorted)
            # Loại outage · đếm rate
            n_ep_valid = 0
            n_hit_valid = 0
            for ep in episodes:
                tok, D_first, div_first = ep[0]
                rows = by_sym[tok]
                has_cross, excl = score_episode(rows, D_first)
                if excl: continue
                n_ep_valid += 1
                if has_cross: n_hit_valid += 1
            result[name]["n_ep_list"].append(n_ep_valid)
            if n_ep_valid >= N_MIN_PER_BUCKET:
                result[name]["n_reached"] += 1
                result[name]["rates"].append(n_hit_valid / n_ep_valid * 100)
            # else: skip (không hạ n · KHÔNG add rate)

    return result, nights_by_bucket


if __name__ == "__main__":
    import sys, io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    print("R1b · pseudo-bell library · KHÔNG chạy trực tiếp (dùng module)")
    print(f"SEED={SEED} · R={R_ITERATIONS} · GAP={GAP_DAYS}d · N_MIN={N_MIN_PER_BUCKET}/bucket")
    print(f"CALIB {CALIB_START} → {CALIB_END} · outage {OUTAGE_DATES}")
