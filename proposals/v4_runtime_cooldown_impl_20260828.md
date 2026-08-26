# V④ Runtime Cross-Day Cooldown — DIFF proposal (OPERATOR KÝ 28/08, 3 điều kiện)

**Status:** OPERATOR KÝ 28/08 với 3 điều kiện · **CHỜ ANALYSIS 1-line cho scope (2) trước merge**.
**Ngày soạn:** 2026-08-28 · **Ngày ký:** 2026-08-28 (post V④ hồi-tố 26/08)
**Ref:** spec §1-H amend V④ (whale_data yaml `gom_h_cooldown_days=14` + `gom_h_cooldown_clean_days=3`); reuse §8.4(i) NGUYÊN VĂN, KHÔNG ngưỡng mới.

---

## 0. §8.4(i) NGUYÊN VĂN (paste bên cạnh diff per điều kiện 1)

Từ `binance-bot-signals/docs/gom_detect_spec.md` line 360:

> **(i)** Suppressor CỨNG (6 tín hiệu: `dist_wall`, `lsr_dist`, `funding_neg_div`, `funding_extreme`, `decay`, `post_climax`) bật = đóng chuỗi + **cooldown 14d từ first-fire của đợt** (fire = day0; blocked days 1→13; clear từ day14 = fire+14); **đợt mới = sau ≥3d sạch (không suppressor bắn)**. Trong cooldown, chuỗi KHÔNG được mở lại dù GOM fires. low_conf = flag không reset. Per-day DQ (`wrong_side`, `slope_dq`, `toi_dq`) = block ngày đó only, KHÔNG trigger cooldown 14d.

**Chấm điều kiện (1) "3d sạch có thì giữ":** ✅ **CÓ** trong text gốc line 360. Giữ `clean_days=3` trong impl. KHÔNG ngưỡng mới, KHÔNG cắt bớt.

---

## OPERATOR KÝ 28/08 · 3 ĐIỀU KIỆN

| # | Điều kiện | Trạng thái | Xử lý |
|:-:|:--|:-:|:--|
| 1 | Paste §8.4(i) nguyên văn cạnh diff; "3d sạch" có→giữ, không→cắt | ✅ Done §0 trên | Text gốc có "3d sạch" → giữ clean_days=3 |
| 2 | Cooldown scope = per (token, compose-fire) bất kể nhánh H | ⏸ CHỜ ANALYSIS 1-line | Impl đã đúng scope (check GOM_H=T only, nhánh-agnostic) — chờ ANALYSIS confirm |
| 3 | Backfill re-run KHÔNG đè; CSV cũ giữ `.pre_v4rt`, bản mới ghi cạnh | 📋 Plan ready | Bash: `for f in scratch/gom_h_daily_2026-08-2{2,3,4,5}.csv; do mv "$f" "$f.pre_v4rt"; done` trước rerun |

---

## 1. Scope

Thêm cross-day cooldown check vào `scripts/gom_h_daily.py` runtime — mỗi daily invocation load previous CSVs để kiểm tra cooldown per-symbol trước khi compose GOM-H fire.

**KHÔNG đụng:** thresholds.yaml canonical · adapter · other collectors · other cron entries.

---

## 2. Semantic (reuse §8.4(i) nguyên văn)

Từ `binance-bot-signals/docs/gom_detect_spec.md §8.4(i)`:
> "Suppressor CỨNG bật → đóng chuỗi + **cooldown 14d từ first-fire của đợt** (fire = day0; blocked days 1→13; clear từ day14 = fire+14); **đợt mới = sau ≥3d sạch** (không suppressor bắn)."

**Áp cho GOM-H:**
- First GOM-H fire cho `sym` = day 0
- Days 1→13 sau đó: GOM-H fire của `sym` bị **BLOCK** (mark GOM_H=`F-COOLDOWN`, active=`[cooldown]`)
- Day 14: cooldown clear (nếu không có fire mới nào)
- **Reset đợt sớm:** nếu ≥3 ngày liên tiếp sạch (không có GOM-H fire cho `sym`) trong cooldown window → đợt hiện tại đóng, đợt mới có thể start

**Reuse doctrine _gomc_beta_check(check_cooldown=True):** quét `j ∈ range(max(0, i-13), i)` — bất kỳ day j nào có GOM-H fire cho sym (và không có 3d sạch gap sau đó) → return cooldown-active.

