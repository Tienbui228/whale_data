#!/usr/bin/env python3
"""Probe BR — chốt canh R1-R4: chuỗi 28/07→04/08, tape Gate, alpha layer.

R1: Chain full metrics + funding interval verify
R2: 4 chốt hồ sơ (pos_r floor, gLSR flush, BTW trap, L-26)
R3: Gate tape (collector từ 31/07)
R4: Alpha store BR
"""
import csv, io, json, sys
from pathlib import Path
import pandas as pd
import urllib.request, urllib.error, json as _json

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

EXP_DIR   = Path(r"D:\Check onchain fresh wallets\data\export")
STORE     = Path(r"D:\Data back test\whale_data\data\raw\spot_klines_1d")
TAPE_DIR  = Path(r"D:\Data back test\whale_data\data\raw\tape")
ALPHA_MAP = Path(r"D:\Data back test\whale_data\data\config\alpha_id_map.json")

# ── Helper ────────────────────────────────────────────────────────────────────
def gv(r, k):
    v = r.get(k, "")
    if v in ("", None): return None
    try: return float(v)
    except: return None

def emit(s): print(s)

# ── Load freshwatch BR ────────────────────────────────────────────────────────
br_rows = {}
for f in sorted(EXP_DIR.glob("freshwatch_daily_2026-*.csv")):
    for r in csv.DictReader(open(f, encoding="utf-8-sig")):
        sym = r.get("symbol", "")
        if sym in ("BRUSDT", "BR"):
            br_rows[r["date"]] = r

emit(f"\n{'='*60}")
emit(f"BR freshwatch rows: {len(br_rows)}")
if br_rows:
    emit(f"Date range: {min(br_rows)} → {max(br_rows)}")
    # Sample to check symbol name
    sample = list(br_rows.values())[0]
    emit(f"Symbol field: {sample.get('symbol')}")

# ── Alpha ID ──────────────────────────────────────────────────────────────────
emit(f"\n{'='*60}")
alpha_id_br = None
if ALPHA_MAP.exists():
    m = json.loads(ALPHA_MAP.read_text(encoding="utf-8"))
    alpha_id_br = m.get("BR") or m.get("BRUSDT")
    emit(f"Alpha ID BR: {alpha_id_br}")
    tag_keys = [(k,v) for k,v in m.items() if "BR" in k.upper() and len(k)<=6]
    emit(f"BR-like keys: {tag_keys}")

# ── Alpha store BR ────────────────────────────────────────────────────────────
emit(f"\n{'='*60}")
emit("Alpha store scan for BR:")
alpha_br = {}
for p in sorted(STORE.glob("date=2026-*")):
    files = list(p.glob("*.parquet"))
    if not files: continue
    try:
        df = pd.read_parquet(files[0])
        tag = df[df['symbol'] == 'BR'] if 'symbol' in df.columns else pd.DataFrame()
        if len(tag):
            row = tag.iloc[0]
            qv = row.get('quote_vol', None)
            alpha_br[p.name.replace("date=", "")] = {
                'qv': float(qv) if pd.notna(qv) else None,
                'close': float(row.get('close', 0)),
                'open': float(row.get('open', 0)),
                'abstain': bool(row.get('taker_abstain', True)),
            }
    except: pass

emit(f"Alpha BR dates: {len(alpha_br)}")
if alpha_br:
    emit(f"Range: {min(alpha_br)} → {max(alpha_br)}")
    emit("Last 10:")
    for d in sorted(alpha_br)[-10:]:
        r = alpha_br[d]
        qv_s = f"${r['qv']:,.0f}" if r['qv'] else "None"
        emit(f"  {d}: close={r['close']:.6f}, alpha_vol={qv_s}")

# ── R1: Chuỗi 28/07→04/08 ────────────────────────────────────────────────────
emit(f"\n{'='*60}")
emit("R1 — CHUỖI BR 28/07→04/08")
emit(f"{'='*60}")

# OI floor canonical
OI_FLOOR = 3_782_263
POS_R_FLOOR_REF = 1.661   # mốc hồ sơ
GLSR_PEAK = 1.944          # mốc hồ sơ gLSR
GLSR_FLUSH_THRESH = 1.1    # tái-ARM flush target

dates_window = [
    "2026-07-25","2026-07-26","2026-07-27","2026-07-28","2026-07-29",
    "2026-07-30","2026-07-31","2026-08-01","2026-08-02","2026-08-03","2026-08-04"
]

daily = {}
for d, r in br_rows.items():
    daily[d] = r

