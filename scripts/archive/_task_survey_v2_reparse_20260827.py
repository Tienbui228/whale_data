"""[SURVEY-V2 RE-PARSE · 0-call · KÝ 31/08]

Re-parse 33 raw JSON saved từ survey-Nansen (data/state/nansen_raw_survey/)
dùng CEX-address list curated (docs/reference/cex_addresses_bsc.txt).

Thay đổi vs v1:
  · dom_ex_exchange_v2 = Σ top10 loại ví-khớp-ADDRESS (không keyword)
    (v1 dùng keyword miss "Token Millionaire" = Binance-8 labeled generic)
  · dom_ex_structural bổ sung burn/dead pattern-match address (0x000...dead...)
  · CSV cột instrument {tracker-top100 | nansen-top10} mọi dòng
  · A1∪B split gắn cờ [MIXED-INSTRUMENT — context only]
  · Phép chính B vs C∪D same-instrument đậm
"""
from __future__ import annotations
import sys, io, os, json, hashlib, csv
from pathlib import Path
from statistics import median

REPO = Path(r"D:/Data back test/whale_data")
sys.path.insert(0, str(REPO / "scripts"))
from gom_h_daily import _md5

RAW_DIR = REPO / "data/state/nansen_raw_survey"
CEX_LIST_PATH = REPO / "docs/reference/cex_addresses_bsc.txt"
OUT_CSV = REPO / "docs/reports/survey_dom_level_v2_20260827.csv"

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
if CEX_LIST_PATH.exists():
    for line in CEX_LIST_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"): continue
        parts = line.split("\t")
        if len(parts) >= 2:
            CEX_ADDRESSES[parts[0].lower()] = parts[1]
print(f"[CEX-LIST] loaded {len(CEX_ADDRESSES)} curated addresses from {CEX_LIST_PATH.name}")
print(f"           md5={_md5(CEX_LIST_PATH)}")

# ─── Structural address heuristic (pattern-match) ───
STRUCTURAL_ADDRESSES_EXACT = {
    "0x0000000000000000000000000000000000000000",
    "0x000000000000000000000000000000000000dead",
}
STRUCTURAL_KEYWORDS = ["burn", "dead", "null", "lock", "vesting", "lp",
                       "treasury", "pool", "reserve", "team", "foundation"]

def classify_holder(record):
    """Return ('exchange', 'structural', 'other') using ADDRESS list + address heuristic."""
    addr = (record.get("address") or "").lower()
    label = (record.get("address_label") or "").lower()
    # Address curated exchange list
    if addr in CEX_ADDRESSES:
        return "exchange", CEX_ADDRESSES[addr]
    # Structural exact addresses
    if addr in STRUCTURAL_ADDRESSES_EXACT:
        return "structural", f"burn_{addr[:10]}"
    # Structural pattern: leading zeros pattern (0x00...dead / 0x00...0)
    if addr.startswith("0x00000000") or addr.endswith("dead"):
        return "structural", f"burn_pattern_{addr[:12]}"
    # Structural label keyword fallback
    if any(k in label for k in STRUCTURAL_KEYWORDS):
        return "structural", f"label_{label[:30]}"
    return "other", label or addr[:12]


# ─── Load raw JSON files ───
raw_files = sorted(RAW_DIR.glob("*_survey_tgm-holders_*.json"))
print(f"[RAW] loaded {len(raw_files)} JSON files from {RAW_DIR}")

# Extract token symbol from filename or from records (via contract match)
# Filename pattern: <ts>_survey_tgm-holders_<contract_short>_p1.json
# Better: read call_meta.token from file
token_records = {}  # {contract_full: records_list}
for f in raw_files:
    try:
        d = json.loads(f.read_text(encoding="utf-8"))
        contract = d.get("call_meta", {}).get("token", "")
        body = d.get("response_body", {})
        recs = body.get("data", []) if isinstance(body, dict) else []
        if contract:
            # Dedup: keep latest file per contract
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
    """Return dict with all 3 measures + n_loai_exchange + n_loai_structural + supply + labels."""
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
# Nhóm A: tracker-top100 instrument
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


# ─── BẢNG-CẶP A1 v2 ───
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


# ─── BẢNG TÓM v2 ───
print("\n[BẢNG TÓM v2 · median · p25-p75 · ≥0.80]")

def _num(v):
    try: return float(v)
    except: return None

summary = []
for nhom in ["A", "B", "C", "D"]:
    grp = [r for r in rows if r["nhom"] == nhom]
    for thuoc in ["dom_raw", "dom_ex_exchange_v2", "dom_ex_structural"]:
        vals = sorted([_num(r[thuoc]) for r in grp if _num(r[thuoc]) is not None])
        n_ge_80 = sum(1 for v in vals if v >= 0.80)
        pct_ge_80 = f"{100 * n_ge_80 / len(vals):.1f}%" if vals else "—"
        n = len(vals)
        med = median(vals) if vals else None
        p25 = vals[int(n*0.25)] if n >= 4 else None
        p75 = vals[int(n*0.75)] if n >= 4 else None
        s = {"nhom": nhom, "thuoc": thuoc, "instrument": "MIXED" if nhom == "A" else "nansen-top10",
             "n_valid": n, "n_total": len(grp),
             "median": f"{med:.3f}" if med is not None else "—",
             "p25": f"{p25:.3f}" if p25 is not None else "—",
             "p75": f"{p75:.3f}" if p75 is not None else "—",
             "n_ge_0.80": n_ge_80, "pct_ge_0.80": pct_ge_80}
        summary.append(s)

