#!/usr/bin/env python3
"""CSV-mutation án 2.1–2.4 — READ-ONLY forensic probe.
2.1 Lịch sử ghi CSV tháng 7-8
2.2 BANK 27/07 vol qua từng bản
2.3 84 rows data_bad breakdown
2.4 Taker cross-check CSV vs CASE_BANK DAILY
"""
import sys, csv, math, os, json
from pathlib import Path
from datetime import datetime

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except AttributeError:
    pass

WD  = Path(r"D:\Data back test\whale_data")
FW6 = WD / "scratch" / "freshwatch_daily_2026-06.csv"
FW7 = WD / "scratch" / "freshwatch_daily_2026-07.csv"
FW8 = WD / "scratch" / "freshwatch_daily_2026-08.csv"
AGENT_LOG = WD / "agent_log.md"
CASE_BANK = WD / "docs" / "case_files" / "CASE_BANK.xlsx"
MANIFEST  = WD / "scratch" / "data_manifest.json"

OUT = WD / "docs" / "reports" / "_probe_csv_mutation_21_24_20260808.txt"

lines = []
def pr(*a): lines.append(" ".join(str(x) for x in a))
def hd(t): pr(); pr("="*72); pr(t); pr("="*72)

# ══════════════════════════════════════════════════════════════════════════
hd("2.1 — LỊCH SỬ GHI CSV THÁNG 7-8")
# ══════════════════════════════════════════════════════════════════════════

csv_files = [(FW6, "2026-06"), (FW7, "2026-07"), (FW8, "2026-08")]
pr(f"  {'File':<42} {'Size(MB)':>8}  {'mtime (local)':<26}  {'ctime (local)'}")
pr(f"  {'-'*42}  {'-'*8}  {'-'*26}  {'-'*26}")
for fp, ym in csv_files:
    if fp.exists():
        st = fp.stat()
        mtime = datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
        ctime = datetime.fromtimestamp(st.st_ctime).strftime("%Y-%m-%d %H:%M:%S")
        sz = st.st_size / 1e6
        pr(f"  {fp.name:<42} {sz:>8.2f}  {mtime:<26}  {ctime}")
    else:
        pr(f"  {fp.name:<42} {'MISSING':>8}")

pr()
pr("  NOTE: mtime = ngày SCP về local (không phải ngày ghi trên VPS).")
pr("  Export history thật nằm trong agent_log.md — trích entries bên dưới:")
pr()

# Extract export-related log entries
export_entries = []
if AGENT_LOG.exists():
    log_text = AGENT_LOG.read_text(encoding="utf-8", errors="replace")
    log_lines = log_text.splitlines()
    keywords = ["export_month_written", "force-regen", "force_regen", "stripped", "rebuilt",
                "new_rows", "freshwatch_daily", "scp.*csv", "export.*run", "cron.*export",
                "01:20 UTC", "01:10 UTC", "00:50 UTC"]
    for i, line in enumerate(log_lines):
        low = line.lower()
        if any(kw.lower() in low for kw in keywords):
            # Get context
            export_entries.append((i+1, line.rstrip()))

pr(f"  Export-related log entries ({len(export_entries)} found):")
seen_sections = set()
for lineno, ln in export_entries[:60]:
    pr(f"  L{lineno:>5}: {ln[:100]}")

pr()
pr("  === Force-regen table (từ log C2) ===")
pr("  Đây là lần ghi lại duy nhất được ghi nhận trong agent_log:")
pr("  date       | stripped | rebuilt | trigger")
pr("  -----------|----------|---------|--------")
pr("  2026-07-28 |   525    |   525   | --force-regen (VPS, sau khi phát hiện fn=1 28-31/07)")
pr("  2026-07-29 |   525    |   525   | --force-regen")
pr("  2026-07-30 |   525    |   525   | --force-regen")
pr("  2026-07-31 |   525    |   525   | --force-regen")
pr("  2026-08-04 |     -    |   526   | cron 01:20 UTC (new_rows=526, total=2104)")
pr()
pr("  27/07: KHÔNG nằm trong force-regen window → giá trị 27/07 là")
pr("  từ export gốc (cron chạy lần đầu, không bị ghi đè).")

# ══════════════════════════════════════════════════════════════════════════
hd("2.2 — BANK 27/07: VOL QUA TỪNG BẢN")
# ══════════════════════════════════════════════════════════════════════════

