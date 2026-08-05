# -*- coding: utf-8 -*-
"""BANK vong-2 watch: gLSR/pos_r/funding 01-05/08 + today candle detail + 3 dieu kien."""
import urllib.request, json, ssl, time
from datetime import datetime, timezone

OUT = "scratch/bank_vong2_20260805.txt"
lines = []

def p(s=""):
    print(str(s).encode('ascii', 'replace').decode('ascii'))
    lines.append(str(s))

def fetch(url, timeout=15, retries=3):
    ctx = ssl.create_default_context()
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
                return json.loads(r.read())
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(2 + attempt * 2)
            else:
                return {"_error": str(e)}

def sf(x, d=None):
    try: return float(x)
    except: return d

TS = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
p("=" * 70)
p(f"BANK VONG-2 WATCH - {TS}")
p("=" * 70)

# ─── READ CASE_BANK DAILY (last 10 rows) ──────────────────────────
p("\n### [A] CASE_BANK DAILY: 01-05/08 freshwatch cols")
try:
    import openpyxl
    wb = openpyxl.load_workbook("docs/case_files/CASE_BANK.xlsx", read_only=True)

    # Get DAILY sheet
    ws = wb["DAILY"]
    rows_data = []
    for row in ws.iter_rows(min_row=3, values_only=True):
        if row[0]:
            rows_data.append(row)

    p(f"  Total DAILY rows: {len(rows_data)}")

    # Col indices (0-based): date=0, px=1, vol=3, taker=4, f_avg=5, f_n=8,
    # lsr_pos_r=14, lsr_acc_r=15, lsr_global_r=16, oi=11, data_bad=25
    header = [
        "date", "px_avg", "ret_1d", "vol_perp", "taker", "f_avg", "f_min", "f_max", "f_n",
        "f_regime", "pin_streak", "oi_usd", "oi_vs_med14", "oi_cycle_pos",
        "pos_r", "acc_r", "gLSR",
    ]

    p(f"\n  {'date':<12} {'px':>8} {'vol_perp':>10} {'taker':>7} {'f_avg':>9} {'f_n':>4} {'pos_r':>6} {'acc_r':>6} {'gLSR':>6} {'oi':>10}")
    p("  " + "-"*85)

    for row in rows_data:
        d_str = str(row[0])[:10] if row[0] else ""
        if d_str < "2026-07-28": continue  # show last week+
        px = sf(row[1])
        vol = sf(row[3])
        taker = sf(row[4])
        f_avg = sf(row[5])
        f_n = row[8]
        pos_r = sf(row[14])
        acc_r = sf(row[15])
        glsr = sf(row[16])
        oi = sf(row[11])
        data_bad = row[25]

        flag = " [!]" if data_bad else ""
        px_s = f"{px:.4f}" if px else "N/A"
        vol_s = f"${vol/1e6:.0f}M" if vol else "N/A"
        tak_s = f"{taker:.1%}" if taker else "N/A"
        fa_s = f"{f_avg:.5f}" if f_avg else "N/A"
        pr_s = f"{pos_r:.3f}" if pos_r else "N/A"
        ar_s = f"{acc_r:.3f}" if acc_r else "N/A"
        gl_s = f"{glsr:.3f}" if glsr else "N/A"
        oi_s = f"${oi/1e6:.1f}M" if oi else "N/A"
        p(f"  {d_str:<12} {px_s:>8} {vol_s:>10} {tak_s:>7} {fa_s:>9} {str(f_n):>4} {pr_s:>6} {ar_s:>6} {gl_s:>6} {oi_s:>10}{flag}")

    # Extract 01-05/08 rows specifically
    aug_rows = [r for r in rows_data if str(r[0])[:10] >= "2026-08-01"]
    p(f"\n  Aug rows in CASE_BANK DAILY: {len(aug_rows)}")

    # TRIGGERS sheet
    ws_t = wb["TRIGGERS"]
    p("\n### [B] TRIGGERS sheet:")
    for row in ws_t.iter_rows(min_row=1, values_only=True):
        if any(v is not None for v in row):
            non_null = [str(v)[:60] for v in row if v is not None]
            p("  " + " | ".join(non_null))

    wb.close()
