"""[2] Registry div_avg3 distribution + [4] GUA d_acc_2d verification.

[2] Bucket 64 registry tokens từ dry-run đã chụp (no new fetch).
[4] Đọc VPS CSV lsr_acc_r / lsr_pos_r cho GUAUSDT ngày 08-08 và 08-10
    → tính d_pos_2d, d_acc_2d → xác định DENOM-ASSIST hay NUM sạch.

data-source:
  [2] = captured stdout từ Q1 dry-run (hardcoded, no VPS call)
  [4] = VPS /root/.../data/export/freshwatch_daily_2026-08.csv (read-only)
machine: local (parse) + local→VPS via SSH ([4])
date-range: 2026-08-08, 2026-08-10
code-commit: see git log
"""
import sys
import io
import subprocess
import json

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

VPS = "root@5.223.67.21"
VPS_ROOT = "/root/Data_back_test/whale_data"

# ── [2] Registry div_avg3 distribution ────────────────────────────────────────
# Data từ Q1 dry-run output (EVAL=2026-08-10, 64 tokens, không fetch lại)
REGISTRY_DIV_AVG3 = {
    "1000000BOBUSDT": 0.370, "4USDT": 0.724,    "ACUUSDT": 0.456,
    "AGTUSDT": 0.530,        "AIAUSDT": 0.491,  "AINUSDT": 0.593,
    "AIOTUSDT": 0.673,       "AIOUSDT": 0.782,  "ARIAUSDT": 0.428,
    "BASUSDT": 0.909,        "BILLUSDT": 0.599, "BLUAIUSDT": 1.224,
    "BTRUSDT": 0.314,        "CLOUSDT": 0.348,  "COAIUSDT": 0.244,
    "COLLECTUSDT": 0.495,    "COOKIEUSDT": 0.765, "CROSSUSDT": 0.432,
    "CUSDT": 0.666,          "ESPORTSUSDT": 0.513, "FHEUSDT": 0.460,
    "FIGHTUSDT": 0.354,      "FOLKSUSDT": 0.398, "FUSDT": 0.487,
    "GUAUSDT": 0.386,        "GWEIUSDT": 0.721,  "HAEDALUSDT": 0.456,
    "HANAUSDT": 0.640,       "INUSDT": 0.414,   "INXUSDT": 0.344,
    "IRYSUSDT": 0.543,       "KGENUSDT": 0.575, "KOMAUSDT": 0.854,
    "LABUSDT": 0.416,        "LIGHTUSDT": 0.328, "LYNUSDT": 0.184,
    "MERLUSDT": 0.490,       "MYXUSDT": 0.382,  "NEWTUSDT": 0.426,
    "ORDERUSDT": 0.460,      "PLAYUSDT": 0.461, "POWERUSDT": 0.395,
    "PTBUSDT": 0.735,        "PUMPBTCUSDT": 0.252, "RAVEUSDT": 0.469,
    "RIVERUSDT": 0.397,      "SHELLUSDT": 0.305, "SIRENUSDT": 0.339,
    "SOPHUSDT": 0.335,       "SPACEUSDT": 0.438, "SQDUSDT": 0.443,
    "STARUSDT": 0.367,       "STBLUSDT": 0.244, "TACUSDT": 0.282,
    "TAIKOUSDT": 0.346,      "TAKEUSDT": 1.432, "TOWNSUSDT": 0.644,
    "TRADOORUSDT": 0.438,    "TRIAUSDT": 0.317, "TURTLEUSDT": 0.557,
    "XANUSDT": 0.669,        "XNYUSDT": 0.669,  "ZKCUSDT": 0.564,
    "WTMLUSDT": 0.335,  # 我踏马来了USDT
}
assert len(REGISTRY_DIV_AVG3) == 64, f"Expected 64, got {len(REGISTRY_DIV_AVG3)}"

b_le085  = {k: v for k, v in REGISTRY_DIV_AVG3.items() if v <= 0.85}
b_085_10 = {k: v for k, v in REGISTRY_DIV_AVG3.items() if 0.85 < v <= 1.0}
b_gt10   = {k: v for k, v in REGISTRY_DIV_AVG3.items() if v > 1.0}

