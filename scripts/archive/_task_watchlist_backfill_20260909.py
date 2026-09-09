"""Watchlist 09-08 artifact backfill từ log-block · provenance=log-block · posthoc còn sống."""
import os, sys, hashlib
from pathlib import Path
from datetime import datetime, timezone
import re

REPO = Path("/root/Data_back_test/whale_data") if os.name != "nt" else Path(r"D:/Data back test/whale_data")
LOG = REPO / "data/export/watchlist_cron.log"
ART = REPO / "data/artifacts"
TARGET = "2026-09-08"

# Find watchlist tg_out block for target · scan log
if not LOG.exists():
    print(f"[N/A-ERROR] {LOG} not found"); sys.exit(1)

txt = LOG.read_text(encoding="utf-8", errors="replace")
# Split by target_date markers · block-scoped (L-80 fix)
sections = re.split(r"(?=^INFO:\s+target_date=)", txt, flags=re.MULTILINE)
target_block = None
for s in sections:
    m = re.match(r"^INFO:\s+target_date=(\d{4}-\d{2}-\d{2})", s)
    if m and m.group(1) == TARGET:
        target_block = s

if not target_block:
    print(f"[N/A-ERROR] no target={TARGET} block found in watchlist_cron.log"); sys.exit(1)

# Watchlist body = the tg_out that was sent (part of the block)
# The [SENT] watchlist line is at the end · body precedes it
# Extract everything up to [SENT] watchlist marker
end_marker = "[SENT] watchlist"
end_pos = target_block.find(end_marker)
if end_pos > 0:
    body = target_block[:end_pos].rstrip()
else:
    body = target_block

# Load artifact_dump to backfill (uses V1.4 anchor)
sys.path.insert(0, str(REPO / "scripts"))
from lib.artifact_dump import dump_as_sent

# Use provenance=log-block (not as-sent)
txt_p = ART / f"tg_final_watchlist_{TARGET}.txt"
jsonl_p = ART / f"tg_final_watchlist_{TARGET}.jsonl"

# Override provenance header manually · use dump_as_sent then rewrite header
try:
    ok, msg = dump_as_sent("watchlist", TARGET, body, channel="log-block-backfill")
    print(f"[BACKFILL watchlist] {ok} · {msg}")
    # Verify
    if txt_p.exists():
        # Rewrite provenance
        content = txt_p.read_text(encoding="utf-8")
        content = content.replace("[PROVENANCE=as-sent]", "[PROVENANCE=log-block-backfill]", 1)
        txt_p.write_text(content, encoding="utf-8")
        print(f"[PROVENANCE-REWRITE] {txt_p.name} → log-block-backfill")
        print(f"[VERIFY] txt={txt_p.stat().st_size}B · jsonl_rows={sum(1 for _ in open(jsonl_p, encoding='utf-8')) if jsonl_p.exists() else 0}")
    else:
        print(f"[N/A-ERROR] txt not created")
except Exception as e:
    print(f"[N/A-ERROR:BACKFILL] {type(e).__name__}: {e}")
    sys.exit(1)