except Exception as e:
    p(f"  CASE_BANK read error: {e}")

# ─── FAPI LIVE DATA ───────────────────────────────────────────────
p("\n### [C] FAPI LIVE: klines 04-05/08 + OI")
time.sleep(1)

# 04/08 kline detail (1h bars to get OHLC detail)
start_04 = int(datetime(2026, 8, 4, tzinfo=timezone.utc).timestamp() * 1000)
end_04   = int(datetime(2026, 8, 4, 23, 59, tzinfo=timezone.utc).timestamp() * 1000)
d_1h = fetch(f"https://fapi.binance.com/fapi/v1/klines?symbol=BANKUSDT&interval=1h"
             f"&startTime={start_04}&endTime={end_04}&limit=24", timeout=15)

if "_error" not in d_1h and isinstance(d_1h, list):
    p(f"\n  04/08 1H klines: {len(d_1h)} bars")
    opens = [sf(b[1]) for b in d_1h if sf(b[1])]
    highs = [sf(b[2]) for b in d_1h if sf(b[2])]
    lows  = [sf(b[3]) for b in d_1h if sf(b[3])]
    closes= [sf(b[4]) for b in d_1h if sf(b[4])]
    vols  = [sf(b[7]) for b in d_1h if sf(b[7])]  # quote vol
    takers= [sf(b[9]) for b in d_1h if sf(b[9])]
    bases = [sf(b[5]) for b in d_1h if sf(b[5])]

    day_open = opens[0] if opens else None
    day_high = max(highs) if highs else None
    day_low  = min(lows) if lows else None
    day_close= closes[-1] if closes else None
    day_vol  = sum(vols) if vols else None
    taker_base_sum = sum(takers) if takers else None
    base_sum = sum(bases) if bases else None
    day_taker_pct = taker_base_sum/base_sum if (taker_base_sum and base_sum and base_sum>0) else None

    ret_04 = (day_close/day_open - 1) if (day_open and day_close and day_open>0) else None

    p(f"  04/08 O={day_open:.4f} H={day_high:.4f} L={day_low:.4f} C={day_close:.4f}")
    p(f"  ret O->C: {ret_04:.1%}" if ret_04 else "")
    p(f"  vol_perp: ${day_vol/1e6:.1f}M" if day_vol else "")
    p(f"  taker_perp: {day_taker_pct:.1%}" if day_taker_pct else "")

    # Also check previous day close for true daily ret
    d_prev = fetch("https://fapi.binance.com/fapi/v1/klines?symbol=BANKUSDT&interval=1d&limit=5", timeout=15)
    if "_error" not in d_prev and isinstance(d_prev, list):
        p("\n  Daily klines (recent):")
        for bar in d_prev[-5:]:
            ds = datetime.fromtimestamp(int(bar[0])/1000, tz=timezone.utc).strftime("%Y-%m-%d")
            o,h,l,c = sf(bar[1]),sf(bar[2]),sf(bar[3]),sf(bar[4])
            v = sf(bar[7])
            tb = sf(bar[9]); bb = sf(bar[5])
            tk = tb/bb if (tb and bb and bb>0) else None
            p(f"  {ds}: O={o:.4f} H={h:.4f} L={l:.4f} C={c:.4f} vol=${v/1e6:.1f}M taker={tk:.1%}" if (o and tk) else f"  {ds}: O={o} C={c}")
else:
    p(f"  1h klines error: {d_1h}")

time.sleep(1)

# Current OI
d_oi = fetch("https://fapi.binance.com/fapi/v1/openInterest?symbol=BANKUSDT", timeout=10)
if "_error" not in d_oi:
    oi_tokens = sf(d_oi.get("openInterest"))
    oi_ts = d_oi.get("time")
    p(f"\n  Live OI: {oi_tokens:,.0f} tokens (tokens, not USD)")

