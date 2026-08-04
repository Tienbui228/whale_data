#!/usr/bin/env python3
"""PROBE K1+K6: IDOL case_daily 03/08 + suppressor + campaign timeline.

K1: freshwatch daily fn-check, pos_r/acc_r/gLSR 03/08, OI 03-04/08,
    funding ghim?, suppressor scan (>=25% tu dinh), round-trip build zone.
K6: Campaign autopsy timeline voi bang chung so.
Output: docs/reports/_probe_idol_k1_k6_20260804.md
"""
import csv, io, sys
from datetime import datetime, timezone
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

WHALE   = Path(r"D:\Data back test\whale_data")
EXP_DIR = Path(r"D:\Check onchain fresh wallets\data\export")
OUT     = WHALE / "docs" / "reports" / "_probe_idol_k1_k6_20260804.md"

lines = []
def emit(*args):
    s = " ".join(str(a) for a in args)
    print(s); lines.append(s)

# ─── Load freshwatch_daily IDOL rows ──────────────────────────────────────────
# CSV columns: date (not date_str), symbol=IDOLUSDT, funding_n (not fn)
idol_rows = []
for fname in sorted(EXP_DIR.glob("freshwatch_daily_2026-*.csv")):
    for r in csv.DictReader(open(fname, encoding="utf-8-sig")):
        if r.get("symbol") == "IDOLUSDT":
            r["date_str"] = r.get("date", "")
            idol_rows.append(r)

idol_rows.sort(key=lambda r: r.get("date_str", ""))

