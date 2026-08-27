"""XAN P0 reconcile 07-01..07-06 · HAI ĐƯỜNG · read-only · DỪNG-PASTE-TRƯỚC-KHI-SỬA"""
from __future__ import annotations
import sys, io, json
from pathlib import Path
from datetime import date as _date, timedelta as _td
import pandas as pd

REPO = Path(r"D:/Data back test/whale_data")
sys.path.insert(0, str(REPO / "scripts"))

from gom_h_daily import _load_cfg, _eval_h1
from adapter_h1_nansen import read_adapter_daily

SNAPSHOTS_DIR = Path(r"D:/Check onchain fresh wallets/snapshots")

cfg_all = _load_cfg()
gom_h_cfg = cfg_all["gom_h"]
gn_cfg = cfg_all.get("goi_nhe", {})
OBS_MIN = gn_cfg.get("obs_min", 14)
gom_h_cfg["t0_1"]["floor_obs_min"] = OBS_MIN
gom_h_cfg["h2"]["floor_obs_min"] = OBS_MIN

# Balance series for XAN
BAL_XAN = {}
for p in sorted(SNAPSHOTS_DIR.glob("*.json")):
    if not (p.stem[:4].isdigit() and len(p.stem) == 10): continue
    try: d = json.loads(p.read_text(encoding="utf-8"))
    except: continue
    if not isinstance(d, dict): continue
    for r in d.get("rows", []):
        if r and (r.get("symbol") or "").upper() == "XAN":
            bal = r.get("exchange_balance_tokens")
            if bal is not None:
                try: BAL_XAN[p.stem] = float(bal)
                except: pass


def annex_kho_step_3d(target_date_str):
    """annex-path: direct snapshot read."""
    ingest = (_date.fromisoformat(target_date_str) + _td(days=1)).isoformat()
    b_end = BAL_XAN.get(ingest)
    if b_end is None or b_end <= 0: return None, "NO-INGEST"
    best = None
    best_from = None
    for lb in range(1, 4):
        d_start = (_date.fromisoformat(ingest) - _td(days=lb)).isoformat()
        b_start = BAL_XAN.get(d_start)
        if b_start is None or b_start <= 0: continue
        dp = abs(b_end - b_start) / b_start
        if best is None or dp > best:
            best = dp
            best_from = d_start
    return best, best_from


print("═" * 100)
print("[XAN P0 RECONCILE · 07-01..07-06 · HAI ĐƯỜNG · read-only]")
print("═" * 100)
print()
print("XAN balance series (ingest_date → balance):")
sorted_dates = sorted([d for d in BAL_XAN.keys() if "2026-06" in d or "2026-07-0" in d])
for d in sorted_dates:
    print(f"  ingest={d}  bal={BAL_XAN[d]:,.2f}")

print()
print(f"  {'target':10} | {'ingest':10} | {'bal_end':>15} | {'annex_step_3d':>13} | {'best_from':>10} | {'h1_prod':>10} | {'h1_raw_prod':>15} | {'match':>6}")
print(f"  {'-'*10}-+-{'-'*10}-+-{'-'*15}-+-{'-'*13}-+-{'-'*10}-+-{'-'*10}-+-{'-'*15}-+-{'-'*6}")
for target_str in ["2026-07-01","2026-07-02","2026-07-03","2026-07-04","2026-07-05","2026-07-06"]:
    ingest = (_date.fromisoformat(target_str) + _td(days=1)).isoformat()
    b_end = BAL_XAN.get(ingest)

    # annex-path
    step_annex, from_date = annex_kho_step_3d(target_str)

    # replay-compose-path: prod _eval_h1 with adapter_df
    adapter_df = read_adapter_daily(ingest)
    xan_row = adapter_df[adapter_df["symbol"] == "XAN"]
    h1_status, h1_detail = _eval_h1("XANUSDT", target_str, adapter_df, gom_h_cfg["h1"])
    h1_kho_raw = h1_detail.get("kho_raw", "N/A")
    h1_step_prod = h1_detail.get("kho_step_pct")
    adapter_flags = h1_detail.get("flags", "")

    match = "YES" if (
        (step_annex is None and h1_kho_raw == "N/A") or
        (step_annex is not None and h1_step_prod is not None and abs(step_annex*100 - h1_step_prod) < 0.01)
    ) else "NO"

    bal_str = f"{b_end:,.0f}" if b_end else "NO-BAL"
    step_a_str = f"{step_annex*100:.2f}%" if step_annex is not None else "N/A"
    step_p_str = f"{h1_step_prod:.2f}%" if h1_step_prod is not None else "N/A"
    print(f"  {target_str} | {ingest} | {bal_str:>15} | {step_a_str:>13} | {str(from_date or '—'):>10} | {step_p_str:>10} | {h1_kho_raw:>15} | {match:>6}")
    if adapter_flags:
        print(f"    ↳ adapter flags: {adapter_flags}")

print()
print("[NGÀY LỆCH ĐẦU TIÊN]")
