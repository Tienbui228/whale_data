# A3-2 · Rename plan: U0 → U0-CLASS · SANDBOX

**Scope**: chỉ `scripts/digest_summary_v2.py` (grep whole repo · Grep '\bU0\b' trả 1 file).

**Rationale**: phân biệt 2 khái niệm:
- **U0-CLASS** (cũ, A2.1) = species-B classifier, dùng gán loài + mở U1 gate.
- **U0-BELL** (mới, A3-1) = chuông sớm (backward Δacc), CALIBRATION-ONLY.

Trước A3, "U0" mơ hồ. Sau A3, rõ 2 tên.

## Diff cần apply

File: `scripts/digest_summary_v2.py`

```diff
--- L579  ORIG
-        # b6 U0 W3: skip (needs cross-date) — DRAFT: use b4_cross as proxy for U0 pass
+        # b6 U0-CLASS W3: skip (needs cross-date) — DRAFT: use b4_cross as proxy for U0-CLASS pass

--- L580  ORIG
-        b6_u0 = b4_cross  # DRAFT proxy
+        b6_u0_class = b4_cross  # DRAFT proxy (A3-2 rename U0 → U0-CLASS)

--- L581  ORIG
-        k_total = k_tagger + int(b3_age) + int(b4_cross) + int(b6_u0)
+        k_total = k_tagger + int(b3_age) + int(b4_cross) + int(b6_u0_class)

--- L588  ORIG
-            "b6_u0_proxy":    b6_u0,
+            "b6_u0_class_proxy":    b6_u0_class,
```

## Spec update

`docs/PATTERN_BOOK_v1_3_20260910.md` R5 ghi "U0 vượt 0.5→0.7 ..." → update sang "U0-CLASS vượt 0.5→0.7 ...".

`proposals/v1_3_species_layout_amendment_20260913.md` L57 "b6 U0 W3" → "b6 U0-CLASS W3".

## Wire condition

**KHÔNG apply live** tới khi:
- ANALYSIS ký A3-3 (header đếm token distinct)
- Pin p85-p88 đều PASS
- SCP đợi handover A3-7 chấp thuận

Sandbox chỉ ghi plan · live rename khi pin đen đủ.

## Backward-compat

Nếu có consumer đọc `b6_u0_proxy` field trong verdict-file, cần update reader.
Grep `b6_u0_proxy` → 0 hit ngoài `digest_summary_v2.py`. An toàn rename.
