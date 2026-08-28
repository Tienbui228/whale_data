"""MA-D3 DELIST-FLAG column · zero-call bên trong workflow (2 public API calls) · KÝ 01/09

Sources (OR):
  (1) fullyDelisted (Alpha bapi L-48): fetch alpha token list public endpoint
  (2) spot status ≠ TRADING (exchangeInfo, proxy cho deposit-closed L-52a + network-withdrawal):
      status ∈ {HALT, BREAK, END_OF_DAY, AUCTION_MATCH, PRE_TRADING, POST_TRADING} → flag
  (3) walletset BROAD-QUIET persistent (từ VPS gom_h_daily.log, ≥3 emits trong 30d recent = persistent)

Note: sapi/capital/config/getall requires auth key → dùng exchangeInfo status làm proxy hợp lý
(nếu delist thì status=BREAK/END; nếu chỉ deposit-closed thì status=TRADING nhưng operator ky proxy).

Output:
  Per-token bảng: {token · flag_status · flag_alpha_delist · flag_walletset_quiet · flag_ANY · sources}
  Dòng tổng: % fire-mass (n_ma_fires) mang flag=True
"""
import sys, io, csv, hashlib, json, urllib.request, subprocess, glob
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
from collections import Counter

ROOT = Path(r"D:\Data back test\whale_data")
MA_CSV = ROOT / "docs" / "reports" / "ma_shadow_backtest_20260828.csv"
OUT_CSV = ROOT / "docs" / "reports" / "ma_delist_flag_20260828.csv"
S6_MAP = ROOT / "scratch" / "s6_fw139_binance_spot_map_20260827.csv"

def fetch_json(url, timeout=15):
    req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        return {"_error": str(e)}

# ── 51 tokens từ s6 map ──
tokens_51 = []
with open(S6_MAP, encoding="utf-8") as f:
    for r in csv.DictReader(f):
        if r["has_binance_spot"] == "YES":
            tokens_51.append(r["symbol"] + "USDT")
print(f"[LOAD] 51 tokens (from s6 map)")

# ── (1) exchangeInfo public — spot status ──
print(f"\n[FETCH-1] api.binance.com/api/v3/exchangeInfo")
ei = fetch_json("https://api.binance.com/api/v3/exchangeInfo")
if "_error" in ei:
    print(f"  FAIL: {ei['_error']}")
    ei_status = {}
else:
    ei_status = {s["symbol"]: s["status"] for s in ei.get("symbols", [])}
    print(f"  OK · {len(ei_status)} symbols fetched")

# ── (2) Alpha bapi public — fullyDelisted ──
print(f"\n[FETCH-2] bapi Alpha token list")
alpha_url = "https://www.binance.com/bapi/defi/v1/public/wallet-direct/buw/wallet/cex/alpha/all/token/list"
alpha_data = fetch_json(alpha_url)
alpha_delisted = {}  # {symbol_upper: fullyDelisted_bool}
if "_error" in alpha_data or not isinstance(alpha_data.get("data"), list):
    print(f"  FAIL or no list: {alpha_data.get('_error', 'no data list')}")
else:
    for item in alpha_data.get("data", []):
        sym = (item.get("symbol") or "").upper()
        if sym:
            alpha_delisted[sym] = bool(item.get("fullyDelisted", False))
    n_del = sum(1 for v in alpha_delisted.values() if v)
    print(f"  OK · {len(alpha_delisted)} alpha entries · {n_del} fullyDelisted=True")

# ── (3) VPS gom_h_daily.log walletset BROAD-QUIET counts ──
print(f"\n[FETCH-3] VPS gom_h_daily.log grep BROAD-QUIET")
try:
    ssh_out = subprocess.check_output(
        ["ssh", "-o", "ConnectTimeout=5", "root@5.223.67.21",
         "grep 'BROAD-QUIET' /root/Data_back_test/whale_data/data/logs/gom_h_daily.log"],
        stderr=subprocess.STDOUT, timeout=15
    ).decode()
    quiet_counter = Counter()
    for line in ssh_out.splitlines():
        # Line format: "  TOKENUSDT  [...]  ...  [WALLETSET: BROAD-QUIET]"
        parts = line.strip().split()
        if not parts: continue
        tok = parts[0]
        if tok.endswith("USDT"):
            quiet_counter[tok] += 1
    print(f"  OK · BROAD-QUIET emits per-token: {len(quiet_counter)} tokens · max={max(quiet_counter.values()) if quiet_counter else 0}")
except Exception as e:
    print(f"  FAIL VPS grep: {e}")
    quiet_counter = Counter()

PERSISTENT_THRESH = 3  # ≥3 BROAD-QUIET emits = persistent

# ── Load MA fires per token ──
print(f"\n[LOAD] MA-shadow fire counts per token")
ma_fires = Counter()
with open(MA_CSV, encoding="utf-8") as f:
    for line in f:
        if line.startswith("#") or line.startswith("symbol,"): continue
        p = line.rstrip("\n").split(",")
        if len(p) < 8: continue
        if p[7] == "True":
            ma_fires[p[0]] += 1
print(f"  MA fires: {sum(ma_fires.values())} total across {len(ma_fires)} tokens")

