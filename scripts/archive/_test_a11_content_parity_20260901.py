"""A11 CONTENT-PARITY (permanent audit item · KÝ 01/09)

Mọi block trùng tên hai nhà {h4 · spot_cvd · ma_shadow · walletset*} → diff nội dung.
Kỳ vọng: pointer-style (bot mirror status/changelog_ref/canonical) hoặc trùng tuyệt đối.
Lệch nội dung ngoài pointer = FAIL (context-inversion họ L-48/L-51).

Rule per-block:
  · block canonical MỘT nhà (declared by canonical:key hoặc yaml comment) → nhà kia phải POINTER
  · pointer keys tối thiểu: {status, changelog_ref, canonical}
  · pointer KHÔNG mang operational thresholds (dom, imb_min, etc.)
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
import yaml

REPO = Path(r"D:\Data back test\whale_data")
WHALE_YAML = REPO / "screen_thresholds.yaml"
BOT_YAML = Path(r"D:/Data back test/binance-bot-signals/screen_thresholds.yaml")

with open(WHALE_YAML, encoding="utf-8") as f: whale = yaml.safe_load(f)
with open(BOT_YAML, encoding="utf-8") as f: bot = yaml.safe_load(f)

# Blocks to check parity
# Format: (block_name, whale_path, bot_path, canonical_home)
BLOCKS = [
    ("h4",         ["goi_nhe", "h4"],         ["h4"],         "whale_data"),
    ("spot_cvd",   ["goi_nhe"],               ["spot_cvd"],   "bot-signals"),  # bot canonical (render)
    ("ma_shadow",  ["goi_nhe"],               ["ma_shadow"],  "bot-signals"),
    ("walletset_2x2",  ["goi_nhe", "walletset_2x2"], None,   "whale_data"),  # only whale, no bot mirror expected
    ("review_bundle_20260927", ["goi_nhe", "review_bundle_20260927"], None, "whale_data"),
    ("forward_tests", ["forward_tests"], None, "whale_data"),  # [RENDER-V2-20260902] runner reads · bot-signals bảng D mirror doc
]

def _get_nested(d, path):
    for k in path:
        if not isinstance(d, dict): return None
        d = d.get(k, {})
    return d if isinstance(d, dict) and d else None

def _get_block(root, block_name, path):
    """Get block by traversing path. If final leaf name equals block_name, use that; else drill in."""
    if path is None: return None
    node = root
    for k in path:
        if not isinstance(node, dict): return None
        node = node.get(k, {})
    if isinstance(node, dict) and block_name in node and path[-1] != block_name:
        node = node.get(block_name)
    return node if isinstance(node, dict) and node else None

print(f"{'block':<30} {'whale?':<7} {'bot?':<7} {'canonical':<12} {'verdict':<25}")
print("-"*90)

all_pass = True
for block_name, whale_path, bot_path, canonical_home in BLOCKS:
    # For whale, path traversal
    w = None
    node = whale
    for k in whale_path:
        if not isinstance(node, dict): break
        node = node.get(k, {})
    if isinstance(node, dict):
        # If path ends with block_name → node is the block
        if whale_path[-1] == block_name:
            w = node if node else None
        elif block_name in node:
            w = node.get(block_name)
    # For bot
    b = None
    if bot_path:
        node = bot
        for k in bot_path:
            if not isinstance(node, dict): break
            node = node.get(k, {})
        if isinstance(node, dict) and node:
            b = node

    verdict = ""
    if w is None and b is None:
        verdict = "N/A (không có ở cả 2)"
    elif w is not None and b is None:
        # Only whale — OK if canonical=whale_data
        if canonical_home == "whale_data": verdict = "✓ CANONICAL-WHALE only"
        else: verdict = "✗ MISSING-BOT (canonical bot but no block)"; all_pass = False
    elif w is None and b is not None:
        if canonical_home == "bot-signals": verdict = "✓ CANONICAL-BOT only"
        else: verdict = "✗ MISSING-WHALE (canonical whale but no block)"; all_pass = False
    else:
        # Both exist → check pointer-mirror rule
        # Non-canonical side must be pointer: keys ⊆ {status, changelog_ref, canonical, close_reason,
        #   survey_evidence_md5, ci_addendum_md5, verdict_line, reopen_condition, source}
        POINTER_ALLOWED = {"status", "changelog_ref", "canonical", "close_reason",
                            "survey_evidence_md5", "ci_addendum_md5", "verdict_line",
                            "reopen_condition", "source", "signed"}
        if canonical_home == "whale_data":
            bot_extra_keys = set(b.keys()) - POINTER_ALLOWED
            if bot_extra_keys:
                verdict = f"✗ BOT-NOT-POINTER · extra ops keys: {sorted(bot_extra_keys)}"; all_pass = False
            else:
                verdict = "✓ BOT-POINTER (mirror OK)"
        elif canonical_home == "bot-signals":
            whale_extra_keys = set(w.keys()) - POINTER_ALLOWED
            if whale_extra_keys:
                verdict = f"✗ WHALE-NOT-POINTER · extra ops keys: {sorted(whale_extra_keys)}"; all_pass = False
            else:
                verdict = "✓ WHALE-POINTER (mirror OK)"

    print(f"{block_name:<30} {str(w is not None):<7} {str(b is not None):<7} {canonical_home:<12} {verdict:<25}")

print()
print(f"[VERDICT] all_pass={all_pass}")
if not all_pass:
    print("[FAIL] content-parity violation · nhà không-canonical mang operational keys hoặc missing block")
    sys.exit(1)
else:
    print("[OK] all blocks pass content-parity (canonical MỘT nhà · mirror POINTER hai nhà một câu chuyện)")
