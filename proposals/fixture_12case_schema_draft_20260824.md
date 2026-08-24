---
type: fixture-schema-draft
name: 12-case gate conformance fixture (post GOM-RESTRUCT-20260824)
version: v0-schema-draft (24/08/2026)
status: DRAFT SOẠN — CHƯA PIN, chờ ③ đóng (ANALYSIS chốt re-baseline TAG/IDOL/BULLA)
signed_by: PENDING (operator ký cùng gói 4 dòng ①②③④)
---

# 12-case fixture schema — v0 draft (post GOM-RESTRUCT-20260824)

**Ký:** operator ký chat 24/08 (T5). Skeleton chưa pin — chờ ③ đóng (re-baseline).

## Schema (5 điều kiện ANALYSIS)

```json
{
  "type": "gate-conformance-fixture-12case",
  "version": "v0-schema-draft-20260824",
  "generated_at": "<pin-date>",
  "baseline_spec_version": "v4.0-draft (bot-signals 8a96eacc + whale_data afbad16)",
  "spec_source": "D:/Data back test/binance-bot-signals/docs/gom_detect_spec.md",
  "spec_commits": ["8a96eacc", "afbad16", "95e18fe", "940b9ab"],
  "amendments_applied": ["GOM-RESTRUCT-20260824", "C1b rename", "C1 GOM-C off"],
  "runner_side_by_side": {
    "gom_detect": "scripts/gom_scan.py --backtest6",
    "registry_tier_STRICT_feeder": "lib/registry_events.py + BULLA hedge_base_strict feeder (impl pending)"
  },
  "case_result_md5": {
    "BANK_result.txt":     "<md5 pin>",
    "TAG_result.txt":      "<md5 pin>",
    "BAS_result.txt":      "<md5 pin>",
    "BTW_result.txt":      "<md5 pin>",
    "bulla_result.txt":    "<md5 pin>",
    "tut_result.txt":      "<md5 pin>",
    "idol_result.txt":     "<md5 pin>",
    "AKE_result.txt":      "<md5 pin>",
    "BANANAS31_result.txt":"<md5 pin>"
  },
  "config_md5": {
    "screen_thresholds.yaml":                        "<md5 pin>",
    "bot-signals/scanner/screener/thresholds.yaml":  "<md5 pin>"
  },
  "rows": [
    // ── Compose-level (formula check) — 2 rows ──
    {"row": 1,  "token": "_FORMULA", "field": "gom_a_fire",         "expected": "GOM-A = A1 AND A2 AND A3 AND (A4 OR A5)", "provenance": "spec §1 GOM-A"},
    {"row": 2,  "token": "_FORMULA", "field": "hedge_base_strict",  "expected": "HEDGE-BASE-STRICT = B1 AND (B2 OR B3) AND B4 (v4.0 rename gom_b_fire)", "provenance": "spec §1 GOM-B + GOM-RESTRUCT-20260824 §B3"},

    // ── Case-level POSITIVE (chain open/chapter/close) — expected fires ──
    {"row": 3,  "token": "BANK", "episode": "open",     "expected": "Chain mở 07-09 (age gate 14d lifted, lsr_accum onset)", "provenance": "4d0987c initial + verify actual 07-09 chain_open", "TODO": "re-baseline expected 06-29 → 07-09 (age gate delay)"},
    {"row": 4,  "token": "BANK", "episode": "chapter",  "expected": "TBD (crowd_flush 07-02 fires but chain not open — chapter semantic overlap)", "provenance": "T1 evidence + ANALYSIS re-baseline", "TODO": "chờ ANALYSIS chốt chapter semantic"},
    {"row": 5,  "token": "BANK", "episode": "close",    "expected": "TBD (07-13 gap-close vs 07-19 pos_r-close, ANALYSIS chọn)", "provenance": "backtest6 07-13 chain_closed:gom_gap>2d", "TODO": "re-baseline"},
    {"row": 6,  "token": "TAG",  "episode": "open",     "expected": "TBD (T2 evidence: 07-12 A1+A2+A3 pass, A4/A5 fail — TAG-trap ANALYSIS)", "provenance": "T2a first_fail neither A4 nor A5", "TODO": "chờ ANALYSIS ③"},
    {"row": 7,  "token": "BAS",  "episode": "SUPP",     "expected": "07-02→07-15: post_climax dq → GOM không fire", "provenance": "4d0987c stable", "verify": "PASS (dq fired)"},
    {"row": 8,  "token": "BTW",  "episode": "SUPP",     "expected": "06-21→07-05: post_climax dq → GOM không fire", "provenance": "4d0987c stable", "verify": "PASS (dq fired)"},

    // ── Case-level BULLA v4.0 (2 vế) — draft chờ ký ──
    {"row": 9,  "token": "BULLA", "episode": "hedge_base_strict",
     "expected_i":  "gom_day KHÔNG fire toàn window (post-C1b compose = gom_a_fire only, gom_a=F all days)",
     "expected_ii": "hedge_base_strict fire 2026-07-05 first-True; window 07-05→07-09 (5d) + 07-11→07-14 (4d) = 9 days B-path. Registry episode BULLA 06-29→07-17 (freshwatch) nhận tier-STRICT via feeder (spec afbad16, code IMPL 59a7a63, probe BULLA verified).",

     "b_truth_table_04_to_15_july": [
       {"date": "2026-07-04", "b1": false, "b2": false, "b3": false, "b4": true,  "HBS": false},
       {"date": "2026-07-05", "b1": true,  "b2": false, "b3": true,  "b4": true,  "HBS": true,  "note": "*first-True HBS*"},
       {"date": "2026-07-06", "b1": true,  "b2": false, "b3": true,  "b4": true,  "HBS": true},
       {"date": "2026-07-07", "b1": true,  "b2": false, "b3": true,  "b4": true,  "HBS": true},
       {"date": "2026-07-08", "b1": true,  "b2": false, "b3": true,  "b4": true,  "HBS": true},
       {"date": "2026-07-09", "b1": true,  "b2": false, "b3": true,  "b4": true,  "HBS": true,  "note": "dq:slope_dq"},
       {"date": "2026-07-10", "b1": true,  "b2": false, "b3": false, "b4": true,  "HBS": false, "note": "*B3 drop → HBS=F đứt*"},
       {"date": "2026-07-11", "b1": true,  "b2": false, "b3": true,  "b4": true,  "HBS": true,  "note": "resume"},
       {"date": "2026-07-12", "b1": true,  "b2": false, "b3": true,  "b4": true,  "HBS": true},
       {"date": "2026-07-13", "b1": true,  "b2": false, "b3": true,  "b4": true,  "HBS": true},
       {"date": "2026-07-14", "b1": true,  "b2": false, "b3": true,  "b4": true,  "HBS": true},
       {"date": "2026-07-15", "b1": true,  "b2": false, "b3": false, "b4": true,  "HBS": false, "note": "*B3 drop → HBS=F*"}
     ],
     "b_truth_explain":
       "Formula HBS = B1 ∧ (B2 ∨ B3) ∧ B4. B2=F suốt window (funding_pinned KHÔNG bật). "
       "HBS phụ thuộc B3 (absorption). Đứt 07-10 và 07-15: B3 drop → HBS=F. "
       "Window firing: 07-05→07-09 (5d) + 07-11→07-14 (4d) = 9 days total. "
       "'07-05' tự vệ bằng bảng (không lời): B1 first-True + B3 first-True cùng day.",

     "provenance_note":
       "Expected cũ chain_open=2026-07-08 (spec §6 row 7, tiền-v4.0) = ước lượng draft; "
       "K4 probe (4fd5ae4) first-True hedge_base_strict = 2026-07-05 trên snapshot pin; "
       "M1 loại trừ là nguyên nhân (diff ≤0.004).",

     "TODO": "chờ operator ký gói re-baseline ①-⑤"},

    // ── Case-level TUT v4.0 (a-negative) — draft chờ ký ──
    {"row": 10, "token": "TUT", "episode": "a-negative",
     "expected": "GOM-A KHÔNG fire toàn kỳ — A2 fail gLSR>1.1; điểm mù loài captive, văn bản hóa 24/08",
     "provenance": "T4 probe 36/36 days A2 fail, GOM-A 0 fire, g5 1.64-3.40",
     "TODO": "chờ operator ký ②; row cũ 'TUT chapter' giữ ARCHIVED"},

    // ── Case-level IDOL — chờ ANALYSIS ③ ──
    {"row": 11, "token": "IDOL", "episode": "open",
     "expected": "TBD (T2 evidence 07-06: A2 near-miss 1.106 vs 1.1 threshold; IDOL-NEG 4b ANALYSIS)",
     "provenance": "T2a first_fail A2 (1.106 > 1.1 border), IDOL-NEG 4b (21/08)",
     "TODO": "chờ ANALYSIS ③"},

    {"row": 12, "token": "AKE", "episode": "SUPP",
     "expected": "07-08→07-20: decay SUPP → GOM không fire",
     "provenance": "70ed755 stable", "verify": "PASS (dq fired)"},

    // ── Negative bắt buộc (per operator T5 spec) — 4 rows ──
    {"row": 13, "token": "TAG",       "episode": "trap-negative",
     "expected": "TBD (TAG-trap ANALYSIS chat-ký ref pending)",
     "provenance": "twelve_cases TAG-trap", "TODO": "operator relay chat-ký ref exact date"},
    {"row": 14, "token": "IDOL",      "episode": "neg-4b",
     "expected": "TBD (IDOL-NEG 4b ANALYSIS 21/08)",
     "provenance": "IDOL-NEG 4b 21/08", "TODO": "operator relay IDOL-NEG 4b content"},
    {"row": 15, "token": "BANANAS31", "episode": "negative",
     "expected": "PASS (b)-cứng ký 14/08 GOM-C fires=0/54 evaluable + d_pos-block Aug10 + cooldown-block Aug11",
     "provenance": "gom_detect_spec v2.1 (14/08) + _probe_phase3_bananas31_gomc_gate_20260814.py",
     "verify": "existing PASS from v2.1, adjust for v4.0 GOM-C ARCHIVED context"},
    {"row": 16, "token": "TUT",       "episode": "a-negative-supp",
     "expected": "Duplicate của row 10 (TUT-A-NEG) — hoặc merge vào row 10 = 1 row, row 16 removed",
     "TODO": "ANALYSIS quyết row 10 vs row 16 unify"},

    // ── K5 add: feeder tier-STRICT row (status PENDING-BUILD hiển thị, không im) ──
    {"row": 17, "token": "BULLA", "episode": "registry_tier_STRICT_feeder",
     "expected": "Episode BULLA registry 06-29→07-17 (freshwatch) nhận tier-STRICT flag từ feeder GOM-B hedge_base_strict (07-05→07-09 + 07-11→07-14 = 9 days B-path WITHIN episode span). Spec KÝ afbad16 whale_data unhedge_registry_spec §E-R1.",
     "status":   "PENDING-BUILD",
     "note":     "Code IMPL feeder chưa có — lib/registry_events.py chưa đọc GOM-B hedge_base_strict flag. Hiển thị 'PENDING-BUILD' trong fixture output, không im. Chờ operator ký impl scope.",
     "provenance": "K5 fixture row add per TRIAGE-EVIDENCE-20260824 K5"}
  ],
  "gate_semantics": {
    "PASS": "actual event matches expected date/type per row",
    "FAIL": "no matching event OR wrong date/type",
    "SKIP": "row TODO not resolved yet",
    "OVERALL": "PASS all → fixture golden pin; FAIL any → block merge (per L-58 doctrine)"
  },
  "runner": {
    "gom_detect": {
      "cmd": "python scripts/gom_scan.py --backtest6",
      "input": "CASE_DIR (bot-signals docs/case study/*_result.txt) FROZEN",
      "output": "12-case gate table PASS/FAIL per row"
    },
    "registry_tier_STRICT_feeder": {
      "cmd": "python _probe_registry_hbs_feeder_<date>.py  # IMPL PENDING",
      "input": "GOM-B hedge_base_strict output + registry episodes",
      "output": "tier-LOOSE / tier-STRICT assignment per (token, episode)"
    }
  },
  "header": {
    "spec_version":       "v4.0-draft",
    "amendments_applied": ["GOM-RESTRUCT-20260824"],
    "vol_source":         "fapi_k7_fresh",
    "lib_commit":         "<pin>",
    "spec_commit":        "<pin>",
    "case_data_snapshot": "docs/case study/ (bot-signals) — FROZEN calib data"
  }
}
```

