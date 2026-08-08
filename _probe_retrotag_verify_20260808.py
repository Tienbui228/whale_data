"""Verify BANK retro-tag implementation fires on 07-16 (2d after 07-14 close)."""
import sys, math, json
from pathlib import Path
sys.path.insert(0, "scripts")
from fw_loader_utils import load_fw_csvs, build_token_days, enrich_token_days, load_funding_intervals, taker_scale_check_df
import gom_scan as gs
from scanner.screener.signals import load_thresholds

STORE   = Path("D:/Check onchain fresh wallets/data/export")
CONFIG  = Path("data/config")

intervals = load_funding_intervals(CONFIG)
cfg = load_thresholds()
sc  = gs.load_screen_cfg()

df = load_fw_csvs(STORE, "2026-07-25", lookback_days=60)
df = taker_scale_check_df(df)
days, _ = build_token_days(df, "BANKUSDT", "2026-06-01", "2026-07-25", intervals)
enrich_token_days(days)

# Run chain scan on BANK
chain = {}
for i, d in enumerate(days):
    result = gs.eval_gom(days, i, cfg, sc)
    chain = gs.update_chain(chain, "BANKUSDT", days, i, result, cfg, sc)
    dt = d.get("date","")
    if "2026-07-12" <= dt <= "2026-07-22":
        retro = chain.get("retro_tag","")
        note  = chain.get("retro_tag_note","")
        print(f"{dt}: chain_open={chain.get('chain_open')} close_reason={chain.get('close_reason','')} retro_tag={retro} note={note}")

print()
print("Final BANK chain state:")
print(f"  chain_open   : {chain.get('chain_open')}")
print(f"  close_date   : {chain.get('close_date')}")
print(f"  close_reason : {chain.get('close_reason')}")
print(f"  retro_tag    : {chain.get('retro_tag')}")
print(f"  retro_tag_drop: {chain.get('retro_tag_drop')}")
print(f"  retro_tag_note: {chain.get('retro_tag_note')}")
print(f"  peak_pos_r   : {chain.get('peak_pos_r')}")

# Test format_chain_report
report = gs.format_chain_report("BANKUSDT", chain, None, "2026-07-25")
print(f"\nformat_chain_report output:\n{report}")
