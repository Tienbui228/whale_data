#!/usr/bin/env python3
"""[D4 smoke] _run_header + print_header canonical usage.

Verify header output khớp luật D4 (ER-HOME 21/08): spec_path tuyệt đối +
spec_version + amendments_applied + lib_commit + fixture_md5 + snapshot_date.
"""
from __future__ import annotations
import sys, io
from pathlib import Path

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = Path(r"D:\Data back test\whale_data")
sys.path.insert(0, str(REPO))
from lib.registry_events import _run_header, print_header

# Example: registry gate run using golden fixture
hdr = _run_header(
    consumer='registry',
    snapshot_date='2026-08-19',
    fixture_path=REPO / 'tests' / 'fixtures' / 'registry_conformance_20260821.json',
    extra={"probe_name": "_probe_d4_header_smoke_20260821.py"},
)
print_header(hdr)

# Assert field completeness
required = ["spec_path", "spec_version", "amendments_applied",
            "lib_commit", "fixture_md5", "snapshot_date"]
missing = [k for k in required if hdr.get(k) is None or hdr.get(k) == ""]
if missing:
    print(f"\n[D4 FAIL] missing/empty fields: {missing}")
    sys.exit(1)
else:
    print(f"\n[D4 PASS] all 6 canonical fields present")
    print(f"  spec_path abs? {hdr['spec_path'].startswith('D:')} → {hdr['spec_path']}")
    print(f"  amendments {len(hdr['amendments_applied'])} = {hdr['amendments_applied']}")
    print(f"  fixture_md5 len={len(hdr['fixture_md5'])} = {hdr['fixture_md5']}")
