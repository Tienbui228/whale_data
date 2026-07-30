# AGENT LOG — FreshWatch

---

## SESSION 2026-07-30 — P1.5 AUDIT + FIX

**Operator:** Tien
**Agent model:** claude-sonnet-4-6
**Nhiệm vụ:** Trace + fix 3 red flag (BANK row 6, fn=1 mapping, tape design) + cron + alpha guard.

---

### [B1] Án BANK row 6 — ROOT CAUSE + FIX: PASS

**Root cause:** Backfill 35 dòng (Jun09→Jul29) được save vào `CASE_BANK_NEW.xlsx` (file mới tạo trong session backfill 29/07) thay vì `CASE_BANK.xlsx`. CASE_INDEX vẫn trỏ `CASE_BANK.xlsx` → case_daily first-run đúng file INDEX nhưng sai canonical → ghi Jul29 vào row 6 của file cũ chỉ có 4 dòng.

**Bằng chứng số:**
- `CASE_BANK.xlsx`: max_row=7, date rows = Jul26-Jul29 (4 dòng), taker col5 row6 = 0.5046
- `CASE_BANK_NEW.xlsx`: max_row=37, date rows = Jun09-Jul29 (35 dòng), col O row28 = 1.0905 ✓

**Fix đã áp dụng:**
1. Merge taker=0.5046 (comment: "fn=1 (native_1d) — taker từ Zone-A-agg (ledger_v2 CAMPAIGNS/BANK_20260720)") vào CASE_BANK_NEW.xlsx row 37 col 5
2. `CASE_BANK.xlsx` → `CASE_BANK_PRE_BF_20260730.xlsx` (backup)
3. `CASE_BANK_NEW.xlsx` → `CASE_BANK.xlsx` (canonical)
4. Verify: 35 date rows, last=Jul29, taker=0.5046, SKIP_EXISTS Jul29 ✓, row 38 cho Jul30 ✓

**Script:** `scripts/_fix_bank_merge.py --apply`

---

### [B2] Án mapping fn=1 (0.5046) — PASS (mapping đúng)

**Vị trí 0.5046:** CASE_BANK.xlsx (cũ) row 6 **col 5 (taker_buy_pct)** — đúng column, đúng metric.

**Kiểm tra chéo:**
- col 5 (taker_buy_pct) = 0.5046 ← Zone-A-agg CAMPAIGNS/BANK_20260720 ✓ đúng metric
- col 15 (lsr_pos_r) = 1.3307 ← export CSV ✓ đúng metric  
- col 16 (lsr_acc_r) = 0.8567 ← export CSV ✓ đúng metric
- col 17 (lsr_global_r) = 0.9384 ← export CSV ✓ đúng metric
- fn=1 chỉ thay taker, KHÔNG ảnh hưởng gLSR/pos/acc ✓

**Fix phòng ngừa:** Thêm `_ASSERT_COL_METRIC` assertion vào case_daily.py (runs tại import time) — fail-fast nếu ai mapping sai metric sau này.

---

### [B3] Tape collector — ONE-SHOT: HOÃN

**Kết luận:** `collect_tape.py` là ONE-SHOT (asyncio.run rồi exit). Gate REST `/spot/trades?from=X&to=Y` có thể chỉ trả latest N trades → chạy 01:15 UTC sẽ aggregate vài phút cuối ngày = CVD/takerBUY% rác.

**Hành động:** HOÃN tape — KHÔNG thêm vào cron. Cần thiết kế lại thành daemon hoặc polling interval ngắn (buffer trades cả ngày, aggregate lúc 00:00 UTC rollover). Đây là change-set riêng.

**CẦN OPERATOR:** Chọn hướng triển khai daemon (systemd trên VPS theo mẫu oibot) hay polling loop + xem trade-rate thực tế BR@Gate.

---

### [B4] Alpha guard collect_alpha_spot.py — PASS

