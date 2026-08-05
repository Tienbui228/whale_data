# -*- coding: utf-8 -*-
"""
IDOL: Y1 series 04/08->now + Y2 EVAA checklist + Y3 58bro ledger
read CASE_IDOL EVENTS + fetch VPS freshwatch 04-06/08 + fapi live
"""
import urllib.request, json, ssl, time, subprocess
from datetime import datetime, timezone

OUT = "scratch/idol_vong2_20260806.txt"
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
                time.sleep(2 + attempt*2)
            else:
                return {"_error": str(e)}

def sf(x, d=None):
    try: return float(x)
    except: return d

TS = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
p("=" * 72)
p(f"IDOL VONG-2 WATCH (Y1-Y3) - {TS}")
p("=" * 72)

# ─── READ CASE_IDOL DAILY + EVENTS ────────────────────────────────
p("\n### [READ] CASE_IDOL DAILY + EVENTS")
try:
    import openpyxl
    wb = openpyxl.load_workbook("docs/case_files/CASE_IDOL.xlsx", read_only=True)
    p(f"  Sheets: {wb.sheetnames}")

    # DAILY: last 15 rows
    ws_d = wb["DAILY"]
    all_rows = []
    for row in ws_d.iter_rows(min_row=3, values_only=True):
        if row[0]:
            all_rows.append(row)
    p(f"  DAILY rows: {len(all_rows)}")

    p("\n  DAILY last 15 rows (col indices 0-based):")
    p(f"  {'date':<12} {'px':>8} {'vol_p':>9} {'taker':>7} {'f_avg':>9} {'fn':>3} "
      f"{'pos_r':>6} {'acc_r':>6} {'gLSR':>6} {'oi':>9} {'data_bad':>4}")
    p("  " + "-"*90)
    for row in all_rows[-15:]:
        d_str = str(row[0])[:10] if row[0] else ""
        px    = sf(row[1]);   vol   = sf(row[3]);  taker = sf(row[4])
        f_avg = sf(row[5]);   f_n   = row[8]
        pos_r = sf(row[14]);  acc_r = sf(row[15]); glsr  = sf(row[16])
        oi    = sf(row[11]);  dbad  = row[25]
        p(f"  {d_str:<12} {px:>8.5f} {f'${vol/1e6:.0f}M':>9} "
          f"{f'{taker:.1%}':>7} {f'{f_avg:.5f}' if f_avg else 'N/A':>9} "
          f"{str(f_n):>3} {f'{pos_r:.3f}' if pos_r else 'N/A':>6} "
          f"{f'{acc_r:.3f}' if acc_r else 'N/A':>6} {f'{glsr:.3f}' if glsr else 'N/A':>6} "
          f"{f'${oi/1e6:.2f}M' if oi else 'N/A':>9} {'[!]' if dbad else '':>4}")

    # EVENTS sheet
    if "EVENTS" in wb.sheetnames:
        ws_e = wb["EVENTS"]
        p("\n  EVENTS sheet (58bro + key wallet events):")
        for row in ws_e.iter_rows(min_row=1, max_row=ws_e.max_row, values_only=True):
            if any(v is not None for v in row):
                vals = [str(v)[:50] if v is not None else "" for v in row]
                p("  " + " | ".join(v for v in vals if v))
    wb.close()
except Exception as e:
    p(f"  CASE_IDOL read error: {e}")

# ─── VPS freshwatch IDOL 01-06/08 ────────────────────────────────
p("\n### [VPS] IDOL freshwatch 01-06/08")
try:
    r = subprocess.run(
        ["ssh", "root@5.223.67.21",
         "grep 'IDOLUSDT' /root/Data_back_test/whale_data/data/export/freshwatch_daily_2026-08.csv"],
        capture_output=True, text=True, timeout=20)
    if r.returncode == 0 and r.stdout.strip():
        p(f"  Raw lines:")
        for line in r.stdout.strip().split("\n"):
            p(f"  {line}")
    else:
        p(f"  No data or error: {r.stderr[:200]}")
except Exception as e:
    p(f"  SSH error: {e}")

time.sleep(1)

# ─── FAPI LIVE: klines + OI + LSR + Funding ──────────────────────
p("\n### [FAPI] IDOL live data 01-06/08")

# Daily klines (last 8 bars)
d_klines = fetch("https://fapi.binance.com/fapi/v1/klines?symbol=IDOLUSDT&interval=1d&limit=8", timeout=15)
if "_error" not in d_klines and isinstance(d_klines, list):
    p("\n  Daily klines:")
    p(f"  {'date':<12} {'O':>8} {'H':>8} {'L':>8} {'C':>8} {'vol_$':>10} {'taker':>7} ret_d")
    prev_c = None
    for bar in d_klines:
        ds = datetime.fromtimestamp(int(bar[0])/1000, tz=timezone.utc).strftime("%Y-%m-%d")
        o,h,l,c = sf(bar[1]),sf(bar[2]),sf(bar[3]),sf(bar[4])
        v = sf(bar[7]);  tb = sf(bar[9]); bb = sf(bar[5])
        tk = tb/bb if (tb and bb and bb>0) else None
        ret = (c/prev_c - 1) if (prev_c and c and prev_c>0) else None
        p(f"  {ds:<12} {o:>8.5f} {h:>8.5f} {l:>8.5f} {c:>8.5f} "
          f"{f'${v/1e6:.1f}M':>10} {f'{tk:.1%}' if tk else 'N/A':>7} "
          f"{f'{ret:.1%}' if ret else '':>6}")
        prev_c = c
