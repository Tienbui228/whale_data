"""O4 · đo ngân sách 6 đêm (09-14..09-19) · pre-cap + post-cap.

Pre-cap = body sau build_v2_digest (chưa qua _v1_3_apply_3tier_cap).
Post-cap = body sau cap · = len msg sent - prefix.

Trả bảng: target · pre_cap · post_cap · n_cut · trạng thái vs 4096.
"""
import sys, os
try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except: pass  # L-66-OK (stdout reconfigure benign)
sys.path.insert(0, "/root/Data_back_test/whale_data/scripts")

os.environ["DIGEST_V1_3"] = "1"
os.environ["DIGEST_U0_BELL_BLOCK"] = "1"
os.environ["DIGEST_B_TIER"] = "1"

from digest_summary_v2 import build_v2_digest, _v1_3_apply_L1_cites, _v1_3_apply_L3_strip_dups

TARGETS = ["2026-09-14", "2026-09-15", "2026-09-16", "2026-09-17", "2026-09-18", "2026-09-19"]

print(f"{'target':12s} | {'pre-cap':>8s} | {'post-cap':>8s} | {'n_cut':>5s} | {'vs 4096':>10s}")
print(f"{'-'*12} | {'-'*8} | {'-'*8} | {'-'*5} | {'-'*10}")

for tgt in TARGETS:
    try:
        # build_v2_digest applies L1_cites + L3_strip + 3tier_cap internally when v1_3_mode.
        # To get pre-cap: monkey-patch or reproduce fragment.
        # Simpler: build_v2_digest returns POST-CAP body. Pre-cap = re-render intermediate
        # by calling internals. For approximation: build_v2_digest gives post-cap.
        # Approximation pre-cap = post + n_cut extracted from BUDGET-CAP audit line.
        body = build_v2_digest(tgt)
        post_cap = len(body)

        # Look for [BUDGET-CAP: cắt N dòng · còn X/budget] audit line
        import re as _re
        m = _re.search(r"BUDGET-CAP:\s+cắt\s+(\d+)\s+dòng\s+·\s+còn\s+(\d+)/(\d+)", body)
        if m:
            n_cut_lines = int(m.group(1))
            len_after = int(m.group(2))
            n_cut_chars = post_cap - len_after   # rough estimate
        else:
            n_cut_lines = 0; n_cut_chars = 0

        # Get pre-cap: monkey-patch _v1_3_apply_3tier_cap to identity, re-call build_v2_digest
        import digest_summary_v2 as dsv
        _orig_cap = dsv._v1_3_apply_3tier_cap
        pre_cap = None
        try:
            def _no_cap(body, budget=3680):
                return body
            dsv._v1_3_apply_3tier_cap = _no_cap
            body_nocap = dsv.build_v2_digest(tgt)
            pre_cap = len(body_nocap)
        except Exception as _e2:
            pre_cap = None
            print(f"  [pre-cap ERR] {type(_e2).__name__}: {_e2}", file=sys.stderr)
        finally:
            dsv._v1_3_apply_3tier_cap = _orig_cap

        pre_str = f"{pre_cap}" if pre_cap else "?"
        cut_est = (pre_cap - post_cap) if pre_cap else n_cut_chars
        vs = ">4096" if post_cap > 4096 else ("≤4096" if post_cap <= 4096 else "?")
        print(f"{tgt:12s} | {pre_str:>8s} | {post_cap:>8d} | {cut_est:>5d} | {vs:>10s}")
    except Exception as e:
        print(f"{tgt:12s} | ERR: {type(e).__name__}: {e}")

print()
print(f"# note: post-cap = body after 3-tier cap · pre-cap monkey-patched (no cap).")
print(f"# limit tin TG = 4096 · prefix ~30 → body budget ≤4066.")