## Row list dự kiến (12+4 negative = 16 rows, giá trị trống)

| Row | Token | Episode | Value (chờ pin) | Status |
|-----|-------|---------|-----------------|--------|
| 1 | _FORMULA | gom_a_fire | – | verify code line |
| 2 | _FORMULA | hedge_base_strict | – | verify code line |
| 3 | BANK | open | – | re-baseline 07-09 (không 06-29) |
| 4 | BANK | chapter | – | chờ ANALYSIS ④ |
| 5 | BANK | close | – | re-baseline gap vs pos_r |
| 6 | TAG | open | – | chờ ANALYSIS ③ |
| 7 | BAS | SUPP | ✓ PASS | stable |
| 8 | BTW | SUPP | ✓ PASS | stable |
| 9 | BULLA | hedge_base_strict | – | chờ ký (i)+(ii) v4.0 draft |
| 10 | TUT | a-negative | – | chờ ký ② (v4.0 a-negative draft) |
| 11 | IDOL | open | – | chờ ANALYSIS ③ |
| 12 | AKE | SUPP | ✓ PASS | stable |
| 13 | TAG | trap-negative | – | negative bắt buộc, chờ ANALYSIS ref |
| 14 | IDOL | neg-4b | – | negative bắt buộc, IDOL-NEG 4b 21/08 |
| 15 | BANANAS31 | negative | – | negative bắt buộc, v2.1 baseline |
| 16 | TUT | a-negative-supp | – | negative bắt buộc, unify với row 10? |

## Cross-ref

- T1-T4 evidence: `docs/reports/_gom_gate_triage_20260824.md` + T1/T2/T3/T4 probes
- Spec v4.0-draft: bot-signals `8a96eacc` + whale_data `afbad16`
- C1b rename: `95e18fe`
- C1 GOM-C off: `940b9ab` + `b5c0365`
- L-58 fixture doctrine: `proposals/lessons_pending_batch_V2.md`

## Chờ ANALYSIS ký (T5 pending)

- ① BANK re-baseline (rows 3/4/5)
- ② TUT-A-NEGATIVE row draft (row 10)
- ③ TAG/IDOL deep-dive verdict (rows 6/11 + rows 13/14 negative)
- ④ chapter semantic (row 4 crowd_flush 07-02 vs chain-open 07-09 overlap)
- BULLA v4.0 draft (row 9 vế i+ii)

Sau ③ đóng → skeleton pin → fixture golden commit riêng.