else:
    p(f"  klines error: {d_klines}")

time.sleep(1)

# 4h klines last 12 bars (verify fn and funding intervals)
d_4h = fetch("https://fapi.binance.com/fapi/v1/klines?symbol=IDOLUSDT&interval=4h&limit=18", timeout=15)
if "_error" not in d_4h and isinstance(d_4h, list):
    p(f"\n  4h klines (last 18 bars — funding intervals):")
    p(f"  {'datetime':<18} {'C':>8} {'vol':>10} {'taker':>7}")
    for bar in d_4h[-12:]:
        ds = datetime.fromtimestamp(int(bar[0])/1000, tz=timezone.utc).strftime("%m-%d %H:00")
        c = sf(bar[4]); v = sf(bar[7]); tb = sf(bar[9]); bb = sf(bar[5])
        tk = tb/bb if (tb and bb and bb>0) else None
        p(f"  {ds:<18} {c:>8.5f} {f'${v/1e6:.2f}M':>10} {f'{tk:.1%}' if tk else 'N/A':>7}")

time.sleep(1)

# OI history
d_oi = fetch("https://fapi.binance.com/futures/data/openInterestHist?symbol=IDOLUSDT&period=1d&limit=8", timeout=15)
OI_FLOOR = 3920000  # user: floor 27/07
if "_error" not in d_oi and isinstance(d_oi, list):
    p(f"\n  OI history (floor={OI_FLOOR/1e6:.2f}M from 27/07):")
    for item in d_oi:
        ts = int(item.get("timestamp",0))
        ds = datetime.fromtimestamp(ts/1000, tz=timezone.utc).strftime("%Y-%m-%d")
        oi_v = sf(item.get("sumOpenInterest"))
        oi_usd = sf(item.get("sumOpenInterestValue"))
        vs_floor = (oi_usd/OI_FLOOR - 1) if (oi_usd and OI_FLOOR>0) else None
        p(f"  {ds}: OI=${oi_usd/1e6:.3f}M  vs_floor={vs_floor:+.1%}" if vs_floor is not None
          else f"  {ds}: {item}")

time.sleep(1)

# gLSR
d_glsr = fetch("https://fapi.binance.com/futures/data/globalLongShortAccountRatio?symbol=IDOLUSDT&period=1d&limit=8", timeout=15)
if "_error" not in d_glsr and isinstance(d_glsr, list):
    p(f"\n  gLSR history (flush target: <=1.1):")
    for item in d_glsr:
        ts = int(item.get("timestamp",0))
        ds = datetime.fromtimestamp(ts/1000, tz=timezone.utc).strftime("%Y-%m-%d")
        glsr = sf(item.get("longShortRatio"))
        lp   = sf(item.get("longAccount"))
        sp   = sf(item.get("shortAccount"))
        tag  = " << FLUSH" if glsr and glsr <= 1.1 else (" [close]" if glsr and glsr <= 1.3 else "")
        p(f"  {ds}: gLSR={glsr:.3f} long={lp:.1%} short={sp:.1%}{tag}" if glsr else f"  {ds}: err")

time.sleep(1)

# pos_r
d_pos = fetch("https://fapi.binance.com/futures/data/topLongShortPositionRatio?symbol=IDOLUSDT&period=1d&limit=8", timeout=15)
if "_error" not in d_pos and isinstance(d_pos, list):
    p(f"\n  pos_r (top trader position) — rebuild from trough?")
    prev_pr = None
    for item in d_pos:
        ts = int(item.get("timestamp",0))
        ds = datetime.fromtimestamp(ts/1000, tz=timezone.utc).strftime("%Y-%m-%d")
        pr = sf(item.get("longShortRatio"))
        delta = (pr/prev_pr - 1) if (prev_pr and pr and prev_pr>0) else None
        tag = f" {'+' if delta>=0 else ''}{delta:.1%}" if delta else ""
        p(f"  {ds}: pos_r={pr:.3f}{tag}" if pr else f"  {ds}: err")
        prev_pr = pr

time.sleep(1)

# acc_r (top trader account ratio)
d_acc = fetch("https://fapi.binance.com/futures/data/topLongShortAccountRatio?symbol=IDOLUSDT&period=1d&limit=8", timeout=15)
if "_error" not in d_acc and isinstance(d_acc, list):
    p(f"\n  acc_r (top trader account):")
    for item in d_acc:
        ts = int(item.get("timestamp",0))
        ds = datetime.fromtimestamp(ts/1000, tz=timezone.utc).strftime("%Y-%m-%d")
        ar = sf(item.get("longShortRatio"))
        p(f"  {ds}: acc_r={ar:.3f}" if ar else f"  {ds}: err")

