"""[SURVEY-NANSEN one-shot · KÝ 31/08 · budget ≤45 call]

Nguồn: Nansen /tgm/holders page-1 rpp-10 (cùng-máy-đo H4 production)
Tokens: 39 = 36 B∪C∪D (SEED=42 chốt) + 3 A1 (TUT·BTW·AKE)
Ledger riêng: survey_oneshot (KHÔNG chạm H4 cap 2/ngày)
Raw-save mỗi call: nansen_raw_survey/<ts>_survey_...json

Thước 3 loại:
  dom_raw           = Σ top10 ownership_percentage
  dom_ex_exchange   = trừ label chứa "exchange"/"Binance"/"Gate"/etc.
  dom_ex_structural = trừ thêm burn/dead/lock/vesting/LP/treasury (label + address heuristic)

Bảng-cặp A1: TUT·BTW·AKE · tracker vs Nansen-raw vs ex-exchange
Bảng tóm: median/p25-p75 × nhóm × thước · A1∪B vs C∪D · ≥0.80

CSV + md5 + wc + ledger tổng credits.
"""
from __future__ import annotations
import sys, io, os, json, hashlib, csv, asyncio, time
from pathlib import Path
from datetime import datetime, timezone
from statistics import median

REPO = Path(r"D:/Data back test/whale_data")
BOT_DIR = Path(r"D:/Check onchain fresh wallets")
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(BOT_DIR))

from gom_h_daily import _load_universe, _md5

# [Survey KÝ 31/08] operator ky survey-Nansen · load NANSEN_KEY_LOCKED → NANSEN_API_KEY
# for bot core_nansen usage (task-scoped, không rename permanent)
if not os.getenv("NANSEN_API_KEY"):
    env_path = BOT_DIR / ".env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            if line.startswith("NANSEN_KEY_LOCKED="):
                os.environ["NANSEN_API_KEY"] = line.split("=", 1)[1].strip()
                break

# Import Nansen bot survey wrapper (AFTER env set)
import httpx
from core_nansen import fetch_holders_survey, CHAIN, SURVEY_LEDGER_PATH, NANSEN_SURVEY_BUDGET

# ─── Token lists (per operator ky 31/08) ───
NHOM_A_TRACKER = [
    ("BANK", 0.51, "A2"), ("TUT", 0.83, "A1"), ("CYS", 0.81, "A2"),
    ("AKE", 0.86, "A1"), ("BTW", 0.96, "A1"), ("HEMI", 0.788, "A2"),
    ("ON", None, "A2"), ("CAP", 0.17, "A2"), ("BTR", None, "A2"),
]
NHOM_B = ["ACU", "ARIA", "ENSO", "FF", "FHE", "LIGHT", "MUBARAK", "SQD", "TRADOOR", "TUT", "XNY"]
NHOM_C = ['RAVE', 'BARD', '4', 'STAR', 'EDEN', 'COOKIE', 'CLO', 'BILL', 'B2', 'SHELL', 'ZEST', 'OPEN', 'ARX', 'PLAY', 'INX']
NHOM_D = ['AIA', 'AGT', 'BAS', 'DOOD', 'ESPORTS', 'PIEVERSE', 'SLX', 'RIVER', 'CROSS', 'TST']

# 3 A1 tokens for bảng-cặp (already in A but need Nansen call too)
A1_BANG_CAP = ["TUT", "BTW", "AKE"]

# 39 tokens to call = 36 (B∪C∪D unique) + 3 A1
# TUT in both B and A1 → 1 call for TUT
b_set = set(NHOM_B)
c_set = set(NHOM_C)
d_set = set(NHOM_D)
bcd_set = b_set | c_set | d_set
a1_set = set(A1_BANG_CAP)
# Union · TUT overlap counted once
all_to_call = sorted(bcd_set | a1_set)
print(f"[SURVEY-NANSEN] {len(all_to_call)} unique tokens to call (target ≤45)")

# ─── Load contracts from Nansen snapshot ───
SNAPS = Path(r"D:/Check onchain fresh wallets/snapshots")
CONTRACTS = {}
for p in sorted(SNAPS.glob("*.json"), reverse=True)[:5]:
    if not (p.stem[:4].isdigit() and len(p.stem) == 10): continue
    try: d = json.loads(p.read_text(encoding="utf-8"))
    except: continue
    for r in d.get("rows", []):
        if not r: continue
        s = (r.get("symbol") or "").upper()
        tok = r.get("token", "")
        if s and tok and s not in CONTRACTS:
            CONTRACTS[s] = tok

# Filter contracts for target tokens
target_contracts = {}
for tok in all_to_call:
    c = CONTRACTS.get(tok) or CONTRACTS.get(tok + "USDT")
    if c:
        target_contracts[tok] = c
    else:
        print(f"  WARN: no contract for {tok}")

