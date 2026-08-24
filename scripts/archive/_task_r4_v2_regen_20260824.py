#!/usr/bin/env python3
"""[R4-v2 REGEN] LSR (RATIO) + RATIO takerRatio + KLINES taker_buy_pct%
   Từ store canonical + klines_1h fresh k[10]/k[7] agg (fetched from VPS).

⑩-AMENDMENT ba vế:
  Vế 1: basis PIN k[10]/k[7] (quote/quote)
  Vế 2: regen scope MỞ RỘNG sang KLINES taker_buy_pct, PERCENT khuôn _result
  Vế 3: (collector migrate — separate task)

Idempotent trên .bak_pre_R4_20260824. MỘT commit duy nhất (spec + regen + changelog).
"""
from __future__ import annotations
import sys, io, hashlib, re, shutil
from pathlib import Path
import pandas as pd
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

REPO = Path(r"D:/Data back test/whale_data")
BOT = Path(r"D:/Data back test/binance-bot-signals")
CASE_DIR = BOT / "docs" / "case study"
BACKUP_SUFFIX = ".bak_pre_R4_20260824"
CHANGELOG_PATH = REPO / "docs" / "reports" / "resulttxt_regen_v2_changelog_20260824.md"

def _md5(p: Path) -> str:
    h = hashlib.md5()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 16), b""): h.update(c)
    return h.hexdigest()

# Load store LSR data
def _load_store():
    frames = []
    for m in ["05","06","07","08"]:
        p = REPO / f"data/export/freshwatch_daily_2026-{m}.csv"
        if p.exists():
            frames.append(pd.read_csv(p))
    return pd.concat(frames, ignore_index=True)

def _build_lsr_lookup(df):
    lookup = {}
    for _, r in df.iterrows():
        sym = str(r["symbol"])
        if not sym.endswith("USDT"): continue
        token = sym[:-4]
        date = str(r["date"])
        mmdd = date[5:] if len(date) >= 7 else date
        def _f(k):
            try:
                v = r[k]
                if pd.isna(v): return None
                return float(v)
            except: return None
        pos = _f("lsr_pos_r"); acc = _f("lsr_acc_r"); gl = _f("lsr_global_r"); tk = _f("taker_ratio")
        if pos is None and acc is None and gl is None and tk is None: continue
        lookup[(token, mmdd)] = (pos, acc, gl, tk)
    return lookup

# Load klines k[10]/k[7] fresh aggregated
def _load_klines_taker():
    p = REPO / "data/reference/klines_taker_daily_20260824.csv"
    if not p.exists():
        sys.exit(f"MISSING: {p} — run _task_vps_aggregate_klines first")
    df = pd.read_csv(p)
    lookup = {}
    for _, r in df.iterrows():
        sym = str(r["symbol"])
        if not sym.endswith("USDT"): continue
        token = sym[:-4]
        date = str(r["date"])
        mmdd = date[5:] if len(date) >= 7 else date
        try:
            v = float(r["taker_buy_pct_k10k7"])
            if pd.isna(v): continue
        except: continue
        lookup[(token, mmdd)] = v
    return lookup

# ─── Block patterns ───
RATIO_HEADER_RE = re.compile(r"^--- RATIO (\S+)USDT ---\s*$")
KLINES_HEADER_RE = re.compile(r"^--- KLINES (\S+)USDT ---\s*$")

# RATIO data row: ` MM-DD    xx.xx    yy.yy    zz.zz    ww.ww`
RATIO_ROW_RE = re.compile(r"^\s*(\d{2}-\d{2})\s+")
# KLINES data row: ` MM-DD     0.NNNNNN       N,NNN,NNN      NN.N%`
KLINES_ROW_RE = re.compile(r"^\s*(\d{2}-\d{2})\s+([^\s]+)\s+([^\s]+)\s+([\d.]+)%\s*$")

def _fmt_ratio_val(v):
    if v is None or v != v: return "         nan"
    return f"{v:>12.2f}" if abs(v) < 1000 else f"{v:>12.0f}"