# ── Build per-token flag table ──
rows = []
for tok in sorted(tokens_51):
    tok_base = tok.replace("USDT", "")
    # (1) spot status flag
    st = ei_status.get(tok, "N/A")
    flag_status = (st not in ["TRADING", "N/A"])  # HALT/BREAK/END etc.
    # (2) alpha fullyDelisted
    alpha_del = alpha_delisted.get(tok_base, None)
    flag_alpha = bool(alpha_del) if alpha_del is not None else False
    # (3) walletset BROAD-QUIET persistent
    quiet_n = quiet_counter.get(tok, 0)
    flag_quiet = quiet_n >= PERSISTENT_THRESH
    # OR
    flag_any = flag_status or flag_alpha or flag_quiet
    src = []
    if flag_status: src.append(f"status={st}")
    if flag_alpha: src.append("alpha_delisted")
    if flag_quiet: src.append(f"walletset_quiet(n={quiet_n})")
    rows.append({"token": tok, "n_ma_fires": ma_fires.get(tok, 0),
                 "flag_status": flag_status, "spot_status": st,
                 "flag_alpha_delisted": flag_alpha, "alpha_status": alpha_del,
                 "flag_walletset_quiet": flag_quiet, "walletset_quiet_n": quiet_n,
                 "flag_ANY": flag_any, "sources": " | ".join(src) if src else "—"})

# ── Fire-mass stats ──
n_total_fires = sum(r["n_ma_fires"] for r in rows)
n_flag_fires = sum(r["n_ma_fires"] for r in rows if r["flag_ANY"])
pct_flag = n_flag_fires / n_total_fires * 100 if n_total_fires else 0

print(f"\n[FIRE-MASS mang delist_flag]")
print(f"  n_total_fires: {n_total_fires}")
print(f"  n_flag_fires : {n_flag_fires}")
print(f"  % fire-mass mang flag: {pct_flag:.2f}%")

# Top flagged tokens by n_ma_fires
flagged = sorted([r for r in rows if r["flag_ANY"]], key=lambda x: -x["n_ma_fires"])
print(f"\n[FLAGGED TOP-10 by fire-count]:")
for r in flagged[:10]:
    print(f"  {r['token']:<14} fires={r['n_ma_fires']:>3}  ({r['sources']})")

# ── Write CSV ──
OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
with open(OUT_CSV, "w", encoding="utf-8", newline="") as f:
    f.write(f"# MA-D3 DELIST-FLAG column · KÝ 01/09 · zero-call bên trong (2 public API calls trước)\n")
    f.write(f"# Sources (OR):\n")
    f.write(f"#   (1) spot status ≠ TRADING (exchangeInfo · proxy cho deposit-closed L-52a + network-withdrawal L-triage-SOPH)\n")
    f.write(f"#   (2) alpha fullyDelisted (bapi L-48)\n")
    f.write(f"#   (3) walletset BROAD-QUIET persistent (VPS gom_h_daily.log · ≥{PERSISTENT_THRESH} emits)\n")
    f.write(f"# Note: sapi/capital/config/getall requires auth · dùng exchangeInfo status proxy hợp lý\n")
    f.write(f"#\n")
    f.write(f"# ─── L-64 mẫu-số ───\n")
    f.write(f"#   51 tokens (s6 map has_binance_spot=YES)\n")
    f.write(f"#   MA fires source: docs/reports/ma_shadow_backtest_20260828.csv md5 b7e8277c\n")
    f.write(f"#   exchangeInfo symbols fetched: {len(ei_status)}\n")
    f.write(f"#   alpha bapi entries: {len(alpha_delisted)} · fullyDelisted=True: {sum(1 for v in alpha_delisted.values() if v)}\n")
    f.write(f"#   walletset BROAD-QUIET tokens (any emit): {len(quiet_counter)}\n")
    f.write(f"#\n")
    f.write(f"# ─── FIRE-MASS STATS ───\n")
    f.write(f"#   n_total_fires: {n_total_fires}\n")
    f.write(f"#   n_flag_fires : {n_flag_fires}\n")
    f.write(f"#   % fire-mass mang delist_flag: {pct_flag:.2f}%\n")
    f.write(f"#\n")
    f.write(f"# ─── FLAGGED TOKENS (top by fire-count) ───\n")
    for r in flagged[:15]:
        f.write(f"#   {r['token']:<14} fires={r['n_ma_fires']:>3}  ({r['sources']})\n")
    f.write(f"#\n")
    f.write(f"# ─── DRAFT DQ-DELIST khuôn DQ-SERIAL (KHÔNG wire · chờ Tiên nhìn 27/09) ───\n")
    f.write(f"#   dq_delist:\n")
    f.write(f"#     members: [<auto-populated từ flag_ANY=True where fires ≥ threshold>]\n")
    f.write(f"#     source: \"OR 4 sources · draft SPOTCVD-cùng-đợt · chờ Tiên ký 27/09\"\n")
    f.write(f"#     check_before_emit: true (same pattern DQ-SERIAL BANANAS31)\n")
    f.write(f"# KHÔNG kết luận — bảng cho ANALYSIS 27/09\n")
    f.write(f"#\n")
    w = csv.DictWriter(f, fieldnames=["token","n_ma_fires","flag_status","spot_status",
                                       "flag_alpha_delisted","alpha_status",
                                       "flag_walletset_quiet","walletset_quiet_n",
                                       "flag_ANY","sources"])
    w.writeheader()
    for r in rows:
        w.writerow(r)

md5_out = hashlib.md5(OUT_CSV.read_bytes()).hexdigest()
n_lines = sum(1 for _ in open(OUT_CSV, encoding="utf-8"))
print(f"\n[OUT] {OUT_CSV.relative_to(ROOT)}")
print(f"[MD5] {md5_out}")
print(f"[WC ] {n_lines}")
