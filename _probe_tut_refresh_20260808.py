"""TUT refresh 08/08 (VN) / 07/08 (UTC): export 05-06/08 + fapi 07/08 intraday + spot + DEX.
Date note: 09:04 VN = 02:04 UTC — intraday data = 07/08 UTC (nến 08/08 UTC chưa mở).
"""
import sys, io, json, urllib.request, csv, time
from pathlib import Path
from datetime import datetime, timezone, timedelta

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

SYM = "TUTUSDT"
BASE_F = "https://fapi.binance.com"
BASE_S = "https://api.binance.com"
EXPORT_DIR = Path(r"D:\Check onchain fresh wallets\data\export")
now_utc = datetime.now(tz=timezone.utc)
now_str = now_utc.strftime("%Y-%m-%d %H:%M UTC")
today_utc = now_utc.strftime("%Y-%m-%d")          # 2026-08-07
intraday_date = today_utc                           # ngày đang chạy UTC

def get(url, label=""):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read())
    except Exception as e:
        return {"ERROR": str(e)[:200]}

def ts_date(ms): return datetime.fromtimestamp(ms/1000, tz=timezone.utc).strftime("%Y-%m-%d")
def ts_hm(ms):   return datetime.fromtimestamp(ms/1000, tz=timezone.utc).strftime("%H:%M")
def fv(v,d=5):   return f"{v:.{d}f}" if v is not None else "—"
def fi(v):        return f"{v:,.0f}" if v is not None else "—"

print("=" * 72)
print(f"TUT REFRESH — chạy {now_str}")
print(f"  intraday_date (UTC) = {intraday_date}")
print(f"  Hôm nay VN = 08/08; UTC nến 08/08 mở lúc 00:00 UTC (chưa tới)")
print("=" * 72)

