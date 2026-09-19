"""A6 · BẢNG CALIBRATION E2 EXTENDED · cửa sổ mở qua D0+45 · TRƯỚC 20/09.

Sửa lỗi A5: cửa sổ dừng tại D0 → post_D0=0 SAI. Mở tới D0+45 (hoặc <20/09).

Cột:
  token · loài · D0 · cửa_sổ_quét
  TIỀN-D0: first_bell · lead_known · n_bells
  HẬU-XẢ:  n_bells · ngày cụ thể · outcome_30d (ret_max từ mỗi ring · using px_avg)
  hoặc "không chuông"

A6-3 · 5 ca đích danh: MITO 10-11/09 · MARSCOIN 07-10/09 · UAI nền 05-22/08
       · BULLA sóng 2 (~09-05) · HEMI 16/08 (D0+1)

A6-4 · Chuông hậu-xả nhãn `[U0-BELL · hậu-xả]` · KHÔNG vào 🎯.

A6-5 · HOLD-OUT guard: max_date_used < 2026-09-20.
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
from u0_bell import u0_bell

HOLDOUT_START = datetime(2026, 9, 20).date()

by_sym = {}
max_date_used = "0000-00-00"
for m in ["05","06","07","08","09"]:
    p = Path(rf"d:\Data back test\whale_data\data\export\freshwatch_daily_2026-{m}.csv")
    if not p.exists(): continue
    with p.open(encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            sym = r["symbol"]
            bare = sym.replace("USDT","") if sym.endswith("USDT") else sym
            d_iso = r["date"]
            d_row = datetime.strptime(d_iso, "%Y-%m-%d").date()
            if d_row >= HOLDOUT_START:
                continue
            by_sym.setdefault(bare, []).append(r)
            if d_iso > max_date_used:
                max_date_used = d_iso

print(f"═══ A6-5 · HOLD-OUT guard: max_date_used = {max_date_used} < 2026-09-20 · {'PASS' if max_date_used < '2026-09-20' else 'FAIL'} ═══\n")

def _flt(v):
    if v is None or v == "": return None
    try:
        f = float(v)
        return None if math.isnan(f) else f
    except: return None

def _get(rows, dt, field):
    for r in rows:
        if r["date"] == dt:
            return _flt(r.get(field))
    return None

# D0 by sổ (per A5-1 hand-curated)
PROVEN_HEDGE_B = [
    ("BTR",   "B", "2026-08-26"),
    ("BULLA", "B", "2026-07-20"),   # wave-1
    ("UAI",   "B", "2026-08-24"),   # push
    ("AKE",   "B", "2026-07-15"),
    ("HEMI",  "B", "2026-08-15"),
    ("ON",    "B", "2026-07-19"),
]
PROVEN_NON_HEDGE = [
    ("BANK",    "A", "2026-07-11"),
    ("CYS",     "A", "2026-08-04"),
    ("PROM",    "A", "2026-07-19"),
    ("TUT",     "A", "2026-07-09"),
    ("BTW",     "D", "2026-08-03"),
    ("CAP",     "D", "2026-07-30"),
    ("LOBSTER", "D", "2026-08-25"),
]

# Negatives · dùng G2 rule (dd ≤ -40% từ ATH) cho ca sống cần D0
def find_d0_by_g2(rows, dd_threshold=-0.40):
    """D0 = ngày drawdown 30d ≤ -40% ĐẦU tiên qua ngưỡng.
    Simple: ngày đầu có (px_avg / max20d_before) − 1 ≤ dd_threshold."""
    sorted_rows = sorted(rows, key=lambda r: r["date"])
    for r in sorted_rows:
        d = r["date"]
        px = _flt(r.get("px_avg"))
        if px is None: continue
        d_date = datetime.strptime(d, "%Y-%m-%d").date()
        # ATH 20d trước
        max_before = None
        for k in range(1, 21):
            dt_k = (d_date - timedelta(days=k)).isoformat()
            px_k = _get(rows, dt_k, "px_avg")
            if px_k is not None:
                max_before = px_k if max_before is None else max(max_before, px_k)
        if max_before and max_before > 0:
            dd = px / max_before - 1
            if dd <= dd_threshold:
                return d
    return None

NEGATIVES_SPEC = [
    ("LIGHT",        "chronic-âm",     None),   # dùng G2
    ("BROCCOLIF3B",  "chronic-âm×2",   None),
    ("SOPH",         "chronic + D0 07-09", "2026-09-07"),
    ("POWER",        "âm",             None),
    ("HYPER",        "âm",             None),
    ("BASED",        "âm",             None),
    ("MITO",         "âm · đích danh 10-11/09", None),
    ("MARSCOIN",     "âm · đích danh 07-10/09", None),
]

def scan_bells_in_window(rows, w_start, w_end, threshold):
    days = []
    d = w_start
    while d <= w_end:
        res = u0_bell(rows, d.isoformat(), _div_avg3, dacc_bell_max=threshold)
        if res["status"] == "BELL":
            days.append((d.isoformat(), res))
        d += timedelta(days=1)
    return days

def ret_max_after(rows, d_from, n_days=30):
    """Trả max % ret trong [d_from+1, d_from+n_days] so với px_avg(d_from)."""
    px0 = _get(rows, d_from, "px_avg")
    if px0 is None or px0 <= 0: return None
    d0 = datetime.strptime(d_from, "%Y-%m-%d").date()
    max_pct = None
    for k in range(1, n_days+1):
        dk = (d0 + timedelta(days=k)).isoformat()
        pxk = _get(rows, dk, "px_avg")
        if pxk is None: continue
        pct = (pxk - px0) / px0
        if max_pct is None or pct > max_pct:
            max_pct = pct
    return max_pct


def calibration_row_a6(tok, loai, D0_str, threshold):
    rows = by_sym.get(tok, [])
    if not rows:
        return {"token": tok, "loai": loai, "status": "NO-DATA"}

    if not D0_str:
        # Try G2 rule
        D0_str = find_d0_by_g2(rows)

    if D0_str:
        d0 = datetime.strptime(D0_str, "%Y-%m-%d").date()
        w_start = d0 - timedelta(days=60)
        w_end_absolute = min(d0 + timedelta(days=45), HOLDOUT_START - timedelta(days=1))
        w_end = w_end_absolute
        d0_used = d0
        d0_src = "sổ" if tok in [t for t,_,_ in PROVEN_HEDGE_B + PROVEN_NON_HEDGE] else "G2-dd40%"
    else:
        w_end = HOLDOUT_START - timedelta(days=1)
        w_start = w_end - timedelta(days=90)
        d0 = None
        d0_used = None
        d0_src = "no-D0"

    bells = scan_bells_in_window(rows, w_start, w_end, threshold)

    pre_d0 = []; post_xa = []
    if d0:
        for dstr, res in bells:
            bd = datetime.strptime(dstr, "%Y-%m-%d").date()
            if bd < d0:
                pre_d0.append((dstr, res))
            elif bd >= d0 + timedelta(days=3):  # A6-1 spec: [D0+3, D0+45]
                post_xa.append((dstr, res))
            # bells trong [D0, D0+2] ignore (transition)
    else:
        # No D0 · all counted as unresolved
        pre_d0 = list(bells)

    return {
        "token": tok, "loai": loai,
        "D0": D0_str, "D0_src": d0_src,
        "window_start": w_start.isoformat() if w_start else None,
        "window_end": w_end.isoformat() if w_end else None,
        "pre_d0_bells": pre_d0,
        "post_xa_bells": post_xa,
        "n_bells_total": len(bells),
    }


ALL_TOKENS = PROVEN_HEDGE_B + PROVEN_NON_HEDGE + NEGATIVES_SPEC

for T_label, T in [("T=-20%", -0.20), ("T=-15%", -0.15)]:
    print(f"═══ A6-1 · BẢNG E2 EXTENDED · {T_label} · cửa sổ D0-60 → D0+45 (max <20/09) ═══\n")
    print(f"{'token':<14} {'loài':<3} {'D0':<12} {'src':<10} {'window':<25} {'pre first_bell':<14} {'lead':>5} {'n_pre':>5} {'n_post_xa':>10}")
    print("─" * 115)

    all_results = []
    for tok, loai, D0 in ALL_TOKENS:
        row = calibration_row_a6(tok, loai, D0, T)
        all_results.append(row)

        if row.get("status") == "NO-DATA":
            print(f"  {tok:<12} {loai:<3} [NO-DATA in fw store]"); continue

        pre = row["pre_d0_bells"]
        post = row["post_xa_bells"]
        first_bell_pre = pre[0][0] if pre else "─"
        lead_pre = (datetime.strptime(row["D0"], "%Y-%m-%d").date() - datetime.strptime(pre[0][0], "%Y-%m-%d").date()).days if (pre and row["D0"]) else None
        lead_s = f"{lead_pre:+d}" if lead_pre is not None else "─"

        d0_s = row.get("D0") or "─"
        window_s = f"{row['window_start']}→{row['window_end']}"
        print(f"  {tok:<12} {loai:<3} {d0_s:<12} {row['D0_src']:<10} {window_s:<25} {first_bell_pre:<14} {lead_s:>5} {len(pre):>5} {len(post):>10}")

    print(f"\n─── A6-4 · Chi tiết HẬU-XẢ per token · nhãn [U0-BELL · hậu-xả] · KHÔNG vào 🎯 ───")
    for r in all_results:
        if r.get("post_xa_bells"):
            print(f"\n  {r['token']} ({r['loai']}) · D0={r['D0']} · {len(r['post_xa_bells'])} ring hậu-xả:")
            rows_tok = by_sym.get(r['token'], [])
            for dstr, res in r["post_xa_bells"]:
                bd = datetime.strptime(dstr, "%Y-%m-%d").date()
                d0d = datetime.strptime(r['D0'], "%Y-%m-%d").date()
                lag = (bd - d0d).days
                ret_max = ret_max_after(rows_tok, dstr, 30)
                ret_s = f"{ret_max*100:+.1f}%" if ret_max is not None else "N/A"
                print(f"    · {dstr} · lag D0+{lag}d · Δacc={res['dacc_bwd']*100:+.1f}% · ret_max_30d={ret_s} · [U0-BELL · hậu-xả]")

    # A6-3 · Đối chứng 5 ca đích danh
    print(f"\n─── A6-3 · 5 ca đích danh · lệch mấy ngày? ───")
    NAMED = [
        ("MITO",     "2026-09-10", "2026-09-11", "10-11/09"),
        ("MARSCOIN", "2026-09-07", "2026-09-10", "07-10/09"),
        ("UAI",      "2026-08-05", "2026-08-22", "05-22/08"),
        ("BULLA",    "2026-09-05", "2026-09-05", "sóng 2 ~09-05"),
        ("HEMI",     "2026-08-16", "2026-08-16", "16/08 D0+1"),
    ]
    for tok, d_from, d_to, label in NAMED:
        rows_tok = by_sym.get(tok, [])
        if not rows_tok:
            print(f"  {tok:<10} {label} · [NO-DATA]"); continue
        d_f = datetime.strptime(d_from, "%Y-%m-%d").date()
        d_t = datetime.strptime(d_to, "%Y-%m-%d").date()
        # Extend search ±5d
        search_start = d_f - timedelta(days=5)
        search_end = min(d_t + timedelta(days=5), HOLDOUT_START - timedelta(days=1))
        bells_near = scan_bells_in_window(rows_tok, search_start, search_end, T)
        if bells_near:
            # nearest bell to target window
            bells_in = [b for b in bells_near if d_f <= datetime.strptime(b[0], "%Y-%m-%d").date() <= d_t]
            if bells_in:
                b_dates = [b[0] for b in bells_in]
                print(f"  {tok:<10} {label:<20} · KHỚP · bells trong window: {b_dates}")
            else:
                # Nearest bell (offset)
                d_target = d_f  # first day of target
                best = min(bells_near, key=lambda b: abs((datetime.strptime(b[0],'%Y-%m-%d').date() - d_target).days))
                offset = (datetime.strptime(best[0],'%Y-%m-%d').date() - d_target).days
                print(f"  {tok:<10} {label:<20} · gần nhất · {best[0]} · lệch {offset:+d}d")
        else:
            print(f"  {tok:<10} {label:<20} · KHÔNG chuông trong ±5d")
    print()