**Bằng chứng code** (`scripts/collect_alpha_spot.py` hàm `_parse_alpha_kline_row`):
- Đọc: k[1] open, k[2] high, k[3] low, k[4] close, k[5] base_vol, k[7] quote_vol, k[8] n_trades
- **KHÔNG đọc** k[9] (taker_buy_base_vol) hoặc k[10] (taker_buy_quote_vol)
- Guard comment: "GUARD: DO NOT read klines[9] ... For BSC-bridged tokens these fields always equal klines[5]/klines[7] (100% taker buy = broken API field)"
- Store values: `taker_buy_base_vol=nan, taker_buy_quote_vol=nan, taker_buy_pct=nan, taker_abstain=True`
- Sổ rác không vào store ✓

---

### [B5] Cron VPS — PASS (2/3)

**Export job (export_freshwatch_daily.py):** 00:50 UTC ← dependency của case_daily

**Đã thêm vào VPS crontab (`5.223.67.21`):**
```
05 01 * * * cd /root/Data_back_test/whale_data && .venv/bin/python3 scripts/collect_spot_daily.py >> data/logs/collect_spot_daily.log 2>&1
10 01 * * * cd /root/Data_back_test/whale_data && .venv/bin/python3 scripts/collect_alpha_spot.py >> data/logs/collect_alpha_spot.log 2>&1
```

**Thứ tự phụ thuộc:** export 00:50 → spot_daily 01:05 (+15min) → alpha_spot 01:10 (+5min) ✓

**Tape:** KHÔNG thêm (hoãn per B3).

**case_daily:** KHÔNG trong VPS crontab — script có Windows path (`D:\...`), phải chạy Windows Task Scheduler. Operator cần thiết lập Task Scheduler job 02:00 UTC.

**Scripts deployed to VPS:** `collect_spot_daily.py`, `collect_alpha_spot.py`, `whale_collector/storage/paths.py` (updated với `spot_klines_partition_path`)

**Crontab backup:** `/root/archive/crontab_backup_2026-07-30.txt`

---

### [B6] Bài học mới — L-26, L-27

- **L-26** (GHI NHẬN): Backfill save nhầm file → canonical phải đúng tên trong INDEX
- **L-27** (GHI NHẬN): fn=1 fallback chỉ taker_buy_pct; assert guard đã vào case_daily.py

---

## SESSION 2026-07-30 — SETUP SKIP-PERMISSIONS + NANSEN LOCK

**Operator:** Tien
**Agent model:** claude-sonnet-4-6
**Nhiệm vụ:** Chuyển sang chế độ skip-permissions an toàn: khoá Nansen tầng env, cập nhật CLAUDE.md, ghi điểm khởi động.

---

### [B1] Nansen ENV Lock — PASS

**Biến đã rename (tên, không ghi giá trị):**
- `NANSEN_API_KEY` → `NANSEN_KEY_LOCKED`
- Vị trí: `D:\Check onchain fresh wallets\.env` dòng 21
- Windows User/System env: KHÔNG tồn tại biến NANSEN (đã kiểm tra)

**Code đọc NANSEN_API_KEY (KHÔNG sửa — để fail-fast tự nhiên):**
- `botaccum.py:116` — `os.getenv("NANSEN_API_KEY")`
- `core_nansen.py:20` — `os.getenv("NANSEN_API_KEY", "")`
- `core_nansen.py:362` — guard `if not NANSEN_API_KEY: raise RuntimeError`
- `m1_check.py:43` — `os.getenv("NANSEN_API_KEY")`
- `probe_botaccum_v3.py:29` — `os.getenv("NANSEN_API_KEY")`
- `probe_flows.py:21` — `env.get("NANSEN_API_KEY", "")`
- `probe_window.py:27` — `env.get("NANSEN_API_KEY", "")`

**Verify:** `_probe_nansen_lock.py` chạy tại repo root → `NANSEN_API_KEY: None` ✓ `NANSEN_KEY_LOCKED: SET` ✓ → **PASS**

---

### [B2] CLAUDE.md — PASS

Ba dòng KỶ LUẬT thêm vào mục KỶ LUẬT:
1. Skip-permissions + Nansen env lock rule
2. Bash discipline (lệnh trần, không chain, không python -c)
3. Nhắc tầng HUMAN (thresholds.yaml, verdict CASE)

---

### [B3] Task Scheduler — N/A (không có task claude)

**Đã kiểm tra:** Tasks FreshWatch, FreshWatch-SnapshotWriter, WhalePhaseScanner — không có task nào chạy `claude`.