time.sleep(1)

# Funding history (last 20 intervals = ~3.3 ngày x 6 kỳ/ngày)
d_fund = fetch("https://fapi.binance.com/fapi/v1/fundingRate?symbol=IDOLUSDT&limit=20", timeout=15)
if "_error" not in d_fund and isinstance(d_fund, list):
    p(f"\n  Funding rate (last 20 intervals — 4h each):")
    PIN = 5e-5
    pin_streak = 0
    for item in d_fund[-20:]:
        ts = int(item.get("fundingTime",0))
        ds = datetime.fromtimestamp(ts/1000, tz=timezone.utc).strftime("%m-%d %H:00")
        rate = sf(item.get("fundingRate"))
        is_pin = rate and abs(rate - PIN) < 5e-6
        if is_pin:
            pin_streak += 1
        else:
            pin_streak = 0
        tag = f" [PIN x{pin_streak}]" if is_pin else ""
        p(f"  {ds}: f={rate:.5f}{tag}" if rate is not None else f"  {ds}: err")
    p(f"  PIN streak at end: {pin_streak} intervals (target: >=4)")

time.sleep(1)

# Current live snapshot
d_oi_live = fetch("https://fapi.binance.com/fapi/v1/openInterest?symbol=IDOLUSDT", timeout=10)
if "_error" not in d_oi_live:
    oi_tok = sf(d_oi_live.get("openInterest"))
    p(f"\n  Live OI tokens: {oi_tok:,.0f}" if oi_tok else "  Live OI: err")

# Live ticker
d_tick = fetch("https://fapi.binance.com/fapi/v1/ticker/24hr?symbol=IDOLUSDT", timeout=10)
if "_error" not in d_tick:
    px_last = sf(d_tick.get("lastPrice"))
    px_high = sf(d_tick.get("highPrice"))
    px_low  = sf(d_tick.get("lowPrice"))
    vol24   = sf(d_tick.get("quoteVolume"))
    p(f"  Live 24h: last={px_last:.5f} H={px_high:.5f} L={px_low:.5f} vol=${vol24/1e6:.1f}M" if px_last else "")

# ─── Y3: 58bro ledger from operator info ─────────────────────────
p("\n" + "=" * 72)
p("### [Y3] 58bro LEDGER (operator 06/08 screenshot, so doi chieu)")
p("")
p("  Hanh dong 58bro tu EVENTS cu (truoc 04/08):")
p("  - Co the da ghi: 'rut 24M hold' -> CAN KIEM TRA SO LIEU CHINH XAC")
p("  - Neu EVENTS ghi 'rut 24M' nhung thuc te 58bro nhan 27.06M thi can sua")
p("")
p("  Dong moi (06/08 — operator screenshot):")
p("  [1] Nhan 27.06M tokens (Gate xuat -> vi 58bro?), roi NAP LAI 27.06M (04/08)")
p("      => net dong [1] = ZERO (nhan xong nap luon, khong hold them)")
p("  [2] Nhan 10M tokens (04/08)")
p("  [3] Nhan 14.3M tokens (04/08)")
p("  [4] Nhan 8.14M tokens (06/08)")
p("")
p("  Net tinh tu dong moi:")
p("  Nap lai (di ra): -27.06M")
p("  Nhan (vao):      +27.06M + 10M + 14.3M + 8.14M = +59.5M")
p("  NET MO'I:        +59.5M - 27.06M = +32.44M tokens")
p("")
p("  Pat tern doc:")
p("  Gate -> vi -> Gate: DONG 1 = 27.06M roundtrip 04/08 (nhan xong nap ngay)")
p("  Net giu lai: 10M + 14.3M + 8.14M = 32.44M (chua nap)")
p("  -> NEU 32.44M van con trong vi -> GIAM DAN KHOI GATE (gom them)")
p("  -> NEU da nap tiep vao Gate sau -> PHAN PHOI (con thoi day hang)")
p("  PENDING: kiem tra vi 58bro co phat sinh them lenh nap nao sau 06/08?")
p("")
p("  Doi chieu Gate wallet 0x0d0707:")
p("  PENDING operator: balance hien tai + tx log 01-06/08")

# ─── Y2: EVAA CHECKLIST (computed from data above) ────────────────
p("\n" + "=" * 72)
p("### [Y2] EVAA CHECKLIST (se tinh sau khi co so lieu fapi ben tren)")
p("")
p("  [1] gLSR flush <= 1.1: XEM SECTION gLSR TREN")
p("  [2] pos_r rebuild tu day: XEM SECTION pos_r TREN")
p("  [3] Funding pin >=4d: XEM SECTION funding TREN (PIN streak)")
p("  [4] px vs nen 0.0147-0.0155: XEM daily klines TREN")
p("  [5] Suppressor moi: xem tren phan vol/taker pattern")

with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
p(f"\n[DONE] -> {OUT}")
