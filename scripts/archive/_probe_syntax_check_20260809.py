"""Syntax check for gom_scan.py + run_gom_daily.py after 4-bug fix."""
import py_compile, sys

files = [
    r"D:\Data back test\whale_data\scripts\gom_scan.py",
    r"D:\Data back test\whale_data\scripts\run_gom_daily.py",
]

ok = True
for f in files:
    try:
        py_compile.compile(f, doraise=True)
        print(f"OK  {f}")
    except py_compile.PyCompileError as e:
        print(f"ERR {f}: {e}")
        ok = False

sys.exit(0 if ok else 1)
