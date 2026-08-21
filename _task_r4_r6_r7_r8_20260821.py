"""_task_r4_r6_r7_r8_20260821.py
R4: Schema v1→v2.1 BANK/TUT (append o/h/l/c + vol_alpha, cols 51-52 spot-ext);
    BTW/CYS: append cols 51-52.
R6: TUT paste close 08/08 + 20/08 in evidence.
R7: LAYER COVERAGE vào CASE meta mỗi file.
R8: CORRECTIONS append.
"""
import sys, io, pickle, shutil
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
import openpyxl

ROOT = Path(r"D:\Data back test\whale_data")
SCRATCH = ROOT / "scratch"
CASES = ROOT / "docs" / "case_files"

with open(SCRATCH / "r_nhip1_fetch_20260821.pkl", "rb") as f:
    ALL = pickle.load(f)

# Backup pre-R4
for sym in ["BANK","TUT","BTW","CYS"]:
    src = CASES / f"CASE_{sym}.xlsx"
    dst = SCRATCH / f"CASE_{sym}_bak_pre_r4_20260821.xlsx"
    if src.exists():
        shutil.copy2(src, dst)
print(f"Backups pre-R4 saved to scratch")

# ── R4 for BANK/TUT (v1 append o/h/l/c/vol_alpha/cols 51-52) ──
def upgrade_v1(sym):
    fp = CASES / f"CASE_{sym}.xlsx"
    wb = openpyxl.load_workbook(fp)
    ws = wb["DAILY"]
    row2 = [c.value for c in ws[2]]
    ci = {str(n).strip(): i+1 for i, n in enumerate(row2) if n}
    print(f"\n[{sym}] v1 pre-R4: {len(row2)} cols")

    # Add cols 42-52
    # Section header row 1: SPOT-EXT amendment
    # Row 2 field names:
    NEW_COLS = [
        (42, "OHLC-append (R4)", "o"),
        (43, "", "h"),
        (44, "", "l"),
        (45, "", "c"),
        (46, "vol_alpha-append (R4)", "vol_alpha"),
        (47, "", "taker_alpha"),
        (48, "reserved", ""),
        (49, "reserved", ""),
        (50, "reserved", ""),
        (51, "SPOT-EXT (v2.1 R4 21/08)", "vol_spot_ext_usd"),
        (52, "", "spot_ext_venue"),
    ]
    for c_idx, sec, field in NEW_COLS:
        if sec: ws.cell(1, c_idx).value = sec
        ws.cell(2, c_idx).value = field
    print(f"  Added cols 42-52 (schema v2.1 partial migration)")

    # Populate o/h/l/c + vol_alpha placeholder + cols 51-52 CHƯA-TRA (nhịp 2 pending)
    d = ALL[sym]
    n_rows_written = 0
    for r in range(3, ws.max_row + 1):
        dd = ws.cell(r, 1).value
        if not dd: continue
        d_str = str(dd)[:10]
        klines = d["klines"].get(d_str)
        if klines:
            ws.cell(r, 42).value = klines["o"]
            ws.cell(r, 43).value = klines["h"]
            ws.cell(r, 44).value = klines["l"]
            ws.cell(r, 45).value = klines["c"]
            n_rows_written += 1
        # Placeholders for nhịp 2
        ws.cell(r, 46).value = "CHƯA-TRA"      # vol_alpha
        ws.cell(r, 47).value = "ABSTAIN-STRUCTURAL"  # taker_alpha
        ws.cell(r, 51).value = "CHƯA-TRA"      # vol_spot_ext_usd
        ws.cell(r, 52).value = "CHƯA-TRA"      # spot_ext_venue
    print(f"  Wrote o/h/l/c: {n_rows_written} rows")

    # CASE meta append LAYER COVERAGE + CORRECTIONS
    ws_case = wb["CASE"]
    start_row = ws_case.max_row + 2  # gap 1 blank row
    ws_case.cell(start_row, 1).value = f"LAYER COVERAGE (R7 21/08)"
    layer_info = compute_layer_coverage(d, sym)
    for i, (k, v) in enumerate(layer_info, start=1):
        ws_case.cell(start_row+i, 1).value = k
        ws_case.cell(start_row+i, 2).value = v
    corr_row = start_row + len(layer_info) + 2
    ws_case.cell(corr_row, 1).value = "CORRECTIONS (R8 21/08)"
    ws_case.cell(corr_row+1, 1).value = "Gap 24-26/07 nguồn store"
    ws_case.cell(corr_row+1, 2).value = "3 ngày freshwatch drop toàn universe (họ TUT+BTW) — không sửa lịch sử"
    ws_case.cell(corr_row+2, 1).value = "Schema-migration R4 v2.1 partial"
    ws_case.cell(corr_row+2, 2).value = ("cols 42-45 = o/h/l/c append (append-only per L-57 R4) · "
                                          "cols 46-47 = vol_alpha/taker_alpha CHƯA-TRA (chờ nhịp 2 R5) · "
                                          "cols 51-52 = vol_spot_ext_usd/spot_ext_venue CHƯA-TRA (chờ nhịp 2 R5) · "
                                          "cols 48-50 reserved. Cột v1 cũ (1-41) KHÔNG đè.")
    print(f"  CASE meta: LAYER COVERAGE + CORRECTIONS appended (rows {start_row}-{corr_row+2})")

    wb.save(fp)
    print(f"  SAVED")
    return True

