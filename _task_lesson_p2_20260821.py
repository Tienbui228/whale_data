"""_task_lesson_p2_20260821.py — P0 audit part 2:
1. UPDATE L-51 (row 54) → Step-0 token-identity (post-SUPERFORTUNE fix)
   Old content (GOM-C C1 spec) archived in commit message
2. INSERT L-48-AMD row → Amendment L-48 (19/08) nguyên văn operator + N=88 Alpha-only
3. Regen md via scripts/_task_regen_lessons.py

Backup already: scratch/CASE_INDEX_bak_pre_lesson_insert_20260821.xlsx
Additional backup here (P2 delta):
"""
import sys, io, shutil
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
import openpyxl

XLSX = Path(r"D:\Data back test\whale_data\docs\case_files\CASE_INDEX.xlsx")
BAK_P2 = Path(r"D:\Data back test\whale_data\scratch\CASE_INDEX_bak_pre_p2_20260821.xlsx")

# Backup P2
shutil.copy2(XLSX, BAK_P2)
print(f"Backup P2: {BAK_P2}")

wb = openpyxl.load_workbook(XLSX)
ws = wb["LESSONS"]

# ── 1. UPDATE L-51 row 54 → Step-0 token-identity ──
old_L51_bai_hoc = ws.cell(54, 4).value
print(f"\n[L-51 OVERWRITE — old content archived in commit]")
print(f"  OLD bai_hoc: {old_L51_bai_hoc[:100]}...")

ws.cell(54, 2).value = "2026-08-19"
ws.cell(54, 3).value = "GUA (SUPERFORTUNE án F1-F7 19/08) + toàn hệ"
ws.cell(54, 4).value = (
    "Step-0 token-identity discipline (một-thứ-hai-tên) — trước khi dùng BẤT KỲ data từ venue nào, "
    "phải verify identity bằng 4 bước: "
    "(1) Contract canonical PHẢI từ operator-niêm (tracker-relayed 0x + chain) — cấm symbol-string lookup "
    "(bài F1 GUA: bapi trả contract khớp SUPERFORTUNE nhưng chưa đảm bảo là token operator target). "
    "(2) Bit-level compare bapi/venue contract vs operator contract (lowercase) — identical mới confirmed. "
    "(3) Price-band check: klines venue vs klines perp ±20% (tolerance rộng cho illiquid Alpha). Ngoài band = FALSE-VENUE. "
    "(4) Van flag deposit/withdraw per chain — LOCKED chain = ISOLATED, không đếm băng-thông xả. "
    "Bằng chứng F1-F7: bapi ALPHA_483 SUPERFORTUNE contract 0xa5c8e15... — CẦN operator 0x mới quyết True/False venue. "
    "Áp dụng: TRIA (Bybit), STBL (Gate+MEXC+KuCoin+Alpha), HEMI (Gate+MEXC, Alpha delisted), PUMPBTC (MEXC+Gate+Bitget, verified 20/08). "
    "Old L-51 content (GOM-C C1 spec drift 11/08) archived in git history — canonical L-51 từ nay = Step-0 identity discipline."
)
ws.cell(54, 5).value = "IDENTITY"
ws.cell(54, 6).value = "DA VAO — spec + code hoá bắt buộc (đang chờ collector Step-0 assert)"
ws.cell(54, 7).value = (
    "Case-open mọi token mới: Step-0 (contract canonical operator) TRƯỚC data load. "
    "Collector code: add contract_canonical field + assert bit-eq trước fetch/store. "
    "Amendment cho tất cả CASE files: cột `contract_canonical` (row 7 CASE meta). "
    "Ref: docs/reports/_gua_identity_forensics_20260819.md §F6 schema v2.1-ext"
)
ws.cell(54, 8).value = "F1-20260819"
print(f"  NEW L-51: IDENTITY / Step-0 token-identity (post-SUPERFORTUNE)")

# ── 2. INSERT L-48-AMD row (next available row) ──
# Find first empty row
next_r = ws.max_row + 1
for r in range(ws.max_row, 4, -1):
    if ws.cell(r, 1).value:
        next_r = r + 1
        break
print(f"\n[L-48-AMD insert at row {next_r}]")

ws.cell(next_r, 1).value = "L-48-AMD"
ws.cell(next_r, 2).value = "2026-08-19"
ws.cell(next_r, 3).value = "Amendment L-48 (ref L-48 fullyDelisted) — token Alpha-only cross fw-139 × Binance spot"
ws.cell(next_r, 4).value = (
    "Amendment L-48 (19/08) NGUYÊN VĂN operator: "
    "'phạm vi mở rộng — token Alpha-only (danh sách N token theo probe cross exchangeInfo 18/08): "
    "taker_spot_pct và taker_alpha = ABSTAIN-STRUCTURAL (không phải data-gap) · "
    "vol_spot_usd = N/A-STRUCTURAL · số Alpha chỉ ở vol_alpha.' "
    "N COUNT (nợ 18/08, trả 21/08 probe _probe_alpha_only_N_20260821): "
    "N = 88 tokens Alpha-only / fw-139 tổng 139 tokens (51 có Binance spot pair). "
    "Danh sách 88 token snapshot 21/08: scratch/alpha_only_fw139_20260821.csv. "
    "Bao gồm các case đang mở: AGT, AIN, APR, BR, BTW, CLO, CYS, GUA, HEMI, IDOL, KOMA, ON, "
    "PUMPBTC, STBL, TAG, TRIA, XPIN (17/17 case active KHÔNG có Binance spot pair — toàn Alpha-only)."
)
ws.cell(next_r, 5).value = "AMENDMENT"
ws.cell(next_r, 6).value = "DA VAO — 21/08 (nguyên văn operator + N count trả nợ)"
ws.cell(next_r, 7).value = (
    "Mọi case Alpha-only từ nay MẶC ĐỊNH tag: vol_spot_usd=N/A-STRUCTURAL · "
    "taker_spot_pct/taker_alpha=ABSTAIN-STRUCTURAL · vol chỉ điền vol_alpha (col 35). "
    "Universe cross-check chạy lại khi Binance list token mới (delta 51→N reassess). "
    "Ref: probe scratch/alpha_only_fw139_20260821.csv, canonical N snapshot 21/08."
)
ws.cell(next_r, 8).value = "AMEND-L48-20260819"
print(f"  L-48-AMD inserted at row {next_r} with N=88 evidence")

wb.save(XLSX)
print(f"\nSAVED: {XLSX}")

# Verify
wb2 = openpyxl.load_workbook(XLSX, data_only=True)
ws2 = wb2["LESSONS"]
print(f"\n=== VERIFY ===")
print(f"Row 54 (L-51 updated):")
print(f"  id: {ws2.cell(54,1).value} · loai: {ws2.cell(54,5).value}")
print(f"  bai_hoc[:150]: {str(ws2.cell(54,4).value)[:150]}")
print(f"\nRow {next_r} (L-48-AMD new):")
print(f"  id: {ws2.cell(next_r,1).value} · loai: {ws2.cell(next_r,5).value}")
print(f"  bai_hoc[:150]: {str(ws2.cell(next_r,4).value)[:150]}")

print("\n[DONE P2]")
