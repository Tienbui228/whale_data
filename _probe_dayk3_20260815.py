#!/usr/bin/env python3
"""
Day-K=3 anti-look-ahead test. K cố định = 3 (ANALYSIS pre-commit), KHÔNG thử K khác.

net_k3 = oi_usd(fire+3) - oi_usd(fire)
─ ĐO GÌ: OI window 3 ngày đầu chain (raw snapshot delta 2 điểm).
─ KHÔNG ĐO GÌ: KHÔNG lọc counts_q1, KHÔNG lọc ret_1d, KHÔNG lọc partial_day.
  Nhãn: **[OI-3d-đầu window]** — cùng họ semantic với net_oi_window (nhiễm chase-pump).

Finding "net_k3 âm-đậm=cờ xấu" (SKYAI −11.3M → hold 0.157) — GIỮ.
Finding "Group B beat A → net-signal đóng" (run 15/08 08:13 UTC /tmp/dayk3.txt) — **INVALID**
  do dùng wrong-variable (net_k3 raw window, semantic ngang net_oi_window). Verdict 17/08
  operator signed: rerun trên net_gated_usd (Σ ΔOI on counts_q1 days).

Group A: net_k3 > 0. Group B: net_k3 <= 0.
mg11 = forward max_gain 11 ngày từ fire+3 (avg_px SÀN).
So sanh %mg>15% + median mg11. BANK check riêng.
Run: python3 _probe_dayk3_20260815.py > /tmp/dayk3.txt 2>&1; cat /tmp/dayk3.txt
"""
import json, math, statistics
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

REPO   = Path("/root/Data_back_test/whale_data")
DATA   = REPO / "data"
EXPORT = DATA / "export"
K      = 3          # LOCKED — KHONG doi
FWD    = 14 - K     # = 11
NaN    = float("nan")

def bare(s):
    return s[:-4] if s.endswith("USDT") else s

# ── Load gom_state chapters ───────────────────────────────────────────────────
gom = json.load(open(DATA / "gom_state.json", encoding="utf-8"))

def cat_r(r):
    if not r:             return "?"
    if "gom_gap"    in r: return "gap-dead"
    if "pos_r_drop" in r: return "harvest"
    if "suppressor" in r: return "suppressor"
    return r[:18]

chapters = []
for sym, v in gom.items():
    sd = v.get("start_date", "")
    if not sd: continue
    is_open = v.get("chain_open")
    cd = v.get("close_date", "")
    net_close = v.get("net_oi_delta_usd", NaN)
    chapters.append({
        "symbol":    sym,
        "sym_usdt":  sym + "USDT",
        "chapter":   v.get("chapter", 1),
        "is_open":   is_open,
        "fire_date": sd,
        "close_date": cd if not is_open else "OPEN",
        "net_close": net_close,
        "close_cat": cat_r(v.get("close_reason","")) if not is_open else "OPEN",
        "source":    "gom_state",
    })

# Add closed_chapters Aug
cc_path = EXPORT / "closed_chapters_2026-08.csv"
if cc_path.exists():
    cc = pd.read_csv(cc_path)
    existing = {(c["symbol"], c["chapter"]) for c in chapters}
    for _, row in cc.iterrows():
        sym = bare(str(row["token"]).strip())
        if sym not in {c["symbol"] for c in chapters}: continue
        chap = int(row.get("chapter", 1))
        if (sym, chap) in existing: continue
        sd = str(row["start_date"]).strip()
        chapters.append({
            "symbol": sym, "sym_usdt": sym + "USDT",
            "chapter": chap, "is_open": False,
            "fire_date": sd, "close_date": str(row["close_date"]).strip(),
            "net_close": float(row.get("net_oi_delta", NaN)),
            "close_cat": cat_r(str(row.get("close_reason",""))),
            "source": "closed_chapters",
        })

chapters = [c for c in chapters if c["fire_date"] and c["fire_date"] != "nan"]
print(f"[load] chapters: {len(chapters)}")

# ── Load freshwatch_daily (px_avg + oi_usd) ───────────────────────────────────
daily_dfs = []
for f in sorted(EXPORT.glob("freshwatch_daily_*.csv")):
    daily_dfs.append(pd.read_csv(f, usecols=["date", "symbol", "px_avg", "oi_usd"]))
