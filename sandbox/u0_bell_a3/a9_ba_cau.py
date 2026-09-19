"""A9 · BA CÂU từ bảng A8 · READ, không rule.

A9-1: Gộp đợt trùng (MARSCOIN, CYS · gap D0 < 14d)
A9-2: 12/17 đợt không div-cross · tách (i) từng hedge rồi thoát · (ii) chưa hedge
A9-3: Test acc-drop + pos-rise trên 50 mẫu random universe · % chạm cả hai
A9-4: KHÔNG rule
"""
import sys, csv, importlib, math, random
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
for m in ["05","06","07","08","09"]:
    p = Path(rf"d:\Data back test\whale_data\data\export\freshwatch_daily_2026-{m}.csv")
    if not p.exists(): continue
    with p.open(encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            sym = r["symbol"]
            bare = sym[:-4] if sym.endswith("USDT") else sym
            d_iso = r["date"]
            d_row = datetime.strptime(d_iso, "%Y-%m-%d").date()
            if d_row < HOLDOUT_START:
                by_sym.setdefault(bare, []).append(r)

def _flt(v):
    if v is None or v == "": return None
    try:
        f = float(v)
        return None if math.isnan(f) else f
    except: return None


# ═════════════════════════════
# A9-1 · Gộp đợt trùng
# ═════════════════════════════
print("═══ A9-1 · Kiểm gap D0 và gộp đợt trùng ═══\n")

CASES = [
    ("BULLA",   "sóng 1",      "2026-07-20"),
    ("BULLA",   "sóng 2",      "2026-09-05"),
    ("HEMI",    "wave-1 20/07","2026-07-20"),
    ("HEMI",    "D0 15/08",    "2026-08-15"),
    ("UAI",     "pump#1",      "2026-07-07"),
    ("UAI",     "push 24/08",  "2026-08-24"),
    ("龙虾",    "D0 25/08",    "2026-08-25"),
    ("龙虾",    "leg 2 29/08", "2026-08-29"),
    ("MITO",    "đạp 28/08",   "2026-08-28"),
    ("MITO",    "long 10-11/09","2026-09-10"),
    ("MARSCOIN","D0 03/09",    "2026-09-03"),
    ("MARSCOIN","rebuild 07-10/09","2026-09-08"),
    ("CYS",     "D0 04/08",    "2026-08-04"),
    ("CYS",     "13-15/08",    "2026-08-14"),
    ("PROM",    "sóng 1",      "2026-07-19"),
    ("PROM",    "sóng 2",      "2026-08-05"),
    ("PROM",    "sóng 3",      "2026-08-25"),
]

from collections import defaultdict
by_tok = defaultdict(list)
for tok, ep, D0 in CASES:
    by_tok[tok].append((ep, D0))

print(f"{'token':<12} {'ep 1':<28} {'ep 2':<28} {'gap (ngày)':>12} {'gộp?':<8}")
print("─" * 90)

grouped_cases = []   # list of (tok, ep_label, D0) sau gộp
seen_first_per_tok = {}

for tok, eps in by_tok.items():
    if len(eps) == 1:
        grouped_cases.append((tok, eps[0][0], eps[0][1]))
        continue
    prev_d = None; prev_ep = None
    keep = []
    for ep, D0 in eps:
        d = datetime.strptime(D0, "%Y-%m-%d").date()
        if prev_d is None:
            keep.append((ep, D0))
        else:
            gap = (d - prev_d).days
            merged = gap < 14
            print(f"  {tok:<12} {prev_ep:<28} {ep:<28} {gap:>10}d  {'GỘP' if merged else 'giữ':<8}")
            if not merged:
                keep.append((ep, D0))
            else:
                # Gộp: giữ ep đầu, bỏ ep 2
                pass
        prev_d = d; prev_ep = ep
    for ep, D0 in keep:
        grouped_cases.append((tok, ep, D0))

# In cả các cặp không gộp (nếu chưa in)
for tok, eps in by_tok.items():
    if len(eps) < 2: continue
    for i in range(len(eps)-1):
        d1 = datetime.strptime(eps[i][1], "%Y-%m-%d").date()
        d2 = datetime.strptime(eps[i+1][1], "%Y-%m-%d").date()
        gap = (d2 - d1).days
        if gap >= 14:
            # Đã in? Skip
            pass

print(f"\nTổng đợt sau gộp: {len(grouped_cases)} (từ {len(CASES)})")
merged_cases_names = [(tok, ep) for tok, ep, _ in grouped_cases]
dropped = [(tok, ep) for tok, ep, _ in CASES if (tok, ep) not in merged_cases_names]
print(f"Bỏ (do gộp): {dropped}")


# ═════════════════════════════
# A9-1 tiếp · đếm lại A8-3 sau gộp
# ═════════════════════════════
print(f"\n─── Đếm lại A8-3 (thứ tự đợt 1 vs đợt 2+) sau gộp ───\n")

# Chạy lại logic A8-2 để lấy thứ tự per đợt còn lại
CASES_MERGED = grouped_cases

# Windows hint hard-code như A8
window_hints = {
    ("BULLA","sóng 1"): ("2026-06-25","2026-07-30"),
    ("BULLA","sóng 2"): ("2026-08-20","2026-09-15"),
    ("HEMI","wave-1 20/07"): ("2026-06-25","2026-07-30"),
    ("HEMI","D0 15/08"): ("2026-07-25","2026-08-25"),
    ("UAI","pump#1"): ("2026-06-15","2026-07-17"),
    ("UAI","push 24/08"): ("2026-08-05","2026-09-03"),
    ("龙虾","D0 25/08"): ("2026-08-05","2026-09-04"),
    ("龙虾","leg 2 29/08"): ("2026-08-19","2026-09-08"),
    ("MITO","đạp 28/08"): ("2026-08-15","2026-09-07"),
    ("MITO","long 10-11/09"): ("2026-08-31","2026-09-19"),
    ("MARSCOIN","D0 03/09"): ("2026-08-15","2026-09-13"),
    ("MARSCOIN","rebuild 07-10/09"): ("2026-08-25","2026-09-18"),
    ("CYS","D0 04/08"): ("2026-07-15","2026-08-14"),
    ("CYS","13-15/08"): ("2026-07-25","2026-08-24"),
    ("PROM","sóng 1"): ("2026-06-25","2026-07-29"),
    ("PROM","sóng 2"): ("2026-07-15","2026-08-15"),
    ("PROM","sóng 3"): ("2026-08-05","2026-09-04"),
}

def find_first_acc_drop(rows, s, e):
    d = s
    while d <= e:
        dacc, _, _ = delta_bwd(rows, d.isoformat(), "lsr_acc_r")
        if dacc is not None and dacc <= -0.20:
            return d.isoformat()
        d += timedelta(days=1)
    return None

def find_first_div_cross(rows, s, e):
    d = s
    while d <= e:
        dt = d.isoformat(); dt_p = (d - timedelta(days=1)).isoformat()
        v = _div_avg3(rows, dt); vp = _div_avg3(rows, dt_p)
        if v is not None and vp is not None and vp <= 0.5 and v > 0.5:
            return dt
        d += timedelta(days=1)
    return None

def find_first_pos_rise(rows, s, e):
    d = s
    while d <= e:
        dpos, _, _ = delta_bwd(rows, d.isoformat(), "lsr_pos_r")
        if dpos is not None and dpos >= 0.10:
            return d.isoformat()
        d += timedelta(days=1)
    return None

def get_order(rows, w_start, w_end):
    marks = [
        ("acc", find_first_acc_drop(rows, w_start, w_end)),
        ("div", find_first_div_cross(rows, w_start, w_end)),
        ("pos", find_first_pos_rise(rows, w_start, w_end)),
    ]
    valid = [(n, d) for n, d in marks if d]
    valid.sort(key=lambda x: x[1])
    return " → ".join(n for n, _ in valid) if valid else "─"

from collections import Counter
ep1_orders = Counter(); ep2p_orders = Counter()
seen = set()
merged_results = []
for tok, ep, D0 in CASES_MERGED:
    rows = by_sym.get(tok, [])
    if not rows: continue
    wh_s, wh_e = window_hints.get((tok, ep), (None, None))
    if not wh_s: continue
    ws = datetime.strptime(wh_s, "%Y-%m-%d").date()
    we = min(datetime.strptime(wh_e, "%Y-%m-%d").date(), HOLDOUT_START - timedelta(days=1))
    order = get_order(rows, ws, we)
    is_first = tok not in seen
    seen.add(tok)
    if is_first:
        ep1_orders[order] += 1
    else:
        ep2p_orders[order] += 1
    merged_results.append((tok, ep, order, is_first))

print(f"Đợt 1 (n={sum(ep1_orders.values())}) · tần suất:")
for o, n in ep1_orders.most_common():
    print(f"  {o:<20} {n}")

print(f"\nĐợt 2+ (n={sum(ep2p_orders.values())}) · tần suất:")
for o, n in ep2p_orders.most_common():
    print(f"  {o:<20} {n}")

pos_first_1 = sum(n for o, n in ep1_orders.items() if o.startswith("pos"))
pos_first_2p = sum(n for o, n in ep2p_orders.items() if o.startswith("pos"))
t1 = sum(ep1_orders.values()); t2 = sum(ep2p_orders.values())
print(f"\n  pos đi trước · đợt 1: {pos_first_1}/{t1} = {pos_first_1/max(1,t1)*100:.0f}%")
print(f"  pos đi trước · đợt 2+: {pos_first_2p}/{t2} = {pos_first_2p/max(1,t2)*100:.0f}%")


# ═════════════════════════════
# A9-2 · 12/17 đợt không div-cross · từng hedge?
# ═════════════════════════════
print(f"\n═══ A9-2 · Đợt không có div-cross · từng hedge hay chưa? ═══\n")
print(f"{'ca':<28} {'div_min_window':>15} {'div_min_60d_pre_D0':>20} {'phân loại':<30}")
print("─" * 100)

nhom_i = []; nhom_ii = []
for tok, ep, D0 in CASES:
    rows = by_sym.get(tok, [])
    if not rows: continue
    wh_s, wh_e = window_hints.get((tok, ep), (None, None))
    if not wh_s: continue
    ws = datetime.strptime(wh_s, "%Y-%m-%d").date()
    we = min(datetime.strptime(wh_e, "%Y-%m-%d").date(), HOLDOUT_START - timedelta(days=1))

    # Check if any div-cross in window
    dc = find_first_div_cross(rows, ws, we)
    if dc: continue  # có div-cross, skip

    # div_min in window
    div_vals_w = []
    d = ws
    while d <= we:
        v = _div_avg3(rows, d.isoformat())
        if v is not None: div_vals_w.append(v)
        d += timedelta(days=1)
    div_min_w = min(div_vals_w) if div_vals_w else None

    # div_min in 60d before D0
    D0d = datetime.strptime(D0, "%Y-%m-%d").date()
    div_vals_pre = []
    for k in range(1, 61):
        dk = (D0d - timedelta(days=k)).isoformat()
        if dk >= "2026-09-20": continue
        v = _div_avg3(rows, dk)
        if v is not None: div_vals_pre.append(v)
    div_min_pre = min(div_vals_pre) if div_vals_pre else None

    # Phân loại
    if div_min_pre is not None and div_min_pre <= 0.5:
        classification = "(i) từng hedge rồi thoát"
        nhom_i.append((tok, ep))
    elif div_min_pre is not None:
        classification = "(ii) chưa hedge bao giờ"
        nhom_ii.append((tok, ep))
    else:
        classification = "N/A (không đủ data)"

    dm_w_s = f"{div_min_w:.3f}" if div_min_w is not None else "N/A"
    dm_p_s = f"{div_min_pre:.3f}" if div_min_pre is not None else "N/A"
    print(f"  {tok+' · '+ep:<28} {dm_w_s:>15} {dm_p_s:>20} {classification:<30}")

print(f"\n  Nhóm (i) từng hedge rồi thoát TRƯỚC cửa sổ: {len(nhom_i)} → U0-BELL có thể áp scope trước-cross")
print(f"  Nhóm (ii) chưa hedge bao giờ:              {len(nhom_ii)} → U0-BELL KHÔNG áp được")


# ═════════════════════════════
# A9-3 · Random 50 tokens · % chạm acc-drop + pos-rise
# ═════════════════════════════
print(f"\n═══ A9-3 · 50 mẫu random universe · % chạm cả acc-drop và pos-rise trong window 35d ═══\n")

# Load universe 228
fw_p = Path(r"d:\Data back test\whale_data\data\config\freshwatch_symbols.txt")
universe = [l.strip().replace("USDT","") for l in fw_p.read_text(encoding="utf-8").splitlines() if l.strip()]

random.seed(42)  # reproducible
sample_tokens = random.sample(universe, min(50, len(universe)))

# Cửa sổ 35d cố định · chọn end random trong [2026-07-15, 2026-09-15]
def check_both(rows, w_start, w_end):
    """True nếu trong window có cả acc-drop và pos-rise."""
    acc = find_first_acc_drop(rows, w_start, w_end)
    pos = find_first_pos_rise(rows, w_start, w_end)
    return bool(acc) and bool(pos)

both_count = 0; both_tokens = []
acc_only = 0; pos_only = 0; neither = 0
window_end_range = (datetime(2026,7,15).date(), datetime(2026,9,15).date())
range_days = (window_end_range[1] - window_end_range[0]).days

for tok in sample_tokens:
    rows = by_sym.get(tok, [])
    if not rows:
        continue
    # random window end trong range
    offset = random.randint(0, range_days)
    w_end = window_end_range[0] + timedelta(days=offset)
    w_start = w_end - timedelta(days=35)
    acc = find_first_acc_drop(rows, w_start, w_end)
    pos = find_first_pos_rise(rows, w_start, w_end)
    if acc and pos:
        both_count += 1
        both_tokens.append(tok)
    elif acc: acc_only += 1
    elif pos: pos_only += 1
    else: neither += 1

n = both_count + acc_only + pos_only + neither
print(f"  n mẫu (có data): {n}/{len(sample_tokens)}")
print(f"  Chạm CẢ acc-drop ∧ pos-rise: {both_count}/{n} = {both_count/max(1,n)*100:.0f}%")
print(f"  Chạm chỉ acc-drop:            {acc_only}/{n}")
print(f"  Chạm chỉ pos-rise:            {pos_only}/{n}")
print(f"  Không chạm cả hai:            {neither}/{n}")

print(f"\n  Nếu tỷ lệ ~100% → hai mốc không phân biệt → chuyện thường ngày.")
print(f"  Tỷ lệ đo được: {both_count/max(1,n)*100:.0f}% · so với 17/17 = 100% trong tập A8 proven")

print(f"\n═══ A9-4 · KHÔNG rule, KHÔNG wire ═══")