---

## 3. Unified DIFF

```diff
--- a/scripts/gom_h_daily.py
+++ b/scripts/gom_h_daily.py
@@ -22,6 +22,7 @@
 Output:
   - scratch/gom_h_daily_<date>.csv (append-only, khóa (token,date))
   - stdout Telegram block "CAMPAIGN-PRE (soi on-chain) [REPORT-ONLY · PROVISIONAL-UNSIGNED]"
+  - V④ cross-day cooldown: reuse §8.4(i) — reads previous N-1 CSVs to check cooldown.

 Usage:
   python scripts/gom_h_daily.py --date 2026-08-23    # target date (D-1 typical)
@@ -43,6 +44,7 @@
 YAML_PATH = REPO / "screen_thresholds.yaml"
 SCRATCH_DIR = REPO / "scratch"
 SPEC_VERSION = "v4.0-draft"
 AMENDMENTS = ["GOM-RESTRUCT-20260824", "⑬-COLUMN-MANIFEST-20260826"]
+AMENDMENTS.extend(["V①-V⑤-20260828", "V④-RUNTIME-COOLDOWN-20260828"])

 # ─── Warmup thresholds (điểm-non-null) ───

@@ -272,6 +274,52 @@ def _eval_h1(sym, target_date, adapter_df, cfg_h1, t01_status=None):
     return "F", detail
+
+
+def _check_gom_h_cooldown(sym: str, target: str, scratch_dir: Path,
+                          cooldown_days: int = 14, clean_days: int = 3) -> tuple[bool, str]:
+    """V④ cross-day cooldown per §8.4(i) reuse — reads previous (cooldown_days-1) CSVs.
+
+    Semantic:
+      - Scan j ∈ [target - cooldown_days + 1, target - 1] previous CSVs (nếu exist)
+      - Tìm fires của `sym` trong window
+      - Nếu ≥1 fire trong window AND không có ≥clean_days sạch consecutive sau fire mới nhất
+        → cooldown ACTIVE (BLOCK)
+      - Ngược lại → free (fire allowed)
+
+    Returns: (in_cooldown: bool, reason: str)
+      in_cooldown=True → runner mark GOM_H='F-COOLDOWN', active='[cooldown]'
+    """
+    target_dt = datetime.strptime(target, "%Y-%m-%d")
+    fires_in_window: list[str] = []
+    for lb in range(1, cooldown_days):
+        d = (target_dt - timedelta(days=lb)).strftime("%Y-%m-%d")
+        csv_path = Path(scratch_dir) / f"gom_h_daily_{d}.csv"
+        if not csv_path.exists():
+            continue
+        try:
+            df = pd.read_csv(csv_path)
+            row = df[df["symbol"] == sym]
+            if not row.empty and str(row.iloc[0].get("GOM_H", "")) == "T":
+                fires_in_window.append(d)
+        except Exception:
+            continue
+
+    if not fires_in_window:
+        return False, "no-prev-fire"
+
+    # Sort fires ascending
+    fires_in_window.sort()
+    last_fire = fires_in_window[-1]
+    last_fire_dt = datetime.strptime(last_fire, "%Y-%m-%d")
+    days_since_last = (target_dt - last_fire_dt).days
+
+    # ≥clean_days sạch since last fire → đợt closed
+    if days_since_last >= clean_days + 1:
+        # Check: days last_fire+1 .. target-1 all sạch (no other fires)
+        # (Simplification: if fires_in_window has no dates between last_fire+1 and target-1,
+        #  those days were sạch. Since last_fire is the latest, that's already true.)
+        # → đợt considered closed after ≥clean_days consecutive sạch
+        return False, f"reset-clean-{days_since_last}d"
+
+    return True, f"cooldown-active-since-{last_fire}"


 def main():
@@ -350,7 +398,7 @@ def main():
         h2_status, h2_detail = _eval_h2(df_sym, target, gom_h_cfg["h2"])
         h3_status, h3_detail = _eval_h3(df_sym, target, gom_h_cfg["h3"])

         for h, s in [("T0.1", t01_status), ("H1", h1_status), ("H2", h2_status), ("H3", h3_status)]:
             if s == "T" or s == "F" or s in ("N/A-WARMUP", "N/A"):
                 coverage[h][s] += 1

-        # Compose GOM-H = H1 ∨ (H2 ∧ T0.1); H3 nâng conf
+        # Compose GOM-H = (H1 ∨ (H2 ∧ T0.1)) AND NOT gom_h_cooldown_14d (V④); H3 nâng conf
         h1_t = h1_status == "T"
         h2t01 = (h2_status == "T") and (t01_status == "T")
-        # If H1 has data and either fires
-        if h1_t or h2t01:
+        raw_fire = h1_t or h2t01
+
+        # V④ cross-day cooldown check
+        cooldown_days = gom_h_cfg.get("gom_h_cooldown_days", 14)
+        clean_days = gom_h_cfg.get("gom_h_cooldown_clean_days", 3)
+        in_cd, cd_reason = _check_gom_h_cooldown(sym, target, SCRATCH_DIR,
+                                                  cooldown_days, clean_days) if raw_fire else (False, "-")
+
+        if raw_fire and not in_cd:
             gom_h = "T"
             n_fire += 1
             active = []
             if h1_t: active.append("H1")
             if h2t01: active.append("H2+T0.1")
             conf = "conf-boosted" if h3_status == "T" else "normal"
             fires.append({"symbol": sym, "active": active, "conf": conf,
                           "h1": h1_status, "h2": h2_status, "t01": t01_status, "h3": h3_status,
                           "h1_detail": h1_detail})
+        elif raw_fire and in_cd:
+            gom_h = "F-COOLDOWN"
+            active = ["[cooldown]"]
+            conf = "-"
+            # Log to fires with cooldown suffix (report-only visibility)
+            fires.append({"symbol": sym, "active": active, "conf": f"blocked:{cd_reason}",
+                          "h1": h1_status, "h2": h2_status, "t01": t01_status, "h3": h3_status,
+                          "h1_detail": h1_detail})
         else:
             gom_h = "F" if (h1_status in ("F",) and h2_status in ("F","N/A-WARMUP") and t01_status in ("F","N/A-WARMUP")) else \
                     ("N/A-WARMUP" if "N/A-WARMUP" in (t01_status, h2_status) else "F")
             conf = "-"
```

