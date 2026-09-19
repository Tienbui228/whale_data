"""A7 · Trình tự đợt hai · READ, không wire.

A7-1: Với token có ≥2 cross trong window, tách đợt 1 và đợt 2+ (gap ≥14 = đợt mới).
      Mỗi đợt: ngày cross · ngày acc lần đầu Δacc_bwd ≤ -20% · lệch.
A7-2: BULLA chuỗi 08-25 → 09-10 mỗi ngày.
A7-3: MITO 10-11/09 · MARSCOIN 07-10/09 · HEMI 16/08 — bảng 3 cột.
A7-4: KHÔNG rule mới.
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
from u0_bell import u0_bell, delta_bwd

by_sym = {}
for m in ["05","06","07","08","09"]:
    p = Path(rf"d:\Data back test\whale_data\data\export\freshwatch_daily_2026-{m}.csv")
    if not p.exists(): continue
    with p.open(encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            sym = r["symbol"]
            bare = sym.replace("USDT","") if sym.endswith("USDT") else sym
            d_iso = r["date"]
            d_row = datetime.strptime(d_iso, "%Y-%m-%d").date()
            if d_row < datetime(2026,9,20).date():
                by_sym.setdefault(bare, []).append(r)

def _flt(v):
    try: return float(v) if v not in (None,"") else None
    except: return None

def find_all_crosses(rows, d_start, d_end):
    crosses = []
    d = d_start
    while d <= d_end:
        dt = d.isoformat()
        dt_prev = (d - timedelta(days=1)).isoformat()
        v = _div_avg3(rows, dt); vp = _div_avg3(rows, dt_prev)
        if v is not None and vp is not None and vp <= 0.5 and v > 0.5:
            crosses.append(dt)
        d += timedelta(days=1)
    return crosses

def group_episodes(crosses, gap=14):
    """WL-EPISODE: gap ≥14d = đợt mới."""
    if not crosses: return []
    episodes = [[crosses[0]]]
    for c in crosses[1:]:
        prev = datetime.strptime(episodes[-1][-1], "%Y-%m-%d").date()
        cur = datetime.strptime(c, "%Y-%m-%d").date()
        if (cur - prev).days >= gap:
            episodes.append([c])
        else:
            episodes[-1].append(c)
    return episodes

def acc_first_bwd_le_target(rows, d_start, d_end, target=-0.20):
    """Trả ngày đầu tiên trong [d_start, d_end] có Δacc_bwd(D) ≤ target."""
    d = d_start
    while d <= d_end:
        dacc, _, _ = delta_bwd(rows, d.isoformat(), "lsr_acc_r")
        if dacc is not None and dacc <= target:
            return d.isoformat(), dacc
        d += timedelta(days=1)
    return None, None


# A7-1 · Tách đợt cho MỌI token có ≥2 cross
print("═══ A7-1 · Tách đợt 1 / đợt 2+ (gap ≥14d) · so acc-trigger vs cross ═══\n")

TOKENS_SCAN = [
    "BTR","BULLA","UAI","AKE","HEMI","ON",           # HEDGE proven
    "BANK","CYS","PROM","TUT","BTW","CAP",           # non-hedge
    "LIGHT","BROCCOLIF3B","SOPH","POWER","BASED","MITO","MARSCOIN","APR","HYPER"
]
W_START = datetime(2026, 5, 1).date()
W_END = datetime(2026, 9, 19).date()

multi_ep_tokens = []
for tok in TOKENS_SCAN:
    rows = by_sym.get(tok, [])
    if not rows: continue
    crosses = find_all_crosses(rows, W_START, W_END)
    if len(crosses) < 2: continue
    episodes = group_episodes(crosses, gap=14)
    if len(episodes) < 2: continue
    multi_ep_tokens.append((tok, episodes))

if not multi_ep_tokens:
    print("  Không có token nào có ≥2 đợt cross trong window.")
else:
    print(f"{'token':<15} {'đợt':<4} {'cross đầu':<12} {'acc first Δ≤-20%':<20} {'lệch (ngày)':>12} {'acc Δ%':>8}")
    print("─" * 80)
    for tok, eps in multi_ep_tokens:
        rows = by_sym[tok]
        for i, ep in enumerate(eps, 1):
            cross_first = ep[0]
            cross_d = datetime.strptime(cross_first, "%Y-%m-%d").date()
            # Search acc-first-trigger trong [cross-14, cross+7]
            s = max(W_START, cross_d - timedelta(days=14))
            e = min(W_END, cross_d + timedelta(days=7))
            acc_date, dacc = acc_first_bwd_le_target(rows, s, e)
            if acc_date:
                lag = (cross_d - datetime.strptime(acc_date, "%Y-%m-%d").date()).days
                lag_s = f"{lag:+d}"  # dương = acc TRƯỚC cross
                dacc_s = f"{dacc*100:+.1f}%"
            else:
                lag_s = "─ (no)"
                acc_date = "─"
                dacc_s = "─"
            print(f"  {tok:<13} #{i:<3} {cross_first:<12} {acc_date:<20} {lag_s:>12} {dacc_s:>8}")

# So sánh đợt 1 vs 2+
print(f"\n─── So đợt 1 vs đợt 2+ · dấu lệch (dương = acc TRƯỚC cross) ───")
ep1_leads = []
ep2p_leads = []
for tok, eps in multi_ep_tokens:
    rows = by_sym[tok]
    for i, ep in enumerate(eps, 1):
        cross_d = datetime.strptime(ep[0], "%Y-%m-%d").date()
        s = max(W_START, cross_d - timedelta(days=14))
        e = min(W_END, cross_d + timedelta(days=7))
        acc_date, dacc = acc_first_bwd_le_target(rows, s, e)
        if acc_date:
            lag = (cross_d - datetime.strptime(acc_date, "%Y-%m-%d").date()).days
            if i == 1: ep1_leads.append((tok, lag))
            else: ep2p_leads.append((tok, lag))

if ep1_leads:
    from statistics import median
    print(f"  Đợt 1 · n={len(ep1_leads)} · median lag={median([x[1] for x in ep1_leads]):.1f}d")
    for tok, lag in ep1_leads:
        print(f"    {tok}: {lag:+d}d")
if ep2p_leads:
    from statistics import median
    print(f"\n  Đợt 2+ · n={len(ep2p_leads)} · median lag={median([x[1] for x in ep2p_leads]):.1f}d")
    for tok, lag in ep2p_leads:
        print(f"    {tok}: {lag:+d}d")


# A7-2 · BULLA chuỗi 08-25 → 09-10
print(f"\n\n═══ A7-2 · BULLA · chuỗi số thô 2026-08-25 → 2026-09-10 ═══\n")
rows = by_sym["BULLA"]
print(f"  {'date':<12} {'div_avg3':>8} {'acc_r':>8} {'pos_r':>8} {'Δacc_bwd':>10} {'Δpos_bwd':>10} {'note':<20}")
print("─" * 82)
d = datetime(2026, 8, 25).date()
while d <= datetime(2026, 9, 10).date():
    dt = d.isoformat()
    div = _div_avg3(rows, dt)
    acc = next((_flt(r.get("lsr_acc_r")) for r in rows if r["date"] == dt), None)
    pos = next((_flt(r.get("lsr_pos_r")) for r in rows if r["date"] == dt), None)
    dacc, _, _ = delta_bwd(rows, dt, "lsr_acc_r")
    dpos, _, _ = delta_bwd(rows, dt, "lsr_pos_r")
    div_s = f"{div:.3f}" if div is not None else "N/A"
    acc_s = f"{acc:.3f}" if acc is not None else "N/A"
    pos_s = f"{pos:.3f}" if pos is not None else "N/A"
    dacc_s = f"{dacc*100:+.1f}%" if dacc is not None else "N/A"
    dpos_s = f"{dpos*100:+.1f}%" if dpos is not None else "N/A"
    note = ""
    if div is not None and div > 0.5 and _div_avg3(rows, (d - timedelta(days=1)).isoformat()) is not None:
        prev = _div_avg3(rows, (d - timedelta(days=1)).isoformat())
        if prev is not None and prev <= 0.5:
            note = "★ CROSS UP"
    if dacc is not None and dacc <= -0.20:
        note += " · acc≤-20%"
    print(f"  {dt:<12} {div_s:>8} {acc_s:>8} {pos_s:>8} {dacc_s:>10} {dpos_s:>10} {note:<20}")
    d += timedelta(days=1)


# A7-3 · MITO/MARSCOIN/HEMI · bảng 3 cột
print(f"\n\n═══ A7-3 · Trình tự acc-sập vs div-vượt-0.5 · 3 ca ═══\n")

CASES_A73 = [
    ("MITO", "2026-09-05", "2026-09-13"),
    ("MARSCOIN", "2026-09-04", "2026-09-12"),
    ("HEMI", "2026-08-10", "2026-08-19"),
]

for tok, ds, de in CASES_A73:
    rows = by_sym.get(tok, [])
    if not rows:
        print(f"── {tok} [NO-DATA] ──\n"); continue
    print(f"── {tok} · window {ds} → {de} ──")
    print(f"  {'date':<12} {'div_avg3':>8} {'div>0.5?':<9} {'Δacc_bwd':>10} {'Δacc≤-20?':<11}")
    print("─" * 55)
    dstart = datetime.strptime(ds, "%Y-%m-%d").date()
    dend = datetime.strptime(de, "%Y-%m-%d").date()
    div_cross_date = None
    acc_drop_date = None
    d = dstart
    while d <= dend:
        dt = d.isoformat()
        div = _div_avg3(rows, dt)
        dacc, _, _ = delta_bwd(rows, dt, "lsr_acc_r")
        div_gt = div is not None and div > 0.5
        acc_le = dacc is not None and dacc <= -0.20
        div_s = f"{div:.3f}" if div is not None else "N/A"
        dacc_s = f"{dacc*100:+.1f}%" if dacc is not None else "N/A"
        print(f"  {dt:<12} {div_s:>8} {'✓' if div_gt else '·':<9} {dacc_s:>10} {'✓' if acc_le else '·':<11}")
        if div_cross_date is None and div_gt:
            # first crossing check: prev day was ≤ 0.5
            prev = _div_avg3(rows, (d - timedelta(days=1)).isoformat())
            if prev is not None and prev <= 0.5:
                div_cross_date = dt
        if acc_drop_date is None and acc_le:
            acc_drop_date = dt
        d += timedelta(days=1)

    print(f"\n  → div vượt 0.5 đầu tiên: {div_cross_date or '─ (không cross)'}")
    print(f"  → Δacc_bwd ≤ -20% đầu tiên: {acc_drop_date or '─'}")
    if div_cross_date and acc_drop_date:
        lag = (datetime.strptime(div_cross_date, "%Y-%m-%d").date() -
               datetime.strptime(acc_drop_date, "%Y-%m-%d").date()).days
        if lag > 0: order = f"acc TRƯỚC div {lag}d"
        elif lag < 0: order = f"acc SAU div {abs(lag)}d"
        else: order = "acc và div CÙNG NGÀY"
        print(f"  → THỨ TỰ: {order}")
    print()

print(f"\nA7-4 · KHÔNG rule mới. Chỉ in trình tự · giữ nguyên spec A5-0.")
