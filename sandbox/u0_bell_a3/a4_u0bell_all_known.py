"""A4 · U0-BELL trên toàn tập đã biết · ĐỌC · w=3, ngưỡng -20%, cap pos 10%.

Tập:
  DƯƠNG · 13 proven (per PATTERN_BOOK B section + h2r_u0_measurement handover):
    BTR, BULLA, UAI, AKE, HEMI, ON, LOBSTER, PROM, CAP, BANK, TUT, CYS, BTW
  ÂM · 4 controls:
    APR, SOPH (đối chứng đã biết negative)
    LIGHT, BROCCOLIF3B (nền âm chronic)

Mỗi ca: có kêu · ngày kêu · Δacc_bwd · Δpos_bwd · khoảng cách D_cross gần nhất
        (D0 skip vì cần external per-token, không có in fw store)

A4-3: chạy lại BỎ cap |Δpos|. So dương/âm cột.
"""
import sys, csv, importlib, math
from pathlib import Path
from datetime import datetime, timedelta
try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except: pass  # L-66-OK
sys.path.insert(0, r"d:\Data back test\whale_data\scripts")
sys.path.insert(0, r"d:\Data back test\whale_data\sandbox\u0_bell_a3")
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
            by_sym.setdefault(bare, []).append(r)

def _flt(v):
    if v is None or v == "": return None
    try:
        f = float(v)
        return None if math.isnan(f) else f
    except: return None

POSITIVE = ["BTR","BULLA","UAI","AKE","HEMI","ON","LOBSTER","PROM","CAP","BANK","TUT","CYS","BTW"]
NEGATIVE = ["APR","SOPH","LIGHT","BROCCOLIF3B"]
WINDOW_START = datetime(2026, 6, 1).date()
WINDOW_END = datetime(2026, 9, 17).date()

def find_all_crosses(rows, start_date=WINDOW_START, end_date=WINDOW_END):
    """List of D_cross dates (div_avg3 vượt 0.5 up)."""
    crosses = []
    d = start_date
    while d <= end_date:
        dt = d.isoformat()
        dt_prev = (d - timedelta(days=1)).isoformat()
        v = _div_avg3(rows, dt)
        vp = _div_avg3(rows, dt_prev)
        if v is not None and vp is not None and vp <= 0.5 and v > 0.5:
            if not crosses or (d - datetime.strptime(crosses[-1], "%Y-%m-%d").date()).days > 7:
                crosses.append(dt)
        d += timedelta(days=1)
    return crosses


def u0_bell_no_pos_cap(rows, target_date):
    """Variant · bỏ cap |Δpos| · giữ div ≤0.5 ∧ Δacc_bwd ≤-20%."""
    div_D = _div_avg3(rows, target_date)
    dacc, acc_D, acc_m3 = delta_bwd(rows, target_date, "lsr_acc_r")
    dpos, pos_D, pos_m3 = delta_bwd(rows, target_date, "lsr_pos_r")
    if acc_D is None or acc_m3 is None:
        return {"status": "BLIND", "dacc": dacc, "dpos": dpos, "div_D": div_D}
    if div_D is None or div_D > 0.5:
        return {"status": "MISS", "dacc": dacc, "dpos": dpos, "div_D": div_D}
    if dacc > -0.20:
        return {"status": "MISS", "dacc": dacc, "dpos": dpos, "div_D": div_D}
    return {"status": "BELL", "dacc": dacc, "dpos": dpos, "div_D": div_D}


def scan_bells_strict(rows):
    """A3-1 strict: 3 conditions."""
    days = []
    d = WINDOW_START
    while d <= WINDOW_END:
        res = u0_bell(rows, d.isoformat(), _div_avg3)
        if res["status"] == "BELL":
            days.append((d.isoformat(), res))
        d += timedelta(days=1)
    return days


def scan_bells_no_pos(rows):
    """A4-3 variant: no |Δpos| cap."""
    days = []
    d = WINDOW_START
    while d <= WINDOW_END:
        res = u0_bell_no_pos_cap(rows, d.isoformat())
        if res["status"] == "BELL":
            days.append((d.isoformat(), res))
        d += timedelta(days=1)
    return days


def nearest_cross_distance(bell_date, crosses):
    """Trả (D_cross_nearest, distance_days). Positive = cross AFTER bell."""
    bd = datetime.strptime(bell_date, "%Y-%m-%d").date()
    best = None
    best_dist = None
    for cd in crosses:
        cd_d = datetime.strptime(cd, "%Y-%m-%d").date()
        dist = (cd_d - bd).days
        if best is None or abs(dist) < abs(best_dist):
            best = cd
            best_dist = dist
    return best, best_dist


print(f"═══ A4-1 · U0-BELL A3-1 STRICT trên 13 proven + 4 âm ═══\n")
print(f"Ngưỡng: div ≤ 0.5 ∧ Δacc_bwd ≤ -20% ∧ |Δpos_bwd| ≤ 10%\n")

total_pos_with_bell = 0
total_neg_with_bell = 0

for label, tokens in [("DƯƠNG (13 proven)", POSITIVE), ("ÂM (4 controls)", NEGATIVE)]:
    print(f"─── {label} ───")
    for tok in tokens:
        rows = by_sym.get(tok, [])
        if not rows:
            print(f"  {tok:<12} [NO-DATA in fw store]")
            continue
        crosses = find_all_crosses(rows)
        bells = scan_bells_strict(rows)
        has_bell = len(bells) > 0
        if has_bell:
            if label.startswith("DƯƠNG"): total_pos_with_bell += 1
            else: total_neg_with_bell += 1
        print(f"  {tok:<12} · n_bells={len(bells)} · n_crosses={len(crosses)} · has_bell={has_bell}")
        for dstr, res in bells:
            cr, dist = nearest_cross_distance(dstr, crosses)
            dist_s = f"{dist:+d}d" if dist is not None else "N/A"
            cr_s = cr if cr else "N/A"
            print(f"     · D_bell={dstr} · Δacc={res['dacc_bwd']*100:+.1f}% · Δpos={res['dpos_bwd']*100:+.1f}% · nearest_cross={cr_s} · dist={dist_s}")