# Compute metrics
def oi_cycle(oi):
    oi_vals = [gv(r, "oi_usd") for r in br_rows.values() if gv(r,"oi_usd")]
    if not oi_vals or oi is None: return "?"
    mn, mx = min(oi_vals), max(oi_vals)
    if mx == mn: return "FLAT"
    pct = (oi - mn)/(mx - mn)*100
    tag = "FLOOR" if pct < 20 else "PEAK" if pct > 80 else "MID"
    return f"{tag}({pct:.0f}%)"

emit(f"\n{'date':12} {'px':10} {'ret1d':7} {'ret3d':7} {'vol_M':6} {'tk%':5} "
     f"{'f_avg':8} {'f_min':8} {'f_max':8} {'fn':3} "
     f"{'OI_M':7} {'OI_pos':12} {'pos_r':6} {'acc_r':6} {'gLSR':6} "
     f"{'div':5} {'div3':5} {'sl5d':5} {'SUSPECT'}")

rows_data = []
for d in dates_window:
    r = daily.get(d, {})
    px  = gv(r, "px_avg")
    vol = gv(r, "vol_quote")
    tk  = gv(r, "taker_buy_pct")
    fav = gv(r, "funding_avg")
    fmi = gv(r, "funding_min")
    fmx = gv(r, "funding_max")
    fn  = gv(r, "funding_n")
    oi  = gv(r, "oi_usd")
    pr  = gv(r, "lsr_pos_r")
    ar  = gv(r, "lsr_acc_r")
    gl  = gv(r, "lsr_global_r")
    tr  = gv(r, "taker_ratio")
    lc  = r.get("low_conf","") if r else ""

    # ret_1d
    prev_dates = [x for x in dates_window if x < d]
    prev_px = gv(daily.get(prev_dates[-1], {}), "px_avg") if prev_dates else None
    r1d = (px/prev_px - 1) if px and prev_px else None
    # ret_3d
    p3 = [x for x in dates_window if x < d]
    px3 = gv(daily.get(p3[-3], {}), "px_avg") if len(p3) >= 3 else None
    r3d = (px/px3 - 1) if px and px3 else None
    # div_raw
    div = (ar/pr) if ar and pr and pr > 0 else None
    # div_avg3 (simple 3d window)
    p3_dates = [x for x in dates_window if x < d][-2:]
    divs = []
    for pd_ in p3_dates + [d]:
        rr = daily.get(pd_, {})
        a2, p2 = gv(rr,"lsr_acc_r"), gv(rr,"lsr_pos_r")
        if a2 and p2 and p2>0: divs.append(a2/p2)
    div3 = sum(divs)/len(divs) if divs else None
    # glsr_slope_5d
    p5_dates = [x for x in dates_window if x < d]
    gl5 = gv(daily.get(p5_dates[-5], {}), "lsr_global_r") if len(p5_dates) >= 5 else None
    slope5 = (gl/gl5) if gl and gl5 and gl5 > 0 else None

    suspects = []
    if lc == "True": suspects.append("low_conf")
    if fn and fn == 1: suspects.append("fn=1")
    if px is None: suspects.append("NO_DATA")
    suspect_str = ",".join(suspects) if suspects else "OK"

    rows_data.append({
        'd': d, 'px': px, 'r1d': r1d, 'r3d': r3d, 'vol': vol,
        'tk': tk, 'fav': fav, 'fmi': fmi, 'fmx': fmx, 'fn': fn,
        'oi': oi, 'pr': pr, 'ar': ar, 'gl': gl,
        'div': div, 'div3': div3, 'slope5': slope5,
    })

    px_s  = f"{px:.6f}" if px else "—"
    r1_s  = f"{r1d*100:+.1f}%" if r1d is not None else "—"
    r3_s  = f"{r3d*100:+.1f}%" if r3d is not None else "—"
    vol_s = f"{vol/1e6:.1f}" if vol else "—"
    tk_s  = f"{tk*100:.1f}" if tk else "—"
    fav_s = f"{fav:.5f}" if fav else "—"
    fmi_s = f"{fmi:.5f}" if fmi else "—"
    fmx_s = f"{fmx:.5f}" if fmx else "—"
    fn_s  = f"{int(fn)}" if fn else "—"
    oi_s  = f"{oi/1e6:.2f}" if oi else "—"
    pr_s  = f"{pr:.3f}" if pr else "—"
    ar_s  = f"{ar:.3f}" if ar else "—"
    gl_s  = f"{gl:.4f}" if gl else "—"
    d_s   = f"{div:.3f}" if div else "—"
    d3_s  = f"{div3:.3f}" if div3 else "—"
    sl_s  = f"{slope5:.3f}" if slope5 else "—"
    oi_p  = oi_cycle(oi) if oi else "—"

    emit(f"{d:12} {px_s:10} {r1_s:7} {r3_s:7} {vol_s:6} {tk_s:5} "
         f"{fav_s:8} {fmi_s:8} {fmx_s:8} {fn_s:3} "
         f"{oi_s:7} {oi_p:12} {pr_s:6} {ar_s:6} {gl_s:6} "
         f"{d_s:5} {d3_s:5} {sl_s:5} {suspect_str}")

