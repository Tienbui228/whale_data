#!/usr/bin/env python3
"""Rename 9 loose calib files in u50_data to _LOOSE_RETIRED suffix.
TAG/BTW đã archived trước đó; BAS không có file rời."""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from pathlib import Path

LOOSE = Path(r"D:\Check onchain fresh wallets\u50_data")

# Files to rename (TAG/BTW already ARCHIVED, BAS missing)
LOOSE_FILES = [
    "BANK_result.txt",
    "AKE_result.txt",
    "BASED_result.txt",
    "POWER_result.txt",
    "CLO_result.txt",
    "TUT_result.txt",
    "BULLA_result.txt",
    "ESPORTS_result.txt",
    "IDOL_result.txt",
]

print(f"Loose dir: {LOOSE}")
print(f"Files to rename: {len(LOOSE_FILES)}\n")

renamed = []
missing = []
for fname in LOOSE_FILES:
    src = LOOSE / fname
    if not src.exists():
        missing.append(fname)
        print(f"  MISSING: {fname}")
        continue
    stem = src.stem  # e.g. BANK_result
    new_name = f"{stem}_LOOSE_RETIRED_20260731.txt"
    dst = src.with_name(new_name)
    if dst.exists():
        print(f"  ALREADY RENAMED: {new_name}")
        renamed.append((fname, new_name))
        continue
    src.rename(dst)
    print(f"  OK: {fname} → {new_name}")
    renamed.append((fname, new_name))

print(f"\nRenamed: {len(renamed)}, Missing: {len(missing)}")

# Verify
print("\n=== Verify — remaining *_result.txt (not ARCHIVED/RETIRED) in u50_data ===")
active = [p.name for p in sorted(LOOSE.glob("*_result*.txt"))
          if "ARCHIVED" not in p.name and "RETIRED" not in p.name]
print(f"Active _result.txt count: {len(active)}")
for n in active[:10]:
    print(f"  {n}")
if len(active) > 10:
    print(f"  ... ({len(active)-10} more)")

print("\n=== ARCHIVED/RETIRED files ===")
retired = sorted([p.name for p in LOOSE.glob("*_result*.txt")
                  if "ARCHIVED" in p.name or "RETIRED" in p.name])
for n in retired:
    print(f"  {n}")
