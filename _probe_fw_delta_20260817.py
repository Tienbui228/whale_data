#!/usr/bin/env python3
"""
[5] freshwatch_symbols.txt delta: tìm symbol mới trong universe_master.csv
sau 2026-07-25 (ngày freshwatch_symbols.txt cuối cập nhật).
In danh sách chênh lệch để operator quyết định có thêm vào fw list không.
Run: python _probe_fw_delta_20260817.py > /tmp/fw_delta.txt 2>&1; cat /tmp/fw_delta.txt
"""
import csv
from datetime import date
from pathlib import Path

REPO = Path("/root/Data_back_test/whale_data")
FW_PATH = REPO / "data" / "config" / "freshwatch_symbols.txt"
MASTER_PATH = REPO / "data" / "config" / "universe_master.csv"
FW_MTIME_DATE = date(2026, 7, 25)

# Load freshwatch current list
fw_lines = [l.strip() for l in FW_PATH.read_text(encoding="utf-8").splitlines() if l.strip()]
fw_set = set(fw_lines)
print(f"[fw] current freshwatch_symbols.txt: {len(fw_set)} symbols  mtime={FW_MTIME_DATE}")

# Load universe_master
with open(MASTER_PATH, encoding="utf-8") as f:
    master = list(csv.DictReader(f))

print(f"[master] universe_master.csv: {len(master)} rows")

# Active symbols added AFTER FW_MTIME_DATE
new_active = []
delisted = []
for row in master:
    sym    = row["symbol"]
    status = row["status"]
    added  = row.get("added_date", "")
    try:
        added_d = date.fromisoformat(added)
    except Exception:
        continue
    if status == "active" and added_d > FW_MTIME_DATE and sym not in fw_set:
        new_active.append((sym, added, row.get("source",""), row.get("note","")))
    if status == "delisted" and sym in fw_set:
        delisted.append((sym, row.get("last_seen_exchangeinfo",""), added))

print()
print("=" * 70)
print(f"[1] ACTIVE symbols added AFTER {FW_MTIME_DATE} — NOT in freshwatch ({len(new_active)})")
print("=" * 70)
for sym, added, src, note in sorted(new_active, key=lambda x: x[1]):
    print(f"  {sym:>22}  added={added}  src={src}  note={note}")

print()
print("=" * 70)
print(f"[2] symbols IN freshwatch nhưng DELISTED ({len(delisted)})")
print("=" * 70)
for sym, last_seen, added in sorted(delisted, key=lambda x: x[1] or ""):
    print(f"  {sym:>22}  last_seen={last_seen}  added={added}")

print()
print("=" * 70)
print("[3] Tổng hợp")
print("=" * 70)
print(f"  freshwatch hiện tại:  {len(fw_set)} symbols")
print(f"  có thể THÊM (mới+active): {len(new_active)}")
print(f"  có thể XÓA (delisted):    {len(delisted)}")
fw_net = len(fw_set) + len(new_active) - len(delisted)
print(f"  fw sau khi cập nhật (nếu apply tất cả): {fw_net}")
print()
print("OPERATOR ACTION: duyệt danh sách [1] — thêm vào freshwatch_symbols.txt,")
print("  rồi SCP lên VPS và restart run_gom_daily nếu cần.")
print("DUNG.")
