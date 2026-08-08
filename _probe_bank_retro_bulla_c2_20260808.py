"""BANK retro-tag check + BULLA C2 GOM-C 07-17->21."""
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

# ── BANK retro-tag ────────────────────────────────────────────────────────────
state = json.loads(Path("data/gom_state_v8.json").read_text(encoding="utf-8"))
bank_st = state.get("BANK", {})
peak_pos = bank_st.get("peak_pos_r", float("nan"))
print(f"BANK peak_pos_r in v8 state: {peak_pos}")
print(f"BANK close: {bank_st.get('close_date','?')} reason: {bank_st.get('close_reason','?')}")

days_b, _ = build_token_days(df, "BANKUSDT", "2026-06-01", "2026-07-25", intervals)
enrich_token_days(days_b)
print("\nBANK pos_r (lsr_pos) 07-12->07-18:")
print(f"  {'date':<12} {'lsr_pos':>9} {'drop_from_peak':>15}")
for d in days_b:
    dt = d.get("date","")
    if dt < "2026-07-12" or dt > "2026-07-18":
        continue
    lp = d.get("lsr_pos", float("nan"))
    if not math.isnan(peak_pos) and not math.isnan(lp) and peak_pos > 0:
        drop = (peak_pos - lp) / peak_pos
        drop_str = f"{drop:.1%}"
    else:
        drop_str = "N/A"
    print(f"  {dt:<12} {lp:>9.4f} {drop_str:>15}")

print()
drop_trigger = 0.30
# Find first date after 07-14 where drop >= 30%
retro_date = None
for d in days_b:
    dt = d.get("date","")
    if dt <= "2026-07-14":
        continue
    lp = d.get("lsr_pos", float("nan"))
    if not math.isnan(peak_pos) and not math.isnan(lp) and peak_pos > 0:
        drop = (peak_pos - lp) / peak_pos
        if drop >= drop_trigger:
            retro_date = dt
            print(f"RETRO-TAG candidate: {dt} pos_r={lp:.4f} drop={drop:.1%} from peak={peak_pos:.4f}")
            break
if not retro_date:
    print("RETRO-TAG: no pos_r drop >=30% found in 07-15->07-17 window")

# Check within <=3d of close 07-14
if retro_date:
    from datetime import datetime
    close_dt = datetime.strptime("2026-07-14", "%Y-%m-%d")
    retro_dt = datetime.strptime(retro_date, "%Y-%m-%d")
    gap = (retro_dt - close_dt).days
    print(f"Gap from close to retro-tag: {gap} days (<=3 = qualifies)")

# ── BULLA GOM-C 07-17->21 ────────────────────────────────────────────────────
print()
print("BULLA GOM-C check 07-17->21 (no cooldown from gom_gap close):")
days_bul, _ = build_token_days(df, "BULLAUSDT", "2026-06-01", "2026-07-25", intervals)
enrich_token_days(days_bul)

CHECK_DATES = ["2026-07-17","2026-07-18","2026-07-19","2026-07-20","2026-07-21"]
print(f"{'date':<12} {'FIRE(no-cd)':>12} {'FIRE(cd)':>10}")
print("-"*40)
for i, d in enumerate(days_bul):
    dt = d.get("date","")
    if dt not in CHECK_DATES:
        continue
    if d.get("_suspect") or d.get("_skip_eval"):
        print(f"{dt:<12} SKIP")
        continue
    result = gs.eval_gom(days_bul, i, cfg, sc)
    f_nocd = gs._gomc_beta_check(days_bul, i, cfg, sc, result, check_cooldown=False)
    f_cd   = gs._gomc_beta_check(days_bul, i, cfg, sc, result, check_cooldown=True)
    print(f"{dt:<12} {str(f_nocd):>12} {str(f_cd):>10}")
