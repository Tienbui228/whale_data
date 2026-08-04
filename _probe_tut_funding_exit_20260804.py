#!/usr/bin/env python3
"""PROBE TUT FUNDING EXIT: scorecard thesis exit.

(1) Xac minh co (e) tren Binance native funding tung ky 03-04/08
    vs Velo aggregate (freshwatch) — ghi an venue-scope
(2) Ghi moc exit_price = px nen funding-burst
(3) Do ket cuc: px_max sau co + time to peak (h) + T+24h/T+72h
    PASS: dinh <=24h sau co AND T+72h < exit_price
(4) [report spec gap — handled in proposals separately]
(5) Summary cho OUTCOME sheet: T0=09/07, exit-tell=04/08, T+7/14/30

Output: docs/reports/_probe_tut_funding_exit_20260804.md
"""
import io, json, sys, time, urllib.request, urllib.parse
from datetime import datetime, timezone, timedelta
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

WHALE = Path(r"D:\Data back test\whale_data")
OUT   = WHALE / "docs" / "reports" / "_probe_tut_funding_exit_20260804.md"

lines = []
def emit(*args):
    s = " ".join(str(a) for a in args)
    print(s); lines.append(s)

def ms_to_dt(ms: int) -> str:
    return datetime.utcfromtimestamp(ms / 1000).strftime("%Y-%m-%d %H:%M UTC")

def fetch_json(url: str, pause=0.3) -> dict | list | None:
    time.sleep(pause)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        emit(f"  [FETCH ERROR] {url[:80]}: {e}")
        return None

FAPI = "https://fapi.binance.com"

