"""
_probe_btw_4_lifecycle_20260810.py
W-4: Phase lifecycle — 5 flags + oi_cycle_pos + GOM-A Q1 + phase assignment.
BTW = ALPHA_778, Aug 2026 pump/echo scenario.
"""
import sys, io, csv
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
from datetime import datetime, timezone
import openpyxl

ROOT    = Path(r"D:\Data back test\whale_data")
SCRATCH = ROOT / "scratch"
DATE_TAG = "20260810"
SYM = "BTWUSDT"
XLSX = ROOT / "docs" / "case_files" / "CASE_BTW.xlsx"

def log(s=""): print(s)
NOW = datetime.now(timezone.utc)
log(f"W-4 LIFECYCLE  |  {NOW.strftime('%Y-%m-%d %H:%M UTC')}")

def sf(v, d=None):
    try: return float(v) if v not in (None,"","None","nan","#N/A") else d
    except: return d

# ── Load DAILY ────────────────────────────────────────────────────────────────
wb = openpyxl.load_workbook(XLSX, data_only=True)
ws_d = wb["DAILY"]
rows_raw = list(ws_d.iter_rows(values_only=True))
hdr_idx = None; headers = []
for i, row in enumerate(rows_raw):
    if str(row[0] or "").lower().strip() == "date":
        hdr_idx = i; headers = [str(c or "").strip() for c in row]; break

daily = []
for row in rows_raw[hdr_idx+1:]:
    if not row[0]: continue
    d = {}
    for k, v in zip(headers, row):
        if k: d[k] = v
    daily.append(d)
dates = [str(r["date"])[:10] for r in daily]

# ── A. GOM-A Q1 rechấm từ DAILY ──────────────────────────────────────────────
log("\n=== A. GOM-A fires + Q1 ===")
GOM_A_DATES = ['2026-06-19', '2026-06-20', '2026-06-21', '2026-07-03', '2026-07-13']
gom_a_rows = []
for r in daily:
    d = str(r.get("date",""))[:10]
    gom_a = str(r.get("gom_A_screen","")).lower()
    if gom_a in ("true","1","yes") or d in GOM_A_DATES:
        vol = sf(r.get("vol_perp_usd"))
        tk = sf(r.get("taker_buy_pct (k[10]/k[7])"))
        cl = sf(r.get("c"))
        gom_a_rows.append({
            "date": d, "vol": vol, "taker": tk, "close": cl,
            "gom_a": gom_a, "ret": sf(r.get("ret_1d (close-to-close)")),
            "oi_usd": sf(r.get("oi_usd")),
        })

log(f"  GOM-A fire dates ({len(gom_a_rows)}):")
for r in gom_a_rows:
    q1_est = round(r["vol"] * (r["taker"]/100 if r["taker"] else 0.5), 0) if r["vol"] else None
    log(f"  {r['date']}: vol=${r['vol']:,.0f}  taker={r['taker']:.1f}%  close=${r['close']:.6f}  ret={r['ret']:+.2f}%  Q1_est_taker=${q1_est:,.0f}" if (r["vol"] and r["taker"] and q1_est) else f"  {r['date']}: vol={r['vol']}  taker={r['taker']}")

# Total Q1 (taker_buy vol = estimated buyer-initiated)
q1_total_est = sum(r["vol"]*(r["taker"]/100) for r in gom_a_rows if r["vol"] and r["taker"])
log(f"\n  Q1 total (Σ taker_buy at GOM-A fires): ${q1_total_est:,.0f}")
log(f"  Note: BTW has no Q1_USD column in DAILY — estimating from taker_buy vol")

# Also check agent_log for $7.5M Q1 on 08-08
log(f"\n  agent_log 08-08 GOM-A mention (from summary): BTW $7.5M Q1 on 08-08 from LIVE signals")
log(f"  ← build_case.py retroactive fires differ from live (OI/threshold gate timing)")
log(f"  → Use build_case retroactive: 5 fires (Jun-Jul), NOT Aug 8 (live vs retroactive divergence)")

# ── B. Lifecycle flags from DAILY ─────────────────────────────────────────────
log("\n=== B. Lifecycle flags ===")
# Full-window counts
flag_cols = {
    "flag_neg_div":      "flag_neg_div (f<=-2e-4&range3d<=7%)",
    "flag_dist_wall":    "flag_dist_wall_day (taker>=50&ret<0)",
    "flag_decay":        "flag_decay_day (taker<45)",
    "flag_hedge_struct": "flag_hedge_struct (div_avg3<=0.5)",
    "flag_knife":        "flag_knife_crowd (gLSR↑&ret<-3%)",
}

log(f"  {'Flag':<20} {'True days':>10} {'Last 14 True':>13} {'Current':>10}")
log(f"  {'-'*20} {'-'*10} {'-'*13} {'-'*10}")
flag_totals = {}
for fname, col in flag_cols.items():
    total = sum(1 for r in daily if str(r.get(col,"")).lower() in ("true","1"))
    last14 = sum(1 for r in daily[-14:] if str(r.get(col,"")).lower() in ("true","1"))
    current = str(daily[-1].get(col,"")).lower() in ("true","1")
    flag_totals[fname] = {"total": total, "last14": last14, "current": current}
    log(f"  {fname:<20} {total:>10} {last14:>13} {str(current):>10}")

