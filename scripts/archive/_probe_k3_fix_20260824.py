#!/usr/bin/env python3
"""[K3-FIX] LSR-SKEW re-run với LABEL CHỐT theo case_lsr_ref (fapi-1d canonical).

Label rectification (ANALYSIS bắt):
  - REF = case_lsr_ref_20260824.csv (fapi-1d, md5 7de16e7e...). File KHÔNG có local/VPS.
    → Dùng freshwatch CSV lsr_global_r làm REF equivalent (same fapi-1d source per store
      canonical). Verify: BANK 02/07 REF phải = 0.7947 (operator spec).
  - CMP = _result.txt bot-signals docs/case study/ (backtest calib data).

K3 OLD tráo nhãn: gọi _result.txt là "case", freshwatch CSV là "store". Đúng:
  - freshwatch CSV lsr_global_r = fapi-1d ≡ operator's "case_lsr_ref" (REF chuẩn)
  - _result.txt = local backtest snapshot (CMP, khác source hoặc extract time)

Lag convention (chốt trước bảng):
  lag 0:  cmp[d] vs ref[d]      (cùng ngày)
  lag +1: cmp[d] vs ref[d+1]    (cmp dịch SỚM 1 ngày → so với ref hôm sau)
  lag −1: cmp[d] vs ref[d-1]    (cmp dịch MUỘN 1 ngày → so với ref hôm trước)

Match threshold: |Δ| < 0.01 (absolute gLSR difference).
"""
from __future__ import annotations
import sys, io, hashlib
from pathlib import Path
import pandas as pd

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = Path(r"D:/Data back test/whale_data")
BOT = Path(r"D:/Data back test/binance-bot-signals")
sys.path.insert(0, str(BOT))
from replay import parse_result_file, build_days

def _md5(p):
    h = hashlib.md5()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1<<16), b""): h.update(c)
    return h.hexdigest()

def load_ref_freshwatch(sym):
    """REF = freshwatch CSV lsr_global_r (fapi-1d canonical)."""
    rows = []
    paths = []
    for m in ["06","07","08"]:
        p = REPO / f"data/export/freshwatch_daily_2026-{m}.csv"
        if p.exists():
            paths.append(str(p))
            df = pd.read_csv(p)
            df = df[df["symbol"] == f"{sym}USDT"]
            for _, r in df.iterrows():
                rows.append({"date": r["date"], "gLSR": float(r["lsr_global_r"]) if pd.notna(r["lsr_global_r"]) else float("nan")})
    return pd.DataFrame(rows).sort_values("date").reset_index(drop=True), paths

def load_cmp_result(sym, pat):
    """CMP = bot-signals _result.txt."""
    fps = list((BOT / "docs" / "case study").glob(pat))
    if not fps:
        fps = list((BOT / "docs" / "case study").glob(pat.lower()))
    if not fps: return None, None
    fpath = fps[0]
    funding, oi, ratio, klines = parse_result_file(fpath)
    days = build_days(funding, oi, ratio, klines)
    rows = []
    for d in days:
        date_str = d.get("date", "")
        if len(date_str) == 5: date_str = "2026-" + date_str
        if not date_str: continue
        rows.append({"date": date_str, "gLSR": d.get("lsr_global", float("nan"))})
    return pd.DataFrame(rows).sort_values("date").reset_index(drop=True), str(fpath)

# ─── (a) Paste path + md5 + 3 rows raw ───
print(f"══ [K3-FIX (a)] Path + md5 hai input K3 cũ đã đọc ══")
for sym, pat in [("BANK", "BANK*_result.txt"), ("TUT", "TUT*_result.txt"), ("CYS", "CYS*_result.txt")]:
    ref, ref_paths = load_ref_freshwatch(sym)
    cmp_df, cmp_path = load_cmp_result(sym, pat)
    print(f"\n  {sym}:")
    print(f"    REF (freshwatch CSV lsr_global_r, fapi-1d):")
    for p in ref_paths:
        print(f"      path: {p}  md5={_md5(p)}")
    if cmp_path:
        print(f"    CMP (_result.txt): path: {cmp_path}  md5={_md5(cmp_path)}")
    else:
        print(f"    CMP (_result.txt): NOT FOUND")
    # 3 rows raw BANK 01-04/07
    print(f"    REF rows 01-04/07:")
    for d in ["2026-07-01","2026-07-02","2026-07-03","2026-07-04"]:
        r = ref[ref["date"]==d]
        if not r.empty:
            print(f"      {d}: gLSR={r['gLSR'].iloc[0]:.4f}")
    if cmp_df is not None:
        print(f"    CMP rows 01-04/07:")
        for d in ["2026-07-01","2026-07-02","2026-07-03","2026-07-04"]:
            r = cmp_df[cmp_df["date"]==d]
            if not r.empty:
                print(f"      {d}: gLSR={r['gLSR'].iloc[0]:.4f}")

