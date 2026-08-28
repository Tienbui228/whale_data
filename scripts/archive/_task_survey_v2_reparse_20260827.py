"""[SURVEY-V2 RE-PARSE · 0-call · KÝ 31/08 · rev2 08-31]

Re-parse 33 raw JSON saved từ survey-Nansen (data/state/nansen_raw_survey/)
dùng CEX-address list curated (data/ref/cex_addresses_bsc.txt — operator directive;
canonical đồng-content ở docs/reference/cex_addresses_bsc.txt vì .gitignore chặn data/ref/).

Rev2 (08-31) vs rev1:
  · Đổi tên OUT_CSV → survey_dom_level_nansen_v2_20260827.csv (v1 601984ad giữ mốc)
  · Cột MỚI Δ_ex = median(dom_raw) − median(dom_ex_exchange_v2) per nhóm
  · Một dòng so-sánh Δ_B vs Δ_C∪D (chẩn đoán kịch bản #4 "captive-trong-ví-sàn")
  · Header CSV thêm 3 kết-cục ANALYSIS làm khung đọc (KHÔNG kết luận)
"""
from __future__ import annotations
import sys, io, os, json, hashlib, csv
from pathlib import Path
from statistics import median

REPO = Path(r"D:/Data back test/whale_data")
sys.path.insert(0, str(REPO / "scripts"))
from gom_h_daily import _md5

RAW_DIR = REPO / "data/state/nansen_raw_survey"
# CEX list: try data/ref/ (operator directive) → fallback docs/reference/ (committed canonical)
CEX_LIST_PATH = REPO / "data/ref/cex_addresses_bsc.txt"
if not CEX_LIST_PATH.exists():
    CEX_LIST_PATH = REPO / "docs/reference/cex_addresses_bsc.txt"
CEX_CANONICAL = REPO / "docs/reference/cex_addresses_bsc.txt"
OUT_CSV = REPO / "docs/reports/survey_dom_level_nansen_v2_20260827.csv"

# ─── Token lists (same as v1 per operator freeze) ───
NHOM_A_TRACKER = [
    ("BANK", 0.51, "A2"), ("TUT", 0.83, "A1"), ("CYS", 0.81, "A2"),
    ("AKE", 0.86, "A1"), ("BTW", 0.96, "A1"), ("HEMI", 0.788, "A2"),
    ("ON", None, "A2"), ("CAP", 0.17, "A2"), ("BTR", None, "A2"),
]
NHOM_B = ["ACU", "ARIA", "ENSO", "FF", "FHE", "LIGHT", "MUBARAK", "SQD", "TRADOOR", "TUT", "XNY"]
NHOM_C = ['RAVE', 'BARD', '4', 'STAR', 'EDEN', 'COOKIE', 'CLO', 'BILL', 'B2', 'SHELL', 'ZEST', 'OPEN', 'ARX', 'PLAY', 'INX']
NHOM_D = ['AIA', 'AGT', 'BAS', 'DOOD', 'ESPORTS', 'PIEVERSE', 'SLX', 'RIVER', 'CROSS', 'TST']

# ─── Load CEX curated list ───
CEX_ADDRESSES = {}  # {addr_lower: name}
for line in CEX_LIST_PATH.read_text(encoding="utf-8").splitlines():
    line = line.strip()
    if not line or line.startswith("#"): continue
    parts = line.split("\t")
    if len(parts) >= 2:
        CEX_ADDRESSES[parts[0].lower()] = parts[1]
CEX_MD5 = _md5(CEX_LIST_PATH)
print(f"[CEX-LIST] loaded {len(CEX_ADDRESSES)} curated addresses from {CEX_LIST_PATH.relative_to(REPO)}")
print(f"           md5={CEX_MD5}")
print(f"[CEX-CANONICAL] committed at docs/reference/cex_addresses_bsc.txt md5={_md5(CEX_CANONICAL)}")
assert CEX_MD5 == _md5(CEX_CANONICAL), "data/ref vs docs/reference md5 mismatch — please sync"