# OI vs floor
emit(f"\nOI floor canonical: {OI_FLOOR:,} USD = {OI_FLOOR/1e6:.3f}M")
for x in rows_data:
    if x['oi']:
        ratio = x['oi']/OI_FLOOR
        above = x['oi'] - OI_FLOOR
        emit(f"  {x['d']}: OI={x['oi']/1e6:.3f}M vs floor → ×{ratio:.2f} ({'+' if above>=0 else ''}{above/1e6:.3f}M)")

# ── R2: 4 Chốt hồ sơ ─────────────────────────────────────────────────────────
emit(f"\n{'='*60}")
emit("R2 — 4 CHỐT HỒ SƠ")
emit(f"{'='*60}")

recent = [x for x in rows_data if x['d'] >= "2026-07-28" and x['pr']]

# ① pos_r nhích bền tại floor
emit("\n① pos_r vs floor ref 1.661:")
for x in rows_data:
    if x['d'] >= "2026-07-25" and x['pr']:
        diff = x['pr'] - POS_R_FLOOR_REF
        above_floor = "↑" if diff > 0 else "↓"
        emit(f"  {x['d']}: pos_r={x['pr']:.3f} ({above_floor}{abs(diff):.3f} vs ref) | OI={x['oi']/1e6:.2f}M" if x['oi'] else
             f"  {x['d']}: pos_r={x['pr']:.3f} ({above_floor}{abs(diff):.3f} vs ref) | OI=—")

# Sequence check — ≥3d tăng liên tục?
pr_seq = [(x['d'], x['pr']) for x in rows_data if x['d'] >= "2026-07-28" and x['pr']]
max_streak = 0
cur_streak = 0
for i in range(1, len(pr_seq)):
    if pr_seq[i][1] > pr_seq[i-1][1]:
        cur_streak += 1
        max_streak = max(max_streak, cur_streak)
    else:
        cur_streak = 0
emit(f"  Max tăng liên tục: {max_streak} ngày (cần ≥3)")

# ② gLSR crowd_flush
emit(f"\n② gLSR crowd_flush (mốc peak={GLSR_PEAK}, flush target ≤{GLSR_FLUSH_THRESH}):")
gl_vals = [(x['d'], x['gl']) for x in rows_data if x['gl']]
if gl_vals:
    gl_min = min(gl_vals, key=lambda x: x[1])
    gl_max = max(gl_vals, key=lambda x: x[1])
    emit(f"  gLSR range: min={gl_min[1]:.4f} ({gl_min[0]}) max={gl_max[1]:.4f} ({gl_max[0]})")
    emit(f"  Flush ≤{GLSR_FLUSH_THRESH} xảy ra: {'ĐÃ QUA' if gl_min[1] <= GLSR_FLUSH_THRESH else 'CHƯA'}")

# 3d max drop check (crowd flush L-26)
emit(f"\n  L-26 crowd_flush check (pos_r drop ≥30% trong 3d):")
for i in range(2, len(rows_data)):
    if rows_data[i]['pr'] and rows_data[i-2]['pr']:
        drop = (rows_data[i]['pr'] - rows_data[i-2]['pr']) / rows_data[i-2]['pr']
        if rows_data[i]['d'] >= "2026-07-28":
            emit(f"  {rows_data[i-2]['d']}→{rows_data[i]['d']}: pos_r {rows_data[i-2]['pr']:.3f}→{rows_data[i]['pr']:.3f} = {drop*100:+.1f}% {'✓ FLUSH' if drop <= -0.30 else '✗'}")

# gLSR direction L-26
emit(f"\n  gLSR direction 28/07→03/08:")
gl28 = next((x['gl'] for x in rows_data if x['d']=='2026-07-28'), None)
gl03 = next((x['gl'] for x in rows_data if x['d']=='2026-08-03'), None)
if gl28 and gl03:
    emit(f"  28/07 gLSR={gl28:.4f} → 03/08 gLSR={gl03:.4f} = {(gl03/gl28-1)*100:+.1f}%")