print("=" * 60)
print("[2] REGISTRY div_avg3 DISTRIBUTION (EVAL=2026-08-10, 64 tokens)")
print("=" * 60)
print(f"\n  Bucket     count   pct    tokens")
print(f"  {'='*56}")
print(f"  ≤0.85      {len(b_le085):5d}   {len(b_le085)/64*100:5.1f}%  (core HEDGE-FARM zone)")
print(f"  0.85–1.0   {len(b_085_10):5d}   {len(b_085_10)/64*100:5.1f}%  borderline")
print(f"  >1.0       {len(b_gt10):5d}   {len(b_gt10)/64*100:5.1f}%  vượt EXIT threshold")

if b_085_10:
    print(f"\n  Borderline (0.85–1.0):")
    for sym, v in sorted(b_085_10.items(), key=lambda x: x[1]):
        print(f"    {sym:<20} div_avg3={v:.3f}")

if b_gt10:
    print(f"\n  Vượt EXIT (>1.0):")
    for sym, v in sorted(b_gt10.items(), key=lambda x: x[1]):
        print(f"    {sym:<20} div_avg3={v:.3f}")

pct_clean = len(b_le085) / 64 * 100
if pct_clean >= 90:
    verdict2 = "LANH — đa số deep HEDGE-FARM, tail nhỏ. Tiến backfill."
elif pct_clean >= 75:
    verdict2 = "TRUNG BINH — cân nhắc siết H1 trước backfill."
else:
    verdict2 = "LONG — H1 cần siết TRUOC KHI daily ghi sổ."

print(f"\n  VERDICT [2]: {verdict2}")

# ── [4] GUA d_acc_2d — đọc VPS CSV ────────────────────────────────────────────
print("\n" + "=" * 60)
print("[4] GUA d_acc_2d VERIFICATION (GUAUSDT 2026-08-08 vs 2026-08-10)")
print("=" * 60)

GUA_SYM = "GUAUSDT"
DATES_NEEDED = ["2026-08-08", "2026-08-10"]
CSV_PATH = f"{VPS_ROOT}/data/export/freshwatch_daily_2026-08.csv"

script = f"""
import csv, json
rows = {{}}
with open('{CSV_PATH}', encoding='utf-8', errors='replace') as f:
    rdr = csv.DictReader(f)
    for r in rdr:
        if r.get('symbol') == '{GUA_SYM}' and r.get('date') in {json.dumps(DATES_NEEDED)}:
            rows[r['date']] = {{
                'lsr_pos_r': r.get('lsr_pos_r', ''),
                'lsr_acc_r': r.get('lsr_acc_r', ''),
                'lsr_global_r': r.get('lsr_global_r', ''),
                'oi_usd': r.get('oi_usd', ''),
                'px_avg': r.get('px_avg', ''),
                'low_conf': r.get('low_conf', ''),
            }}
print(json.dumps(rows))
"""
r = subprocess.run(["ssh", VPS, f"python3 -c \"{script}\""],
                   capture_output=True, text=True, encoding="utf-8", errors="replace")
if r.returncode != 0:
    print(f"SSH ERROR: {r.stderr[:300]}")
    sys.exit(1)

try:
    data = json.loads(r.stdout.strip())
except Exception as e:
    print(f"Parse error: {e}\nraw: {r.stdout[:500]}")
    sys.exit(1)

print(f"\n  CSV rows found: {sorted(data.keys())}")
for d in DATES_NEEDED:
    if d not in data:
        print(f"  MISSING: {d}")
    else:
        row = data[d]
        print(f"  {d}: lsr_pos_r={row['lsr_pos_r']!r}  lsr_acc_r={row['lsr_acc_r']!r}  "
              f"lsr_global_r={row['lsr_global_r']!r}  low_conf={row['low_conf']!r}")

if "2026-08-08" not in data or "2026-08-10" not in data:
    print("\n  ERROR: Missing dates — cannot compute d_acc_2d")
    sys.exit(1)

