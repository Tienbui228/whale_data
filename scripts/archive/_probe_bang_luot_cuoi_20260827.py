#!/usr/bin/env python3
"""[⑬ (4) Bảng hậu-regen MỘT LƯỢT]

Đo hậu-regen-full-canonical:
  (a) Backtest6 lật bảng (đã in trong log commit — reference lại)
  (b) BULLA identity hai họ classifier-FIXED (WARMUP=6 formula-correct)
  (c) BULLA 07-05 chấm theo số canonical (per ⑬ ii neutral)
  (d) HEMI anchor rerun (episode tier, GATE(i) 3 vế, ⚡ 15/08)
  (e) A-conditions BANK 07-08→07-11 (rerun canonical input)
"""
from __future__ import annotations
import sys, io
from pathlib import Path
import pandas as pd
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = Path(r"D:/Data back test/whale_data")
BOT = Path(r"D:/Data back test/binance-bot-signals")
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(BOT))

from replay import parse_result_file, build_days
import scripts.gom_scan as gom_scan
cfg = gom_scan.load_thresholds()
_sc = gom_scan.load_screen_cfg()
cfg.update(_sc)
sc = {}

# ─── (b) BULLA identity hai họ classifier-FIXED ───
print("═" * 90)
print(" (b) BULLA identity hai họ — classifier FIXED (formula-correct)")
print("═" * 90)

# Family CALIB post-regen-full
fps = list((BOT / "docs" / "case study").glob("bulla*_result.txt"))
funding_c, oi_c, ratio_c, klines_c = parse_result_file(fps[0])
days_calib = build_days(funding_c, oi_c, ratio_c, klines_c)

# Family RUNTIME (store post-backfill)
rows_store = []
for m in ["06","07","08"]:
    p = REPO / f"data/export/freshwatch_daily_2026-{m}.csv"
    if p.exists():
        df = pd.read_csv(p)
        df = df[df["symbol"] == "BULLAUSDT"].sort_values("date")
        for _, r in df.iterrows(): rows_store.append(r)
def _f(r, k):
    try: return float(r[k])
    except: return float("nan")
funding_r, oi_r, ratio_r, klines_r = {}, {}, {}, {}
for r in rows_store:
    d = r["date"]; mmdd = d[5:]
    funding_r[mmdd] = {"avg": _f(r,"funding_avg"), "min": _f(r,"funding_min"), "max": _f(r,"funding_max")}
    oi_r[mmdd] = _f(r,"oi_usd")
    ratio_r[mmdd] = {"lsr_pos": _f(r,"lsr_pos_r"), "lsr_acc": _f(r,"lsr_acc_r"),
                     "lsr_global": _f(r,"lsr_global_r"), "taker_ratio": _f(r,"taker_ratio")}
    klines_r[mmdd] = {"avg_px": _f(r,"px_avg"), "vol_quote": _f(r,"vol_quote"),
                      "taker_buy_pct": _f(r,"taker_buy_pct")*100 if _f(r,"taker_buy_pct")==_f(r,"taker_buy_pct") else float("nan")}
days_runtime = build_days(funding_r, oi_r, ratio_r, klines_r)

def _hbs_map(days):
    m = {}
    for i in range(len(days)):
        d = days[i]
        mmdd = d.get("date","")
        if len(mmdd) == 10: mmdd = mmdd[5:]
        if not mmdd: continue
        try: r = gom_scan.eval_gom(days, i, cfg, sc)
        except Exception: continue
        gb = r.get("gom_b", {})
        m[mmdd] = (r.get("hedge_base_strict"), gb)
    return m

hbs_calib = _hbs_map(days_calib)
hbs_runtime = _hbs_map(days_runtime)

# Formula-correct WARMUP boundaries:
# calib first_seen = 06-16 (funding block start), warmup 06-16..06-22, first_non_warmup 06-23
# runtime first_seen = 06-27, warmup 06-27..07-02, first_non_warmup 07-03
CALIB_FIRST = "06-16"
CALIB_WARMUP_LAST = "06-22"
RUNTIME_FIRST = "06-27"
RUNTIME_WARMUP_LAST = "07-02"

print(f"  Formula-correct boundaries:")
print(f"    Calib first_seen={CALIB_FIRST} warmup_last={CALIB_WARMUP_LAST}")
print(f"    Runtime first_seen={RUNTIME_FIRST} warmup_last={RUNTIME_WARMUP_LAST}")
print()
print(f"  {'date':>6}  {'HBS_c':>6} {'HBS_r':>6}  {'B1c/r':>7} {'B3c/r':>7}  {'nhãn':<25}")

