"""V3.5o directive item 4 · backfill fresh_digest artifacts 08-31→09-06 from log-blocks.
After backfill, grep DOS/BEAT/ONE/B for as-sent-only counter."""
import os, sys, re
from pathlib import Path

REPO = Path("/root/Data_back_test/whale_data") if os.name != "nt" else Path(r"D:/Data back test/whale_data")
LOG = REPO / "data/logs/digest_daily_vps.log"

txt = LOG.read_text(encoding="utf-8", errors="replace")
# Fresh_digest [SENT] event · followed by ARTIFACT-DUMP fresh_digest · body between [LOAD] and [SENT]
# Actually digest body composed and sent via tg. Log doesn't have body content · only markers.
# Alternative: reconstruct from nansen_snapshots via _fresh_delta then format
# BUT operator directive says "cite = as-sent artifact" — if artifact missing, cite VOID

# Check which fresh_digest [SENT] events happened for which target
sys.path.insert(0, str(REPO / "scripts"))
import re
sent_targets = set()
for m in re.finditer(r"\[LOAD\] snapshot=(\d{4}-\d{2}-\d{2})\.json[^\n]*\n\[[^\]]+\] \[SENT\] Fresh-Wallets", txt):
    sent_targets.add(m.group(1))
print(f"[SENT-TARGETS] fresh_digest as-sent-era: {sorted(sent_targets)}")

# ART existing
ART = REPO / "data/artifacts"
existing = sorted([p.name for p in ART.glob("tg_final_fresh_digest_2026-*.txt")])
print(f"[EXISTING artifacts]: {existing}")

# For missing dates in sent-era: log-block backfill possible? Body content NOT in digest_log
# We only have artifact-body for dates AFTER sender-dump wire (09-07 onwards)
missing_backfill = [t for t in sorted(sent_targets) if f"tg_final_fresh_digest_{t}.txt" not in existing]
print(f"\n[VERDICT]")
print(f"  SENT-era targets: {len(sent_targets)} dates ({sorted(sent_targets)[0]} → {sorted(sent_targets)[-1]})")
print(f"  Existing as-sent artifacts: {len(existing)}")
print(f"  Missing (no body content in log): {len(missing_backfill)}")
print(f"  {missing_backfill}")

print(f"\n[STRICT-COUNTER] cite=as-sent-artifact-only (per V3.5o directive):")
from collections import defaultdict
per_token = defaultdict(list)
for p in sorted(ART.glob("tg_final_fresh_digest_2026-*.txt")):
    date = p.name.split("_")[-1].replace(".txt","")
    body = p.read_text(encoding="utf-8", errors="replace")
    for tok in ["DOS","ONE","BEAT","B"]:
        # $TOKEN word boundary · exclude $BULLA matching $B
        pat = r"\$" + tok + r"\b"
        m = re.search(pat, body)
        if m:
            # extract line
            start = body.rfind("\n", 0, m.start()) + 1
            end = body.find("\n", m.end())
            line = body[start:end].strip()
            per_token[tok].append((date, p.name, line[:80]))

for tok in ["DOS","ONE","BEAT","B"]:
    hits = per_token[tok]
    print(f"  {tok}: {len(hits)}× as-sent")
    for date, fname, line in hits:
        print(f"    {date} · {fname} · {line}")
