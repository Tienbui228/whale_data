"""_probe_hemi_h2_h4_20260820.py
H4: Gate + MEXC klines for HEMI (Jul01-Aug19, 50d) + identity check
H2: GOM-MISS AUTOPSY on Jul01-Aug13 baseline
Read-only.
"""
import sys, io, csv, json, urllib.request, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
from datetime import datetime, timezone, date as _date, timedelta
from statistics import median

ROOT     = Path(r"D:\Data back test\whale_data")
SCRATCH  = ROOT / "scratch"

SYM = "HEMI"
TICKER_PERP = "HEMIUSDT"
START = "2026-07-01"
END = "2026-08-19"

def fetch_json(url, params=None, timeout=15):
    if params:
        qs = "&".join(f"{k}={v}" for k, v in params.items())
        url = f"{url}?{qs}"
    req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        return {"_error": str(e)}
def to_ms(d): return int(datetime.strptime(d,"%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp()*1000)
def ms_to_date(ms): return datetime.fromtimestamp(int(ms)/1000, tz=timezone.utc).strftime("%Y-%m-%d")
def safe_float(v):
    if v in (None,"","None"): return None
    try: return float(v)
    except: return None

def hr(t): print("\n" + "="*70 + f"\n{t}\n" + "="*70)

s_ms = to_ms(START); e_ms = to_ms(END) + 86400000 - 1

# ── H4.1 Gate klines ──
hr("[H4.1 Gate HEMI_USDT klines]")
d = fetch_json("https://api.gateio.ws/api/v4/spot/candlesticks",
               {"currency_pair":f"{SYM}_USDT","interval":"1d",
                "from": s_ms//1000, "to": e_ms//1000, "limit": 100})
time.sleep(0.3)
gate_by_d = {}
if isinstance(d, list):
    # [t, v(quote), c, h, l, o, a(base), b(is_closed?)]
    for r in d:
        ts = int(r[0]) * 1000
        d_str = ms_to_date(ts)
        if d_str < START or d_str > END: continue
        gate_by_d[d_str] = {
            "o": float(r[5]), "c": float(r[2]),
            "vol_quote_usd": float(r[1]),
            "base_vol": float(r[6]) if len(r) > 6 else None,
        }
print(f"  Gate: {len(gate_by_d)} days")
# identity check
sample = sorted(gate_by_d.keys())[:3]
print("  identity-check 3 mẫu:")
for s in sample:
    r = gate_by_d[s]
    bit_eq = r.get("base_vol") == r["vol_quote_usd"]
    implied = r["vol_quote_usd"] / r["base_vol"] if r.get("base_vol") else None
    print(f"    {s}: vol_q={r['vol_quote_usd']} base={r.get('base_vol')} bit-eq={bit_eq} "
          f"implied={implied} c={r['c']}")

# ── H4.2 MEXC klines ──
hr("[H4.2 MEXC HEMIUSDT klines]")
d = fetch_json("https://api.mexc.com/api/v3/klines",
               {"symbol": f"{SYM}USDT","interval":"1d",
                "startTime": s_ms, "endTime": e_ms, "limit": 100})
time.sleep(0.3)
mexc_by_d = {}
if isinstance(d, list):
    # [openTime, o, h, l, c, base_vol, closeTime, quote_vol]
    for k in d:
        ts = int(k[0]); d_str = ms_to_date(ts)
        if d_str < START or d_str > END: continue
        mexc_by_d[d_str] = {
            "o": float(k[1]), "c": float(k[4]),
            "base_vol": float(k[5]),
            "quote_vol_usd": float(k[7]),
        }
print(f"  MEXC: {len(mexc_by_d)} days")
sample = sorted(mexc_by_d.keys())[:3]
print("  identity-check 3 mẫu:")
for s in sample:
    r = mexc_by_d[s]
    bit_eq = r["base_vol"] == r["quote_vol_usd"]
    implied = r["quote_vol_usd"] / r["base_vol"] if r["base_vol"] else None
    print(f"    {s}: vol_q={r['quote_vol_usd']} base={r['base_vol']} bit-eq={bit_eq} "
          f"implied={implied} c={r['c']}")

# ── H4.3 Price-band check (bài SUPERFORTUNE) ──
hr("[H4.3 PRICE-BAND CHECK vs perp]")
# Load perp
perp_by_d = {}
with open(SCRATCH / "hemi_perp_20260820.csv", encoding="utf-8") as f:
    for r in csv.DictReader(f):
        perp_by_d[r["date"]] = r

print("  Sample 3 ngày: perp_c vs gate_c vs mexc_c (band tolerance ±5%)")
for d_str in ["2026-07-15", "2026-08-01", "2026-08-15"]:
    pc = safe_float(perp_by_d.get(d_str,{}).get("c"))
    gc = gate_by_d.get(d_str,{}).get("c")
    mc = mexc_by_d.get(d_str,{}).get("c")
    print(f"    {d_str}: perp={pc} gate={gc} mexc={mc}")
    if pc and gc:
        band_gate = abs(gc-pc)/pc * 100
        print(f"      gate deviation: {band_gate:.2f}% {'OK' if band_gate<5 else 'FAIL'}")
    if pc and mc:
        band_mexc = abs(mc-pc)/pc * 100
        print(f"      mexc deviation: {band_mexc:.2f}% {'OK' if band_mexc<5 else 'FAIL'}")

# ── H4.4 Nền T7 all venues ──
hr("[H4.4 Nền T7 (Jul01-Aug13, pre-pump baseline) MEDIAN each venue]")
baseline_days = [d for d in perp_by_d if "2026-07-01" <= d <= "2026-08-13"]
for name, by_d, vol_key in [("perp", perp_by_d, "vol_quote_usd"),
                              ("gate", gate_by_d, "vol_quote_usd"),
                              ("mexc", mexc_by_d, "quote_vol_usd")]:
    vals = []
    for d in baseline_days:
        r = by_d.get(d)
        if r:
            v = r.get(vol_key)
            if v: vals.append(float(v))
    if vals:
        med = median(vals)
        print(f"  {name:<6}: median=${med:>13,.0f}  range=${min(vals):,.0f}..${max(vals):,.0f}  n={len(vals)}")

# Save
def write_csv(path, rows, fields):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for r in rows: w.writerow(r)

write_csv(SCRATCH / "hemi_gate_20260820.csv",
          [{"date": d, **v} for d,v in sorted(gate_by_d.items())],
          ["date","o","c","vol_quote_usd","base_vol"])
print(f"\n  Written: hemi_gate_20260820.csv ({len(gate_by_d)} rows)")
write_csv(SCRATCH / "hemi_mexc_20260820.csv",
          [{"date": d, **v} for d,v in sorted(mexc_by_d.items())],
          ["date","o","c","base_vol","quote_vol_usd"])
print(f"  Written: hemi_mexc_20260820.csv ({len(mexc_by_d)} rows)")

# ── H2 GOM-MISS AUTOPSY on Jul01-Aug13 ──
hr("[H2 GOM-MISS AUTOPSY Jul01-Aug13 (44 days baseline pre-pump)]")

# Load LSR + funding + OI
lsr_by_d = {}
with open(SCRATCH / "hemi_lsr_freshwatch_20260820.csv", encoding="utf-8") as f:
    for r in csv.DictReader(f):
        lsr_by_d[r["date"]] = {
            "pos_r": safe_float(r["pos_r"]),
            "acc_r": safe_float(r["acc_r"]),
            "gLSR": safe_float(r["gLSR"]),
            "taker_lsr": safe_float(r["taker_lsr"]),
        }

fund_by_d = {}
with open(SCRATCH / "hemi_funding_20260820.csv", encoding="utf-8") as f:
    for r in csv.DictReader(f):
        fund_by_d.setdefault(r["date"], []).append(float(r["fundingRate"]))

oi_by_d = {}
with open(SCRATCH / "hemi_oi_20260820.csv", encoding="utf-8") as f:
    for r in csv.DictReader(f):
        oi_by_d[r["date"]] = float(r["oi_usd"])

# Build derived: div_raw, div_avg3
autopsy = []
for d_str in sorted(perp_by_d):
    if d_str > "2026-08-13": continue
    lsr = lsr_by_d.get(d_str, {})
    pos_r = lsr.get("pos_r"); acc_r = lsr.get("acc_r"); gl = lsr.get("gLSR")
    div = round(pos_r/acc_r,4) if (pos_r and acc_r) else None
    frs = fund_by_d.get(d_str, [])
    f_avg = sum(frs)/len(frs) if frs else None
    # range3d
    prices = [safe_float(perp_by_d.get(x,{}).get("c")) for x in sorted(perp_by_d) if x <= d_str]
    range3d = None
    hi_lo = [(safe_float(perp_by_d.get(x,{}).get("h")), safe_float(perp_by_d.get(x,{}).get("l"))) for x in sorted(perp_by_d) if x <= d_str]
    hi_lo = [(h,l) for h,l in hi_lo if h and l][-3:]
    if len(hi_lo) == 3:
        h_max = max(h for h,_ in hi_lo)
        l_min = min(l for _,l in hi_lo)
        ref = (h_max + l_min)/2
        range3d = round((h_max-l_min)/ref*100, 2) if ref > 0 else None
    autopsy.append({
        "date": d_str, "c": safe_float(perp_by_d[d_str]["c"]),
        "pos_r": pos_r, "acc_r": acc_r, "gLSR": gl, "div": div,
        "f_avg": f_avg, "range3d": range3d, "oi": oi_by_d.get(d_str),
    })

# div_avg3
for i, r in enumerate(autopsy):
    if i < 2: continue
    p3 = [autopsy[j]["pos_r"] for j in range(i-2, i+1) if autopsy[j]["pos_r"]]
    a3 = [autopsy[j]["acc_r"] for j in range(i-2, i+1) if autopsy[j]["acc_r"]]
    if len(p3)==3 and len(a3)==3:
        aa = sum(a3)/3
        r["div_avg3"] = round((sum(p3)/3)/aa, 4) if aa else None

# oi_cycle_pos (30d rolling)
oi_arr = [r["oi"] for r in autopsy]
for i, r in enumerate(autopsy):
    if i < 15: continue  # need at least 15 pts
    w = [v for v in oi_arr[max(0,i-29):i+1] if v]
    cur = r["oi"]
    if len(w) >= 10 and cur:
        mn, mx = min(w), max(w)
        if mx > mn:
            r["oi_cycle_pos"] = round((cur-mn)/(mx-mn), 3)

# GOM-A A1 gate: div_avg3 leo TỪ ≤0.5 → ≥1.5 (bulls unwind hedge?) + gLSR ≤ 1.1 (no crowd)
# GOM-B B1: div_avg3 ≤ 0.5 + struct_n ≥ 3 + pin (f_avg 4e-5..6e-5) + no neg_div ngày bẩn
# GOM-C stealth_grind: breakout + oi_mult (2×+) + taker >= 50

print(f"\n  {'date':<11} {'c':>9} {'div':>6} {'div3':>7} {'gLSR':>6} {'f_avg':>10} "
      f"{'range3d':>7} {'oi':>10} {'cyc':>5} {'A1':>3} {'B1':>3}")

# Track streaks
struct_n_arr = []
struct = 0
near_miss = []
for r in autopsy:
    d3 = r.get("div_avg3")
    gl = r["gLSR"]; f_avg = r["f_avg"]; range3d = r["range3d"]
    cyc = r.get("oi_cycle_pos")

    # B1 check: div_avg3 ≤ 0.5
    if d3 is not None and d3 <= 0.5:
        struct += 1
    else:
        struct = 0
    r["struct_n"] = struct

    # A1 check: div_avg3 ≥ 1.5 AND gLSR ≤ 1.1 (transition from hedge to bull)
    a1_div_ok = d3 is not None and d3 >= 1.5
    a1_glsr_ok = gl is not None and gl <= 1.1
    a1_hit = a1_div_ok and a1_glsr_ok

    # B1 check: struct >= 3, pin funding, no neg_div
    b1_struct_ok = struct >= 3
    b1_pin_ok = f_avg is not None and 4e-5 <= f_avg <= 6e-5
    b1_neg_div_bẩn = f_avg is not None and f_avg <= -2e-4 and range3d is not None and range3d <= 7.0
    b1_hit = b1_struct_ok and b1_pin_ok and not b1_neg_div_bẩn

    a1_str = "HIT" if a1_hit else f"~{'d' if not a1_div_ok else 'g' if not a1_glsr_ok else ''}"
    b1_str = "HIT" if b1_hit else f"~{'s' if not b1_struct_ok else 'p' if not b1_pin_ok else 'n' if b1_neg_div_bẩn else ''}"

    def fmt(v, w, prec=2): return f"{v:>{w}.{prec}f}" if v is not None else " "*w
    print(f"  {r['date']:<11} {fmt(r['c'],9,5)} {fmt(r['div'],6,3)} {fmt(d3,7,4)} "
          f"{fmt(gl,6,3)} {fmt(f_avg,10,6)} {fmt(range3d,7,2)} "
          f"{fmt(r['oi'],10,0)} {fmt(cyc,5,3)} {a1_str:>3} {b1_str:>3}")

    # collect near-miss for report
    if d3 is not None:
        near = {}
        near["date"] = r["date"]
        near["div3"] = d3
        near["gLSR"] = gl
        near["b1_struct_n"] = struct
        near["b1_pin"] = b1_pin_ok
        near["a1_div_diff"] = 1.5 - d3 if not a1_div_ok else 0
        near["a1_glsr_diff"] = gl - 1.1 if gl and not a1_glsr_ok else 0
        near_miss.append(near)

# Find closest to A1 hit
if near_miss:
    print(f"\n  === TOP 5 NEAREST-MISS ===")
    print(f"  A1 (div_avg3 ≥ 1.5 AND gLSR ≤ 1.1):")
    a1_sorted = sorted(near_miss, key=lambda x: x["a1_div_diff"] + max(0, x["a1_glsr_diff"]))
    for r in a1_sorted[:5]:
        print(f"    {r['date']}: div_avg3={r['div3']} (cần ≥1.5, thiếu {r['a1_div_diff']:.4f}) · "
              f"gLSR={r['gLSR']} (cần ≤1.1, vượt {r['a1_glsr_diff']:.4f})")

    print(f"\n  B1 (div_avg3 ≤ 0.5 struct_n=3+ + pin):")
    b1_sorted = [r for r in near_miss if r["div3"] <= 0.5 and r["b1_pin"]]
    if b1_sorted:
        print(f"    Ngày HIT: {[r['date'] for r in b1_sorted]}")
    else:
        # nearest miss: struct_n close but not 3+
        b1_close = [r for r in near_miss if r["b1_struct_n"] >= 1]
        for r in b1_close[:5]:
            print(f"    {r['date']}: struct_n={r['b1_struct_n']} div3={r['div3']} pin={r['b1_pin']}")

# ── Watchlist_log check (via VPS) ──
hr("[H2.5 Watchlist_log grep HEMI]")
import subprocess
try:
    result = subprocess.run(["ssh","root@5.223.67.21",
                              "grep HEMI /root/Data_back_test/whale_data/data/export/watchlist_log_2026-08.csv"],
                             capture_output=True, text=True, timeout=30)
    if result.stdout:
        print(result.stdout)
    else:
        print("  (không có HEMI row nào trong watchlist_log_2026-08.csv)")
except Exception as e:
    print(f"  SSH err: {e}")

# Also 2026-07
try:
    result = subprocess.run(["ssh","root@5.223.67.21",
                              "grep HEMI /root/Data_back_test/whale_data/data/export/watchlist_log_2026-07.csv 2>/dev/null | tail -20"],
                             capture_output=True, text=True, timeout=30)
    if result.stdout:
        print("  --- Jul 2026 (last 20 HEMI rows) ---")
        print(result.stdout)
except Exception as e:
    pass

print("\n[DONE H2+H4]")