# ══════════════════════════════════════════════════════════════════════════════
# D1a. EXPORT CSV — canonical 00:00 UTC snapshot
# ══════════════════════════════════════════════════════════════════════════════
print("\n══ D1a. EXPORT CSV (canonical — bot snapshot 00:00 UTC) ══")
export_rows = {}
for fname in ["freshwatch_daily_2026-07.csv", "freshwatch_daily_2026-08.csv"]:
    fp = EXPORT_DIR / fname
    if not fp.exists():
        print(f"  MISSING FILE: {fname}")
        continue
    with open(fp, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["symbol"] == SYM:
                export_rows[row["date"]] = row
print(f"  Export TUT: {len(export_rows)} rows | range: {min(export_rows)} → {max(export_rows)}")

def show_export_row(d):
    if d not in export_rows:
        print(f"  {d}: MISSING từ export (cron chưa chạy hoặc data_ok=False)")
        return
    r = export_rows[d]
    fn_val = int(r.get("funding_n") or 0)
    fn_ok = "✓ OK" if fn_val >= 6 else f"⚠ SUSPECT fn={fn_val}"
    taker = float(r.get("taker_buy_pct") or 0)
    if taker <= 1: taker *= 100
    print(f"  {d}: px={float(r.get('px_avg','0')):.5f}  vol={float(r.get('vol_quote','0')):>14,.0f}  "
          f"taker={taker:.2f}%  f_avg={float(r.get('funding_avg','0') or 0):.6f} {fn_ok}  "
          f"OI={float(r.get('oi_usd','0') or 0):>12,.0f}  "
          f"pos_r={float(r.get('lsr_pos_r','0') or 0):.4f}  "
          f"acc_r={float(r.get('lsr_acc_r','0') or 0):.4f}  "
          f"gLSR={float(r.get('lsr_global_r','0') or 0):.4f}  "
          f"data_ok={r.get('data_ok')}")

print()
print("  [Ngày đã có export — verify fn từng dòng]")
for d in sorted(export_rows):
    if d >= "2026-08-04":
        show_export_row(d)

print()
print("  [07/08 từ export:]")
show_export_row("2026-08-07")

# ══════════════════════════════════════════════════════════════════════════════
# D1b. FAPI 07/08 intraday (UTC) — vì 08/08 UTC chưa tới
# ══════════════════════════════════════════════════════════════════════════════
print("\n══ D1b. FAPI 07/08 INTRADAY (UTC) — nến 1h từ 00:00 UTC ══")

start_ts_today = int(datetime(int(intraday_date[:4]), int(intraday_date[5:7]),
                               int(intraday_date[8:10]), 0, 0, 0, tzinfo=timezone.utc).timestamp()*1000)
kl1h = get(f"{BASE_F}/fapi/v1/klines?symbol={SYM}&interval=1h&startTime={start_ts_today}&limit=48")

day_vol = 0; day_taker_q = 0; px_open_day = None; px_high = 0; px_low = 999; px_last = None
if isinstance(kl1h, list):
    print(f"  {'H:MM':>5} {'open':>10} {'high':>10} {'low':>10} {'close':>10} {'vol$':>13} {'taker%':>8} {'note'}")
    print(f"  {'-'*5} {'-'*10} {'-'*10} {'-'*10} {'-'*10} {'-'*13} {'-'*8}")
    for k in kl1h:
        if ts_date(k[0]) != intraday_date: continue
        hm  = ts_hm(k[0])
        o,h,lo,c = float(k[1]),float(k[2]),float(k[3]),float(k[4])
        qv  = float(k[7]); tbq = float(k[10])
        tp  = tbq/qv*100 if qv > 0 else 0
        is_open = (k[6] > now_utc.timestamp()*1000)  # closeTime > now = nến chưa đóng
        note = "← open" if is_open else ""
        day_vol += qv; day_taker_q += tbq
        if px_open_day is None: px_open_day = o
        if h > px_high: px_high = h
        if lo < px_low: px_low = lo
        px_last = c
        print(f"  {hm:>5} {o:>10.5f} {h:>10.5f} {lo:>10.5f} {c:>10.5f} {qv:>13,.0f} {tp:>8.1f}% {note}")

print(f"\n  [{intraday_date} cumulative — INTRADAY, boundary L-38: ≠ daily 00:00]")
if px_open_day:
    ret_day = (px_last/px_open_day - 1)*100 if px_last else 0
    print(f"    px_open      = {px_open_day:.5f}")
    print(f"    px_high      = {px_high:.5f}")
    print(f"    px_low       = {px_low:.5f}")
    print(f"    px_last      = {px_last:.5f}  ({ret_day:+.2f}% từ 00:00 UTC)")
    print(f"    vol_perp_day = ${day_vol:,.0f}")
    taker_day = day_taker_q/day_vol*100 if day_vol > 0 else 0
    print(f"    taker_day    = {taker_day:.2f}%")
else:
    print(f"    Không có nến nào cho {intraday_date} — kiểm tra startTime")

time.sleep(0.3)

# OI realtime
oi_rt = get(f"{BASE_F}/fapi/v1/openInterest?symbol={SYM}")
print(f"\n  [OI realtime snapshot]")
if "openInterest" in oi_rt and px_last:
    oi_tokens = float(oi_rt["openInterest"])
    oi_usd = oi_tokens * px_last
    print(f"    OI tokens = {oi_tokens:,.0f}")
    print(f"    OI USD    = ${oi_usd:,.0f}  (×px_last={px_last:.5f})")
elif "openInterest" in oi_rt:
    print(f"    OI tokens = {float(oi_rt['openInterest']):,.0f}")
else:
    print(f"    {oi_rt}")

time.sleep(0.3)

# premiumIndex
pm = get(f"{BASE_F}/fapi/v1/premiumIndex?symbol={SYM}")
print(f"\n  [premiumIndex / funding]")
if isinstance(pm, dict) and "markPrice" in pm:
    mark = float(pm["markPrice"])
    idx  = float(pm["indexPrice"])
    last_fr = float(pm["lastFundingRate"])
    next_ft = datetime.fromtimestamp(pm["nextFundingTime"]//1000, tz=timezone.utc)
    mins_to_next = (next_ft - now_utc).seconds // 60
    pin = "PIN [4e-5,6e-5]" if 4e-5 <= last_fr <= 6e-5 else ("NEG!" if last_fr < 0 else "FLOAT")
    print(f"    markPrice       = {mark:.6f}")
    print(f"    indexPrice      = {idx:.6f}")
    print(f"    premium (mark-idx)/idx = {(mark-idx)/idx*100:+.4f}%")
    print(f"    lastFundingRate = {last_fr:.6f}  → {pin}")
    print(f"    nextFundingTime = {next_ft.strftime('%H:%M UTC')}  (còn {mins_to_next} phút)")
else:
    print(f"    {pm}")

time.sleep(0.3)

# Funding đã settle trong ngày (07/08 và 08/08 UTC window)
fr_list = get(f"{BASE_F}/fapi/v1/fundingRate?symbol={SYM}&limit=30")
print(f"\n  [Funding đã settle — 4h/kỳ, 12 kỳ gần nhất]")
if isinstance(fr_list, list):
    recent = fr_list[-12:]
    for rec in recent:
        t  = datetime.fromtimestamp(rec["fundingTime"]//1000, tz=timezone.utc)
        fv_val = float(rec["fundingRate"])
        flag = "✓PIN" if 4e-5 <= fv_val <= 6e-5 else ("⚠NEG" if fv_val < 0 else "FLOAT")
        print(f"    {t.strftime('%m-%d %H:%M UTC')}: {fv_val:.6f}  {flag}")
else:
    print(f"    {fr_list}")

time.sleep(0.3)

# LSR snapshots
print(f"\n  [LSR snapshots — 5m period, INTRADAY — L-38: ≠ daily 00:00]")
def fetch_lsr(ep, label):
    d = get(f"{BASE_F}/futures/data/{ep}?symbol={SYM}&period=5m&limit=3")
    if isinstance(d, list) and d:
        latest = d[-1]
        t = datetime.fromtimestamp(latest["timestamp"]//1000, tz=timezone.utc).strftime("%m-%d %H:%M UTC")
        val = float(latest["longShortRatio"])
        print(f"    {label:<32}: {val:.4f}  [{t}]")
        return val
    print(f"    {label:<32}: ERROR {d}")
    return None

pr_snap = fetch_lsr("topLongShortPositionRatio", "pos_r (top-trader position)")
time.sleep(0.2)
ar_snap = fetch_lsr("topLongShortAccountRatio",  "acc_r (top-trader account)")
time.sleep(0.2)
gl_snap = fetch_lsr("globalLongShortAccountRatio","gLSR (global)")

# ══════════════════════════════════════════════════════════════════════════════
# D2. SPOT — Binance TUTUSDT daily + intraday
# ══════════════════════════════════════════════════════════════════════════════
print("\n══ D2a. SPOT — Binance TUTUSDT ══")
sk = get(f"{BASE_S}/api/v3/klines?symbol={SYM}&interval=1d&limit=10")
if isinstance(sk, list):
    print(f"  {'date':<12} {'vol_spot$':>14} {'taker_spot%':>12} {'close':>10}  [venue=binance_spot, k[10]/k[7]]")
    print(f"  {'-'*12} {'-'*14} {'-'*12} {'-'*10}")
    for k in sk:
        d   = ts_date(k[0])
        if d > intraday_date: continue
        qv  = float(k[7]); tbq = float(k[10]); cl = float(k[4])
        tp  = tbq/qv*100 if qv > 0 else 0
        print(f"  {d:<12} {qv:>14,.0f} {tp:>12.2f}%  {cl:>10.5f}")
else:
    print(f"  ERROR: {sk}")

time.sleep(0.3)

# Spot intraday 07/08
sk1h = get(f"{BASE_S}/api/v3/klines?symbol={SYM}&interval=1h&startTime={start_ts_today}&limit=24")
day_spot_vol = 0; day_spot_tbq = 0
if isinstance(sk1h, list):
    for k in sk1h:
        if ts_date(k[0]) != intraday_date: continue
        day_spot_vol += float(k[7]); day_spot_tbq += float(k[10])
tsp_intra = day_spot_tbq/day_spot_vol*100 if day_spot_vol > 0 else 0
print(f"\n  [{intraday_date} spot intraday cumulative]")
print(f"    vol_spot     = ${day_spot_vol:,.0f}")
print(f"    taker_spot   = {tsp_intra:.2f}%  [k[10]/k[7], venue=binance_spot]")
if day_vol > 0:
    ratio = day_spot_vol/day_vol
    guard = "✓ CLEAR (<3×)" if ratio < 3 else "⚠ SUSPECT (≥3×)"
    print(f"    L-29 guard   = spot/perp = {ratio:.3f}×  {guard}")

time.sleep(0.3)

# ══════════════════════════════════════════════════════════════════════════════
# D2b. DEX BSC — GeckoTerminal TUT pools
# ══════════════════════════════════════════════════════════════════════════════
print("\n══ D2b. DEX BSC — GeckoTerminal ══")

# Search TUT on BSC
gt_search = get("https://api.geckoterminal.com/api/v2/networks/bsc/tokens/search?query=TUT")
tut_pool_id = None
tut_addr = None
if "data" in gt_search:
    for tok in gt_search.get("data", []):
        attr = tok.get("attributes", {})
        sym  = attr.get("symbol","").upper()
        name = attr.get("name","")
        if sym == "TUT" or "TUT" in name.upper():
            addr = attr.get("address","")
            pools_rel = tok.get("relationships",{}).get("top_pools",{}).get("data",[])
            if pools_rel:
                tut_pool_id = pools_rel[0].get("id","")
                tut_addr = addr
                print(f"  Found: {sym} ({name}) | addr: {addr[:20]}...")
                print(f"  Top pool id: {tut_pool_id}")
                break
    if not tut_pool_id:
        print(f"  No TUT pool found in search results:")
        for tok in gt_search.get("data",[])[:3]:
            a = tok.get("attributes",{})
            print(f"    {a.get('symbol')} — {a.get('name')} — {a.get('address','')[:20]}")
else:
    print(f"  Search error: {str(gt_search)[:200]}")

if tut_pool_id:
    time.sleep(0.5)
    net = tut_pool_id.split("_")[0]
    pool_addr = tut_pool_id.split("_",1)[1] if "_" in tut_pool_id else tut_pool_id
    pool_data = get(f"https://api.geckoterminal.com/api/v2/networks/{net}/pools/{pool_addr}")
    if "data" in pool_data:
        attr = pool_data["data"].get("attributes",{})
        print(f"\n  Pool: {attr.get('name','?')}")
        print(f"  price_usd:   {attr.get('base_token_price_usd','?')}")
        vol = attr.get("volume_usd",{})
        print(f"  vol_24h:     ${float(vol.get('h24','0') or 0):,.0f}")
        print(f"  vol_6h:      ${float(vol.get('h6','0') or 0):,.0f}")
        print(f"  vol_1h:      ${float(vol.get('h1','0') or 0):,.0f}")
        pc = attr.get("price_change_percentage",{})
        print(f"  px_chg_24h:  {pc.get('h24','?')}%")
        txns = attr.get("transactions",{})
        h24 = txns.get("h24",{}); h1 = txns.get("h1",{})
        print(f"  txns 24h:    buys={h24.get('buys','?')} sells={h24.get('sells','?')} "
              f"buy_vol=${float(h24.get('buy_volume_usd','0') or 0):,.0f} sell_vol=${float(h24.get('sell_volume_usd','0') or 0):,.0f}")
        print(f"  txns 1h:     buys={h1.get('buys','?')} sells={h1.get('sells','?')}")
        if h24.get('buy_volume_usd') and h24.get('sell_volume_usd'):
            buy_v = float(h24['buy_volume_usd'] or 0)
            sell_v = float(h24['sell_volume_usd'] or 0)
            tot = buy_v + sell_v
            if tot > 0:
                print(f"  buy_pct 24h: {buy_v/tot*100:.1f}%  sell_pct: {sell_v/tot*100:.1f}%")
    else:
        print(f"  Pool data error: {str(pool_data)[:200]}")
    time.sleep(0.5)
    # OHLCV daily
    ohlcv = get(f"https://api.geckoterminal.com/api/v2/networks/{net}/pools/{pool_addr}/ohlcv/day?limit=7")
    if "data" in ohlcv:
        candles = ohlcv["data"].get("attributes",{}).get("ohlcv_list",[])
        print(f"\n  GeckoTerminal daily OHLCV (7 ngày gần nhất):")
        print(f"  {'date':<12} {'open':>10} {'high':>10} {'low':>10} {'close':>10} {'vol_usd':>14}")
        for c in candles:
            dt = datetime.fromtimestamp(c[0], tz=timezone.utc).strftime("%Y-%m-%d")
            print(f"  {dt:<12} {c[1]:>10.5f} {c[2]:>10.5f} {c[3]:>10.5f} {c[4]:>10.5f} {c[5]:>14,.0f}")
    else:
        print(f"  OHLCV error: {str(ohlcv)[:200]}")

# ══════════════════════════════════════════════════════════════════════════════
# SUMMARY BLOCK cho D3 analysis
# ══════════════════════════════════════════════════════════════════════════════
print("\n══ SUMMARY BLOCK (cho D3 chấm chốt) ══")
print(f"  Thời điểm đọc: {now_str}")
print(f"  B = 1.922M (OI floor 09/07, canonical)")
print()

# Latest daily (06/08) from export
if "2026-08-06" in export_rows:
    r6 = export_rows["2026-08-06"]
    taker6 = float(r6.get("taker_buy_pct") or 0)
    if taker6 <= 1: taker6 *= 100
    oi6 = float(r6.get("oi_usd") or 0)
    pr6 = float(r6.get("lsr_pos_r") or 0)
    gl6 = float(r6.get("lsr_global_r") or 0)
    fa6 = float(r6.get("funding_avg") or 0)
    print(f"  [06/08 daily — export canonical]")
    print(f"    px       = {float(r6.get('px_avg','0')):.5f}")
    print(f"    OI       = ${oi6:,.0f}  ΔOI/B = {(oi6-1922000)/1922000:.2f}×")
    print(f"    pos_r    = {pr6:.4f}")
    print(f"    gLSR     = {gl6:.4f}")
    print(f"    f_avg    = {fa6:.6f}  {'PIN' if 4e-5<=fa6<=6e-5 else 'FLOAT'}")
    print(f"    taker    = {taker6:.2f}%  (perp)")

if "2026-08-05" in export_rows:
    r5 = export_rows["2026-08-05"]
    oi5 = float(r5.get("oi_usd") or 0)
    pr5 = float(r5.get("lsr_pos_r") or 0)
    gl5 = float(r5.get("lsr_global_r") or 0)
    print(f"\n  [05/08 daily — export canonical]")
    print(f"    px       = {float(r5.get('px_avg','0')):.5f}")
    print(f"    OI       = ${oi5:,.0f}  ΔOI/B = {(oi5-1922000)/1922000:.2f}×")
    print(f"    pos_r    = {pr5:.4f}")
    print(f"    gLSR     = {gl5:.4f}")

if px_last:
    print(f"\n  [07/08 intraday — {now_str}]")
    oi_intra_usd = float(oi_rt.get("openInterest",0))*px_last if "openInterest" in oi_rt else 0
    print(f"    px_last  = {px_last:.5f}  H={px_high:.5f} L={px_low:.5f}")
    print(f"    OI intra = ${oi_intra_usd:,.0f}  (tokens×px_last, L-38 boundary)")
    if pr_snap: print(f"    pos_r    = {pr_snap:.4f}  (5m intraday snapshot)")
    if gl_snap: print(f"    gLSR     = {gl_snap:.4f}  (5m intraday snapshot)")

print("\n[DONE]")
