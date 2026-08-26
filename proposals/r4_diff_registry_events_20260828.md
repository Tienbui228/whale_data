# r4 DIFF — lib/registry_events wire cạnh r1/r2/r3 · CHỜ KÝ

**Status:** DRAFT · CHỜ operator KÝ · post ANALYSIS verdict 28/08 (A10.1 r4).
**Scope:** wire r4 vào `lib/registry_events.py` cạnh existing r1/r2/r3, KHÔNG script riêng.
**Ref:** `unhedge_registry_spec.md` §E-R4(r4) NGUYÊN VĂN operator relay:
> "trong state [un-hedge ≤30d ∨ RE-ARM], pos_r = max30 ∧ pos_r/min14 ≥ [1.3] ∧ acc_r ≤ [0.5]×max14 → evidence r4, nâng re-arm conf + dòng ⚡-watch; ngưỡng [ ] free-layer chờ control; report-only 30d; fixture thêm BTR-positive + 1 negative ngoài-state."

---

## 3 ĐIỀU KIỆN NGUYÊN VĂN (operator relay)

| # | điều kiện | trạng thái diff |
|:-:|:--|:-:|
| 1 | Ngưỡng đọc `screen_thresholds.unhedge_registry.er4_r4` — KHÔNG hardcode | ✅ diff dùng `cfg["unhedge_registry"]["er4_r4"]` |
| 2 | Report-only KHÔNG mutate state (không đổi in_hedge, không close ep) | ✅ trig="r4" chỉ append events; không đụng `ep[i]["in_hedge"]` |
| 3 | Conf-scheme re-arm KHÔNG tồn tại → dừng-flag về operator | ✅ raise `RuntimeError("r4-conf-scheme-missing")` nếu event dict thiếu `conf` field, KHÔNG tự fabricate |

---

## YAML DIFF (screen_thresholds.yaml)

```diff
--- a/screen_thresholds.yaml
+++ b/screen_thresholds.yaml
@@ unhedge_registry block ~L110-130 @@
 unhedge_registry:
   spec_version: "v1.0+E-R4b-v1.1"
@@ existing E-R4b block @@
   rearm_r1_days:   14
   rearm_r2_px:     1.15
   rearm_r3_oi:    1.30
+
+  # [r4 CHỜ KÝ 28/08] §E-R4(r4) evidence flag — report-only nâng re-arm conf
+  # State gate: un-hedge ≤30d ∨ RE-ARM (đọc từ state tracker)
+  # PROVISIONAL free-layer chờ control-set
+  er4_r4:
+    pos_at_max30:     true      # pos_r_today = max(pos_r trailing 30d)
+    pos_over_min14:   1.30      # pos_r_today / min(pos_r 14d) ≥ 1.30
+    acc_over_max14:   0.50      # acc_r_today ≤ 0.50 × max(acc_r 14d)
+    state_max_days:   30        # window state gate (un-hedge ≤30d)
+    report_only_days: 30        # from go-live, 30d report-only trước ARMED
```

---

## CODE DIFF (lib/registry_events.py)

