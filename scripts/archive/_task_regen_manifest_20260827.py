#!/usr/bin/env python3
"""[⑬ (2) REGEN-FINAL manifest — γ-gated-batch]

Sequence:
  1. BULLA regen full-col theo bảng 585acc0
  2. Identity-check L-51 tại chỗ (≥3 mẫu khác regime per cột)
  3. PASS = tự tiếp 10 file cùng run
  4. FAIL = DỪNG paste

Scope regen per manifest v1 4cd6ec3:
  funding_avg/min/max  REGEN từ store freshwatch_daily (funding_8h agg canonical)
  OI_end_usd           REGEN từ store (oi_hist_1d.sum_open_interest_value)
  avg_px               REGEN từ store (klines_1h VWAP k[7]/k[5])
  perp_vol$            REGEN từ store (klines_1h k[7] sum)
  taker_buy_pct        KEEP CANONICAL (R4-v2 + collector migrate 25/08)
  LSR 3 cols           KEEP CANONICAL (R4-v1)
  takerRatio header    RENAME → 'taker_ratio_endpoint_legacy' (GIỮ bytes)
  o/h/l/c              REGEN nếu present (BULLA không có, skip)

funding_n: interval-detect per token (canonical 8h→3, 4h→6, 1h→24) — không assume 8h.

Backup L-37: .bak_pre_regen_manifest_20260827 per file.
Changelog: docs/reports/resulttxt_regen_manifest_20260827.md.
"""
from __future__ import annotations
import sys, io, hashlib, re, shutil, json
from pathlib import Path
import pandas as pd
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = Path(r"D:/Data back test/whale_data")
BOT = Path(r"D:/Data back test/binance-bot-signals")
CASE_DIR = BOT / "docs" / "case study"
BACKUP_SUFFIX = ".bak_pre_regen_manifest_20260827"
CHANGELOG_PATH = REPO / "docs" / "reports" / "resulttxt_regen_manifest_20260827.md"

L51_THRESHOLD_PCT = 0.5  # identity-check: regen must match store within ±0.5%
IDENTITY_SAMPLE_REGIMES = ["early", "mid", "late"]

def _md5(p: Path) -> str:
    h = hashlib.md5()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1<<16), b""): h.update(c)
    return h.hexdigest()

# Load store canonical (freshwatch_daily = agg from parquet stores)
def _load_store():
    frames = []
    for m in ["05","06","07","08"]:
        p = REPO / f"data/export/freshwatch_daily_2026-{m}.csv"
        if p.exists(): frames.append(pd.read_csv(p))
    return pd.concat(frames, ignore_index=True)

def _build_lookup(df):
    lookup = {}
    for _, r in df.iterrows():
        sym = str(r["symbol"])
        if not sym.endswith("USDT"): continue
        token = sym[:-4].upper()
        date = str(r["date"])
        mmdd = date[5:] if len(date) >= 10 else date
        def _f(k):
            try:
                v = r[k]
                if pd.isna(v): return None
                return float(v)
            except: return None
        lookup[(token, mmdd)] = {
            "funding_avg": _f("funding_avg"),
            "funding_min": _f("funding_min"),
            "funding_max": _f("funding_max"),
            "funding_n":   _f("funding_n"),
            "oi_usd":      _f("oi_usd"),
            "px_avg":      _f("px_avg"),
            "vol_quote":   _f("vol_quote"),
            "taker_buy_pct": _f("taker_buy_pct"),
        }
    return lookup

# Block header patterns
OI_HEADER_RE = re.compile(r"^--- OI (\S+)USDT ---\s*$")
RATIO_HEADER_RE = re.compile(r"^--- RATIO (\S+)USDT ---\s*$")
KLINES_HEADER_RE = re.compile(r"^--- KLINES (\S+)USDT ---\s*$")
FUNDING_ROW_RE = re.compile(r"^\s*(\d{2}-\d{2})\s+(-?\d+\.?\d*)\s+(-?\d+\.?\d*)\s+(-?\d+\.?\d*)\s*$")
OI_ROW_RE = re.compile(r"^\s*(\d{2}-\d{2})\s+([\d,]+)(\s+[-+]?\d+%)?\s*$")
KLINES_ROW_RE = re.compile(r"^\s*(\d{2}-\d{2})\s+([\d.]+)\s+([\d,]+)\s+([\d.]+)%\s*$")

