"""
_task_ain_index_log_20260813.py
Update CASE_INDEX + INDEX.md + agent_log + TASKS.md cho AIN cold-start.
"""
import sys, io, shutil
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
from datetime import datetime, timezone
import openpyxl

ROOT = Path(r"D:\Data back test\whale_data")
NOW  = datetime.now(timezone.utc)

# ── 1. CASE_INDEX.xlsx ────────────────────────────────────────────────────
index_path = ROOT / "docs" / "case_files" / "CASE_INDEX.xlsx"
bkp = ROOT / "scratch" / f"CASE_INDEX_bak_ain_{NOW.strftime('%Y%m%d_%H%M')}.xlsx"
shutil.copy2(index_path, bkp)
print(f"Backup: {bkp.name}")

wb = openpyxl.load_workbook(index_path)
ws = wb["INDEX"]

for r in ws.iter_rows(values_only=True):
    if r[1] == "AIN":
        print("AIN already in INDEX — skip insert")
        break
else:
    max_row = ws.max_row
    next_row = max_row + 1
    ws.cell(next_row, 1, "CASE_AIN.xlsx")
    ws.cell(next_row, 2, "AIN")
    ws.cell(next_row, 3, "COLD_START — PENDING")
    ws.cell(next_row, 4, "Deposit intel: 30M token ≈ $2.4M từ 04/08. GOM-D 4/4 PASS, GOM-E PASS 29d hedge. Taxonomy BLEED. Blockchain UNKNOWN. Gate thin $78K/d. CẦN OPERATOR on-chain.")
    ws.cell(next_row, 5, "COLD_START")
    ws.cell(next_row, 6, "2026-08-13")
    ws.cell(next_row, 7, None)
    ws.cell(next_row, 8, None)
    ws.cell(next_row, 9, None)
    ws.cell(next_row, 10, None)
    ws.cell(next_row, 11, "AI narrative | chain UNKNOWN | collect 13/08/2026 | on-chain CẦN OPERATOR")
    print(f"Added AIN at row {next_row}")

wb.save(index_path)
print(f"CASE_INDEX saved")

# ── 2. INDEX.md ───────────────────────────────────────────────────────────
idx_md = ROOT / "docs" / "INDEX.md"
if idx_md.exists():
    txt = idx_md.read_text(encoding="utf-8")
    if "CASE_AIN" not in txt:
        insert_line = "| CASE_AIN.xlsx | AIN | COLD_START — PENDING | Deposit 30M token 04/08, GOM-E 29d, blockchain UNKNOWN. Collect 13/08 |"
        for marker in ["CASE_CYS", "CASE_TST"]:
            if marker in txt:
                txt = txt.replace(f"| {marker}", insert_line + f"\n| {marker}", 1)
                idx_md.write_text(txt, encoding="utf-8")
                print(f"INDEX.md updated with AIN row (before {marker})")
                break
        else:
            print("WARN: marker not found — AIN not appended to INDEX.md")
    else:
        print("CASE_AIN already in INDEX.md")
else:
    print("WARN: INDEX.md not found")

