# RENDER-V2 FIXTURE F1 · EXPECTED · KÝ 29/08 (data 28/08 · post-ruling MỌI-H3=T)

**Status:** ruling ĐÓNG (MỌI-H3=T, A/B RETIRED L-51). Fixture expected viết ngay, chờ Đêm-6 code deploy.

**Data source:** VPS `data/logs/gom_h_daily.log` latest CAMPAIGN-PRE target=2026-08-28 (post-wire smoke-3 · yaml_md5=3d11e572d77a)

**Ref spec:** [gom_detect_spec.md §Render](../../../binance-bot-signals/docs/gom_detect_spec.md) RENDER-V2-20260902 · AMENDMENT-APPEND VERBATIM

---

## F1 · ĐẾM-BẢO-TOÀN (3 số)

| n | source | expected |
|---|---|---:|
| **n_v1** | fires + suppressed (Telegram v1 total rows) | **33** |
| **n_H3_ngoài** | H3=T toàn universe TRỪ (fires ∪ suppressed in v1) | **1** |
| **n_v2** | n_v1 + n_H3_ngoài | **34** |

**Con thứ hai đích danh (ngoài tập alert):** **HUMAUSDT** (`h1_raw=F · h2t01_raw=F · h3_raw=T · vol=11.5× · WALLETSET BROAD-STRESS`).

Fixture F1 print cả 3 số để phần cộng tự khai nguồn (không im).

---

## Pin-row 2 · TAC (STRESS ∧ ret<0)

**Input:** `TACUSDT  [[suppressed:kho]]  conf=LOW (1/4; N/A: -)  H3=F  [SUPPRESSED 3/14 lane=kho]  [WALLETSET: BROAD-STRESS · vol=16.8x ret=-41.0%]`

**Expected khối:** **Khối 4 ⏳ · subgroup `≤1/4 +STRESS`** (dòng riêng cuối khối)

**Expected line format:**
```
🟡 ≤1/4 +STRESS: TACUSDT (ret=-41.0% · vol=16.8×)
```

(Note: TAC không fire hôm nay · suppressed đủ 3/14 · rơi subgroup ≤1/4 +STRESS chứ không rơi khối 🔴 vì khối 🔴 = fires-hôm-nay ∧ STRESS ∧ ret<0)

---

## Pin-row 3 · BTR (H3=T ∧ suppressed cả hai lane)

**Input:** `BTRUSDT  [[suppressed:kho+perp]]  conf=LOW (0/4; N/A: -)  H3=T  [SUPPRESSED 1/14 lane=kho] [SUPPRESSED 1/14 lane=perp]  [WALLETSET: BROAD-STRESS · vol=87.5x]`

**Expected khối:** **Khối 3 🌊** (H3=T thắng khối ⏳ · KHÔNG xuất hiện trong ⏳)

**Expected line format:**
```
BTRUSDT vol=87.5× · BROAD-STRESS · B-P1/P2: đỉnh ≤+60%/0.083 ≤7d rồi −50% ≤14d · kho rút ≥15% = đổi loài
```

(Note: BTR trong tập alert v1 · nhưng H3=T → khối 🌊 · KHÔNG hậu tố `(ngoài tập alert)`; forward_test dòng B-P1 từ yaml.forward_tests.BTR)

---

## Pin-row 4 · MIRA (HIGH trong suppressed)

**Input:** `MIRAUSDT  [[suppressed:perp]]  conf=HIGH (4/4; N/A: -)  H3=F  [SUPPRESSED 4/14 lane=perp]`

**Expected khối:** **Khối 4 ⏳** (suppressed ∧ H3=F · dòng HIGH riêng prefix 🔥)

**Expected line format:**
```
🔥 MIRAUSDT [perp·ghế] ████ 4/4 HIGH  ← nợ số 1
```

(Note: MIRA lâu chưa soi nhất trong tập HIGH-suppressed → hậu tố `← nợ số 1`)

---

## Pin-row 5 · HUMAUSDT (H3=T ngoài tập alert — MỚI post-ruling MỌI-H3=T)

**Input (từ CSV toàn universe · KHÔNG có trong Telegram v1):** `HUMAUSDT` · h1_raw=F · h2t01_raw=F · h3_raw=T · vol=11.5× · WALLETSET BROAD-STRESS

**Expected khối:** **Khối 3 🌊** (H3=T · ngoài tập fire/suppressed · hậu tố `(ngoài tập alert — đang chạy)`)

**Expected line format:**
```
HUMAUSDT vol=11.5× · BROAD-STRESS (ngoài tập alert — đang chạy)
```

(Note: HUMA KHÔNG có trong forward_tests yaml → không in dòng phép-thử)

---

## Fixture pass criteria

1. **F1 3-số print:** `n_v1=33 · n_H3_ngoài=1 · n_v2=34` (khối BANNER hoặc footer)
2. **TAC** đúng khối 4 subgroup ≤1/4+STRESS với ret/vol
3. **BTR** đúng khối 🌊 với dòng B-P1 từ forward_tests · KHÔNG có trong khối ⏳
4. **MIRA** đúng khối 4 dòng HIGH riêng prefix 🔥 với hậu tố `← nợ số 1`
5. **HUMA** đúng khối 🌊 với hậu tố `(ngoài tập alert — đang chạy)` · KHÔNG có forward_test dòng
6. **Đếm khối:** n_v2 = n(khối 0) + n(🟢) + n(🔴) + n(🌊) + n(⏳) + n(👁) = 34 (khối 0 BANNER = 0 rows dữ liệu)
7. **Sort verify khối 🟢:** conf desc → QUIET trước → alphabet (fixture case với ≥3 rows)
8. **Split-safe:** nếu tin > 4096 chars → cắt tại ranh khối ⏳ · trailing tripwire 3 dòng ĐÓNG tin cuối `[GOM-H N/N]`

## Read code từ H3 toàn universe

Render-v2 code phải đọc H3 từ **cột CSV toàn universe** (`data/scratch/gom_h_daily_<date>.csv`), KHÔNG chỉ từ Telegram-v1 rows. Coverage `H3 n_fire` count là source-of-truth cho n_H3_ngoài calc:
- n_H3_toàn = coverage[H3][T] (từ log/CSV)
- n_H3_trong_v1 = count(rows H3=T trong Telegram v1 output)
- n_H3_ngoài = n_H3_toàn − n_H3_trong_v1

Verify data 28/08: coverage H3 n_fire=2 · Telegram v1 chỉ có BTR (1) → n_H3_ngoài=1 · match HUMA ✓.

## Ref

- Spec: [gom_detect_spec.md §Render VERBATIM AMENDMENT-APPEND](../../../binance-bot-signals/docs/gom_detect_spec.md) commit ??? (post-ruling MỌI-H3=T)
- Pre-spec: [render_v2_prespec_20260829.md](render_v2_prespec_20260829.md) (superseded parts merged into spec)
- yaml: [screen_thresholds.yaml `forward_tests` block](../../screen_thresholds.yaml) md5 `7a9d911d4af15d5608893aab62f89baf`
- H3=T verify: `data/scratch/gom_h_daily_2026-08-28.csv` col 6 = 'T' → BTR + HUMA (2 rows)
