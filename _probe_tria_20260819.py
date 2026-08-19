"""_probe_tria_20260819.py — TRIAUSDT un-hedge readout probe.
Window: 2026-07-20 → 2026-08-18 (30d) + intraday 19/08.
Read-only. Output: raw data for report.
"""
import sys, io, csv, json, urllib.request, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
from datetime import datetime, timezone
from statistics import median

ROOT    = Path(r"D:\Data back test\whale_data")
SCRATCH = ROOT / "scratch"
EXPORT  = ROOT / "data" / "export"

SYM    = "TRIA"
TICKER = "TRIAUSDT"
START  = "2026-07-20"
END    = "2026-08-18"

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

# ── verify perp exists ─────────────────────────────────────────────────
hr("[EXCHANGE INFO] fapi verify TRIAUSDT")
d = fetch_json("https://fapi.binance.com/fapi/v1/exchangeInfo", {})
time.sleep(0.3)
tria_perp = None
if isinstance(d, dict):
    tria_perp = next((s for s in d.get("symbols",[]) if s.get("symbol")==TICKER), None)
if tria_perp:
    print(f"  PERP TRIAUSDT: status={tria_perp.get('status')} onboardDate={tria_perp.get('onboardDate')}")
    if tria_perp.get('onboardDate'):
        print(f"    onboarded: {ms_to_date(tria_perp['onboardDate'])}")
else:
    print("  PERP TRIAUSDT: NOT FOUND")
    sys.exit(1)

# also alpha meta
d = fetch_json("https://www.binance.com/bapi/defi/v1/public/wallet-direct/buw/wallet/cex/alpha/all/token/list", {})
time.sleep(0.3)
tria_alpha = None
if isinstance(d, dict) and "data" in d:
    for tok in d.get("data") or []:
        if str(tok.get("symbol","")).upper() == "TRIA":
            tria_alpha = tok; break
if tria_alpha:
    print(f"  Alpha TRIA: alphaId={tria_alpha.get('alphaId')} name={tria_alpha.get('name')} "
          f"fullyDelisted={tria_alpha.get('fullyDelisted')} offline={tria_alpha.get('offline')} "
          f"chain={tria_alpha.get('chainName')}")
else:
    print("  Alpha TRIA: not in list")

# ── perp klines ─────────────────────────────────────────────────────────
hr(f"[PERP klines {START} → {END}]")
s_ms = to_ms(START); e_ms = to_ms(END) + 86400000 - 1
d = fetch_json("https://fapi.binance.com/fapi/v1/klines",
               {"symbol": TICKER, "interval": "1d",
                "startTime": s_ms, "endTime": e_ms, "limit": 40})
time.sleep(0.3)
perp = {}
if isinstance(d, list):
    for k in d:
        d_str = ms_to_date(int(k[0]))
        if d_str < START or d_str > END: continue
        vol_q = float(k[7]); taker_q = float(k[10])
        perp[d_str] = {
            "o": float(k[1]), "h": float(k[2]), "l": float(k[3]), "c": float(k[4]),
            "vol_quote_usd": round(vol_q, 2),
            "taker_buy_pct": round(taker_q/vol_q*100, 4) if vol_q > 0 else None,
        }
print(f"  perp days: {len(perp)}, range={min(perp)}→{max(perp)}")

# ── funding ─────────────────────────────────────────────────────────────
hr(f"[FUNDING {START} → {END}]")
fund_all = []; cur = s_ms
while cur <= e_ms:
    d = fetch_json("https://fapi.binance.com/fapi/v1/fundingRate",
                   {"symbol": TICKER, "startTime": cur, "endTime": e_ms, "limit": 1000})
    time.sleep(0.3)
    if not isinstance(d, list) or not d: break
    fund_all.extend(d)
    last = int(d[-1]["fundingTime"])
    if last <= cur or last >= e_ms: break
    cur = last + 1
fund_by_d = {}
for it in fund_all:
    ts = int(it["fundingTime"])
    d_str = ms_to_date(ts)
    if START <= d_str <= END:
        fund_by_d.setdefault(d_str, []).append({"ts": ts, "fr": float(it["fundingRate"])})
# assign interval + stats
fund_stats = {}
for d_str, entries in fund_by_d.items():
    frs = [e["fr"] for e in entries]
    tss = sorted(e["ts"] for e in entries)
    intervals = [(tss[i]-tss[i-1])/3600000 for i in range(1,len(tss))] if len(tss)>1 else []
    med_int = median(intervals) if intervals else None
    fund_stats[d_str] = {
        "fn": len(entries), "f_avg": round(sum(frs)/len(frs),8),
        "f_min": min(frs), "f_max": max(frs), "interval_h": med_int,
    }