print(f"  Contracts resolved: {len(target_contracts)}/{len(all_to_call)}")

# ═══════════════════════════════════════════════════════════════════════════════
# EXCHANGE LABEL HEURISTIC
# ═══════════════════════════════════════════════════════════════════════════════
EXCHANGE_KEYWORDS = ["exchange", "binance", "gate", "mexc", "bybit", "okx", "kucoin",
                     "bitget", "bitfinex", "coinbase", "kraken", "huobi", "cex", "hot wallet"]
STRUCTURAL_KEYWORDS = ["burn", "dead", "null", "lock", "vesting", "lp", "treasury",
                       "pool", "reserve", "team", "foundation"]
STRUCTURAL_ADDRESSES = {
    "0x0000000000000000000000000000000000000000",
    "0x000000000000000000000000000000000000dead",
    "0x000000000000000000000000000000000000dEaD",
}


def classify_label(record):
    """Return ('exchange', 'structural', 'other') based on label + address heuristic."""
    addr = (record.get("address") or "").lower()
    label = (record.get("address_label") or "").lower()
    if addr in {a.lower() for a in STRUCTURAL_ADDRESSES}:
        return "structural"
    if any(k in label for k in EXCHANGE_KEYWORDS):
        return "exchange"
    if any(k in label for k in STRUCTURAL_KEYWORDS):
        return "structural"
    return "other"


# ═══════════════════════════════════════════════════════════════════════════════
# Nansen call wrapper — async, rate-limit lễ phép
# ═══════════════════════════════════════════════════════════════════════════════
async def call_all():
    results = {}
    async with httpx.AsyncClient() as client:
        for i, tok in enumerate(all_to_call):
            contract = target_contracts.get(tok)
            if not contract:
                results[tok] = {"status": "NO-CONTRACT", "records": None}
                continue
            print(f"  [{i+1}/{len(all_to_call)}] {tok} {contract[:12]}...", end=" ", flush=True)
            records, status = await fetch_holders_survey(client, contract)
            print(f"→ {status}")
            results[tok] = {"status": status, "records": records or []}
            await asyncio.sleep(0.3)  # rate lễ phép
    return results

print(f"\n[Calling Nansen · budget cap={NANSEN_SURVEY_BUDGET}]")
call_results = asyncio.run(call_all())

# ═══════════════════════════════════════════════════════════════════════════════
# Compute 3 thước per token
# ═══════════════════════════════════════════════════════════════════════════════
def compute_dominance(records):
    """Return (raw, ex_exchange, ex_structural, n_exchange, n_structural, supply, top1_op)"""
    if not records:
        return None, None, None, 0, 0, None, None
    # Sort by ownership_percentage desc (usually already, but ensure)
    recs = sorted(records, key=lambda r: -r.get("ownership_percentage", 0))
    top10 = recs[:10]
    sum_raw = sum(r.get("ownership_percentage", 0) for r in top10)
    n_ex = 0; n_struct = 0
    sum_ex_exchange = sum_raw
    sum_ex_structural = sum_raw
    for r in top10:
        cat = classify_label(r)
        if cat == "exchange":
            n_ex += 1
            sum_ex_exchange -= r.get("ownership_percentage", 0)
            sum_ex_structural -= r.get("ownership_percentage", 0)
        elif cat == "structural":
            n_struct += 1
            sum_ex_structural -= r.get("ownership_percentage", 0)
    # Supply derived: token_amount / ownership_percentage (from any valid record)
    supply = None
    for r in top10:
        op = r.get("ownership_percentage", 0)
        ta = r.get("token_amount", 0)
        if op > 0 and ta > 0:
            supply = ta / op
            break
    top1_op = top10[0].get("ownership_percentage") if top10 else None
    return sum_raw, sum_ex_exchange, sum_ex_structural, n_ex, n_struct, supply, top1_op


# Assemble rows
rows = []
# Nhóm A: 9 dòng tracker (chép §10 · giữ như bản chỉnh)
for tok, pct, sub in NHOM_A_TRACKER:
    row = {
        "nhom": "A", "nhom_con": sub, "token": tok,
        "contract": target_contracts.get(tok, "—"),
        "chain": "bsc" if target_contracts.get(tok, "").startswith("0x") else "unknown",
        "source": "tracker-§10-rev9",
        "dom_raw":            f"{pct:.3f}" if pct is not None else "N/A-SOURCE-TRACKER",
        "n_loai_exchange":    "—", "dom_ex_exchange":   "N/A-TRACKER-NO-BREAKDOWN",
        "n_loai_structural":  "—", "dom_ex_structural": "N/A-TRACKER-NO-BREAKDOWN",
        "supply_used": "—", "source_supply": "tracker-derived[UNVERIFIED-SURVEY]",
        "n_records_fetched": "—",
        "status": "TRACKER-OK" if pct else "N/A-SOURCE-TRACKER",
        "note": f"§10 tracker {pct or 'N/A'}",
    }
    rows.append(row)

