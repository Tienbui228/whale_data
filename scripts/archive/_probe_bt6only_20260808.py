#!/usr/bin/env python3
# Run only run_backtest6 (skip full backfill output)
import sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(r"D:\Data back test\whale_data\scripts")))
sys.path.insert(0, str(Path(r"D:\Data back test\binance-bot-signals")))

from gom_scan import load_screen_cfg, run_backtest6
from scanner.screener.signals import load_thresholds

cfg = load_thresholds()
sc  = load_screen_cfg()

run_backtest6(cfg, sc)