daily   = pd.concat(daily_dfs, ignore_index=True)
daily   = daily.dropna(subset=["px_avg"])
daily   = daily[daily["px_avg"] > 0]
px_map  = {(r["symbol"], r["date"]): r["px_avg"]  for _, r in daily.iterrows()}
oi_map  = {(r["symbol"], r["date"]): r["oi_usd"]  for _, r in daily.iterrows()
           if not (isinstance(r["oi_usd"], float) and math.isnan(r["oi_usd"]))}
px_max_date = date.fromisoformat(daily["date"].max())
print(f"[load] px_map: {len(px_map)}  oi_map: {len(oi_map)}  up to {px_max_date}")

def fwd_mg(sym_usdt, from_dt_str, days_n):
    t   = date.fromisoformat(from_dt_str)
    px0 = px_map.get((sym_usdt, from_dt_str))
    if not px0:
        t2  = t + timedelta(1)
        px0 = px_map.get((sym_usdt, t2.isoformat()))
        if not px0: return NaN, NaN, 0
        t = t2
    fwd_d = [(t + timedelta(d)).isoformat() for d in range(1, days_n + 1)]
    pxs   = [px_map[(sym_usdt, d)] for d in fwd_d if (sym_usdt, d) in px_map]
    if not pxs: return NaN, NaN, 0
    return max(pxs) / px0 - 1.0, pxs[-1] / max(pxs), len(pxs)

# ── Compute per chapter ───────────────────────────────────────────────────────
print(f"[compute] net_k3 (K={K}) + mg{FWD} for all chapters ...", flush=True)

results = []
for c in chapters:
    fire_dt = date.fromisoformat(c["fire_date"])
    fk_dt   = fire_dt + timedelta(K)           # fire+3
    fk_str  = fk_dt.isoformat()
    sym_u   = c["sym_usdt"]

    # Skip if fire+K is in the future (no data yet)
    if fk_dt > px_max_date:
        c["skip_reason"] = f"fire+K={fk_str} > px_max={px_max_date}"
        continue

    # oi at fire and fire+K
    oi_fire = oi_map.get((sym_u, c["fire_date"]))
    oi_fk   = oi_map.get((sym_u, fk_str))

    # Fallback: try fire+1 for oi_fire if missing (some symbols have T+1 data)
    if oi_fire is None:
        oi_fire = oi_map.get((sym_u, (fire_dt + timedelta(1)).isoformat()))
    if oi_fk is None:
        oi_fk   = oi_map.get((sym_u, (fk_dt + timedelta(1)).isoformat()))

    if oi_fire is None or oi_fk is None:
        c["skip_reason"] = f"oi_missing fire={oi_fire} fk={oi_fk}"
        continue

    net_k3   = oi_fk - oi_fire
    group    = "A" if net_k3 > 0 else "B"
    mg11, h11, n11 = fwd_mg(sym_u, fk_str, FWD)

    results.append({**c,
        "fk_str":   fk_str,
        "oi_fire":  oi_fire,
        "oi_fk":    oi_fk,
        "net_k3":   net_k3,
        "group":    group,
        "mg11":     mg11,
        "h11":      h11,
        "n11":      n11,
    })

skipped = len(chapters) - len(results)
print(f"[compute] computed: {len(results)}  skipped: {skipped}")

# ── Split groups ──────────────────────────────────────────────────────────────
grp_a = [r for r in results if r["group"] == "A"]
grp_b = [r for r in results if r["group"] == "B"]

# Only chapters with n11 >= 3 for stats
a_fwd = [r for r in grp_a if r["n11"] >= 3]
b_fwd = [r for r in grp_b if r["n11"] >= 3]

def stats(group):
    mgs  = [r["mg11"]  for r in group if not math.isnan(r["mg11"])]
    hs   = [r["h11"]   for r in group if not math.isnan(r.get("h11", NaN))]
    n    = len(mgs)
    if n == 0: return {"n": 0, "pct_mg15": NaN, "med_mg": NaN, "mean_mg": NaN, "med_h": NaN}
    pct15 = sum(1 for v in mgs if v > 0.15) / n * 100
    return {
        "n":       n,
        "pct_mg15": pct15,
        "med_mg":  statistics.median(mgs) * 100,
        "mean_mg": statistics.mean(mgs)   * 100,
        "med_h":   statistics.median(hs)  * 100 if hs else NaN,
    }

