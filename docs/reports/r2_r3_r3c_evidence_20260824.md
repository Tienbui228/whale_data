# R2 + R3 + R3-c evidence report (TRIAGE-CLOSE-20260824)

Backfill sổ hổng — R2/R3/R3-c chỉ có báo cáo chat trước đây, nay pin file trong git.

Stack sha lineage:
- RE-PIN-20260824 (α): `69b2e2d`
- R1 BACKTEST_GATE ②④: `434f954`
- ⑨-FIX + W1-W3 sweep: `330d683`
- ⑨-FIX grep-audit type-warning: `2212a49`

---

## R2 — ROOT-CAUSE _result.txt LSR slice generator

**Kết luận 1 dòng:** _result.txt slice LSR generator **KHÔNG CÓ** — 12 file curated ONE-OFF tại commit `b0b4cff4` (bot-signals, 28/07/2026) đánh dấu "READ-ONLY" trong commit msg ("12 calibration files (BOM de-duplication set, READ-ONLY)"). Không có script write vào `docs/case study/`, không có cron regen. Generator "còn sống và còn dùng cho calib export?" = **KHÔNG (dead)**.

**Bằng chứng:**
- `git log --diff-filter=A --all -- "docs/case study/BANK_result.txt"` → chỉ 1 commit `b0b4cff4`
- `grep 'write.*result\.txt|f\.write.*RATIO|open.*result.*'w'' D:\Data back test\binance-bot-signals` → 0 kết quả
- Grep `--- RATIO|globalLSR|topLSR_pos` trong .py bot-signals → chỉ PARSERS (parse_result_file, replay.py, screen_daily.py), không writer
- Commit `b0b4cff4` msg verbatim: `"docs/case study/: 12 calibration files (BOM de-duplication set, READ-ONLY)"`

**Implication cho R4 REGEN:** phải TỰ SINH bằng script mới — thay 4 cột trong block `--- RATIO <TOKEN>USDT ---` bằng data từ store canonical (`data/export/freshwatch_daily_2026-*.csv` cột `lsr_pos_r/lsr_acc_r/lsr_global_r/taker_ratio`), giữ nguyên format 4-cột (topLSR_pos, topLSR_acc, globalLSR, takerRatio).

---

## R3 (K4-PROVENANCE) — bảng lệch OLD vs NEW HBS BULLA

**(a) K4 probe cũ đọc từ đâu:** `_probe_bulla_hbs_date_20260824.py` (archived at [scripts/archive/](../scripts/archive/) sau grep-audit fix). Đường-đọc:

- Line 34: `case_dir = BOT / "docs" / "case study"` (BOT = `D:/Data back test/binance-bot-signals`)
- Line 35: `list(case_dir.glob("BULLA*_result.txt")) + list(case_dir.glob("bulla*_result.txt"))`
- Line 45: `funding, oi, ratio, klines = parse_result_file(fpath)` — parse `bulla_result.txt`

→ **K4 đọc `bulla_result.txt` (không phải store)**

**(b) So bảng OLD (_result.txt) vs NEW (store) — first version R3 CÓ BUG:**

R3 v1 báo `NEW = None` (không HBS ngày nào). Nguyên nhân: probe key mapping sai (`topLSR_pos` thay vì canonical `lsr_pos` per replay.py:201). Sau fix (R3-c), bảng thực:

| date | OLD HBS (bulla_result.txt) | NEW HBS (store freshwatch) | diff? |
|---|:---:|:---:|:---:|
| 07-04 | F | F | |
| 07-05 | **T** *first* | F | ★ |
| 07-06 | T | F | ★ |
| 07-07 | T | F | ★ |
| 07-08 | T | **T** *first store* | |
| 07-09 | T | F | ★ |
| 07-10 | F | F | |
| 07-11 | T | T | |
| 07-12 | T | T | |
| 07-13 | T | T | |
| 07-14 | T | T | |
| 07-15 | F | F | |

**first-True HBS:** OLD = 07-05  →  NEW = **07-08** (không phải None). Vẫn CHÊNH 3 ngày — vẫn triggers DỪNG rule.

---

## R3-c localize — chân dead + display bug + fail-open

### (0)(a) div3 display bug — DISPLAY ONLY

