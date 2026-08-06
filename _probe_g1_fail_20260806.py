#!/usr/bin/env python3
"""G1 FAIL analysis: BAS post_climax cooldown + AKE decay series.
Probe-only, no state changes.
"""
import sys, math
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except AttributeError:
    pass

BOT_ROOT = Path(r"D:\Data back test\binance-bot-signals")
sys.path.insert(0, str(BOT_ROOT))

from scanner.screener.signals import load_thresholds, post_climax, decay, funding_extreme
import importlib.util

_replay_spec = importlib.util.spec_from_file_location("replay", BOT_ROOT / "replay.py")
_replay_mod  = importlib.util.module_from_spec(_replay_spec)
_replay_spec.loader.exec_module(_replay_mod)

parse_result_file = _replay_mod.parse_result_file
build_days        = _replay_mod.build_days
CASE_DIR = BOT_ROOT / "docs" / "case study"

cfg = load_thresholds()

def load_token(name: str):
    for fpath in CASE_DIR.glob("*_result.txt"):
        tok = _replay_mod._token_from_path(fpath)
        if tok == name:
            funding, oi, ratio, klines = parse_result_file(fpath)
            return build_days(funding, oi, ratio, klines)
    raise FileNotFoundError(name)

# ── BAS analysis ──────────────────────────────────────────────────────────────
print("=" * 72)
print("BAS — post_climax series (tìm crash day + cooldown mapping)")
print("=" * 72)
bas = load_token("BAS")

print(f"\npost_climax def (signals.py lines 594-613):")
print(f"  Scan back k=0..cooldown (0..14) ngày từ ngày i.")
print(f"  Nếu có ngày j: price_drop(j-1→j) <= -25% → fire.")
print(f"  Hoặc funding_extreme(j) → fire.")
print(f"  → Signal tự chứa 14d cooldown (cooldown_days=14, range = 15 ngày).")
print()
print(f"State machine hiện tại: thêm rolling 14d NỮA trên đỉnh signal.")
print(f"  Total cooldown = crash_day + signal_14d + state_14d = crash + 28d. DOUBLED!")
print()

print(f"{'date':>6}  {'px_avg':>8}  {'taker%':>7}  {'f_avg':>8}  {'OI_usd':>12}  "
      f"{'pc_fire':>7}  {'drop_prev':>10}  {'fe_fire':>7}")
print("-" * 80)
for i, d in enumerate(bas):
    date = d["date"]
    if date < "07-01" or date > "07-18":
        continue
    pc = post_climax(bas, i, cfg)
    fe = funding_extreme(bas, i, cfg)
    # compute day-over-day price drop
    if i > 0 and not math.isnan(bas[i-1]["avg_px"]) and bas[i-1]["avg_px"] > 0:
        drop = (d["avg_px"] - bas[i-1]["avg_px"]) / bas[i-1]["avg_px"]
        drop_str = f"{drop:+.1%}"
    else:
        drop_str = "N/A"
    pc_str = "YES" if pc else "."
    fe_str = "YES" if fe else "."
    print(f"{date:>6}  {d['avg_px']:>8.5f}  {d['taker_buy_pct']:>6.1f}%  "
          f"{d['funding_avg']:>8.5f}  {d['oi_usd']:>12,.0f}  "
          f"{pc_str:>7}  {drop_str:>10}  {fe_str:>7}")

# Find the crash day explicitly
print("\nCrash detection (price drop >= 25% single day):")
for i, d in enumerate(bas):
    if i == 0:
        continue
    if math.isnan(bas[i-1]["avg_px"]) or bas[i-1]["avg_px"] <= 0:
        continue
    drop = (d["avg_px"] - bas[i-1]["avg_px"]) / bas[i-1]["avg_px"]
    if drop <= -0.25:
        print(f"  CRASH: {bas[i-1]['date']} -> {d['date']}: {drop:+.1%} = {drop:.4f}")

print()
print("Fix ĐƯỢC PHÉP (tầng state, không đụng signals.py):")
print("  Thay rolling-14d check bằng episode-based: 14d tính từ first-fire.")
print("  Vì post_climax đã tự nhúng 14d cooldown, state chỉ cần dùng first-fire")
print("  làm anchor, không extend khi signal tiếp tục fire trong cùng episode.")