# ④ BTW trap check
emit(f"\n④ BTW hình bẫy PHA 2 check:")
# Price flatness: biên độ 3d
recent3 = [x for x in rows_data if x['d'] >= "2026-07-31" and x['px']]
if recent3:
    px_vals = [x['px'] for x in recent3]
    px_range = (max(px_vals) - min(px_vals)) / min(px_vals)
    emit(f"  Biên độ px 31/07→03/08: {px_range*100:+.1f}% (ngưỡng ±7%: {'FLAT ✓' if px_range < 0.07 else 'KHÔNG FLAT ✗'})")
    emit(f"  px: {[f'{x[chr(112)]:.5f}' for x in recent3]}")

# Funding negative divergence §5
emit(f"  Funding neg-div §5 (avg ≤-2e-4 OR min ≤-5e-4):")
for x in rows_data:
    if x['d'] >= "2026-07-28" and x['fav'] is not None:
        neg_avg = x['fav'] <= -2e-4
        neg_min = x['fmi'] <= -5e-4 if x['fmi'] is not None else False
        tag = "SUPPRESSOR_ON" if (neg_avg or neg_min) else "—"
        emit(f"  {x['d']}: f_avg={x['fav']:.5f}, f_min={x['fmi']:.5f if x['fmi'] else '—'} → {tag}")

# ── Funding interval verify ────────────────────────────────────────────────────
emit(f"\n{'='*60}")
emit("Funding interval verify (fapi native BR, last 20 periods):")
emit(f"{'='*60}")
try:
    url = "https://fapi.binance.com/fapi/v1/fundingRate?symbol=BRUSDT&limit=20"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = _json.loads(resp.read())
    if data:
        for item in data:
            import datetime
            ts = item['fundingTime'] // 1000
            dt = datetime.datetime.utcfromtimestamp(ts).strftime("%Y-%m-%d %H:%M UTC")
            emit(f"  {dt}  rate={float(item['fundingRate']):.6f}")
        # Detect interval
        if len(data) >= 2:
            ts0 = data[0]['fundingTime'] // 1000
            ts1 = data[1]['fundingTime'] // 1000
            interval_h = (ts1 - ts0) / 3600
            emit(f"\n  → Dominant interval: {interval_h:.0f}h (BR funding cycle = {interval_h:.0f}h)")
            emit(f"  → fn=6 trong freshwatch = 6 × {interval_h:.0f}h = {6*interval_h:.0f}h = {6*interval_h/24:.1f}d")
except Exception as e:
    emit(f"  fapi error: {e}")

# ── R3: Gate Tape ─────────────────────────────────────────────────────────────
emit(f"\n{'='*60}")
emit("R3 — GATE TAPE (collector từ 31/07)")
emit(f"{'='*60}")

tape_files = sorted(TAPE_DIR.glob("**/*BR*.parquet")) if TAPE_DIR.exists() else []
emit(f"TAPE_DIR exists: {TAPE_DIR.exists()}")
emit(f"BR tape files: {len(tape_files)}")
for f in tape_files[:5]:
    emit(f"  {f}")

# Check tape directory structure
if TAPE_DIR.exists():
    emit(f"\nTape dir contents (top level):")
    for d in sorted(TAPE_DIR.iterdir())[:10]:
        emit(f"  {d.name}")
    # Find any parquet
    all_pq = sorted(TAPE_DIR.glob("**/*.parquet"))[:5]
    emit(f"\nSample parquets: {[str(f) for f in all_pq]}")
    if all_pq:
        df = pd.read_parquet(all_pq[0])
        emit(f"Schema: {list(df.columns)}")
        emit(f"Symbols: {df['symbol'].unique()[:10].tolist() if 'symbol' in df.columns else '?'}")

# ── R4: Alpha store BR ────────────────────────────────────────────────────────
emit(f"\n{'='*60}")
emit("R4 — ALPHA store BR (vol, price)")
emit(f"{'='*60}")
if alpha_br:
    emit(f"\n{'date':12} {'alpha_vol_USD':>15} {'close':>10} {'vs_perp_px':>12}")
    for d in sorted(alpha_br):
        r = alpha_br[d]
        perp_px = gv(daily.get(d, {}), "px_avg")
        vs = (r['close']/perp_px - 1)*100 if perp_px and r['close'] else None
        qv_s = f"${r['qv']:,.0f}" if r['qv'] else "—"
        vs_s = f"{vs:+.2f}%" if vs is not None else "—"
        emit(f"{d:12} {qv_s:>15} {r['close']:>10.6f} {vs_s:>12}")
else:
    emit("No alpha data for BR")
