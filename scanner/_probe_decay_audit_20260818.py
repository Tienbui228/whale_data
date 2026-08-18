#!/usr/bin/env python3
"""[P2][P3][P4] B1-decay fire-audit — loader taker_buy_pct scale bug."""
import sys, io, csv, math
from pathlib import Path

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = Path(__file__).parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, r"D:\Data back test\binance-bot-signals")

from replay import parse_result_file, build_days
import yaml

FRESHWATCH_DIR = REPO / "data" / "export"
BOT_REPO = Path(r"D:\Data back test\binance-bot-signals")
CASE_STUDY = BOT_REPO / "docs" / "case study"
CFG = yaml.safe_load(open(BOT_REPO / "scanner" / "screener" / "thresholds.yaml", encoding="utf-8"))

FW_MAP = {"BANK":"BANKUSDT","TAG":"TAGUSDT","AKE":"AKEUSDT","BAS":"BASUSDT",
          "BASED":"BASEDUSDT","BTW":"BTWUSDT","BULLA":"BULLAUSDT","CLO":"CLOUSDT",
          "ESPORT":"ESPORTSUSDT","IDOL":"IDOLUSDT","POWER":"POWERUSDT","TUT":"TUTUSDT"}
RT_MAP = {"BANK":"BANK_result.txt","TAG":"TAG_result.txt","AKE":"ake_result.txt",
          "BAS":"bas_result.txt","BASED":"based_result.txt","BTW":"btw_result.txt",
          "BULLA":"bulla_result.txt","CLO":"clo_result.txt","ESPORT":"esport_result.txt",
          "IDOL":"idol_result.txt","POWER":"power_result.txt","TUT":"tut_result.txt"}

def load_fw(tok, x100=False):
    sym = FW_MAP[tok]
    rows = []
    for p in sorted(FRESHWATCH_DIR.glob("freshwatch_daily_*.csv")):
        with open(p, encoding="utf-8") as f:
            for r in csv.DictReader(f):
                if r.get("symbol") != sym: continue
                def _f(v):
                    if v is None or str(v).strip()=="": return float("nan")
                    try: x=float(v); return float("nan") if math.isnan(x) else x
                    except: return float("nan")
                tb = _f(r.get("taker_buy_pct"))
                if x100 and not math.isnan(tb): tb *= 100.0
                rows.append({"date":r["date"], "taker_buy_pct":tb,
                             "avg_px":_f(r.get("px_avg")), "oi_usd":_f(r.get("oi_usd")),
                             "vol_quote":_f(r.get("vol_quote"))})
    rows.sort(key=lambda x:x["date"])
    return rows

def load_rt(tok):
    fp = CASE_STUDY / RT_MAP[tok]
    if not fp.exists(): return []
    f,o,r,k = parse_result_file(fp); return build_days(f,o,r,k)

def find_day(days, dt_pat):
    for i,d in enumerate(days):
        if dt_pat in d.get("date","") or d.get("date","").endswith(dt_pat): return i
    return -1

def decay_check(days, i):
    """Manual: all 5-day taker_buy_pct < 45.0"""
    hold = 5; tb_max = 45.0
    if i < hold - 1: return False, "warmup"
    tbs = [days[j].get("taker_buy_pct", float("nan")) for j in range(i-hold+1, i+1)]
    if any(math.isnan(v) for v in tbs): return False, f"nan tbs={tbs}"
    fires = all(v < tb_max for v in tbs)
    return fires, tbs

DIV = "="*78

# ── [P2] BULLA 07-20 fire audit ─────────────────────────────────────────────
print(f"{DIV}\n[P2] BULLA 07-20 B1-decay fire-audit\n{DIV}")

# Load 3 ways: freshwatch raw, freshwatch x100, result.txt
fw_raw = load_fw("BULLA", x100=False)
fw_x100 = load_fw("BULLA", x100=True)
rt = load_rt("BULLA")

