"""R1a · V6 nền episode theo dải · gốc + loại outage.

Episode = chuỗi token-night baseline (div_avg3(D) ≤ 0.5) liên tiếp;
episodes cùng token cách nhau ≥14 ngày = episode mới (gộp 14d).

Kết cục = có cross (vp≤0.5 → v>0.5) trong [D_first+1, D_first+10]
  · trong đó D_first = chuông ĐẦU episode (Q1 + C9).

Outage filter (C8b): loại episode có [D_first-2, D_first+10] ∩ {24,25,26/07} ≠ ∅.

Dải: {<0.3, [0.3, 0.4), [0.4, 0.5]} với div đo tại D_first.
Dải 0 episode → w=0, "∅".
"""
import sys, os, csv, math, io, json, hashlib
from pathlib import Path
from datetime import datetime, timedelta
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

_REPO = Path("/root/Data_back_test/whale_data") if os.name != "nt" \
        else Path(r"D:/Data back test/whale_data")
sys.path.insert(0, str(_REPO / "scripts"))

import importlib
import species_tag; importlib.reload(species_tag)
from species_tag import _div_avg3

TARGET = "2026-09-17"  # cùng TARGET as V3 · để so sánh so-với 33.4% token-night
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

def scan_baseline_nights(tok, rows):
    """Trả list of (date, div_D)."""
    nights = []
    d = WINDOW_START
    while d <= WINDOW_END:
        div_D = _div_avg3(rows, d.isoformat())
        if div_D is not None and div_D <= 0.5:
            nights.append((d, div_D))
        d += timedelta(days=1)
    return nights

def group_episodes(nights, gap_days=14):
    """Group consecutive baseline nights into episodes; new episode when gap > gap_days.
    Trả list of episodes, each = list of (date, div_D)."""
    if not nights: return []
    episodes = [[nights[0]]]
    for date, div_D in nights[1:]:
        prev_date = episodes[-1][-1][0]
        if (date - prev_date).days > gap_days:
            episodes.append([(date, div_D)])
        else:
            episodes[-1].append((date, div_D))
    return episodes

# ═════ Build episode list ═════
episodes_all = []  # (tok, d_first, div_first, cross_or_None, excl)
for tok in universe:
    if tok not in by_sym: continue
    rows = by_sym[tok]
    nights = scan_baseline_nights(tok, rows)
    for ep in group_episodes(nights, gap_days=14):
        d_first, div_first = ep[0]  # chuông đầu episode
        cross = find_cross(rows, d_first + timedelta(days=1), d_first + timedelta(days=10))
        excl = _touches_excl(d_first)
        episodes_all.append((tok, d_first.isoformat(), div_first, cross, excl))

n_ep_all = len(episodes_all)
n_hit_all = sum(1 for e in episodes_all if e[3] is not None)
rate_all = n_hit_all / n_ep_all * 100 if n_ep_all > 0 else 0

# Loại outage
episodes_excl = [e for e in episodes_all if not e[4]]
n_ep_excl = len(episodes_excl)
n_hit_excl = sum(1 for e in episodes_excl if e[3] is not None)
rate_excl = n_hit_excl / n_ep_excl * 100 if n_ep_excl > 0 else 0

# ═════ Print gốc + loại outage ═════
print(f"═══ R1a · V6 nền episode ═══\n")
print(f"NGUỒN: data/export/freshwatch_daily_2026-{{05..09}}.csv")
print(f"WINDOW: {WINDOW_START.isoformat()} → {WINDOW_END.isoformat()} ({(WINDOW_END-WINDOW_START).days+1} ngày)")
print(f"GATE: div_avg3(D) ≤ 0.5 · GROUP: gap-14d episode · FORWARD: [D_first+1, D_first+10]")
print(f"OUTAGE FILTER: [D_first-2, D_first+10] ∩ {{24,25,26/07/2026}} ≠ ∅ → loại\n")

print(f"─── Bảng R1a.a · GỐC (không loại outage) ───")
print(f"n_denom (episodes): {n_ep_all}")
print(f"n_num   (cross trong [D+1, D+10] từ D_first): {n_hit_all}")
print(f"rate = n_num / n_denom = {rate_all:.2f}%\n")

print(f"─── Bảng R1a.b · LOẠI outage ───")
n_removed = n_ep_all - n_ep_excl
print(f"n_loại: {n_removed}")
print(f"n_denom' (giữ): {n_ep_excl}")
print(f"n_num'   (giữ · cross): {n_hit_excl}")
print(f"rate' = {rate_excl:.2f}% · so với gốc: {rate_excl-rate_all:+.2f} pp\n")

# ═════ Rate theo dải ═════
def _bucket(v):
    if v < 0.3: return "<0.3"
    if v < 0.4: return "0.3-0.4"
    return "0.4-0.5"

buckets_all = {"<0.3": [], "0.3-0.4": [], "0.4-0.5": []}
buckets_excl = {"<0.3": [], "0.3-0.4": [], "0.4-0.5": []}
for e in episodes_all:
    b = _bucket(e[2])
    buckets_all[b].append(e)
    if not e[4]:
        buckets_excl[b].append(e)

def _rate(rows):
    n = len(rows); h = sum(1 for r in rows if r[3] is not None)
    return h, n, (h/n*100 if n>0 else 0)

print(f"─── Bảng R1a.c · rate theo dải div_avg3(D_first) · GỐC ───")
print(f"{'bucket':>10s} | {'n_num':>7s} | {'n_denom':>8s} | {'rate':>7s}")
print(f"{'-'*10} | {'-'*7} | {'-'*8} | {'-'*7}")
bucket_summary_all = {}
for name, rows in buckets_all.items():
    h, n, r = _rate(rows)
    bucket_summary_all[name] = {"n_num": h, "n_denom": n, "rate": r}
    r_str = f"{r:.2f}%" if n > 0 else "∅ (w=0)"
    print(f"{name:>10s} | {h:>7d} | {n:>8d} | {r_str:>7s}")

print(f"\n─── Bảng R1a.d · rate theo dải · LOẠI outage ───")
print(f"{'bucket':>10s} | {'n_num':>7s} | {'n_denom':>8s} | {'rate':>7s}")
print(f"{'-'*10} | {'-'*7} | {'-'*8} | {'-'*7}")
bucket_summary_excl = {}
for name, rows in buckets_excl.items():
    h, n, r = _rate(rows)
    bucket_summary_excl[name] = {"n_num": h, "n_denom": n, "rate": r}
    r_str = f"{r:.2f}%" if n > 0 else "∅ (w=0)"
    print(f"{name:>10s} | {h:>7d} | {n:>8d} | {r_str:>7s}")

# ═════ Dump results as JSON for addendum ═════
result = {
    "goc": {
        "n_denom": n_ep_all, "n_num": n_hit_all, "rate": rate_all,
        "buckets": bucket_summary_all,
    },
    "loai_outage": {
        "n_loai": n_removed, "n_denom": n_ep_excl, "n_num": n_hit_excl, "rate": rate_excl,
        "buckets": bucket_summary_excl,
    },
    "window_start": WINDOW_START.isoformat(),
    "window_end": WINDOW_END.isoformat(),
    "target": TARGET,
    "gap_days": 14,
    "forward_range": "[D_first+1, D_first+10]",
    "outage_dates": ["2026-07-24","2026-07-25","2026-07-26"],
}
out = Path("scratch/R1a_episode_baseline.json")
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"\n[out] {out} · md5={hashlib.md5(out.read_bytes()).hexdigest()}")
