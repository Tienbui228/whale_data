"""
_task_cys_index_log_20260813.py
Update CASE_INDEX + append agent_log + update TASKS.md cho CYS collect.
"""
import sys, io, shutil
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
from datetime import datetime, timezone
import openpyxl

ROOT = Path(r"D:\Data back test\whale_data")
NOW  = datetime.now(timezone.utc)

# ── 1. CASE_INDEX update ──────────────────────────────────────────────────────
index_path = ROOT / "docs" / "case_files" / "CASE_INDEX.xlsx"
bkp = ROOT / "scratch" / f"CASE_INDEX_bak_cys_{NOW.strftime('%Y%m%d_%H%M')}.xlsx"
shutil.copy2(index_path, bkp)
print(f"Backup: {bkp.name}")

wb = openpyxl.load_workbook(index_path)
ws = wb["INDEX"]

# Find last row
max_row = ws.max_row
# Check if CYS already exists
for r in ws.iter_rows(values_only=True):
    if r[1] == "CYS":
        print("CYS already in INDEX — skip insert")
        break
else:
    # Insert new row after header rows (find first data row position)
    # Header rows = row1 (title), row2 (subtitle), row3 (first data = TST), row4 (col headers)
    # Insert as a new data row at the end
    next_row = max_row + 1
    ws.cell(next_row, 1, "CASE_CYS.xlsx")
    ws.cell(next_row, 2, "CYS")
    ws.cell(next_row, 3, "COLD_START — PENDING")
    ws.cell(next_row, 4, "GOM audit: gom thật vs staged-pump. Short squeeze Aug04-12 (+438% từ Jun trough). 4 vân: pos_r GIẢM, hedge Jul, squeeze Aug05. CẦN on-chain Solana.")
    ws.cell(next_row, 5, "COLD_START")
    ws.cell(next_row, 6, "2026-08-13")
    ws.cell(next_row, 7, None)  # T0
    ws.cell(next_row, 8, None)  # moc_ke_tiep
    ws.cell(next_row, 9, None)  # han
    ws.cell(next_row, 10, None) # MM_ID
    ws.cell(next_row, 11, "ALPHA_495 | Solana | collect 13/08/2026 | on-chain CẦN OPERATOR")
    print(f"Added CYS at row {next_row}")

wb.save(index_path)
print(f"CASE_INDEX saved: {index_path.name}")

# ── 2. INDEX.md update ───────────────────────────────────────────────────────
idx_md = ROOT / "docs" / "INDEX.md"
if idx_md.exists():
    txt = idx_md.read_text(encoding="utf-8")
    if "CASE_CYS" not in txt:
        # Find case_files section and append
        marker = "CASE_TST"
        if marker in txt:
            insert_line = "| CASE_CYS.xlsx | CYS | COLD_START — PENDING | GOM audit: gom thật vs staged-pump. Solana. Collect 13/08 |"
            txt = txt.replace("| CASE_TST", insert_line + "\n| CASE_TST", 1)
            idx_md.write_text(txt, encoding="utf-8")
            print("INDEX.md updated with CYS row")
        else:
            print("WARN: CASE_TST marker not found in INDEX.md — CYS not appended")
    else:
        print("CASE_CYS already in INDEX.md")
else:
    print("WARN: INDEX.md not found")

# ── 3. agent_log append ──────────────────────────────────────────────────────
log_path = ROOT / "agent_log.md"
entry = f"""
---

## CYS COLLECT — CASE_CYS.xlsx COLD_START — {NOW.strftime('%Y-%m-%d %H:%M UTC')}

**Scope:** Full collect CYSUSDT: C-0→C-8, tạo CASE_CYS.xlsx (224 rows, 7 sheets).
**Output:** _collect_cys_20260813.md | CASE_CYS.xlsx

### Data collected
- fapi klines 1d: 224 rows (Jan01-Aug12 2026)
- fapi funding: 1344 entries = full history Jan01-Aug12
- fapi LSR 4 endpoints: 30 rows Jul15-Aug12
- freshwatch merge: +43 rows Jun01-Jul14 → total LSR 73 dates
- OI hist 30d: Jul15-Aug12
- BAPI identity: ALPHA_495 (not in current bapi list — perp only)
- Gate.io spot: CYS_USDT $9.75M vol24h (PRIMARY SPOT)
- GeckoTerminal: CYS on Solana (CYS/USDC $346K vol24)

### Key findings
- C-0: CYSUSDT perp onboard 2025-12-12, Solana chain, Gate.io primary spot, Binance spot ABSENT
- C-0 Alert: GOM-C fire confirmed Aug07 (cùng COOKIE, gate 15/08 pending) — stateless, VWAP=N/A
- C-2: ATH=$1.6751 Aug12. Pre-Aug ATH=$0.715 Mar23. Events: 10× vol≥8× med14 (3 Jan/Mar clusters + 7 Aug)
- C-3 Vân1: pos_r −63.5% Jun→Aug12. Pump Aug05: acc_r 1.685→0.383 (short cover/liquidation). KHÔNG leo bậc.
- C-3 Vân2: Funding mostly neutral-pin. Jul02-18: 17d div<1 (hedge). Neg funding: Mar25/26 + Aug05/08/09 (squeeze).
- C-3 Vân3: Dip recovery 49% (ngẫu nhiên). Range Jun-Aug03 70% (không kiểm soát).
- C-3 Vân4: Solana on-chain MISSING. Proxy: hedge Jul02-18, un-hedge Jul19. Ô quyết định: C/D.
- C-4 Kính1: GOM-C PROVISIONAL Aug07. OI: $12.2M(Jun01)→$7.1M(Aug03)→$23.1M(Aug06). Net +$10.37M Jul15-Aug12.
- C-4 Kính2: GOM-D: D1 FAIL, D3 PASS(4 clusters), D4 PASS(10 wake), D5 PASS(6 churn). GOM-E: hedge Jul02-18.
- C-5: Aug04: gLSR=2.008 (retail peak long) → Aug05-12: gLSR=0.46-0.68 (retail SHORT). SHORT SQUEEZE màn-đặc-biệt.
- C-6: Perp depth ±2% = $379 bid/$128 ask với OI $30M → Depth/OI=0.001% → CỰC MỎ, flag wash candidate.
- C-7: 5/5 SANITY PASS (224 rows, 0 gaps, 0 neg close, ATH verified, taker in range)
- C-8: CASE_CYS.xlsx COLD_START, CASE_INDEX updated, INDEX.md updated

### Verdict thu thập (không phán)
Bằng chứng thiên về STAGED-PUMP (ô D): pos_r giảm, short squeeze cơ chế, OI expand từ FOMO.
On-chain Solana MISSING → chờ operator xác nhận.

**DỪNG CHỜ OPERATOR ĐỌC _collect_cys_20260813.md.**
"""
with open(log_path, "a", encoding="utf-8") as f:
    f.write(entry)
print(f"agent_log appended ({len(entry)} chars)")
print("[DONE]")
