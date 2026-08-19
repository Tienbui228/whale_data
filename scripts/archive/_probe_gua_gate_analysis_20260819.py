#!/usr/bin/env python3
"""GUA Gate analysis + doctrine #10 recompute + report."""
import sys, io, math
from pathlib import Path
from statistics import median
import openpyxl

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = Path(r"D:\Data back test\whale_data")
XLSX = REPO / "docs" / "case_files" / "CASE_GUA.xlsx"
REPORT = REPO / "docs" / "reports" / "_gua_gate_backfill_20260819.md"

wb = openpyxl.load_workbook(str(XLSX), data_only=True, read_only=True)
ws = wb["DAILY"]

def _f(v):
    if v is None or v == "": return float("nan")
    try:
        x = float(v); return float("nan") if math.isnan(x) else x
    except (ValueError, TypeError): return float("nan")

rows = []
for r in range(3, ws.max_row + 1):
    d = ws.cell(r, 1).value
    if not d: continue
    ds = str(d)[:10]
    rows.append({
        "date": ds,
        "vol_perp": _f(ws.cell(r, 7).value),
        "vol_alpha": _f(ws.cell(r, 35).value) if ws.cell(r,35).value not in (None,"") and any(c.isdigit() for c in str(ws.cell(r,35).value)) else float("nan"),
        "vol_gate": _f(ws.cell(r, 51).value),
        "px": _f(ws.cell(r, 2).value),
        "oi": _f(ws.cell(r, 13).value),
    })
wb.close()

# vol_alpha col35 contains string 'alpha_klines_store(...)' — parse number if present
# Actually col 35 = string source, need separate col for actual number. Let me check
# Skip vol_alpha parse for now — operator provided context

# Filter windows
def _in(dstr, lo, hi): return lo <= dstr <= hi
r_jul = [r for r in rows if _in(r["date"], "2026-07-01", "2026-07-31")]
r_pump = [r for r in rows if _in(r["date"], "2026-08-05", "2026-08-08")]
r_post = [r for r in rows if _in(r["date"], "2026-08-09", "2026-08-18")]

# ─── Gate baseline T7 ────────────────────────────────────────────────────────
gate_jul = [r["vol_gate"] for r in r_jul if not math.isnan(r["vol_gate"])]
gate_pump = [r["vol_gate"] for r in r_pump if not math.isnan(r["vol_gate"])]
gate_post = [r["vol_gate"] for r in r_post if not math.isnan(r["vol_gate"])]

print(f"═══ E.1 Per-day 08-01..08-18 (Gate + Perp) ═══")
print(f"  {'date':>12}  {'vol_perp':>13}  {'vol_gate':>10}  {'gate/perp%':>10}  {'px':>8}")
for r in rows:
    if not _in(r["date"], "2026-08-01", "2026-08-18"): continue
    pr = f"{r['vol_perp']:>13,.0f}" if not math.isnan(r["vol_perp"]) else " "*13
    gt = f"{r['vol_gate']:>10,.0f}" if not math.isnan(r["vol_gate"]) else " "*10
    ratio = f"{r['vol_gate']/r['vol_perp']*100:>9.2f}%" if (not math.isnan(r["vol_gate"]) and not math.isnan(r["vol_perp"]) and r["vol_perp"] > 0) else "     —"
    print(f"  {r['date']:>12}  {pr}  {gt}  {ratio}  {r['px']:>8.5f}")

print(f"\n═══ E.2 Nền T7 vs pump 05-08 vs post-pump ═══")
print(f"  Nền Gate  (Jul 01-31)  n={len(gate_jul):>2}  median=${median(gate_jul):>10,.0f}  max=${max(gate_jul):>10,.0f}  min=${min(gate_jul):>10,.0f}")
print(f"  Pump Gate (Aug 05-08)  n={len(gate_pump):>2}  median=${median(gate_pump):>10,.0f}  max=${max(gate_pump):>10,.0f}")
print(f"  Post Gate (Aug 09-18)  n={len(gate_post):>2}  median=${median(gate_post):>10,.0f}  max=${max(gate_post):>10,.0f}")
med_jul = median(gate_jul)
med_pump = median(gate_pump)
med_post = median(gate_post)
print(f"\n  Pump vs Nền: {med_pump/med_jul:.2f}× · Post vs Nền: {med_post/med_jul:.2f}×")