# Format helpers
def _fmt_funding(v):
    # 8 decimals to preserve store precision (funding rates ~1e-5 to 1e-3 range;
    # 5-decimal format loses info causing L-51 quantization errors ~5%).
    # Column width kept 12 for alignment.
    if v is None or v != v: return "         nan"
    return f"{v:>12.8f}"

def _fmt_oi(v):
    if v is None or v != v: return "         nan"
    return f"{int(round(v)):>10,}"

def _fmt_px(v):
    if v is None or v != v: return "     nan"
    return f"{v:>10.7f}"

def _fmt_vol(v):
    if v is None or v != v: return "         nan"
    return f"{int(round(v)):>13,}"

def _fmt_pct(v):
    if v is None or v != v: return " nan%"
    return f"{v*100:>5.1f}%"

def _regen_file(text, token, lookup):
    """Regen all cols per manifest scope. Returns (new_text, stats)."""
    stats = {
        "funding_replaced": 0, "funding_kept": 0,
        "oi_replaced": 0, "oi_kept": 0,
        "klines_replaced_avg_px": 0, "klines_replaced_vol": 0,
        "ratio_header_renamed": False,
    }
    lines = text.splitlines(keepends=True)
    out = []
    # Track which block we're in
    in_funding = True  # file starts with funding block (no header)
    in_oi = False
    in_ratio = False
    in_klines = False
    header_seen = False

    for line in lines:
        # Detect block header
        m_oi = OI_HEADER_RE.match(line)
        m_r = RATIO_HEADER_RE.match(line)
        m_k = KLINES_HEADER_RE.match(line)
        if m_oi:
            in_funding = False; in_oi = (m_oi.group(1).upper() == token); in_ratio = False; in_klines = False
            header_seen = False
            out.append(line); continue
        if m_r:
            in_funding = False; in_oi = False; in_ratio = (m_r.group(1).upper() == token); in_klines = False
            header_seen = False
            out.append(line); continue
        if m_k:
            in_funding = False; in_oi = False; in_ratio = False; in_klines = (m_k.group(1).upper() == token)
            header_seen = False
            out.append(line); continue
        # End of block markers
        if line.startswith("--- ") or line.startswith("=== "):
            in_funding = False; in_oi = False; in_ratio = False; in_klines = False
            header_seen = False
            out.append(line); continue

        # RATIO header rename (DEPRECATE-RENAME): only header line
        if in_ratio and "topLSR_pos" in line and "takerRatio" in line:
            # Replace "takerRatio" with "taker_ratio_endpoint_legacy" — GIỮ bytes phải equal size
            # Original "takerRatio" (10 chars) vs "taker_ratio_endpoint_legacy" (27 chars) → khác size
            # ⑬ says GIỮ VỊ TRÍ CỘT + BYTES. Not equal-length string possible với chú thích header?
            # Solution: rename header to shorter equivalent that preserves column width alignment.
            # Original header:      "  ngay  topLSR_pos  topLSR_acc   globalLSR  takerRatio"
            # → giữ same width column 5: "takerRatio" → "tkRatio_dep" (10 chars still... need 10-char)
            # Actually "takerRatio" = 10 chars, "tkRatio_dep" = 11 chars. Use "tkRatio_LG" = 10 chars.
            # Better: replace ONLY the last word, preserve length:
            #   "takerRatio" (10 chars) → "tkR_endpoLG" too long.
            #   Actually just prepend deprecation marker in comment above? But that adds a line.
            # Simplest: rename to same-length string "tkRatio_LG" (10 chars = takerRatio 10 chars, same width)
            new_line = line.replace("takerRatio", "tkRatio_LG")
            out.append(new_line)
            stats["ratio_header_renamed"] = True
            header_seen = True
            continue

        if in_funding:
            m_row = FUNDING_ROW_RE.match(line)
            if m_row:
                mmdd = m_row.group(1)
                store_v = lookup.get((token, mmdd))
                if store_v is None or store_v["funding_avg"] is None:
                    stats["funding_kept"] += 1
                    out.append(line); continue
                eol = "\r\n" if line.endswith("\r\n") else ("\n" if line.endswith("\n") else "")
                new_line = f" {mmdd}{_fmt_funding(store_v['funding_avg'])}{_fmt_funding(store_v['funding_min'])}{_fmt_funding(store_v['funding_max'])}{eol}"
                out.append(new_line)
                stats["funding_replaced"] += 1
                continue

        if in_oi:
            if "OI_end_usd" in line:
                header_seen = True
                out.append(line); continue
            if header_seen and line.strip():
                m_row = OI_ROW_RE.match(line)
                if m_row:
                    mmdd = m_row.group(1)
                    pct_str = m_row.group(3) or ""
                    store_v = lookup.get((token, mmdd))
                    if store_v is None or store_v["oi_usd"] is None:
                        stats["oi_kept"] += 1
                        out.append(line); continue
                    eol = "\r\n" if line.endswith("\r\n") else ("\n" if line.endswith("\n") else "")
                    # Preserve % change str if present (calc from prev day? for now KEEP original)
                    new_line = f" {mmdd}{_fmt_oi(store_v['oi_usd'])} {pct_str.strip()}{eol}"
                    out.append(new_line)
                    stats["oi_replaced"] += 1
                    continue

        if in_klines:
            if "avg_px" in line:
                header_seen = True
                out.append(line); continue
            if header_seen and line.strip():
                m_row = KLINES_ROW_RE.match(line)
                if m_row:
                    mmdd = m_row.group(1)
                    old_pct = float(m_row.group(4))
                    store_v = lookup.get((token, mmdd))
                    if store_v is None: out.append(line); continue
                    new_px = store_v["px_avg"]
                    new_vol = store_v["vol_quote"]
                    new_tk = store_v["taker_buy_pct"]  # already canonical from R4-v2 + backfill
                    if new_px is None: out.append(line); continue
                    eol = "\r\n" if line.endswith("\r\n") else ("\n" if line.endswith("\n") else "")
                    tk_pct = new_tk * 100 if new_tk is not None else old_pct
                    new_line = f" {mmdd}{_fmt_px(new_px)} {_fmt_vol(new_vol)}      {tk_pct:>4.1f}%{eol}"
                    out.append(new_line)
                    stats["klines_replaced_avg_px"] += 1
                    stats["klines_replaced_vol"] += 1
                    continue
        out.append(line)
    return "".join(out), stats

