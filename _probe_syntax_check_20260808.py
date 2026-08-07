#!/usr/bin/env python3
import ast, sys
with open("scripts/gom_scan.py", encoding="utf-8") as f:
    src = f.read()
ast.parse(src)
print("syntax OK")