sa = stats(a_fwd)
sb = stats(b_fwd)

DIV = "=" * 110

# ── Output [1] per-chapter table ───────────────────────────────────────────────
print()
print(DIV)
print(f"[1] PER-CHAPTER — net_k3 = oi(fire+{K}) - oi(fire). Group A: >0. Group B: <=0.")
print(f"    mg{FWD} from fire+{K} (avg_px [SAN]). K={K} LOCKED (ANALYSIS pre-commit).")
print(DIV)

results_sorted = sorted(results, key=lambda x: x["fire_date"])
hdr = (f"{'#':>3}  {'fire':>10}  {'fk':>10}  {'sym':>12}  {'ch':>2}  "
       f"{'oi_fire':>12}  {'oi_fk':>12}  {'net_k3':>12}  {'G':>1}  "
       f"{'mg11%':>7}  {'h11':>5}  {'n11':>3}  {'net_close':>12}  cat")
print(hdr)
print("─" * len(hdr))

def fmg(v):  return f"{v*100:>+6.1f}%" if not math.isnan(v) else "    NaN"
def fh(v):   return f"{v:.3f}"          if not math.isnan(v) else "  NaN"
def fn(v):   return str(int(v))          if not math.isnan(v) else "─"

for i, r in enumerate(results_sorted):
    nc_s = f"{r['net_close']:>+12,.0f}" if not math.isnan(r["net_close"]) else "         NaN"
    n11_s = fn(r["n11"])
    print(f"{i+1:>3}  {r['fire_date']:>10}  {r['fk_str']:>10}  {r['symbol']:>12}  {r['chapter']:>2}  "
          f"{r['oi_fire']:>12,.0f}  {r['oi_fk']:>12,.0f}  {r['net_k3']:>+12,.0f}  {r['group']:>1}  "
          f"{fmg(r['mg11']):>7}  {fh(r['h11']):>5}  {n11_s:>3}  {nc_s}  {r['close_cat']}")

print(f"\n  Group A (net_k3>0):  {len(grp_a)} chapters  |  Group B (net_k3<=0): {len(grp_b)} chapters")
print(f"  Skipped (fire+K>px_max or oi_missing): {skipped}")

# ── Output [2] Stats comparison ────────────────────────────────────────────────
print()
print(DIV)
print(f"[2] GROUP A vs B — mg{FWD} from fire+{K} (n11>={3} only)")
print(DIV)

print(f"  {'metric':>28}  {'Group A (n={:d})'.format(sa['n']):>18}  "
      f"{'Group B (n={:d})'.format(sb['n']):>18}  {'delta':>10}")

def row(label, a, b):
    if math.isnan(a) or math.isnan(b):
        print(f"  {label:>28}  {'NaN':>18}  {'NaN':>18}  {'─':>10}")
    else:
        d = a - b
        sign = "+" if d >= 0 else ""
        print(f"  {label:>28}  {a:>18.1f}  {b:>18.1f}  {sign}{d:>9.1f}")

row(f"%mg>{15}% [mg{FWD}]", sa["pct_mg15"], sb["pct_mg15"])
row(f"median mg{FWD}%",      sa["med_mg"],   sb["med_mg"])
row(f"mean mg{FWD}%",        sa["mean_mg"],  sb["mean_mg"])
row(f"median hold{FWD}%",    sa["med_h"],    sb["med_h"])

# Base rate (all with fwd)
all_fwd = a_fwd + b_fwd
if all_fwd:
    all_mgs = [r["mg11"] for r in all_fwd if not math.isnan(r["mg11"])]
    base_pct15  = sum(1 for v in all_mgs if v > 0.15) / len(all_mgs) * 100 if all_mgs else NaN
    base_median = statistics.median(all_mgs) * 100 if all_mgs else NaN
    print(f"\n  Base rate (all n={len(all_mgs)}): %mg>15%={base_pct15:.1f}%  median mg{FWD}={base_median:+.1f}%")