# Nhóm B/C/D: Nansen data
for nhom, tokens_list in [("B", NHOM_B), ("C", NHOM_C), ("D", NHOM_D)]:
    for tok in tokens_list:
        r = call_results.get(tok, {"status": "NOT-CALLED", "records": []})
        records = r.get("records") or []
        raw, ex_ex, ex_st, n_ex, n_st, supply, top1_op = compute_dominance(records)
        contract = target_contracts.get(tok, "—")
        rows.append({
            "nhom": nhom, "nhom_con": nhom, "token": tok, "contract": contract,
            "chain": "bsc" if contract.startswith("0x") else "unknown",
            "source": "nansen-/tgm/holders",
            "dom_raw":            f"{raw:.4f}" if raw is not None else "N/A",
            "n_loai_exchange":    n_ex if raw is not None else "—",
            "dom_ex_exchange":    f"{ex_ex:.4f}" if ex_ex is not None else "N/A",
            "n_loai_structural":  n_st if raw is not None else "—",
            "dom_ex_structural":  f"{ex_st:.4f}" if ex_st is not None else "N/A",
            "supply_used":        f"{supply:,.0f}" if supply else "—",
            "source_supply":      "nansen-derived (token_amount/op)",
            "n_records_fetched":  len(records),
            "status": r.get("status"),
            "note":   f"top1_op={top1_op:.4f}" if top1_op else "N/A",
        })

# ═══════════════════════════════════════════════════════════════════════════════
# BẢNG-CẶP A1 (L-51) · TUT · BTW · AKE
# ═══════════════════════════════════════════════════════════════════════════════
print("\n[BẢNG-CẶP A1 (L-51)]")
print(f"{'tok':>5} {'tracker§10':>12} {'Nansen-raw':>12} {'ex-exchange':>12} {'chênh(N-t)':>12}")
bang_cap = []
for tok in A1_BANG_CAP:
    tracker = next((p for (t,p,_) in NHOM_A_TRACKER if t == tok), None)
    r = call_results.get(tok, {"records": []})
    records = r.get("records") or []
    raw, ex_ex, ex_st, n_ex, n_st, sup, _ = compute_dominance(records)
    chenh_nt = (raw - tracker) if (raw is not None and tracker is not None) else None
    print(f"{tok:>5} {tracker:>12.3f}" if tracker else f"{tok:>5} {'N/A':>12}", end="")
    print(f" {raw:>12.4f}" if raw is not None else f" {'N/A':>12}", end="")
    print(f" {ex_ex:>12.4f}" if ex_ex is not None else f" {'N/A':>12}", end="")
    print(f" {chenh_nt:>+12.4f}" if chenh_nt is not None else f" {'N/A':>12}")
    bang_cap.append({"tok": tok, "tracker": tracker, "nansen_raw": raw,
                     "ex_exchange": ex_ex, "chenh_N_t": chenh_nt,
                     "n_loai_exchange": n_ex})

# ═══════════════════════════════════════════════════════════════════════════════
# BẢNG TÓM
# ═══════════════════════════════════════════════════════════════════════════════
print("\n[BẢNG TÓM · median · p25-p75 · ≥0.80]")

def _num(v):
    try: return float(v)
    except: return None

summary = []
for nhom in ["A", "B", "C", "D"]:
    grp = [r for r in rows if r["nhom"] == nhom]
    for thuoc in ["dom_raw", "dom_ex_exchange", "dom_ex_structural"]:
        vals = sorted([_num(r[thuoc]) for r in grp if _num(r[thuoc]) is not None])
        n_ge_80 = sum(1 for v in vals if v >= 0.80)
        n = len(vals)
        med = median(vals) if vals else None
        p25 = vals[int(n*0.25)] if n >= 4 else None
        p75 = vals[int(n*0.75)] if n >= 4 else None
        s = {"nhom": nhom, "thuoc": thuoc,
             "n_valid": n, "n_total": len(grp),
             "median": f"{med:.3f}" if med is not None else "—",
             "p25": f"{p25:.3f}" if p25 is not None else "—",
             "p75": f"{p75:.3f}" if p75 is not None else "—",
             "n_ge_0.80": n_ge_80}
        summary.append(s)

# A1 vs A2 vs A1∪B vs C∪D
a1_rows = [r for r in rows if r.get("nhom_con") == "A1"]
b_rows = [r for r in rows if r["nhom"] == "B"]
c_rows = [r for r in rows if r["nhom"] == "C"]
d_rows = [r for r in rows if r["nhom"] == "D"]

