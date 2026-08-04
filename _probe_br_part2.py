#!/usr/bin/env python3
"""Probe BR Part 2 — funding interval + BTW fix + Gate tape + R4 alpha."""
import csv, io, json, sys, datetime
from pathlib import Path
import pandas as pd
import urllib.request, urllib.error

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

EXP_DIR  = Path(r"D:\Check onchain fresh wallets\data\export")
STORE    = Path(r"D:\Data back test\whale_data\data\raw\spot_klines_1d")
TAPE_DIR = Path(r"D:\Data back test\whale_data\data\raw\tape")

def gv(r, k):
    v = r.get(k, "")
    if v in ("", None): return None
    try: return float(v)
    except: return None

# Load BR freshwatch
br_rows = {}
for f in sorted(EXP_DIR.glob("freshwatch_daily_2026-*.csv")):
    for r in csv.DictReader(open(f, encoding="utf-8-sig")):
        if r.get("symbol") == "BRUSDT":
            br_rows[r["date"]] = r

# ── BTW trap fix ──────────────────────────────────────────────────────────────
print("④ BTW hình bẫy PHA 2 — CORRECTED:")
window = ["2026-07-31","2026-08-01","2026-08-02","2026-08-03"]
px_list = [(d, gv(br_rows.get(d,{}), "px_avg")) for d in window]
px_vals = [p for _, p in px_list if p]
if px_vals:
    px_range = (max(px_vals)-min(px_vals))/min(px_vals)
    print(f"  px vals: {[(d, f'{p:.5f}') for d,p in px_list if p]}")
    print(f"  Biên độ 31/07→03/08: {px_range*100:.1f}% (cần ≤7% để là 'flat')")
    flat_tag = "KHÔNG FLAT" if px_range > 0.07 else "FLAT"
    print(f"  → {flat_tag}")

print("\n  Funding neg-div §5 (avg ≤-2e-4 OR min ≤-5e-4):")
for d in ["2026-07-28","2026-07-29","2026-07-30","2026-07-31","2026-08-01","2026-08-02","2026-08-03"]:
    r = br_rows.get(d, {})
    fav = gv(r, "funding_avg")
    fmi = gv(r, "funding_min")
    if fav is not None:
        neg_avg = fav <= -2e-4
        neg_min = (fmi is not None and fmi <= -5e-4)
        tag = "SUPPRESSOR_ON" if (neg_avg or neg_min) else "—"
        fmi_s = f"{fmi:.5f}" if fmi is not None else "?"
        print(f"  {d}: f_avg={fav:.5f}, f_min={fmi_s} → {tag}")

# ── Funding interval verify ────────────────────────────────────────────────────
print(f"\n{'='*60}")
print("Funding interval verify (fapi native BRUSDT, last 20 periods):")
try:
    url = "https://fapi.binance.com/fapi/v1/fundingRate?symbol=BRUSDT&limit=20"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read())
    for item in data:
        ts = item['fundingTime'] // 1000
        dt = datetime.datetime.utcfromtimestamp(ts).strftime("%Y-%m-%d %H:%M UTC")
        print(f"  {dt}  rate={float(item['fundingRate']):.6f}")
    if len(data) >= 2:
        intervals = []
        for i in range(1, len(data)):
            dt0 = data[i-1]['fundingTime'] // 1000
            dt1 = data[i]['fundingTime'] // 1000
            intervals.append((dt1-dt0)/3600)
        dom = max(set([round(x) for x in intervals]), key=[round(x) for x in intervals].count)
        print(f"\n  → Dominant interval: {dom:.0f}h")
        print(f"  → fn=6 trong freshwatch = 6 × {dom:.0f}h = {6*dom:.0f}h = {6*dom/24:.1f}d coverage/ngày")
except Exception as e:
    print(f"  fapi error: {e}")

# ── R3: Gate Tape ─────────────────────────────────────────────────────────────
print(f"\n{'='*60}")
print("R3 — GATE TAPE structure:")
print(f"TAPE_DIR: {TAPE_DIR}")
print(f"Exists: {TAPE_DIR.exists()}")