try:
    pos_08   = float(data["2026-08-08"]["lsr_pos_r"])
    acc_08   = float(data["2026-08-08"]["lsr_acc_r"])
    pos_10   = float(data["2026-08-10"]["lsr_pos_r"])
    acc_10   = float(data["2026-08-10"]["lsr_acc_r"])
    oi_08    = float(data["2026-08-08"].get("oi_usd") or "nan")
    oi_10    = float(data["2026-08-10"].get("oi_usd") or "nan")
    px_08    = float(data["2026-08-08"].get("px_avg") or "nan")
    px_10    = float(data["2026-08-10"].get("px_avg") or "nan")
except (ValueError, KeyError) as e:
    print(f"\n  ERROR parsing floats: {e}")
    sys.exit(1)

d_pos_2d = pos_10 / pos_08 - 1
d_acc_2d = acc_10 / acc_08 - 1
div_10   = pos_10 / acc_10
div_08   = pos_08 / acc_08

# oi_token = oi_usd / px_avg
import math
oi_tok_08 = oi_08 / px_08 if (not math.isnan(oi_08) and not math.isnan(px_08) and px_08 != 0) else float("nan")
oi_tok_10 = oi_10 / px_10 if (not math.isnan(oi_10) and not math.isnan(px_10) and px_10 != 0) else float("nan")
d_oitok_2d = (oi_tok_10 / oi_tok_08 - 1) if (not math.isnan(oi_tok_08) and oi_tok_08 != 0) else float("nan")

denom_assist = abs(d_acc_2d) > abs(d_pos_2d)

print(f"\n=== GUA 2026-08-10 METRICS ===")
print(f"  pos_r(08-08)  = {pos_08:.6f}")
print(f"  pos_r(08-10)  = {pos_10:.6f}")
print(f"  acc_r(08-08)  = {acc_08:.6f}")
print(f"  acc_r(08-10)  = {acc_10:.6f}")
print(f"")
print(f"  d_pos_2d = pos_10/pos_08 - 1 = {pos_10:.6f}/{pos_08:.6f} - 1 = {d_pos_2d:+.6f}")
print(f"  d_acc_2d = acc_10/acc_08 - 1 = {acc_10:.6f}/{acc_08:.6f} - 1 = {d_acc_2d:+.6f}")
print(f"  |d_acc_2d| = {abs(d_acc_2d):.6f}  vs  d_pos_2d = {d_pos_2d:.6f}")
print(f"  d_oitok_2d = {d_oitok_2d:+.6f}  (E3: ≤0 → {d_oitok_2d <= 0})")
print(f"")
print(f"  div_raw(08-08) = {div_08:.6f}")
print(f"  div_raw(08-10) = {div_10:.6f}")
print(f"")

print(f"=== DENOM-ASSIST CHECK ===")
print(f"  |d_acc_2d| ({abs(d_acc_2d):.6f}) {'>' if denom_assist else '<='} d_pos_2d ({d_pos_2d:.6f})")
if denom_assist:
    print(f"  → DENOM-ASSIST TAG ÁP DỤNG")
    print(f"    GUA 08-10 = DENOM-ASSIST case: acc_r sập mạnh hơn pos_r tăng")
    print(f"    Không phải positive #2 thuần NUM — là biên case (d_pos>+0.15 nhưng mẫu kéo)")
    print(f"    Cần operator xét: positive #2 hay negative-by-tag [DENOM-ASSIST]?")
else:
    print(f"  → DENOM-ASSIST KHÔNG áp dụng")
    print(f"    GUA 08-10 = NUM sạch: pos tăng nhiều hơn acc giảm")
    print(f"    E3✓ (d_oi≤0) + không DENOM → [NUM-DRIVEN] thuần")
    print(f"    positive #2 đứng.")

# ── Summary ────────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("SUMMARY CHUA-BACKFILL:")
print(f"  [2] Registry LANH={pct_clean:.1f}% ≤0.85, tail={len(b_gt10)} con >1.0")
print(f"  [4] GUA DENOM-ASSIST={'YES' if denom_assist else 'NO'}")
print(f"\nDUNG — doi operator verdict truoc backfill.")
