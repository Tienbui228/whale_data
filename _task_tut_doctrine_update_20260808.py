"""
U2: Cập nhật CASE_TUT.xlsx — EVENTS (3 dòng mới), CASE thesis_1line, TRIGGERS (Cửa B).
U3: Draft 2 lessons → append vào CASE_INDEX.xlsx sheet LESSONS.
"""
import sys, io
from pathlib import Path
import openpyxl
from openpyxl.styles import Font
from datetime import date

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

TUT_PATH   = Path(r"D:\Data back test\whale_data\docs\case_files\CASE_TUT.xlsx")
INDEX_PATH = Path(r"D:\Data back test\whale_data\docs\case_files\CASE_INDEX.xlsx")

# ── PART 1: CASE_TUT.xlsx ────────────────────────────────────────────────────

print("=" * 60)
print("PART 1 — CASE_TUT.xlsx")
print("=" * 60)

wb = openpyxl.load_workbook(TUT_PATH)
print(f"Sheets: {wb.sheetnames}")

# ── 1a. EVENTS sheet — append 3 rows ─────────────────────────────────────────
ws_ev = wb["EVENTS"]

# Determine header map
hdrs_ev = {c.value: c.column for c in ws_ev[1] if c.value}
print(f"\nEVENTS headers: {list(hdrs_ev.keys())}")

# Find last data row
last_ev_row = ws_ev.max_row
while last_ev_row > 1 and ws_ev.cell(last_ev_row, 1).value is None:
    last_ev_row -= 1
print(f"EVENTS last data row: {last_ev_row}")

# 3 new events to append
new_events = [
    {
        "date": "2026-08-05",
        "event_type": "HARVEST_INTO_STRENGTH",
        "description": "GHE_ROI_LAN_2: pos_r 4.01→2.07 (−48%), gia +33%, gLSR GIAM 1.44→1.11. KHONG phai L-26 (L-26 = gia sap + gLSR tang). Khuon BANK 19-21/07.",
        "note": "SUA AN NHAN: truoc ghi nham L-26 FIRED — chinh xac la HARVEST-INTO-STRENGTH"
    },
    {
        "date": "2026-08-06",
        "event_type": "FUNDING_NEG_SPOT_DUMP",
        "description": "Funding NEG x2 (12:00 UTC -0.000021, 16:00 UTC -0.000059). Spot close-to-close: 0.02870→0.02450 = −14.6% (DO LON). OI ATH 7.873M (3x band). Khoi phuc PIN 20:00 UTC.",
        "note": "Cua B pattern: funding am sau + OI cao + pos that post-dinh"
    },
    {
        "date": "2026-08-07",
        "event_type": "POS_REBUILD_INTRADAY",
        "description": "pos_r rebuild 2.07→2.72 (intraday 02:05 UTC). gLSR=1.18, OI co ve ~6.07M tu ATH 7.873M. Spot +4.74% tu open. Taker_spot=63.97% (2h).",
        "note": "Rebuild dang dien ra — chua xac nhan boi daily cron 01:20 UTC"
    },
]

# Check if cols exist: date, event_type, description, note
# Map to actual column numbers using hdrs_ev
col_date  = hdrs_ev.get("date") or hdrs_ev.get("Date") or 1
col_type  = hdrs_ev.get("event_type") or hdrs_ev.get("type") or 2
col_desc  = hdrs_ev.get("description") or hdrs_ev.get("Description") or 3
col_note  = hdrs_ev.get("note") or hdrs_ev.get("Note") or 4

print(f"  date→col{col_date}, event_type→col{col_type}, desc→col{col_desc}, note→col{col_note}")

appended = 0
for ev in new_events:
    r = last_ev_row + 1 + appended
    ws_ev.cell(r, col_date).value  = ev["date"]
    ws_ev.cell(r, col_type).value  = ev["event_type"]
    ws_ev.cell(r, col_desc).value  = ev["description"]
    if col_note <= ws_ev.max_column or col_note == 4:
        ws_ev.cell(r, col_note).value = ev["note"]
    appended += 1
    print(f"  EVENTS row {r}: {ev['date']} | {ev['event_type']}")

# ── 1b. CASE sheet — update thesis_1line ─────────────────────────────────────
ws_case = wb["CASE"]

# Find thesis_1line row: col A = key name
updated_thesis = False
for row in ws_case.iter_rows():
    for cell in row:
        if cell.value and str(cell.value).strip().lower() in ("thesis_1line", "thesis"):
            # Value is in next column
            val_cell = ws_case.cell(cell.row, cell.column + 1)
            old_val = val_cell.value
            val_cell.value = "Campaign HAI CHAN KHO: perp book ~$2M VWAP 0.0108 (ghé-rời 2 lần) + spot kho ~83% supply Loai C (chua monetize). Ket thuc qua Cua A (kho/vol ≤10%) hoac Cua B (short-hedge)."
            print(f"\n  CASE thesis_1line updated: [{str(old_val)[:60]}] → [...HAI CHAN KHO...]")
            updated_thesis = True
            break
    if updated_thesis:
        break

if not updated_thesis:
    print("\n  WARN: thesis_1line row not found in CASE sheet — searching all rows...")
    for row in ws_case.iter_rows(values_only=False):
        for cell in row:
            if cell.value:
                print(f"    row{cell.row} col{cell.column}: {str(cell.value)[:40]}")