**Dòng lệnh khởi động thủ công cho operator:**
```
cd "D:\Data back test\whale_data"
claude --dangerously-skip-permissions
```
Claude path: `C:\Users\Hello\AppData\Roaming\npm\claude.cmd`

---

### [B4] settings.local.json — GHI CHÚ (schema block)

`_note` field bị schema validation block (settings.json không cho additionalProperties có tên lạ).
Ghi chú thay thế trong agent_log này: **chạy chính bằng `--dangerously-skip-permissions`; settings.local.json là fallback khi ai chạy không flag.**

---

### [B5] Kết quả tổng

| Bước | Trạng thái | Ghi chú |
|------|-----------|---------|
| 1a/b Rename env var | PASS | `.env` FreshWatch repo |
| 1c List code đọc key | PASS | 7 file:line liệt kê trên |
| 1d Verify probe | PASS | NANSEN_API_KEY → None |
| 2 CLAUDE.md | PASS | 3 dòng KỶ LUẬT thêm |
| 3a Task Scheduler | N/A | Không có task claude |
| 3c Dòng lệnh operator | PASS | Ghi trên |
| 4 settings.json note | PARTIAL | Schema block _note → ghi vào log |
| 5 agent_log.md | PASS | Bài này |

---

## SESSION 2026-07-29

**Operator:** Tien  
**Agent model:** claude-sonnet-4-6  
**Nhiem vu:** T1 verify P1 + commit · T2 fix R1 join · T3 canh TAG+BR 29/07 · T4 ton dong · T5 cooldown packet

---

### [T1] P1 Screener Verify — FAIL (AN DA XU LY)

**Lenh chay:** `_probe_p1_deploy.py` — SSH VPS check file mtime + service start + trigger code

**Chan doan dung (sua lai):** AN BAN DAU SAI HUONG.
- `oi_scanner.py` mtime: **2026-07-29 02:16 UTC** — deploy THANH CONG
- oibot service start: **2026-07-29 06:10 UTC** (PID 2217202)
- OLD PID 1854765 dang chay luc 00:03-00:04 UTC (KHONG co screener code)
- Window 00:05 UTC da bi miss boi ca 2 ly do: (1) code moi chua tren VPS luc 00:05, (2) service chua restart

**Nguyen nhan chinh xac:** Deploy Item 5 thuc thi SAU window 00:05 UTC (deploy 02:16, restart 06:10). KHONG phai exception swallow. Old code khong co `_m5_structural_pass` / `_snapshot_writer`.

**Trang thai hien tai:** Code moi dang chay (PID 2217202 tu 06:10 UTC). Trigger dung:
```python
if (_today_utc != self._screener_snapshot_date
        and _now_utc.hour == 0 and _now_utc.minute >= 5):
    self._snapshot_writer(symbols, tickers)
```
**Jul 29 snapshot: MAT** (missed window — khong the recover). **Jul 30 00:05 UTC se la first capture.**

**Lenh xac nhan:** Hai function `_snapshot_writer` (line 3290) va `_m5_structural_pass` (line 3424) da co trong code VPS hien tai.

**Ket luan T1:** Root cause = deploy + restart sau window. Khong can operator intervention. Theo doi Jul 30 00:05-00:10 UTC de confirm first `daily_2026-07.csv` duoc ghi.

---

### [T2] Fix R1 Join ledger_daily.py — DONE

**Lenh chay:** `_fix_r1_ledger.py` (download patch upload + live run)  
**Root cause xac nhan:** CAMPAIGNS sheet luu bare symbol ('TAG'), export_data keyed by 'TAGUSDT' — 28/28 campaigns bi 0-match.  
**Patch ap dung** (lines 623-626 tren VPS):
```python
# TRUOC (lines 623-624):
sym_upper = symbol.upper()
sym_rows = export_data.get(sym_upper, [])

# SAU (lines 623-626):
sym_upper = symbol.upper()
# R1 fix: ledger stores 'TAG', export stores 'TAGUSDT' — normalize one-way
_exp_key = sym_upper if sym_upper in export_data else (sym_upper + "USDT")
sym_rows = export_data.get(_exp_key, [])
```
**Ket qua live run 07:36:18 UTC:**
- `zone_a: OK (ok (28 rows updated, 0 no data))` — truoc fix: 28 no data
- `report_2026-07-29.xlsx` regenerated, 1 change detected
- Backup: `/root/Data_back_test/whale_data/ledger_daily.py.bak_before_r1fix`

