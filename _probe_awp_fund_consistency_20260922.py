"""AW-α' α2 · fund_state consistency HEDGE vs GOM-E · PUMPBTC & 1000000BOB same PIN.

Rules (lib/fund_state · leg4'):
  PIN       = f_min ≈ 5e-5 (round 8 chữ số) ≥5/7 days
  SHORT-TRẢ = f_avg ≤ 0 ≥3/7 days
  NONE      = else

Đo trên 6 đêm mẫu · CẢ HAI phải cho cùng kết quả.
"""
from __future__ import annotations
import os, sys
from pathlib import Path

_REPO = Path("/root/Data_back_test/whale_data") if os.name != "nt" \
        else Path(r"D:/Data back test/whale_data")
sys.path.insert(0, str(_REPO / "scripts"))

try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except AttributeError: pass  # L-66-OK

import hedge_v2 as hv
from lib.fund_state import fund_state_7d

TARGETS = ["2026-09-15", "2026-09-16", "2026-09-17", "2026-09-18",
           "2026-09-19", "2026-09-20"]
CHECK_SYMS = ["PUMPBTCUSDT", "1000000BOBUSDT"]

print(f"═══ α2 · fund_state consistency 6 đêm ═══")
print(f"{'target':12s} | {'sym':>18s} | {'hedge':>10s} | {'gome_direct':>10s} | {'match':>5s}")
print(f"{'-'*12} | {'-'*18} | {'-'*10} | {'-'*10} | {'-'*5}")

fails = 0
for tgt in TARGETS:
    fw_extra = hv.load_fw_extra(tgt, back=14)
    for sym in CHECK_SYMS:
        hedge_state = hv._fund_state_for_sym(sym, tgt, fw_extra)
        # gom-e direct: cùng logic (dùng cùng lib) · nếu load riêng để so
        dmap = fw_extra.get(sym, {})
        dates = sorted(dmap.keys())[-7:]
        days = [{"f_min": dmap[d].get("f_min"), "f_avg": dmap[d].get("f_avg")} for d in dates]
        gome_direct = fund_state_7d(days)
        match = hedge_state == gome_direct
        if not match: fails += 1
        print(f"{tgt:12s} | {sym:>18s} | {hedge_state:>10s} | {gome_direct:>10s} | {str(match):>5s}")

print()
print(f"═══ TỔNG · {(len(TARGETS)*len(CHECK_SYMS))-fails}/{len(TARGETS)*len(CHECK_SYMS)} match ═══")
sys.exit(0 if fails == 0 else 1)