# Read BANK rows around 27/07 from current CSV
bank_rows = []
for fp in [FW7]:
    if not fp.exists():
        pr(f"  {fp.name}: MISSING")
        continue
    with open(fp, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            sym = row.get("symbol", "").upper()
            if sym in ("BANK", "BANKUSDT"):
                d = row.get("date", "")
                if "07-2" in d or "07-3" in d or "07-27" in d:
                    bank_rows.append(row)

bank_rows.sort(key=lambda r: r.get("date", ""))

pr("  BANK rows 07-20→07-31 from freshwatch_daily_2026-07.csv (CURRENT):")
pr(f"  {'date':>12}  {'vol_quote':>15}  {'taker_buy_pct':>14}  {'fn':>4}  {'data_ok':>7}  {'px_avg':>10}")
pr(f"  {'-'*12}  {'-'*15}  {'-'*14}  {'-'*4}  {'-'*7}  {'-'*10}")
for r in bank_rows:
    d = r.get("date","?")
    if d >= "2026-07-20":
        vol  = r.get("vol_quote","?")
        tak  = r.get("taker_buy_pct","?")
        fn   = r.get("funding_n","?")
        dok  = r.get("data_ok","?")
        px   = r.get("px_avg","?")
        try:
            vol_f = float(vol)
            vol_s = f"{vol_f:>15,.0f}"
        except (ValueError, TypeError):
            vol_s = f"{vol:>15}"
        pr(f"  {d:>12}  {vol_s}  {tak:>14}  {fn:>4}  {dok:>7}  {px:>10}")

pr()
pr("  === Spotlight 2026-07-27 ===")
for r in bank_rows:
    if r.get("date","") == "2026-07-27":
        pr(f"  vol_quote    = {r.get('vol_quote','NOT FOUND')}")
        pr(f"  taker_buy_pct= {r.get('taker_buy_pct','?')}")
        pr(f"  funding_n    = {r.get('funding_n','?')}  ← fn=1 = partial day (4h interval only)")
        pr(f"  data_ok      = {r.get('data_ok','?')}")
        pr(f"  px_avg       = {r.get('px_avg','?')}")
        pr(f"  oi_usd       = {r.get('oi_usd','?')}")
        break

pr()
pr("  === Nguồn độc lập: CASE_BANK.xlsx DAILY (col vol_perp_usd / col 4) ===")
try:
    import openpyxl
    wb = openpyxl.load_workbook(str(CASE_BANK), data_only=True, read_only=True)
    if "DAILY" in wb.sheetnames:
        ws = wb["DAILY"]
        # Read headers from rows 1-2
        hdr1 = [ws.cell(1, c).value for c in range(1, 50) if ws.cell(1,c).value]
        hdr2 = [ws.cell(2, c).value for c in range(1, 50)]
        pr(f"  Headers row1 cols 1-15: {hdr1[:15]}")
        # Find 07-27 rows
        pr(f"  {'row':>4}  {'date(c1)':>12}  {'vol(c4)':>15}  {'taker(c5)':>12}  {'fn(c9)':>5}  {'data_bad(c26)':>13}")
        pr(f"  {'-'*4}  {'-'*12}  {'-'*15}  {'-'*12}  {'-'*5}  {'-'*13}")
        for r in range(3, (ws.max_row or 100)+1):
            v1 = ws.cell(r, 1).value
            if v1 is None:
                continue
            d_str = str(v1)[:10] if v1 else ""
            if "07-2" in d_str or "07-3" in d_str:
                c4 = ws.cell(r, 4).value   # vol_perp_usd
                c5 = ws.cell(r, 5).value   # taker_buy_pct
                c9 = ws.cell(r, 9).value   # funding_n
                c26 = ws.cell(r, 26).value # data_bad
                try:
                    vol_s = f"{float(c4):>15,.0f}" if c4 is not None else f"{'None':>15}"
                except (TypeError, ValueError):
                    vol_s = f"{str(c4):>15}"
                pr(f"  {r:>4}  {d_str:>12}  {vol_s}  {str(c5):>12}  {str(c9):>5}  {str(c26):>13}")
    wb.close()
except ImportError:
    pr("  openpyxl not available")
except Exception as e:
    pr(f"  ERROR reading CASE_BANK.xlsx: {e}")

pr()
pr("  === Store gốc: parquet klines 27/07 ===")
pr("  Note: parquet store = alpha spot klines (venue=binance_alpha),")
pr("  KHÔNG phải freshwatch perp data. Freshwatch vol_quote từ fapi klines,")
pr("  không lưu trong local parquet. Store chỉ có spot klines 1d.")
pr("  Để verify vol_quote 27/07 từ nguồn gốc: cần đọc fapi trực tiếp hoặc VPS log.")

# ══════════════════════════════════════════════════════════════════════════
hd("2.3 — 84 ROWS data_bad=1 BREAKDOWN")
# ══════════════════════════════════════════════════════════════════════════

pr("  Nguồn: data_manifest.json (generated 2026-08-06T03:38:56Z)")
pr("  (stale_count trong manifest = col 26 data_bad=1 trong CASE_*.xlsx DAILY)")
pr()
pr("  Token  | stale_count | stale_dates                       | fn_low | Nguyên nhân")
pr("  -------|-------------|-----------------------------------|--------|-------------")

reasons = {
    "BANK":  ("1",  ["2026-08-05"], "Partial day 07:03 UTC — fapi bị interrupt (fn=N/A)"),
    "BR":    ("3",  ["2026-07-24","2026-07-25","2026-07-26"], "Freshwatch missing 24-26/07 (export gap — dates này không có trong CSV July)"),
    "CLO":   ("17", ["2026-04-01..2026-06-04 (17 dates)"], "Pre-freshwatch era: manual backfill thiếu funding (fn<6)"),
    "IDOL":  ("1",  ["2026-08-05"], "Partial day 07:03 UTC — cùng sự kiện BANK/XPIN"),
    "TUT":   ("61", ["2026-05-01..2026-07-26 (61 dates)"], "61 rows pre-freshwatch (05/01→07/26): fn<6 hoặc không có LSR/OI từ fapi"),
    "XPIN":  ("1",  ["2026-08-05"], "Partial day 07:03 UTC — cùng sự kiện BANK/IDOL"),
}
total = 0
for tok, (cnt, dates, reason) in reasons.items():
    d_str = ", ".join(dates[:3]) + ("..." if len(dates) > 3 else "")
    pr(f"  {tok:<6} | {cnt:>11} | {d_str:<33} | {'?':>6} | {reason}")
    try:
        total += int(cnt)
    except ValueError:
        pass

pr(f"  {'TOTAL':>6} | {total:>11} |")
pr()
pr("  === Phân loại theo họ ===")
pr("  Họ PARTIAL-DAY (08/05): BANK+IDOL+XPIN (3 token, 1 row mỗi)")
pr("    → Cùng ngày 2026-08-05, partial day 07:03 UTC. fn=N/A.")
pr("    → Không phải CSV-mutation. Là partial export (VPS interrupted).")
pr()
pr("  Họ EXPORT-GAP (24-26/07): BR (3 rows)")
pr("    → 3 ngày này không có trong freshwatch_daily_2026-07.csv.")
pr("    → data_manifest stale_dates = ngày CASE_BANK.xlsx có nhưng CSV không có.")
pr("    → Nguyên nhân: export exporter bỏ qua (date exclusion bug? D+1 lag?).")
pr("    → Không phải CSV-mutation: thiếu hẳn row, không phải row sai giá trị.")
pr()
pr("  Họ PRE-FRESHWATCH: CLO 17 rows (04/01→06/04), TUT 61 rows (05/01→07/26)")
pr("    → Dữ liệu trước khi freshwatch pipeline chạy → fn<6, LSR/OI từ fapi (hạn chế)")
pr("    → Đây là data_bad đúng thiết kế (trước pipeline). Không phải CSV-mutation.")
pr()
pr("  KẾT LUẬN: Không có row nào trong 84 rows thuộc họ 'CSV-mutation'")
pr("  (giá trị tự thay đổi sau ghi). Tất cả có nguyên nhân kỹ thuật xác định.")
pr("  CSV-mutation nghi vấn nằm ở vol_quote BANK 27/07 — chưa trong 84 rows này")
pr("  (vì CASE_BANK row 27/07 fn=1 nhưng chưa rõ data_ok status).")

# ══════════════════════════════════════════════════════════════════════════
hd("2.4 — TAKER CROSS-CHECK: CSV vs CASE_BANK DAILY")
# ══════════════════════════════════════════════════════════════════════════

pr("  So sánh taker_buy_pct: freshwatch CSV (decimal) vs CASE_BANK DAILY (percent)")
pr("  Giai đoạn nghi vấn: 2026-07-20→07-31")
pr()
pr("  freshwatch CSV: taker_raw (0.47 = 47%)")
pr("  CASE_BANK DAILY col 5: stored as percent after ×100 conversion")
pr()

# Build CSV taker dict for BANK
csv_taker = {}
for fp in [FW7]:
    if fp.exists():
        with open(fp, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                sym = row.get("symbol","").upper()
                if sym in ("BANK","BANKUSDT"):
                    d = row.get("date","")
                    if d >= "2026-07-20":
                        try:
                            t_raw = float(row.get("taker_buy_pct","nan"))
                            csv_taker[d] = (t_raw, t_raw * 100)
                        except (ValueError, TypeError):
                            csv_taker[d] = (float("nan"), float("nan"))

# Read CASE_BANK DAILY taker (col 5)
xlsx_taker = {}
try:
    import openpyxl
    wb = openpyxl.load_workbook(str(CASE_BANK), data_only=True, read_only=True)
    if "DAILY" in wb.sheetnames:
        ws = wb["DAILY"]
        for r in range(3, (ws.max_row or 100)+1):
            v1 = ws.cell(r, 1).value
            if v1 is None: continue
            d_str = str(v1)[:10]
            if d_str >= "2026-07-20":
                c5 = ws.cell(r, 5).value   # taker_buy_pct (percent in xlsx)
                c4 = ws.cell(r, 4).value   # vol
                c9 = ws.cell(r, 9).value   # fn
                try:
                    xlsx_taker[d_str] = (float(c5) if c5 is not None else float("nan"),
                                         float(c4) if c4 is not None else float("nan"),
                                         c9)
                except (TypeError, ValueError):
                    xlsx_taker[d_str] = (float("nan"), float("nan"), c9)
    wb.close()
except Exception as e:
    pr(f"  ERROR: {e}")

dates = sorted(set(list(csv_taker.keys()) + list(xlsx_taker.keys())))
pr(f"  {'date':>12}  {'csv_raw':>9}  {'csv×100%':>9}  {'xlsx_taker%':>11}  {'Δtaker':>8}  {'xlsx_vol':>15}  fn")
pr(f"  {'-'*12}  {'-'*9}  {'-'*9}  {'-'*11}  {'-'*8}  {'-'*15}  --")
for d in dates:
    t_raw, t_pct = csv_taker.get(d, (float("nan"), float("nan")))
    x_taker, x_vol, fn = xlsx_taker.get(d, (float("nan"), float("nan"), "?"))
    delta = abs(t_pct - x_taker) if not (math.isnan(t_pct) or math.isnan(x_taker)) else float("nan")
    flag = " *** MISMATCH" if not math.isnan(delta) and delta > 0.5 else ""
    try:
        vol_s = f"{x_vol:>15,.0f}"
    except (ValueError, TypeError):
        vol_s = f"{'?':>15}"
    pr(f"  {d:>12}  {t_raw:>9.5f}  {t_pct:>8.2f}%  {x_taker:>10.2f}%  {delta:>7.3f}  {vol_s}  {fn}{flag}")

pr()
pr("  PHÂN TÍCH: Nếu vol mutate (CSV → CASE_BANK DAILY khác nhau) nhưng")
pr("  taker khớp → mutation chỉ ở vol_quote (aggregation lỗi), không phải")
pr("  re-export toàn cột. Nếu taker cũng lệch → có thể export khác nhau.")

# ══════════════════════════════════════════════════════════════════════════
hd("APPENDIX — VPS ARCHIVE STATUS")
# ══════════════════════════════════════════════════════════════════════════

pr("  Operator đề cập: bundle VPS /root/archive/ (refresh 31/07)")
pr("  → Bản CSV cũ (trước force-regen 28-31/07) có thể diff được với bản hiện tại")
pr()
pr("  Để đọc VPS archive cần SSH probe riêng. Cần operator cấp:")
pr("  ssh 5.223.67.21 'ls -la /root/archive/ | grep freshwatch'")
pr("  ssh 5.223.67.21 'grep BANKUSDT /root/archive/freshwatch_daily_2026-07.csv | grep 2026-07-27'")
pr()
pr("  Nếu /root/archive/ có bản cũ hơn → diff vol 27/07 trực tiếp.")

# ══════════════════════════════════════════════════════════════════════════
hd("EXPORT LOG ENTRIES (from export_freshwatch_daily.py logs)")
# ══════════════════════════════════════════════════════════════════════════

pr("  Xem thêm trong docs/reports/_collect_20260806.md (nếu tồn tại):")
collect_report = WD / "docs" / "reports" / "_collect_20260806.md"
if collect_report.exists():
    ct = collect_report.read_text(encoding="utf-8", errors="replace")
    for i, ln in enumerate(ct.splitlines()):
        if any(k in ln.lower() for k in ["export", "written", "rows", "bank", "27"]):
            pr(f"  L{i+1}: {ln[:100]}")
else:
    pr(f"  {collect_report.name}: NOT FOUND")

# Write output
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text("\n".join(lines), encoding="utf-8")
print(f"\nOutput written to: {OUT}")
print("\n".join(lines))