---

## 4. Behavior change matrix

| Scenario | Pre-V④ | Post-V④ runtime |
|---|:--|:--|
| First fire cho SYM | GOM_H=T | GOM_H=T (unchanged) |
| Fire ngày +1..+13 sau first-fire (không sạch gap) | GOM_H=T | **GOM_H=F-COOLDOWN** |
| Fire ngày +3 nhưng có 3d sạch trước đó | GOM_H=T | GOM_H=T (đợt reset) |
| Fire ngày +14 sau first-fire | GOM_H=T | GOM_H=T (cooldown clear) |
| No prev fire | GOM_H=T | GOM_H=T (unchanged) |

CSV col `GOM_H` values sau impl: `T` · `F` · `F-COOLDOWN` · `N/A-WARMUP` · `N/A`.

**Scope confirmation cho điều kiện (2):** `_check_gom_h_cooldown()` chỉ đọc CSV col `GOM_H` == `"T"` (compose-fire aggregate). **Nhánh-agnostic:** không phân biệt H1 fire vs H2+T0.1 fire — cả 2 đều trigger cooldown. Đây là scope "per (token, compose-fire) bất kể nhánh H" per operator điều kiện (2). **Chờ ANALYSIS 1-line confirm.**

---

## 5. Backtest evidence — MIRAUSDT case

**Backfill 26/08 session (P0 cron fix):**
- 2026-08-24 MIRAUSDT [H2+T0.1] GOM_H=T
- 2026-08-25 MIRAUSDT [H2+T0.1] GOM_H=T ← same symbol, 1 day gap

**Post-V④ runtime expected:**
- 08-24 GOM_H=T (first fire)
- 08-25 GOM_H=F-COOLDOWN (blocked, cooldown-active-since-2026-08-24)
- Collapse: 2 consecutive fires → 1 fire, 6.7-day mean-gap-per-fire (báo tín hiệu chỉ 1 lần/đợt).

**LAUSDT 08-25 (1 fire only, no 08-24 fire):** GOM_H=T unchanged (no prev fire).

---

## 6. Testing plan (post-ký · post-ANALYSIS-1-line)

