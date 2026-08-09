"""
_probe_xpin_x0_read_20260808.py
X-0: Đọc trạng thái hiện tại CASE_XPIN.xlsx — paste nguyên trạng.
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
import openpyxl

ROOT     = Path(r"D:\Data back test\whale_data")
CASE_DIR = ROOT / "docs" / "case_files"
XPIN_XL  = CASE_DIR / "CASE_XPIN.xlsx"

def log(s=""): print(s)

log("=== X-0 READ CASE_XPIN.xlsx ===")
log(f"File: {XPIN_XL}")
log(f"Exists: {XPIN_XL.exists()}")
if not XPIN_XL.exists():
    log("ERROR: file not found"); sys.exit(1)

wb = openpyxl.load_workbook(str(XPIN_XL), data_only=True)
log(f"Sheets: {wb.sheetnames}")
log()

# ── CASE sheet ──────────────────────────────────────────────────────────────
log("=== CASE SHEET ===")
ws_case = wb["CASE"] if "CASE" in wb.sheetnames else None
if ws_case:
    for r in ws_case.iter_rows():
        parts = []
        for c in r:
            v = c.value
            if v is not None:
                parts.append(f"[{c.coordinate}] {repr(v)}")
        if parts:
            log("  " + " | ".join(parts))
else:
    log("  CASE sheet not found")

log()

# ── DAILY sheet ──────────────────────────────────────────────────────────────
log("=== DAILY SHEET ===")
ws_daily = wb["DAILY"] if "DAILY" in wb.sheetnames else None
if ws_daily:
    max_r = ws_daily.max_row
    max_c = ws_daily.max_column
    log(f"  max_row={max_r}  max_col={max_c}")

    # Header rows (rows 1-2)
    log("\n  --- Row 1 (group headers) ---")
    row1 = []
    for c in range(1, max_c + 1):
        v = ws_daily.cell(1, c).value
        if v is not None:
            row1.append(f"col{c}={repr(v)}")
    log("  " + " | ".join(row1) if row1 else "  (all None)")

    log("\n  --- Row 2 (field headers) ---")
    headers = []
    for c in range(1, max_c + 1):
        v = ws_daily.cell(2, c).value
        headers.append(str(v) if v is not None else f"COL{c}")
    log("  " + " | ".join(headers[:30]))
    if len(headers) > 30:
        log("  (continued) " + " | ".join(headers[30:]))
    log(f"\n  TOTAL COLUMNS: {len(headers)}")

    # Last 5 data rows
    log("\n  --- Last 5 data rows ---")
    data_rows = []
    for r in range(3, max_r + 1):
        row_vals = [ws_daily.cell(r, c).value for c in range(1, max_c + 1)]
        if any(v is not None for v in row_vals):
            data_rows.append((r, row_vals))

    log(f"  Total data rows: {len(data_rows)}")
    last5 = data_rows[-5:] if len(data_rows) >= 5 else data_rows
    for (ri, vals) in last5:
        non_none = [(headers[i] if i < len(headers) else f"c{i+1}", vals[i])
                    for i in range(len(vals)) if vals[i] is not None]
        log(f"\n  Row {ri}:")
        for k, v in non_none:
            log(f"    {k}: {repr(v)}")

    if data_rows:
        last_date_row = data_rows[-1]
        last_date = last_date_row[1][0]  # col 1 = date
        log(f"\n  LAST DATE: {last_date}")

    # Schema check — standard 50 cols
    STANDARD_50 = [
        "date","open","high","low","close","vol_quote_usd","taker_pct","ret_1d",
        "f_avg","f_min","f_max","f_n",
        "oi_usd","oi_token","oi_vs_med14","oi_cycle_pos",
        "lsr_pos_r","lsr_acc_r","lsr_global_r","taker_lsr",
        "div_raw","div_avg3","glsr_slope_5d","d_pos_3d","d_acc_3d",
        "gom_A","gom_B",
        "signals_bullish","signals_suppress","screen_rank",
        "data_bad",
        "vol_spot_usd","taker_spot_pct","spot_perp_ratio",
        "vol_alpha","taker_alpha",
        "alpha_suspect",
        "depth_bid2_usd","depth_ask2_usd","depth_ratio","ask_wall_usd",
        "exch_balance_delta","wallet_activity","dominance_pct",
        "note_operator","mm_note",
        "ret_7d","ret_30d","vol_vs_med14",
        "lsr_taker_r",
        "ret_atl",
    ]

    log("\n  --- Schema check vs standard 50 ---")
    present = set(h.lower().strip() for h in headers if h and not h.startswith("COL"))
    missing_cols = [c for c in STANDARD_50 if c not in present]
    extra_cols   = [h for h in headers if h and not h.startswith("COL")
                    and h.lower() not in STANDARD_50]
    log(f"  Columns present: {len([h for h in headers if not h.startswith('COL')])}")
    log(f"  Standard cols missing: {missing_cols}")
    log(f"  Extra cols (not in standard): {extra_cols}")
else:
    log("  DAILY sheet not found")

log()

# ── TRIGGERS sheet ──────────────────────────────────────────────────────────
log("=== TRIGGERS SHEET ===")
ws_trig = wb["TRIGGERS"] if "TRIGGERS" in wb.sheetnames else None
if ws_trig:
    for r in ws_trig.iter_rows():
        parts = []
        for c in r:
            v = c.value
            if v is not None:
                parts.append(f"[{c.coordinate}]{repr(v)}")
        if parts:
            log("  " + " | ".join(parts))
else:
    log("  TRIGGERS sheet not found")

log()

# ── EVENTS sheet last 10 ─────────────────────────────────────────────────────
log("=== EVENTS SHEET (last 10) ===")
ws_ev = wb["EVENTS"] if "EVENTS" in wb.sheetnames else None
if ws_ev:
    ev_max = ws_ev.max_row
    ev_hdr = [ws_ev.cell(1, c).value for c in range(1, ws_ev.max_column + 1)]
    log(f"  Headers: {ev_hdr}")
    ev_rows = []
    for r in range(2, ev_max + 1):
        vals = [ws_ev.cell(r, c).value for c in range(1, ws_ev.max_column + 1)]
        if any(v is not None for v in vals):
            ev_rows.append(vals)
    log(f"  Total event rows: {len(ev_rows)}")
    for vals in ev_rows[-10:]:
        log(f"  {vals}")
else:
    log("  EVENTS sheet not found")

log()

# ── Other sheets ─────────────────────────────────────────────────────────────
log("=== OTHER SHEETS ===")
for sname in wb.sheetnames:
    if sname not in ("CASE", "DAILY", "TRIGGERS", "EVENTS"):
        ws = wb[sname]
        log(f"  Sheet '{sname}': max_row={ws.max_row}, max_col={ws.max_column}")

log("\n=== X-0 READ DONE ===")