# ─── Structural address heuristic (pattern-match) ───
STRUCTURAL_ADDRESSES_EXACT = {
    "0x0000000000000000000000000000000000000000",
    "0x000000000000000000000000000000000000dead",
}
STRUCTURAL_KEYWORDS = ["burn", "dead", "null", "lock", "vesting", "lp",
                       "treasury", "pool", "reserve", "team", "foundation"]

def classify_holder(record):
    """Return ('exchange'|'structural'|'other', name)."""
    addr = (record.get("address") or "").lower()
    label = (record.get("address_label") or "").lower()
    if addr in CEX_ADDRESSES:
        return "exchange", CEX_ADDRESSES[addr]
    if addr in STRUCTURAL_ADDRESSES_EXACT:
        return "structural", f"burn_{addr[:10]}"
    if addr.startswith("0x00000000") or addr.endswith("dead"):
        return "structural", f"burn_pattern_{addr[:12]}"
    if any(k in label for k in STRUCTURAL_KEYWORDS):
        return "structural", f"label_{label[:30]}"
    return "other", label or addr[:12]


# ─── Load raw JSON files ───
raw_files = sorted(RAW_DIR.glob("*_survey_tgm-holders_*.json"))
print(f"[RAW] loaded {len(raw_files)} JSON files from {RAW_DIR}")

token_records = {}  # {contract_full_lower: records_list}
for f in raw_files:
    try:
        d = json.loads(f.read_text(encoding="utf-8"))
        contract = d.get("call_meta", {}).get("token", "")
        body = d.get("response_body", {})
        recs = body.get("data", []) if isinstance(body, dict) else []
        if contract:
            token_records[contract.lower()] = recs
    except Exception as e:
        print(f"  WARN {f.name}: {e}")

# Map token symbol → contract (from Nansen snapshot)
SNAPS = Path(r"D:/Check onchain fresh wallets/snapshots")
CONTRACTS = {}
for p in sorted(SNAPS.glob("*.json"), reverse=True)[:5]:
    if not (p.stem[:4].isdigit() and len(p.stem) == 10): continue
    try: sd = json.loads(p.read_text(encoding="utf-8"))
    except: continue
    for r in sd.get("rows", []):
        if not r: continue
        s = (r.get("symbol") or "").upper()
        tok = (r.get("token", "") or "").lower()
        if s and tok and s not in CONTRACTS:
            CONTRACTS[s] = tok

def get_records_for(tok):
    contract = CONTRACTS.get(tok, "").lower()
    return token_records.get(contract, [])


# ─── Compute dominance v2 ───
def compute_dominance_v2(records):
    if not records:
        return {"dom_raw": None, "dom_ex_exchange_v2": None, "dom_ex_structural": None,
                "n_loai_exchange": 0, "n_loai_structural": 0,
                "supply": None, "top1_op": None,
                "exchange_labels": [], "structural_labels": []}
    recs = sorted(records, key=lambda r: -r.get("ownership_percentage", 0))
    top10 = recs[:10]
    sum_raw = sum(r.get("ownership_percentage", 0) for r in top10)
    n_ex = 0; n_st = 0
    sum_ex_ex = sum_raw
    sum_ex_st = sum_raw
    ex_labels = []; st_labels = []
    for r in top10:
        cat, name = classify_holder(r)
        op = r.get("ownership_percentage", 0)
        if cat == "exchange":
            n_ex += 1
            sum_ex_ex -= op
            sum_ex_st -= op
            ex_labels.append(f"{name}({op:.3f})")
        elif cat == "structural":
            n_st += 1
            sum_ex_st -= op
            st_labels.append(f"{name}({op:.3f})")
    supply = None
    for r in top10:
        op = r.get("ownership_percentage", 0)
        ta = r.get("token_amount", 0)
        if op > 0 and ta > 0:
            supply = ta / op; break
    top1_op = top10[0].get("ownership_percentage") if top10 else None
    return {"dom_raw": sum_raw, "dom_ex_exchange_v2": sum_ex_ex, "dom_ex_structural": sum_ex_st,
            "n_loai_exchange": n_ex, "n_loai_structural": n_st,
            "supply": supply, "top1_op": top1_op,
            "exchange_labels": ex_labels, "structural_labels": st_labels}


