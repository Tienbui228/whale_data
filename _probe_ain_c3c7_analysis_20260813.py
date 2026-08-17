"""
_probe_ain_c3c7_analysis_20260813.py
AI-3→AI-8 analysis: AINUSDT bốn vân + hai lăng kính + rũ-đàn + venue + sanity.
Intel operator: 30M tokens ≈ $2.4M nạp từ 04/08.
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
import openpyxl, math
from datetime import datetime, date, timedelta, timezone

ROOT = Path(r"D:\Data back test\whale_data")
NOW = datetime.now(timezone.utc)

print("=" * 70)
print(f"AIN ANALYSIS — AI-3→AI-8 — {NOW.strftime('%Y-%m-%d %H:%M UTC')}")
print("=" * 70)

# ── Read CASE_AIN.xlsx DAILY ───────────────────────────────────────────────
case_path = ROOT / "docs" / "case_files" / "CASE_AIN.xlsx"
wb = openpyxl.load_workbook(case_path, read_only=True, data_only=True)
ws = wb["DAILY"]

all_rows = list(ws.iter_rows(values_only=True))
# Row0 = category labels, Row1 = HDR_LABELS, Row2+ = data
headers = list(all_rows[1])

_HMAP = {}
for h in headers:
    if h:
        short = str(h).split(" ")[0].split("(")[0].rstrip()
        _HMAP[short] = h
        _HMAP[str(h)] = h

# Column aliases: logical name → actual short key in this XLSX
ALIAS = {
    "close":           "c",
    "vol_q_usd":       "vol_perp_usd",
    "taker_pct":       "taker_buy_pct",
    "funding_d":       "f_avg",
    "div":             "div_raw",
    "flag_dist_wall":  "flag_dist_wall_day",
}

def sf(v, d=None):
    if v is None or v == "":
        return d
    if isinstance(v, float) and math.isnan(v):
        return d
    try:
        return float(v)
    except Exception:
        return d

def get(r, k, d=None):
    k2 = ALIAS.get(k, k)
    full_key = _HMAP.get(k2, k2)
    v = r.get(full_key)
    if v is None:
        v = r.get(k2)
    if v is None:
        v = r.get(k)
    return sf(v, d)

rows = []
for row in all_rows[2:]:
    r = dict(zip(headers, row))
    rows.append(r)

print(f"\nDAILY rows loaded: {len(rows)}")
if not rows:
    print("ERROR: no rows"); sys.exit(1)

def date_str(r):
    d = r.get("date")
    if d is None:
        return ""
    if hasattr(d, "strftime"):
        return d.strftime("%Y-%m-%d")
    return str(d)[:10]

# ── Build arrays ───────────────────────────────────────────────────────────
dates     = [date_str(r) for r in rows]
closes    = [get(r, "close") for r in rows]
pos_r     = [get(r, "pos_r") for r in rows]
acc_r     = [get(r, "acc_r") for r in rows]
div_avg3  = [get(r, "div_avg3") for r in rows]
div_raw   = [get(r, "div") for r in rows]
funding_d = [get(r, "funding_d") for r in rows]
ret_1d    = [get(r, "ret_1d") for r in rows]
vol_q     = [get(r, "vol_q_usd") for r in rows]
taker     = [get(r, "taker_pct") for r in rows]
oi_usd    = [get(r, "oi_usd") for r in rows]
gLSR      = [get(r, "gLSR") for r in rows]
N = len(rows)

# Quick verify
print(f"  Sample row2 close={closes[0]}, vol={vol_q[0]}, ret={ret_1d[0]}")
print(f"  Sample last close={closes[-1]}, pos_r={pos_r[-1]}, gLSR={gLSR[-1]}")

# ── AI-3. DEPOSIT WINDOW ───────────────────────────────────────────────────
print("\n" + "=" * 70)
print("AI-3. DEPOSIT WINDOW — SPRINT / GRIND / BLEED")
print("  Intel: 30M tokens ≈ $2.4M nạp từ 04/08")
print("=" * 70)

dep_start = "2026-08-04"
dep_end   = "2026-08-12"
dep_rows  = [(r, d) for r, d in zip(rows, dates) if dep_start <= d <= dep_end]
dep_dates_filt = [d for _, d in dep_rows]
dep_rows_only  = [r for r, _ in dep_rows]

dep_closes  = [get(r, "close") for r in dep_rows_only]
dep_rets    = [get(r, "ret_1d") for r in dep_rows_only]
dep_vols    = [get(r, "vol_q_usd") for r in dep_rows_only]
dep_funding = [get(r, "funding_d") for r in dep_rows_only]
dep_oi      = [get(r, "oi_usd") for r in dep_rows_only]
dep_glsr    = [get(r, "gLSR") for r in dep_rows_only]
dep_pos_r   = [get(r, "pos_r") for r in dep_rows_only]
dep_acc_r   = [get(r, "acc_r") for r in dep_rows_only]

print(f"\n  {'date':<12} {'close':>8} {'ret_1d':>8} {'vol_usd':>13} {'fund_d':>9} {'oi_usd':>12} {'gLSR':>6} {'pos_r':>7} {'acc_r':>7}")
for i, d in enumerate(dep_dates_filt):
    c  = dep_closes[i] or 0
    r1 = dep_rets[i] or 0
    v  = dep_vols[i] or 0
    f  = dep_funding[i] or 0
    o  = dep_oi[i] or 0
    g  = dep_glsr[i] or 0
    p  = dep_pos_r[i] or 0
    a  = dep_acc_r[i] or 0
    print(f"  {d:<12} {c:>8.5f} {r1:>+8.2f} {v:>13,.0f} {f:>9.5f} {o:>12,.0f} {g:>6.3f} {p:>7.3f} {a:>7.3f}")

c_entry = dep_closes[0] if dep_closes else None
c_exit  = dep_closes[-1] if dep_closes else None
net_ret = (c_exit - c_entry) / c_entry * 100 if c_entry and c_exit else None

dep_vols_clean = [v for v in dep_vols if v]
vol_max_day  = max(dep_vols_clean) if dep_vols_clean else 0
vol_mean_day = sum(dep_vols_clean) / len(dep_vols_clean) if dep_vols_clean else 0

green_days = [d for d, r in zip(dep_dates_filt, dep_rets) if r is not None and r > 0]
red_days   = [d for d, r in zip(dep_dates_filt, dep_rets) if r is not None and r < 0]

oi_start = next((o for o in dep_oi if o), None)
oi_end   = next((o for o in reversed(dep_oi) if o), None)
oi_delta = (oi_end - oi_start) if oi_start and oi_end else None

pr_dep_start = next((p for p in dep_pos_r if p is not None), None)
pr_dep_end   = next((p for p in reversed(dep_pos_r) if p is not None), None)
pr_dep_delta = pr_dep_end - pr_dep_start if pr_dep_start is not None and pr_dep_end is not None else None

print(f"\n  Entry (Aug04): {c_entry:.5f}" if c_entry else "  Entry: N/A")
print(f"  Exit  (Aug12): {c_exit:.5f}" if c_exit else "  Exit: N/A")
print(f"  Net ret:       {net_ret:+.1f}%" if net_ret is not None else "  Net ret: N/A")
print(f"  Green/Red:     {len(green_days)}/{len(red_days)}")
print(f"  Vol max day:   ${vol_max_day:,.0f}")
print(f"  Vol mean day:  ${vol_mean_day:,.0f}")
print(f"  OI start:      ${oi_start:,.0f}" if oi_start else "  OI start: N/A")
print(f"  OI end:        ${oi_end:,.0f}" if oi_end else "  OI end: N/A")
print(f"  OI delta:      ${oi_delta:+,.0f}" if oi_delta is not None else "  OI delta: N/A")
print(f"  pos_r start:   {pr_dep_start:.3f}" if pr_dep_start is not None else "  pos_r start: N/A")
print(f"  pos_r end:     {pr_dep_end:.3f}" if pr_dep_end is not None else "  pos_r end: N/A")
print(f"  pos_r delta:   {pr_dep_delta:+.3f}" if pr_dep_delta is not None else "  pos_r delta: N/A")

# Aug07 spike check
vol_aug07 = dep_vols[3] if len(dep_vols) > 3 else 0
spike_flag = bool(vol_aug07 and vol_mean_day and vol_aug07 > vol_mean_day * 3)
print(f"\n  Aug07 vol: ${vol_aug07:,.0f}" if vol_aug07 else "  Aug07 vol: N/A")
print(f"  Spike flag (Aug07 > 3× mean): {'YES' if spike_flag else 'NO'}")

# Taxonomy
if len(red_days) > len(green_days) and net_ret is not None and abs(net_ret) < 20:
    if oi_delta is not None and oi_delta > 0 and pr_dep_delta is not None and pr_dep_delta < -0.05:
        taxonomy = "BLEED/DEPOSIT — OI leo (vị thế mở thêm), pos_r giảm (acc giảm tỷ lệ), giá mostly đỏ → nhồi lệnh phân phối dần"
    else:
        taxonomy = "BLEED — nhiều đỏ, net thấp, không có sprint spike rõ"
elif spike_flag:
    taxonomy = "SPRINT — spike 1 ngày, trước/sau bleed"
else:
    taxonomy = "GRIND — slow, no spike, OI tích lũy chậm"
print(f"\n  ► TAXONOMY: {taxonomy}")

# Deposit ladder
print("\n  LADDER — phân tầng nạp theo vol:")
print(f"  {'date':<12} {'vol_usd':>14} {'tier':<18} {'ret_1d':>8}")
for i, d in enumerate(dep_dates_filt):
    v = dep_vols[i] or 0
    r1 = dep_rets[i] or 0
    tier = "TIER1-spike" if v > 2_000_000 else "TIER2-mod" if v > 500_000 else "TIER3-quiet"
    print(f"  {d:<12} ${v:>13,.0f} {tier:<18} {r1:>+8.2f}%")

# Token estimate
if c_exit:
    dep30m_usd = 30e6 * c_exit
    print(f"\n  30M tokens at Aug12 close ${c_exit:.5f} = ${dep30m_usd:,.0f}")
oi_tokens_est = (oi_end / c_exit) if oi_end and c_exit and c_exit > 0 else None
if oi_tokens_est:
    print(f"  OI est tokens: {oi_tokens_est:,.0f}  |  30M/OI = {30e6/oi_tokens_est*100:.1f}%")

# ── AI-4. BỐN VÂN ─────────────────────────────────────────────────────────
print("\n" + "=" * 70)
print("AI-4. BỐN VÂN TRIAGE")
print("=" * 70)

# VÂN 1: pos_r
print("\n  VÂN 1 — pos_r TREND")
pr_valid = [(d, p) for d, p in zip(dates, pos_r) if p is not None]
pr_jan_mar = [(d, p) for d, p in pr_valid if "2026-01" <= d <= "2026-03-31"]
pr_apr_jun = [(d, p) for d, p in pr_valid if "2026-04-01" <= d <= "2026-06-30"]
pr_jul_aug = [(d, p) for d, p in pr_valid if "2026-07-01" <= d <= "2026-08-12"]

def mean_pr(pairs):
    if not pairs:
        return None
    return sum(p for _, p in pairs) / len(pairs)

pr_m1 = mean_pr(pr_jan_mar)
pr_m2 = mean_pr(pr_apr_jun)
pr_m3 = mean_pr(pr_jul_aug)

if pr_m1:
    print(f"  Jan-Mar avg pos_r: {pr_m1:.3f}")
if pr_m2:
    print(f"  Apr-Jun avg pos_r: {pr_m2:.3f}")
if pr_m3:
    print(f"  Jul-Aug12 avg pos_r: {pr_m3:.3f}")

pr_last90 = [(i, p) for i, (d, p) in enumerate(pr_valid) if d >= "2026-05-01"]
if len(pr_last90) >= 5:
    xs = [i for i, _ in pr_last90]
    ys = [p for _, p in pr_last90]
    xm, ym = sum(xs)/len(xs), sum(ys)/len(ys)
    num = sum((x-xm)*(y-ym) for x,y in zip(xs,ys))
    den = sum((x-xm)**2 for x in xs)
    slope = num/den if den else 0
    print(f"  OLS slope (May01-Aug12, {len(pr_last90)} pts): {slope:+.4f} {'↑ RISING' if slope>0 else '↓ FALLING'}")

ath_close = max((c for c in closes if c), default=None)
ath_idx   = next((i for i, c in enumerate(closes) if c == ath_close), None)
if ath_idx is not None:
    pr_at_ath = pos_r[ath_idx]
    print(f"  ATH ({dates[ath_idx]}, ${ath_close:.5f}): pos_r={pr_at_ath:.3f}" if pr_at_ath else f"  ATH ({dates[ath_idx]}): pos_r=N/A")

print(f"  Last 5 pos_r: {[f'{p:.3f}' if p else 'N/A' for _, p in pr_valid[-5:]]}")

pr_price = [(p, c) for p, c in zip(pos_r, closes) if p is not None and c is not None]
if len(pr_price) > 10:
    same = sum(1 for i in range(1, len(pr_price)) if
               (pr_price[i][0] - pr_price[i-1][0]) * (pr_price[i][1] - pr_price[i-1][1]) >= 0)
    total = len(pr_price) - 1
    frac = same / total if total else 0
    label = "RETAIL-FOLLOW (pos_r theo giá)" if frac > 0.55 else "INVERSO (pos_r ngược giá → gom signal)"
    print(f"  pos_r vs price: {same}/{total} same dir → {label}")

# VÂN 2: Funding / hedge
print("\n  VÂN 2 — FUNDING / HEDGE-FARM (div_avg3 < 1)")
div_valid = [(d, v) for d, v in zip(dates, div_avg3) if v is not None]
hedge_periods = [(d, v) for d, v in div_valid if v < 1.0]
print(f"  Total days div_avg3 < 1.0: {len(hedge_periods)} / {len(div_valid)}")

blocks = []
cur_block = []
for d, v in div_valid:
    if v < 1.0:
        cur_block.append((d, v))
    else:
        if cur_block:
            blocks.append(cur_block)
            cur_block = []
if cur_block:
    blocks.append(cur_block)

print(f"  Continuous hedge blocks: {len(blocks)}")
for b in blocks:
    avg_d = sum(v for _, v in b) / len(b)
    print(f"    {b[0][0]} → {b[-1][0]} ({len(b)}d, avg_div={avg_d:.3f})")

fund_valid = [(d, f) for d, f in zip(dates, funding_d) if f is not None]
neg_fund   = [(d, f) for d, f in fund_valid if f < -0.0001]
pos_fund   = [(d, f) for d, f in fund_valid if f > 0.0001]
print(f"  Funding days: neg={len(neg_fund)}, pos={len(pos_fund)}, total={len(fund_valid)}")
if neg_fund:
    mn = min(f for _, f in neg_fund)
    mn_d = [d for d, f in neg_fund if f == mn][0]
    print(f"  Most negative: {mn:.6f} on {mn_d}")
if pos_fund:
    mx = max(f for _, f in pos_fund)
    mx_d = [d for d, f in pos_fund if f == mx][0]
    print(f"  Most positive: {mx:.6f} on {mx_d}")

longest_block = max(blocks, key=lambda b: len(b)) if blocks else []
gome_pass = len(longest_block) >= 14
print(f"  Longest hedge block: {len(longest_block)}d {'→ GOM-E PASS' if gome_pass else '→ GOM-E FAIL'}")

# Un-hedge crossings
un_hedge_crossings = []
for i in range(1, len(div_valid)):
    if div_valid[i-1][1] < 1.0 and div_valid[i][1] >= 1.0:
        post = [v for _, v in div_valid[i:i+5]]
        sustained = sum(1 for v in post if v >= 1.0) >= 3
        un_hedge_crossings.append((div_valid[i][0], div_valid[i][1], sustained))
print(f"  Un-hedge crossings (div <1→≥1): {len(un_hedge_crossings)}")
for d, v, sustained in un_hedge_crossings:
    print(f"    {d}: div={v:.3f} sustained={'YES ▶ SIGNAL' if sustained else 'NO'}")

# VÂN 3: Dip recovery
print("\n  VÂN 3 — RANGE CONTROL (dip recovery)")
ret_triplets = [(d, r, c) for d, r, c in zip(dates, ret_1d, closes) if r is not None and c is not None]
dip_recovery  = []
no_recovery   = []
for i in range(len(ret_triplets) - 1):
    d, r, c = ret_triplets[i]
    if r <= -5.0:
        nd, nr, nc = ret_triplets[i+1]
        if nr > 0:
            dip_recovery.append((d, r, nd, nr))
        else:
            no_recovery.append((d, r, nd, nr))

total_dips = len(dip_recovery) + len(no_recovery)
dr_rate = len(dip_recovery) / total_dips * 100 if total_dips else 0
print(f"  Days ret≤-5%: {total_dips}")
print(f"  Next-day recovery: {len(dip_recovery)}/{total_dips} = {dr_rate:.0f}%")

dip_days_all = [i for i, (_, r, _) in enumerate(ret_triplets) if r <= -5.0]
multi_rec = []
for idx in dip_days_all:
    w = ret_triplets[idx+1:idx+4]
    if any(r > 0 for _, r, _ in w):
        multi_rec.append(ret_triplets[idx][0])
print(f"  3d recovery rate: {len(multi_rec)}/{len(dip_days_all)} = {len(multi_rec)/len(dip_days_all)*100:.0f}%" if dip_days_all else "  3d recovery: N/A")

print(f"  ATH: ${ath_close:.5f} on {dates[ath_idx]}" if ath_idx is not None and ath_close else "")
if closes[-1] and ath_close:
    dd = (closes[-1] - ath_close) / ath_close * 100
    print(f"  Aug12 close: ${closes[-1]:.5f}, drawdown from ATH: {dd:.1f}%")

# VÂN 4: On-chain / venue
print("\n  VÂN 4 — ON-CHAIN / VENUE")
print("  Binance spot AINUSDT: ABSENT (HTTP 400)")
print("  Binance Alpha BAPI: NOT FOUND in alpha list (confirmed AI-0a)")
print("  Gate.io AIN_USDT: vol24h=$78,181 — THIN PRIMARY SPOT")
print("  GeckoTerminal AIN: 3+ pools, total vol24h ~$44K — fragmented")
print("  On-chain blockchain: UNKNOWN — CoinGecko returned irrelevant results")
print("  underlyingSubType: ['AI'] → AI narrative token category")
print("  CẦN OPERATOR: xác định chain + vesting schedule + wallet 30M token")

# ── AI-5. HAI LĂNG KÍNH ────────────────────────────────────────────────────
print("\n" + "=" * 70)
print("AI-5. HAI LĂNG KÍNH (GOM-D + GOM-E)")
print("=" * 70)

# GOM-D
print("\n  LĂNG KÍNH 1 — GOM-D (D1/D3/D4/D5)")

vol_valid = [(d, v, r) for d, v, r in zip(dates, vol_q, ret_1d)
             if v is not None and r is not None]

med14_vols = []
for i in range(len(vol_valid)):
    window = [x[1] for x in vol_valid[max(0,i-14):i] if x[1]]
    med14 = sorted(window)[len(window)//2] if window else vol_valid[i][1]
    med14_vols.append(med14 or 1)

# D1: vol≥8×med + ret>0
d1_events = [(vol_valid[i][0], vol_valid[i][1], vol_valid[i][2], med14_vols[i])
             for i in range(len(vol_valid))
             if vol_valid[i][1] and vol_valid[i][1] >= 8 * med14_vols[i] and vol_valid[i][2] > 0]
d1_pass = len(d1_events) >= 1
print(f"  D1: vol≥8×med14 + ret>0: {len(d1_events)} events {'PASS' if d1_pass else 'FAIL'}")
for d, v, r, m in d1_events[:5]:
    print(f"      {d}: {v/m:.1f}× ret={r:+.1f}%")
if len(d1_events) > 5:
    print(f"      ... ({len(d1_events)-5} more)")

# D3: ≥3d consecutive clusters ≥4×med14
clusters = []
cur = []
for i, (d, v, r) in enumerate(vol_valid):
    if med14_vols[i] and v and v >= 4 * med14_vols[i]:
        cur.append(d)
    else:
        if len(cur) >= 3:
            clusters.append(cur.copy())
        cur = []
if len(cur) >= 3:
    clusters.append(cur)
d3_pass = len(clusters) >= 1
print(f"  D3: vol clusters ≥3d ≥4×med14: {len(clusters)} {'PASS' if d3_pass else 'FAIL'}")
for c in clusters:
    print(f"      {c[0]} → {c[-1]} ({len(c)}d)")

# D4: wake-up (quiet then ≥+15% in 1d)
quiet_wake = []
for i in range(14, len(vol_valid)):
    d, v, r = vol_valid[i]
    prev_vols = [vol_valid[j][1] for j in range(i-7, i) if vol_valid[j][1]]
    prev_avg  = sum(prev_vols) / len(prev_vols) if prev_vols else 0
    lm = med14_vols[i-7] if i >= 7 else None
    if lm and prev_avg < 2 * lm and r >= 15:
        quiet_wake.append((d, r, v))
d4_pass = len(quiet_wake) >= 3
print(f"  D4: wake-up (quiet→ret≥+15%): {len(quiet_wake)} events {'PASS' if d4_pass else 'FAIL'}")
for d, r, v in quiet_wake[:3]:
    print(f"      {d}: +{r:.1f}%")

# D5: churn (high vol + |ret|<5%)
churn_days = [(vol_valid[i][0], vol_valid[i][1], vol_valid[i][2])
              for i in range(len(vol_valid))
              if vol_valid[i][1] and med14_vols[i] and
              vol_valid[i][1] >= 4 * med14_vols[i] and abs(vol_valid[i][2] or 0) < 5]
d5_pass = len(churn_days) >= 3
print(f"  D5: churn (≥4×med + |ret|<5%): {len(churn_days)} days {'PASS' if d5_pass else 'FAIL'}")

gomd_n = sum([d1_pass, d3_pass, d4_pass, d5_pass])
print(f"\n  GOM-D RESULT: {gomd_n}/4 PASS")

# GOM-E: hedge-farm
print("\n  LĂNG KÍNH 2 — GOM-E (hedge-farm)")
print(f"  Longest continuous div<1 block: {len(longest_block)}d" +
      (f" ({longest_block[0][0]} → {longest_block[-1][0]})" if longest_block else ""))
print(f"  Total hedge days: {len(hedge_periods)} / {len(div_valid)}")
print(f"  GOM-E: {'PASS' if gome_pass else 'FAIL'} (≥14d threshold)")

# ── AI-6. RŨ-ĐÀN GAUGE ─────────────────────────────────────────────────────
print("\n" + "=" * 70)
print("AI-6. RŨ-ĐÀN GAUGE (gLSR + acc_r around key events)")
print("=" * 70)

key_events = [
    ("2026-01-30", "Jan30 spike +17% 13.8×"),
    ("2026-03-10", "Mar10 pump +50% 87.5×"),
    ("2026-03-18", "Mar18 pump +21% 37.2×"),
    ("2026-04-11", "Apr11 pump +77% 22×"),
    ("2026-04-12", "Apr12 dump -18% 93.5×"),
    ("2026-05-13", "May13 ATH +35% 24.3×"),
    ("2026-05-14", "May14 dump -25% 24.4×"),
    ("2026-06-12", "Jun12 pump +27% 25.6×"),
    ("2026-06-26", "Jun26 dump -16% 54.2×"),
    ("2026-08-07", "Aug07 pump +12% [deposit]"),
]

print(f"\n  {'date':<12} {'event':<30} {'gLSR':>6} {'acc_r':>7} {'pos_r':>7} {'f_avg':>9}")
for evt_d, evt_label in key_events:
    idx = next((i for i, d in enumerate(dates) if d == evt_d), None)
    if idx is not None:
        g = gLSR[idx] or 0
        a = acc_r[idx] or 0
        p = pos_r[idx] or 0
        f = funding_d[idx] or 0
        print(f"  {evt_d:<12} {evt_label:<30} {g:>6.3f} {a:>7.3f} {p:>7.3f} {f:>9.6f}")
    else:
        print(f"  {evt_d:<12} {evt_label:<30} NO DATA")

# Deposit window gLSR
print(f"\n  gLSR deposit window Aug04-12:")
print(f"  {'date':<12} {'gLSR':>8} {'acc_r':>8} {'interp'}")
for i, d in enumerate(dep_dates_filt):
    g = dep_glsr[i]
    a = dep_acc_r[i] or 0
    if g is not None:
        interp = "retail LONG peak" if g >= 2.5 else "retail LONG" if g >= 1.5 else "neutral" if g >= 0.7 else "retail SHORT"
        print(f"  {d:<12} {g:>8.3f} {a:>8.3f} {interp}")

glsr_valid = [g for g in gLSR if g is not None]
if glsr_valid:
    glsr_mean = sum(glsr_valid) / len(glsr_valid)
    glsr_high = [g for g in glsr_valid if g >= 2.0]
    glsr_low  = [g for g in glsr_valid if g <= 0.7]
    print(f"\n  gLSR all: mean={glsr_mean:.3f}, ≥2.0: {len(glsr_high)}d, ≤0.7: {len(glsr_low)}d")

# acc_r trajectory
acc_valid = [(d, a) for d, a in zip(dates, acc_r) if a is not None]
for label, s, e in [("Mar", "2026-03-01", "2026-03-31"),
                     ("May", "2026-05-01", "2026-05-31"),
                     ("Jun", "2026-06-01", "2026-06-30"),
                     ("Aug04-12", "2026-08-04", "2026-08-12")]:
    sub = [a for d, a in acc_valid if s <= d <= e]
    if sub:
        print(f"  acc_r {label} avg: {sum(sub)/len(sub):.3f}")

# ── AI-7. SPOT / VENUE / DEPTH ─────────────────────────────────────────────
print("\n" + "=" * 70)
print("AI-7. SPOT / VENUE / DEPTH")
print("=" * 70)

c_cur = closes[-1] if closes[-1] else 0.0755
oi_snap_tokens = 59_692_669
oi_snap_usd = oi_snap_tokens * c_cur
bid_2pct = 591
ask_2pct = 421
total_depth = bid_2pct + ask_2pct

print(f"  Perp: AINUSDT Binance, onboard 2025-07-10, status=TRADING")
print(f"  Spot Binance: ABSENT (400)")
print(f"  Spot Gate.io: vol24h=$78,181 — PRIMARY (thin)")
print(f"  DEX (GeckoTerminal): ~$44K/day fragmented")
print(f"  OI snapshot (2026-08-17): {oi_snap_tokens:,} tokens = ${oi_snap_usd:,.0f}")
print(f"  Depth ±2% bid: ${bid_2pct:,}  ask: ${ask_2pct:,}  total: ${total_depth:,}")
print(f"  Depth/OI: {total_depth/oi_snap_usd*100:.4f}% — EXTREME THIN")
deposit_usd = 30e6 * c_cur
days_to_exit = deposit_usd / 78_181 if deposit_usd else 0
print(f"  30M tokens at ${c_cur:.5f} = ${deposit_usd:,.0f}")
print(f"  To exit via Gate.io spot: ~{days_to_exit:.0f} days at $78K/day")
print(f"  CANNOT exit via perp depth (bid only $591 vs ${deposit_usd:,.0f})")

# ── AI-8. SANITY ────────────────────────────────────────────────────────────
print("\n" + "=" * 70)
print("AI-8. SANITY CHECKS")
print("=" * 70)

s1 = len(rows) == 224
print(f"  S1: Row count = {len(rows)} (expected 224): {'PASS' if s1 else 'FAIL'}")

parsed_dates = []
for d in dates:
    try:
        parsed_dates.append(date.fromisoformat(d))
    except Exception:
        pass
gap_count = sum(1 for i in range(1, len(parsed_dates))
                if (parsed_dates[i] - parsed_dates[i-1]).days > 1)
s2 = gap_count == 0
print(f"  S2: Date continuity ({gap_count} gaps): {'PASS' if s2 else 'FAIL'}")

neg_closes = [c for c in closes if c is not None and c < 0]
s3 = len(neg_closes) == 0
print(f"  S3: No negative closes ({len(neg_closes)} neg): {'PASS' if s3 else 'FAIL'}")

s4 = ath_close is not None and abs(ath_close - 0.13472) < 0.0001
print(f"  S4: ATH verified (${ath_close:.5f} vs 0.13472): {'PASS' if s4 else 'FAIL'}" if ath_close else "  S4: ATH N/A: FAIL")

taker_valid = [t for t in taker if t is not None]
taker_oor   = [t for t in taker_valid if t < 30 or t > 70]
s5 = len(taker_oor) == 0
print(f"  S5: Taker in [30,70]% ({len(taker_oor)} OOR / {len(taker_valid)}): {'PASS' if s5 else 'FAIL'}")

n_pass = sum([s1, s2, s3, s4, s5])
print(f"\n  SANITY: {n_pass}/5 {'PASS' if n_pass == 5 else 'FAIL'}")

# ── SUMMARY TABLE ──────────────────────────────────────────────────────────
print("\n" + "=" * 70)
print("BẢNG BỐN VÂN — SUMMARY")
print("=" * 70)

pr_m1_s = f"{pr_m1:.3f}" if pr_m1 else "N/A"
pr_m3_s = f"{pr_m3:.3f}" if pr_m3 else "N/A"
pr_net   = (pr_m3 - pr_m1) if pr_m1 and pr_m3 else None
pr_net_s = f"{pr_net:+.3f}" if pr_net is not None else "N/A"
pr_dir   = "GIẢM" if pr_net and pr_net < -0.03 else "LEO" if pr_net and pr_net > 0.03 else "FLAT"
dr_s     = f"{len(dip_recovery)}/{total_dips}={dr_rate:.0f}%"
hedge_s  = f"{len(hedge_periods)}d hedge / {len(longest_block)}d max block"

print(f"""
  VÂN | BIẾN        | GIÁ TRỊ CHỐT                                  | SIGNAL
  ----+-------------+------------------------------------------------+--------
  1   | pos_r trend  | Jan-Mar={pr_m1_s} → Jul-Aug={pr_m3_s} ({pr_net_s}) → {pr_dir} | {'KHÔNG GOM (retail follow)' if pr_dir != 'GIẢM' else 'Acc giảm tỷ lệ'}
  2   | funding/hedge| {hedge_s} | {'GOM-E PASS' if gome_pass else 'GOM-E FAIL'}
  3   | dip recovery | {dr_s} next-day                               | Kiểm soát range {dr_rate:.0f}%
  4   | on-chain     | MISSING blockchain, Gate thin $78K/d          | CẦN OPERATOR
""")

print(f"  AI-3 TAXONOMY: {taxonomy}")
print(f"  GOM-D: {gomd_n}/4 PASS")
print(f"  GOM-E: {'PASS' if gome_pass else 'FAIL'}")
print(f"  Depth: BID $591 / ASK $421 — CANNOT EXIT 30M tokens via perp")
glsr_mean_s = f"{glsr_mean:.3f}" if glsr_valid else "N/A"
print(f"  gLSR mean {glsr_mean_s} → retail LONG dominant (pos_r 1.4-1.5 region)")

print(f"""
  Ô QUYẾT ĐỊNH ĐỀ XUẤT: C/D
  — pos_r >1.0 nhưng GIẢM dần: retail longs vẫn nhiều hơn shorts nhưng đang rút
  — Không có gom NGƯỢC retail (pos_r không inverso)
  — Gate thin, depth cực mỏng → exit khó
  — On-chain MISSING → chờ operator xác nhận blockchain + vesting

  DỪNG CHỜ OPERATOR ĐỌC _collect_ain_20260813.md.
""")

print("[DONE] AI-3→AI-8 analysis complete")
