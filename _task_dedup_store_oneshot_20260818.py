#!/usr/bin/env python3
"""
ONE-SHOT dedup store (oi_hist_1h + taker_ratio_1h + klines_1h).

TRÌNH TỰ:
  1. Backup mọi partition → .bak + ghi MD5 vào scratch/dedup_store_manifest_20260818.tsv
  2. Đọc → drop_duplicates(subset=DEDUP_KEY, keep="last") ưu tiên fetched_at_ms mới
  3. Ghi lại parquet (compression zstd giữ nguyên)
  4. In bảng before/after: partition × field → n_rows trước/sau
  5. klines_1h: KIỂM trước; partition có dup thì dedup, mới thì skip

CẤM cron. Chạy MỘT LẦN sau khi vá _sync_append (source đã chặn).

Requires: whale_collector/storage/dedup.py::DEDUP_KEY tồn tại + writer đã vá.
Usage on VPS:
  cd /root/Data_back_test/whale_data && python3 _task_dedup_store_oneshot_20260818.py
"""
import sys, io, hashlib, shutil, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

sys.path.insert(0, str(Path(__file__).parent))
from whale_collector.storage.dedup import DEDUP_KEY

RAW = Path("/root/Data_back_test/whale_data/data/raw")
SCRATCH = Path("/root/Data_back_test/whale_data/scratch")
SCRATCH.mkdir(exist_ok=True, parents=True)
MANIFEST = SCRATCH / "dedup_store_manifest_20260818.tsv"

METRICS = ["oi_hist_1h", "taker_ratio_1h", "klines_1h"]

DIV = "=" * 78

def md5_file(p: Path) -> str:
    h = hashlib.md5()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

def _dedup_sort(df: pd.DataFrame) -> pd.DataFrame:
    if "fetched_at_ms" in df.columns:
        df = df.sort_values("fetched_at_ms")
    return df.drop_duplicates(subset=DEDUP_KEY, keep="last")

# ── Manifest header ───────────────────────────────────────────────────────────
with open(MANIFEST, "w", encoding="utf-8") as f:
    f.write("metric\tpartition\tstage\tpath\tmd5\tsize_bytes\tn_rows\n")

print(f"{DIV}\nONE-SHOT DEDUP STORE  —  {time.strftime('%Y-%m-%d %H:%M:%S')}\n{DIV}")
print(f"DEDUP_KEY = {DEDUP_KEY}")
print(f"metrics   = {METRICS}")
print(f"backup    = *.bak sibling; MANIFEST = {MANIFEST}")
print()

summary = []   # (metric, n_partitions, n_dedup, n_skip, rows_before_total, rows_after_total)

for metric in METRICS:
    metric_dir = RAW / metric
    if not metric_dir.exists():
        print(f"[{metric}] DIR MISSING — skip")
        continue

    partitions = sorted(metric_dir.glob("date=*/part-0.parquet"))
    print(f"\n{DIV}\n[{metric}]  {len(partitions)} partitions\n{DIV}")

    metric_rows_before = 0
    metric_rows_after  = 0
    n_dedup = n_skip = 0

    print(f"  {'partition':>16}  {'rows_before':>11}  {'rows_after':>10}  {'delta':>7}  {'md5_before':>10}  status")

    for p in partitions:
        d_name = p.parent.name
        try:
            df = pd.read_parquet(p)
        except Exception as e:
            print(f"  {d_name:>16}  ERROR read: {e}")
            continue

        n_before = len(df)
        df_dd = _dedup_sort(df)
        n_after = len(df_dd)
        metric_rows_before += n_before
        metric_rows_after  += n_after

        if n_after == n_before:
            # Clean — no dedup needed
            n_skip += 1
            md5_b = md5_file(p)
            with open(MANIFEST, "a", encoding="utf-8") as f:
                f.write(f"{metric}\t{d_name}\tSKIP\t{p}\t{md5_b}\t{p.stat().st_size}\t{n_before}\n")
            print(f"  {d_name:>16}  {n_before:>11}  {n_after:>10}  {0:>7}  {md5_b[:8]:>10}  SKIP (clean)")
            continue

        # Backup .bak + MD5
        bak = p.with_suffix(".parquet.bak")
        shutil.copy2(p, bak)
        md5_b = md5_file(bak)
        size_b = bak.stat().st_size
        with open(MANIFEST, "a", encoding="utf-8") as f:
            f.write(f"{metric}\t{d_name}\tBEFORE\t{bak}\t{md5_b}\t{size_b}\t{n_before}\n")

        # Write dedup'd parquet (zstd level 3 = collector default)
        table = pa.Table.from_pandas(df_dd, preserve_index=False)
        pq.write_table(table, p, compression="zstd", compression_level=3)
        md5_a = md5_file(p)
        size_a = p.stat().st_size
        with open(MANIFEST, "a", encoding="utf-8") as f:
            f.write(f"{metric}\t{d_name}\tAFTER\t{p}\t{md5_a}\t{size_a}\t{n_after}\n")

        n_dedup += 1
        delta = n_after - n_before
        ratio = n_before / n_after if n_after else 0
        print(f"  {d_name:>16}  {n_before:>11}  {n_after:>10}  {delta:>+7}  {md5_b[:8]:>10}  DEDUP ratio={ratio:.2f}×")

    summary.append((metric, len(partitions), n_dedup, n_skip, metric_rows_before, metric_rows_after))

# ── Summary ───────────────────────────────────────────────────────────────────
print(f"\n{DIV}\nSUMMARY\n{DIV}")
print(f"  {'metric':>16}  {'partitions':>10}  {'dedup':>6}  {'skip':>5}  {'rows_before':>13}  {'rows_after':>12}  {'reduction':>10}")
for m, np_, nd, ns, rb, ra in summary:
    red = (rb - ra) / rb * 100 if rb else 0
    print(f"  {m:>16}  {np_:>10}  {nd:>6}  {ns:>5}  {rb:>13,}  {ra:>12,}  {red:>9.1f}%")

print(f"\nManifest (backup .bak paths + MD5 before/after per changed partition):")
print(f"  {MANIFEST}")
print(f"\nDUNG. One-shot dedup complete. Reverse: cp .bak → .parquet cho từng partition.")
