"""ZBT chapter 08-01→08-07: pos_r series + ANALYSIS flag.
Finding: ZBT shows rule-iv (50% pos_r drop) in scratch data — seats rotating out.
This is a LIVE signal pending VPS canonical verification.
Data: scratch/freshwatch_daily_2026-08.csv (ZBTUSDT)
"""
import sys, math
from pathlib import Path

sys.path.insert(0, "scripts")
BOT_ROOT = Path(r"D:\Data back test\binance-bot-signals")
sys.path.insert(0, str(BOT_ROOT))

import pandas as pd
import gom_scan as gs
from fw_loader_utils import build_token_days, enrich_token_days, load_funding_intervals, taker_scale_check_df

CONFIG   = Path("data/config")
SCRATCH  = Path("scratch")
intervals = load_funding_intervals(CONFIG)
cfg = gs.load_thresholds()
sc  = gs.load_screen_cfg()

frames = []
for fn in ["freshwatch_daily_2026-06.csv", "freshwatch_daily_2026-07.csv", "freshwatch_daily_2026-08.csv"]:
    p = SCRATCH / fn
    if p.exists():
        frames.append(pd.read_csv(p))
df = pd.concat(frames, ignore_index=True)
df = taker_scale_check_df(df)

days_zbt, _ = build_token_days(df, "ZBTUSDT", "2026-06-01", "2026-08-07", intervals)
enrich_token_days(days_zbt)

chain = {}
for i, d in enumerate(days_zbt):
    r = gs.eval_gom(days_zbt, i, cfg, sc)
    chain = gs.update_chain(chain, "ZBT", days_zbt, i, r, cfg, sc)

print("ZBT ANALYSIS — chapter tháng 8")
print("Data: scratch/freshwatch_daily_2026-0[678].csv (ZBTUSDT)")
print(f"Chain: start={chain.get('start_date')} close={chain.get('close_date')} "
      f"reason={chain.get('close_reason')} peak_pos_r={chain.get('peak_pos_r')}")
print()

# Show pos_r series around chapter
print(f"{'Date':10}  {'pos_r':6}  {'GOM':4}  {'DQ':4}  notes")
print("-" * 55)
for i, d in enumerate(days_zbt):
    dt = d.get("date", "")
    if dt < "2026-07-28" or dt > "2026-08-07":
        continue
    r   = gs.eval_gom(days_zbt, i, cfg, sc)
    gom = r.get("gom_day", False)
    dq  = r.get("any_supp_dq", False)
    pos = d.get("lsr_pos", float("nan"))
    oi  = d.get("oi_usd", float("nan"))
    pos_s = f"{pos:.3f}" if not math.isnan(pos) else "N/A"
    oi_s  = f"${oi/1e6:.2f}M" if not math.isnan(oi) else "N/A"
    note  = ""
    if dt == chain.get("start_date", ""):
        note = " [chain OPEN]"
    if dt == chain.get("close_date", ""):
        note = " [chain CLOSE]"
    print(f"{dt:10}  {pos_s:6}  {'Y' if gom else 'N':4}  {'Y' if dq else 'N':4}  OI={oi_s}{note}")

# Summary
peak = chain.get("peak_pos_r", float("nan"))
close_r = chain.get("close_reason", "")
start = chain.get("start_date", "?")
close = chain.get("close_date", "?")

print()
print("=" * 55)
print("ANALYSIS FLAG — ZBT (PENDING VPS canonical verify)")
print("=" * 55)
print(f"  Chapter: {start} → {close}")
print(f"  Trigger: {close_r}")
print(f"  peak_pos_r = {peak:.2f}")
print()
print("  Signal: ZBT ghế vừa rời (rule-iv, pos_r sập từ peak)")
print("  Status: WATCH-B → trigger rule-iv → ARMED candidate")
print()
print("  NOTE: Series trên scratch data (local, chưa VPS canonical).")
print("  Verify bằng: VPS rescan khi chạy lệnh (1) backfill canonical.")
print("  Nếu VPS confirm: ZBT rule-iv chapter 08-01→07 đứng vững →")
print("  move to ANALYSIS tracking, monitor for new accumulation signal.")
print()
print("  pos_r series 08-01→07 (drop sequence):")
for i, d in enumerate(days_zbt):
    dt = d.get("date", "")
    if dt < "2026-08-01" or dt > "2026-08-07":
        continue
    pos = d.get("lsr_pos", float("nan"))
    pos_s = f"{pos:.3f}" if not math.isnan(pos) else "N/A"
    delta = ""
    if dt > "2026-08-01":
        for j2, d2 in enumerate(days_zbt):
            if d2.get("date") == "2026-08-01":
                p0 = d2.get("lsr_pos", float("nan"))
                if not math.isnan(p0) and not math.isnan(pos):
                    pct = (pos - p0) / p0 * 100
                    delta = f" ({pct:+.1f}% from 08-01)"
                break
    print(f"  {dt}  pos_r={pos_s}{delta}")
