"""BA4 · lint một-token-một-khối · REPORT-ONLY (doctrine BA5).

Tokenizer FIX: chỉ quét tên token trong universe (data/config/freshwatch_symbols.txt),
KHÔNG regex bắt ngày tháng/chữ.

Doctrine BA5 (ANALYSIS 22/09): mọi lint mới = REPORT-ONLY ≥5 đêm trước khi chặn gửi.
Trạng thái hiện tại: DAY 1/5 · CHỈ BÁO · KHÔNG chặn.
"""
from __future__ import annotations
import os, sys, re
from pathlib import Path

_REPO = Path("/root/Data_back_test/whale_data") if os.name != "nt" \
        else Path(r"D:/Data back test/whale_data")

try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except AttributeError: pass  # L-66-OK

FW_SYM_P = _REPO / "data/config/freshwatch_symbols.txt"
BODY_P = _REPO / "data/logs/master_preview_body.txt"

# Load universe (short-form · strip USDT · thêm cả 2 forms)
if not FW_SYM_P.exists():
    print(f"ERROR: {FW_SYM_P} missing"); sys.exit(1)

universe_full = set()
universe_bare = set()
for ln in FW_SYM_P.read_text(encoding="utf-8").splitlines():
    ln = ln.strip()
    if not ln: continue
    universe_full.add(ln)
    if ln.endswith("USDT"): universe_bare.add(ln[:-4])
    else: universe_bare.add(ln)
print(f"universe loaded: {len(universe_full)} full-form · {len(universe_bare)} bare-form")

if not BODY_P.exists():
    print(f"ERROR: {BODY_P} missing · run master render first"); sys.exit(1)

body = BODY_P.read_text(encoding="utf-8")
print(f"body loaded · {len(body)} chars · md5={__import__('hashlib').md5(body.encode()).hexdigest()[:12]}")

# Extract blocks by "── HEADER ──" marker
blocks = re.split(r"^(── [^─\n]+ ──.*?)$", body, flags=re.M)
# blocks alternates: [before_first, header_1, content_1, header_2, content_2, ...]

named_blocks = []
current_header = "START"
current_content = ""
for i, chunk in enumerate(blocks):
    if chunk.startswith("── "):
        if current_content.strip():
            named_blocks.append((current_header, current_content))
        current_header = chunk[:60].strip()
        current_content = ""
    else:
        current_content += chunk
if current_content.strip():
    named_blocks.append((current_header, current_content))

print(f"blocks parsed: {len(named_blocks)}")

# For each token in universe, find which blocks it appears in
# Match bare form as word boundary: \bTOK\b (or with USDT suffix)
token_blocks = {}
for header, content in named_blocks:
    header_short = header[:35]
    tokens_found = set()
    # scan word-boundary tokens · check against universe_bare set
    for m in re.finditer(r"\b([A-Z0-9]{2,20})\b", content):
        tok = m.group(1)
        if tok in universe_bare:
            tokens_found.add(tok)
        elif tok.endswith("USDT") and tok[:-4] in universe_bare:
            tokens_found.add(tok[:-4])
    for tok in tokens_found:
        token_blocks.setdefault(tok, set()).add(header_short)

# tokens appearing in ≥2 blocks (excluding non-content blocks)
multi = {t: hs for t, hs in token_blocks.items() if len(hs) >= 2}

print(f"tokens in universe appearing in ≥2 blocks: {len(multi)}")
print()
if multi:
    for tok, hs in sorted(multi.items()):
        print(f"  {tok:15s} · in {len(hs)} blocks: {sorted(hs)}")
else:
    print("  (none)")

print()
print(f"═══ BA4 · lint one-token-one-block · REPORT-ONLY DAY 1/5 (doctrine BA5) ═══")
print(f"  Không chặn gửi · chỉ báo trong 5 đêm mẫu · sau đó ANALYSIS quyết")
sys.exit(0)   # report-only always exits 0