**Backfill Zone A:** Zone A la snapshot (tinh aggregate tu t0_date den today). Live run Jul 29 da tu dong backfill — `_compute_zone_a` tinh tat ca export rows tu t0_date (2026-07-20) den 2026-07-29. Khong co `--date` flag; mot lan chay la du.

**2 sample rows xac nhan (CAMPAIGNS):**
- TAG: lsr_pos_r=1.5221, acc_r=1.2090, div_r=1.2589, oi_usd=11172261, data_ok=yes, zoneA_updated=2026-07-29T07:36:18Z
- BANK: div_r=2.4335, data_ok=yes, zoneA_updated=2026-07-29T07:36:18Z
- CLO: div_r=0.5550, state_manual=suppressed, data_ok=yes

**Ket luan T2:** PASS — 28 campaigns Zone A da duoc cap nhat dung, backfill implicit qua aggregate tu t0_date.

---

### [T3] Handover Chot 29/07 (sua lai)

**SUA AN 30/07:** Buoi sang tao CSV trong docs/case_files/data/ = TAI PHAM. DAILY song trong CASE_<TOKEN>.xlsx.
**Hanh dong sua:** Git rm 2 CSV, them rule vao CLAUDE.md, append row 31 vao CASE_TAG.xlsx DAILY, fill missing fields vao CASE_BR.xlsx row 67 (G/H/I f_min/max/n, khong dung data operator).

**Files cap nhat:**
- `CASE_TAG.xlsx` DAILY row 31 (2026-07-29): O=1.6204, P=1.3719, Q=1.8129 fn=1, L=11172261, formulas R/S/T/U/V copied+incremented tu row 30, note AN31 flag gLSR suspect
- `CASE_BR.xlsx` DAILY row 67: G=0.00017978, H=0.00017978, I=1 them vao (khong override du lieu operator: B=0.146, L=4634000, N=FLOOR, O=1.661, P=1.49, Q=1.944, AK/AL/AN/AO)

**TAG 29/07 — S1 Handover:**
| Metric | Value | Moc | Status |
|--------|-------|-----|--------|
| pos_r | 1.6204 | — | — |
| acc_r | 1.3719 | — | — |
| div_raw | 1.1811 | — | — |
| div_avg3 | 1.2844 | >=1.5 | MISS |
| gLSR | 1.8129 | <=1.1 | MISS |
| OI | 11,172,261 USD | >=12M | <12M |
| funding_n | 1 (low_conf=True) | 6 | PEND |
| oi_cycle_pos | PEAK | — | — |
| **ARM check** | **div_avg3 < 1.5 AND gLSR > 1.1** | — | **FAIL** |

ARM FAIL — chua du dieu kien tai-ARM.  
tx cum 6 vi: PENDING (can BscScan 0-credit, nguon ngoai agent).

**BR 29/07 — S1 Handover:**
| Metric | Value | Moc | Status |
|--------|-------|-----|--------|
| pos_r | 1.6609 | floor 1.661 | tai floor |
| acc_r | 1.4900 | — | — |
| gLSR | 1.9438 | sap tu 1.94 | TREN nguong |
| OI | 3,782,263 USD | — | — |
| funding_n | 1 (low_conf=True) | 6 | PEND |
| funding_avg | 0.00017978 | — | FLOAT |
| kho 6% | PENDING | — | can on-chain |
| bid_wall/ask_wall | PENDING | — | CAN OPERATOR |

---

### [T4] Ton dong kiem tra — DONE

**T4.1 Task #2 git log:** Commit `2172bbb` — "docs: case tracker v1.1 + 4 xlsx + CASE_TAG legend" — xac nhan 4 xlsx + case_tracker.md + CASE_TAG legend da duoc commit.

**T4.2 missing_jul.md:** `missing_july_2026.txt` ton tai local (522 symbols co >= 1 missing day). Tao `docs/reports/missing_jul.md` tu file nay. Cluster chinh: Jul 24-26 (3 ngay, anh huong gan toan bo 525 symbols). 7 symbols hoan toan vang mat khoi July.

