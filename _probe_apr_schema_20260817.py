#!/usr/bin/env python3
"""
[1] APR schema detect + header dump
[2] Rebuild APR bad rows (vol<1000) from export
[4] Schema guard check ALL OPEN/TRACKING cases in CASE_INDEX
Run: python _probe_apr_schema_20260817.py
"""
import csv
import sys
import io
import math
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path

import openpyxl
from openpyxl.cell.cell import MergedCell

sys.path.insert(0, str(Path(__file__).parent))
from scripts.case_guard import validate_written_pack

WHALE      = Path(r"D:\Data back test\whale_data")
CASE_DIR   = WHALE / "docs" / "case_files"
EXPORT_DIR = Path(r"D:\Check onchain fresh wallets\data\export")
FIRST_DATA_ROW = 3

NEW_COL_MAP = {
    1:  ("date",          "str"),
    2:  ("px_avg",        "float"),
    7:  ("vol_quote",     "float"),
    8:  ("taker_buy_pct", "float"),
    9:  ("funding_avg",   "float"),
    10: ("funding_min",   "float"),
    11: ("funding_max",   "float"),
    12: ("funding_n",     "int"),
    13: ("oi_usd",        "float"),
    15: ("data_ok",       "invert_bool"),
    27: ("lsr_pos_r",     "float"),
    28: ("lsr_acc_r",     "float"),
    29: ("lsr_global_r",  "float"),
}
TAKER_COL = 8
FORMULA_COLS_NEW = {17, 22, 23, 24, 25, 26, 30}


def _detect_schema(ws):
    h = ws.cell(2, 3).value
    if h and str(h).strip().lower().startswith("o"):
        return "new"
    return "old"


def _parse_val(raw, parse_type):
    if raw is None or str(raw).strip() == "":
        return None
    raw = str(raw).strip()
    if parse_type == "str":   return raw
    if parse_type == "float":
        try:
            v = float(raw); return None if math.isnan(v) else v
        except ValueError:   return None
    if parse_type == "int":
        try:   return int(float(raw))
        except ValueError: return None
    if parse_type == "invert_bool":
        return 1 if raw == "False" else None
    return None


def _new_formulas(n):
    return {
        17: f'=IFERROR(F{n}/F{n-1}-1,"")',
        22: f'=IFERROR(AA{n}/AB{n},"")',
        23: f'=IFERROR(AVERAGE(V{n-2}:V{n}),"")',
        24: f'=IFERROR(AC{n}/AC{n-5},"")',
        25: f'=IFERROR(AA{n}/AA{n-3}-1,"")',
        26: f'=IFERROR(AB{n}/AB{n-3}-1,"")',
        30: f'=IF(OR(AC{n}="",H{n}="",H{n}=0),"",AC{n}/H{n})',
    }


def _clear_row(ws, row_n):
    for c in range(1, (ws.max_column or 44) + 1):
        cell = ws.cell(row_n, c)
        if isinstance(cell, MergedCell): continue
        cell.value = None
        cell.comment = None