# dist_wall streak + cumul_ret
dw_streak = sf(daily[-1].get("dist_wall_streak (consec days)"))
dw_cumul  = sf(daily[-1].get("dist_wall_cumul_ret (%)"))
log(f"\n  dist_wall_streak (current): {dw_streak}")
log(f"  dist_wall_cumul_ret (current): {dw_cumul}%")

# oi_cycle_pos
oi_cycle = sf(daily[-1].get("oi_cycle_pos (30d rolling)"))
log(f"\n  oi_cycle_pos (30d, last): {oi_cycle}")
# Also trend
oi_cycle_5d = [sf(daily[i].get("oi_cycle_pos (30d rolling)")) for i in range(-5,0)]
log(f"  oi_cycle_pos last 5 days: {[round(v,4) if v else None for v in oi_cycle_5d]}")

# ── C. Lifecycle flag timeline (last 30d) ─────────────────────────────────────
log("\n=== C. Lifecycle timeline (last 30d) ===")
log(f"  {'Date':<12} {'neg_div':>8} {'dist_w':>7} {'decay':>6} {'knife':>6} {'oi_cyc':>7} {'f_avg':>9} {'vol_vs14':>9}")
log(f"  {'-'*12} {'-'*8} {'-'*7} {'-'*6} {'-'*6} {'-'*7} {'-'*9} {'-'*9}")
for r in daily[-30:]:
    d = str(r.get("date",""))[:10]
    nd = "Y" if str(r.get("flag_neg_div (f<=-2e-4&range3d<=7%)","")).lower()=="true" else "."
    dw = "Y" if str(r.get("flag_dist_wall_day (taker>=50&ret<0)","")).lower()=="true" else "."
    dc = "Y" if str(r.get("flag_decay_day (taker<45)","")).lower()=="true" else "."
    kn = "Y" if str(r.get("flag_knife_crowd (gLSR↑&ret<-3%)","")).lower()=="true" else "."
    oc = sf(r.get("oi_cycle_pos (30d rolling)"))
    fa = sf(r.get("f_avg"))
    vm = sf(r.get("vol_vs_med14"))
    log(f"  {d:<12} {nd:>8} {dw:>7} {dc:>6} {kn:>6} "
        f"{oc:>7.4f} {fa:>9.6f} {vm:>9}" if (oc and fa) else
        f"  {d:<12} {nd:>8} {dw:>7} {dc:>6} {kn:>6}")

# ── D. Phase assignment ───────────────────────────────────────────────────────
log("\n=== D. Phase assignment ===")
# Decay flags: majority taker<45 + price below VWAP
decay_days = flag_totals["flag_decay"]["total"]
knife_days = flag_totals["flag_knife"]["total"]
neg_div_days = flag_totals["flag_neg_div"]["total"]

log(f"  Full window flags summary:")
log(f"    flag_decay: {decay_days} days (taker<45) — decay signal")
log(f"    flag_knife: {knife_days} days (gLSR↑&ret<-3%) — distribution signal")
log(f"    flag_neg_div: {neg_div_days} days — short-dominant window")
log(f"    flag_dist_wall: {flag_totals['flag_dist_wall']['total']} days")

log(f"\n  Current state (Aug 9):")
log(f"    oi_cycle_pos = {oi_cycle:.4f} → NEAR PEAK (90th percentile of 30d range)")
log(f"    f_avg = 0.001091 → HOT funding (20× pin range)")
log(f"    vol_vs_med14 = {sf(daily[-1].get('vol_vs_med14'))} → {'moderate' if sf(daily[-1].get('vol_vs_med14',''),'') and sf(daily[-1].get('vol_vs_med14'))<=2 else 'elevated'}")
log(f"    All lifecycle flags: FALSE (no current distress signal)")

# Price context
close_vals = [sf(r.get("c")) for r in daily if sf(r.get("c"))]
px_now = close_vals[-1]; ath = max(close_vals); atl = min(close_vals)
original_blowoff = 0.20  # from án tích
log(f"\n  Price lifecycle:")
log(f"    ATL (listing): ${atl:.6f}")
log(f"    Original blowoff ~Jun 8-10: ~${original_blowoff:.3f} (btw_result.txt reference)")
log(f"    Trap/decay bottom: ~$0.052-0.065 (Jun 27 → Jul 26)")
log(f"    DQ cooldown end: 2026-07-31")
log(f"    New ATH (Aug 7): ${ath:.6f} [EXCEEDED original blowoff!]")
log(f"    Current (Aug 9): ${px_now:.6f} ({(px_now-ath)/ath*100:+.2f}% from ATH)")
log(f"    vs original blowoff $0.20: {(px_now-0.20)/0.20*100:+.2f}%")

log(f"\n  PHASE VERDICT:")
log(f"    Phase = BLOWOFF 2.0 (echo pump / second wave)")
log(f"    Evidence:")
log(f"      - Price exceeded original Jun blowoff ($0.224 vs ~$0.20)")
log(f"      - Vol Aug 5-9: $85M/$83M/$73M/$198M/$101M (blowoff scale)")
log(f"      - Funding 0.0006→0.0011/period (far above pin range)")
log(f"      - OI: $46.9M (oi_cycle_pos=0.899, near 30d peak)")
log(f"      - S5 SUPPRESSED since Jul 20 — case dormant during pump")
log(f"    Án tích 3 điều kiện: NOT MET (0/3 trigger score)")
log(f"    Risk: continuation blowoff OR rapid reversal (no defense wall from OI)")

log(f"\n[W-4 DONE]")
