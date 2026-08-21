"""_task_r_nhip1_fetch_20260821.py — R Nhịp 1 fetch pipeline (READ-ONLY fetch).
Kéo dữ liệu perp/funding/OI/LSR cho 5 token BANK/TUT/AKE/BTW/CYS trước khi write.
Windows:
- BANK: min→2026-08-20 (từ current min 06-09)
- TUT: 2026-05-01→2026-08-20 (full v1 range)
- AKE: 2026-05-01→2026-08-20 (COLD_START, klines về 05-01)
- BTW: 2026-04-21→2026-08-20 (R3 backfill early + refresh late)
- CYS: 2026-06-01→2026-08-20 (từ freshwatch first_nn Jun01)

Backup 4 file trước.
"""
import sys, io, json, urllib.request, time, csv, shutil
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
from datetime import datetime, timezone, date as _date, timedelta

ROOT = Path(r"D:\Data back test\whale_data")
SCRATCH = ROOT / "scratch"
CASES = ROOT / "docs" / "case_files"

END = "2026-08-20"

TOKENS = {
    "BANK": {"ticker":"BANKUSDT", "start":"2026-06-09"},   # extend to D-1
    "TUT":  {"ticker":"TUTUSDT",  "start":"2026-05-01"},
    "AKE":  {"ticker":"AKEUSDT",  "start":"2026-05-01"},   # cold-start
    "BTW":  {"ticker":"BTWUSDT",  "start":"2026-04-21"},   # backfill early
    "CYS":  {"ticker":"CYSUSDT",  "start":"2026-06-01"},   # from first_nn
}

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

# ── Backup 4 file ──
print("=== BACKUP 4 file (L-37) ===")
for sym in ["BANK","TUT","BTW","CYS"]:
    src = CASES / f"CASE_{sym}.xlsx"
    dst = SCRATCH / f"CASE_{sym}_bak_pre_r1_20260821.xlsx"
    if src.exists():
        shutil.copy2(src, dst)
        print(f"  {sym}: {dst.name} ({dst.stat().st_size} B)")
    else:
        print(f"  {sym}: SOURCE MISSING")

# ── Verify AKE on fapi ──
print("\n=== VERIFY AKE fapi (for R2 cold-start) ===")
d = fetch_json("https://fapi.binance.com/fapi/v1/exchangeInfo")
time.sleep(0.3)
if isinstance(d, dict):
    ake = next((s for s in d.get("symbols",[]) if s.get("symbol")=="AKEUSDT"), None)
    if ake:
        onboard = ms_to_date(ake.get("onboardDate"))
        print(f"  AKEUSDT: TRADING · onboard={onboard}")
    else:
        print(f"  AKEUSDT: NOT FOUND on fapi — R2 CHƯA CHẠY (không có perp)")
        # Handle gracefully
        TOKENS.pop("AKE", None)

