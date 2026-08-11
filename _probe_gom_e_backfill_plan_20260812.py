"""[4] GOM-E T1-STORE backfill PLAN probe — read-only, DUNG sau paste.

Mục đích: xác định kế hoạch backfill trước khi ghi bất cứ thứ gì vào store.
Output: bảng (date · symbol · raw_fetchable · canonical_src · canonical_avail · action)

Kỷ luật (operator 12/08):
  pos_raw_1h / acc_raw_1h / oi_raw_1h: FETCH Binance startTime+endTime epoch ms
  pos_canonical / acc_canonical / oi_canonical: DOC từ canonical pipeline ĐA-GHI
  CHUA có số canonical → cột để TRỐNG (không tính lại, không bịa)
  TUYỆT ĐỐI KHÔNG tính lại canonical cho ngày cũ (= viết lại DAILY = P0 + L-41)

PHAM VI KHE HOACH:
  A. PRODUCTION WARMUP: 2026-08-10 và 2026-08-11
     Lý do: T2 poll ngày 2026-08-12 cần store[2026-08-10]; T2 poll ngày 2026-08-13 cần store[2026-08-11]
  B. ON CALIB CONTEXT (optional): 2026-07-08 → 2026-07-25 cho ONUSDT
     Lý do: kiểm tra T2 behavior trong window cover. Chỉ điền nếu canonical có.

data-source: VPS /root/Data_back_test/whale_data/data/export/ (canonical read)
             Binance /futures/data (raw fetch — chỉ kiểm tra feasibility, chưa fetch)
machine: local → VPS via SSH (read-only)
date-range: 2026-07-08 → 2026-08-11
code-commit: see git log
"""
import sys
import io
import json
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

VPS = "root@5.223.67.21"
VPS_ROOT = "/root/Data_back_test/whale_data"
LOCAL_ROOT = Path(__file__).resolve().parent

STATE_PATH_VPS = f"{VPS_ROOT}/data/gom_e_state.json"
EXPORT_PATH_VPS = f"{VPS_ROOT}/data/export"

# Đây là ngày chạy probe (forming day)
PROBE_DATE = datetime.now(timezone.utc).date()

# ── PHAM VI ────────────────────────────────────────────────────────────────────
# A. Production warmup: 2 ngày trước T1 first run
WARMUP_DATES = [
    (PROBE_DATE - timedelta(days=2)).strftime("%Y-%m-%d"),  # 2026-08-10
    (PROBE_DATE - timedelta(days=1)).strftime("%Y-%m-%d"),  # 2026-08-11
]

# B. ON calib context
ON_CALIB_START = "2026-07-08"
ON_CALIB_END   = "2026-07-25"
ON_SYM         = "ONUSDT"

print("=" * 70)
print(f"GOM-E T1-STORE BACKFILL PLAN — {PROBE_DATE} (read-only, CHUA GHI)")
print("=" * 70)
print(f"\nProbe date (forming=D_run): {PROBE_DATE}")
print(f"Warmup A: {WARMUP_DATES[0]}, {WARMUP_DATES[1]}")
print(f"ON calib B: {ON_CALIB_START} → {ON_CALIB_END} (ONUSDT)")

# ── STEP 1: Current candidate symbols from T1 state (if exists) ───────────────
print("\n=== STEP 1: Current candidate symbols ===")
r = subprocess.run(
    ["ssh", VPS, f"cat {STATE_PATH_VPS} 2>/dev/null || echo MISSING"],
    capture_output=True, text=True, encoding="utf-8", errors="replace"
)
t1_state = {}
if r.returncode == 0 and r.stdout.strip() != "MISSING":
    try:
        t1_state = json.loads(r.stdout)
        candidates = [sym for sym, st in t1_state.items()
                      if st.get("in_registry") or
                      (st.get("exit_date") and
                       (datetime.strptime(PROBE_DATE.strftime("%Y-%m-%d"), "%Y-%m-%d") -
                        datetime.strptime(st["exit_date"], "%Y-%m-%d")).days <= 3)]
        print(f"  gom_e_state.json found: {len(t1_state)} symbols, {len(candidates)} candidates")
        print(f"  Candidates: {sorted(candidates)}")
    except Exception as e:
        print(f"  Parse error: {e}"); candidates = []
else:
    print("  gom_e_state.json MISSING (T1 chua chay production)")
    candidates = []

# Always include ONUSDT for calib context B
symbols_warmup = list(set(candidates + [ON_SYM]))
print(f"  Final symbols for plan: {sorted(symbols_warmup)}")

# ── STEP 2: Check canonical availability on VPS for each date ─────────────────
print("\n=== STEP 2: Canonical availability check (VPS export CSV) ===")

