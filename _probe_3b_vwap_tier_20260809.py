"""3b: VWAP rep-threshold smoke test.
Tests:
  1. BANK calib case: vwap_den(T1) vs 5% * oi_start_usd → T1 or T2?
     Expect [vw-vol] after threshold (seat-rotation chain).
  2. Scan all 12 calib cases: show tier decision for each.
  3. Find at least one calib that is pure Tier-2 (vwap_den=0, vwap_vol_den>0).
"""
import sys, math
from pathlib import Path
sys.path.insert(0, "scripts")
import gom_scan as gs

BOT_ROOT = Path(r"D:\Data back test\binance-bot-signals")
sys.path.insert(0, str(BOT_ROOT))

import importlib.util
_spec = importlib.util.spec_from_file_location("replay", BOT_ROOT / "replay.py")
_replay = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_replay)

cfg = gs.load_thresholds()
sc  = gs.load_screen_cfg()
g   = sc.get("gom", sc)
REP_FRAC = float(g.get("vwap_t1_min_rep_frac", 0.05))

CASE_DIR = BOT_ROOT / "docs" / "case study"

CALIB = [
    "BANK", "TAG", "bas", "based", "clo", "btw", "tut",
    "bulla", "esport", "idol", "ake", "power",
]

print(f"vwap_t1_min_rep_frac = {REP_FRAC:.2%}")
print()
print(f"{'Token':<10} {'vwap_den':>12} {'oi_start':>12} {'5%_thresh':>12} {'tier':>12} {'vwap_val':>14}")
print("-" * 76)

tier2_found = []

for name in CALIB:
    cpath = CASE_DIR / f"{name.lower()}_result.txt"
    if not cpath.exists():
        cpath = CASE_DIR / f"{name}_result.txt"
    if not cpath.exists():
        print(f"{name:<10} FILE NOT FOUND")
        continue
    try:
        funding, oi, ratio, klines = _replay.parse_result_file(cpath)
        days = _replay.build_days(funding, oi, ratio, klines)
    except Exception as e:
        print(f"{name:<10} LOAD ERROR: {e}")
        continue

    chain = {}
    for i, d in enumerate(days):
        result = gs.eval_gom(days, i, cfg, sc)
        chain  = gs.update_chain(chain, name.upper(), days, i, result, cfg, sc)

    vd       = chain.get("vwap_den", 0.0)
    vn       = chain.get("vwap_num", 0.0)
    vvn      = chain.get("vwap_vol_num", 0.0)
    vvd      = chain.get("vwap_vol_den", 0.0)
    oi_start = chain.get("oi_start_usd", 0.0) or 0.0
    thresh   = REP_FRAC * oi_start if oi_start > 0 else 0.0

    t1_ok = vd > 0 and (oi_start <= 0 or vd >= thresh)
    if t1_ok:
        tier = "T1-oi_wt"
        vwap = vn / vd
    elif vvd > 0:
        tier = "T2-vw-vol"
        vwap = vvn / vvd
        tier2_found.append(name.upper())
    else:
        tier = "N/A"
        vwap = math.nan

    oi_s = f"${oi_start/1e6:.2f}M" if oi_start >= 1e6 else (f"${oi_start/1e3:.0f}k" if oi_start >= 1000 else "$0")
    vd_s = f"${vd/1e3:.0f}k" if vd >= 1000 else f"${vd:.0f}"
    th_s = f"${thresh/1e3:.0f}k" if thresh >= 1000 else f"${thresh:.0f}"
    vw_s = f"{vwap:.6f}" if not math.isnan(vwap) else "N/A"

    mark = " <<< seat-rot chain" if tier == "T2-vw-vol" else ""
    print(f"{name.upper():<10} {vd_s:>12} {oi_s:>12} {th_s:>12} {tier:>12} {vw_s:>14}{mark}")

print()
print(f"Tier-2 tokens found: {tier2_found if tier2_found else '(none — all Tier 1)'}")

print("\n=== BANK detail (key question) ===")
bank_path = CASE_DIR / "BANK_result.txt"
funding, oi, ratio, klines = _replay.parse_result_file(bank_path)
days_bank = _replay.build_days(funding, oi, ratio, klines)
chain_bank = {}
for i, d in enumerate(days_bank):
    result = gs.eval_gom(days_bank, i, cfg, sc)
    chain_bank = gs.update_chain(chain_bank, "BANK", days_bank, i, result, cfg, sc)

vd   = chain_bank.get("vwap_den", 0.0)
vvd  = chain_bank.get("vwap_vol_den", 0.0)
vvn  = chain_bank.get("vwap_vol_num", 0.0)
ois  = chain_bank.get("oi_start_usd", 0.0) or 0.0
thresh = REP_FRAC * ois

print(f"  oi_start_usd   = ${ois:,.0f}")
print(f"  5% threshold   = ${thresh:,.0f}")
print(f"  vwap_den (T1)  = ${vd:,.0f}")
print(f"  T1 rep ok?     = {vd > 0 and (ois <= 0 or vd >= thresh)}")
if vvd > 0:
    vwap_t2 = vvn / vvd
    print(f"  Tier-2 VWAP    = {vwap_t2:.6f} [vw-vol — seat-rotation chain]")
    print(f"  => BANK: [vw-vol] PASS" if not (vd > 0 and (ois <= 0 or vd >= thresh)) else "  => BANK: T1 (rep ok)")
else:
    print(f"  Tier-2 VWAP    = N/A (no vol data)")

print("\nDone.")