def _regen_file(lines, token, lsr_lookup, klines_lookup):
    stats = {"ratio_replaced": 0, "klines_replaced": 0,
             "ratio_kept_stale": 0, "klines_kept_stale": 0,
             "ratio_stale_dates": [], "klines_stale_dates": []}
    out = []
    in_ratio = False
    in_klines = False
    ratio_header_seen = False
    klines_header_seen = False
    for line in lines:
        # Detect block start
        m_r = RATIO_HEADER_RE.match(line)
        m_k = KLINES_HEADER_RE.match(line)
        if m_r:
            in_ratio = (m_r.group(1).upper() == token.upper())
            in_klines = False
            ratio_header_seen = False
            out.append(line); continue
        if m_k:
            in_klines = (m_k.group(1).upper() == token.upper())
            in_ratio = False
            klines_header_seen = False
            out.append(line); continue
        if in_ratio or in_klines:
            if line.startswith("--- ") or line.startswith("=== "):
                in_ratio = False; in_klines = False
                out.append(line); continue

        # RATIO block processing
        if in_ratio:
            if "topLSR_pos" in line:
                ratio_header_seen = True
                out.append(line); continue
            if ratio_header_seen and line.strip():
                m_row = RATIO_ROW_RE.match(line)
                if m_row:
                    mmdd = m_row.group(1)
                    vals = lsr_lookup.get((token.upper(), mmdd))
                    if vals is not None:
                        pos, acc, gl, tk = vals
                        eol = "\r\n" if line.endswith("\r\n") else ("\n" if line.endswith("\n") else "")
                        new_line = f" {mmdd}{_fmt_ratio_val(pos)}{_fmt_ratio_val(acc)}{_fmt_ratio_val(gl)}{_fmt_ratio_val(tk)}{eol}"
                        out.append(new_line)
                        stats["ratio_replaced"] += 1
                        continue
                    else:
                        stats["ratio_kept_stale"] += 1
                        stats["ratio_stale_dates"].append(mmdd)
                        out.append(line); continue
            out.append(line); continue

        # KLINES block processing
        if in_klines:
            if "avg_px" in line:
                klines_header_seen = True
                out.append(line); continue
            if klines_header_seen and line.strip():
                m_row = KLINES_ROW_RE.match(line)
                if m_row:
                    mmdd = m_row.group(1)
                    px_str = m_row.group(2)
                    vol_str = m_row.group(3)
                    old_pct = float(m_row.group(4))
                    new_pct_frac = klines_lookup.get((token.upper(), mmdd))
                    if new_pct_frac is not None:
                        new_pct = new_pct_frac * 100.0  # fraction 0-1 → percent 0-100
                        eol = "\r\n" if line.endswith("\r\n") else ("\n" if line.endswith("\n") else "")
                        # Preserve original spacing: ` MM-DD     0.NNNNNN       N,NNN,NNN      NN.N%`
                        # Rebuild with format matching sample
                        new_line = f" {mmdd}     {px_str:>9}   {vol_str:>13}      {new_pct:>4.1f}%{eol}"
                        out.append(new_line)
                        stats["klines_replaced"] += 1
                        continue
                    else:
                        stats["klines_kept_stale"] += 1
                        stats["klines_stale_dates"].append(mmdd)
                        out.append(line); continue
            out.append(line); continue

        out.append(line)
    return out, stats

def _detect_token(text):
    for line in text.split("\n"):
        m = RATIO_HEADER_RE.match(line)
        if m: return m.group(1).upper()
        # For files without RATIO block, try KLINES header
        m = KLINES_HEADER_RE.match(line)
        if m: return m.group(1).upper()
    return None

# ─── Main ───
print("═" * 90)
print(" [R4-v2 REGEN] LSR + RATIO taker + KLINES taker_buy_pct% — ⑩-AMENDMENT scope")
print("═" * 90)

lsr_lookup = _build_lsr_lookup(_load_store())
klines_lookup = _load_klines_taker()
print(f"  LSR lookup: {len(lsr_lookup)} keys")
print(f"  KLINES k[10]/k[7] lookup: {len(klines_lookup)} keys")