# ── R4 for BTW/CYS (v2 append cols 51-52 only) ──
def upgrade_v2(sym):
    fp = CASES / f"CASE_{sym}.xlsx"
    wb = openpyxl.load_workbook(fp)
    ws = wb["DAILY"]
    row2 = [c.value for c in ws[2]]
    ci = {str(n).strip(): i+1 for i, n in enumerate(row2) if n}
    print(f"\n[{sym}] v2 pre-R4: {len(row2)} cols")

    if "vol_spot_ext_usd" in ci and "spot_ext_venue" in ci:
        print(f"  Already has cols 51-52. Skip append.")
    else:
        ws.cell(1, 51).value = "SPOT-EXT (v2.1 R4 21/08)"
        ws.cell(2, 51).value = "vol_spot_ext_usd"
        ws.cell(2, 52).value = "spot_ext_venue"
        for r in range(3, ws.max_row + 1):
            if ws.cell(r, 1).value:
                ws.cell(r, 51).value = "CHƯA-TRA"
                ws.cell(r, 52).value = "CHƯA-TRA"
        print(f"  Added cols 51-52 · rows tagged CHƯA-TRA (chờ nhịp 2)")

    # CASE meta append
    ws_case = wb["CASE"]
    start_row = ws_case.max_row + 2
    ws_case.cell(start_row, 1).value = f"LAYER COVERAGE (R7 21/08)"
    d = ALL[sym]
    layer_info = compute_layer_coverage(d, sym)
    for i, (k, v) in enumerate(layer_info, start=1):
        ws_case.cell(start_row+i, 1).value = k
        ws_case.cell(start_row+i, 2).value = v
    corr_row = start_row + len(layer_info) + 2
    ws_case.cell(corr_row, 1).value = "CORRECTIONS (R8 21/08)"
    ws_case.cell(corr_row+1, 1).value = "Gap 24-26/07 nguồn store"
    ws_case.cell(corr_row+1, 2).value = "3 ngày freshwatch drop toàn universe — không sửa lịch sử"
    ws_case.cell(corr_row+2, 1).value = "Schema v2.1 append cols 51-52"
    ws_case.cell(corr_row+2, 2).value = "vol_spot_ext_usd + spot_ext_venue = CHƯA-TRA · chờ nhịp 2 R5"

    wb.save(fp)
    print(f"  SAVED")
    return True

def compute_layer_coverage(d, sym):
    lsr_dates = sorted(d["lsr"].keys())
    oi_dates = sorted(d["oi"].keys())
    fw_first = lsr_dates[0] if lsr_dates else "N/A"
    oi_first = oi_dates[0] if oi_dates else "N/A"
    # Common gaps
    gap_dates = ["2026-07-24", "2026-07-25", "2026-07-26"]
    if sym == "BANK": gap_dates.append("2026-07-28")
    if sym == "TUT": gap_dates.append("2026-08-05")
    if sym == "BTW": gap_dates.extend(["2026-08-08", "2026-08-09"])
    return [
        ("first_nn LSR (freshwatch)", fw_first),
        ("first_nn OI (fapi 30d)", oi_first),
        (f"N/A-GAP dates (freshwatch)", ", ".join(gap_dates)),
        ("N/A-RETENTION rule", "Trước first_nn = N/A-RETENTION (store không cover, không collect)"),
    ]

# ── RUN R4 ──
print("="*70)
print("R4 SCHEMA MIGRATION")
print("="*70)
upgrade_v1("BANK")
upgrade_v1("TUT")
upgrade_v2("BTW")
upgrade_v2("CYS")

# ── R6 TUT close 08/08 + 20/08 paste ──
print("\n" + "="*70)
print("R6 TUT close 2026-08-08 + 2026-08-20 [DATA]")
print("="*70)
wb = openpyxl.load_workbook(CASES / "CASE_TUT.xlsx", data_only=True)
ws = wb["DAILY"]
# After R4, col 45 = c (append)
c_col = 45  # per R4 upgrade_v1
for target in ["2026-08-08", "2026-08-20"]:
    for r in range(3, ws.max_row+1):
        d = ws.cell(r, 1).value
        if d and str(d)[:10] == target:
            c_val = ws.cell(r, c_col).value
            print(f"  {target}: close (col 45) = {c_val}")
            break
    else:
        print(f"  {target}: DAILY row not found")

print("\n[DONE R4+R6+R7+R8]")
