"""_task_clo_b5_b6_b7_20260818.py
B5: CLO spot api/v3 pair check (must verify from VPS since api.binance geo-blocked)
B6: PHASE-TAG cross-check phase_tag_daily.csv
B7: EVENTS append (Aug18 operator + machine events Aug10 dump, Aug18 pump)
"""
import sys, io, csv, json, urllib.request, time, subprocess
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
import openpyxl

ROOT    = Path(r"D:\Data back test\whale_data")
XLSX    = ROOT / "docs" / "case_files" / "CASE_CLO.xlsx"

# ── B5: spot api/v3 check via VPS ────────────────────────────────────────
print("="*70)
print("B5: SPOT api/v3 pair check (via VPS)")
print("="*70)

vps_probe = '''
import json, urllib.request
try:
    r = urllib.request.urlopen("https://api.binance.com/api/v3/exchangeInfo", timeout=15)
    info = json.loads(r.read().decode())
    print(f"total_spot={len(info.get('symbols',[]))}")
    matches = [s for s in info.get("symbols",[])
               if s.get("baseAsset")=="CLO" or "CLO" in s.get("symbol","")]
    if not matches:
        print("CLO spot: NONE")
    else:
        for s in matches[:10]:
            print(f"  {s.get('symbol')}  base={s.get('baseAsset')}  quote={s.get('quoteAsset')}  status={s.get('status')}")
    # Also search for "Yei" project name — sometimes tickers differ
    yei = [s for s in info.get("symbols",[])
           if "YEI" in s.get("baseAsset","").upper() or "YEI" in s.get("symbol","")]
    print(f"YEI spot matches: {len(yei)}")
    for s in yei[:5]:
        print(f"  {s.get('symbol')} base={s.get('baseAsset')} status={s.get('status')}")
except Exception as e:
    print(f"ERR: {e}")
'''

result = subprocess.run(
    ["ssh","-o","StrictHostKeyChecking=no","root@5.223.67.21","python3","-c",vps_probe],
    capture_output=True, text=True, timeout=45
)
print(result.stdout)
if result.stderr:
    print(f"stderr: {result.stderr[:500]}")

# ── B6: phase_tag_daily.csv cross-check ─────────────────────────────────
print("="*70)
print("B6: PHASE-TAG cross-check (phase_tag_daily.csv)")
print("="*70)

pt_paths = [
    ROOT / "data" / "screener" / "phase_tag_daily.csv",
    ROOT / "data" / "reports" / "phase_tag_daily.csv",
    ROOT / "scratch" / "phase_tag_daily.csv",
]
found = None
for p in pt_paths:
    if p.exists():
        found = p; break

if not found:
    # try scan whole tree
    matches = list(ROOT.rglob("phase_tag_daily*.csv"))
    print(f"  {len(matches)} candidate paths found via rglob:")
    for m in matches:
        print(f"    {m}")
    if matches:
        found = sorted(matches, key=lambda p: p.stat().st_mtime)[-1]  # newest

if not found:
    print("  ⚠ phase_tag_daily.csv NOT FOUND locally.")
    print("  Try VPS side...")
    result = subprocess.run(
        ["ssh","-o","StrictHostKeyChecking=no","root@5.223.67.21",
         "find /root/Data_back_test/whale_data -maxdepth 6 -iname 'phase_tag_daily*.csv' 2>/dev/null | head"],
        capture_output=True, text=True, timeout=30
    )
    print(result.stdout)
    if result.stderr: print(f"  stderr: {result.stderr[:300]}")
else:
    print(f"  Found: {found}")
    print(f"    mtime: {time.ctime(found.stat().st_mtime)}")
    with open(found, encoding="utf-8") as f:
        header = f.readline().strip()
        print(f"    header: {header}")
        rows = list(csv.DictReader(open(found, encoding="utf-8")))
    print(f"    rows: {len(rows)}")
    clo_rows = [r for r in rows if r.get("symbol","").upper() in ("CLO","CLOUSDT")]
    print(f"\n  CLO rows: {len(clo_rows)}")
    if clo_rows:
        for cr in clo_rows[-3:]:
            print(f"    {cr}")
    else:
        print("  ⚠⚠⚠ CLO VẮNG MẶT trong phase_tag_daily.csv (bug go-live phase-tag).")

# ── B7: EVENTS append ────────────────────────────────────────────────────
print("\n" + "="*70)
print("B7: EVENTS append")
print("="*70)

wb = openpyxl.load_workbook(XLSX)
ws_ev = wb["EVENTS"]
# Header row 3 (row 1 = title, row 3 = ngay/su_kien/nguon/doc_nhanh)
print(f"  EVENTS max_row: {ws_ev.max_row}")
print(f"  Row 3 (header): {[c.value for c in ws_ev[3]]}")
print(f"  Last existing event: {[c.value for c in ws_ev[ws_ev.max_row]]}")

next_r = ws_ev.max_row + 1
events_new = [
    # Aug08 (from data): funding drop to +23bps from ~+47bps trend
    ["08-08", "funding cool: f_avg 0.000229 vs 0.000466 avg preceding = warming down day", "fapi funding", "warmdown"],
    # Aug10: -14.57% crash
    ["08-10", "CRASH -14.57%, vol 10.6M spike, OI stable 4.5M (crowd flushed but perp size unchanged)", "fapi klines+OI", "flush_wave1"],
    # Aug11: recovery, biggest vol
    ["08-11", "REBOUND +7.67%, vol 16.1M (biggest day), OI -9.5% to 4.07M, pos_r 0.851→0.913 (SHORT-COVER partial)", "fapi klines+LSR", "cover_wave1"],
    # Aug12: pos_r rerate + OI rebuild
    ["08-12", "pos_r 0.939 leo, OI 4.91M rebuild, div_raw 0.520 CHẠM 0.5 (hedge tháo tạm)", "fapi+LSR", "hedge_untap_wave1"],
    # Aug14-15: pos_r crosses 1.0
    ["08-14", "pos_r CROSS 1.0 (0.985→1.024), gLSR 2.18 leo, div_raw 0.424 rơi lại (re-hedge)", "fapi LSR", "pos_r_cross_1"],
    # Aug18 intraday pump (operator source)
    ["08-18", "INTRADAY PUMP +27.15% (0.11604→0.14754 @13:50 UTC), OI 3.95M→6.27M (+58.8%), vol 24h $44M — cú đẩy operator ghi 18/08", "fapi ticker+OI intraday", "PUMP_INTRADAY_18"],
]
for ev in events_new:
    for ci, val in enumerate(ev, start=1):
        ws_ev.cell(next_r, ci).value = val
    print(f"  + row {next_r}: {ev[0]} | {ev[1][:50]}...")
    next_r += 1

wb.save(XLSX)
print(f"\n  EVENTS +{len(events_new)} rows saved")

print("\n[DONE B5+B6+B7]")