if TAPE_DIR.exists():
    # Top-level dirs
    top = sorted(TAPE_DIR.iterdir())
    print(f"Top-level entries ({len(top)}):")
    for d in top[:15]:
        print(f"  {d.name}")

    # Find BR-related files
    br_tape = sorted(TAPE_DIR.glob("**/*[Bb][Rr]*"))
    print(f"\nBR tape files: {len(br_tape)}")
    for f in br_tape[:10]:
        print(f"  {f.relative_to(TAPE_DIR)}")

    # Try reading any parquet to see schema
    all_pq = sorted(TAPE_DIR.glob("**/*.parquet"))
    print(f"\nTotal tape parquets: {len(all_pq)}")
    if all_pq:
        try:
            df = pd.read_parquet(all_pq[0])
            print(f"Schema: {list(df.columns)}")
            print(f"Dtypes: {df.dtypes.to_dict()}")
            if 'symbol' in df.columns:
                syms = df['symbol'].unique().tolist()
                print(f"Symbols: {syms[:20]}")
                br_df = df[df['symbol'].str.contains("BR", na=False)]
                print(f"BR rows: {len(br_df)}")
                if len(br_df):
                    print(br_df.head(3).to_string())
        except Exception as e:
            print(f"Error: {e}")
    else:
        # Maybe CSV or other format
        other = sorted(TAPE_DIR.glob("**/*.csv"))[:3]
        print(f"CSV files: {other}")
        if other:
            df = pd.read_csv(other[0])
            print(f"CSV schema: {list(df.columns)}")
            print(df.head(3).to_string())
else:
    print("TAPE_DIR does not exist — tape not collected locally?")
    # Check if tape is on VPS only
    print("\nChecking alternate tape paths...")
    alt_paths = [
        Path(r"D:\Data back test\whale_data\scratch"),
        Path(r"D:\Check onchain fresh wallets\data\raw\tape"),
    ]
    for ap in alt_paths:
        if ap.exists():
            entries = list(ap.iterdir())[:5]
            print(f"  {ap}: {[e.name for e in entries]}")

# ── R4: Alpha store summary ───────────────────────────────────────────────────
print(f"\n{'='*60}")
print("R4 — ALPHA store BR: full Jul-Aug window")
alpha_br = {}
for p in sorted(STORE.glob("date=2026-07-*"), key=str) + sorted(STORE.glob("date=2026-08-*"), key=str):
    files = list(p.glob("*.parquet"))
    if not files: continue
    try:
        df = pd.read_parquet(files[0])
        tag = df[df['symbol'] == 'BR'] if 'symbol' in df.columns else pd.DataFrame()
        if len(tag):
            row = tag.iloc[0]
            alpha_br[p.name.replace("date=", "")] = {
                'qv': float(row.get('quote_vol', 0) or 0),
                'close': float(row.get('close', 0) or 0),
            }
    except: pass

perp_px_map = {d: gv(r, "px_avg") for d,r in br_rows.items()}

print(f"{'date':12} {'alpha_vol_USD':>15} {'alpha_close':>12} {'perp_px':>10} {'spread%':>8}")
for d in sorted(alpha_br):
    r = alpha_br[d]
    pp = perp_px_map.get(d)
    spr = (r['close']/pp - 1)*100 if pp and r['close'] else None
    qv_s = f"${r['qv']:,.0f}" if r['qv'] else "$0"
    spr_s = f"{spr:+.2f}%" if spr is not None else "—"
    print(f"{d:12} {qv_s:>15} {r['close']:>12.6f} {pp if pp else 0:>10.6f} {spr_s:>8}")

# Alpha vol spike check
all_qv = [(d, r['qv']) for d, r in alpha_br.items() if r['qv'] > 0]
if all_qv:
    max_vol = max(all_qv, key=lambda x: x[1])
    avg_vol = sum(v for _, v in all_qv)/len(all_qv)
    print(f"\nAlpha vol max: ${max_vol[1]:,.0f} on {max_vol[0]}")
    print(f"Alpha vol avg (non-zero): ${avg_vol:,.0f}")
    print(f"Alpha vol 2026-07+: {[(d,f'${v:,.0f}') for d,v in all_qv if d>='2026-07-01']}")
