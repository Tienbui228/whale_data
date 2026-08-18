"""_task_gua_b0_backup_20260818.py — B0 backup CASE_GUA.xlsx"""
import sys, io, shutil
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path

ROOT    = Path(r"D:\Data back test\whale_data")
src     = ROOT / "docs" / "case_files" / "CASE_GUA.xlsx"
dst     = ROOT / "scratch" / "CASE_GUA_bak_pre_refresh_20260818.xlsx"

assert src.exists(), f"SOURCE MISSING: {src}"
shutil.copy2(src, dst)
assert dst.exists() and dst.stat().st_size == src.stat().st_size

print(f"BACKUP OK")
print(f"  src:  {src}  ({src.stat().st_size} B)")
print(f"  dst:  {dst}  ({dst.stat().st_size} B)")
