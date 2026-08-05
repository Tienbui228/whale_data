"""Update CASE_TUT DAILY with Binance spot klines + DEX data for spot columns."""
import openpyxl
from openpyxl.styles import PatternFill, Font
from openpyxl.utils import get_column_letter

# Binance spot klines from probe (hardcoded from S2 table output)
# Format: date -> {vol_spot_usd, taker_spot_pct, spot_venue}
SPOT_DATA = {
    # Pre-campaign (01/07->08/07 — spot available, no perp in freshwatch)
    "2026-07-01": {"sv": 290000, "tk": 0.520, "src": "Binance_spot"},
    "2026-07-02": {"sv": 400000, "tk": 0.524, "src": "Binance_spot"},
    "2026-07-03": {"sv": 280000, "tk": 0.644, "src": "Binance_spot"},
    "2026-07-04": {"sv": 350000, "tk": 0.522, "src": "Binance_spot"},
    "2026-07-05": {"sv": 750000, "tk": 0.487, "src": "Binance_spot"},
    "2026-07-06": {"sv": 650000, "tk": 0.528, "src": "Binance_spot"},
    "2026-07-07": {"sv": 690000, "tk": 0.476, "src": "Binance_spot"},
    "2026-07-08": {"sv": 230000, "tk": 0.461, "src": "Binance_spot"},
    # Campaign window (from S2 table, Binance spot col)
    "2026-07-09": {"sv": 1020000, "tk": 0.548, "src": "Binance_spot"},
    "2026-07-10": {"sv": 440000, "tk": 0.570, "src": "Binance_spot"},
    "2026-07-11": {"sv": 2000000, "tk": 0.549, "src": "Binance_spot"},
    "2026-07-12": {"sv": 790000, "tk": 0.464, "src": "Binance_spot"},
    "2026-07-13": {"sv": 560000, "tk": 0.547, "src": "Binance_spot"},
    "2026-07-14": {"sv": 330000, "tk": 0.504, "src": "Binance_spot"},
    "2026-07-15": {"sv": 370000, "tk": 0.479, "src": "Binance_spot"},
    "2026-07-16": {"sv": 350000, "tk": 0.511, "src": "Binance_spot"},
    "2026-07-17": {"sv": 470000, "tk": 0.548, "src": "Binance_spot"},
    "2026-07-18": {"sv": 330000, "tk": 0.510, "src": "Binance_spot"},
    "2026-07-19": {"sv": 170000, "tk": 0.379, "src": "Binance_spot"},
    "2026-07-20": {"sv": 840000, "tk": 0.569, "src": "Binance_spot"},
    "2026-07-21": {"sv": 1650000, "tk": 0.518, "src": "Binance_spot"},
    "2026-07-22": {"sv": 930000, "tk": 0.523, "src": "Binance_spot"},
    "2026-07-23": {"sv": 360000, "tk": 0.441, "src": "Binance_spot"},
    "2026-07-24": {"sv": 410000, "tk": 0.491, "src": "Binance_spot"},
    "2026-07-25": {"sv": 640000, "tk": 0.510, "src": "Binance_spot"},
    "2026-07-26": {"sv": 370000, "tk": 0.492, "src": "Binance_spot"},
    "2026-07-27": {"sv": 500000, "tk": 0.497, "src": "Binance_spot"},
    "2026-07-28": {"sv": 750000, "tk": 0.578, "src": "Binance_spot"},
    "2026-07-29": {"sv": 740000, "tk": 0.502, "src": "Binance_spot"},
    "2026-07-30": {"sv": 350000, "tk": 0.466, "src": "Binance_spot"},
    "2026-07-31": {"sv": 780000, "tk": 0.442, "src": "Binance_spot"},
    "2026-08-01": {"sv": 2752516, "tk": 0.542, "src": "Binance_spot"},
    "2026-08-02": {"sv": 1019876, "tk": 0.540, "src": "Binance_spot"},
    "2026-08-03": {"sv": 5475175, "tk": 0.568, "src": "Binance_spot"},
    "2026-08-04": {"sv": 7156175, "tk": 0.509, "src": "Binance_spot"},
    "2026-08-05": {"sv": 1195520, "tk": 0.440, "src": "Binance_spot_partial"},
}

# DEX data (BSC TUT/WBNB, from S2 dex_bsc col)
DEX_DATA = {
    "2026-07-09": 40000, "2026-07-10": 30000, "2026-07-11": 300000,
    "2026-07-12": 240000, "2026-07-13": 50000, "2026-07-14": 20000,
    "2026-07-15": 30000, "2026-07-16": 30000, "2026-07-17": 40000,
    "2026-07-18": 30000, "2026-07-19": 10000, "2026-07-20": 100000,
    "2026-07-21": 250000, "2026-07-22": 100000, "2026-07-23": 60000,
    "2026-07-24": 40000, "2026-07-25": 90000, "2026-07-26": 90000,
    "2026-07-27": 100000, "2026-07-28": 180000, "2026-07-29": 120000,
    "2026-07-30": 70000, "2026-07-31": 180000,
    "2026-08-01": 513756, "2026-08-02": 144085, "2026-08-03": 736647,
    "2026-08-04": 1024660, "2026-08-05": 283632,
}

FNAME = "docs/case_files/CASE_TUT.xlsx"
wb = openpyxl.load_workbook(FNAME)
ws = wb["DAILY"]