**T4.3 Cleanup exemption (_cleanup_old_data):** Xac nhan trong `oi_scanner.py` lines 906-954:
- `data/pending/` — 7-day cutoff, EXEMPTION: current-month files never purged
- `data/signals/` — by-month, purge months < cutoff_month
- `data/results/` — by-month, purge months < cutoff_month
- **`data/screener/`** — **COVERED** voi separate `keep_months=12` retention window (doc lap voi 7-day pending)

Ket luan T4: Tat ca items done. Cleanup bao phu day du screener + pending exemption chinh xac.

---

### [T5] Cooldown Review 4 token — DRAFT DONE

**Lenh chay:** `_run_t5.py` probe VPS export + CAMPAIGNS sheet  
**File tao:** `docs/reports/cooldown_review_2026-07-30.md`

**Tom tat de xuat agent (verdict = CAN OPERATOR):**

| Token | div_raw 29/07 | gLSR 29/07 | OI trend | De xuat agent |
|-------|--------------|------------|----------|---------------|
| PARTI | 1.63 (trending down tu 3.42) | 0.854 (<1) | -57% | Xem xet UNLOCK |
| EVAA  | 0.849 (da dao chieu) | 1.746 | -72% | De xuat UNLOCK |
| CLO   | 0.510 (dao chieu sau) | 1.401 | stable | De xuat UNLOCK |
| BLUAI | 0.633 | 2.532 (HOT!) | stable | REMAIN COOLDOWN |

**Chua hoan thien:** `oi_vs_med14` cho 3 ungvien UNLOCK — can window 14 ngay day du (Jul 24-26 missing). Operator can verify tu VPS signals.py truoc khi unlock.

---

### SO SANH NGUON BR OI 29/07

**AN SO SANH:** CASE_BR row 67 L=4,634,000 (operator entry) vs export probe = 3,782,263. Chenh ~22%.
- Khong tu ghi de — operator co nguon rieng (possibly spot+perp aggregate hoac diem ngay khac).
- Ghi an, khong tu chon.

### TAG raw 29/07 (so sanh nguon)

| Metric | Export (probe) | CAMPAIGNS Zone A |
|--------|----------------|-----------------|
| pos_r | 1.6204 | 1.5221 (aggregate) |
| acc_r | 1.3719 | 1.2090 (aggregate) |
| div_raw | 1.181 | 1.2589 (aggregate) |
| gLSR | 1.8129 (fn=1 SUSPECT) | 1.6059 (aggregate) |
| OI | 11,172,261 | 11,172,261 (match) |

**gLSR SUSPECT:** 1.2978 (Jul28, fn=1) → 1.8129 (Jul29, fn=1) — both single-snapshot. Khong tin duoc.
**acc_r bat nguoc:** Jul28 acc_r=0.9988 → Jul29 acc_r=1.3719, keo div_raw tu 1.597 xuong 1.181.
**div_avg3(29)** = (1.075+1.597+1.181)/3 = **1.284** (confirm, match operator number 1.344 la cua Jul28).

### CAN OPERATOR

1. **T1:** Confirm Jul 30 00:05-00:10 UTC — `daily_2026-07.csv` ghi dung. Neu khong → o khac ngoai deploy.
2. **T3 TAG:** tx cum 6 vi (BscScan), bid_wall/ask_wall Gate snapshot (bat dau tu 30/07 theo note xlsx).
3. **T3 BR:** kho 6% chuyen dong (on-chain); verify OI 4.634M vs 3.782M nguon nao dung.
4. **T5:** Phan verdict cooldown tu packet. EVAA → WATCH neu unlock (khong phai NO_SETUP). Verify oi_vs_med14 VPS signals.py.
5. **BLUAI nhan 'HOT':** sua nhan trong cooldown_review — 'gLSR cao = crowd long day = wrong-side' thay vi 'hot tier A'.

---

### TAG — Verdict trang thai (operator chot 29/07)

**Invalidate theo nghia den: CHUA BAN.** Ve "gia dung" FAIL — ret_3d = -9.87%, gia dang roi that (0.001348 → 0.001295 → 0.001215). Hard floor 0.00072: con xa.