# ── 3. agent_log.md ───────────────────────────────────────────────────────
log_path = ROOT / "agent_log.md"
entry = f"""
---

## AIN COLLECT — CASE_AIN.xlsx COLD_START — {NOW.strftime('%Y-%m-%d %H:%M UTC')}

**Scope:** Full collect AINUSDT: AI-0→AI-8, tạo CASE_AIN.xlsx (224 rows, 7 sheets).
**Intel operator:** 30M token ≈ $2.4M nạp từ 04/08.
**Output:** _collect_ain_20260813.md | CASE_AIN.xlsx

### Data collected
- fapi klines 1d: 224 rows (Jan01-Aug12 2026)
- fapi funding: 1344 entries full history
- fapi LSR 4 endpoints: 30 rows Jul19-Aug17
- freshwatch merge: 49 dates total LSR
- OI hist 30d: 25 rows Jul19-Aug17
- OI snapshot: 59,692,669 tokens ≈ $4.51M
- BAPI alpha list: AIN NOT FOUND (perp only, no alpha token)
- Gate.io: vol24h=$78,181 (thin primary spot)
- GeckoTerminal: ~$44K fragmented multi-pool

### Key findings
- AI-0: AINUSDT perp onboard 2025-07-10. Binance spot ABSENT. Chain UNKNOWN.
- AI-2: ATH=$0.13472 May13. ATL=$0.02877 Feb08. PROVEN_PUMP=NO.
- AI-2 Events: 18 events vol≥8×med14. 4 major cụm: Mar10-18, Apr11-13, May13-14, Jun11-14.
- AI-3: Deposit window Aug04-12: BLEED taxonomy. 6/9 đỏ. Net +11%. OI +$621K.
- AI-3: gLSR đỉnh 3.819 Aug07, hạ về 2.271 Aug12 — retail rút sau spike.
- AI-4 Vân1: pos_r 1.45-1.68, RETAIL-FOLLOW, KHÔNG inverso.
- AI-4 Vân2: 29d hedge ongoing (Jul15-Aug12, div_avg3=0.658 avg). GOM-E PASS.
- AI-4 Vân3: 14/47=30% dip recovery (low). 3d=81%.
- AI-4 Vân4: blockchain UNKNOWN. Gate $78K/d = 29 ngày exit. Depth $591/$421 CRITICAL.
- AI-5 GOM-D: 4/4 PASS (D1/D3/D4/D5). Nhưng mỗi cluster có dump ngay sau.
- AI-5 GOM-E: PASS (29d). Funding positive → retail long trả phí cho short side.
- AI-6: gLSR mean 2.705, ≥2.0 trong 40 ngày — retail long dominant.
- AI-7: Depth/OI=0.0225% EXTREME THIN. Không exit được 30M via perp.
- AI-8: 5/5 SANITY PASS.

### Verdict thu thập (không phán)
Tín hiệu MIXED: GOM-E PASS (hedge-farm có cấu trúc) nhưng pos_r không inverso.
Deposit BLEED + depth cực mỏng + chain UNKNOWN → CẦN OPERATOR.

**CẦN OPERATOR: (1) blockchain AIN + vesting schedule; (2) wallet 30M token; (3) verdict ô A/B/C/D.**
**DỪNG CHỜ OPERATOR ĐỌC _collect_ain_20260813.md.**
"""
with open(log_path, "a", encoding="utf-8") as f:
    f.write(entry)
print(f"agent_log appended ({len(entry)} chars)")

# ── 4. TASKS.md ───────────────────────────────────────────────────────────
tasks_path = ROOT / "docs" / "TASKS.md"
txt = tasks_path.read_text(encoding="utf-8")

# Update CASE-AKE from QUEUED to DOING
old = "| CASE-AKE | - | CASE_AKE tạo + cold start pack (AKE chưa có file) | QUEUED |"
new = "| CASE-AIN | 13/08 | CASE_AIN.xlsx COLD_START AI-0→AI-8 (224 rows). Intel: 30M token nạp từ 04/08. GOM-D 4/4, GOM-E 29d. Taxonomy BLEED. Chain UNKNOWN. CẦN OPERATOR on-chain. | DOING — _collect_ain_20260813.md sẵn sàng |"

if "CASE-AIN" not in txt:
    # Insert new CASE-AIN row before CASE-AKE
    if old in txt:
        txt = txt.replace(old, new + "\n" + old)
        print("TASKS.md: added CASE-AIN row")
    else:
        # append before last line
        lines = txt.rstrip().split("\n")
        lines.append(new)
        txt = "\n".join(lines) + "\n"
        print("TASKS.md: appended CASE-AIN row at end")
else:
    print("TASKS.md: CASE-AIN already present")

tasks_path.write_text(txt, encoding="utf-8")
print("TASKS.md saved")

print("[DONE]")
