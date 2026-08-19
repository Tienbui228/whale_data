"""Supplementary venue fetch: Alpha + KuCoin + MEXC klines for STBL Jul20-Aug18."""
import sys, io, json, urllib.request, time, csv
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
from datetime import datetime, timezone, date as _date, timedelta
from statistics import median

SCRATCH = Path(r"D:\Data back test\whale_data\scratch")

SYM = "STBL"
ALPHA_ID = "ALPHA_376"  # from S0.③ probe (UNVERIFIED — symbol-string match)
END = "2026-08-18"
END_DT = _date.fromisoformat(END)
START_30D = (END_DT - timedelta(days=30)).isoformat()

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

s_ms = to_ms(START_30D); e_ms = to_ms(END) + 86400000 - 1

# ── Alpha bapi klines (ALPHA_376) ──
print("=== Alpha ALPHA_376 klines ===")
d = fetch_json("https://www.binance.com/bapi/defi/v1/public/alpha-trade/klines",
               {"symbol":f"{ALPHA_ID}USDT","interval":"1d","startTime":s_ms,"endTime":e_ms,"limit":40})
time.sleep(0.3)
alpha_by_d = {}
data = d.get("data") if isinstance(d, dict) and "data" in d else (d if isinstance(d, list) else [])
for k in data:
    ts = int(k[0]); d_str = ms_to_date(ts)
    if d_str < START_30D or d_str > END: continue
    # IDENTITY CHECK: L-48 mirror pattern
    bv = float(k[5]); tv = float(k[9]) if len(k)>=10 else 0
    q  = float(k[7]); tq = float(k[10]) if len(k)>=11 else 0
    mirror = (bv==tv and q==tq)
    alpha_by_d[d_str] = {
        "c": float(k[4]), "quote_vol_usd": q, "trades": int(k[8]) if len(k)>=9 else 0,
        "MIRROR_FLAG": mirror,
    }
print(f"  rows: {len(alpha_by_d)}")
mir = sum(1 for r in alpha_by_d.values() if r["MIRROR_FLAG"])
print(f"  MIRROR flag count: {mir}/{len(alpha_by_d)} (L-48 broken taker pattern)")
for d_str in sorted(alpha_by_d)[-5:]:
    r = alpha_by_d[d_str]
    print(f"    {d_str}: c={r['c']} vol_usd={r['quote_vol_usd']:.2f} trades={r['trades']} mirror={r['MIRROR_FLAG']}")

