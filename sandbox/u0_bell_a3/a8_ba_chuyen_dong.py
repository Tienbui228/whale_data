"""A8 · BẢNG BA CHUYỂN ĐỘNG · đợt 1 vs đợt 2+ · READ, không rule.

Bốn mốc/đợt: acc-drop · div-cross · pos-rise · OI-at-each
Cửa sổ mỗi đợt: [mốc sớm nhất − 10d, D0_đợt + 10d]
Hold-out: max_date < 2026-09-20.
"""
import sys, csv, importlib, math
from pathlib import Path
from datetime import datetime, timedelta
try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except: pass  # L-66-OK
sys.path.insert(0, r"d:\Data back test\whale_data\scripts")
sys.path.insert(0, r"d:\Data back test\whale_data\sandbox\u0_bell_a3")
import u0_bell as u0mod; importlib.reload(u0mod)
import species_tag; importlib.reload(species_tag)
from species_tag import _div_avg3
from u0_bell import delta_bwd

HOLDOUT_START = datetime(2026, 9, 20).date()

by_sym = {}
max_date_used = "0000-00-00"
for m in ["05","06","07","08","09"]:
    p = Path(rf"d:\Data back test\whale_data\data\export\freshwatch_daily_2026-{m}.csv")
    if not p.exists(): continue
    with p.open(encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            sym = r["symbol"]
            # Preserve Chinese chars for 龙虾
            bare = sym[:-4] if sym.endswith("USDT") else sym
            d_iso = r["date"]
            d_row = datetime.strptime(d_iso, "%Y-%m-%d").date()
            if d_row < HOLDOUT_START:
                by_sym.setdefault(bare, []).append(r)
                if d_iso > max_date_used:
                    max_date_used = d_iso

print(f"═══ A8-5 · HOLD-OUT GUARD: max_date_used = {max_date_used} < 2026-09-20 · {'PASS' if max_date_used < '2026-09-20' else 'FAIL'} ═══\n")

def _flt(v):
    if v is None or v == "": return None
    try:
        f = float(v)
        return None if math.isnan(f) else f
    except: return None

def _get(rows, dt, field):
    for r in rows:
        if r["date"] == dt: return _flt(r.get(field))
    return None

def find_first_acc_drop(rows, w_start, w_end, threshold=-0.20):
    d = w_start
    while d <= w_end:
        dacc, _, _ = delta_bwd(rows, d.isoformat(), "lsr_acc_r")
        if dacc is not None and dacc <= threshold:
            return d.isoformat(), dacc
        d += timedelta(days=1)
    return None, None

def find_first_div_cross(rows, w_start, w_end):
    d = w_start
    while d <= w_end:
        dt = d.isoformat()
        dt_prev = (d - timedelta(days=1)).isoformat()
        v = _div_avg3(rows, dt); vp = _div_avg3(rows, dt_prev)
        if v is not None and vp is not None and vp <= 0.5 and v > 0.5:
            return dt, v
        d += timedelta(days=1)
    return None, None

def find_first_pos_rise(rows, w_start, w_end, threshold=0.10):
    """Δpos_bwd(D) = (pos(D) − pos(D−3)) / pos(D−3) ≥ +threshold."""
    d = w_start
    while d <= w_end:
        dpos, _, _ = delta_bwd(rows, d.isoformat(), "lsr_pos_r")
        if dpos is not None and dpos >= threshold:
            return d.isoformat(), dpos
        d += timedelta(days=1)
    return None, None

# ═════════════════════════════
# Cases · từng đợt · (token, đợt, D0, cửa sổ tiếp cận · ANALYSIS ký)
# ═════════════════════════════
# Format: token, ep_label, D0, w_hint_start (for pre-search anchor), w_hint_end
CASES = [
    # BULLA
    ("BULLA",   "sóng 1",      "2026-07-20",  "2026-06-25", "2026-07-30"),
    ("BULLA",   "sóng 2",      "2026-09-05",  "2026-08-20", "2026-09-15"),
    # HEMI
    ("HEMI",    "wave-1 20/07","2026-07-20",  "2026-06-25", "2026-07-30"),
    ("HEMI",    "D0 15/08",    "2026-08-15",  "2026-07-25", "2026-08-25"),
    # UAI
    ("UAI",     "pump#1",      "2026-07-07",  "2026-06-15", "2026-07-17"),
    ("UAI",     "push 24/08",  "2026-08-24",  "2026-08-05", "2026-09-03"),
    # 龙虾 (LOBSTER)
    ("龙虾",    "D0 25/08",    "2026-08-25",  "2026-08-05", "2026-09-04"),
    ("龙虾",    "leg 2 29/08", "2026-08-29",  "2026-08-19", "2026-09-08"),
    # MITO
    ("MITO",    "đạp 28/08",   "2026-08-28",  "2026-08-15", "2026-09-07"),
    ("MITO",    "long 10-11/09", "2026-09-10","2026-08-31", "2026-09-19"),
    # MARSCOIN
    ("MARSCOIN","D0 03/09",    "2026-09-03",  "2026-08-15", "2026-09-13"),
    ("MARSCOIN","rebuild 07-10/09", "2026-09-08", "2026-08-25", "2026-09-18"),
    # CYS
    ("CYS",     "D0 04/08",    "2026-08-04",  "2026-07-15", "2026-08-14"),
    ("CYS",     "13-15/08",    "2026-08-14",  "2026-07-25", "2026-08-24"),
    # PROM (3 sóng)
    ("PROM",    "sóng 1",      "2026-07-19",  "2026-06-25", "2026-07-29"),
    ("PROM",    "sóng 2",      "2026-08-05",  "2026-07-15", "2026-08-15"),
    ("PROM",    "sóng 3",      "2026-08-25",  "2026-08-05", "2026-09-04"),
]

def guard_holdout(dt_str):
    return dt_str is not None and dt_str < "2026-09-20"

results = []

print("═══ A8-2 · Bảng bốn cột ngày mỗi đợt · KHÔNG suy · KHÔNG chuông ═══\n")
print(f"{'ca':<28} {'D0':<12} {'cửa sổ':<25} {'acc-drop':<12} {'div-cross':<12} {'pos-rise':<12} {'thứ tự':<20}")
print("─" * 130)

for tok, ep, D0, wh_s, wh_e in CASES:
    rows = by_sym.get(tok, [])
    if not rows:
        print(f"  {tok+' · '+ep:<28} {'[NO-DATA in fw store]':<70}")
        results.append({"tok": tok, "ep": ep, "status": "NO-DATA"})
        continue

    # Cửa sổ: hint start → hint end (rộng hơn D0+10 để chắc chắn tìm được mốc sớm nhất)
    w_start = datetime.strptime(wh_s, "%Y-%m-%d").date()
    w_end = min(datetime.strptime(wh_e, "%Y-%m-%d").date(),
                HOLDOUT_START - timedelta(days=1))

    # Find 3 mốc
    acc_d, dacc_val = find_first_acc_drop(rows, w_start, w_end)
    div_d, div_val = find_first_div_cross(rows, w_start, w_end)
    pos_d, dpos_val = find_first_pos_rise(rows, w_start, w_end)

    # Hold-out guard on each mốc
    def _fmt_mark(md, val, unit):
        if md is None: return "─"
        if md >= "2026-09-20": return f"[NGOÀI] {md}"
        return f"{md} ({val*100:+.0f}%)" if val is not None else md

    acc_s = _fmt_mark(acc_d, dacc_val, "%")
    div_s = _fmt_mark(div_d, div_val, "")
    pos_s = _fmt_mark(pos_d, dpos_val, "%")

    # Adjust window: [min(3 marks) − 10d, D0 + 10d]
    marks = [d for d in (acc_d, div_d, pos_d) if d is not None and d < "2026-09-20"]
    if marks:
        earliest = min(marks)
        adj_start = datetime.strptime(earliest, "%Y-%m-%d").date() - timedelta(days=10)
    else:
        adj_start = w_start
    D0_d = datetime.strptime(D0, "%Y-%m-%d").date()
    adj_end = min(D0_d + timedelta(days=10), HOLDOUT_START - timedelta(days=1))
    adj_window = f"{adj_start}→{adj_end}"

    # Thứ tự
    order_items = [("acc", acc_d), ("div", div_d), ("pos", pos_d)]
    order_valid = [(name, d) for name, d in order_items if d and d < "2026-09-20"]
    order_valid.sort(key=lambda x: x[1])
    order_str = " → ".join(n for n, _ in order_valid) if order_valid else "─"

    print(f"  {tok+' · '+ep:<28} {D0:<12} {adj_window:<25} {acc_s:<12} {div_s:<12} {pos_s:<12} {order_str:<20}")

    results.append({
        "tok": tok, "ep": ep, "D0": D0, "window": adj_window,
        "acc_d": acc_d if acc_d and acc_d < "2026-09-20" else None,
        "div_d": div_d if div_d and div_d < "2026-09-20" else None,
        "pos_d": pos_d if pos_d and pos_d < "2026-09-20" else None,
        "order": order_str,
    })


# ── OI at each mốc + at D0 ──
print(f"\n═══ OI at each mốc + D0 (usd) ═══\n")
print(f"{'ca':<28} {'OI@acc':>12} {'OI@div':>12} {'OI@pos':>12} {'OI@D0':>12}")
print("─" * 82)
for r in results:
    if r.get("status") == "NO-DATA":
        continue
    rows = by_sym[r["tok"]]
    def _oi(d):
        if not d: return None
        return _get(rows, d, "oi_usd")
    oi_acc = _oi(r["acc_d"]); oi_div = _oi(r["div_d"]); oi_pos = _oi(r["pos_d"]); oi_d0 = _oi(r["D0"])
    def _fmt(v):
        if v is None: return "─"
        return f"{v/1e6:.2f}M"
    print(f"  {r['tok']+' · '+r['ep']:<28} {_fmt(oi_acc):>12} {_fmt(oi_div):>12} {_fmt(oi_pos):>12} {_fmt(oi_d0):>12}")


# ── Khoảng cách giữa các mốc ──
print(f"\n═══ Khoảng cách giữa các mốc (ngày, có dấu, tham chiếu = mốc sớm nhất) ═══\n")
print(f"{'ca':<28} {'earliest':<12} {'acc − earliest':>15} {'div − earliest':>15} {'pos − earliest':>15}")
print("─" * 90)
for r in results:
    if r.get("status") == "NO-DATA": continue
    marks = [(n, r[k]) for n, k in [("acc","acc_d"),("div","div_d"),("pos","pos_d")] if r.get(k)]
    if not marks:
        print(f"  {r['tok']+' · '+r['ep']:<28} {'─':<12}")
        continue
    marks.sort(key=lambda x: x[1])
    earliest_name, earliest_date = marks[0]
    earl_d = datetime.strptime(earliest_date, "%Y-%m-%d").date()
    def _diff(k):
        if not r.get(k): return "─"
        d = datetime.strptime(r[k], "%Y-%m-%d").date()
        return f"{(d - earl_d).days:+d}d"
    print(f"  {r['tok']+' · '+r['ep']:<28} {earliest_date+' ('+earliest_name+')':<12} {_diff('acc_d'):>15} {_diff('div_d'):>15} {_diff('pos_d'):>15}")


# ── A8-3 · Đếm tần suất thứ tự đợt 1 vs đợt 2+ ──
print(f"\n═══ A8-3 · Tần suất chuỗi thứ tự · đợt 1 vs đợt 2+ ═══\n")

from collections import Counter
ep1_orders = Counter()
ep2p_orders = Counter()
# Phân đợt 1 vs 2+: đơn giản - đợt đầu tiên trong CASES cho mỗi token là ep1
seen_tokens = set()
for r in results:
    if r.get("status") == "NO-DATA": continue
    is_first = r["tok"] not in seen_tokens
    seen_tokens.add(r["tok"])
    order = r["order"]
    if is_first:
        ep1_orders[order] += 1
    else:
        ep2p_orders[order] += 1

print("  Đợt 1 · tần suất:")
for order, n in ep1_orders.most_common():
    print(f"    {order:<20} {n}")

print(f"\n  Đợt 2+ · tần suất:")
for order, n in ep2p_orders.most_common():
    print(f"    {order:<20} {n}")

# Đợt 2+ có nghiêng về pos đi trước?
pos_first_1 = sum(n for o, n in ep1_orders.items() if o.startswith("pos"))
pos_first_2p = sum(n for o, n in ep2p_orders.items() if o.startswith("pos"))
total_1 = sum(ep1_orders.values())
total_2p = sum(ep2p_orders.values())

print(f"\n  pos đi trước trong đợt 1: {pos_first_1}/{total_1}")
print(f"  pos đi trước trong đợt 2+: {pos_first_2p}/{total_2p}")
print(f"  (chỉ đếm · không diễn giải · per A8-3)")

print(f"\n═══ A8-6 · KHÔNG rule, KHÔNG chọn ═══")
