#!/usr/bin/env python3
"""[A2 CSV migrate] Migrate VPS watchlist_log_2026-08.csv: add sn_count_le050 col.

Insert empty `sn_count_le050` column after `struct_n` (position 8→9 shift).
File cũ 17 cols → file mới 18 cols. Backup đã tạo (.bak_pre_A2_20260821).

Run: ssh vps → python3 /tmp/_task_a2_csv_migrate_vps_20260821.py
Verify: wc -l cùng, head -1 shows new col, spot-check row còn ok.
"""
from __future__ import annotations
import csv, sys, io
from pathlib import Path

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

CSV_PATH = "/root/Data_back_test/whale_data/data/export/watchlist_log_2026-08.csv"

OLD_COLS = [
    "run_date", "symbol", "list", "as_of",
    "div_ratio", "div_5d_ago", "div_delta",
    "struct_n", "episode_id", "hedge_start_date", "hedge_start_px",
    "px_now", "px_dist_pct", "pos_trend", "oi_trend", "oi_note", "funding_pct",
]
NEW_COLS = [
    "run_date", "symbol", "list", "as_of",
    "div_ratio", "div_5d_ago", "div_delta",
    "struct_n", "sn_count_le050",   # NEW insertion
    "episode_id", "hedge_start_date", "hedge_start_px",
    "px_now", "px_dist_pct", "pos_trend", "oi_trend", "oi_note", "funding_pct",
]

with open(CSV_PATH, encoding="utf-8") as f:
    rdr = csv.DictReader(f)
    hdr = rdr.fieldnames
    if hdr != OLD_COLS:
        print(f"[MIGRATE FAIL] header mismatch expected: {OLD_COLS}")
        print(f"                                 got: {hdr}")
        sys.exit(1)
    rows = list(rdr)

for r in rows:
    r["sn_count_le050"] = ""  # empty for legacy rows; new rows filled by cron

tmp = CSV_PATH + ".tmp"
with open(tmp, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=NEW_COLS)
    w.writeheader()
    for r in rows:
        w.writerow(r)

import os
os.replace(tmp, CSV_PATH)

print(f"[MIGRATE OK] {CSV_PATH}")
print(f"  header cols: {len(OLD_COLS)} → {len(NEW_COLS)}")
print(f"  rows migrated: {len(rows)}")

# Verify
with open(CSV_PATH, encoding="utf-8") as f:
    rdr = csv.DictReader(f)
    print(f"  new header: {rdr.fieldnames}")
    first = next(rdr)
    print(f"  first row sn_count_le050='{first.get('sn_count_le050','')}' struct_n='{first.get('struct_n','')}'")