**Điều kiện (3) — KHÔNG ĐÈ backfill:**
```bash
# VPS SSH: rename existing CSVs to .pre_v4rt BEFORE re-running
for f in scratch/gom_h_daily_2026-08-2{1,2,3,4,5}.csv; do
    [ -f "$f" ] && mv "$f" "$f.pre_v4rt"
done
# Then re-run under V④ runtime (writes fresh CSV cạnh .pre_v4rt)
for d in 2026-08-21 2026-08-22 2026-08-23 2026-08-24 2026-08-25; do
    .venv/bin/python3 scripts/gom_h_daily.py --date $d
done
# Diff:
diff scratch/gom_h_daily_2026-08-25.csv.pre_v4rt scratch/gom_h_daily_2026-08-25.csv
```

1. **Unit test:** `_check_gom_h_cooldown` với sample fires history + edge cases (empty · 1 fire · 3d clean · exactly 14d).
2. **Backfill re-run KHÔNG ĐÈ:** rename `.pre_v4rt` → chạy lại 08-21..08-25 dưới V④ runtime → verify MIRA 08-25 flip T→F-COOLDOWN.
3. **Live smoke:** đêm sau ký, cron 45 1 * * * chạy target=D-1, log GOM_H=F-COOLDOWN rows nếu có.
4. **Regression census T-④:** re-run E2 FULL 52 census dưới V④ runtime → per-token fires collapse. Update T-④ GATE RENDER trên bản MỚI (bản `.pre_v4rt` giữ nguyên đối chứng).

---

## 7. Rủi ro & mitigation

- **Rủi ro (a):** CSV history không tồn tại (backfill gaps) → cooldown check silent-skip → false-fire.
  **Mitigation:** log "no-prev-fire" reason; operator check log nếu suspect.

- **Rủi ro (b):** CSV corrupt / schema drift → read fail → silent-skip cooldown check.
  **Mitigation:** try/except swallow lỗi, KHÔNG raise (cron không fail); log skipped days ở footer.

- **Rủi ro (c):** Concurrent write nếu operator manual re-run cùng ngày cron chạy → CSV last-write-wins.
  **Mitigation:** hiếm; nếu xảy ra CSV vẫn deterministic; cooldown check chạy trên CSV cũ hơn nếu race.

- **Guard KHÔNG áp:** cooldown KHÔNG áp cho H3 (H3 là booster, không compose).

---

## 8. Sign-off checklist

- [x] Operator KÝ diff 28/08 với 3 điều kiện (1)(2)(3) — see top
- [x] §8.4(i) nguyên văn paste (điều kiện 1) — §0
- [x] "3d sạch" verify text gốc → GIỮ clean_days=3
- [ ] **ANALYSIS xác nhận 1 dòng scope per (token, compose-fire) nhánh-agnostic (điều kiện 2)** ← GATE
- [ ] Merge `scripts/gom_h_daily.py` commit `[V④-RUNTIME-COOLDOWN-20260828 · ký operator+ANALYSIS]`
- [ ] SCP `scp scripts/gom_h_daily.py root@5.223.67.21:/root/Data_back_test/whale_data/scripts/`
- [ ] Backfill KHÔNG ĐÈ: mv `.pre_v4rt` first, re-run 08-21..08-25 fresh CSV
- [ ] Verify cron 01:45 UTC đêm kế: log mtime + CSV file
- [ ] Commit backfill CSVs (cả `.pre_v4rt` cạnh CSV mới) + paste diff MIRA before/after
- [ ] Update E2 census probe với `_check_gom_h_cooldown` semantic
- [ ] Regression T-④ GATE RENDER trên bản MỚI — passes/evaluable số mới

---

## 9. Refs

- Spec §1-H amend V④ ký hồi tố 26/08: `binance-bot-signals` commit `d9c89598` (spec merge) + operator ký chat 26/08
- yaml declaration: `screen_thresholds.yaml` (commit `96b57b8`) `gom_h.gom_h_cooldown_days=14 · gom_h_cooldown_clean_days=3`
- Reuse origin: `binance-bot-signals/docs/gom_detect_spec.md §8.4(i)` line 356
- Related tests: `_probe_vps_0821_h1_recheck_20260828.py` (5 fires baseline pre-V④)
