"""A5-1/A5-2/A5-3 · BẢNG CALIBRATION E2 · A5-0 (bỏ cap Δpos, T ∈ {-20%, -15%}).

Cột theo ANALYSIS:
  token · loài · ngày chuông ĐẦU TIÊN · lead_known tới D0
  · số chuông TRƯỚC D0 · số chuông SAU D0 · hoặc "không chuông"

Tập:
  DƯƠNG · 13 proven với D0 hand-curated từ stage_ledger:
    HEDGE loài B (theo sổ): BTR · BULLA · UAI · AKE · HEMI · ON
    KHÔNG-HEDGE (loài A + khác): BANK · CYS · PROM · TUT · BTW · CAP · LOBSTER
  ÂM (đã biết):
    LIGHT · BROCCOLIF3B (2 crosses) · SOPH (3 crosses)
    POWER · HYPER · BASED · MITO

Cửa sổ quét: [D0 − 60d, D0 + 30d]. KHÔNG quét cả đời.

A5-4 hold-out guard: max_date_used < 2026-09-20.
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
            # A5-4: EXCLUDE any row on/after 2026-09-20
            d_iso = r["date"]
            d_row = datetime.strptime(d_iso, "%Y-%m-%d").date()
            if d_row >= HOLDOUT_START:
                continue
            by_sym.setdefault(bare, []).append(r)
            if d_iso > max_date_used:
                max_date_used = d_iso

# A5-4 · in guard
print(f"═══ A5-4 · HOLD-OUT GUARD ═══")
print(f"  max_date_used = {max_date_used}")
print(f"  HOLDOUT_START = {HOLDOUT_START}")
assert max_date_used < "2026-09-20", "HOLD-OUT VIOLATED"
print(f"  ✓ max_date_used < 2026-09-20 · PASS\n")

# Hand-curated D0 per token (từ stage_ledger)
POSITIVE_HEDGE = [
    # (token, loài, D0)
    ("BTR",   "B", "2026-08-26"),
    ("BULLA", "B", "2026-07-20"),   # wave-1 D0 · thứ 2 ~09-05 outside window
    ("UAI",   "B", "2026-08-24"),   # push D0 (pump 24/08)
    ("AKE",   "B", "2026-07-15"),
    ("HEMI",  "B", "2026-08-15"),
    ("ON",    "B", "2026-07-19"),
]

POSITIVE_NON_HEDGE = [
    ("BANK",    "A", "2026-07-11"),
    ("CYS",     "A", "2026-08-04"),
    ("PROM",    "A", "2026-07-19"),
    ("TUT",     "A", "2026-07-09"),
    ("BTW",     "D", "2026-08-03"),
    ("CAP",     "D", "2026-07-30"),
    ("LOBSTER", "D", "2026-08-25"),
]

NEGATIVE = [
    # (token, loại, D0-proxy · dùng ngày to check per Tiên. Nếu chỉ tokename thì scan full window)
    ("LIGHT",       "chronic-âm",     None),        # scan full 90d
    ("BROCCOLIF3B", "chronic-âm-x2",  None),
    ("SOPH",        "chronic-âm-x3 + D0 07-09", "2026-09-07"),   # one-column ignition
    ("POWER",       "âm",             None),
    ("HYPER",       "âm",             None),
    ("BASED",       "âm",             None),
    ("MITO",        "âm",             None),
    ("APR",         "âm (một cột)",   None),        # APR one-column pump earlier
]


def scan_bells_window(rows, d_start, d_end, threshold):
    """Trả list (date, res dict) với BELL status trong [d_start, d_end]."""
    days = []
    d = d_start
    while d <= d_end:
        res = u0_bell(rows, d.isoformat(), _div_avg3, dacc_bell_max=threshold)
        if res["status"] == "BELL":
            days.append((d.isoformat(), res))
        d += timedelta(days=1)
    return days


def calibration_row(tok, loai, D0_str, threshold):
    """Trả dict row cho bảng."""
    rows = by_sym.get(tok, [])
    if not rows:
        return {"token": tok, "loai": loai, "status": "NO-DATA"}

    if D0_str:
        d0 = datetime.strptime(D0_str, "%Y-%m-%d").date()
        w_start = d0 - timedelta(days=60)
        w_end = min(d0 + timedelta(days=30), HOLDOUT_START - timedelta(days=1))
    else:
        # Negative sans D0 · scan whole 90d ending pre-holdout
        w_end = HOLDOUT_START - timedelta(days=1)
        w_start = w_end - timedelta(days=90)
        d0 = None

    bells = scan_bells_window(rows, w_start, w_end, threshold)
    if not bells:
        return {"token": tok, "loai": loai, "D0": D0_str, "window": f"{w_start}→{w_end}",
                "status": "không chuông", "n_bells": 0}

    first_bell = bells[0][0]
    first_bell_d = datetime.strptime(first_bell, "%Y-%m-%d").date()

    if d0:
        lead_known = (d0 - first_bell_d).days  # positive = bell trước D0
        pre_d0 = sum(1 for dstr, _ in bells if datetime.strptime(dstr, "%Y-%m-%d").date() < d0)
        post_d0 = sum(1 for dstr, _ in bells if datetime.strptime(dstr, "%Y-%m-%d").date() >= d0)
    else:
        lead_known = None
        pre_d0 = None
        post_d0 = None

    return {
        "token": tok, "loai": loai, "D0": D0_str,
        "window": f"{w_start}→{w_end}",
        "first_bell": first_bell,
        "lead_known": lead_known,
        "n_bells": len(bells),
        "n_pre_d0": pre_d0,
        "n_post_d0": post_d0,
        "bells": bells,
    }


for T_label, T in [("T=-20%", -0.20), ("T=-15%", -0.15)]:
    print(f"\n═══ A5-1/A5-2/A5-3 · Bảng E2 · {T_label} · A5-0 (bỏ cap Δpos) ═══\n")

    # Table
    print(f"{'token':<15} {'loài':<3} {'D0':<12} {'first_bell':<12} {'lead':>5} {'n_bells':>7} {'pre_D0':>7} {'post_D0':>7} {'window':<25}")
    print("─" * 108)

    all_rows = []
    for tok, loai, D0 in POSITIVE_HEDGE + POSITIVE_NON_HEDGE + NEGATIVE:
        row = calibration_row(tok, loai, D0, T)
        all_rows.append(row)

        if row.get("status") == "NO-DATA":
            print(f"  {tok:<13} {loai:<3} [NO-DATA in fw store]")
            continue

        fb = row.get("first_bell", "─")
        lead = row.get("lead_known")
        lead_s = f"{lead:+d}" if lead is not None else "─"
        pre = row.get("n_pre_d0")
        post = row.get("n_post_d0")
        pre_s = str(pre) if pre is not None else "─"
        post_s = str(post) if post is not None else "─"
        d0_s = D0 if D0 else "─"
        print(f"  {tok:<13} {loai:<3} {d0_s:<12} {fb:<12} {lead_s:>5} {row.get('n_bells',0):>7} {pre_s:>7} {post_s:>7} {row['window']:<25}")

    # A5-2 · Split by loài
    print(f"\n─── A5-2 · Tách loài · sensitivity ───")
    hedge_hits = [r for r in all_rows if r["loai"] == "B" and r.get("n_bells", 0) > 0]
    hedge_total = [r for r in all_rows if r["loai"] == "B" and r.get("status") != "NO-DATA"]
    non_hedge_hits = [r for r in all_rows if r["loai"] in ("A", "D") and r.get("n_bells", 0) > 0]
    non_hedge_total = [r for r in all_rows if r["loai"] in ("A", "D") and r.get("status") != "NO-DATA"]
    neg_hits = [r for r in all_rows if r["loai"] not in ("A", "B", "D") and r.get("n_bells", 0) > 0]
    neg_total = [r for r in all_rows if r["loai"] not in ("A", "B", "D") and r.get("status") != "NO-DATA"]

    print(f"  HEDGE (loài B): {len(hedge_hits)}/{len(hedge_total)} có chuông")
    for r in hedge_hits:
        print(f"    ✓ {r['token']} · first_bell={r.get('first_bell')} · lead={r.get('lead_known')}d")
    for r in [r for r in hedge_total if r.get('n_bells', 0) == 0]:
        print(f"    ✗ {r['token']} không chuông")

    print(f"\n  KHÔNG-HEDGE (A/D): {len(non_hedge_hits)}/{len(non_hedge_total)} có chuông (per ANALYSIS: NGOÀI phạm vi)")
    for r in non_hedge_hits:
        print(f"    · {r['token']} ({r['loai']}) · first_bell={r.get('first_bell')} · lead={r.get('lead_known')}d · (out-of-scope)")
    for r in [r for r in non_hedge_total if r.get('n_bells', 0) == 0]:
        print(f"    · {r['token']} không chuông (out-of-scope · đúng)")

    print(f"\n  Sensitivity HEDGE-ONLY: {len(hedge_hits)}/{len(hedge_total)} = {len(hedge_hits)/max(1,len(hedge_total))*100:.0f}%")

    # A5-3 · post-D0 rings (vòng hai)
    print(f"\n─── A5-3 · Chuông SAU D0 (nạp-xả vòng hai, đếm riêng) ───")
    post_d0_rings = []
    for r in all_rows:
        if r.get("bells") and r.get("D0"):
            d0 = datetime.strptime(r["D0"], "%Y-%m-%d").date()
            for dstr, res in r["bells"]:
                bd = datetime.strptime(dstr, "%Y-%m-%d").date()
                if bd >= d0:
                    lag = (bd - d0).days
                    post_d0_rings.append((r["token"], r["loai"], dstr, lag, res["dacc_bwd"]))

    if post_d0_rings:
        print(f"  {'token':<15} {'loai':<3} {'ring':<12} {'lag_D0':>7} {'Δacc':>8}")
        for tok, loai, dstr, lag, dacc in post_d0_rings:
            print(f"    {tok:<13} {loai:<3} {dstr:<12} {lag:>+5}d {dacc*100:>+6.1f}%")
    else:
        print(f"  (không có chuông sau D0)")

    # Negative section stats
    print(f"\n─── ÂM · {len(neg_hits)}/{len(neg_total)} có chuông ───")
    for r in neg_hits:
        print(f"    · {r['token']} ({r['loai']}) · n_bells={r['n_bells']} · first={r.get('first_bell')}")
    for r in [r for r in neg_total if r.get('n_bells', 0) == 0]:
        print(f"    · {r['token']} không chuông")

    print()