def check_canonical_vps(date_str: str, syms: list[str]) -> dict[str, dict]:
    """SSH to VPS, grep date+symbols from freshwatch_daily CSV. Returns {sym: {avail, pos_r, acc_r, oi_usd, px_avg}}."""
    ym = date_str[:7].replace("-", "-")  # "2026-07"
    csv_path = f"{EXPORT_PATH_VPS}/freshwatch_daily_{ym}.csv"

    # Check if file exists
    r_exists = subprocess.run(
        ["ssh", VPS, f"test -f {csv_path} && echo EXISTS || echo MISSING"],
        capture_output=True, text=True, encoding="utf-8", errors="replace"
    )
    if "MISSING" in r_exists.stdout:
        return {sym: {"avail": False, "reason": f"{csv_path} not found"} for sym in syms}

    # Extract rows matching date + symbols
    syms_grep = "|".join(syms)
    # CSV format: first col=date, second col=symbol
    script = (
        f"python3 -c \""
        f"import csv,sys; "
        f"rows={{}}; "
        f"f=open('{csv_path}',encoding='utf-8',errors='replace'); "
        f"rdr=csv.DictReader(f); "
        f"syms=set({syms!r}); "
        f"target='{date_str}'; "
        f"[rows.update({{r['symbol']: {{'pos_r':r.get('lsr_pos_r',''),'acc_r':r.get('lsr_acc_r',''),'oi_usd':r.get('oi_usd',''),'px_avg':r.get('px_avg','')}}}}) for r in rdr if r.get('date')==target and r.get('symbol') in syms]; "
        f"import json; print(json.dumps(rows))\""
    )
    r2 = subprocess.run(["ssh", VPS, script], capture_output=True, text=True, encoding="utf-8", errors="replace")
    try:
        data = json.loads(r2.stdout.strip())
    except Exception:
        data = {}

    result = {}
    for sym in syms:
        if sym in data:
            row = data[sym]
            pos_r = row.get("pos_r", "")
            has_data = bool(pos_r and pos_r not in ("", "nan", "None"))
            result[sym] = {"avail": has_data, "pos_r": pos_r,
                           "oi_usd": row.get("oi_usd", ""), "px_avg": row.get("px_avg", "")}
        else:
            result[sym] = {"avail": False, "reason": "no row for this date"}
    return result

# ── SECTION A: Production warmup dates ────────────────────────────────────────
print("\n-- Section A: Production warmup (2026-08-10, 2026-08-11) --")
print(f"{'date':<12} {'symbol':<12} {'canonical_avail':<16} {'pos_r':<10} {'raw_fetch':<12} {'action'}")
print("-" * 80)

for d in WARMUP_DATES:
    canon = check_canonical_vps(d, symbols_warmup)
    for sym in sorted(symbols_warmup):
        c = canon.get(sym, {"avail": False})
        can_avail = "YES" if c.get("avail") else "NO"
        pos_r_val = c.get("pos_r", "")[:8] if c.get("avail") else "-"
        raw_fetch = "FETCH(API)"
        if c.get("avail"):
            action = "fetch_raw + read_canonical"
        else:
            action = "fetch_raw + canonical=EMPTY (gap_pct=NULL)"
        print(f"  {d:<12} {sym:<12} {can_avail:<16} {pos_r_val:<10} {raw_fetch:<12} {action}")

# ── SECTION B: ON calib context dates ─────────────────────────────────────────
print("\n-- Section B: ON calib context (2026-07-08 → 2026-07-25, ONUSDT only) --")
print(f"{'date':<12} {'canonical_avail':<16} {'pos_r':<10} {'raw_fetch':<12} {'action'}")
print("-" * 70)

d_cur = datetime.strptime(ON_CALIB_START, "%Y-%m-%d")
d_end = datetime.strptime(ON_CALIB_END, "%Y-%m-%d")
while d_cur <= d_end:
    d_str = d_cur.strftime("%Y-%m-%d")
    canon = check_canonical_vps(d_str, [ON_SYM])
    c = canon.get(ON_SYM, {"avail": False})
    can_avail = "YES" if c.get("avail") else "NO"
    pos_r_val = c.get("pos_r", "")[:8] if c.get("avail") else "-"
    raw_fetch = "FETCH(API)"
    if c.get("avail"):
        action = "fetch_raw + read_canonical"
    else:
        action = "fetch_raw + canonical=EMPTY (gap_pct=NULL)"
    print(f"  {d_str:<12} {can_avail:<16} {pos_r_val:<10} {raw_fetch:<12} {action}")
    d_cur += timedelta(days=1)

# ── Summary ────────────────────────────────────────────────────────────────────
print("\n" + "=" * 70)
print("SUMMARY — KE HOACH (CHUA GHI, cho đến khi operator duyet):")
print("""
  raw fields (pos_raw_1h, acc_raw_1h, oi_raw_1h):
    FETCH Binance startTime+endTime epoch ms, backfill_src="fetch"
    Feasibility: da xac nhan probe B1b (PART2/PART3 match check)

  canonical fields (pos_canonical, acc_canonical, oi_canonical):
    Doc từ freshwatch_daily_YYYY-MM.csv tren VPS (canonical pipeline da-ghi)
    Ngay co data → dien; ngay CHUA co → de TRONG + gap_pct=NULL
    TUYET ĐOI KHONG tinh lai canonical = vi pham L-41/P0

  PHAM VI BACKFILL đe xuat:
    A. Warmup: 2 ngay (2026-08-10, 2026-08-11) × all candidates + ON
    B. ON calib (optional): 2026-07-08→07-25 × ONUSDT (neu canonical co)

  SYMBOLS: xem Step 1 output tren (candidates từ gom_e_state.json)
""")
print("DUNG — doi operator duyet truoc khi tao probe ghi store.")
print("=" * 70)