def _split_stats(rows_list, name, thuoc):
    vals = sorted([_num(r[thuoc]) for r in rows_list if _num(r[thuoc]) is not None])
    n_ge_80 = sum(1 for v in vals if v >= 0.80)
    n = len(vals)
    med = median(vals) if vals else None
    return {"nhom": name, "thuoc": thuoc, "n_valid": n, "n_total": len(rows_list),
            "median": f"{med:.3f}" if med is not None else "—",
            "p25": "—", "p75": "—", "n_ge_0.80": n_ge_80}

for thuoc in ["dom_raw", "dom_ex_exchange", "dom_ex_structural"]:
    summary.append(_split_stats(a1_rows + b_rows, "A1∪B", thuoc))
    summary.append(_split_stats(c_rows + d_rows, "C∪D", thuoc))

# Print summary
print(f"  {'nhóm':>6} {'thước':>22} {'n_valid':>8} {'n_total':>8} {'median':>8} {'p25':>7} {'p75':>7} {'≥0.80':>7}")
for s in summary:
    print(f"  {s['nhom']:>6} {s['thuoc']:>22} {s['n_valid']:>8} {s['n_total']:>8} {s['median']:>8} {s['p25']:>7} {s['p75']:>7} {s['n_ge_0.80']:>7}")

# ═══════════════════════════════════════════════════════════════════════════════
# CSV OUTPUT
# ═══════════════════════════════════════════════════════════════════════════════
OUT_CSV = REPO / "docs/reports/survey_dom_level_nansen_20260827.csv"
# Credit accounting
n_calls_ok = sum(1 for r in call_results.values() if r["status"] == "OK")
n_calls_fail = sum(1 for r in call_results.values() if r["status"] in ("API-FAIL", "BUDGET-EXCEEDED"))
total_credits = n_calls_ok * 5

OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
with open(OUT_CSV, "w", encoding="utf-8", newline="") as f:
    f.write(f"# SURVEY-NANSEN one-shot · KÝ 31/08 · budget ≤45 call\n")
    f.write(f"# Source: Nansen /tgm/holders page-1 rpp-10 (cùng-máy-đo H4 production)\n")
    f.write(f"# Ledger riêng: {SURVEY_LEDGER_PATH}\n")
    f.write(f"# Etherscan $49 wrapper: HỦY per operator 31/08 (survey_path_a_setup SUPERSEDED)\n")
    f.write(f"# Tokens called: {len(all_to_call)} · ok={n_calls_ok} · fail={n_calls_fail} · credits={total_credits}\n")
    f.write(f"#\n")
    f.write(f"# 3 thước:\n")
    f.write(f"#   dom_raw           = Σ top10 ownership_percentage\n")
    f.write(f"#   dom_ex_exchange   = trừ label chứa exchange/Binance/Gate/Bitget/... (n_loại)\n")
    f.write(f"#   dom_ex_structural = trừ thêm burn/dead/lock/vesting/LP/treasury/pool/reserve/team/foundation\n")
    f.write(f"# cờ [UNVERIFIED-SURVEY]: label heuristic từ Nansen · chưa cross-verify với bapi/dexscreener\n")
    f.write(f"#\n")
    f.write(f"# BẢNG-CẶP A1 (L-51 nghi thức trước [0.80] ký):\n")
    for bc in bang_cap:
        t_str = f"{bc['tracker']:.3f}" if bc['tracker'] is not None else "N/A"
        r_str = f"{bc['nansen_raw']:.4f}" if bc['nansen_raw'] is not None else "N/A"
        e_str = f"{bc['ex_exchange']:.4f}" if bc['ex_exchange'] is not None else "N/A"
        c_str = f"{bc['chenh_N_t']:+.4f}" if bc['chenh_N_t'] is not None else "N/A"
        f.write(f"#   {bc['tok']:5}  tracker§10={t_str}  Nansen-raw={r_str}  ex-exchange={e_str}  chênh(N-t)={c_str}\n")
    f.write(f"#\n")
    f.write(f"# BẢNG TÓM · median · p25-p75 × nhóm × thước · ≥0.80:\n")
    for s in summary:
        f.write(f"#   {s['nhom']:>6} × {s['thuoc']:>22}: n={s['n_valid']}/{s['n_total']} med={s['median']} p25={s['p25']} p75={s['p75']} ≥0.80={s['n_ge_0.80']}\n")
    f.write(f"#\n")
    f.write(f"# NGƯỠNG PHỦ (per operator): B≥7/11 · C≥10/15 (Nansen phủ được là qua ngưỡng dễ)\n")
    f.write(f"# KHÔNG kết luận · luật đọc (i)-(iv) ANALYSIS\n")
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
print(f"[LEDGER] {SURVEY_LEDGER_PATH}")
print(f"[CREDITS] {total_credits}cr consumed · budget cap={NANSEN_SURVEY_BUDGET} · remaining={NANSEN_SURVEY_BUDGET - n_calls_ok}")