# PASS/FAIL verdict
delta_pct15  = sa["pct_mg15"] - sb["pct_mg15"] if not (math.isnan(sa["pct_mg15"]) or math.isnan(sb["pct_mg15"])) else NaN
delta_median = sa["med_mg"]   - sb["med_mg"]   if not (math.isnan(sa["med_mg"])   or math.isnan(sb["med_mg"]))   else NaN

print(f"\n  [VERDICT pre-commit]")
if math.isnan(delta_pct15):
    print(f"  INCONCLUSIVE — khong du data.")
elif sa["n"] < 5:
    print(f"  n Group A = {sa['n']} — QUA NHO de ket luan (<<5). Doc nhu goi-y, KHONG tradeable.")
elif delta_pct15 > 15 and delta_median > 5:
    print(f"  → PASS: A tach B ro: delta %mg>15% = +{delta_pct15:.1f}pp, delta median = +{delta_median:.1f}pp.")
    print(f"    net_k3>0 co tien-su tradeable (ANALYSIS xac nhan truoc khi thay so).")
elif delta_pct15 > 5 or delta_median > 3:
    print(f"  → MO: delta %mg>15% = {delta_pct15:+.1f}pp, delta median = {delta_median:+.1f}pp — yeu.")
    print(f"    Khong du manh de goi tradeable. Xep 'lien he mo ta', KHONG vao lenh.")
else:
    print(f"  → FAIL: delta %mg>15% = {delta_pct15:+.1f}pp, delta median = {delta_median:+.1f}pp — khong tach.")
    print(f"    +23.9pp fire-date la look-ahead artifact. 'net' khong tradeable tren K={K}.")

# ── BANK specific ──────────────────────────────────────────────────────────────
print()
print(DIV)
print("[3] BANK CHECK RIENG")
print(DIV)

bank = next((r for r in results if r["symbol"] == "BANK"), None)
if bank:
    print(f"  BANK chapter {bank['chapter']}: fire={bank['fire_date']}  fire+{K}={bank['fk_str']}")
    print(f"  oi_fire ({bank['fire_date']}): {bank['oi_fire']:>15,.0f}")
    print(f"  oi_fk   ({bank['fk_str']}): {bank['oi_fk']:>15,.0f}")
    print(f"  net_k3 = {bank['net_k3']:>+15,.0f}  → Group {bank['group']}")
    print(f"  mg{FWD} from {bank['fk_str']}: {fmg(bank['mg11'])}  h11={fh(bank['h11'])}  n11={fn(bank['n11'])}")
    if bank["group"] == "B":
        print(f"  BANK nằm Group B (net_k3 ≤ 0) — dù sau đó giá nổ mạnh.")
        print(f"  Giải thích: OI GIAM trong 3 ngày đầu chain (có thể: short covering trước khi gom thật bắt đầu,")
        print(f"  hoặc vị thế cũ đóng trước khi tích lũy mới mở). K=3 không bắt BANK.")
    else:
        print(f"  BANK nằm Group A (net_k3 > 0) → confirming.")
else:
    print("  BANK không có trong results (bị skip hoặc không có chapter).")

# ── Group A detail ─────────────────────────────────────────────────────────────
print()
print(DIV)
print(f"[4] GROUP A DETAIL (net_k3>0, {len(grp_a)} chapters)")
print(DIV)
a_sorted = sorted(grp_a, key=lambda x: x.get("mg11", NaN) if not math.isnan(x.get("mg11", NaN)) else -999, reverse=True)
hdr4 = f"{'symbol':>12}  {'fire':>10}  {'fk':>10}  {'net_k3':>12}  {'mg11%':>7}  {'h11':>5}  n11"
print(hdr4)
print("─" * len(hdr4))
for r in a_sorted:
    print(f"{r['symbol']:>12}  {r['fire_date']:>10}  {r['fk_str']:>10}  "
          f"{r['net_k3']:>+12,.0f}  {fmg(r['mg11']):>7}  {fh(r['h11']):>5}  {fn(r['n11'])}")

print()
print(f"[NOTE] K={K} LOCKED. mg{FWD} = 14-{K} = forward {FWD}d tu fire+{K}.")
print(f"       oi_usd tu freshwatch_daily (snapshot daily). net_k3 = oi(fire+{K}) - oi(fire).")
print(f"       fired_by A|B chua biet (schema debt). avg_px [SAN].")
print("DUNG.")