# Verify REF sample BANK 02/07 = 0.7947 (operator spec)
print(f"\n[K3-FIX verify] Operator spec: BANK 02/07 REF gLSR = 0.7947")
bank_ref, _ = load_ref_freshwatch("BANK")
sample = bank_ref[bank_ref["date"] == "2026-07-02"]
if not sample.empty:
    val = sample["gLSR"].iloc[0]
    print(f"  Actual REF BANK 02/07 = {val:.4f} {'✓ MATCH' if abs(val - 0.7947) < 0.001 else '✗ MISMATCH'}")
    if abs(val - 0.7947) < 0.001:
        print(f"  → REF equivalent (freshwatch CSV) matches case_lsr_ref sample")

# ─── (b) Re-run corr + match-rate at 3 lags ───
print(f"\n══ [K3-FIX (b)] Corr + match-rate at lag −1 / 0 / +1 ══")
print(f"  Quy ước dấu lag: cmp[d] compared with ref[d + lag]")
print(f"    lag 0:  cùng ngày")
print(f"    lag +1: cmp[d] vs ref[d+1] (cmp dịch SỚM 1 ngày, cmp hôm nay so ref hôm sau)")
print(f"    lag −1: cmp[d] vs ref[d-1] (cmp dịch MUỘN 1 ngày, cmp hôm nay so ref hôm trước)")
print(f"  Match threshold: |Δ| < 0.01")
WINDOW = ("2026-06-29", "2026-08-17")

for sym, pat in [("BANK", "BANK*_result.txt"), ("TUT", "TUT*_result.txt"), ("CYS", "CYS*_result.txt")]:
    ref, _ = load_ref_freshwatch(sym)
    cmp_df, _ = load_cmp_result(sym, pat)
    if cmp_df is None or cmp_df.empty:
        print(f"\n  {sym}: CMP not found — skip")
        continue
    # Merge on date
    m = pd.merge(cmp_df.rename(columns={"gLSR":"cmp"}),
                 ref.rename(columns={"gLSR":"ref"}), on="date", how="inner").sort_values("date").reset_index(drop=True)
    m = m[(m["date"] >= WINDOW[0]) & (m["date"] <= WINDOW[1])].reset_index(drop=True)
    if m.empty:
        print(f"\n  {sym}: no overlap"); continue
    n = len(m)
    # Build lag-shifted ref
    print(f"\n  {sym} (n={n} rows in window {WINDOW[0]}→{WINDOW[1]}):")
    results = {}
    for lag in [-1, 0, +1]:
        # cmp[d] vs ref[d+lag]: shift ref by -lag (so index[d]->ref[d+lag])
        ref_shifted = m["ref"].shift(-lag)
        valid = ref_shifted.notna() & m["cmp"].notna()
        cmp_v = m["cmp"][valid]; ref_v = ref_shifted[valid]
        if len(cmp_v) < 2:
            print(f"    lag {lag:+d}: insufficient overlap"); continue
        corr = cmp_v.corr(ref_v)
        diff = (cmp_v - ref_v).abs()
        match = (diff < 0.01).sum() / len(cmp_v) * 100
        results[lag] = (corr, match, diff)
        print(f"    lag {lag:+d}: n={len(cmp_v)}  corr={corr:.4f}  match={match:.1f}%")
    # ─── (c) At winning lag, |Δ|% distribution ───
    if results:
        winner = max(results, key=lambda k: results[k][0])
        corr_w, match_w, diff_w = results[winner]
        # Actually operator wants ratio not abs. But |Δ| already abs value. Use %|Δ|/ref
        m_valid = m.copy()
        ref_shifted = m_valid["ref"].shift(-winner)
        valid = ref_shifted.notna() & m_valid["cmp"].notna() & (ref_shifted > 0)
        cmp_v = m_valid["cmp"][valid]; ref_v = ref_shifted[valid]
        pct_diff = ((cmp_v - ref_v).abs() / ref_v * 100).sort_values()
        if len(pct_diff) > 0:
            p50 = pct_diff.quantile(0.50)
            p90 = pct_diff.quantile(0.90)
            pmax = pct_diff.max()
            n_ge10 = (pct_diff >= 10).sum()
            n_ge20 = (pct_diff >= 20).sum()
            print(f"    [winner lag {winner:+d}] |Δ|% distribution: p50={p50:.2f}%  p90={p90:.2f}%  max={pmax:.2f}%")
            print(f"    [winner lag {winner:+d}] count |Δ|≥10%={n_ge10}  |Δ|≥20%={n_ge20}  (of {len(pct_diff)} pairs)")

print(f"\n══ [K3-FIX (d)] KHÔNG kết luận — bảng về ANALYSIS ══")
print(f"  Bảng trên: ANALYSIS chấm store-LSR (freshwatch CSV = REF fapi-1d) đủ sạch nuôi")
print(f"  GOM-H H2/registry/watchlist, hay H2 phải đọc fapi 30d + CASE-lineage cho lịch sử.")