Probe R3-c line 138: `return acc / pos if pos > 0` — **nghịch đảo** canonical (`avg3(lsr_pos)/avg3(lsr_acc)` per [signals.py:106-124](../scanner/screener/signals.py#L106-L124) + [hedge_episode.py:45-51](../lib/hedge_episode.py#L45-L51) `calc_div`).

Displayed div3=2.818 for 07-05 = 1/0.355. Canonical value = 0.355 (≈ K4 M1 spec 0.341).

**HBS/B1-B4 decisions KHÔNG ẢNH HƯỞNG** — eval_gom nội bộ dùng canonical `_div_ratio`. Bug chỉ ở display column của probe archive. Fixed trong R3-c v2 archive (sha this commit).

### (0)(b) B1 fail-OPEN với lookback thiếu — PROD BUG (fixed at ⑨-FIX 330d683)

B1 code trước fix — [gom_scan.py:128-132](../scripts/gom_scan.py#L128-L132):
```python
b1 = all(hedge_structure(days, j, cfg) for j in range(max(0, i - hedge_lb + 1), i + 1))
```
Với BULLA store 06-29 (i=2, hedge_lb=7): `range(max(0,-4), 3) = range(0,3)` → chỉ 3 iterations, `all()` returns True nếu 3d pass.

**Fix (330d683):** `_warmup_b1 = i < hlb-1 → b1=False + hedge_base_strict="N/A-WARMUP"`.

### Chân dead trong BULLA 06-29→07-15 STORE (bảng đầy đủ)

Formula HBS = B1 ∧ (B2 ∨ B3) ∧ B4. B2=F suốt window (funding_pinned không bật). Post ⑨-FIX bảng:

| date | i_st | b1 | b2 | b3 | b4 | HBS | note |
|---:|---:|:---:|:---:|:---:|:---:|:---:|---|
| 06-29 | 2 | **F** (warmup) | F | F | T | N/A-WARMUP | B1 warmup (i=2<6) |
| 06-30 | 3 | **F** (warmup) | F | F | T | N/A-WARMUP | |
| 07-01 | 4 | **F** (warmup) | F | F | T | N/A-WARMUP | |
| 07-02 | 5 | **F** (warmup) | F | F | T | N/A-WARMUP | |
| 07-03 | 6 | T | F | F | T | F | *B3 dead |
| 07-04 | 7 | T | F | F | T | F | *B3 dead |
| **07-05** | 8 | T | F | **F** | T | **F** | ***B3 dead** |
| 07-06 | 9 | T | F | F | T | F | *B3 dead |
| 07-07 | 10 | T | F | F | T | F | *B3 dead |
| **07-08** | 11 | T | F | **T** | T | **T** | *first STRICT store |
| 07-09 | 12 | T | F | F | T | F | *B3 dead |
| 07-10 | 13 | T | F | F | T | F | *B3 dead |
| 07-11 | 14 | T | F | T | T | T | |
| 07-12 | 15 | T | F | T | T | T | |
| 07-13 | 16 | T | F | T | T | T | |
| 07-14 | 17 | T | F | T | T | T | |
| 07-15 | 18 | T | F | F | T | F | *B3 dead |

**Chân dead: B3** (absorption). Pre-fix bảng có b1=T ngày 06-29→07-02 (fake), post-fix warmup đúng. Store HBS-True: 07-08, 07-11, 07-12, 07-13, 07-14 (**5 days**, vs _result.txt 9 days).

---

## Raw diff BULLA 07-05 STORE vs _result.txt

|  | Store freshwatch | _result.txt | Δ |
|---|---:|---:|---:|
| pos_r | 1.8521 | 1.77 | +0.082 (+4.6%) |
| acc_r | 4.7537 | 4.59 | +0.164 (+3.5%) |
| gLSR  | 4.6433 | 4.51 | +0.134 (+2.9%) |
| taker_ratio | 0.9755 | 1.10 | −0.124 |

Data drift 3-5% (đồng magnitude BANK 07-02 K3-fix earlier). B3 (absorption) nhạy — flip T→F tại threshold.

## Store data range

| source | min | max | n rows |
|---|---|---|---:|
| STORE (freshwatch) | 06-27 | 08-23 | 55 |
| _result.txt (bulla_result.txt) | 06-16 | 07-21 | 36 |

Store thiếu 11 ngày history đầu (06-16→06-26) → hedge_structure lookback ăn ngay warmup ở 06-27→07-02 (fixed post ⑨).

---

## R3-DIRECTION per operator ký

Operator ký (β) + source-lock ANALYSIS ②: hai họ fixture, ba điều kiện cứng:
1. divergence_note bắt buộc
2. hội tụ đo sau regen, residual hợp lệ duy nhất = rìa trái
3. N/A-WARMUP (điều kiện ⑨)

Row 9 434f954 gắn nhãn [PENDING-REGEN] ngay (số sẽ đổi khi taker+LSR regen).