**Cau hinh thuc te:** Gia -9.87%/3d + gLSR bo 1.30→1.61 + acc_r bat 0.999→1.372 = crowd long nap vao duong gia xuong (bat dao). Khong phai wash-by-rally (crowd roi khi gia tang). Gan nhat voi pha fade hau-stealth-fire: fire 07-28 margin mong, gia fade, crowd sai phia nap vao.

**Ket luan trang thai: TAG WATCH ha nhiet.**
- Cach tai-ARM xa hon: can div_raw >= 1.72 hai ngay lien, trong khi raw vua sap ve 1.18
- Dieu kien can truoc moi ho so tai-ARM: gLSR quay ve <=1.1 (lua long moi phai bi rua)
- **Diem canh giac:** neu gia NGUNG roi ma gLSR van >1.5 → ca hai ve invalidate cung thoa → canh chinh xac to hop do tung ngay

**Trong so tang:** tx cum 6 vi ma 6 vi van hold trong pha fade + crowd sai phia = kich ban gom-tiep con song. Bat ky redeposit nao = dong an khong cho gia.

---

### BR OI Canonical — Quy uoc chot (30/07)

**Confirmed:** OI daily canonical = export 00:00 UTC (Binance openInterestHist sumOpenInterestValue).
- Export 3,782,263 = snapshot ~00:00 UTC Jul 29 → ghi vao DAILY
- Operator 4,634,000 = snapshot intraday (Coinglass/GMGN luc nhin) → ghi EVENTS kem timestamp, khong vao DAILY
- Hieu qua: CASE_BR row 67 L = 4,634,000 la EVENTS entry, khong phai DAILY canonical. Dinh luat #9 tinh tren floor theo chuan export (3.78M); pos_r 1.661 tai floor van dung.

**Quy uoc da vao CLAUDE.md:** "OI daily canonical = export 00:00 UTC; so intraday chi ghi EVENTS kem timestamp, khong vao cot DAILY."

---

### Checklist sang mai (Jul 30, sau 07:10 ICT)

- [ ] **Verify P1 snapshot:** SSH VPS → kiem `data/screener/daily_2026-07.csv` 526 dong + TAGUSDT fn=6 → PASS → goi agent commit P1
- [ ] **Cooldown verdict 4 con:** PARTI/EVAA/CLO (UNLOCK → dien verdict sheet CASE). EVAA unlock → WATCH (re-staging). BLUAI: REMAIN. Verify oi_vs_med14 VPS signals.py truoc khi ghi verdict.
- [ ] **Viec tay TAG:** tx cum 6 vi (BscScan) — trong so da tang sau fade + crowd sai phia
- [ ] **Viec tay BR:** bid/ask wall Gate snapshot ngay 2 (30/07)

**Sau P1 commit:** case_daily + BscScan watcher (nho hon, khep vong tu van hanh) → P2 session tuoi rieng.

---

*Cap nhat: 2026-07-29 → operator chot 30/07*

---

## SESSION 2026-07-30 — LESSONS consolidation

**Operator:** Tien
**Agent model:** claude-sonnet-4-6
**Nhiem vu:** Them cot MM vao CASE_INDEX LESSONS, tong hop 12 lesson moi tu 4 nguon, sinh docs/lessons_learned.md, cap nhat CLAUDE.md

---

### [L-CON] LESSONS Consolidation — DONE

**Lenh chay:** openpyxl update CASE_INDEX.xlsx + Write lessons_learned.md + Edit CLAUDE.md

**Ket qua so:**
- CASE_INDEX.xlsx sheet LESSONS: them cot H = "MM" (header), tat ca o de trong (operator dien)
- Append 12 lesson moi: L-14 den L-25
- Tong sheet LESSONS sau consolidation: 25 bai hoc (L-01 to L-25)
- docs/lessons_learned.md: 18,482 bytes, 4 muc (I.SIGNAL-LEVEL 11 bai / II.MM-LEVEL 4 / III.DATA-QUALITY 7 / IV.PROCESS 3)
- CLAUDE.md: them 1 dong cuoi KY LUAT: "lessons_learned.md la view sinh tu sheet LESSONS..."