print(f"\n═══ A4-2 · Đếm gọn ═══\n")
print(f"  DƯƠNG có chuông: {total_pos_with_bell}/{sum(1 for t in POSITIVE if by_sym.get(t))}")
print(f"  ÂM   có chuông: {total_neg_with_bell}/{sum(1 for t in NEGATIVE if by_sym.get(t))}")

if total_neg_with_bell > total_pos_with_bell:
    print(f"  ⚠ CHUÔNG KÊU TRÊN ÂM ({total_neg_with_bell}) > DƯƠNG ({total_pos_with_bell}) → BÁO THẲNG, ĐỪNG WIRE")
else:
    print(f"  · Dương ≥ Âm · phần ứng cử wire (chờ Tiên/ANALYSIS thảo)")


# A4-3 · BỎ cap |Δpos|
print(f"\n═══ A4-3 · BỎ cap |Δpos| (chỉ giữ div ≤0.5 ∧ Δacc_bwd ≤-20%) ═══\n")

table = []   # (label, tok, strict_bells, no_pos_bells)
for label, tokens in [("DƯƠNG", POSITIVE), ("ÂM", NEGATIVE)]:
    for tok in tokens:
        rows = by_sym.get(tok, [])
        if not rows: continue
        strict = scan_bells_strict(rows)
        nopos = scan_bells_no_pos(rows)
        # Số BELL day "cứu" = số ngày trong nopos mà không trong strict
        strict_days = set(d for d, _ in strict)
        rescued = [d for d, _ in nopos if d not in strict_days]
        table.append((label, tok, len(strict), len(nopos), len(rescued)))

print(f"{'label':<8} {'token':<15} {'strict':>8} {'no_pos':>8} {'rescued':>8}")
print("─" * 55)
for label, tok, n_s, n_np, n_r in table:
    marker = " ★ BTR" if tok == "BTR" and n_r > 0 else ""
    print(f"  {label:<6} {tok:<15} {n_s:>8} {n_np:>8} {n_r:>8}{marker}")

# Đếm total
pos_rescued = sum(n_r for l, t, ns, nn, n_r in table if l == "DƯƠNG")
neg_leaked = sum(n_r for l, t, ns, nn, n_r in table if l == "ÂM")
pos_strict = sum(ns for l, t, ns, nn, n_r in table if l == "DƯƠNG")
pos_nopos = sum(nn for l, t, ns, nn, n_r in table if l == "DƯƠNG")
neg_strict = sum(ns for l, t, ns, nn, n_r in table if l == "ÂM")
neg_nopos = sum(nn for l, t, ns, nn, n_r in table if l == "ÂM")

print(f"\nTổng: DƯƠNG strict={pos_strict} · no_pos={pos_nopos} · rescued={pos_rescued}")
print(f"      ÂM   strict={neg_strict} · no_pos={neg_nopos} · rescued={neg_leaked}")

# Số DƯƠNG mới cứu (0 → có ít nhất 1 BELL day) vs ÂM mới lọt
pos_new_tokens_saved = sum(1 for l, t, ns, nn, n_r in table if l == "DƯƠNG" and ns == 0 and nn > 0)
neg_new_tokens_leaked = sum(1 for l, t, ns, nn, n_r in table if l == "ÂM" and ns == 0 and nn > 0)
print(f"\nSố TOKEN dương mới có BELL sau khi bỏ cap: {pos_new_tokens_saved}")
print(f"Số TOKEN âm mới có BELL sau khi bỏ cap:    {neg_new_tokens_leaked}")

# BTR cụ thể
btr_row = next((x for x in table if x[1] == "BTR"), None)
if btr_row:
    _, _, n_s, n_np, n_r = btr_row
    if n_r > 0:
        print(f"\n★ BTR: strict=0 BELL · no_pos={n_np} BELL · CỨU {n_r} ngày")
        # In các ngày rescued BTR
        rows = by_sym["BTR"]
        nopos = scan_bells_no_pos(rows)
        strict = set(d for d, _ in scan_bells_strict(rows))
        for dstr, res in nopos:
            if dstr not in strict:
                print(f"    BTR RESCUED · {dstr} · Δacc={res['dacc']*100:+.1f}% · Δpos={res['dpos']*100:+.1f}% · div={res['div_D']:.3f}")
    else:
        print(f"\n☒ BTR: cả strict và no_pos đều 0 BELL")

print(f"\n═══ A4-4 · Cost estimate w=2 rerun (chưa chạy) ═══\n")
print("  Nếu đổi window w=3 → w=2, mọi kết quả AO/AL/AM phải chạy lại vì Δ*_bwd đổi giá trị.")
print("  Chi phí:")
print("  · Rerun AL/AM (universe 228 × 90d × 4 thresholds) ≈ 2-3 phút local")
print("  · Rerun AO grid (backward, universe scan) ≈ 2-3 phút local")
print("  · Rerun A3-4 calibration (28 crosses × D+5 check) ≈ 30 giây")
print("  · Rerun A3-7 UNHEDGE samples ≈ 30 giây")
print("  · Tổng: ~10 phút local + edit BWD_WINDOW=2 in u0_bell.py + rerun pins")
print("  ĐỪNG mượn số w=3 cho w=2 · nếu Tiên chọn w=2 phải chạy lại tất cả.")