# ── AKE analysis ──────────────────────────────────────────────────────────────
print()
print("=" * 72)
print("AKE — decay series (kiểm tra từng điều kiện 07-04..07-12)")
print("=" * 72)
ake = load_token("AKE")

print(f"\ndecay def (signals.py lines 573-583):")
print(f"  hold_n=5 consecutive days taker_buy_pct < 45.0%")
print(f"  (captures BTW-style: taker low + price mòn + OI phẳng)")
print()

decay_days_min = cfg["decay"]["decay_days_min"]  # 5
taker_max = cfg["decay"]["taker_buy_max"]  # yaml: 48.0 (spec comment says 45.0 — discrepancy!)
print(f"  decay_days_min={decay_days_min}, taker_buy_max={taker_max}")
print()

print(f"{'date':>6}  {'px_avg':>9}  {'taker%':>7}  {'f_avg':>8}  {'OI_usd':>12}  "
      f"{'decay':>6}  {'5d_takers':>40}")
print("-" * 100)
for i, d in enumerate(ake):
    if d["date"] < "07-02" or d["date"] > "07-15":
        continue
    dc = decay(ake, i, cfg)
    # collect 5d takers ending at i
    if i >= decay_days_min - 1:
        takers_5d = [ake[j]["taker_buy_pct"] for j in range(i - decay_days_min + 1, i + 1)]
        takers_str = str([f"{t:.1f}" for t in takers_5d])
        all_below = all(t < taker_max for t in takers_5d)
        flag = "FIRE" if dc else "."
        flag_tag = " ← BUG?" if (d["date"] == "07-08" and dc) else ""
    else:
        takers_str = "(window short)"
        flag = "."
        flag_tag = ""
    print(f"{d['date']:>6}  {d['avg_px']:>9.6f}  {d['taker_buy_pct']:>6.1f}%  "
          f"{d['funding_avg']:>8.5f}  {d['oi_usd']:>12,.0f}  "
          f"{flag:>6}  {takers_str}{flag_tag}")

print()
print("Chấm điều kiện từng day trong window 07-04..07-08:")
for i, d in enumerate(ake):
    if d["date"] < "07-01" or d["date"] > "07-12":
        continue
    tb = d["taker_buy_pct"]
    below = tb < taker_max
    print(f"  {d['date']}: taker={tb:.2f}%  < {taker_max}? {'YES' if below else 'NO'}")

print()
print("Decay fires on 07-08 => window 07-04..07-08. Tất cả < 45%?")
for i, d in enumerate(ake):
    if d["date"] == "07-08":
        takers_window = [ake[j]["taker_buy_pct"] for j in range(i - 4, i + 1)]
        print(f"  07-04 to 07-08 takers: {[f'{t:.2f}' for t in takers_window]}")
        print(f"  All < {taker_max}% (yaml threshold): {all(t < taker_max for t in takers_window)}")
        print(f"  All < 45.0% (spec intent):  {all(t < 45.0 for t in takers_window)}")
        break

print()
print("Kết luận sơ bộ:")
for i, d in enumerate(ake):
    if d["date"] == "07-08":
        takers_window = [ake[j]["taker_buy_pct"] for j in range(i - 4, i + 1)]
        genuine_yaml = all(t < taker_max for t in takers_window)
        genuine_spec  = all(t < 45.0 for t in takers_window)
        if genuine_yaml:
            print(f"  decay trên AKE 07-08 = GENUINE dưới yaml taker_buy_max={taker_max}%.")
            if not genuine_spec:
                print(f"  NHƯNG không genuine dưới spec intent (45.0%): có ngày taker >= 45%.")
                print(f"  → Root cause: yaml threshold 48.0 > spec 45.0 → threshold quá permissive.")
                print(f"  → Fix: proposals/yaml_change_decay_20260806.md (48.0→45.0). Operator sign-off.")
                print(f"  → G1 AKE 07-20 = SUPP (FAIL, diff=2). 1 case còn lại sau fix BAS.")
            else:
                print(f"  → Không fix trong G1. Cần proposal riêng nếu muốn đổi threshold.")
        else:
            print(f"  decay trên AKE 07-08 = BUG (có ngày taker >= {taker_max}% trong window).")
            print(f"  → Fix ĐƯỢC trong replay hoặc input. Kiểm tra dòng data nghi vấn.")
        break
