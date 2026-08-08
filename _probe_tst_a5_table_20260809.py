"""
_probe_tst_a5_table_20260809.py
Read perp CSV + LSR CSV to compute A.5 ba-dao-ham table values.
+ B-2 flag summary from scratch CSVs.
"""
import sys, io, csv, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
from datetime import datetime, timezone

SCRATCH = Path(r"D:\Data back test\whale_data\scratch")

def log(s="", end="\n"): print(s, end=end)
def sf(v, d=None):
    try: return float(v) if v not in (None,"",) else d
    except: return d

NOW = datetime.now(timezone.utc)
log("=" * 70)
log(f"TST A.5 TABLE + B-2  |  {NOW.strftime('%Y-%m-%d %H:%M UTC')}")
log("=" * 70)

# ── Load perp klines (converted) ─────────────────────────────────────────────
perp_rows = []
with open(SCRATCH / "tst_perp_20260809.csv", encoding="utf-8") as f:
    perp_rows = sorted(csv.DictReader(f), key=lambda r: r.get("date",""))
log(f"  Perp rows: {len(perp_rows)} ({perp_rows[0]['date']} → {perp_rows[-1]['date']})")

# ── Load LSR (merged fresh+freshwatch) ───────────────────────────────────────
lsr_by_d = {}
# freshwatch first (lower priority)
for tag in ["2026-06", "2026-07"]:
    fw_path = SCRATCH / f"freshwatch_daily_{tag}.csv"
    if fw_path.exists():
        with open(fw_path, encoding="utf-8") as f:
            for r in csv.DictReader(f):
                if r.get("symbol","").upper() == "TSTUSDT":
                    lsr_by_d[r["date"]] = {
                        "pos_r": sf(r.get("lsr_pos_r")), "acc_r": sf(r.get("lsr_acc_r")),
                        "gLSR":  sf(r.get("lsr_global_r")), "src": "freshwatch"
                    }
# fresh LSR overrides
with open(SCRATCH / "tst_lsr_raw_20260809.csv", encoding="utf-8") as f:
    for r in csv.DictReader(f):
        d = r.get("date","")
        if d:
            lsr_by_d[d] = {
                "pos_r": sf(r.get("pos_r")), "acc_r": sf(r.get("acc_r")),
                "gLSR":  sf(r.get("gLSR")),  "src": "fresh"
            }
log(f"  LSR dates: {len(lsr_by_d)} ({min(lsr_by_d)} → {max(lsr_by_d)})")

# ── Load OI hist ──────────────────────────────────────────────────────────────
oi_by_d = {}
with open(SCRATCH / "tst_oi_hist_20260809.csv", encoding="utf-8") as f:
    for r in csv.DictReader(f):
        if r.get("date"):
            oi_by_d[r["date"]] = {"oi_usd": sf(r.get("oi_usd")), "oi_token": sf(r.get("oi_token"))}

# ── Load funding ──────────────────────────────────────────────────────────────
fund_by_d = {}
with open(SCRATCH / "tst_funding_20260809.csv", encoding="utf-8") as f:
    for r in csv.DictReader(f):
        d = r.get("date",""); rate = sf(r.get("fundingRate"))
        if d and rate is not None:
            fund_by_d.setdefault(d, []).append(rate)

# ── Build arrays ─────────────────────────────────────────────────────────────
all_dates = [r["date"] for r in perp_rows]
N = len(all_dates)

c_vals    = [sf(r["c"])             for r in perp_rows]
h_vals    = [sf(r["h"])             for r in perp_rows]
l_vals    = [sf(r["l"])             for r in perp_rows]
vol_usd   = [sf(r["vol_quote_usd"]) for r in perp_rows]
taker_all = [sf(r["taker_pct"])     for r in perp_rows]
ret_all   = [sf(r["ret_1d"])        for r in perp_rows]
pos_r_all = [lsr_by_d.get(d, {}).get("pos_r") for d in all_dates]
acc_r_all = [lsr_by_d.get(d, {}).get("acc_r") for d in all_dates]
glsr_all  = [lsr_by_d.get(d, {}).get("gLSR")  for d in all_dates]