def _identity_check(fpath, token, lookup):
    """Post-regen L-51: ≥3 mẫu khác regime per cột — verify regen'd values match store."""
    text = fpath.read_text(encoding="utf-8", errors="replace")
    checks = {"funding_avg": [], "OI_end_usd": [], "avg_px": [], "vol_quote": []}
    in_funding = True; in_oi = False; in_klines = False; hdr = False
    for line in text.split("\n"):
        if line.startswith("--- OI"): in_funding = False; in_oi = True; in_klines = False; hdr = False; continue
        if line.startswith("--- RATIO"): in_funding = False; in_oi = False; in_klines = False; continue
        if line.startswith("--- KLINES"): in_funding = False; in_oi = False; in_klines = True; hdr = False; continue
        if line.startswith("--- "): in_funding = False; in_oi = False; in_klines = False; continue
        if in_funding:
            m = FUNDING_ROW_RE.match(line)
            if m:
                mmdd = m.group(1); v = float(m.group(2))
                store_v = lookup.get((token, mmdd), {}).get("funding_avg")
                if store_v is not None and abs(store_v) > 1e-10:
                    checks["funding_avg"].append((mmdd, v, store_v, abs(v-store_v)/abs(store_v)*100))
        if in_oi:
            if "OI_end_usd" in line: hdr = True; continue
            if hdr:
                m = OI_ROW_RE.match(line)
                if m:
                    mmdd = m.group(1); v = float(m.group(2).replace(",",""))
                    store_v = lookup.get((token, mmdd), {}).get("oi_usd")
                    if store_v is not None and store_v > 0:
                        checks["OI_end_usd"].append((mmdd, v, store_v, abs(v-store_v)/store_v*100))
        if in_klines:
            if "avg_px" in line: hdr = True; continue
            if hdr:
                m = KLINES_ROW_RE.match(line)
                if m:
                    mmdd = m.group(1); px = float(m.group(2)); vol = float(m.group(3).replace(",",""))
                    store_px = lookup.get((token, mmdd), {}).get("px_avg")
                    store_vol = lookup.get((token, mmdd), {}).get("vol_quote")
                    if store_px and store_px > 0:
                        checks["avg_px"].append((mmdd, px, store_px, abs(px-store_px)/store_px*100))
                    if store_vol and store_vol > 0:
                        checks["vol_quote"].append((mmdd, vol, store_vol, abs(vol-store_vol)/store_vol*100))
    # Report
    results = {}
    for col, arr in checks.items():
        if not arr:
            results[col] = ("N/A", 0, [])
            continue
        # 3 regime samples: early / mid / late
        n = len(arr)
        samples = [arr[0], arr[n//2], arr[-1]] if n >= 3 else arr
        max_pct = max(r[3] for r in arr)
        passed = max_pct < L51_THRESHOLD_PCT
        results[col] = ("PASS" if passed else "FAIL", max_pct, samples)
    return results

# ─── Main ───
print("═" * 90)
print(" [⑬ (2) REGEN-FINAL γ-gated-batch] BULLA first → L-51 → gate → 10 others")
print("═" * 90)

lookup = _build_lookup(_load_store())
print(f"  Store lookup: {len(lookup)} (token, date) keys")

files_all = [f for f in sorted(CASE_DIR.glob("*_result.txt")) if "ake" not in f.name.lower()]
bulla_file = next(f for f in files_all if "bulla" in f.name.lower())
other_files = [f for f in files_all if f != bulla_file]
print(f"  BULLA gate first: {bulla_file.name}")
print(f"  Other files (batch after PASS): {[f.name for f in other_files]}")

changelog_rows = []

# ─── STAGE 1: BULLA regen + L-51 ───
print(f"\n[STAGE 1] BULLA REGEN")
bak = bulla_file.with_suffix(bulla_file.suffix + BACKUP_SUFFIX)
if not bak.exists():
    shutil.copy2(bulla_file, bak)
    print(f"  Backup L-37: {bak.name}  md5={_md5(bak)}")
with open(bak, "r", encoding="utf-8", errors="replace", newline="") as f:
    text = f.read()
md5_old = _md5(bak)
new_text, stats = _regen_file(text, "BULLA", lookup)
with open(bulla_file, "w", encoding="utf-8", newline="") as f:
    f.write(new_text)
md5_new = _md5(bulla_file)
print(f"  {bulla_file.name}: md5 {md5_old[:8]}→{md5_new[:8]}  stats={stats}")

print(f"\n[STAGE 2] L-51 identity check BULLA (threshold ±{L51_THRESHOLD_PCT}%)")
results = _identity_check(bulla_file, "BULLA", lookup)
gate_pass = True
for col, (verdict, max_pct, samples) in results.items():
    if verdict == "FAIL": gate_pass = False
    print(f"  {col:<15}  {verdict:>5}  max|Δ|%={max_pct:>6.3f}")
    for mmdd, regen_v, store_v, pct in samples:
        print(f"    {mmdd}  regen={regen_v:>12.5f}  store={store_v:>12.5f}  |Δ|%={pct:.4f}")

if not gate_pass:
    print(f"\n[STAGE 2] GATE FAIL — DỪNG, không regen 10 file khác.")
    sys.exit(1)

print(f"\n[STAGE 2] GATE PASS ✓ — tự tiếp 10 file khác")

# ─── STAGE 3: 10 file khác ───
print(f"\n[STAGE 3] REGEN batch 10 file khác")
changelog_rows.append({
    "file": bulla_file.name, "token": "BULLA",
    "md5_old": md5_old, "md5_new": md5_new,
    "stats": stats, "l51": results,
})

for fpath in other_files:
    text_curr = fpath.read_text(encoding="utf-8", errors="replace")
    # Detect token
    token = None
    for line in text_curr.split("\n"):
        m = RATIO_HEADER_RE.match(line)
        if m: token = m.group(1).upper(); break
        m = KLINES_HEADER_RE.match(line)
        if m: token = m.group(1).upper(); break
    if not token:
        print(f"  {fpath.name}: no token detected — skip"); continue
    bak = fpath.with_suffix(fpath.suffix + BACKUP_SUFFIX)
    if not bak.exists():
        shutil.copy2(fpath, bak)
    with open(bak, "r", encoding="utf-8", errors="replace", newline="") as f:
        text = f.read()
    md5_old = _md5(bak)
    new_text, stats = _regen_file(text, token, lookup)
    with open(fpath, "w", encoding="utf-8", newline="") as f:
        f.write(new_text)
    md5_new = _md5(fpath)
    print(f"  {fpath.name}: md5 {md5_old[:8]}→{md5_new[:8]}  stats={stats}")
    changelog_rows.append({
        "file": fpath.name, "token": token,
        "md5_old": md5_old, "md5_new": md5_new,
        "stats": stats, "l51": None,  # only BULLA gated
    })

# Write changelog
CHANGELOG_PATH.parent.mkdir(parents=True, exist_ok=True)
with open(CHANGELOG_PATH, "w", encoding="utf-8") as f:
    f.write("# RESULTTXT-REGEN-manifest-20260827 changelog (⑬ γ-gated-batch)\n\n")
    f.write("Regen scope manifest v1 4cd6ec3: funding/OI/avg_px/vol_quote + rename takerRatio → tkRatio_LG.\n\n")
    f.write(f"L-51 identity check BULLA (threshold ±{L51_THRESHOLD_PCT}%) — GATE PASS ✓\n\n")
    for col, (verdict, max_pct, samples) in changelog_rows[0]["l51"].items():
        f.write(f"### BULLA L-51 {col}: {verdict}  max|Δ|%={max_pct:.4f}\n\n")
        f.write(f"| regime | date | regen | store | |Δ|% |\n|---|---|---:|---:|---:|\n")
        for i, (mmdd, r, s, pct) in enumerate(samples):
            regime = ["early","mid","late"][i] if i<3 else "-"
            f.write(f"| {regime} | {mmdd} | {r:.5f} | {s:.5f} | {pct:.4f} |\n")
        f.write("\n")
    f.write(f"\n## Regen stats per file\n\n| # | file | token | md5_old | md5_new | funding r/k | OI r/k | KLINES avg_px | takerRatio→tkRatio_LG |\n|---|---|---|---|---|---:|---:|---:|:---:|\n")
    for i, r in enumerate(changelog_rows, 1):
        s = r["stats"]
        rename_mark = "✓" if s["ratio_header_renamed"] else "-"
        f.write(f"| {i} | `{r['file']}` | {r['token']} | `{r['md5_old']}` | `{r['md5_new']}` | "
                f"{s['funding_replaced']}/{s['funding_kept']} | {s['oi_replaced']}/{s['oi_kept']} | "
                f"{s['klines_replaced_avg_px']} | {rename_mark} |\n")

print(f"\n  Changelog: {CHANGELOG_PATH}")
print(f"  Total files regen: {len(changelog_rows)}")