# ─── Assemble rows ───
print("\n[Assembling rows · v2 with instrument col]")
rows = []
# Nhóm A: tracker-top100 (minh-họa-nguồn-thesis, KHÔNG vào phép tách)
for tok, pct, sub in NHOM_A_TRACKER:
    contract = CONTRACTS.get(tok, "")
    rows.append({
        "nhom": "A", "nhom_con": sub, "token": tok,
        "instrument": "tracker-top100",
        "contract": contract, "chain": "bsc" if contract.startswith("0x") else "unknown",
        "source": "tracker-§10-rev9",
        "dom_raw":            f"{pct:.3f}" if pct is not None else "N/A-SOURCE-TRACKER",
        "n_loai_exchange":    "—", "dom_ex_exchange_v2":  "N/A-TRACKER-NO-BREAKDOWN",
        "n_loai_structural":  "—", "dom_ex_structural":   "N/A-TRACKER-NO-BREAKDOWN",
        "supply_used": "—", "source_supply": "tracker-derived[UNVERIFIED-SURVEY]",
        "exchange_labels": "—", "structural_labels": "—",
        "n_records_fetched": "—",
        "status": "TRACKER-OK" if pct else "N/A-SOURCE-TRACKER",
        "note": f"§10 tracker {pct or 'N/A'}",
    })

# Nhóm B/C/D: nansen-top10 instrument · re-parse với CEX list
for nhom, tokens_list in [("B", NHOM_B), ("C", NHOM_C), ("D", NHOM_D)]:
    for tok in tokens_list:
        contract = CONTRACTS.get(tok, "")
        recs = get_records_for(tok)
        m = compute_dominance_v2(recs)
        rows.append({
            "nhom": nhom, "nhom_con": nhom, "token": tok,
            "instrument": "nansen-top10",
            "contract": contract, "chain": "bsc" if contract.startswith("0x") else "unknown",
            "source": "nansen-/tgm/holders",
            "dom_raw":              f"{m['dom_raw']:.4f}" if m["dom_raw"] is not None else "N/A-NO-DATA",
            "n_loai_exchange":      m["n_loai_exchange"] if recs else "—",
            "dom_ex_exchange_v2":   f"{m['dom_ex_exchange_v2']:.4f}" if m["dom_ex_exchange_v2"] is not None else "N/A-NO-DATA",
            "n_loai_structural":    m["n_loai_structural"] if recs else "—",
            "dom_ex_structural":    f"{m['dom_ex_structural']:.4f}" if m["dom_ex_structural"] is not None else "N/A-NO-DATA",
            "supply_used":          f"{m['supply']:,.0f}" if m["supply"] else "—",
            "source_supply":        "nansen-derived (token_amount/op)",
            "exchange_labels":      " | ".join(m["exchange_labels"]) if m["exchange_labels"] else "—",
            "structural_labels":    " | ".join(m["structural_labels"]) if m["structural_labels"] else "—",
            "n_records_fetched":    len(recs),
            "status":               "OK" if recs else "N/A-NO-DATA",
            "note":                 f"top1_op={m['top1_op']:.4f}" if m["top1_op"] else "N/A",
        })


# ─── BẢNG-CẶP A1 v2 (minh họa nguồn thesis, không vào phép tách) ───
print("\n[BẢNG-CẶP A1 v2 (L-51) · tracker vs Nansen raw vs ex-exchange-v2]")
print(f"  {'tok':>5} {'tracker§10':>10} {'Nansen-raw':>10} {'ex-exchange-v2':>15} {'chênh(N-t)':>12} {'ex_labels':>40}")
bang_cap = []
for tok in ["TUT", "BTW", "AKE"]:
    tracker = next((p for (t,p,_) in NHOM_A_TRACKER if t == tok), None)
    recs = get_records_for(tok)
    m = compute_dominance_v2(recs)
    chenh = (m["dom_raw"] - tracker) if (m["dom_raw"] is not None and tracker is not None) else None
    labels = " | ".join(m["exchange_labels"])[:40] if m["exchange_labels"] else "—"
    if m["dom_raw"] is not None:
        print(f"  {tok:>5} {tracker:>10.3f} {m['dom_raw']:>10.4f} {m['dom_ex_exchange_v2']:>15.4f} {chenh:>+12.4f} {labels:>40}")
    else:
        t_str = f"{tracker:.3f}" if tracker is not None else "N/A"
        print(f"  {tok:>5} {t_str:>10} {'N/A':>10} {'N/A':>15} {'N/A':>12} {'N/A':>40}")
    bang_cap.append({"tok": tok, "tracker": tracker,
                     "nansen_raw": m["dom_raw"], "ex_exchange_v2": m["dom_ex_exchange_v2"],
                     "chenh_N_t": chenh, "n_ex": m["n_loai_exchange"], "ex_labels": labels})


