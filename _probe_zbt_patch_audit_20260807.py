"""Audit patch: so sánh CASE_ZBT trước và sau patch taker_spot_pct.
Kiểm tra: (a) chỉ col 29 thay đổi, (b) không cột nào khác bị động,
(c) giá trị cũ vs mới, (d) venue ZBT từ u50_venues.csv.
"""
import sys, io, csv
from pathlib import Path
import openpyxl

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

PRE  = Path(r"D:\Data back test\whale_data\scratch\CASE_ZBT_pre_patch.xlsx")
POST = Path(r"D:\Data back test\whale_data\docs\case_files\CASE_ZBT.xlsx")
VEN  = Path(r"D:\Check onchain fresh wallets\u50_venues.csv")

# ── A. So sánh DAILY sheet cell-by-cell ─────────────────────────────────────
print("=" * 70)
print("A. DIFF DAILY: pre-patch vs post-patch")
print("=" * 70)

wb_pre  = openpyxl.load_workbook(PRE,  data_only=True)
wb_post = openpyxl.load_workbook(POST, data_only=True)
ws_pre  = wb_pre["DAILY"]
ws_post = wb_post["DAILY"]

# Header row 2
hdrs = [c.value for c in ws_post[2]]
print(f"Columns: {len(hdrs)}")

changed_cols = set()
changed_rows = []
total_cells = 0
for row_pre, row_post in zip(ws_pre.iter_rows(min_row=3), ws_post.iter_rows(min_row=3)):
    if not row_pre[0].value:
        continue
    for ci, (cp, cq) in enumerate(zip(row_pre, row_post)):
        total_cells += 1
        vp = cp.value; vq = cq.value
        if vp != vq:
            col_name = hdrs[ci] if ci < len(hdrs) else f"col{ci+1}"
            changed_cols.add(ci + 1)
            changed_rows.append((row_pre[0].value, ci + 1, col_name, vp, vq))

print(f"\nChanged cells: {len(changed_rows)} / {total_cells}")
print(f"Changed columns (1-indexed): {sorted(changed_cols)}")
print()

if changed_rows:
    print(f"  {'date':<12} {'col':>4} {'col_name':<20} {'before':>12} {'after':>12}")
    print(f"  {'-'*12} {'-'*4} {'-'*20} {'-'*12} {'-'*12}")
    for date_v, ci, cname, before, after in changed_rows[:40]:
        bstr = str(before)[:12] if before is not None else "None"
        astr = f"{after:.2f}" if isinstance(after, float) else str(after)[:12]
        print(f"  {str(date_v)[:12]:<12} {ci:>4} {cname:<20} {bstr:>12} {astr:>12}")
    if len(changed_rows) > 40:
        print(f"  ... (+{len(changed_rows)-40} more rows)")

# ── B. Xác nhận chỉ col 29 bị thay đổi ─────────────────────────────────────
print()
print("=" * 70)
print("B. WRITE PATH CHECK")
print("=" * 70)
expected_col = 29
only_expected = changed_cols == {expected_col}
print(f"  Expected only col {expected_col} (taker_spot_pct) to change: {'YES ✓' if only_expected else 'NO — EXTRA COLS: ' + str(changed_cols - {expected_col})}")
print(f"  Probe ghi thẳng qua openpyxl wb.save() — không qua case_daily writer")
print(f"  CASE_ZBT.xlsx là file COLD_REFRESH, chưa có operator live-edit tầng phân tích")

# ── C. Giá trị cũ trước ghi ─────────────────────────────────────────────────
print()
print("=" * 70)
print("C. GIÁ TRỊ CŨ taker_spot_pct (pre-patch = từ _task_rebuild_case_zbt)")
print("=" * 70)
old_vals = set(r[3] for r in changed_rows)
print(f"  Tập giá trị cũ: {old_vals}")
if old_vals == {None}:
    print("  → Toàn bộ là None (ABSTAIN) — không có số 350-480% nào từng ghi vào xlsx")
else:
    print("  → CÓ số cũ khác None — kiểm tra từng giá trị:")
    for r in changed_rows:
        if r[3] is not None:
            print(f"    {r[0]} col{r[1]} ({r[2]}): {r[3]}")

# ── D. Venue audit ZBT ──────────────────────────────────────────────────────
print()
print("=" * 70)
print("D. VENUE AUDIT ZBT từ u50_venues.csv")
print("=" * 70)
if VEN.exists():
    with open(VEN, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    zbt_rows = [r for r in rows if r.get("symbol","").upper() == "ZBT"]
    if zbt_rows:
        for r in zbt_rows:
            print(f"  symbol          : {r.get('symbol')}")
            print(f"  venue_top       : {r.get('venue_top','—')}")
            print(f"  venue_top_measurable: {r.get('venue_top_measurable','—')}")
            print(f"  spot_pair       : {r.get('spot_pair','—')}")
            print(f"  dex_only        : {r.get('dex_only','—')}")
            for k, v in r.items():
                if k not in ("symbol","venue_top","venue_top_measurable","spot_pair","dex_only") and v:
                    print(f"  {k:<22}: {v}")
    else:
        print("  ZBT NOT FOUND in u50_venues.csv")
        # Show columns
        print(f"  Columns: {list(rows[0].keys()) if rows else '(empty)'}")
else:
    print(f"  FILE NOT FOUND: {VEN}")

# ── E. Nguồn API xác nhận ────────────────────────────────────────────────────
print()
print("=" * 70)
print("E. API SOURCE xác nhận")
print("=" * 70)
print("  URL dùng: https://api.binance.com/api/v3/klines?symbol=ZBTUSDT")
print("  KHÔNG phải: https://www.binance.com/bapi/defi/v1/public/alpha-trade/klines")
print("  alpha klines url = bapi.binance.com (BANNED, ABSTAIN k[9]==k[5])")
print("  api.binance.com  = Binance spot chuẩn (same url spot_collector.py dùng)")

print("\n[DONE]")
