#!/usr/bin/env python3
"""Bước 3: Chạy backtest §6 gom_scan — in bảng PASS/FAIL 10 dòng."""
import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
from scripts.gom_scan import run_backtest6, load_screen_cfg
sys.path.insert(0, r"D:\Data back test\binance-bot-signals")
from scanner.screener.signals import load_thresholds

cfg = load_thresholds()
sc  = load_screen_cfg()
run_backtest6(cfg, sc)