**Nguon 4 du lieu da tich hop:**
1. 13 lesson hien co (L-01 to L-13) — giu nguyen, chi them cot MM
2. twelve_cases_ref: L-14 (wash-by-crash), L-15 (bai-probe), L-16 (M2 dao dau), L-17 (squeeze-nhien-lieu)
3. u50_verdicts: L-18 (§2 phase check), L-19 (§3 phase-context filter), L-20 (§6 tu-ha-cap)
4. An topic 30/07: L-21 (OI canonical), L-22 (fn=1 fallback), L-23 (TAG fire-fade), L-24 (hai-window), L-25 (mot-nha-mot-data x2)

**Phan loai moi:**
| Muc | Lesson |
|-----|--------|
| I. SIGNAL-LEVEL | L-01, L-03, L-04, L-06, L-11, L-14, L-15, L-16, L-17, L-18, L-23 |
| II. MM-LEVEL | L-05, L-07, L-08, L-12 |
| III. DATA-QUALITY | L-09, L-10, L-20, L-21, L-22, L-24, L-25 |
| IV. PROCESS | L-02, L-13, L-19 |

**Trang thai moi:**
- GHI NHAN (can theo doi them): L-04, L-06, L-07, L-14, L-15, L-16, L-17, L-18, L-19, L-23
- DA VAO CLAUDE.md: L-20, L-21, L-22, L-24, L-25
- Da co trong spec/tracker truoc: L-01, L-02, L-03, L-05, L-08, L-09, L-10, L-11, L-12, L-13

*Cap nhat: 2026-07-30*

## SESSION 2026-07-30 — case_daily digest

**Target date:** 2026-07-29  **Run:** 2026-07-30 02:02 UTC  **dry_run:** False

### §1 Handover digest

| Token | Status | row | lsr_pos_r | lsr_acc_r | div_raw | taker_buy_pct | f_avg | f_n | OI_USD | fn=1 | Zone-A src |
|-------|--------|-----|-----------|-----------|---------|---------------|-------|-----|--------|------|------------|
| BANK | OK | 6 | 1.3307 | 0.8567 | 1.5533 | 0.5046 | -0.000268 | 1 | 25,365,666 | YES | Zone-A-agg (ledger_v2 CAMPAIGNS/BANK_20260720) |
| TAG | SKIP_EXISTS | — | — | — | — | — | — | — | — | — | — |
| BR | SKIP_EXISTS | — | — | — | — | — | — | — | — | — | — |

**Tổng:** 1 OK, 2 skip, 0 dry_run

---

## SESSION 2026-07-30 — P1.5 FOLLOW-UP (session 3)

**Nhiệm vụ:** LESSONS gap check, case_daily fn<6 fix, schtasks, tape spec, commits.

---

### [T1] LESSONS sheet — BLOCKER: CẦN OPERATOR

**Probe kết quả:** CASE_INDEX.xlsx LESSONS sheet có **27 bài** (L-01 đến L-27), max_row=31 (4 header rows + 27 data rows).

**Task yêu cầu:** sync lên 31 bài trước khi renumber. L-28 đến L-31 nội dung **chưa có** — không tìm thấy trong codebase hay chat history.

**Chặn cứng:** Cần operator cung cấp nội dung L-28 đến L-31, sau đó:
- Append L-28..L-31 vào LESSONS sheet
- Renumber: L-26→L-32 (file-canonical), L-27→L-33 (fn=1-guard)
- Thêm L-34: cấm silent-save sang tên khác khi file lock → RAISE
- Regenerate lessons_learned.md

Code của L-34 (PermissionError → RAISE) đã được implement trong case_daily.py.

---

### [T2] case_daily fn<6 fix — DONE

**Root cause Jul29 taker substitution:** `fn_n == "1"` → `fn1 = True` → Zone-A-agg (0.5046) thay thế native taker (0.4989). Logic cũ sai: Zone-A thay taker khi fn=1 dù taker KHÔNG phải ratio field cần suspect.

**Fix đã apply:**
- `fn_suspect = int(fn_n) < 6 or low_conf == "True"` (thay vì `fn_n == "1"`)
- Taker (col 5): luôn dùng native, bỏ Zone-A substitution
- Ratio cols {15,16,17}: ghi native + comment `"SUSPECT fn<6 (fn={fn_n}, src={src_ratio})"` khi fn_suspect=True
- PermissionError handler → `raise RuntimeError("[L-34] File locked — close xlsx then retry")` (bỏ fallback _NEW file)
- Xóa `_load_zone_a` và toàn bộ Zone-A code (dead code)