# ─── BẢNG TÓM v2 · CỘT MỚI Δ_ex ───
print("\n[BẢNG TÓM v2 · median · p25-p75 · %≥0.80 · Δ_ex]")

def _num(v):
    try: return float(v)
    except: return None

def _stats_full(rows_list):
    """Return {thuoc: {'median': float, 'p25': float|None, 'p75': float|None, 'n_ge_80': int, 'pct_ge_80': str, 'n_valid': int}}"""
    result = {}
    for thuoc in ["dom_raw", "dom_ex_exchange_v2", "dom_ex_structural"]:
        vals = sorted([_num(r[thuoc]) for r in rows_list if _num(r[thuoc]) is not None])
        n = len(vals)
        n_ge_80 = sum(1 for v in vals if v >= 0.80)
        pct_ge_80 = f"{100 * n_ge_80 / n:.1f}%" if n else "—"
        med = median(vals) if vals else None
        p25 = vals[int(n*0.25)] if n >= 4 else None
        p75 = vals[int(n*0.75)] if n >= 4 else None
        result[thuoc] = {"median": med, "p25": p25, "p75": p75,
                         "n_ge_80": n_ge_80, "pct_ge_80": pct_ge_80,
                         "n_valid": n, "n_total": len(rows_list)}
    return result

# A1∪B[MIXED-CTX] · phép chính = B(nansen-top10) vs C∪D(nansen-top10)
a1_rows = [r for r in rows if r.get("nhom_con") == "A1"]
b_rows = [r for r in rows if r["nhom"] == "B"]
c_rows = [r for r in rows if r["nhom"] == "C"]
d_rows = [r for r in rows if r["nhom"] == "D"]
cd_rows = c_rows + d_rows

# Full per-nhóm stats (A/B/C/D) for baseline table
stats_by_grp = {}
for name, grp, instr in [
    ("A", [r for r in rows if r["nhom"] == "A"], "tracker-top100[MIXED]"),
    ("B", b_rows, "nansen-top10"),
    ("C", c_rows, "nansen-top10"),
    ("D", d_rows, "nansen-top10"),
    ("A1∪B[MIXED-CTX]", a1_rows + b_rows, "MIXED — context only"),
    ("★B(same-instr)★", b_rows, "nansen-top10"),
    ("★C∪D(same-instr)★", cd_rows, "nansen-top10"),
]:
    stats_by_grp[name] = {"stats": _stats_full(grp), "instrument": instr, "n_total": len(grp)}


def _fmt(v, digits=3):
    if v is None: return "—"
    return f"{v:.{digits}f}"


# Print bảng tóm rich (per-thuoc + Δ_ex derived)
print(f"  {'nhóm':>20} {'thước':>22} {'instr':>24} {'n_v/tot':>8} {'median':>7} {'p25':>7} {'p75':>7} {'%≥0.8':>7}  {'Δ_ex':>7}")
for name, meta in stats_by_grp.items():
    s = meta["stats"]
    d_raw_med = s["dom_raw"]["median"]
    d_ex_med = s["dom_ex_exchange_v2"]["median"]
    delta_ex = (d_raw_med - d_ex_med) if (d_raw_med is not None and d_ex_med is not None) else None
    for thuoc in ["dom_raw", "dom_ex_exchange_v2", "dom_ex_structural"]:
        st = s[thuoc]
        # Δ_ex shown once per nhóm (align with dom_ex_exchange_v2 row)
        d_str = _fmt(delta_ex, 3) if thuoc == "dom_ex_exchange_v2" else ""
        print(f"  {name:>20} {thuoc:>22} {meta['instrument']:>24} {st['n_valid']:>3}/{st['n_total']:>3} "
              f"{_fmt(st['median']):>7} {_fmt(st['p25']):>7} {_fmt(st['p75']):>7} {st['pct_ge_80']:>7}  {d_str:>7}")


