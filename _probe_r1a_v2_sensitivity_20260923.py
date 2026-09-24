"""R1a.v2 · sensitivity analysis · so bucket khi neo tại
  · D_first (canonical · đã pin R1a)
  · D_middle (ngày giữa episode · median index)
  · D_lowdiv (ngày có div thấp nhất trong episode)

CHỈ in số · KHÔNG đổi R1a · KHÔNG đổi luật.
"""
import sys, os, csv, math, io
from pathlib import Path
from datetime import datetime, timedelta
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

_REPO = Path("/root/Data_back_test/whale_data") if os.name != "nt" \
        else Path(r"D:/Data back test/whale_data")
sys.path.insert(0, str(_REPO / "scripts"))

import importlib
import species_tag; importlib.reload(species_tag)
from species_tag import _div_avg3

TARGET = "2026-09-17"
TODAY = datetime.strptime(TARGET, "%Y-%m-%d").date()

by_sym = {}
for m in ["05","06","07","08","09"]:
    p = _REPO / f"data/export/freshwatch_daily_2026-{m}.csv"
    if not p.exists(): continue
    with p.open(encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            sym = r["symbol"]
            bare = sym.replace("USDT","") if sym.endswith("USDT") else sym
            by_sym.setdefault(bare, []).append(r)

fw_p = _REPO / "data/config/freshwatch_symbols.txt"
universe = [l.strip().replace("USDT","") for l in fw_p.read_text(encoding="utf-8").splitlines() if l.strip()]

WINDOW_START = TODAY - timedelta(days=90)
WINDOW_END = TODAY - timedelta(days=12)
EXCL_DATES = {(2026, 7, 24), (2026, 7, 25), (2026, 7, 26)}

def _touches_excl(d):
    for i in range(-2, 11):
        dd = d + timedelta(days=i)
        if (dd.year, dd.month, dd.day) in EXCL_DATES:
            return True
    return False

def find_cross(rows, d_start, d_end):
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

def scan_baseline_nights(rows):
    nights = []
    d = WINDOW_START
    while d <= WINDOW_END:
        div_D = _div_avg3(rows, d.isoformat())
        if div_D is not None and div_D <= 0.5:
            nights.append((d, div_D))
        d += timedelta(days=1)
    return nights

def group_episodes(nights, gap_days=14):
    if not nights: return []
    episodes = [[nights[0]]]
    for date, div_D in nights[1:]:
        prev_date = episodes[-1][-1][0]
        if (date - prev_date).days > gap_days:
            episodes.append([(date, div_D)])
        else:
            episodes[-1].append((date, div_D))
    return episodes

# Build episodes
episodes_by_tok = []
for tok in universe:
    if tok not in by_sym: continue
    rows = by_sym[tok]
    nights = scan_baseline_nights(rows)
    for ep in group_episodes(nights, gap_days=14):
        episodes_by_tok.append((tok, ep, rows))

def _bucket(v):
    if v < 0.3: return "<0.3"
    if v < 0.4: return "0.3-0.4"
    return "0.4-0.5"

def _run(anchor_fn, name):
    """anchor_fn(ep) → (d_anchor, div_anchor)"""
    print(f"\n═══ Anchor: {name} ═══")
    buckets_all = {"<0.3": [], "0.3-0.4": [], "0.4-0.5": []}
    buckets_excl = {"<0.3": [], "0.3-0.4": [], "0.4-0.5": []}
    for tok, ep, rows in episodes_by_tok:
        d_anchor, div_anchor = anchor_fn(ep)
        cr = find_cross(rows, d_anchor + timedelta(days=1), d_anchor + timedelta(days=10))
        excl = _touches_excl(d_anchor)
        b = _bucket(div_anchor)
        record = (tok, d_anchor.isoformat(), div_anchor, cr, excl)
        buckets_all[b].append(record)
        if not excl: buckets_excl[b].append(record)

    def _rate(rows):
        n = len(rows); h = sum(1 for r in rows if r[3] is not None)
        return h, n, (h/n*100 if n>0 else 0)

    print(f"  {'bucket':>10s} | {'n_num':>6s} | {'n_denom':>8s} | {'rate':>7s} · goc")
    for b, rows in buckets_all.items():
        h, n, r = _rate(rows)
        r_str = f"{r:.2f}%" if n>0 else "∅"
        print(f"  {b:>10s} | {h:>6d} | {n:>8d} | {r_str:>7s}")
    total_goc = sum(len(v) for v in buckets_all.values())
    total_hit_goc = sum(sum(1 for r in v if r[3] is not None) for v in buckets_all.values())
    print(f"  TOTAL goc: n_denom={total_goc} n_num={total_hit_goc} rate={total_hit_goc/total_goc*100:.2f}%")

    print(f"\n  {'bucket':>10s} | {'n_num':>6s} | {'n_denom':>8s} | {'rate':>7s} · loai outage")
    for b, rows in buckets_excl.items():
        h, n, r = _rate(rows)
        r_str = f"{r:.2f}%" if n>0 else "∅"
        print(f"  {b:>10s} | {h:>6d} | {n:>8d} | {r_str:>7s}")
    total_excl = sum(len(v) for v in buckets_excl.values())
    total_hit_excl = sum(sum(1 for r in v if r[3] is not None) for v in buckets_excl.values())
    print(f"  TOTAL loai: n_denom={total_excl} n_num={total_hit_excl} rate={total_hit_excl/total_excl*100:.2f}%")

# Anchor 1 · D_first (canonical R1a)
def anchor_first(ep):
    return ep[0]  # first (date, div)

# Anchor 2 · middle-of-episode (median index)
def anchor_middle(ep):
    return ep[len(ep) // 2]

# Anchor 3 · lowest-div-in-episode
def anchor_lowdiv(ep):
    return min(ep, key=lambda x: x[1])

print(f"NGUỒN: probe `_probe_r1a_episode_20260923.py:113-128` (canonical D_first anchor)")
print(f"WINDOW: 2026-06-19 → 2026-09-05 · TOTAL episodes: {len(episodes_by_tok)}\n")
print(f"Định nghĩa neo canonical (R1a pinned):")
print(f"  · '_probe_r1a_episode_20260923.py' function scan_baseline_nights → group_episodes → ep[0] = (D_first, div_first)")
print(f"  · Nguồn: _probe_r1a_episode_20260923.py:107-110 vòng lặp episodes, dòng `d_first, div_first = ep[0]  # chuông đầu episode`")
print(f"  · Đối chiếu registration L64 C9 verbatim: 'div đo tại D của chuông ĐẦU episode'")

_run(anchor_first, "D_first (CANONICAL · R1a pinned)")
_run(anchor_middle, "D_middle (ngày giữa episode · sensitivity)")
_run(anchor_lowdiv, "D_lowdiv (ngày div thấp nhất · sensitivity)")

print(f"\n═══ SENSITIVITY: KHÔNG đổi R1a · chỉ in để ANALYSIS thấy độ nhạy ═══")