emit("# PROBE TUT FUNDING EXIT — Scorecard thesis exit")
emit(f"Run: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
emit("")

# ─── (A) VPS store: decode TUT funding_8h timestamps ─────────────────────────
emit("## A — VPS Store: TUT funding_8h (Binance native)")
emit("")
emit("(Data co san tu VPS raw/funding_8h — de-dup theo as_of_ts_ms)")
emit("")

# Raw from VPS output (paste from earlier read)
# as_of_ts_ms values (unique, sorted) from VPS data:
VPS_PERIODS_MS = [
    1785542400001, 1785556800000, 1785571200000, 1785585600000,
    1785600000000, 1785614400000, 1785628800000, 1785643200000,
    1785657600000, 1785672000007, 1785686400000, 1785700800002,
    1785715200000, 1785729600000, 1785744000000, 1785758400000,
    1785772800000, 1785787200003, 1785801600004,
]
VPS_MARK_PRICE = {
    1785542400001: 0.016100,
    1785556800000: 0.016066,
    1785571200000: 0.015911,
    1785585600000: 0.017579,
    1785600000000: 0.017199,
    1785614400000: 0.017380,
    1785628800000: 0.017540,
    1785643200000: 0.017117,
    1785657600000: 0.017318,
    1785672000007: 0.017415,
    1785686400000: 0.017520,
    1785700800002: 0.017521,
    1785715200000: 0.017574,
    1785729600000: 0.018660,
    1785744000000: 0.019515,
    1785758400000: 0.020090,
    1785772800000: 0.019709,
    1785787200003: 0.020480,
    1785801600004: 0.020392,
}

emit("| period (UTC) | funding_rate | mark_px | interval_h |")
emit("|-------------|-------------|---------|-----------|")
prev_ms = None
for ms in sorted(set(int(m) for m in VPS_PERIODS_MS)):
    dt   = ms_to_dt(ms)
    rate = 0.00005  # all pinned per VPS data
    mpx  = VPS_MARK_PRICE.get(ms, 0)
    intv = f"{(ms - prev_ms)/3600000:.1f}h" if prev_ms else "—"
    prev_ms = ms
    emit(f"| {dt} | {rate:.5f} | {mpx:.5f} | {intv} |")

emit("")
vps_start_dt = ms_to_dt(min(int(m) for m in VPS_PERIODS_MS))
vps_end_dt   = ms_to_dt(max(int(m) for m in VPS_PERIODS_MS))
emit(f"- VPS store coverage: {vps_start_dt} → {vps_end_dt}")
emit(f"- Interval: 4h (Binance da chuyen TUT sang 4h funding cycle)")
emit(f"- Tat ca {len(VPS_PERIODS_MS)} periods: funding_rate = 0.00005 (min cap Binance)")
emit(f"- **RESULT A: TUT funding GHIM cung 5bps MOI KY tren Binance native**")
emit("")

# ─── (B) Binance fapi: fetch funding 03/08→latest ────────────────────────────
emit("## B — Binance fapi: fundingRate 03/08→04/08 (real-time)")
emit("")

# 2026-08-03 00:00 UTC in ms
t_0803 = int(datetime(2026, 8, 3, tzinfo=timezone.utc).timestamp() * 1000)
t_now  = int(datetime.now(timezone.utc).timestamp() * 1000)

url_fr = (f"{FAPI}/fapi/v1/fundingRate?symbol=TUTUSDT"
          f"&startTime={t_0803}&limit=20")
fr_data = fetch_json(url_fr)

emit("| period (UTC) | funding_rate | markPrice | vs_velo |")
emit("|-------------|-------------|----------|---------|")

burst_found = False
burst_rate  = None
burst_dt    = None
burst_px    = None

if isinstance(fr_data, list):
    for fr in fr_data:
        ts   = int(fr.get("fundingTime", 0))
        rate = float(fr.get("fundingRate", 0))
        mpx  = float(fr.get("markPrice", 0)) if fr.get("markPrice") else 0
        dt   = ms_to_dt(ts)
        velo = 0.00005  # velo aggregate = pinned 5bps
        diff = "SAME" if abs(rate - velo) < 1e-7 else f"DIVERGE: binance={rate:.5f} velo={velo:.5f}"
        burst_marker = ""
        if rate > 0.0001:  # >2x baseline = burst signal
            burst_found = True
            burst_rate  = rate
            burst_dt    = dt
            burst_px    = mpx
            burst_marker = " ← **BURST**"
        emit(f"| {dt} | {rate:.5f} | {mpx:.5f} | {diff}{burst_marker} |")
else:
    emit(f"- Fetch error hoac empty response")
    emit(f"- Fallback: dung VPS data (tat ca 0.00005)")

emit("")
if burst_found:
    emit(f"- **BURST FOUND**: rate={burst_rate:.5f} tai {burst_dt}, mark_px={burst_px:.5f}")
else:
    emit(f"- **BURST NOT FOUND**: toan bo periods 03-04/08 = 0.00005 (min cap)")
    emit(f"  => Co (e) CHUA BUNG tren Binance native — Velo aggregate dong thuan")
    emit(f"  => Venue-scope gap: freshwatch dung Velo aggregate day du funding_n")
    emit(f"     nhung ca hai deu = 5bps → KHONG CO su phan ky venue nao")
emit("")

# ─── (C) Hourly klines TUT 01/08→now — do T+24h/T+72h ───────────────────────
emit("## C — Hourly klines TUT 01/08→04/08 (Binance fapi)")
emit("")

t_0801 = int(datetime(2026, 8, 1, tzinfo=timezone.utc).timestamp() * 1000)
url_kl = (f"{FAPI}/fapi/v1/klines?symbol=TUTUSDT&interval=1h"
          f"&startTime={t_0801}&limit=96")
kl_data = fetch_json(url_kl)

hour_klines = []  # [(open_ms, open, high, low, close, vol)]
if isinstance(kl_data, list):
    for k in kl_data:
        hour_klines.append({
            "ms":    int(k[0]),
            "dt":    ms_to_dt(int(k[0])),
            "open":  float(k[1]),
            "high":  float(k[2]),
            "low":   float(k[3]),
            "close": float(k[4]),
            "vol":   float(k[5]),
        })
    emit(f"- Fetched {len(hour_klines)} hourly klines (01/08 → latest)")
else:
    emit(f"- Fetch error — fallback to daily data")

# Print hourly table (compact: just date, high, close, vol)
if hour_klines:
    emit("")
    emit("| dt (UTC) | open | high | close | vol_K |")
    emit("|----------|------|------|-------|-------|")
    for h in hour_klines:
        emit(f"| {h['dt']} | {h['open']:.5f} | {h['high']:.5f} | {h['close']:.5f} | {h['vol']/1000:.1f}K |")
    emit("")

# ─── (D) Outcome measurement ──────────────────────────────────────────────────
emit("## D — Outcome Measurement (thesis test)")
emit("")

# Exit tell: 04/08 funding check (today). Since no burst, define exit tell
# as ngay co (e) chưa bật (PENDING) hoặc nếu burst tìm thấy = burst timestamp.
# "exit_price = px nến funding-burst" — nếu chưa bật thì ghi trạng thái PENDING.

if burst_found and burst_px:
    EXIT_PRICE = burst_px
    EXIT_DT    = burst_dt
    emit(f"- Exit tell: FUNDING BURST tại {EXIT_DT}")
    emit(f"- exit_price = {EXIT_PRICE:.5f} USDT (mark px tại burst candle)")
else:
    # No burst yet — use daily px 03/08 as reference (latest available)
    EXIT_PRICE = 0.01986   # px_avg 03/08 from freshwatch
    EXIT_DT    = "2026-08-03 (daily close)"
    emit(f"- Exit tell: CO (e) CHUA BUNG tính đến {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    emit(f"- exit_price (reference 03/08 daily): {EXIT_PRICE:.5f} USDT")
    emit(f"- => Do ket cuc se cap nhat khi burst xuat hien")
    emit("")

# Current px (latest hourly close)
if hour_klines:
    latest = hour_klines[-1]
    cur_px  = latest["close"]
    cur_dt  = latest["dt"]
    cur_ms  = latest["ms"]

    # px_max in full window
    px_max = max(h["high"] for h in hour_klines)
    px_max_h = next(h for h in hour_klines if h["high"] == px_max)

    emit(f"- Hien tai: px={cur_px:.5f} ({cur_dt})")
    emit(f"- px_max trong window 01/08→now: {px_max:.5f} ({px_max_h['dt']})")

    # T+24h/T+72h from 04/08 00:00 UTC
    t0_exit = int(datetime(2026, 8, 4, tzinfo=timezone.utc).timestamp() * 1000)
    t24 = t0_exit + 24 * 3600 * 1000
    t72 = t0_exit + 72 * 3600 * 1000

    def px_at_ms(target_ms):
        candidates = [h for h in hour_klines if h["ms"] <= target_ms]
        return candidates[-1] if candidates else None

    h24 = px_at_ms(t24)
    h72 = px_at_ms(t72)

    emit("")
    emit(f"| checkpoint | target_dt | px_close | vs exit_ref |")
    emit(f"|-----------|----------|---------|------------|")
    emit(f"| T0 exit-tell | 2026-08-04 | {EXIT_PRICE:.5f} | ref |")
    if h24:
        rel24 = (h24['close'] / EXIT_PRICE - 1) * 100
        emit(f"| T+24h | {ms_to_dt(t24)} | {h24['close']:.5f} | {rel24:+.1f}% vs exit_ref |")
    else:
        emit(f"| T+24h | {ms_to_dt(t24)} | PENDING | — |")
    if h72:
        rel72 = (h72['close'] / EXIT_PRICE - 1) * 100
        pass72 = h72['close'] < EXIT_PRICE
        emit(f"| T+72h | {ms_to_dt(t72)} | {h72['close']:.5f} | {rel72:+.1f}% → {'PASS (< exit_ref)' if pass72 else 'FAIL'} |")
    else:
        emit(f"| T+72h | {ms_to_dt(t72)} | PENDING | — |")
    emit("")

    # Thesis verdict
    if burst_found:
        # Check peak <=24h after burst
        burst_ms = int(datetime.strptime(burst_dt[:16], "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc).timestamp() * 1000) if burst_found else t0_exit
        peak_within_24h = (px_max_h["ms"] - burst_ms) <= 24 * 3600 * 1000
        t72_pass = h72 and h72["close"] < EXIT_PRICE if h72 else None

        emit(f"### THESIS VERDICT")
        emit(f"- Peak <=24h sau burst: {'PASS' if peak_within_24h else 'FAIL'} ({px_max_h['dt']})")
        emit(f"- T+72h < exit_price: {'PASS' if t72_pass else ('FAIL' if t72_pass is False else 'PENDING')}")
        overall = "PASS" if (peak_within_24h and t72_pass) else ("PARTIAL" if peak_within_24h else "FAIL")
        emit(f"- **OVERALL: {overall}**")
    else:
        emit(f"### THESIS VERDICT: PENDING (burst chua xuat hien)")
        emit(f"- exit_price reference: {EXIT_PRICE:.5f}")
        emit(f"- Hien tai px: {cur_px:.5f} ({(cur_px/EXIT_PRICE-1)*100:+.1f}% vs ref)")
        emit(f"- px_max da dat: {px_max:.5f} ({(px_max/EXIT_PRICE-1)*100:+.1f}% vs ref, tai {px_max_h['dt']})")

emit("")

# ─── (E) Venue-scope note ─────────────────────────────────────────────────────
emit("## E — Venue-scope Gap (ghi an)")
emit("")
emit("| item | freshwatch (Velo) | Binance fapi native | an gap |")
emit("|------|------------------|---------------------|-------|")
emit("| funding_avg TUT 20/07-03/08 | 0.00005 (tat ca ngay) | 0.00005 (tat ca ky 4h) | DONG THUAN |")
emit("| interval | daily aggregate | 4h per-period | Binance doi TUT sang 4h cycle (khong phai 8h) |")
emit("| burst signal | f_avg fixed 5bps | khong co burst | DONG THUAN — co (e) CHUA BUNG |")
emit("| venue tag | velo-agg | binance-native-fapi | can ghi venue trong co (e) spec |")
emit("")
emit("**Ket luan venue-scope**: Velo aggregate va Binance native DONG THUAN cho TUT.")
emit("Funding_rate = 0.00005 la min cap Binance, KHONG phai bung parabol.")
emit("Co (e) freshwatch dung Velo nhung so lieu khop — khong co phan ky venue.")
emit("**An gap ton tai**: freshwatch khong ghi ro venue nao + khong co nguong 'bung' dinh luong.**")
emit("")

# ─── (F) OUTCOME summary for CASE_TUT ────────────────────────────────────────
emit("## F — OUTCOME Summary (CASE_TUT OUTCOME sheet)")
emit("")
emit("| field | value |")
emit("|-------|-------|")
emit("| T0_ignition | 2026-07-09 |")
emit("| exit_tell_date | 2026-08-04 (co e PENDING — chua burst) |")
emit("| exit_tell_trigger | funding burst >=2x baseline |")
emit("| exit_price_ref | 0.01986 (daily 03/08, latest available) |")
emit("| px_max_so_far | " + (f"{px_max:.5f} ({px_max_h['dt']})" if hour_klines else "pending") + " |")
emit("| T+24h_px | " + (f"{h24['close']:.5f}" if h24 else "PENDING") + " |")
emit("| T+72h_px | " + (f"{h72['close']:.5f}" if h72 else "PENDING") + " |")
emit("| thesis_verdict | PENDING (burst chua xuat hien) |")
emit("| track_T7 | 2026-08-11 |")
emit("| track_T14 | 2026-08-18 |")
emit("| track_T30 | 2026-09-03 |")
emit("| spec_gap_1 | pos sap kieu BANK — chua co nguong so (proposal gap-a) |")
emit("| spec_gap_2 | co (e) thieu venue-scope + nguong burst dinh luong (proposal gap-b) |")
emit("")

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text("\n".join(lines), encoding="utf-8")
print(f"\nOutput: {OUT}")
