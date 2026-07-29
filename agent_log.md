# AGENT LOG — FreshWatch

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

*Cap nhat: 2026-07-29 (sau chinh sua 30/07)*