for label, days in [("freshwatch RAW (probe loader)", fw_raw),
                    ("freshwatch ×100 (production loader)", fw_x100),
                    ("result.txt", rt)]:
    idx = find_day(days, "07-20")
    if idx < 0:
        print(f"\n  [{label}] 07-20 NO_DATA (len={len(days)})"); continue
    fires, info = decay_check(days, idx)
    print(f"\n  [{label}] BULLA 07-20 idx={idx}")
    print(f"    taker_buy_pct 5-day window (i-4..i): {info}")
    print(f"    decay fires (all < 45.0): {fires}")
    d = days[idx]
    print(f"    context: px={d.get('avg_px'):.5f}  oi={d.get('oi_usd'):.0f}  vol={d.get('vol_quote'):.0f}")

# ── [P3] loader map compare — result.txt vs freshwatch on same day ──────────
print(f"\n{DIV}\n[P3] Loader map compare (BULLA 07-16..07-20)\n{DIV}")
print(f"  {'date':>7}  {'src':>28}  {'taker_buy_pct':>14}  {'scale':>8}")
for dt in ["07-16","07-17","07-18","07-19","07-20"]:
    for label, days in [("result.txt", rt), ("freshwatch RAW", fw_raw), ("freshwatch ×100", fw_x100)]:
        idx = find_day(days, dt)
        if idx < 0: continue
        tb = days[idx].get("taker_buy_pct", float("nan"))
        scale = "PERCENT" if tb > 1.5 else "FRACTION"
        print(f"  {dt:>7}  {label:>28}  {tb:>14.4f}  {scale:>8}")

# ── [P4] 6-token cluster: real decay vs loader-false-positive ──────────────
print(f"\n{DIV}\n[P4] 6-token cluster 07-20: decay REAL vs FALSE-POSITIVE\n{DIV}")

cluster = ["POWER","BASED","BAS","IDOL","TUT","BULLA"]
print(f"  {'token':>7} | {'fw_raw fires?':>13} | {'fw_x100 fires?':>15} | {'rt fires?':>10} | verdict")
print("  " + "─"*95)
for tok in cluster:
    fw_r = load_fw(tok, x100=False)
    fw_100 = load_fw(tok, x100=True)
    rt_ = load_rt(tok)
    def _fire(days):
        i = find_day(days, "07-20")
        if i < 0: return "NO_DATA"
        f, _ = decay_check(days, i)
        return "FIRE" if f else "clear"
    r_raw = _fire(fw_r)
    r_100 = _fire(fw_100)
    r_rt  = _fire(rt_)
    # Verdict logic
    if r_raw == "FIRE" and r_100 == "clear" and r_rt == "clear":
        v = "→ LOADER BUG (fake fire vì fraction scale)"
    elif r_raw == "FIRE" and r_100 == "FIRE":
        v = "→ REAL decay (fires cả 2 scale)"
    elif r_raw == "FIRE" and r_100 == "FIRE" and r_rt == "clear":
        v = "→ DATA DRIFT giữa result.txt và freshwatch"
    else:
        v = f"→ mixed ({r_raw}/{r_100}/{r_rt})"
    print(f"  {tok:>7} | {r_raw:>13} | {r_100:>15} | {r_rt:>10} | {v}")

# ── Full-universe: after fix, how many decay-fires remain 07-20? ────────────
print(f"\n{DIV}\n[P4-extra] Post-fix simulation: 12 tokens 07-20 decay fires\n{DIV}")
tokens_12 = list(FW_MAP.keys())
n_fake = n_real = n_nodata = 0
for tok in tokens_12:
    fw_r = load_fw(tok, x100=False)
    fw_100 = load_fw(tok, x100=True)
    ir = find_day(fw_r, "07-20"); i1 = find_day(fw_100, "07-20")
    if ir < 0 or i1 < 0: n_nodata += 1; continue
    fr,_ = decay_check(fw_r, ir); f1,_ = decay_check(fw_100, i1)
    if fr and not f1: n_fake += 1
    elif fr and f1:   n_real += 1
print(f"  fake-fires do loader bug: {n_fake}/12")
print(f"  real-fires (persist sau fix): {n_real}/12")
print(f"  no-data:                  {n_nodata}/12")

print(f"\n{DIV}\nVERDICT\n{DIV}")
print("  → BUG DEV (loader scale mismatch), KHÔNG phải B1 logic bug hay precedence-real")
print("  → Fix: replay_phase.py::load_freshwatch_days() ×100 taker_buy_pct")
print("  → Production loader fw_loader_utils.py:108 đã ×100 (verified) — probe loader thiếu")