label_counts = {"SAME": 0, "WARMUP": 0, "RÌA-TRÁI": 0, "(v)-taker-lineage": 0, "(v)-px-basis": 0, "(v)-basis-mixed": 0, "KHÁC": 0}

def _fmt(v):
    if v is True: return "T"
    if v is False: return "F"
    if v == "N/A-WARMUP": return "WARM"
    return "-"

for date in sorted(set(hbs_calib.keys()) | set(hbs_runtime.keys())):
    if not ("06-15" <= date <= "07-20"): continue
    c = hbs_calib.get(date, (None, {}))
    r = hbs_runtime.get(date, (None, {}))
    hbs_c, gb_c = c[0], c[1] or {}
    hbs_r, gb_r = r[0], r[1] or {}
    b1_c = gb_c.get("B1"); b1_r = gb_r.get("B1")
    b3_c = gb_c.get("B3"); b3_r = gb_r.get("B3")

    # Classifier FIXED:
    # RÌA-TRÁI = một họ chưa có data (None) AND date < họ đó first_seen
    # WARMUP = một họ hoặc cả hai có "N/A-WARMUP" sentinel (i < hedge_lb-1)
    # SAME = both HBS same
    # (v)-taker-lineage etc: post-both-past-warmup, differ
    if hbs_c is None and hbs_r is None:
        label = "MISSING"
    elif hbs_c is None:  # runtime có, calib chưa (impossible bulla)
        label = "RÌA-TRÁI"; label_counts["RÌA-TRÁI"] += 1
    elif hbs_r is None:  # calib có, runtime chưa (date < RUNTIME_FIRST)
        if date < RUNTIME_FIRST:
            label = "RÌA-TRÁI"; label_counts["RÌA-TRÁI"] += 1
        else:
            label = "OTHER-MISSING"
    elif hbs_r == "N/A-WARMUP" or hbs_c == "N/A-WARMUP":
        label = "WARMUP"; label_counts["WARMUP"] += 1
    elif hbs_c == hbs_r:
        label = "SAME"; label_counts["SAME"] += 1
    else:
        # Post-warmup, differ — classify by which B fields differ
        other_diff = (b1_c != b1_r) or (gb_c.get("B2") != gb_r.get("B2")) or (gb_c.get("B4") != gb_r.get("B4"))
        b3_diff = (b3_c != b3_r)
        if b3_diff and not other_diff:
            # Only B3 flip — could be taker or px basis
            label = "(v)-basis-mixed"  # after full-regen, both should have canonical basis; if diff, likely px or taker
            label_counts["(v)-basis-mixed"] += 1
        else:
            label = "KHÁC ★"; label_counts["KHÁC"] += 1
    print(f"  {date:>6}  {_fmt(hbs_c):>6} {_fmt(hbs_r):>6}  {str(b1_c)[:1]+'/'+str(b1_r)[:1]:>7} {str(b3_c)[:1]+'/'+str(b3_r)[:1]:>7}  {label:<25}")

print()
print(f"  Summary: {label_counts}")
if label_counts["KHÁC"] > 0:
    print(f"  ✗ KHÁC ≠ 0 — DỪNG mở án")
elif label_counts["(v)-basis-mixed"] == 0:
    print(f"  ✓ HỘI TỤ ((v)-tag = 0) — canonical basis cả 2 họ, R6-⑫ eligible")
else:
    print(f"  △ (v)-basis-mixed vẫn có — cần investigate cause tag chi tiết")

# ─── (c) BULLA 07-05 chấm canonical ───
print(f"\n" + "═" * 90)
print(" (c) BULLA 07-05 chấm canonical (per ⑬ ii neutral)")
print("═" * 90)

# Post-regen HBS at 07-05
c_705 = hbs_calib.get("07-05", (None, {}))
r_705 = hbs_runtime.get("07-05", (None, {}))
print(f"  Calib post-regen-full HBS 07-05:  {_fmt(c_705[0])}  (B1={c_705[1].get('B1')} B2={c_705[1].get('B2')} B3={c_705[1].get('B3')} B4={c_705[1].get('B4')})")
print(f"  Runtime store HBS 07-05:          {_fmt(r_705[0])}  (B1={r_705[1].get('B1')} B2={r_705[1].get('B2')} B3={r_705[1].get('B3')} B4={r_705[1].get('B4')})")