# ── 1c. TRIGGERS sheet — append Cửa B trigger ────────────────────────────────
if "TRIGGERS" in wb.sheetnames:
    ws_tr = wb["TRIGGERS"]
    hdrs_tr = {c.value: c.column for c in ws_tr[1] if c.value}
    print(f"\nTRIGGERS headers: {list(hdrs_tr.keys())}")

    last_tr_row = ws_tr.max_row
    while last_tr_row > 1 and ws_tr.cell(last_tr_row, 1).value is None:
        last_tr_row -= 1

    new_r = last_tr_row + 1
    # Write columns in order: assume col1=trigger_name, col2=condition, col3=status/note
    col1 = 1; col2 = 2; col3 = 3
    ws_tr.cell(new_r, col1).value = "CUA_B_CAMPAIGN_END"
    ws_tr.cell(new_r, col2).value = "Funding am sau (≤-1.5bps sustained) + OI cao + pos thap hau dinh = campaign ket thuc qua short-hedge (khong ban spot). TUT pattern 08-06."
    ws_tr.cell(new_r, col3).value = "WATCH — chua fire (08-06 = pattern dau hieu, chua xac nhan boi pos_r sap ben du sau)"
    print(f"  TRIGGERS row {new_r}: CUA_B_CAMPAIGN_END appended")
else:
    print("\n  WARN: TRIGGERS sheet not found — listing sheets: " + str(wb.sheetnames))

wb.save(TUT_PATH)
print(f"\nCASE_TUT.xlsx saved. ({appended} EVENTS added)")

# ── PART 2: CASE_INDEX.xlsx — append 2 lesson drafts ─────────────────────────

print("\n" + "=" * 60)
print("PART 2 — CASE_INDEX.xlsx LESSONS")
print("=" * 60)

wb2 = openpyxl.load_workbook(INDEX_PATH)
print(f"Sheets: {wb2.sheetnames}")

if "LESSONS" not in wb2.sheetnames:
    print("  WARN: LESSONS sheet not found. Available: " + str(wb2.sheetnames))
else:
    ws_les = wb2["LESSONS"]
    hdrs_les = {c.value: c.column for c in ws_les[1] if c.value}
    print(f"LESSONS headers: {list(hdrs_les.keys())}")

    # Determine max lesson number
    col_id   = hdrs_les.get("lesson_id") or hdrs_les.get("id") or hdrs_les.get("ID") or 1
    col_body = hdrs_les.get("body") or hdrs_les.get("Body") or hdrs_les.get("lesson") or 2
    col_src  = hdrs_les.get("source") or hdrs_les.get("case") or hdrs_les.get("Source") or 3
    col_date = hdrs_les.get("date") or hdrs_les.get("Date") or 4

    last_les_row = ws_les.max_row
    while last_les_row > 1 and ws_les.cell(last_les_row, col_id).value is None:
        last_les_row -= 1

    # Find max lesson number
    max_num = 0
    for r in range(2, last_les_row + 1):
        v = ws_les.cell(r, col_id).value
        if v:
            s = str(v).upper().replace("L-", "").strip()
            try:
                n = int(s)
                if n > max_num:
                    max_num = n
            except:
                pass
    print(f"Max lesson number found: L-{max_num}")
    next_a = max_num + 1
    next_b = max_num + 2

    lessons_new = [
        {
            "id": f"L-{next_a}",
            "body": f"L-{next_a}(a) DIEU KIEN KET THUC CAMPAIGN: Loai A (kho-muon) = ghe-roi perp la het. Loai B/C (unlock/tu-mua) = ghe-roi perp la CHUYEN PHA — ket thuc that khi kho/vol ≤10% (Cua A) hoac Cua B kich hoat (short-hedge). TUT: pos_r crash 08-05 (−48%) = GHE-ROI LAN 2 (HARVEST-INTO-STRENGTH), KHONG phai L-26, campaign van tiep tuc.",
            "source": "TUT",
            "date": "2026-08-08",
            "status": "DRAFT"
        },
        {
            "id": f"L-{next_b}",
            "body": f"L-{next_b}(b) DURATION SCALING: Thoi luong campaign ty le thuan voi build_window va kho_size. Tham khao draft n=4: BANK (build ~17d, Loai B) → campaign D+17; IDOL (build ~7d, Loai A partial) → D+11; TUT (build 13d, Loai C) → D+16+ ongoing. CLO TBD. Hypothesis: dai build = dai campaign; chua du n de calib chinh xac.",
            "source": "TUT/BANK/IDOL/CLO",
            "date": "2026-08-08",
            "status": "DRAFT"
        }
    ]

    col_status = hdrs_les.get("status") or hdrs_les.get("Status") or 5

    added_les = 0
    for les in lessons_new:
        r = last_les_row + 1 + added_les
        ws_les.cell(r, col_id).value   = les["id"]
        ws_les.cell(r, col_body).value = les["body"]
        ws_les.cell(r, col_src).value  = les["source"]
        ws_les.cell(r, col_date).value = les["date"]
        if col_status <= ws_les.max_column or col_status == 5:
            ws_les.cell(r, col_status).value = les.get("status", "DRAFT")
        added_les += 1
        print(f"  LESSONS row {r}: {les['id']} appended")

    wb2.save(INDEX_PATH)
    print(f"\nCASE_INDEX.xlsx saved. ({added_les} LESSONS added)")

print("\n[DONE]")