# Find column indices from row 2
col_map = {}
for cell in ws[2]:
    if cell.value:
        col_map[cell.value] = cell.column

print("Column map (spot cols):")
spot_cols = ["spot_venue", "vol_spot_usd", "taker_spot_pct", "note_operator", "mm_note"]
for c in spot_cols:
    print(f"  {c}: col {col_map.get(c,'?')}")

# YELLOW fill
YELLOW_FILL = PatternFill("solid", fgColor="FFFF00")
ORANGE_FILL = PatternFill("solid", fgColor="FFC000")
RED_FILL = PatternFill("solid", fgColor="FF0000")
GREEN_FILL = PatternFill("solid", fgColor="E2EFDA")

# Update rows
updated = 0
for row in ws.iter_rows(min_row=3, max_row=ws.max_row, values_only=False):
    d_str = row[0].value
    if not d_str or not isinstance(d_str, str) or len(d_str) != 10:
        continue

    spot = SPOT_DATA.get(d_str)
    dex = DEX_DATA.get(d_str, 0)

    if spot:
        # spot_venue
        if "spot_venue" in col_map:
            ws.cell(row[0].row, col_map["spot_venue"], "Binance_spot+BSC_DEX")
        # vol_spot_usd = Binance spot + DEX
        if "vol_spot_usd" in col_map:
            total_sv = spot["sv"] + dex
            ws.cell(row[0].row, col_map["vol_spot_usd"], total_sv)
        # taker_spot_pct = Binance spot taker (DEX taker ABSTAIN)
        if "taker_spot_pct" in col_map:
            ws.cell(row[0].row, col_map["taker_spot_pct"]).value = spot["tk"]
            ws.cell(row[0].row, col_map["taker_spot_pct"]).number_format = "0.0%"
        # Update mm_note to reflect spot source
        if "mm_note" in col_map:
            cur = ws.cell(row[0].row, col_map["mm_note"]).value or ""
            if "Binance_spot" not in cur:
                ws.cell(row[0].row, col_map["mm_note"],
                        cur + "+spot_klines_Binance" if cur else "spot_klines_Binance")
        updated += 1

    # Also flag rows where taker_spot > 55% on large vol days (possible buy-dominated)
    if spot and spot["sv"] > 1000000 and spot["tk"] > 0.54:
        if "taker_spot_pct" in col_map:
            ws.cell(row[0].row, col_map["taker_spot_pct"]).fill = GREEN_FILL
    # Sell-dominated spot days (taker < 45%)
    if spot and spot["sv"] > 200000 and spot["tk"] < 0.45:
        if "taker_spot_pct" in col_map:
            ws.cell(row[0].row, col_map["taker_spot_pct"]).fill = ORANGE_FILL

print(f"\nUpdated {updated} rows with spot data")

# Add note in CASE sheet about Binance spot discovery
ws_case = wb["CASE"]
ws_case.append(["", ""])
ws_case.append(["S1 VENUE DISCOVERY (05/08)", "Binance spot TUTUSDT: LISTED! vol $0.23-7.16M/day. CoinGecko tickers: 24 markets (Gate/MEXC/LBank $16-84M — SUSPICIOUS wash). Alpha_117: 400 error (defunct)."])
ws_case.append(["venue_top", "Binance_spot_TUTUSDT (confirmed via api.binance.com)"])
ws_case.append(["spot_perp_ratio_campaign", "0.169x avg (Binance spot $30M + DEX $5M vs perp $207M)"])
ws_case.append(["taker_spot_avg", "50.8% (neutral — no clear distribution signal from taker alone)"])
ws_case.append(["cua_A_capacity_day", "$426k/day (30% of $1.42M avg spot)"])
ws_case.append(["cua_A_total_27d_max", "$11.5M possible spot distribution in 27 days (upper bound)"])
ws_case.append(["S3_verdict", "AMBIGUOUS: taker neutral, no DEX large sell pattern visible. On-chain balance PENDING."])

wb.save(FNAME)
print(f"Saved: {FNAME}")

# Summary stats
campaign_sv = [SPOT_DATA[d]["sv"] for d in SPOT_DATA if d >= "2026-07-09" and d <= "2026-08-04"]
if campaign_sv:
    print(f"\nBinance spot campaign summary (09/07->04/08):")
    print(f"  N days: {len(campaign_sv)}")
    print(f"  Total:  ${sum(campaign_sv):,.0f}")
    print(f"  Avg/d:  ${sum(campaign_sv)/len(campaign_sv):,.0f}")
    takers = [SPOT_DATA[d]["tk"] for d in SPOT_DATA if d >= "2026-07-09" and d <= "2026-08-04"]
    print(f"  Avg taker: {sum(takers)/len(takers):.1%}")
    # High-vol sell days
    sell_dom = [d for d in SPOT_DATA if d >= "2026-07-09" and d <= "2026-08-04" and SPOT_DATA[d]["tk"] < 0.45]
    buy_dom = [d for d in SPOT_DATA if d >= "2026-07-09" and d <= "2026-08-04" and SPOT_DATA[d]["tk"] > 0.55]
    print(f"  Sell-dominated days (<45%): {sell_dom}")
    print(f"  Buy-dominated days (>55%): {buy_dom}")