# ─── DÒNG SO-SÁNH Δ_B vs Δ_C∪D (chẩn đoán kịch bản #4) ───
b_stats = stats_by_grp["★B(same-instr)★"]["stats"]
cd_stats = stats_by_grp["★C∪D(same-instr)★"]["stats"]
delta_B = b_stats["dom_raw"]["median"] - b_stats["dom_ex_exchange_v2"]["median"]
delta_CD = cd_stats["dom_raw"]["median"] - cd_stats["dom_ex_exchange_v2"]["median"]

print()
print(f"[Δ SO-SÁNH · chẩn đoán kịch bản #4 captive-trong-ví-sàn]")
print(f"  Δ_B      = med(raw) − med(ex_exchange_v2) = {b_stats['dom_raw']['median']:.3f} − {b_stats['dom_ex_exchange_v2']['median']:.3f} = {delta_B:+.3f}")
print(f"  Δ_C∪D    = med(raw) − med(ex_exchange_v2) = {cd_stats['dom_raw']['median']:.3f} − {cd_stats['dom_ex_exchange_v2']['median']:.3f} = {delta_CD:+.3f}")
if delta_B > delta_CD:
    diag = "Δ_B > Δ_C∪D → B rớt MẠNH HƠN sau loại-sàn (chỉ dấu kịch bản #4 · KHÔNG kết luận)"
elif delta_B < delta_CD:
    diag = "Δ_B < Δ_C∪D → B rớt YẾU HƠN sau loại-sàn (KHÔNG khớp kịch bản #4)"
else:
    diag = "Δ_B ≈ Δ_C∪D → sức rớt tương đương"
print(f"  DIAG    : {diag}")