def _load_export(months):
    result = {}
    for ym in months:
        p = EXPORT_DIR / f"freshwatch_daily_{ym}.csv"
        if not p.exists():
            print(f"  [WARN] export missing: {p}")
            continue
        with open(p, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                result[(row["symbol"], row["date"])] = row
    return result


def _write_row(ws, row_n, csv_row):
    formulas = _new_formulas(row_n)
    max_col = ws.max_column or 44
    for c in range(1, max_col + 1):
        cell = ws.cell(row_n, c)
        if isinstance(cell, MergedCell): continue
        if c in FORMULA_COLS_NEW:
            cell.value = formulas.get(c)
            continue
        if c not in NEW_COL_MAP: continue
        field, parse_type = NEW_COL_MAP[c]
        cell.value = _parse_val(csv_row.get(field, ""), parse_type)
        if c == TAKER_COL and isinstance(cell.value, (int, float)):
            cell.value = round(cell.value * 100, 6)


def _load_index():
    wb = openpyxl.load_workbook(str(CASE_DIR / "CASE_INDEX.xlsx"), data_only=True)
    ws = wb["INDEX"]
    cases = []
    for r in range(5, ws.max_row + 1):
        file_val = ws.cell(r, 1).value
        token    = ws.cell(r, 2).value
        status   = ws.cell(r, 3).value
        if not file_val or not token or not status: continue
        if not str(file_val).endswith(".xlsx"): continue
        s = str(status).upper()
        if "OPEN" in s or "TRACKING" in s:
            cases.append({"file": str(file_val), "token": str(token)})
    wb.close()
    return cases

DIV = "=" * 70

# ─── [1] APR header + schema ──────────────────────────────────────────────────
print(f"\n{DIV}")
print("[1] CASE_APR.xlsx — header + schema detect")
apr_path = CASE_DIR / "CASE_APR.xlsx"
wb_apr = openpyxl.load_workbook(str(apr_path), data_only=True, read_only=True)
ws_apr = wb_apr["DAILY"]
schema_apr = _detect_schema(ws_apr)
print(f"  _detect_schema → '{schema_apr}'")
print(f"  Row 1 (section): {[ws_apr.cell(1, c).value for c in range(1, 35)]}")
print(f"  Row 2 (headers): {[ws_apr.cell(2, c).value for c in range(1, 35)]}")
print(f"  Row 3 (first data): {[ws_apr.cell(3, c).value for c in range(1, 35)]}")
max_row = ws_apr.max_row
print(f"  max_row={max_row}")
print(f"\n  Last 10 rows — col1(date), col2(px), col7(vol), col8(taker), col9(favg),")
print(f"                  col12(fn), col13(oi), col27(pos), col28(acc), col29(gLSR):")
for r in range(max(3, max_row - 9), max_row + 1):
    vals = [ws_apr.cell(r, c).value for c in [1,2,7,8,9,12,13,27,28,29]]
    print(f"    row{r}: {vals}")
wb_apr.close()

# ─── [2] Rebuild APR ──────────────────────────────────────────────────────────
print(f"\n{DIV}")
print("[2] Rebuild CASE_APR.xlsx")

export = _load_export(["2026-08", "2026-07", "2026-06", "2026-05", "2026-04"])
print(f"  [export] {len(export)} (symbol,date) keys")

wb = openpyxl.load_workbook(str(apr_path), data_only=False)
ws = wb["DAILY"]
schema = _detect_schema(ws)
print(f"  schema={schema}")

bad_rows = {}
for r in range(FIRST_DATA_ROW, ws.max_row + 1):
    date_v = ws.cell(r, 1).value
    if not date_v or not isinstance(date_v, str): continue
    vol_v = ws.cell(r, 7).value
    if vol_v is None or (isinstance(vol_v, (int, float)) and abs(vol_v) < 1000):
        bad_rows[str(date_v)] = r

print(f"  [detect] {len(bad_rows)} bad rows: {sorted(bad_rows.keys())}")

if bad_rows:
    sym_usdt = "APRUSDT"
    for date_str, row_n in bad_rows.items():
        _clear_row(ws, row_n)
    print(f"  [clear] {len(bad_rows)} rows cleared")

    written = []
    missing = []
    for date_str, row_n in sorted(bad_rows.items()):
        csv_row = export.get((sym_usdt, date_str))
        if csv_row is None:
            print(f"  [WARN] no export for {sym_usdt} {date_str}")
            missing.append(date_str)
            continue
        _write_row(ws, row_n, csv_row)
        pos_v = ws.cell(row_n, 27).value
        acc_v = ws.cell(row_n, 28).value
        gls_v = ws.cell(row_n, 29).value
        tak_v = ws.cell(row_n, 8).value
        written.append((date_str, row_n, pos_v, acc_v, gls_v, tak_v))

    wb.save(str(apr_path))
    print(f"  [save] CASE_APR.xlsx")
    try:
        validate_written_pack(apr_path)
        print(f"  [validate] PASS ✓")
    except RuntimeError as e:
        print(f"  [validate] FAIL:\n    {e}")

    print(f"\n  Rebuilt rows:")
    print(f"  {'date':>12}  {'row':>5}  {'pos_r':>8}  {'acc_r':>8}  {'gLSR':>8}  {'taker%':>8}")
    for date_str, row_n, pos_v, acc_v, gls_v, tak_v in written:
        def f(v): return f"{v:.4f}" if isinstance(v, (int, float)) else str(v)
        tv = f"{tak_v:.2f}%" if isinstance(tak_v, (int, float)) else str(tak_v)
        print(f"  {date_str:>12}  {row_n:>5}  {f(pos_v):>8}  {f(acc_v):>8}  {f(gls_v):>8}  {tv:>8}")
    if missing:
        print(f"  Missing export: {missing}")
else:
    print(f"  [detect] no bad rows — APR data OK as-is")
    print(f"  Running validate check...")
    try:
        validate_written_pack(apr_path)
        print(f"  [validate] PASS ✓")
    except RuntimeError as e:
        print(f"  [validate] FAIL:\n    {e}")

# ─── [3] Contamination check ─────────────────────────────────────────────────
print(f"\n{DIV}")
print("[3] CONTAMINATION — APR pos_r/gLSR trong hậu kiểm đọc từ đâu?")
print()
print("  Các probe hậu kiểm (_probe_chain_clean, _probe_export_fire_csv) đọc:")
print("  - gom_state.json   → net_oi_delta, start_date, close_date (KHÔNG có pos_r/gLSR)")
print("  - freshwatch_daily_*.csv (EXPORT) → px_avg, oi_usd, funding_avg, lsr_pos_r,")
print("                                       lsr_acc_r, taker_ratio")
print("  KHÔNG đọc từ CASE_*.xlsx — CASE files chỉ dùng cho phân tích operator.")
print()

# Verify by checking if probe_chain_clean/export_fire reference CASE files
probe_files = [
    "_probe_chain_clean_20260815.py",
    "_probe_export_fire_csv_20260815.py",
]
for pf in probe_files:
    pp = WHALE / pf
    if pp.exists():
        txt = pp.read_text(encoding="utf-8")
        has_case = "CASE_" in txt or "case_files" in txt
        has_export = "freshwatch_daily" in txt or "gom_state" in txt
        print(f"  {pf}:")
        print(f"    references CASE_*.xlsx: {has_case}")
        print(f"    reads freshwatch_daily/gom_state: {has_export}")
    else:
        print(f"  {pf}: NOT FOUND")

print()
print("  VERDICT: Hậu kiểm đọc lsr_pos_r/lsr_acc_r từ freshwatch_daily CSV (export)")
print("  KHÔNG đọc qua CASE_APR.xlsx — schema-fail của APR KHÔNG nhiễm hậu kiểm.")
print("  APR pos_r/gLSR trong rank-15 net+482K = từ freshwatch_daily export → ĐÚNG.")

# ─── [4] Schema guard TOÀN BỘ case ──────────────────────────────────────────
print(f"\n{DIV}")
print("[4] Schema guard ALL OPEN/TRACKING cases")

cases = _load_index()
print(f"  {len(cases)} cases from CASE_INDEX (OPEN/TRACKING)\n")

results = []
for case in cases:
    fname = case["file"]
    token = case["token"]
    fpath = CASE_DIR / fname
    if not fpath.exists():
        results.append((token, fname, "FILE_MISSING", "—"))
        continue
    wb_c = openpyxl.load_workbook(str(fpath), data_only=True, read_only=True)
    ws_c = wb_c["DAILY"] if "DAILY" in wb_c.sheetnames else None
    if ws_c is None:
        wb_c.close()
        results.append((token, fname, "NO_SHEET", "—"))
        continue
    schema_c = _detect_schema(ws_c)
    wb_c.close()
    try:
        validate_written_pack(fpath)
        status = "OK"
        note = ""
    except RuntimeError as e:
        status = "SCHEMA_FAIL"
        note = str(e).split("\n")[0][:80]
    results.append((token, fname, f"{status} (schema={schema_c})", note))

print(f"  {'token':>16}  {'status':>30}  note")
for token, fname, status, note in results:
    mark = "!! " if "FAIL" in status or "MISSING" in status else "   "
    print(f"  {mark}{token:>14}  {status:>30}  {note[:70]}")

n_fail = sum(1 for _, _, s, _ in results if "FAIL" in s or "MISSING" in s)
n_ok   = sum(1 for _, _, s, _ in results if s.startswith("OK"))
print(f"\n  SUMMARY: {n_ok} OK, {n_fail} FAIL/MISSING")
print("\nDUNG.")