print(f"  funding days: {len(fund_stats)}, all intervals ≈ 4h × 6/day (L-41 verified)")
# Show any anomalies
anom = [d for d,s in fund_stats.items() if s["interval_h"] and abs(s["interval_h"]-4) > 0.5]
if anom: print(f"  interval anomalies: {anom}")

# ── OI ─────────────────────────────────────────────────────────────────
hr("[OI hist last 30d, dedup]")
d = fetch_json("https://fapi.binance.com/futures/data/openInterestHist",
               {"symbol": TICKER, "period": "1d", "limit": 30})
time.sleep(0.3)
oi_by_d = {}
if isinstance(d, list):
    seen = set()
    for it in d:
        ts = int(it["timestamp"]); d_str = ms_to_date(ts)
        key = (d_str, str(ts))
        if key in seen: continue
        seen.add(key)
        oi_by_d[d_str] = {
            "oi_usd": float(it["sumOpenInterestValue"] or 0),
            "oi_token": float(it["sumOpenInterest"] or 0),
        }
print(f"  OI days: {len(oi_by_d)}, dedup unique")

# ── LSR: 4 endpoints (top pos, top acc, global acc, and taker via freshwatch) ──
hr("[LSR 4 endpoints last 30d]")
def fetch_lsr(ep):
    d = fetch_json(f"https://fapi.binance.com/futures/data/{ep}",
                   {"symbol": TICKER, "period":"1d", "limit": 30})
    time.sleep(0.3)
    by_d = {}
    if isinstance(d, list):
        for it in d:
            ts = int(it["timestamp"])
            by_d[ms_to_date(ts)] = float(it.get("longShortRatio",0) or 0)
    return by_d

lsr_top_pos = fetch_lsr("topLongShortPositionRatio")
lsr_top_acc = fetch_lsr("topLongShortAccountRatio")
lsr_glo     = fetch_lsr("globalLongShortAccountRatio")
print(f"  topPos: {len(lsr_top_pos)} days, sample last: {sorted(lsr_top_pos.items())[-1] if lsr_top_pos else 'none'}")
print(f"  topAcc: {len(lsr_top_acc)} days, sample last: {sorted(lsr_top_acc.items())[-1] if lsr_top_acc else 'none'}")
print(f"  glo:    {len(lsr_glo)} days, sample last: {sorted(lsr_glo.items())[-1] if lsr_glo else 'none'}")