# ── Fetch pipeline: klines + funding + OI + LSR for each token ──
def fetch_all(sym, ticker, start, end):
    print(f"\n--- {sym} ({ticker}) {start}→{end} ---")
    s_ms = to_ms(start); e_ms = to_ms(end) + 86400000 - 1
    result = {}

    # KLINES 1d
    all_klines = []
    cur = s_ms
    while cur <= e_ms:
        d = fetch_json("https://fapi.binance.com/fapi/v1/klines",
                       {"symbol":ticker,"interval":"1d","startTime":cur,"endTime":e_ms,"limit":1000})
        time.sleep(0.3)
        if not isinstance(d, list) or not d: break
        all_klines.extend(d)
        last = int(d[-1][0])
        if last <= cur or last >= e_ms: break
        cur = last + 86400000
    result["klines"] = {}
    for k in all_klines:
        d_str = ms_to_date(int(k[0]))
        if d_str < start or d_str > end: continue
        result["klines"][d_str] = {
            "o": float(k[1]), "h": float(k[2]), "l": float(k[3]), "c": float(k[4]),
            "vol_quote_usd": round(float(k[7]),2),
            "taker_buy_pct": round(float(k[10])/float(k[7])*100, 4) if float(k[7])>0 else None,
        }
    print(f"  klines: {len(result['klines'])} days")

    # FUNDING
    fund_all = []; cur = s_ms
    while cur <= e_ms:
        d = fetch_json("https://fapi.binance.com/fapi/v1/fundingRate",
                       {"symbol":ticker,"startTime":cur,"endTime":e_ms,"limit":1000})
        time.sleep(0.3)
        if not isinstance(d, list) or not d: break
        fund_all.extend(d)
        last = int(d[-1]["fundingTime"])
        if last <= cur or last >= e_ms: break
        cur = last + 1
    result["fund_by_d"] = {}
    for it in fund_all:
        ts = int(it["fundingTime"]); d_str = ms_to_date(ts)
        if start <= d_str <= end:
            result["fund_by_d"].setdefault(d_str, []).append(float(it["fundingRate"]))
    print(f"  funding: {len(result['fund_by_d'])} days, {sum(len(v) for v in result['fund_by_d'].values())} entries")

    # OI (30d limit — chỉ trả về 30 điểm gần nhất từ khi call)
    d = fetch_json("https://fapi.binance.com/futures/data/openInterestHist",
                   {"symbol":ticker,"period":"1d","limit":30})
    time.sleep(0.3)
    result["oi"] = {}
    if isinstance(d, list):
        for it in d:
            ts = int(it["timestamp"]); d_str = ms_to_date(ts)
            if start <= d_str <= end:
                result["oi"][d_str] = {
                    "oi_usd": float(it["sumOpenInterestValue"] or 0),
                    "oi_token": float(it["sumOpenInterest"] or 0),
                }
    print(f"  OI: {len(result['oi'])} days (30d limit)")

    # LSR — freshwatch first, fapi fallback
    EXPORT = ROOT / "data" / "export"
    result["lsr"] = {}
    for fp in sorted(EXPORT.glob("freshwatch_daily_2026-*.csv")):
        try:
            with open(fp, encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    if row.get("symbol","").upper() != ticker: continue
                    d_str = row.get("date","")[:10]
                    try: pr = float(row.get("lsr_pos_r") or 0)
                    except: pr = 0
                    if not d_str or not pr: continue
                    if start <= d_str <= end:
                        result["lsr"][d_str] = {
                            "pos_r": pr,
                            "acc_r": float(row.get("lsr_acc_r") or 0) or None,
                            "gLSR": float(row.get("lsr_global_r") or 0) or None,
                            "taker_lsr": float(row.get("taker_ratio") or 0) or None,
                            "src": "freshwatch",
                        }
        except: pass
    # fapi fallback
    def fetch_ep(ep):
        d = fetch_json(f"https://fapi.binance.com/futures/data/{ep}",
                       {"symbol":ticker,"period":"1d","limit":30})
        time.sleep(0.3)
        by_d = {}
        for it in d if isinstance(d, list) else []:
            ts = int(it["timestamp"])
            by_d[ms_to_date(ts)] = float(it.get("longShortRatio",0) or 0)
        return by_d
    lsr_pos = fetch_ep("topLongShortPositionRatio")
    lsr_acc = fetch_ep("topLongShortAccountRatio")
    lsr_glo = fetch_ep("globalLongShortAccountRatio")
    for d in set(lsr_pos.keys()) | set(lsr_acc.keys()) | set(lsr_glo.keys()):
        if start <= d <= end and d not in result["lsr"]:
            if lsr_pos.get(d) or lsr_acc.get(d) or lsr_glo.get(d):
                result["lsr"][d] = {
                    "pos_r": lsr_pos.get(d),
                    "acc_r": lsr_acc.get(d),
                    "gLSR": lsr_glo.get(d),
                    "taker_lsr": None,
                    "src": "fapi",
                }
    print(f"  LSR: {len(result['lsr'])} days total (freshwatch + fapi fallback)")

    return result

# Fetch all
print("\n" + "="*70)
print("FETCH ALL TOKENS")
print("="*70)
all_data = {}
for sym, meta in TOKENS.items():
    all_data[sym] = fetch_all(sym, meta["ticker"], meta["start"], END)

# Save to scratch for downstream write task
import pickle
pkl_path = SCRATCH / "r_nhip1_fetch_20260821.pkl"
with open(pkl_path, "wb") as f:
    pickle.dump(all_data, f)
print(f"\nSaved fetch dict: {pkl_path} ({pkl_path.stat().st_size} B)")

# Quick summary per token
print("\n" + "="*70)
print("SUMMARY per token")
print("="*70)
for sym, d in all_data.items():
    print(f"  {sym}: klines={len(d['klines'])} · funding={len(d['fund_by_d'])} · OI={len(d['oi'])} · LSR={len(d['lsr'])}")