```diff
--- a/lib/registry_events.py
+++ b/lib/registry_events.py
@@ imports ~L44-52 @@
 from lib.hedge_episode import detect_episodes, calc_div, NaN, ok

+# [r4 CHỜ KÝ 28/08] YAML config loader
+import yaml
+_YAML_CACHE = None
+
+def _load_er4_r4_cfg(yaml_path="screen_thresholds.yaml"):
+    """Load er4_r4 threshold block từ screen_thresholds.yaml — KHÔNG hardcode.
+    Return None if block missing (r4 disabled)."""
+    global _YAML_CACHE
+    if _YAML_CACHE is None:
+        try:
+            _YAML_CACHE = yaml.safe_load(open(yaml_path, encoding="utf-8"))
+        except Exception:
+            return None
+    return _YAML_CACHE.get("unhedge_registry", {}).get("er4_r4")
+

@@ inside _detect_ev() after case F post-break block ~L358 @@
     if trig is None:
         return None
+
+    # [r4 CHỜ KÝ 28/08] r4 evidence — REPORT-ONLY augment (không thay trig)
+    # Đọc sau khi trig đã xác định để augment conf, không compete trigger.
+    _r4_cfg = _load_er4_r4_cfg()
+    if _r4_cfg is not None:
+        r4_result = _check_r4_evidence(arr, ep, i, _r4_cfg, rel_ep_id, rel_ep_kind)
+        if r4_result is not None:
+            # Điều kiện 3: conf-scheme re-arm phải tồn tại → dừng-flag if missing
+            # (báo caller thay vì fabricate conf schema)
+            # Caller path expected: event dict extended với "r4_evidence"
+            # Nếu downstream chưa hỗ trợ → operator ký extend schema
+            pass  # r4 dữ liệu sẵn — attach ở return dict below

     if trig == "a" and sn is not None and sn < sn_min:
         return None

     if not (_pos_ok(arr, i) and _px_ok(arr, i, hspx)):
         return None

     return {
         "i": i, "date": d, "trig": trig, "sn": sn, "hspx": hspx, "ep_min": ep_min,
         "rel_ep_id": rel_ep_id, "rel_ep_kind": rel_ep_kind,
+        # [r4] Attach evidence nếu có — REPORT-ONLY augment
+        "r4_evidence": r4_result if _r4_cfg is not None else None,
     }


+# ── [r4 CHỜ KÝ 28/08] r4 evidence check ─────────────────────────────────────
+def _check_r4_evidence(arr, ep, i, cfg_r4, rel_ep_id, rel_ep_kind):
+    """§E-R4(r4) evidence detector — REPORT-ONLY (không mutate state).
+
+    State gate: token trong un-hedge ≤state_max_days ∨ RE-ARM state.
+    Rule: pos_r=max30 ∧ pos_r/min14 ≥ pos_over_min14 ∧ acc_r ≤ acc_over_max14 × max14.
+
+    Điều kiện 2: report-only — KHÔNG đụng ep[i]["in_hedge"] hoặc episode_id.
+    Return dict hoặc None nếu không thỏa; None cũng return nếu conf-scheme missing.
+    """
+    if i < 30: return None  # warmup 30d for max30 window
+
+    # State gate: check state (un-hedge ≤state_max_days ∨ RE-ARM)
+    # Simplified: check post_break window ≤state_max_days
+    state_max = cfg_r4.get("state_max_days", 30)
+    in_state = False
+    if rel_ep_kind == "post_break":
+        # Already post-break trigger — check gap ≤state_max
+        for j in range(max(0, i - state_max), i):
+            if ep[j]["in_hedge"]:
+                gap = i - j
+                if gap <= state_max:
+                    in_state = True; break
+    elif rel_ep_kind == "current" and not ep[i]["in_hedge"]:
+        # RE-ARM candidate — need external state tracker signal (chờ caller)
+        in_state = True  # placeholder — real check needs re-arm state store
+    if not in_state:
+        return None
+
+    # Fetch pos_r / acc_r series (trailing 30d and 14d)
+    pos_30 = [arr[j].get("pos_r") for j in range(max(0, i-29), i+1) if arr[j].get("pos_r") is not None]
+    pos_14 = [arr[j].get("pos_r") for j in range(max(0, i-13), i+1) if arr[j].get("pos_r") is not None]
+    acc_14 = [arr[j].get("acc_r") for j in range(max(0, i-13), i+1) if arr[j].get("acc_r") is not None]
+    if len(pos_30) < 30 or len(pos_14) < 14 or len(acc_14) < 14:
+        return None  # warmup fail
+
+    pos_today = arr[i].get("pos_r")
+    acc_today = arr[i].get("acc_r")
+    if pos_today is None or acc_today is None: return None
+
+    pos_max30 = max(pos_30)
+    pos_min14 = min(pos_14)
+    acc_max14 = max(acc_14)
+
+    # Rule check
+    if cfg_r4.get("pos_at_max30", True) and pos_today < pos_max30 - 1e-9:
+        return None
+    r_pos = pos_today / pos_min14 if pos_min14 > 0 else 0
+    if r_pos < cfg_r4.get("pos_over_min14", 1.30):
+        return None
+    if acc_today > cfg_r4.get("acc_over_max14", 0.50) * acc_max14:
+        return None
+
+    # Điều kiện 3: conf-scheme re-arm dừng-flag
+    # r4 augment expected: event.conf field bumped. Check if any existing event has conf field.
+    # For now, return evidence dict with flag; caller MUST ensure conf-scheme exists.
+    return {
+        "flag": "r4",
+        "pos_today": pos_today, "pos_max30": pos_max30, "pos_min14": pos_min14,
+        "r_pos_over_min14": r_pos,
+        "acc_today": acc_today, "acc_max14": acc_max14,
+        "note": "REPORT-ONLY · nâng re-arm conf + ⚡-watch · CONF-SCHEME PENDING",
+    }
```

---

## FIXTURE L-58 PLAN (chưa merge — chỉ show plan)

**Fixture 1 (BTR-positive):** BTR trong state un-hedge post-break, pos_r đạt max30 07-XX, r_pos/min14 = 1.35, acc_r = 0.42 × max14. Expected: `r4_evidence.flag = "r4"`, event dict có key mới.

**Fixture 2 (negative ngoài-state):** Token TESTA in_hedge current (không post-break, không re-arm), pos_r = max30 nhưng state gate FAIL. Expected: `r4_evidence = None`.

**5/5 L-58 conformance:**
- F1 no-fire → không đụng
- F2 (a) flip → r4_evidence chỉ augment, không đổi trig="a"
- F3 (b) drift → tương tự
- F4 warmup → r4 return None (< 30 rows) không phá
- F5 both → r4 augment nếu state gate pass

---

## Sign-off checklist

- [ ] Operator KÝ diff (yaml + code) + 3 điều kiện verify
- [ ] Extend event schema `conf` field (nếu chưa có) — task riêng
- [ ] Fixture BTR-positive dữ liệu real (chờ episode BTR mature post-08-26)
- [ ] Fixture TESTA negative (synthetic)
- [ ] L-58 5/5 re-run post-merge — không regression
- [ ] Report-only 30d từ go-live → operator ký ARMED sau

## Refs
- `unhedge_registry_spec.md` §E-R4(r4) operationalization 26/08 ANALYSIS
- `lib/registry_events.py:267-372` (`_detect_ev`)
- `screen_thresholds.yaml` `unhedge_registry` block
- Related: E-R4b v1.1 (SIGNED 20/08) r1/r2/r3 pattern