emit("# PROBE K1+K6: IDOL — case_daily 03/08 + Suppressor + Campaign")
emit(f"Run: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
emit(f"Freshwatch IDOL rows loaded: {len(idol_rows)}")
emit("")

def g(r, k, default=None):
    v = r.get(k, default)
    if v in ("", None): return None
    try: return float(v)
    except: return v

# ─── K1: DAILY TABLE 25/07→latest ─────────────────────────────────────────────
emit("## K1 — Daily Series 25/07→latest")
emit("")
emit("| date | fn | px_avg | vol_perp_M | taker% | f_avg | oi_usd_M | pos_r | acc_r | gLSR | data_ok |")
emit("|------|----|---------|-----------:|-------:|------:|---------:|------:|------:|-----:|---------|")

recent_rows = [r for r in idol_rows if r.get("date_str","") >= "2026-07-25"]
for r in recent_rows:
    ds   = r.get("date_str","")
    fn   = g(r,"funding_n")
    px   = g(r,"px_avg")
    volq = g(r,"vol_quote");   volM = f"{volq/1e6:.2f}" if volq else "-"
    tk   = g(r,"taker_buy_pct"); tks = f"{tk*100:.1f}" if tk is not None else "-"
    fav  = g(r,"funding_avg"); favs = f"{fav:.5f}" if fav is not None else "-"
    oi   = g(r,"oi_usd");      oiM  = f"{oi/1e6:.2f}" if oi else "-"
    pr   = g(r,"lsr_pos_r");   prs  = f"{pr:.3f}" if pr else "-"
    ar   = g(r,"lsr_acc_r");   ars  = f"{ar:.3f}" if ar else "-"
    gl   = g(r,"lsr_global_r"); gls = f"{gl:.3f}" if gl else "-"
    dok  = r.get("data_ok","")
    fn_s = str(int(fn)) if fn is not None else "-"
    px_s = f"{px:.5f}" if px else "-"
    emit(f"| {ds} | {fn_s} | {px_s} | {volM} | {tks} | {favs} | {oiM} | {prs} | {ars} | {gls} | {dok} |")

emit("")

# ─── K1: L-41 verify ──────────────────────────────────────────────────────────
emit("## K1 — L-41 fn Verify (03/08)")
emit("")
row_0803 = next((r for r in idol_rows if r.get("date_str","") == "2026-08-03"), None)
row_0804 = next((r for r in idol_rows if r.get("date_str","") == "2026-08-04"), None)

if row_0803:
    fn_val = g(row_0803, "funding_n")
    emit(f"- 03/08 fn = {fn_val}")
    if fn_val is not None and int(fn_val) == 6:
        emit("- **L-41 PASS** — fn=6 xac nhan => dong an L-41 ✓")
    else:
        emit(f"- **L-41 FAIL** — fn={fn_val} (!=6) => tiep tuc giam sat")
else:
    emit("- 03/08 data MISSING trong freshwatch export")

if row_0804:
    fn_0804 = g(row_0804, "funding_n")
    emit(f"- 04/08 fn = {fn_0804} (partial — hom nay)")
emit("")

# ─── K1: Suppressor scan ──────────────────────────────────────────────────────
emit("## K1 — Suppressor Scan (post-climax >=25% tu dinh)")
emit("")

PEAK_PX = 0.02850
emit(f"- Dinh confirmed (01/08 lich su): {PEAK_PX:.5f} USDT")

last_row = idol_rows[-1] if idol_rows else None
if last_row:
    cur_px   = g(last_row, "px_avg") or 0
    cur_date = last_row.get("date_str","")
else:
    cur_px = 0; cur_date = "N/A"

drawdown_pct = (PEAK_PX - cur_px) / PEAK_PX * 100 if cur_px else 0
threshold_25 = PEAK_PX * 0.75
emit(f"- Latest px: {cur_px:.5f} USDT (date: {cur_date})")
emit(f"- Drawdown tu dinh: {drawdown_pct:.1f}%")
emit(f"- Nguong suppressor (75% dinh): {threshold_25:.5f} USDT")
if cur_px > 0 and cur_px <= threshold_25:
    emit(f"- **SUPPRESSOR: THOA** (cur {cur_px:.5f} <= {threshold_25:.5f})")
    emit(f"  -> Cooldown 14d, de xuat state SUPPRESSED -> operator ky")
else:
    emit(f"- **SUPPRESSOR: CHUA THOA** (cur {cur_px:.5f} > {threshold_25:.5f})")
emit("")

# Round-trip vs build zone
BUILD_LO  = 0.0155; BUILD_HI  = 0.0166
BUILD_MID = (BUILD_LO + BUILD_HI) / 2
if cur_px > 0:
    rt_mid = (cur_px / BUILD_MID - 1) * 100
    rt_lo  = (cur_px / BUILD_LO  - 1) * 100
    rt_hi  = (cur_px / BUILD_HI  - 1) * 100
    emit("## K1 — Round-trip vs Build Zone 0.0155-0.0166")
    emit("")
    emit("| anchor | build_px | cur_px | round-trip% |")
    emit("|--------|---------|--------|-------------|")
    emit(f"| MID    | {BUILD_MID:.5f} | {cur_px:.5f} | {rt_mid:+.1f}% |")
    emit(f"| LOW    | {BUILD_LO:.5f} | {cur_px:.5f} | {rt_lo:+.1f}% |")
    emit(f"| HIGH   | {BUILD_HI:.5f} | {cur_px:.5f} | {rt_hi:+.1f}% |")
    emit("")

# ─── K1: OI + funding regime 01-04/08 ────────────────────────────────────────
emit("## K1 — OI + Funding Regime 01→04/08")
emit("")
emit("| date | oi_usd_M | dOI | f_avg | regime | pos_r | gLSR |")
emit("|------|---------|-----|-------|--------|-------|------|")
oi_prev = None
for r in idol_rows:
    ds = r.get("date_str","")
    if ds < "2026-08-01": continue
    oi  = g(r,"oi_usd"); oiM = oi/1e6 if oi else None
    fav = g(r,"funding_avg")
    pr  = g(r,"lsr_pos_r")
    gl  = g(r,"lsr_global_r")
    doi = f"{(oiM - oi_prev):+.2f}M" if (oiM and oi_prev) else "—"
    regime = "PINNED" if fav is not None and abs(fav - 0.00005) < 1e-5 else ("FLOAT" if fav is not None else "—")
    oiMs = f"{oiM:.2f}M" if oiM else "—"
    favs = f"{fav:.6f}" if fav is not None else "—"
    prs  = f"{pr:.3f}" if pr else "—"
    gls  = f"{gl:.3f}" if gl else "—"
    emit(f"| {ds} | {oiMs} | {doi} | {favs} | {regime} | {prs} | {gls} |")
    if oiM: oi_prev = oiM
emit("")

# ─── K6: Campaign Timeline ────────────────────────────────────────────────────
emit("## K6 — Campaign Autopsy Timeline")
emit("")
emit("| window | event | so lieu | nguon | bang chung |")
emit("|--------|-------|---------|-------|-----------|")

def oi_row(d):
    r = next((x for x in idol_rows if x.get("date_str","") == d), None)
    if not r: return "—", "—", "—"
    oi = g(r,"oi_usd"); pr = g(r,"lsr_pos_r"); vol = g(r,"vol_quote")
    return (f"{oi/1e6:.2f}M" if oi else "—",
            f"{pr:.3f}" if pr else "—",
            f"{vol/1e6:.2f}M" if vol else "—")

oi_0723, pr_0723, vol_0723 = oi_row("2026-07-23")
oi_0728, pr_0728, vol_0728 = oi_row("2026-07-28")
oi_0731, pr_0731, vol_0731 = oi_row("2026-07-31")
oi_0801, pr_0801, vol_0801 = oi_row("2026-08-01")
oi_0802, pr_0802, vol_0802 = oi_row("2026-08-02")
oi_0803, pr_0803, vol_0803 = oi_row("2026-08-03")

px_0803s = f"{g(row_0803,'px_avg'):.5f}" if row_0803 and g(row_0803,'px_avg') else "?"

emit(f"| 03-05/07 | Staging on-chain | 7x20M=140M + others -> 273M tong rut Binance Alpha custody | EVENTS E1 (PENDING txhash) | Z4-rev: GOM qua Alpha mechanism |")
emit(f"| 23/07 | Bait-probe DEX | vol={vol_0723} (8x nen) spike collapse <4d | freshwatch | gLSR {oi_0723} crowd khong bi trap (sap lai) |")
emit(f"| 27/07 | OI accumulate | OI {oi_0728} -> tang | freshwatch | pos_r {pr_0728} 28/07 longs loading pre-ignition |")
emit(f"| 28/07 | OI ignition +62% | OI 6.60M->10.71M | freshwatch | taker=0.480 (bear) = MM mua limit khi retail sell |")
emit(f"| 28-31/07 | Build perp (nen do) | OI {oi_0731}, pos_r {pr_0731} | freshwatch | Longs loaded pre-markup; gLSR leo |")
emit(f"| 01/08 | Markup ignite | px +54.5%, vol={vol_0801} (~10x avg), taker=51.5% | freshwatch | BIDWALK-A crowd khong phat hien |")
emit(f"| 02/08 | Thoat perp + on-chain | OI {oi_0802}, pos_r sap {pr_0802}, rut 273M BSC | freshwatch+EVENTS | gLSR {oi_0802} sap = longs unwind |")
emit(f"| 03/08 | Post-climax | px {px_0803s}, OI {oi_0803} | freshwatch | Funding ghim/float? xem bang K1 OI |")
emit(f"| 04/08 | Round-trip hien tai | px {cur_px:.5f}, drawdown {drawdown_pct:.1f}% tu dinh | freshwatch latest | Suppressor {'THOA' if cur_px > 0 and cur_px <= threshold_25 else 'CHUA THOA'} |")
emit("")

# ─── K6: 4 thesis ranking ─────────────────────────────────────────────────────
emit("## K6 — Xep hang 4 gia thuyet ket thuc")
emit("")
emit("| rank | thesis | bang chung ung ho | bang chung phan | ket luan |")
emit("|------|--------|------------------|----------------|---------|")
emit("| #1 | flip-by-design | Rut 273M TRONG markup (02/08); pos_r sap dung khi crowd vao; staging 7xSent=0 truoc do | Z1 chua confirm redeposit -> cho K2 | DAN DAU neu K2 thay redeposit |")
emit("| #2 | fuel-died | gLSR 02/08 sap (crowd unwind, khong du luc); vol 03/08 sup | OI 02/08 khong sap manh (10.48M) — van con open | Co the ket hop voi flip |")
emit("| #3 | wrong-side | taker 01/08=51.5% (<55%) MM khong dat cuoc mot chieu; OI on dinh | Markup cuc manh +54.5% kho la wrong-side | THAP |")
emit("| #4 | unlock-deadline | Unlock 11/08 97.29M nhung markup no 10d TRUOC | W6: UNLIKELY theo lesson | LOAI |")
emit("")

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text("\n".join(lines), encoding="utf-8")
print(f"\nOutput: {OUT}")
