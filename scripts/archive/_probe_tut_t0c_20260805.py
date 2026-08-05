"""T0c: Read TUT rows from freshwatch_daily_2026-08.csv on VPS."""
import subprocess

VPS = "root@5.223.67.21"
EXPORT = "/root/Data_back_test/whale_data/data/export/freshwatch_daily_2026-08.csv"

def ssh(cmd, timeout=20):
    r = subprocess.run(
        ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=10", VPS, cmd],
        capture_output=True, text=True, timeout=timeout
    )
    return r.stdout.strip(), r.stderr.strip()

# Get header
print("[HEADER]")
out, _ = ssh(f"head -1 {EXPORT}")
print(out)

cols = out.split(",")
print(f"\nTotal columns: {len(cols)}")
for i, c in enumerate(cols):
    print(f"  [{i}] {c}")

# Get TUT rows
print("\n[TUT ROWS - ALL]")
out, _ = ssh(f"grep 'TUTUSDT' {EXPORT}")
rows = out.strip().split("\n")
print(f"Total TUT rows: {len(rows)}")
print()
for row in rows:
    fields = row.split(",")
    if len(fields) > 0:
        print(row)

print("\n[ANALYSIS]")
# Parse last 4 rows with pos_r
key_cols = {}
header_out, _ = ssh(f"head -1 {EXPORT}")
hdrs = header_out.split(",")
col_map = {h: i for i, h in enumerate(hdrs)}

print(f"\nKey column indices: pos_r={col_map.get('pos_r','?')}, gLSR={col_map.get('gLSR','?')}, f_avg={col_map.get('f_avg','?')}, fn={col_map.get('fn','?')}, oi_usd={col_map.get('oi_usd','?')}, px_avg={col_map.get('px_avg','?')}")

print("\n[PARSED TUT rows (date | px | fn | pos_r | gLSR | f_avg | OI)]")
ROLLING_PEAK = 5.083
THRESHOLD = ROLLING_PEAK * 0.75  # 25% drop = 3.81225

for row in rows:
    f = row.split(",")
    if len(f) < 10:
        continue
    date = f[0]
    px = f[col_map.get('px_avg', 2)] if 'px_avg' in col_map else f[2]
    fn_n = f[col_map.get('fn', 8)] if 'fn' in col_map else f[8]
    pos_r_v = f[col_map.get('pos_r', 10)] if 'pos_r' in col_map else f[10]
    glsr_v = f[col_map.get('gLSR', 12)] if 'gLSR' in col_map else f[12]
    f_avg_v = f[col_map.get('f_avg', 5)] if 'f_avg' in col_map else f[5]
    oi_v = f[col_map.get('oi_usd', 9)] if 'oi_usd' in col_map else f[9]
    try:
        pos_r_float = float(pos_r_v)
        flag = " *** BELOW 3.81 ***" if pos_r_float <= THRESHOLD else ""
        pct_from_peak = (ROLLING_PEAK - pos_r_float) / ROLLING_PEAK * 100
        print(f"  {date} | px={float(px):.5f} | fn={fn_n} | pos_r={pos_r_float:.4f}{flag} | gLSR={glsr_v} | f_avg={f_avg_v} | OI=${float(oi_v)/1e6:.3f}M | drop={pct_from_peak:.1f}%")
    except (ValueError, IndexError) as e:
        print(f"  {date} | PARSE ERR: {e} | raw: {row[:120]}")

print(f"\nPeak-14d = {ROLLING_PEAK}, threshold = {THRESHOLD:.4f}")
print(f"CỜ GHẾ-RỜI fires when pos_r ≤ {THRESHOLD:.4f} (25% drop from peak)")
