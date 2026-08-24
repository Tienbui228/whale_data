#!/usr/bin/env python3
"""[D1d CLOSE] 9-token operator paste 21/08 vs adapter — full 9 rows + APR + GUA + date mapping."""
from __future__ import annotations
import sys, io, json
from pathlib import Path
sys.path.insert(0, str(Path(r"D:/Data back test/whale_data")))
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from scripts.adapter_h1_nansen import read_adapter_daily, snapshot_md5, BOT_SNAPSHOTS

# Operator paste (Telegram 21/08):
OPERATOR_9 = [
    ("BEAT",  +2_430_000),
    ("CAP",   +608_000),
    ("TA",    +373_000),
    ("HANA",  +332_000),
    ("APR",   +221_000),
    ("CYS",   +209_000),
    ("GUA",    +34_000),
    ("STBL",  -323_000),
    ("TRIA",  -253_000),
]

# Bot cron 21/08 01:00 UTC → snapshot filename 2026-08-21.json
# Inside: exchange_balance_date = 2026-08-20T00:00:00Z (T-1 UTC)
# So adapter output rows date=08-20, ingest_date param="2026-08-21"

df = read_adapter_daily("2026-08-21")
md5 = snapshot_md5("2026-08-21")
print(f"══ [D1d CLOSE] Adapter output ingest_date=2026-08-21 (snapshot file 2026-08-21.json md5 {md5}) ══")

# Peek internal exchange_balance_date
snap_p = BOT_SNAPSHOTS / "2026-08-21.json"
snap = json.loads(snap_p.read_text(encoding="utf-8"))
sample_bal_dates = [r.get("exchange_balance_date") for r in snap["rows"] if r.get("exchange_balance_date")]
uniq_bal_dates = sorted(set(sample_bal_dates))
print(f"  Snapshot internal exchange_balance_date unique values: {uniq_bal_dates}")

print(f"\n  9-token operator paste 21/08 vs adapter (adapter cột date từ bảng dưới):")
print(f"  {'symbol':>8}  {'operator $':>13}  {'op dấu':>7}  {'adapter date':>13}  {'adapter delta_usd':>18}  {'adapter dấu':>12}  {'match?':>8}")

n_match_sign = 0
n_check = 0
for sym, op_usd in OPERATOR_9:
    row = df[df["symbol"] == sym]
    n_check += 1
    if row.empty:
        print(f"  {sym:>8}  {op_usd:>+13,d}  {('LÊN' if op_usd>0 else 'RỜI'):>7}  {'<not found>':>13}  {'<not found>':>18}  {'-':>12}  MISS")
        continue
    r = row.iloc[0]
    ad_date = r["date"]
    ad_du = r["delta_usd"] if r["delta_usd"] == r["delta_usd"] else None
    op_sign = "LÊN(+)" if op_usd > 0 else "RỜI(−)"
    ad_sign = "LÊN(+)" if ad_du and ad_du > 0 else "RỜI(−)" if ad_du and ad_du < 0 else "?"
    sign_match = (op_sign[:3] == ad_sign[:3]) if ad_du is not None else False
    if sign_match: n_match_sign += 1
    tag = "✓ ok" if sign_match else "✗ LỆCH"
    ad_du_str = f"{ad_du:+,.0f}" if ad_du else "N/A"
    print(f"  {sym:>8}  {op_usd:>+13,d}  {op_sign:>7}  {ad_date:>13}  {ad_du_str:>18}  {ad_sign:>12}  {tag:>8}")

print(f"\n[D1d verdict] 9/9 match dấu: {n_match_sign}/{n_check}")
if n_match_sign == 9:
    print(f"  → D1d PASS 9/9, adapter DẤU khớp operator Telegram 21/08 (sanity L-28 verified)")
else:
    print(f"  → D1d LỆCH DẤU {n_check - n_match_sign} token — DỪNG per operator L-28 rule")

# (b) Date mapping quy ước
print(f"\n══ [D1d (b) Mapping quy ước date] ══")
print(f"  Bot cron 21/08 01:00 UTC → filename snapshots/2026-08-21.json")
print(f"  Inside JSON: exchange_balance_date = '2026-08-20T00:00:00Z' (T-1 UTC balance snapshot)")
print(f"  Adapter output rows date field = exchange_balance_date (T-1) = '2026-08-20'")
print(f"  → Quy ước chốt: date field trong adapter output = balance date THẬT (T-1 UTC)")
print(f"                   ingest_date param = snapshot filename date = T (ingest ngày kế)")
print(f"                   Bot Telegram 21/08 = báo delta cho day 08-20 (compared 08-19)")
