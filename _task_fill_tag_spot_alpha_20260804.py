#!/usr/bin/env python3
"""Task: Fill CASE_TAG.xlsx DAILY — spot_venue + vol_spot_usd + taker_spot_pct + alpha_suspect formula.

Source: data/raw/spot_klines_1d (venue=binance_alpha, symbol=TAG)
Fills: col AA (spot_venue), AB (vol_spot_usd), AC (taker_spot_pct=ABSTAIN)
Adds:  col AJ (alpha_suspect) formula for rows 34-36 (already present 3-33)
Skips: AD-AI (depth/walls — not in store, leave empty)
"""
import io, sys
from pathlib import Path
import pandas as pd
import openpyxl

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

XLSX  = Path(r"D:\Data back test\whale_data\docs\case_files\CASE_TAG.xlsx")
STORE = Path(r"D:\Data back test\whale_data\data\raw\spot_klines_1d")

# ── Load alpha store for TAG ──────────────────────────────────────────────────
alpha = {}
for p in sorted(STORE.glob("date=2026-*")):
    files = list(p.glob("*.parquet"))
    if not files:
        continue
    try:
        df = pd.read_parquet(files[0])
        tag = df[df['symbol'] == 'TAG'] if 'symbol' in df.columns else pd.DataFrame()
        if len(tag):
            row = tag.iloc[0]
            qv = row.get('quote_vol', None)
            alpha[p.name.replace("date=", "")] = float(qv) if pd.notna(qv) else None
    except:
        pass

print(f"Alpha dates loaded: {len(alpha)}")
print(f"Range: {min(alpha)} → {max(alpha)}")
print(f"Sample last 5: { {d: alpha[d] for d in sorted(alpha)[-5:]} }")

# ── Open XLSX ─────────────────────────────────────────────────────────────────
wb = openpyxl.load_workbook(XLSX)
ws = wb["DAILY"]

print(f"\nDAILY max_row={ws.max_row}, scanning rows 3-{ws.max_row}...")

# Column mapping (verified from probe):
# AA=27: spot_venue  AB=28: vol_spot_usd  AC=29: taker_spot_pct
# AJ=36: alpha_suspect

filled = 0
skipped_no_data = 0
skipped_exists = 0

for r in range(3, ws.max_row + 1):
    date_val = ws.cell(r, 1).value
    if not date_val or not str(date_val).startswith("2026"):
        continue

    date_str = str(date_val)
    qv = alpha.get(date_str)

    # AA: spot_venue
    if ws.cell(r, 27).value is None:
        ws.cell(r, 27, "binance_alpha")
    else:
        skipped_exists += 1

    # AB: vol_spot_usd (alpha quote vol in USD)
    if ws.cell(r, 28).value is None:
        if qv is not None:
            ws.cell(r, 28, round(qv, 2))
        # leave empty if no data

    # AC: taker_spot_pct — ABSTAIN for all alpha rows (taker field broken)
    if ws.cell(r, 29).value is None:
        ws.cell(r, 29, "ABSTAIN")

    # AJ: alpha_suspect formula — add if missing
    if ws.cell(r, 36).value is None:
        ws.cell(r, 36, f"=IF(OR(AB{r}=\"\",AB{r}=0,D{r}=\"\",D{r}=0),\"\",AB{r}/D{r})")

    qv_str = f"{qv:.0f}" if qv else "no_data"
    print(f"  {date_str} row {r}: alpha_vol={qv_str} USD")
    filled += 1

print(f"\nFilled: {filled} rows, skipped_exists: {skipped_exists}")

wb.save(XLSX)
print(f"Saved: {XLSX}")