# OI history (last 5 days)
time.sleep(1)
d_oihist = fetch("https://fapi.binance.com/futures/data/openInterestHist?symbol=BANKUSDT&period=1d&limit=6", timeout=15)
if "_error" not in d_oihist and isinstance(d_oihist, list):
    p("\n  OI history (daily snapshots, tokens):")
    for item in d_oihist:
        ts = int(item.get("timestamp", 0))
        ds = datetime.fromtimestamp(ts/1000, tz=timezone.utc).strftime("%Y-%m-%d")
        oi_v = sf(item.get("sumOpenInterest"))
        oi_usd = sf(item.get("sumOpenInterestValue"))
        p(f"  {ds}: OI={oi_v:,.0f} tokens  OI_usd=${oi_usd/1e6:.2f}M" if (oi_v and oi_usd) else f"  {ds}: {item}")

time.sleep(1)

# LSR (long-short ratio) history
d_lsr = fetch("https://fapi.binance.com/futures/data/globalLongShortAccountRatio?symbol=BANKUSDT&period=1d&limit=6", timeout=15)
if "_error" not in d_lsr and isinstance(d_lsr, list):
    p("\n  gLSR history (daily):")
    for item in d_lsr:
        ts = int(item.get("timestamp", 0))
        ds = datetime.fromtimestamp(ts/1000, tz=timezone.utc).strftime("%Y-%m-%d")
        glsr = sf(item.get("longShortRatio"))
        lp = sf(item.get("longAccount"))
        sp = sf(item.get("shortAccount"))
        p(f"  {ds}: gLSR={glsr:.3f}  long={lp:.1%} short={sp:.1%}" if glsr else f"  {ds}: {item}")

time.sleep(1)

# pos_r (top trader position ratio)
d_pos = fetch("https://fapi.binance.com/futures/data/topLongShortPositionRatio?symbol=BANKUSDT&period=1d&limit=6", timeout=15)
if "_error" not in d_pos and isinstance(d_pos, list):
    p("\n  pos_r (top trader position) history:")
    for item in d_pos:
        ts = int(item.get("timestamp", 0))
        ds = datetime.fromtimestamp(ts/1000, tz=timezone.utc).strftime("%Y-%m-%d")
        pos_r = sf(item.get("longShortRatio"))
        p(f"  {ds}: pos_r={pos_r:.3f}" if pos_r else f"  {ds}: {item}")

time.sleep(1)

# Funding rate history
d_fund = fetch("https://fapi.binance.com/fapi/v1/fundingRate?symbol=BANKUSDT&limit=15", timeout=15)
if "_error" not in d_fund and isinstance(d_fund, list):
    p("\n  Funding rate history (last 15 intervals):")
    for item in d_fund[-10:]:
        ts = int(item.get("fundingTime", 0))
        ds = datetime.fromtimestamp(ts/1000, tz=timezone.utc).strftime("%Y-%m-%d %H:00")
        rate = sf(item.get("fundingRate"))
        p(f"  {ds}: f={rate:.5f}" if rate is not None else f"  {ds}: {item}")

# ─── 3 CONDITIONS CHECK ───────────────────────────────────────────
p("\n### [D] 3 DIEU KIEN VONG-2 WATCH")
p("")
p("  Dieu kien 1: pos_r — tren nguong CFF-GHE-ROI (peak-14d x 0.75)?")
p("  [computed above from fapi pos_r history — check vs peak-14d]")
p("")
p("  Dieu kien 2: gLSR — con flush hay da phuc hoi ve >1.3?")
p("  [computed above from gLSR history]")
p("")
p("  Dieu kien 3: funding — van duong (positive) hay da doi sang am/zero?")
p("  [computed above from funding history]")
p("")
p("  Tham chieu BANK peak:")
p("  peak_14d (peak pos_r ~14d truoc 04/08) = peak around 19-21/07 (exit)")
p("  VWAP advisor exit: 0.19710 | T0 ref: 0.04183")

with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
p(f"\n[DONE] -> {OUT}")
