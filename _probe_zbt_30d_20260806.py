"""Fetch full 30-day ZBT data from fapi directly: klines + funding + LSR + OI + spot.
Window: ~07/07→05/08 (30 closed days). Export chỉ dùng để fill taker_buy_pct chuẩn hơn.
"""
import sys, io, json, urllib.request, time
from datetime import datetime, timezone, timedelta
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

SYM = "ZBTUSDT"

def get(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read())
    except Exception as e:
        return {"ERROR": str(e)}

def ts_to_date(ms):
    return datetime.fromtimestamp(ms/1000, tz=timezone.utc).strftime("%Y-%m-%d")

BASE_F = "https://fapi.binance.com"
BASE_S = "https://api.binance.com"

# ── 1. PERP klines 1d, limit=32 (dư) ─────────────────────────────────────────
print("=== [1] Perp klines ===")
kl = get(f"{BASE_F}/fapi/v1/klines?symbol={SYM}&interval=1d&limit=32")
perp = {}
if isinstance(kl, list):
    for k in kl:
        d = ts_to_date(k[0])
        perp[d] = {
            "open": float(k[1]), "high": float(k[2]),
            "low": float(k[3]), "close": float(k[4]),
            "vol_perp": float(k[7]),
            "taker_buy_pct_kl": round(float(k[10])/float(k[7])*100, 4) if float(k[7]) > 0 else None,
        }
    print(f"  Got {len(perp)} perp days: {min(perp)} → {max(perp)}")
else:
    print(f"  ERROR: {kl}")

# ── 2. Funding rate history → aggregate daily ─────────────────────────────────
print("\n=== [2] Funding rates (daily aggregate) ===")
fr = get(f"{BASE_F}/fapi/v1/fundingRate?symbol={SYM}&limit=120")
funding_daily = {}
if isinstance(fr, list):
    for rec in fr:
        d = ts_to_date(rec["fundingTime"])
        f = float(rec["fundingRate"])
        if d not in funding_daily:
            funding_daily[d] = []
        funding_daily[d].append(f)
    print(f"  Got {len(fr)} funding records covering {len(funding_daily)} days")
    for d in sorted(funding_daily.keys())[-5:]:
        vals = funding_daily[d]
        print(f"    {d}: n={len(vals)} avg={sum(vals)/len(vals):.6f} min={min(vals):.6f} max={max(vals):.6f}")
else:
    print(f"  ERROR: {fr}")

# ── 3. Global LSR 1d, limit=30 ────────────────────────────────────────────────
print("\n=== [3] Global LSR (gLSR) ===")
gl = get(f"{BASE_F}/futures/data/globalLongShortAccountRatio?symbol={SYM}&period=1d&limit=32")
glsr = {}
if isinstance(gl, list):
    for rec in gl:
        d = ts_to_date(rec["timestamp"])
        glsr[d] = float(rec["longShortRatio"])
    print(f"  Got {len(glsr)} days: {min(glsr)} → {max(glsr)}")
    for d in sorted(glsr.keys())[-5:]:
        print(f"    {d}: gLSR={glsr[d]}")
else:
    print(f"  ERROR: {gl}")

# ── 4. Top-trader Position Ratio (lsr_pos_r) ──────────────────────────────────
print("\n=== [4] Top-trader Position Ratio (pos_r) ===")
tp = get(f"{BASE_F}/futures/data/topLongShortPositionRatio?symbol={SYM}&period=1d&limit=32")
pos_r = {}
if isinstance(tp, list):
    for rec in tp:
        d = ts_to_date(rec["timestamp"])
        pos_r[d] = float(rec["longShortRatio"])
    print(f"  Got {len(pos_r)} days: {min(pos_r)} → {max(pos_r)}")
    for d in sorted(pos_r.keys())[-3:]:
        print(f"    {d}: pos_r={pos_r[d]}")
else:
    print(f"  ERROR: {tp}")

# ── 5. Top-trader Account Ratio (lsr_acc_r) ───────────────────────────────────
print("\n=== [5] Top-trader Account Ratio (acc_r) ===")
ta = get(f"{BASE_F}/futures/data/topLongShortAccountRatio?symbol={SYM}&period=1d&limit=32")
acc_r = {}
if isinstance(ta, list):
    for rec in ta:
        d = ts_to_date(rec["timestamp"])
        acc_r[d] = float(rec["longShortRatio"])
    print(f"  Got {len(acc_r)} days: {min(acc_r)} → {max(acc_r)}")
    for d in sorted(acc_r.keys())[-3:]:
        print(f"    {d}: acc_r={acc_r[d]}")
else:
    print(f"  ERROR: {ta}")