files = sorted(CASE_DIR.glob("*_result.txt"))
changelog_rows = []
for fpath in files:
    with open(fpath, "r", encoding="utf-8", errors="replace", newline="") as _f:
        text_current = _f.read()
    token = _detect_token(text_current)
    if not token:
        print(f"  {fpath.name}: <no RATIO or KLINES block — skip>")
        continue
    # Idempotent: read from .bak if exists (avoid re-processing regen'd file)
    bak_path = fpath.with_suffix(fpath.suffix + BACKUP_SUFFIX)
    if bak_path.exists():
        with open(bak_path, "r", encoding="utf-8", errors="replace", newline="") as _f:
            text = _f.read()
        md5_old = _md5(bak_path)
    else:
        shutil.copy2(fpath, bak_path)
        text = text_current
        md5_old = _md5(bak_path)
    lines = text.splitlines(keepends=True)
    new_lines, stats = _regen_file(lines, token, lsr_lookup, klines_lookup)
    new_text = "".join(new_lines)
    with open(fpath, "w", encoding="utf-8", newline="") as _f:
        _f.write(new_text)
    md5_new = _md5(fpath)
    changelog_rows.append({
        "file": fpath.name, "token": token,
        "md5_old": md5_old, "md5_new": md5_new,
        "ratio_replaced": stats["ratio_replaced"], "ratio_stale": stats["ratio_kept_stale"],
        "klines_replaced": stats["klines_replaced"], "klines_stale": stats["klines_kept_stale"],
        "backup": bak_path.name,
    })
    status = "CHANGED" if md5_old != md5_new else "IDENTICAL"
    print(f"  {fpath.name}: {status}  md5 {md5_old[:8]}→{md5_new[:8]}  "
          f"RATIO r={stats['ratio_replaced']}/s={stats['ratio_kept_stale']}  "
          f"KLINES r={stats['klines_replaced']}/s={stats['klines_kept_stale']}")

# Write changelog
CHANGELOG_PATH.parent.mkdir(parents=True, exist_ok=True)
with open(CHANGELOG_PATH, "w", encoding="utf-8") as f:
    f.write("# RESULTTXT-REGEN-v2-20260824 changelog (⑩-AMENDMENT scope)\n\n")
    f.write("R4-v2 regen: LSR (RATIO block topLSR_pos/topLSR_acc/globalLSR/takerRatio) "
            "+ KLINES taker_buy_pct% (⑩-AMENDMENT vế 2).\n\n")
    f.write("**Vế 2 scope:** cột `taker_buy_pct` KLINES trong _result.txt, nguồn fapi klines fresh "
            "k[10]/k[7] (quote/quote), ghi PERCENT 0-100 theo khuôn _result.\n\n")
    f.write("**Fresh k[10]/k[7] source:** VPS `/root/Data_back_test/whale_data/data/raw/klines_1h/` "
            "aggregated → `data/reference/klines_taker_daily_20260824.csv` (12 tokens × 116 dates, 987 rows).\n\n")
    f.write("**Backup L-37:** `.bak_pre_R4_20260824` giữ nguyên từ R4-v1 (idempotent).\n\n")
    f.write("**Ngoài scope (giữ nguyên):** funding block, OI block, KLINES avg_px + perp_vol$ (chỉ takerBUY% đổi).\n\n")
    f.write("**Code lineage:** ⑨-FIX `330d683` + ⑩-AMENDMENT bot-signals `41d8d717`.\n\n")
    f.write(f"| # | file | token | md5_old | md5_new | RATIO_r/s | KLINES_r/s | backup |\n")
    f.write(f"|---|---|---|---|---|---:|---:|---|\n")
    for i, r in enumerate(changelog_rows, 1):
        f.write(f"| {i} | `{r['file']}` | {r['token']} | `{r['md5_old']}` | `{r['md5_new']}` | "
                f"{r['ratio_replaced']}/{r['ratio_stale']} | {r['klines_replaced']}/{r['klines_stale']} | "
                f"`{r['backup']}` |\n")

print(f"\n  Changelog: {CHANGELOG_PATH}")
print(f"  Total files: {len(changelog_rows)}")
n_changed = sum(1 for r in changelog_rows if r['md5_old'] != r['md5_new'])
print(f"  CHANGED: {n_changed}  IDENTICAL: {len(changelog_rows) - n_changed}")
