"""AP3 · liệt đích danh token bị cap cắt khỏi thân 09-17..09-20.

Cap cắt = tokens dropped from CHƯA XẾP LOÀI overflow tail (per _v1_3_apply_3tier_cap).
So sánh pre-cap body vs post-cap body · phân tích dòng tail "(+n nữa: X·Y·Z·đủ ở audit)".
"""
import sys, os, re
from pathlib import Path
sys.path.insert(0, "/root/Data_back_test/whale_data/scripts")

os.environ["DIGEST_V1_3"] = "1"
os.environ["DIGEST_U0_BELL_BLOCK"] = "1"
os.environ["DIGEST_B_TIER"] = "1"

import digest_summary_v2 as dsv

for tgt in ["2026-09-17", "2026-09-18", "2026-09-19", "2026-09-20"]:
    # Get post-cap body (normal)
    body_post = dsv.build_v2_digest(tgt)

    # Find tail note dropped tokens: (+n nữa: X·Y·Z · đủ ở audit)
    dropped = []
    for m in re.finditer(r"\(\+\d+\s+nữa:\s+([^)]+?)\s*·\s*đủ\s+ở\s+audit\)", body_post):
        names_str = m.group(1).strip()
        # split by · but be careful with tokens like `⏸TOK`
        names = [n.strip() for n in names_str.split("·")]
        dropped.extend(names)

    # Alt · Look for "(+N nữa:" without audit suffix (older format)
    for m in re.finditer(r"\(\+\d+\s+nữa:\s+([^)]+)\)", body_post):
        names_str = m.group(1).strip()
        # skip if already handled with audit suffix
        if "đủ ở audit" in names_str: continue
        names = [n.strip() for n in names_str.split("·")]
        dropped.extend(names)

    dropped_unique = list(dict.fromkeys(dropped))
    print(f"{tgt}: cap cắt {len(dropped_unique)} tokens · {' · '.join(dropped_unique)}")