# ── 6. OI hist 1d, limit=30 ───────────────────────────────────────────────────
print("\n=== [6] OI hist ===")
oi_d = get(f"{BASE_F}/futures/data/openInterestHist?symbol={SYM}&period=1d&limit=32")
oi = {}
if isinstance(oi_d, list):
    for rec in oi_d:
        d = ts_to_date(rec["timestamp"])
        oi[d] = float(rec["sumOpenInterestValue"])
    print(f"  Got {len(oi)} days: {min(oi)} → {max(oi)}")
else:
    print(f"  ERROR: {oi_d}")

# ── 7. Spot klines 1d, limit=32 ───────────────────────────────────────────────
print("\n=== [7] Spot klines ===")
sk = get(f"{BASE_S}/api/v3/klines?symbol={SYM}&interval=1d&limit=32")
spot = {}
if isinstance(sk, list):
    for k in sk:
        d = ts_to_date(k[0])
        spot[d] = {"vol_spot": float(k[7])}
    print(f"  Got {len(spot)} spot days: {min(spot)} → {max(spot)}")
else:
    print(f"  ERROR: {sk}")

# ── 8. Export CSV taker (canonical where available) ───────────────────────────
import csv
from pathlib import Path
export_taker = {}
export_fn = {}
for fname in ["freshwatch_daily_2026-07.csv", "freshwatch_daily_2026-08.csv"]:
    fp = Path(r"D:\Check onchain fresh wallets\data\export") / fname
    if fp.exists():
        with open(fp, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                if row["symbol"] == SYM:
                    export_taker[row["date"]] = float(row["taker_buy_pct"])*100 if float(row["taker_buy_pct"]) <= 1 else float(row["taker_buy_pct"])
                    export_fn[row["date"]] = int(row.get("funding_n", 0) or 0)

print(f"\n  Export taker dates: {sorted(export_taker.keys())}")

# ── 9. COMPILE ALL DAYS ────────────────────────────────────────────────────────
print("\n=== [9] Full 30-day table ===")

# Union all dates from perp (authoritative range), exclude today
today = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d")
all_dates = sorted([d for d in perp.keys() if d < today])
# Also include any OI hist dates beyond perp
for d in sorted(oi.keys()):
    if d not in all_dates and d < today:
        all_dates.append(d)
all_dates = sorted(set(all_dates))

# Determine what date is "closed" (before today UTC)
print(f"  Total days to compile: {len(all_dates)}  ({all_dates[0]} → {all_dates[-1]})")
print()

hdr = f"{'date':<12} {'open':>8} {'close':>8} {'vol_perp':>13} {'taker%':>7} {'f_avg':>9} {'fn':>3} {'oi_usd':>11} {'pos_r':>7} {'acc_r':>7} {'gLSR':>7} {'vol_spot':>11} db"
print(hdr)
print("-"*len(hdr))

for d in all_dates:
    p = perp.get(d, {})
    # Funding
    f_vals = funding_daily.get(d, [])
    f_avg = sum(f_vals)/len(f_vals) if f_vals else None
    f_min = min(f_vals) if f_vals else None
    f_max = max(f_vals) if f_vals else None
    fn = len(f_vals) if f_vals else None
    # Use export fn if available and higher quality
    if d in export_fn and export_fn[d] >= (fn or 0):
        fn = export_fn[d]
    # Taker: prefer export
    if d in export_taker:
        taker = export_taker[d]
    else:
        taker = p.get("taker_buy_pct_kl")

    oi_v = oi.get(d)
    pr = pos_r.get(d)
    ar = acc_r.get(d)
    gl = glsr.get(d)
    vs = spot.get(d, {}).get("vol_spot")
    # data_bad: 1 if no funding or LSR
    db = 0 if (fn and fn >= 6 and pr is not None) else 1

    def fv(v, width=8, dec=5):
        if v is None: return "—".rjust(width)
        return f"{v:{width}.{dec}f}"
    def fi(v, width=13):
        if v is None: return "—".rjust(width)
        return f"{v:{width},.0f}"

    print(f"  {d}  {fv(p.get('open'),8,5)}  {fv(p.get('close'),8,5)}  "
          f"{fi(p.get('vol_perp'),13)}  {fv(taker,7,1)}  "
          f"{fv(f_avg,9,6)}  {str(fn).rjust(3) if fn is not None else '—'.rjust(3)}  "
          f"{fi(oi_v,11)}  "
          f"{fv(pr,7,4)}  {fv(ar,7,4)}  {fv(gl,7,4)}  "
          f"{fi(vs,11)}  {db}")

print(f"\n  Total rows: {len(all_dates)}")
print("\n[DONE]")