# ─── CSV output ───
OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
with open(OUT_CSV, "w", encoding="utf-8", newline="") as f:
    f.write(f"# SURVEY-V2 RE-PARSE · KÝ 31/08 rev2 08-31 · 0-call re-parse from raw JSON\n")
    f.write(f"# Đợt-1 mốc: docs/reports/survey_dom_level_nansen_20260827.csv md5 601984ad… (giữ nguyên)\n")
    f.write(f"# CEX list [CURATED-LIST-20260831]:\n")
    f.write(f"#   operator-path: data/ref/cex_addresses_bsc.txt (gitignored · runtime local)\n")
    f.write(f"#   canonical    : docs/reference/cex_addresses_bsc.txt (committed · md5 {_md5(CEX_CANONICAL)})\n")
    f.write(f"#   {len(CEX_ADDRESSES)} exchange addresses (Binance/OKX/Bybit/Gate/MEXC/Bitget/HTX/Kraken/Kucoin)\n")
    f.write(f"# Source raw: data/state/nansen_raw_survey/*.json ({len(raw_files)} files)\n")
    f.write(f"#\n")
    f.write(f"# 3 thước v2:\n")
    f.write(f"#   dom_raw               = Σ top10 ownership_percentage\n")
    f.write(f"#   dom_ex_exchange_v2   = trừ ví KHỚP-ADDRESS trong CEX list (NOT keyword)\n")
    f.write(f"#   dom_ex_structural     = trừ thêm burn/dead pattern (0x000.../....dead) + label keyword\n")
    f.write(f"# INSTRUMENT COL: tracker-top100 (nhóm A) vs nansen-top10 (nhóm B/C/D)\n")
    f.write(f"#\n")
    f.write(f"# ─── 3 KẾT-CỤC ANALYSIS làm khung đọc (KHÔNG kết luận · luật đọc (i)-(iv)) ───\n")
    f.write(f"#   (α) sống-refined              : ≥1 thước tách được B vs C∪D bền (H4 tồn tại với thước-loại-sàn/loại-cấu-trúc)\n")
    f.write(f"#   (β) chết-ba-thước [CLOSED-BY-DISTRIBUTION]: cả 3 thước đều KHÔNG tách B vs C∪D (H4 chết vì không phân định)\n")
    f.write(f"#   (γ) chết-nguyên-lý            : dom_raw B ≥ C∪D nhưng dom_ex_exchange B ≤ C∪D + Δ_B > Δ_C∪D\n")
    f.write(f"#                                    → \"kho captive nằm TRONG ví sàn\" (H4 chết-nguyên-lý)\n")
    f.write(f"#\n")
    f.write(f"# ─── BẢNG-CẶP A1 v2 (L-51 · tracker vs Nansen · minh họa nguồn thesis) ───\n")
    for bc in bang_cap:
        t_str = f"{bc['tracker']:.3f}" if bc['tracker'] is not None else "N/A"
        r_str = f"{bc['nansen_raw']:.4f}" if bc['nansen_raw'] is not None else "N/A"
        e_str = f"{bc['ex_exchange_v2']:.4f}" if bc['ex_exchange_v2'] is not None else "N/A"
        c_str = f"{bc['chenh_N_t']:+.4f}" if bc['chenh_N_t'] is not None else "N/A"
        f.write(f"#   {bc['tok']:5}  tracker={t_str}  Nansen-raw={r_str}  ex-exchange-v2={e_str}  chênh={c_str}  n_ex={bc['n_ex']}  labels={bc['ex_labels']}\n")
    f.write(f"#\n")
    f.write(f"# ─── BẢNG TÓM v2 · median · p25-p75 · %≥0.80 · Δ_ex per nhóm ───\n")
    f.write(f"#   {'nhóm':>20} {'thước':>22} {'instr':>24} n_v/tot median  p25    p75    %≥0.8  Δ_ex\n")
    for name, meta in stats_by_grp.items():
        s = meta["stats"]
        d_raw_med = s["dom_raw"]["median"]
        d_ex_med = s["dom_ex_exchange_v2"]["median"]
        delta_ex = (d_raw_med - d_ex_med) if (d_raw_med is not None and d_ex_med is not None) else None
        for thuoc in ["dom_raw", "dom_ex_exchange_v2", "dom_ex_structural"]:
            st = s[thuoc]
            d_str = _fmt(delta_ex, 3) if thuoc == "dom_ex_exchange_v2" else ""
            f.write(f"#   {name:>20} {thuoc:>22} {meta['instrument']:>24} "
                    f"{st['n_valid']:>3}/{st['n_total']:>3} "
                    f"{_fmt(st['median']):>7} {_fmt(st['p25']):>7} {_fmt(st['p75']):>7} {st['pct_ge_80']:>7}  {d_str:>6}\n")
    f.write(f"#\n")
    f.write(f"# ─── Δ SO-SÁNH (chẩn đoán kịch bản #4 captive-trong-ví-sàn) ───\n")
    f.write(f"#   Δ_B      = {b_stats['dom_raw']['median']:.3f} − {b_stats['dom_ex_exchange_v2']['median']:.3f} = {delta_B:+.3f}\n")
    f.write(f"#   Δ_C∪D    = {cd_stats['dom_raw']['median']:.3f} − {cd_stats['dom_ex_exchange_v2']['median']:.3f} = {delta_CD:+.3f}\n")
    f.write(f"#   DIAG    : {diag}\n")
    f.write(f"#\n")
    f.write(f"# NGƯỠNG PHỦ: B={sum(1 for r in rows if r['nhom']=='B' and r.get('status')=='OK')}/11 · C={sum(1 for r in rows if r['nhom']=='C' and r.get('status')=='OK')}/15\n")
    f.write(f"# KHÔNG kết luận — luật đọc (i)-(iv) ANALYSIS\n")
    f.write(f"#\n")
    if rows:
        cols = list(rows[0].keys())
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in rows: w.writerow(r)

md5_out = _md5(OUT_CSV)
n_lines = sum(1 for _ in open(OUT_CSV, "r", encoding="utf-8"))
print(f"\n[OUT] {OUT_CSV}")
print(f"[MD5] {md5_out}")
print(f"[WC ] {n_lines}")
print(f"[COST] 0 credits (re-parse only · budget survey giữ 12)")