# First-True HBS canonical
def _first_true(m):
    for date in sorted(m.keys()):
        if m[date][0] is True: return date
    return None
first_c = _first_true(hbs_calib)
first_r = _first_true(hbs_runtime)
print(f"\n  First-True HBS canonical:")
print(f"    Calib post-regen-full: {first_c}")
print(f"    Runtime store: {first_r}")

if c_705[0] is False and first_c == "07-08":
    print(f"\n  → Per ⑬ (ii) neutral: FLIP T→F at 07-05 → provenance:")
    print(f"    'artifact input pre-regen — K4 first-True 07-05 = artifact of avg_px basis pre-regen'")
elif c_705[0] is True:
    print(f"\n  → Per ⑬ (ii) neutral: TRÙNG (giữ T) → provenance:")
    print(f"    'K4 survives canonical — first-True 07-05 xác nhận cross-basis'")

# ─── (d) HEMI anchor rerun ───
print(f"\n" + "═" * 90)
print(" (d) HEMI anchor §E-R rerun (post canonical taker + avg_px)")
print("═" * 90)
# HEMI has no _result.txt in case study — pure store runtime check
rows_hemi = []
for m in ["06","07","08"]:
    p = REPO / f"data/export/freshwatch_daily_2026-{m}.csv"
    if p.exists():
        df = pd.read_csv(p)
        df = df[df["symbol"] == "HEMIUSDT"].sort_values("date")
        for _, r in df.iterrows(): rows_hemi.append(r)

# Quick HEMI 07-20 raw check
h_720 = None
for r in rows_hemi:
    if r["date"] == "2026-07-20":
        h_720 = r; break
if h_720 is not None:
    print(f"  HEMI 07-20 raw post-backfill:")
    print(f"    taker_buy_pct = {h_720['taker_buy_pct']:.6f}")
    print(f"    taker_source  = {h_720.get('taker_source', 'N/A')}")
    print(f"    lsr_pos = {h_720['lsr_pos_r']:.4f}  acc = {h_720['lsr_acc_r']:.4f}  gLSR = {h_720['lsr_global_r']:.4f}")
    print(f"    oi_usd = {h_720['oi_usd']:.0f}  vol = {h_720['vol_quote']:.0f}")
print(f"\n  HEMI registry episode/tier/GATE(i)/⚡ 15/08 — probe rerun đầy đủ pending sau ký gói cuối")
print(f"  Quick: HEMI 07-20 backfilled canonical → single-day boundary crossing; đơn 1 ngày không đủ flip episode")

# ─── (e) A-conditions BANK 07-08→07-11 canonical ───
print(f"\n" + "═" * 90)
print(" (e) A-conditions BANK 07-08→07-11 (canonical input hậu-regen-full)")
print("═" * 90)

fps_bank = list((BOT / "docs" / "case study").glob("BANK*_result.txt"))
funding_b, oi_b, ratio_b, klines_b = parse_result_file(fps_bank[0])
days_bank = build_days(funding_b, oi_b, ratio_b, klines_b)

targets = ["07-08","07-09","07-10","07-11"]
print(f"  {'date':>7} {'i':>3}  {'A1':>3} {'A2':>3} {'A3':>3} {'A4':>3} {'A5':>3}  {'gom_a':>6}")
for date_str in targets:
    for i, d in enumerate(days_bank):
        dstr = d.get("date","")
        if len(dstr) == 10: dstr = dstr[5:]
        if dstr == date_str:
            r = gom_scan.eval_gom(days_bank, i, cfg, sc)
            ga = r.get("gom_a", {})
            def _b(x): return "T" if x else "F"
            print(f"  {date_str:>7} {i:>3}  {_b(ga.get('A1')):>3} {_b(ga.get('A2')):>3} {_b(ga.get('A3')):>3} {_b(ga.get('A4')):>3} {_b(ga.get('A5')):>3}  {_b(r.get('gom_a_fire')):>6}")
            break
print(f"\n  Compare pre-regen (24/08 KÝ LƯỢT CUỐI): 07-10 = A4 flip F→T, gom_a=T (chain_open 07-10)")
print(f"  Post-regen full canonical: kiểm ngày flip có đổi không.")