**CASE_BANK.xlsx Jul29 retrofix:**
- Col 5 (taker): 0.5046 → **0.49892268377010573** (native)
- Cols 15/16/17: comment "SUSPECT fn<6 (fn=1, src=native_1d)" thêm vào (giá trị pos_r/acc_r/gLSR giữ nguyên đúng native)
- Script: `_task_fix_bank_jul29.py`

---

### [T3] Task Scheduler case_daily — DONE

| Field | Value |
|-------|-------|
| Task name | `FreshWatch_case_daily` |
| Schedule | Daily 09:00 ICT (UTC+7, Vietnam) = 02:00 UTC |
| Wrapper | `scripts/run_case_daily.bat` |
| Log | `data/logs/case_daily.log` |
| Status | Ready (next run 2026-07-31 09:00 ICT) |

**LedgerSync timing:** Export ships ~01:00 UTC = 08:00 ICT. case_daily chạy 09:00 ICT → buffer 1h. PASS.

---

### [T4] Tape daemon spec — DONE

Probe BR@Gate: ~1 282 trades/day, ~2 pages (limit=1000), from/to filter CONFIRMED.

**Kết luận:** BR volume thấp → one-shot daily đủ. Daemon cần cho tokens volume cao (TAG, BANK chưa đo).

Spec: `proposals/tape_daemon_spec.md` — **chờ operator approve** trước khi implement.

---

### [T5] Commits tách

- (a) LESSONS renumber+L-34: **BLOCKED** (chờ L-28..L-31 từ operator)
- (b) case_daily fn<6 fix + BANK Jul29 retrofix: **DONE** (commit sau)
- (c) schtasks bat: **DONE** (commit sau)

---

## SESSION 2026-07-30 — P1.5 FOLLOW-UP (session 4 / tiep theo session 3)

### [T1] LESSONS sync rev.2 — DONE

**Source:** docs/lessons_rev2_source.md (operator-approved rev.2, ghi vao repo cung session nay)

**Thao tac:**
1. Rename: L-26 (file-canonical) → L-32, L-27 (fn=1 guard) → L-33
2. Insert 6 rows: L-26→L-31 (wrong-side fuel, M2 dao dau, tu-ha-cap narrative, alpha_vol_suspect, Bitget lech ngay, consolidation nguon)
3. Update L-14→L-20 theo rev.2 (xoa so bia, sua ten L-16, them co che L-14/L-15)
4. Append L-34: PermissionError RAISE
5. Verify: 34 bai, L-01..L-34 day du, khong trung ID
6. Regenerate docs/lessons_learned.md (141 dong)

Script: _task_sync_lessons.py

---

### [T3] Label fix ICT — DONE

SGT (UTC+8, Singapore) sai — may la UTC+7 (ICT, Vietnam). Sua 4 cho trong agent_log.md:
- 07:10 SGT → 07:10 ICT (lich su)
- 09:00 SGT → 09:00 ICT trong T3 summary (×3)

---

### [T4] BR full-day Jul29 test — PASS

**3 so:**
| Metric | Ket qua |
|--------|---------|
| Trades Jul29 | **2 401 trades** (3 pages x limit=1000) |
| Timestamp phu | 00:00:13 → 23:59:09 UTC (gap <1 phut hai dau) |
| Tape vol vs kline vol | $24,025.34 vs $24,025.34 = **0.0% diff** |

**Ket luan:** PASS — one-shot daily DU cho BR. Collect_tape.py pagination hop le.

**Dinh nghia nguong:** one-shot valid cho token <=5000 trades/ngay (<=5 pages, margin 2x). BR (2401/ngay) nam trong vung an toan.

**Hanh dong tiep (cho operator duyet):**
1. Add collect_tape BR vao cron daily (02:30 ICT = 19:30 UTC hom truoc, sau export)
2. Do volume TAG truoc khi quyet dinh one-shot vs daemon

**Khong thay doi:** collect_tape.py giu nguyen (one-shot da dung). Daemon spec trong proposals/tape_daemon_spec.md cho tokens vol cao.

---