# freshwatch (for taker_ratio too)
hr("[FRESHWATCH store TRIA]")
lsr_fw = {}
for fp in sorted(EXPORT.glob("freshwatch_daily_2026-*.csv")):
    with open(fp, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row.get("symbol","").upper() != TICKER: continue
            d_str = row.get("date","")[:10]
            pr = safe_float(row.get("lsr_pos_r"))
            if not d_str or not pr: continue
            lsr_fw[d_str] = {
                "pos_r": pr,
                "acc_r": safe_float(row.get("lsr_acc_r")),
                "gLSR": safe_float(row.get("lsr_global_r")),
                "taker_ratio": safe_float(row.get("taker_ratio")),
            }
print(f"  freshwatch TRIA rows: {len(lsr_fw)}, range={min(lsr_fw)}→{max(lsr_fw)}" if lsr_fw else "  none")

# ── Build per-day table ────────────────────────────────────────────────
hr(f"[BUILD per-day table {START} → {END}]")
from datetime import date as _date, timedelta
d0 = _date.fromisoformat(START); d1 = _date.fromisoformat(END)
days = []
cur = d0
while cur <= d1:
    days.append(cur.isoformat())
    cur += timedelta(days=1)

# taker scale check
taker_samples = [perp[d]["taker_buy_pct"] for d in days if d in perp and perp[d]["taker_buy_pct"] is not None]
if taker_samples:
    mn, mx = min(taker_samples), max(taker_samples)
    if mx <= 1.5 and mn <= 1.0:
        print(f"  TAKER SCALE: fraction [0,1] detected (max={mx:.4f}) — should ×100")
    elif mn > 1.0:
        print(f"  TAKER SCALE: percent [0,100] detected (range {mn:.2f}-{mx:.2f}) ✓")
    else:
        print(f"  TAKER SCALE: MIXED range={mn}-{mx} ← WARNING")

table = []
prev_oi = None; prev_c = None
for d in days:
    p = perp.get(d, {})
    f = fund_stats.get(d, {})
    oi = oi_by_d.get(d, {})
    # prefer freshwatch for LSR (has all 3 + taker); fallback to fapi
    fw = lsr_fw.get(d, {})
    lsr = {
        "pos_r": fw.get("pos_r") if fw else lsr_top_pos.get(d),
        "acc_r": fw.get("acc_r") if fw else lsr_top_acc.get(d),
        "gLSR":  fw.get("gLSR")  if fw else lsr_glo.get(d),
    }
    c = p.get("c")
    oi_usd = oi.get("oi_usd")
    ret_1d = round((c - prev_c)/prev_c*100, 4) if (c and prev_c) else None
    d_oi   = (oi_usd - prev_oi) if (oi_usd is not None and prev_oi is not None) else None
    prev_c = c if c else prev_c
    prev_oi = oi_usd if oi_usd is not None else prev_oi
    div_raw = None
    if lsr["pos_r"] and lsr["acc_r"] and lsr["acc_r"] != 0:
        div_raw = round(lsr["pos_r"]/lsr["acc_r"], 4)
    table.append({
        "date": d, "c": c, "ret_1d": ret_1d,
        "vol": p.get("vol_quote_usd"), "oi_usd": oi_usd, "d_oi": d_oi,
        "f_avg": f.get("f_avg"), "fn": f.get("fn"),
        "pos_r": lsr["pos_r"], "acc_r": lsr["acc_r"], "gLSR": lsr["gLSR"],
        "div_raw": div_raw,
        "taker": p.get("taker_buy_pct"),
    })

# div_avg3 = avg3(pos)/avg3(acc)
for i, r in enumerate(table):
    if i < 2: continue
    p3 = [table[j]["pos_r"] for j in range(i-2,i+1) if table[j]["pos_r"] is not None]
    a3 = [table[j]["acc_r"] for j in range(i-2,i+1) if table[j]["acc_r"] is not None]
    if len(p3)==3 and len(a3)==3:
        aa = sum(a3)/3
        r["div_avg3"] = round((sum(p3)/3)/aa, 4) if aa else None

print(f"\n  {'date':<12} {'c':>8} {'ret%':>6} {'vol_usd':>11} {'oi_usd':>10} {'Δoi':>8} "
      f"{'f_avg':>10} {'fn':>3} {'pos_r':>6} {'acc_r':>6} {'gLSR':>6} {'div':>6} {'div3':>6} {'tk%':>6}")
def fmt(v, w, prec=2): return f"{v:>{w}.{prec}f}" if v is not None else " "*w
for r in table:
    print(f"  {r['date']:<12} {fmt(r['c'],8,5)} {fmt(r['ret_1d'],6,2)} "
          f"{fmt(r['vol'],11,0)} {fmt(r['oi_usd'],10,0)} {fmt(r['d_oi'],8,0)} "
          f"{fmt(r['f_avg'],10,6)} {str(r['fn'] or ''):>3} "
          f"{fmt(r['pos_r'],6,3)} {fmt(r['acc_r'],6,3)} {fmt(r['gLSR'],6,3)} "
          f"{fmt(r['div_raw'],6,3)} {fmt(r.get('div_avg3'),6,3)} {fmt(r['taker'],6,2)}")

# ── HEDGE EPISODE detection ────────────────────────────────────────────
hr("[B2 HEDGE EPISODE detection (div_avg3 ≤ 0.5, gap-tol 2, break 3)]")
# scan div_avg3 series across full window
below_thresh = []
for r in table:
    if r.get("div_avg3") is not None:
        below_thresh.append((r["date"], r["div_avg3"], r["div_avg3"] <= 0.5))

# Print series to eyeball
print("\n  div_avg3 series:")
for d, v, ok in below_thresh:
    mark = "●" if ok else " "
    print(f"    {d}: {v:.4f} {mark}")

# Find episode: consecutive True with gap-tolerance 2, break=3
episodes = []
cur_ep = None; gap = 0
for d, v, ok in below_thresh:
    if ok:
        if cur_ep is None:
            cur_ep = {"start": d, "end": d, "min_v": v, "min_d": d, "vals": [(d,v)]}
        else:
            cur_ep["end"] = d
            cur_ep["vals"].append((d,v))
            if v < cur_ep["min_v"]:
                cur_ep["min_v"] = v; cur_ep["min_d"] = d
        gap = 0
    else:
        if cur_ep is not None:
            gap += 1
            cur_ep["vals"].append((d,v))
            if gap > 2:  # break after 3 above-thresh days (allow gap-tol 2)
                episodes.append(cur_ep)
                cur_ep = None; gap = 0
if cur_ep:
    episodes.append(cur_ep)

print(f"\n  Episodes detected: {len(episodes)}")
for i, ep in enumerate(episodes):
    struct_n = sum(1 for _,v in ep["vals"] if v <= 0.5)
    print(f"  Episode #{i+1}: start={ep['start']} end={ep['end']} "
          f"struct_n={struct_n} · min div_avg3={ep['min_v']} @ {ep['min_d']}")
    # hedge_start_px = close at start
    start_row = next((r for r in table if r["date"] == ep["start"]), None)
    if start_row:
        print(f"    hedge_start_px = {start_row['c']}")
    # find when div starts rising (nới): find first date after min where div rises consistently
    vals_after_min = [(d,v) for d,v in ep["vals"] if d > ep["min_d"] and v is not None]
    if vals_after_min:
        # first rise from min: first v > min_v + 0.05
        for d,v in vals_after_min:
            if v > ep["min_v"] + 0.05:
                print(f"    div bắt đầu nới from {ep['min_v']:.4f}→{v:.4f} tại {d}")
                break

# Latest px_dist%
last_row = table[-1] if table else None
if last_row and last_row["c"] and episodes:
    last_ep = episodes[-1]
    start_row = next((r for r in table if r["date"]==last_ep["start"]), None)
    if start_row and start_row["c"]:
        px_dist_pct = round((last_row["c"] - start_row["c"])/start_row["c"]*100, 2)
        print(f"\n  px_dist% từ hedge_start={start_row['c']} → today={last_row['c']}: {px_dist_pct}%")

# ── INTRADAY 19/08 ─────────────────────────────────────────────────────
hr("[INTRADAY 19/08 snapshot]")
now = datetime.now(timezone.utc)
print(f"  snapshot at: {now.strftime('%Y-%m-%d %H:%M:%S UTC')}")
d = fetch_json("https://fapi.binance.com/fapi/v1/ticker/24hr", {"symbol": TICKER})
time.sleep(0.3)
if isinstance(d, dict) and "lastPrice" in d:
    px_now = float(d["lastPrice"])
    print(f"  24h ticker: last={px_now} open24h={d['openPrice']} chg={d['priceChangePercent']}% "
          f"vol_quote={d['quoteVolume']}")
d2 = fetch_json("https://fapi.binance.com/fapi/v1/openInterest", {"symbol": TICKER})
time.sleep(0.3)
if isinstance(d2, dict) and "openInterest" in d2:
    oi_now_tok = float(d2["openInterest"])
    oi_now_usd = oi_now_tok * px_now if 'px_now' in dir() else None
    aug18_oi = oi_by_d.get("2026-08-18", {}).get("oi_usd")
    print(f"  OI now: token={oi_now_tok:.0f} usd={oi_now_usd:.0f}")
    if aug18_oi:
        print(f"  vs Aug18 close: usd_delta={(oi_now_usd - aug18_oi):+.0f} "
              f"({((oi_now_usd - aug18_oi)/aug18_oi*100):+.2f}%)")
d3 = fetch_json("https://fapi.binance.com/fapi/v1/fundingRate",
                {"symbol": TICKER, "limit": 3})
time.sleep(0.3)
if isinstance(d3, list):
    print(f"  Recent funding:")
    for it in d3:
        ts = int(it["fundingTime"])
        print(f"    {ms_to_date(ts)} @ {datetime.fromtimestamp(ts/1000,tz=timezone.utc).strftime('%H:%M UTC')}: "
              f"fr={it['fundingRate']}")

# ── B4: spot verify (local first, VPS in follow-up if geo-block) ────────
hr("[B4 SPOT api/v3 verify (best-effort local; VPS follow-up if fail)]")
d = fetch_json("https://api.binance.com/api/v3/exchangeInfo", {})
time.sleep(0.3)
if isinstance(d, dict) and "symbols" in d:
    matches = [s for s in d["symbols"] if s.get("baseAsset")=="TRIA" or "TRIA" in s.get("symbol","")]
    print(f"  TRIA matches: {len(matches)}")
    for s in matches[:5]:
        print(f"    {s.get('symbol')} base={s.get('baseAsset')} status={s.get('status')}")
    if not matches:
        print("  → NO spot api/v3 pair for TRIA")
elif isinstance(d, dict) and "_error" in d:
    print(f"  Local blocked: {d['_error']} — need VPS")

# Alpha vol 5d from Alpha bapi
if tria_alpha:
    aid = tria_alpha.get("alphaId")
    print(f"\n  Alpha klines 5d for {aid}:")
    d = fetch_json("https://www.binance.com/bapi/defi/v1/public/alpha-trade/klines",
                   {"symbol": f"{aid}USDT", "interval": "1d", "limit": 8})
    time.sleep(0.3)
    if isinstance(d, dict) and "data" in d:
        for r in (d.get("data") or [])[-6:]:
            ts = int(r[0])
            dstr = ms_to_date(ts)
            print(f"    {dstr}: c={r[4]} vol_usd={r[7]}")

# ── B6: watchlist_log + phase_tag CSV check ───────────────────────────
hr("[B6 watchlist_log + phase_tag_daily CSV check]")
# local
for pat in ["watchlist*log*", "watchlist*.csv", "phase_tag*"]:
    matches = list(ROOT.rglob(pat))
    print(f"  local rglob '{pat}': {len(matches)} matches")
    for m in matches[:5]:
        print(f"    {m}")

print("\n[DONE probe]")