# ── KuCoin klines ──
print("\n=== KuCoin STBL-USDT klines ===")
d = fetch_json("https://api.kucoin.com/api/v1/market/candles",
               {"type":"1day","symbol":f"{SYM}-USDT",
                "startAt": s_ms//1000, "endAt": e_ms//1000})
time.sleep(0.3)
kucoin_by_d = {}
if isinstance(d, dict) and str(d.get("code")) == "200000":
    rows = d.get("data") or []
    # KuCoin returns [time, open, close, high, low, volume(base), turnover(quote_usd)]
    for r in rows:
        ts = int(r[0]) * 1000
        d_str = ms_to_date(ts)
        if d_str < START_30D or d_str > END: continue
        kucoin_by_d[d_str] = {
            "o": float(r[1]), "c": float(r[2]),
            "base_vol": float(r[5]),
            "turnover_usd": float(r[6]),
        }
else:
    print(f"  KuCoin err: {d}")
print(f"  rows: {len(kucoin_by_d)}")
# identity check
sample = sorted(kucoin_by_d.keys())[:3]
for s in sample:
    r = kucoin_by_d[s]
    print(f"  identity {s}: base_vol={r['base_vol']} turnover_usd={r['turnover_usd']} bit-eq={r['base_vol']==r['turnover_usd']} implied={r['turnover_usd']/r['base_vol'] if r['base_vol'] else '-'} c={r['c']}")
for d_str in sorted(kucoin_by_d)[-5:]:
    r = kucoin_by_d[d_str]
    print(f"    {d_str}: c={r['c']} turnover=${r['turnover_usd']:.0f}")

# ── MEXC klines ──
print("\n=== MEXC STBLUSDT klines ===")
d = fetch_json("https://api.mexc.com/api/v3/klines",
               {"symbol":f"{SYM}USDT","interval":"1d",
                "startTime": s_ms, "endTime": e_ms, "limit": 40})
time.sleep(0.3)
mexc_by_d = {}
if isinstance(d, list):
    # MEXC klines schema: [openTime, o, h, l, c, volume(base), closeTime, quoteVolume]
    for k in d:
        ts = int(k[0]); d_str = ms_to_date(ts)
        if d_str < START_30D or d_str > END: continue
        mexc_by_d[d_str] = {
            "o": float(k[1]), "c": float(k[4]),
            "base_vol": float(k[5]),
            "quote_vol_usd": float(k[7]),
        }
else:
    print(f"  MEXC err: {d}")
print(f"  rows: {len(mexc_by_d)}")
sample = sorted(mexc_by_d.keys())[:3]
for s in sample:
    r = mexc_by_d[s]
    print(f"  identity {s}: base_vol={r['base_vol']} quote_vol={r['quote_vol_usd']} bit-eq={r['base_vol']==r['quote_vol_usd']} implied={r['quote_vol_usd']/r['base_vol'] if r['base_vol'] else '-'} c={r['c']}")
for d_str in sorted(mexc_by_d)[-5:]:
    r = mexc_by_d[d_str]
    print(f"    {d_str}: c={r['c']} vol_usd=${r['quote_vol_usd']:.0f}")

# ── Save + summary comparison table ──
for v_name, by_d in [("alpha_bapi", alpha_by_d), ("kucoin", kucoin_by_d), ("mexc", mexc_by_d)]:
    if not by_d: continue
    p = SCRATCH / f"stbl_{v_name}_20260819.csv"
    keys = list(by_d[list(by_d.keys())[0]].keys())
    with open(p, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["date"] + keys)
        w.writeheader()
        for d_str in sorted(by_d): w.writerow({"date": d_str, **by_d[d_str]})
    print(f"\n  Written: {p.name} ({len(by_d)} rows)")

# ── Combined table Aug10-Aug18 ──
print("\n=== ALL VENUES Aug10-Aug18 ===")
# Load Gate from earlier
gate_by_d = {}
gate_csv = SCRATCH / "stbl_gate_spot_20260819.csv"
if gate_csv.exists():
    for r in csv.DictReader(open(gate_csv, encoding="utf-8")):
        gate_by_d[r["date"]] = r

# Load perp
perp_by_d = {}
perp_csv = SCRATCH / "stbl_perp_60d_20260819.csv"
if perp_csv.exists():
    for r in csv.DictReader(open(perp_csv, encoding="utf-8")):
        perp_by_d[r["date"]] = r

print(f"\n  {'date':<12} {'perp':>12} {'gate':>10} {'kucoin':>10} {'mexc':>10} {'alpha':>10}")
for d_str in sorted(set(list(gate_by_d) + list(mexc_by_d)) & set(perp_by_d)):
    if not ("2026-08-10" <= d_str <= "2026-08-18"): continue
    perp_v = float(perp_by_d.get(d_str,{}).get("vol_quote_usd") or 0)
    gate_v = float(gate_by_d.get(d_str,{}).get("vol_quote_usd") or 0)
    kucoin_v = kucoin_by_d.get(d_str,{}).get("turnover_usd", 0)
    mexc_v = mexc_by_d.get(d_str,{}).get("quote_vol_usd", 0)
    alpha_v = alpha_by_d.get(d_str,{}).get("quote_vol_usd", 0)
    print(f"  {d_str:<12} {perp_v:>12,.0f} {gate_v:>10,.0f} {kucoin_v:>10,.0f} {mexc_v:>10,.0f} {alpha_v:>10,.0f}")

# Nền T7 all venues
print("\n=== Nền T7 (Jul20-Aug01, 13 days) MEDIAN each venue ===")
nen_days = [d for d in perp_by_d if "2026-07-20" <= d <= "2026-08-01"]
for name, by_d, vol_key in [("perp", perp_by_d, "vol_quote_usd"),
                              ("gate", gate_by_d, "vol_quote_usd"),
                              ("kucoin", kucoin_by_d, "turnover_usd"),
                              ("mexc", mexc_by_d, "quote_vol_usd"),
                              ("alpha", alpha_by_d, "quote_vol_usd")]:
    vals = []
    for d in nen_days:
        r = by_d.get(d)
        if r:
            v = r.get(vol_key)
            if v: vals.append(float(v))
    if vals:
        med = median(vals)
        print(f"  {name:<8}: median=${med:>13,.0f}  range=${min(vals):,.0f}..${max(vals):,.0f}  n={len(vals)}")

print("\n[DONE supp]")