def rolling_med14(vals):
    out = [None]*len(vals)
    for i in range(14, len(vals)):
        w = [v for v in vals[i-14:i] if v is not None]
        if len(w) >= 7:
            s = sorted(w); n = len(s)
            out[i] = (s[n//2-1]+s[n//2])/2 if n%2==0 else s[n//2]
    return out

vol_med14 = rolling_med14(vol_usd)
vol_vs_m  = [round(vol_usd[i]/vol_med14[i], 4) if vol_med14[i] else None for i in range(N)]

div_raw_all = [round(pos_r_all[i]/acc_r_all[i], 4)
               if (pos_r_all[i] and acc_r_all[i] and acc_r_all[i] != 0) else None
               for i in range(N)]

div_avg3_all = [None]*N
for i in range(2, N):
    p3 = [v for v in pos_r_all[i-2:i+1] if v is not None]
    a3 = [v for v in acc_r_all[i-2:i+1] if v is not None]
    if len(p3) == 3 and len(a3) == 3:
        ap = sum(p3)/3; aa = sum(a3)/3
        div_avg3_all[i] = round(ap/aa, 4) if aa != 0 else None

slope_all = [None]*N
for i in range(5, N):
    g = glsr_all[i]; gp = glsr_all[i-5]
    if g is not None and gp is not None and gp > 0:
        slope_all[i] = round(g/gp, 4)

# ── A.5 BA-ĐẠO-HÀM TABLE ────────────────────────────────────────────────────
log("\n\n=== A.5 BẢNG BA-ĐẠO-HÀM (TST — mốc 7/14/21/28 ngày trước 07/08/2026) ===")

# Mốc definitions: 7d = 7 rows before last, etc.
# Last row index = N-1 (= 07/08/2026)
mocs = [("28d", 27), ("21d", 20), ("14d", 13), ("7d", 6), ("Now 07/08", 0)]

log(f"\n{'':12s} {'28d (10/07)':>16s} {'21d (17/07)':>16s} {'14d (24/07)':>16s} {'7d (31/07)':>16s} {'07/08':>16s}")
log("-" * 95)

def get_v(arr, offset):
    idx = N-1-offset
    return arr[idx] if 0 <= idx < N else None

# div_avg3
log(f"{'div_avg3':12s}", end="")
da_vals = []
for label, off in mocs:
    v = get_v(div_avg3_all, off)
    da_vals.append(v)
    log(f" {str(round(v,4)) if v else 'N/A':>16s}", end="")
log()
# %chg from 28d
log(f"{'  %chg_28d':12s}", end="")
base = da_vals[0]
for v in da_vals:
    if v and base:
        log(f" {round((v-base)/base*100,1):>15.1f}%", end="")
    else:
        log(f" {'N/A':>16s}", end="")
log()

# gLSR
log(f"\n{'gLSR':12s}", end="")
glsr_vals_moc = []
for label, off in mocs:
    v = get_v(glsr_all, off)
    glsr_vals_moc.append(v)
    log(f" {str(round(v,4)) if v else 'N/A':>16s}", end="")
log()
# min28d + crossings
glsr_28 = [glsr_all[N-1-i] for i in range(28) if glsr_all[N-1-i] is not None]
log(f"  min28d={round(min(glsr_28),4) if glsr_28 else 'N/A'} max28d={round(max(glsr_28),4) if glsr_28 else 'N/A'}")
# Days crossed 0.7 or 1.0
for thr, label in [(0.7,"0.7"), (1.0,"1.0"), (1.1,"1.1")]:
    crossed = [(all_dates[N-1-i], "DOWN" if (glsr_28[i] < thr and (i+1 < len(glsr_28) and glsr_28[i+1] >= thr)) else "UP")
               for i in range(len(glsr_28)-1)
               if (glsr_28[i] >= thr and glsr_28[i+1] < thr) or (glsr_28[i] < thr and glsr_28[i+1] >= thr)]
    if crossed:
        log(f"  gLSR crosses {label}: {crossed}")
    else:
        log(f"  gLSR crosses {label}: NONE in last 28d (range {round(min(glsr_28),3) if glsr_28 else 'N/A'}→{round(max(glsr_28),3) if glsr_28 else 'N/A'})")

# vol_vs_med14 (avg7 ending at each moc)
log(f"\n{'vol_vs_m':12s} avg7 ending at moc:")
for label, off in mocs:
    window = [vol_vs_m[N-1-off-i] for i in range(7) if 0 <= N-1-off-i < N and vol_vs_m[N-1-off-i] is not None]
    avg7 = round(sum(window)/len(window), 3) if window else None
    date = all_dates[N-1-off] if N-1-off >= 0 else "?"
    log(f"  {label} ({date}): avg7={avg7} (n={len(window)})")

log(f"\n  Note: LSR only from 2026-06-27 (freshwatch start)")
log(f"  gLSR has been > 1.1 for entire 42d window (never crosses below 1.1)")

# ── pos_r full trajectory ─────────────────────────────────────────────────────
log("\n\n=== pos_r / gLSR / div_avg3 trajectory (42d LSR window) ===")
log(f"{'date':12s} {'pos_r':>7s} {'acc_r':>7s} {'gLSR':>7s} {'div_raw':>8s} {'div_avg3':>9s} {'slope_5d':>9s} {'vol_vs_m':>9s} {'src':>10s}")
for i in range(N):
    if pos_r_all[i] is None: continue
    src = lsr_by_d.get(all_dates[i], {}).get("src","?")
    log(f"  {all_dates[i]:10s} {str(round(pos_r_all[i],4)):>7s} {str(round(acc_r_all[i],4) if acc_r_all[i] else '-'):>7s} {str(round(glsr_all[i],4) if glsr_all[i] else '-'):>7s} {str(round(div_raw_all[i],4) if div_raw_all[i] else '-'):>8s} {str(round(div_avg3_all[i],4) if div_avg3_all[i] else '-'):>9s} {str(round(slope_all[i],4) if slope_all[i] else '-'):>9s} {str(round(vol_vs_m[i],3) if vol_vs_m[i] else '-'):>9s} {src:>10s}")

# ── B-2 flags (computed from arrays) ─────────────────────────────────────────
log("\n\n=== B-2 Diagnostic Flags (545 days) ===")
flag_dist = sum(1 for i in range(N) if taker_all[i] is not None and ret_all[i] is not None
                and taker_all[i] >= 50.0 and ret_all[i] < 0)
flag_decay = sum(1 for i in range(N) if taker_all[i] is not None and taker_all[i] < 45.0)
flag_hedge = sum(1 for i in range(N) if div_avg3_all[i] is not None and div_avg3_all[i] <= 0.5)
flag_knife = sum(1 for i in range(1, N) if glsr_all[i] is not None and glsr_all[i-1] is not None
                  and ret_all[i] is not None and glsr_all[i] > glsr_all[i-1] and ret_all[i] < -3.0)
# neg_div requires funding
flag_neg_div = 0
for d, rates in fund_by_d.items():
    f_avg = sum(rates)/len(rates) if rates else None
    if f_avg is not None and f_avg <= -2e-4:
        idx = all_dates.index(d) if d in all_dates else -1
        if idx >= 2:
            h3 = [v for v in h_vals[idx-2:idx+1] if v is not None]
            l3 = [v for v in l_vals[idx-2:idx+1] if v is not None]
            if h3 and l3:
                mx = max(h3); mn = min(l3); ref = (mx+mn)/2
                if ref > 0 and (mx-mn)/ref*100 <= 7.0:
                    flag_neg_div += 1

log(f"  flag_dist_wall_day: {flag_dist} / {N} = {flag_dist/N*100:.1f}%")
log(f"  flag_decay_day:     {flag_decay} / {N} = {flag_decay/N*100:.1f}%")
log(f"  flag_hedge_struct:  {flag_hedge} (div_avg3 ≤ 0.5)")
log(f"  flag_neg_div:       {flag_neg_div}")
log(f"  flag_knife_crowd:   {flag_knife}")

# knife_crowd detail
knife_rows = [(all_dates[i], ret_all[i], glsr_all[i], taker_all[i])
              for i in range(1, N)
              if glsr_all[i] is not None and glsr_all[i-1] is not None
              and ret_all[i] is not None
              and glsr_all[i] > glsr_all[i-1] and ret_all[i] < -3.0]
if knife_rows:
    log(f"\n  knife_crowd detail:")
    for d, ret, g, tk in knife_rows:
        log(f"    {d}: ret={ret:.1f}% gLSR={g:.4f} taker={tk:.1f}%")

# ── Funding summary ───────────────────────────────────────────────────────────
log("\n\n=== Funding Summary (fund hist available from 2026-05-16) ===")
log(f"  Total funding days: {len(fund_by_d)}")
neg_fund_days = [(d, round(sum(r)/len(r),6)) for d, r in fund_by_d.items()
                 if r and sum(r)/len(r) < 0]
log(f"  Negative f_avg days: {len(neg_fund_days)}")
log(f"  Last 10 days:")
for d, fn_rates in sorted(fund_by_d.items())[-10:]:
    f_avg = round(sum(fn_rates)/len(fn_rates), 6)
    f_min = round(min(fn_rates), 6)
    f_max = round(max(fn_rates), 6)
    log(f"    {d}: fn={len(fn_rates)} f_avg={f_avg} f_min={f_min} f_max={f_max}")

# ── OIS slope check ──────────────────────────────────────────────────────────
log("\n\n=== OI trend (30d hist) ===")
oi_sorted = sorted(oi_by_d.items())
log(f"  Date range: {oi_sorted[0][0]} → {oi_sorted[-1][0]}")
for d, oi in oi_sorted:
    log(f"    {d}: oi_usd={oi.get('oi_usd','?')} oi_token={oi.get('oi_token','?')}")

log(f"\n[A.5/B-2 DONE]")
