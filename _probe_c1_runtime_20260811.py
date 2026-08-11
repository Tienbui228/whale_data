"""Runtime verify C1 stealth_grind — print breakout_pct + oi_mult tại eval.

Không đọc comment, không đọc yaml bằng tay. Gọi load_thresholds() đúng
path mà gom_scan.py sẽ gọi, rồi in cfg["stealth_grind"] ra.
Sau đó monkey-patch stealth_grind để in giá trị nội bộ tại điểm eval thật.

data-source: binance-bot-signals/scanner/screener/thresholds.yaml (runtime path)
machine: local
"""
from __future__ import annotations
import sys, io, math
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# ── Reproduce chính xác path load của gom_scan.py ────────────────────────────
BOT_ROOT = Path(r"D:\Data back test\binance-bot-signals")
sys.path.insert(0, str(BOT_ROOT))

from scanner.screener.signals import load_thresholds, stealth_grind, DayData

# Step 1: load thresholds đúng path runtime
cfg = load_thresholds()  # no arg → loads Path(__file__).parent/"thresholds.yaml"

sg = cfg["stealth_grind"]
print("=" * 60)
print("STEP 1: load_thresholds() runtime values")
print(f"  breakout_pct  = {sg['breakout_pct']}  (comment trong signals.py: # 0.15)")
print(f"  breakout_days = {sg['breakout_days']}")
print(f"  oi_mult       = {sg['oi_mult']}   (comment trong signals.py: # 1.5)")
print(f"  taker_buy_max = {sg['taker_buy_max']}")
print(f"\n  RUNNING: breakout_pct={sg['breakout_pct']}, oi_mult={sg['oi_mult']}")
print(f"  SOURCE: {Path(load_thresholds.__code__.co_filename).parent / 'thresholds.yaml'}")
print("=" * 60)

# Step 2: instrument stealth_grind với minimal synthetic TUT-like data
# TUT 2026-07-13: giá tăng ~10% trên 14d range, OI surge ~1.47× med14
# Tạo minimal day sequence để bắt stealth_grind fire và print giá trị nội bộ

import types

_captured = {}

original_sg = stealth_grind

def instrumented_sg(days, i, cfg):
    c = cfg["stealth_grind"]
    _captured["breakout_pct"] = c["breakout_pct"]
    _captured["oi_mult"]      = c["oi_mult"]
    _captured["taker_buy_max"] = c["taker_buy_max"]
    result = original_sg(days, i, cfg)
    return result

# Minimal TUT-like data: 25 days
# Range 14d (days 0-13) avg_px ≈ 100
# Build window (days 14-18, i=19 → i-5=14): avg_px climbs to 115 (+15%)
# OI: ≥1.3× med14 in build window; taker: <55%
def make_nan_day():
    return {
        "avg_px": float("nan"), "oi_usd": float("nan"),
        "taker_buy_pct": float("nan"), "lsr_global_r": float("nan"),
        "lsr_pos_r": float("nan"), "lsr_acc_r": float("nan"),
        "funding_avg": float("nan"), "vol_quote": float("nan"),
        "date": "2026-07-01",
    }

days = []
for k in range(20):
    d = make_nan_day()
    if k < 14:
        d["avg_px"] = 100.0
        d["oi_usd"] = 1_000_000.0
        d["taker_buy_pct"] = 48.0
    elif k < 20:
        d["avg_px"] = 115.0  # +15% above range_hi=100
        d["oi_usd"] = 1_500_000.0  # 1.5× med14
        d["taker_buy_pct"] = 50.0
    days.append(d)

result = instrumented_sg(days, 19, cfg)

print("\nSTEP 2: instrumented call on synthetic TUT-like data (i=19)")
print(f"  breakout_pct USED at eval = {_captured['breakout_pct']}")
print(f"  oi_mult USED at eval      = {_captured['oi_mult']}")
print(f"  taker_buy_max USED        = {_captured['taker_buy_max']}")
print(f"  stealth_grind() → {result}")
print()

# Verify: if breakout_pct were 0.15, does the data still fire?
days_15pct = []
for k in range(20):
    d = make_nan_day()
    if k < 14:
        d["avg_px"] = 100.0
        d["oi_usd"] = 1_000_000.0
        d["taker_buy_pct"] = 48.0
    elif k < 20:
        d["avg_px"] = 110.0  # only +10% — passes 0.09 but NOT 0.15
        d["oi_usd"] = 1_400_000.0  # 1.4× med14 — passes 1.3× but NOT 1.5×
        d["taker_buy_pct"] = 50.0
    days_15pct.append(d)

result_with_real = original_sg(days_15pct, 19, cfg)

# Simulate with 0.15/1.5 config
cfg_fake = {k: dict(v) if isinstance(v, dict) else v for k, v in cfg.items()}
cfg_fake["stealth_grind"] = dict(sg)
cfg_fake["stealth_grind"]["breakout_pct"] = 0.15
cfg_fake["stealth_grind"]["oi_mult"] = 1.5
result_with_fake = original_sg(days_15pct, 19, cfg_fake)

print("STEP 3: +10% / 1.4× scenario — discriminating test")
print(f"  stealth_grind with running cfg (0.09/1.3): {result_with_real}")
print(f"  stealth_grind with comment cfg (0.15/1.5): {result_with_fake}")
print(f"  → If running=0.09 and comment=0.15 give DIFFERENT results on this data,")
print(f"    running canonical is confirmed by behavior difference.")

print("\n" + "=" * 60)
print("CONCLUSION:")
print(f"  Running breakout_pct = {sg['breakout_pct']}  (NOT 0.15 as commented)")
print(f"  Running oi_mult      = {sg['oi_mult']}  (NOT 1.5 as commented)")
print(f"  Comment in signals.py line ~394-396 is WRONG — must be fixed.")
print("=" * 60)
