#!/usr/bin/env python3
"""[R4-v2 (4) bảng ký-lượt-cuối] Hai bảng gửi operator:
  (a) A-conditions BANK per-day 07-08→07-11: A1-A5 từng ngày,
      điều kiện nào lật 10/07 mà không lật 09/07 — số tự vệ cho ② (+1d).
  (b) B-truth row 9 hai họ post-regen-v2 với cause-tag (v)-taker-lineage:
      RÌA-TRÁI / WARMUP / (v)-taker-lineage / KHÁC.

⑩-AMENDMENT (v) rule: HBS diff do B3-only-flip khi runtime store còn derive
r/(1+r) và calib đã k[10]/k[7] fresh → cause-tag (v), KHÔNG phải KHÁC.
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

# ─── (a) BANK A-conditions per-day 07-08→07-11 ───
print("═" * 100)
print(" [R4-v2 (4a)] BANK A-conditions per-day 07-08→07-11 — số tự vệ cho ②(+1d)")
print("═" * 100)

fps_bank = list((BOT / "docs" / "case study").glob("BANK*_result.txt"))
funding_b, oi_b, ratio_b, klines_b = parse_result_file(fps_bank[0])
days_bank = build_days(funding_b, oi_b, ratio_b, klines_b)

# find indices for target dates
targets_bank = ["07-08","07-09","07-10","07-11"]
print(f"  {'date':>7} {'i':>3}  {'A1':>3} {'A2':>3} {'A3':>3} {'A4':>3} {'A5':>3}  {'gom_a':>6}  "
      f"{'a2_avg5':>8} {'a3_slope':>9}  {'flags':<30}")
print("  " + "─" * 95)
prev = None
for date_str in targets_bank:
    for i, d in enumerate(days_bank):
        dstr = d.get("date","")
        if len(dstr) == 10: dstr = dstr[5:]
        if dstr == date_str:
            try: r = gom_scan.eval_gom(days_bank, i, cfg, sc)
            except Exception as e: print(f"  {date_str:>7} ERR {e}"); break
            ga = r.get("gom_a", {})
            a1, a2, a3, a4, a5 = ga.get("A1",False), ga.get("A2",False), ga.get("A3",False), ga.get("A4",False), ga.get("A5",False)
            gom_a_fire = r.get("gom_a_fire", False)
            supp = r.get("supp_dq", {}) or {}
            pdq = r.get("perday_dq", {}) or {}
            flags_on = [k for k, v in {**supp, **pdq}.items() if v]
            flags_str = "+".join(flags_on) if flags_on else "-"
            a2v = r.get("a2_avg5_val", float("nan"))
            a3v = r.get("a3_slope_val", float("nan"))
            def _b(x): return "T" if x else "F"
            print(f"  {date_str:>7} {i:>3}  {_b(a1):>3} {_b(a2):>3} {_b(a3):>3} {_b(a4):>3} {_b(a5):>3}  "
                  f"{_b(gom_a_fire):>6}  {a2v:>8.4f} {a3v:>9.4f}  {flags_str:<30}")
            # Compare with previous
            if prev is not None:
                cur_conds = {"A1":a1,"A2":a2,"A3":a3,"A4":a4,"A5":a5,"gom_a_fire":gom_a_fire}
                flipped = [k for k in cur_conds if cur_conds[k] != prev[k]]
                if flipped:
                    print(f"    → flipped from {prev['date']}: {flipped}")
            prev = {"date": date_str, "A1":a1,"A2":a2,"A3":a3,"A4":a4,"A5":a5,"gom_a_fire":gom_a_fire}
            break

print(f"\n  Semantics: gom_a_fire flip F→T = ngày chain_open (Row 3 checker phát PASS)")
print(f"  Điều kiện lật 07-10 mà không lật 07-09 = self-defense cho ②(+1d) shift.")

# ─── (b) B-truth row 9 hai họ hội tụ post-regen-v2 với (v) tag ───
print(f"\n" + "═" * 100)
print(" [R4-v2 (4b)] B-truth row 9 hai họ hậu-regen-v2 với cause-tag (v)-taker-lineage")
print("═" * 100)

# Family CALIB (bulla_result post-regen-v2)
fps_bulla = list((BOT / "docs" / "case study").glob("bulla*_result.txt"))
funding_c, oi_c, ratio_c, klines_c = parse_result_file(fps_bulla[0])
days_calib = build_days(funding_c, oi_c, ratio_c, klines_c)

# Family RUNTIME (store freshwatch)
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

print(f"  {'date':>6}  {'HBS_calib':>10} {'HBS_run':>10}  {'B1_c/B1_r':>10} {'B3_c/B3_r':>10}  {'nhãn':<25}")
print("  " + "─" * 90)

label_counts = {"SAME": 0, "WARMUP": 0, "RÌA-TRÁI": 0, "(v)-taker-lineage": 0, "KHÁC": 0}

def _fmt_hbs(v):
    if v is True: return "T"
    if v is False: return "F"
    if v == "N/A-WARMUP": return "WARM"
    return "-"

for date in sorted(set(hbs_calib.keys()) | set(hbs_runtime.keys())):
    if not ("06-29" <= date <= "07-20"): continue
    c = hbs_calib.get(date, (None, {}))
    r = hbs_runtime.get(date, (None, {}))
    hbs_c, gb_c = c[0], c[1] or {}
    hbs_r, gb_r = r[0], r[1] or {}
    b1_c = gb_c.get("B1", None); b1_r = gb_r.get("B1", None)
    b3_c = gb_c.get("B3", None); b3_r = gb_r.get("B3", None)
    same = (hbs_c == hbs_r)
    label = ""
    if same:
        label = "SAME"; label_counts["SAME"] += 1
    else:
        if hbs_r == "N/A-WARMUP" or hbs_c == "N/A-WARMUP":
            label = "WARMUP"; label_counts["WARMUP"] += 1
        elif date <= "07-03":
            label = "RÌA-TRÁI"; label_counts["RÌA-TRÁI"] += 1
        else:
            # Check (v)-taker-lineage: only B3 flips, others match
            other_diff = (b1_c != b1_r) or (gb_c.get("B2") != gb_r.get("B2")) or (gb_c.get("B4") != gb_r.get("B4"))
            b3_diff = (b3_c != b3_r)
            if b3_diff and not other_diff:
                label = "(v)-taker-lineage"; label_counts["(v)-taker-lineage"] += 1
            else:
                label = "KHÁC ★"; label_counts["KHÁC"] += 1
    mark = "" if label in ("SAME",) else "★" if label == "KHÁC ★" else "○"
    print(f"  {date:>6}  {_fmt_hbs(hbs_c):>10} {_fmt_hbs(hbs_r):>10}  "
          f"{str(b1_c)[:1]+'/'+str(b1_r)[:1]:>10} {str(b3_c)[:1]+'/'+str(b3_r)[:1]:>10}  {label:<25}")

print()
print(f"  Summary: SAME={label_counts['SAME']} · WARMUP={label_counts['WARMUP']} · "
      f"RÌA-TRÁI={label_counts['RÌA-TRÁI']} · "
      f"(v)-taker-lineage={label_counts['(v)-taker-lineage']} · KHÁC={label_counts['KHÁC']}")

if label_counts["KHÁC"] > 0:
    print(f"\n  ✗ KHÁC = {label_counts['KHÁC']} — DỪNG per ANALYSIS ② (bug thật)")
else:
    print(f"\n  ✓ KHÁC = 0 — hội tụ theo ⑩-AMENDMENT: residual chỉ có RÌA-TRÁI/WARMUP/(v)-taker-lineage")
    print(f"  → (v) residuals sẽ biến sau collector migrate (5) — forward-only")