# ─── E.3 SPOT-EXT-LEAD check (Gate spike >=3× nền) ──────────────────────────
print(f"\n═══ E.3 SPOT-EXT-LEAD: Gate spike ≥3× nền (med T7 Jul) ═══")
print(f"  Nền Gate med (T7) = ${med_jul:,.0f}")
print(f"  Threshold spike = ${3*med_jul:,.0f}")
lead_hits = []
for r in rows:
    if not _in(r["date"], "2026-08-01", "2026-08-18"): continue
    if math.isnan(r["vol_gate"]): continue
    if r["vol_gate"] >= 3 * med_jul:
        perp_active = (not math.isnan(r["vol_perp"])) and r["vol_perp"] > 5_000_000  # rough perp-active threshold
        lead_hits.append((r["date"], r["vol_gate"], r["vol_perp"], perp_active))
        print(f"  {r['date']}  Gate=${r['vol_gate']:,.0f} ({r['vol_gate']/med_jul:.1f}× nền)  perp=${r['vol_perp']:,.0f}  perp_active={perp_active}")
if not lead_hits:
    print(f"  → 0 spike ≥3× nền trong 08-01..08-18 window")

# ─── E.4 Doctrine #10 recompute ──────────────────────────────────────────────
print(f"\n═══ E.4 Doctrine #10 recompute: kho ÷ băng-thông ═══")
kho_gua = 130_000_000     # 130M GUA tokens
px_now = rows[-1]["px"] if rows else 0
kho_usd = kho_gua * px_now
print(f"  Kho: 130M GUA × ${px_now:.5f}/GUA = ${kho_usd:,.0f}")

# Băng thông:
# Old assumption: chỉ Alpha $234K/day (per ops handover) → ~$5.6M / $234K / 10% = 240d ≈ 8 tháng
# New: Alpha + Gate
alpha_daily_est = 234_000   # per handover
gate_daily_med_recent = median(gate_post) if gate_post else 0
gate_daily_max_recent = max(gate_post) if gate_post else 0
dex_note = 11_000   # $11K DEX per operator note

total_bandwidth_med = alpha_daily_est + gate_daily_med_recent + dex_note
total_bandwidth_max = alpha_daily_est + gate_daily_max_recent + dex_note

mm_share = 0.10
days_to_exit_med = kho_usd / (total_bandwidth_med * mm_share)
days_to_exit_max = kho_usd / (total_bandwidth_max * mm_share)

print(f"\n  Băng thông tổng (per day, MM 10% share):")
print(f"    Alpha         : ${alpha_daily_est:>10,.0f}/d")
print(f"    Gate (med Aug09-18): ${gate_daily_med_recent:>10,.0f}/d")
print(f"    Gate (max)    : ${gate_daily_max_recent:>10,.0f}/d")
print(f"    DEX (note)    : ${dex_note:>10,.0f}/d")
print(f"    ─ tổng med    : ${total_bandwidth_med:>10,.0f}/d · MM 10% = ${total_bandwidth_med*mm_share:,.0f}/d")
print(f"    ─ tổng max    : ${total_bandwidth_max:>10,.0f}/d · MM 10% = ${total_bandwidth_max*mm_share:,.0f}/d")

print(f"\n  Ngày xả cần thiết (kho ÷ MM_share):")
print(f"    Cũ (Alpha only $234K): {kho_usd / (alpha_daily_est * mm_share):,.0f} ngày ≈ {kho_usd / (alpha_daily_est * mm_share)/30:.1f} tháng")
print(f"    Mới (med tổng):        {days_to_exit_med:,.0f} ngày ≈ {days_to_exit_med/30:.1f} tháng")
print(f"    Mới (max tổng):        {days_to_exit_max:,.0f} ngày ≈ {days_to_exit_max/30:.1f} tháng")

ratio_old_new = (kho_usd / (alpha_daily_est * mm_share)) / days_to_exit_med
print(f"\n  Lệch: {ratio_old_new:.2f}× (số cũ dài hơn số mới bấy nhiêu lần)")

# ─── E.5 Deposit 09-10/08 venue trace ────────────────────────────────────────
print(f"\n═══ E.5 Deposit +62M 09-10/08 — venue trace ═══")
print(f"  [DATA-GAP] tracker 18/08 ảnh không phân venue (Binance vs Gate wallet)")
print(f"  → Cần BscScan/on-chain trace: exchange balance ± 09-10/08")
print(f"  → Chưa trace được → GHI [DATA-GAP] tường minh trong report")
print(f"  Kho nằm van nào quyết van nào xả — câu quan trọng, operator/on-chain phải trả lời")