# Split rules per operator v2:
# A1∪B split gắn cờ [MIXED-INSTRUMENT — context only]
# Phép chính B vs C∪D same-instrument (nansen-top10) IN ĐẬM
a1_rows = [r for r in rows if r.get("nhom_con") == "A1"]
b_rows = [r for r in rows if r["nhom"] == "B"]
c_rows = [r for r in rows if r["nhom"] == "C"]
d_rows = [r for r in rows if r["nhom"] == "D"]

def _stats(rows_list, name, thuoc, instrument):
    vals = sorted([_num(r[thuoc]) for r in rows_list if _num(r[thuoc]) is not None])
    n_ge_80 = sum(1 for v in vals if v >= 0.80)
    pct_ge_80 = f"{100 * n_ge_80 / len(vals):.1f}%" if vals else "—"
    n = len(vals)
    med = median(vals) if vals else None
    return {"nhom": name, "thuoc": thuoc, "instrument": instrument,
            "n_valid": n, "n_total": len(rows_list),
            "median": f"{med:.3f}" if med is not None else "—",
            "p25": "—", "p75": "—",
            "n_ge_0.80": n_ge_80, "pct_ge_0.80": pct_ge_80}

# A1∪B MIXED-INSTRUMENT context only
for thuoc in ["dom_raw", "dom_ex_exchange_v2", "dom_ex_structural"]:
    summary.append(_stats(a1_rows + b_rows, "A1∪B[MIXED-CTX]", thuoc, "MIXED"))
# Phép chính B vs C∪D same-instrument
for thuoc in ["dom_raw", "dom_ex_exchange_v2", "dom_ex_structural"]:
    summary.append(_stats(b_rows, "★B(same-instr)★", thuoc, "nansen-top10"))
    summary.append(_stats(c_rows + d_rows, "★C∪D(same-instr)★", thuoc, "nansen-top10"))

print(f"  {'nhóm':>18} {'thước':>22} {'instr':>16} {'n_v/tot':>8} {'median':>7} {'p25':>7} {'p75':>7} {'%≥0.8':>7}")
for s in summary:
    print(f"  {s['nhom']:>18} {s['thuoc']:>22} {s['instrument']:>16} {s['n_valid']:>3}/{s['n_total']:>3} {s['median']:>7} {s['p25']:>7} {s['p75']:>7} {s['pct_ge_0.80']:>7}")


# ─── CSV output ───
OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
with open(OUT_CSV, "w", encoding="utf-8", newline="") as f:
    f.write(f"# SURVEY-V2 RE-PARSE · KÝ 31/08 · 0-call re-parse from raw JSON\n")
    f.write(f"# CEX list curated [CURATED-LIST-20260831]: docs/reference/cex_addresses_bsc.txt md5 {_md5(CEX_LIST_PATH)}\n")
    f.write(f"#   {len(CEX_ADDRESSES)} exchange addresses (Binance/OKX/Bybit/Gate/MEXC/Bitget/HTX/Kraken/Kucoin)\n")
    f.write(f"# Source raw: data/state/nansen_raw_survey/*.json ({len(raw_files)} files)\n")
    f.write(f"#\n")
    f.write(f"# 3 thước v2:\n")
    f.write(f"#   dom_raw               = Σ top10 ownership_percentage\n")
    f.write(f"#   dom_ex_exchange_v2   = trừ ví KHỚP-ADDRESS trong CEX list (NOT keyword)\n")
    f.write(f"#   dom_ex_structural     = trừ thêm burn/dead pattern (0x000.../....dead) + label keyword\n")
    f.write(f"# INSTRUMENT COL: tracker-top100 (nhóm A) vs nansen-top10 (nhóm B/C/D)\n")
    f.write(f"#\n")
    f.write(f"# BẢNG-CẶP A1 v2 (L-51 · tracker vs Nansen · sau CEX-list filter):\n")
    for bc in bang_cap:
        t_str = f"{bc['tracker']:.3f}" if bc['tracker'] is not None else "N/A"
        r_str = f"{bc['nansen_raw']:.4f}" if bc['nansen_raw'] is not None else "N/A"
        e_str = f"{bc['ex_exchange_v2']:.4f}" if bc['ex_exchange_v2'] is not None else "N/A"
        c_str = f"{bc['chenh_N_t']:+.4f}" if bc['chenh_N_t'] is not None else "N/A"
        f.write(f"#   {bc['tok']:5}  tracker={t_str}  Nansen-raw={r_str}  ex-exchange-v2={e_str}  chênh={c_str}  n_ex={bc['n_ex']}  labels={bc['ex_labels']}\n")
    f.write(f"#\n")
    f.write(f"# BẢNG TÓM v2 · phép chính ★B vs C∪D same-instrument★:\n")
    for s in summary:
        f.write(f"#   {s['nhom']:>20} × {s['thuoc']:>22} [{s['instrument']}]: n={s['n_valid']}/{s['n_total']} med={s['median']} p25={s['p25']} p75={s['p75']} ≥0.80={s['n_ge_0.80']} ({s['pct_ge_0.80']})\n")
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
