# ÁN LSR-MERGE GUA/APR — Forensic Report
**Date:** 2026-08-17  
**Probe:** `_probe_lsr_merge_20260817.py`  
**Files touched:** read-only. Không rebuild, không ghi đè.

---

## §1. Backup Files — Paths Xác Nhận

| File | Path | Size | Nội dung |
|------|------|------|---------|
| GUA (hậu-rebuild Aug10, trước spot-patch hôm nay) | `scratch/CASE_GUA_BACKUP_20260817_0315.xlsx` | 66,979 B | State sau build Aug10 — LSR từ freshwatch **CÓ đủ** |
| APR (pre-rebuild Aug10, best historical) | `scratch/CASE_APR_bak_reg_20260810_034444.xlsx` | 78,580 B | State trước Aug10 rebuild — LSR từ freshwatch **CÓ đủ** |
| APR (hậu-rebuild Aug10, trước spot-patch hôm nay) | `scratch/CASE_APR_BACKUP_20260817_0315.xlsx` | 80,061 B | State sau build Aug10 — LSR mix freshwatch+fapi |

> GUA backup 0315 là auto-backup trước khi spot-patch chạy hôm nay. APR bak_0810_034444 là pre-rebuild canonical.  
> Không có backup GUA nào trước Aug10 (GUA CASE cold-start Aug10, commit `b752948`).

---

## §2. Counter-Evidence — Số Nhận Diện Khớp ✓

### GUA — `scratch/CASE_GUA_BACKUP_20260817_0315.xlsx` DAILY, sheet DAILY, row 2=fieldnames

Window 27/06→07/08. Số nhận diện: **acc_r ≈ 6.1, gLSR 6.0→2.87**

| date | pos_r | acc_r | gLSR | taker_lsr | data_source_lsr |
|------|-------|-------|------|-----------|----------------|
| 2026-06-27 | 1.1265 | 1.2041 | 1.0934 | 0.8119 | freshwatch |
| 2026-07-05 | 1.1310 | 2.3613 | 2.2020 | 0.8666 | freshwatch |
| 2026-07-13 | 1.2713 | 2.5075 | 1.9824 | 0.8911 | freshwatch |
| 2026-07-21 | 1.3032 | 4.5772 | 3.7870 | 1.0095 | freshwatch |
| **2026-07-29** | **1.4063** | **6.0323** | **5.9300** | 0.8143 | freshwatch |

Xác nhận: acc_r đạt đỉnh **6.1124** tại Jul31 (gLSR=5.9348), rơi về **2.8745** tại Aug07. Khớp hoàn toàn với số nhận diện `6.0→2.87`. ✓

### APR — `scratch/CASE_APR_bak_reg_20260810_034444.xlsx` DAILY

Window 01/06→07/08. Số nhận diện: **pos_r 1.78–2.0**

| date | pos_r | acc_r | gLSR | taker_lsr | data_source_lsr |
|------|-------|-------|------|-----------|----------------|
| 2026-06-01 | 2.2645 | 1.6624 | 1.5170 | 0.9446 | freshwatch |
| 2026-06-14 | 2.1788 | 1.8944 | 1.7863 | 0.9820 | freshwatch |
| 2026-06-27 | 1.9246 | 2.3190 | 2.7538 | 0.9267 | freshwatch |
| 2026-07-10 | 1.9349 | 1.6731 | 1.8377 | 1.0600 | freshwatch |
| **2026-07-23** | **1.8296** | **1.6702** | **1.8433** | 0.9041 | freshwatch |

Xác nhận: pos_r range Jun01-Aug07 = **1.69→2.27**, trung tâm 1.78–2.0 ✓

**→ Số nhận diện đã khớp. Tiếp tục trace.**

---

## §3. Current Files — Xác Nhận NULL

Probe: `_probe_lsr_merge_20260817.py`, đọc `docs/case_files/CASE_GUA.xlsx` và `CASE_APR.xlsx`.

### CASE_GUA.xlsx (current)
- 238 data rows, last date: **2026-08-16**
- **pos_r null: 238/238 (100.0%)** — toàn bộ DAILY không có LSR

Window 27/06→07/08 (5 rows):

| date | pos_r | acc_r | gLSR | taker_lsr | data_source_lsr |
|------|-------|-------|------|-----------|----------------|
| 2026-06-27 | **None** | **None** | **None** | **None** | MISSING(>30d) |
| 2026-07-05 | **None** | **None** | **None** | **None** | MISSING(>30d) |
| 2026-07-13 | **None** | **None** | **None** | **None** | MISSING(>30d) |
| 2026-07-21 | **None** | **None** | **None** | **None** | fapi_LSR_30d |
| 2026-07-29 | **None** | **None** | **None** | **None** | fapi_LSR_30d |

> Note: `data_source_lsr='fapi_LSR_30d'` xuất hiện từ Jul19 (vào trong 30d window của bản fetch mới) nhưng giá trị vẫn null — đây chính là dấu hiệu của schema mismatch (xem §4).

### CASE_APR.xlsx (current)
- 298 data rows, last date: **2026-08-16**
- **pos_r null: 224/298 (75.2%)**
- pos_r/acc_r/gLSR **POPULATED** cho Jun01–Jul18 (freshwatch range ngoài 30d window)
- pos_r/acc_r/gLSR **NULL** cho Jul19–Aug16 (bị block bởi schema-mismatch CSV)
- **taker_lsr: 100% NULL** trên toàn file (cả freshwatch range)

Window 01/06→07/08 (5 rows):

| date | pos_r | acc_r | gLSR | taker_lsr | data_source_lsr |
|------|-------|-------|------|-----------|----------------|
| 2026-06-01 | 2.2645 | 1.6624 | 1.5170 | **None** | MISSING(>30d) |
| 2026-06-14 | 2.1788 | 1.8944 | 1.7863 | **None** | MISSING(>30d) |
| 2026-06-27 | 1.9246 | 2.3190 | 2.7538 | **None** | MISSING(>30d) |
| 2026-07-10 | 1.9349 | 1.6731 | 1.8377 | **None** | MISSING(>30d) |
| 2026-07-23 | 1.8296 | 1.6702 | 1.8433 | **None** | fapi_LSR_30d |

> APR pos_r/acc_r/gLSR cho pre-Jul19 = freshwatch survived (không bị block). taker_lsr null = freshwatch_daily CSVs không có `taker_ratio` cho APR.

---

## §4. Diff Pipeline — Điểm Gãy Chính Xác

### 4.1 Đường dữ liệu build Aug10 vs rebuild Aug17

| | Build Aug10 (HOẠT ĐỘNG) | Rebuild Aug17 (GÃY) |
|---|---|---|
| LSR scratch file | `gua_lsr_raw_20260810.csv` (62B, **header-only, 0 rows**) | `gua_lsr_raw_20260817.csv` (1464B, **30 rows**) |
| Schema CSV | N/A (empty) | `date, time_ms, longShortRatio, longAccount, shortAccount` |
| build_case.py expects | `pos_r_raw\|pos_r`, `acc_r_raw\|acc_r`, `glsr_raw\|gLSR\|glsr` | ← same, không thay đổi |
| `lsr_by_d` sau CSV | **empty** (0 keys) | **30 keys** Jul19–Aug17, tất cả **{pos_r_raw:None, acc_r_raw:None, glsr_raw:None}** |
| Freshwatch extend | Fills **ALL dates** freely (dict empty) | Fills **chỉ pre-Jul19** (Jul19-Aug17 đã bị occupied, bị skip) |
| GUA result | LSR populated từ freshwatch Jun27→Aug07 | **100% NULL** |

**APR:** Không có `apr_lsr_raw_20260810.csv` → Aug10 build cũng dùng freshwatch toàn bộ. `apr_lsr_raw_20260817.csv` (1464B, 30 rows, cùng schema sai) → tương tự GUA: Jul19-Aug16 null, pre-Jul19 freshwatch survived.

---

### 4.2 Code gãy — `build_case.py` (3 điểm)

**ĐIỂM GÃY 1 — A-0a normalize (lines 141–152):** Không nhận `longShortRatio`

```python
# build_case.py lines 141-152
# A-0a fix: normalize LSR CSV columns (handles both "pos_r" and "pos_r_raw" naming)
lsr_by_d = {}
for r in lsr_rows:
    dt = r.get("date","")
    if not dt: continue
    lsr_by_d[dt] = {
        "pos_r_raw":     safe_float(r.get("pos_r_raw") or r.get("pos_r")),       # ← không có "longShortRatio"
        "acc_r_raw":     safe_float(r.get("acc_r_raw") or r.get("acc_r")),       # ← không có "longAccount"
        "glsr_raw":      safe_float(r.get("glsr_raw") or r.get("gLSR") or r.get("glsr")),  # ← không có "longShortRatio"
        "taker_lsr_raw": safe_float(r.get("taker_lsr_raw") or r.get("taker_lsr")),         # ← không có field nào
        "_src":          r.get("_src", "fapi_LSR_30d"),
    }
```

CSV mới có: `longShortRatio=3.4783`, `longAccount=0.7767`, `shortAccount=0.2233`.  
Kết quả: **tất cả safe_float() trả về None** → 30 entries với all-None values điền vào `lsr_by_d`.

---

**ĐIỂM GÃY 2 — Freshwatch blocking guard (line 162):** Dates đã chiếm → freshwatch bị chặn

```python
# build_case.py lines 154-171
for fw_csv in sorted((SCRATCH).glob("freshwatch_daily_*.csv")):
    with open(fw_csv, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            sym = row.get("symbol","")
            if sym.upper() != SYMBOL_PERP: continue
            dt = row.get("date","")
            if not dt or dt in lsr_by_d: continue  # ← BLOCKING GUARD: dates chiếm bởi CSV null → freshwatch skip
            pos_r = safe_float(row.get("lsr_pos_r"))
            ...
            if pos_r:
                lsr_by_d[dt] = {..., "_src": "freshwatch"}
```

Tác động: 30 dates Jul19-Aug17 đã có null-entries trong `lsr_by_d` → freshwatch nhìn thấy `dt in lsr_by_d = True` → `continue` → bỏ qua toàn bộ freshwatch data cho Jul19-Aug17.

---

**ĐIỂM GÃY 3 — A-0b guard KHÔNG có staleness check riêng cho LSR CSV (lines 197-204 vs 857-868):**

```python
# Staleness guard (lines 197-204) — CHỈ kiểm tra perp CSV:
_gap_days = (datetime.strptime(_yesterday, "%Y-%m-%d") - datetime.strptime(MAX_DATE, "%Y-%m-%d")).days
if _gap_days > 2:
    raise RuntimeError(f"STALENESS GUARD: perp CSV last date={MAX_DATE}...")

# A-0b coverage guard (lines 857-868) — kiểm tra LATE (sau khi XLSX đã ghi):
lsr_null_pct = ...
if lsr_null_pct > 50:
    raise ValueError(f"A-0b guard: LSR pos_r null {lsr_null_pct:.1f}% > 50% in last 30d")
```

A-0b DID fire (exit ≠ 0) nhưng XLSX đã được ghi trước đó (write XLSX ≈ line 800-856, guard ≈ line 857-868). Corrupted state tồn tại trên disk.

---

### 4.3 Scratch LSR CSV raw data (xác nhận schema mismatch)

```
gua_lsr_raw_20260810.csv (62B):
  cols=['date', 'pos_r_raw', 'acc_r_raw', 'glsr_raw', 'taker_lsr_raw', 'div_raw', '_src']
  rows=0   ← EMPTY (header only) — Aug10 build đọc file này, lsr_by_d = {} → freshwatch fill free

gua_lsr_raw_20260817.csv (1464B):
  cols=['date', 'time_ms', 'longShortRatio', 'longAccount', 'shortAccount']
  rows=30, range=2026-07-19→2026-08-17
  sample: date=2026-07-19, longShortRatio=3.4783, longAccount=0.7767, shortAccount=0.2233
  ← Schema KHÔNG khớp A-0a lookup → tất cả None

apr_lsr_raw_20260817.csv (1464B):
  cols=['date', 'time_ms', 'longShortRatio', 'longAccount', 'shortAccount']  ← cùng schema sai
  rows=30, range=2026-07-19→2026-08-17
  sample: date=2026-07-19, longShortRatio=2.0979, longAccount=0.6772, shortAccount=0.3228
```

**Nguồn sinh CSV sai:** `_probe_gua_apr_rebuild_20260817.py` → `fetch_lsr()` → ghi `longShortRatio/longAccount/shortAccount` (Binance raw format). Thiếu bước transform sang schema chuẩn `pos_r_raw/acc_r_raw/glsr_raw`.

---

## §5. Proposal Fix (chưa apply — chờ operator duyệt)

### Fix A: Extend A-0a normalize thêm Binance raw columns

**File:** `build_case.py`, thay thế lines 146–152.

**Diff dự kiến:**

```python
# BEFORE (lines 146-152):
    lsr_by_d[dt] = {
        "pos_r_raw":     safe_float(r.get("pos_r_raw") or r.get("pos_r")),
        "acc_r_raw":     safe_float(r.get("acc_r_raw") or r.get("acc_r")),
        "glsr_raw":      safe_float(r.get("glsr_raw") or r.get("gLSR") or r.get("glsr")),
        "taker_lsr_raw": safe_float(r.get("taker_lsr_raw") or r.get("taker_lsr")),
        "_src":          r.get("_src", "fapi_LSR_30d"),
    }

# AFTER:
    # Binance raw: longShortRatio=gLSR, longAccount=acc_fraction, shortAccount=short_fraction
    # pos_r: not available from globalLongShortAccountRatio → use gLSR as proxy (same endpoint)
    # acc_r = longShortRatio (long accounts / short accounts)
    _lsr_ratio = safe_float(r.get("longShortRatio"))
    _long_acct = safe_float(r.get("longAccount"))
    _short_acct = safe_float(r.get("shortAccount"))
    # compute acc_r from fractions if available: long/short ratio = longAccount/shortAccount
    _acc_r_from_fractions = (
        round(_long_acct / _short_acct, 4)
        if _long_acct and _short_acct and _short_acct > 0 else None
    )
    lsr_by_d[dt] = {
        "pos_r_raw":     safe_float(r.get("pos_r_raw") or r.get("pos_r") or _lsr_ratio),  # proxy: gLSR
        "acc_r_raw":     safe_float(r.get("acc_r_raw") or r.get("acc_r") or _acc_r_from_fractions or _lsr_ratio),
        "glsr_raw":      safe_float(r.get("glsr_raw") or r.get("gLSR") or r.get("glsr") or _lsr_ratio),
        "taker_lsr_raw": safe_float(r.get("taker_lsr_raw") or r.get("taker_lsr")),
        "_src":          r.get("_src", "fapi_LSR_30d"),
    }
```

**Lưu ý Fix A:**
- `pos_r_raw` sẽ dùng `longShortRatio` làm proxy (= acc ratio, không phải position ratio). Khác nguồn freshwatch `lsr_pos_r` (= Binance top-trader position ratio). Accept difference, ghi rõ trong metadata.
- Phương án sạch hơn: sửa `fetch_lsr()` trong rebuild probe để compute đúng từ đầu (Fix B).

---

### Fix B (alternated / cleanest): Sửa `fetch_lsr()` output schema

**File:** `_probe_gua_apr_rebuild_20260817.py` (hoặc template fetch script), `fetch_lsr()` → write canonical columns.

```python
# BEFORE fetch_lsr():
rows.append({
    "date": ms_to_date(ts),
    "time_ms": str(ts),
    "longShortRatio": item.get("longShortRatio", ""),
    "longAccount": item.get("longAccount", ""),
    "shortAccount": item.get("shortAccount", ""),
})
write_csv(..., ["date", "time_ms", "longShortRatio", "longAccount", "shortAccount"])

# AFTER:
_lsr  = float(item.get("longShortRatio", 0) or 0)
_long = float(item.get("longAccount", 0) or 0)
_short= float(item.get("shortAccount", 0) or 0)
_acc_r = round(_long / _short, 4) if _short > 0 else None
rows.append({
    "date":         ms_to_date(ts),
    "pos_r_raw":    round(_lsr, 4),    # proxy = acc ratio from globalLSR endpoint
    "acc_r_raw":    _acc_r,
    "glsr_raw":     round(_lsr, 4),
    "taker_lsr_raw": "",               # ABSTAIN: not available from this endpoint
    "_src":         "fapi_LSR_30d",
})
write_csv(..., ["date", "pos_r_raw", "acc_r_raw", "glsr_raw", "taker_lsr_raw", "_src"])
```

Fix B giải quyết root cause ở điểm sinh dữ liệu, không cần sửa build_case.py.

---

### Fix C: Staleness guard cho LSR CSV (generalize cho MỌI case build)

**File:** `build_case.py`, thêm sau line 152 (sau khi build `lsr_by_d`):

```python
# Proposal: generalize staleness guard to LSR CSV
# (currently staleness guard only checks perp CSV — lines 197-204)
_lsr_dates = sorted(lsr_by_d.keys())
if _lsr_dates:
    _lsr_last = _lsr_dates[-1]
    _lsr_gap  = (datetime.strptime(_yesterday, "%Y-%m-%d") -
                 datetime.strptime(_lsr_last, "%Y-%m-%d")).days
    if _lsr_gap > 2:
        raise RuntimeError(
            f"STALENESS GUARD LSR: last date in {SYM_LOWER}_lsr_raw_{DATE_TAG}.csv = {_lsr_last}, "
            f"gap={_lsr_gap}d > 2. Re-fetch LSR scratch before build_case."
        )
else:
    # lsr_by_d empty (CSV header-only) — do NOT raise, let freshwatch fill
    log("  LSR CSV empty — freshwatch will fill all dates")
```

**Generalization cho mọi case build:** Staleness guard hiện tại chỉ có cho perp CSV. Cần thêm guard tương tự cho LSR CSV — nhưng với exception: nếu CSV header-only (0 rows) → không lỗi, để freshwatch handle. Chỉ lỗi khi CSV có data nhưng data cũ > 2d.

**Pre-check tốt hơn (tùy chọn):** Guard nên check SCHEMA thay vì staleness:

```python
# Check columns match expected schema before processing
_lsr_cols = set(lsr_rows[0].keys()) if lsr_rows else set()
_required  = {"pos_r_raw", "pos_r", "glsr_raw", "gLSR", "glsr"}
if lsr_rows and not (_lsr_cols & _required):
    raise RuntimeError(
        f"LSR CSV SCHEMA MISMATCH: got cols={sorted(_lsr_cols)}, "
        f"expected any of {sorted(_required)}. "
        f"File: {SYM_LOWER}_lsr_raw_{DATE_TAG}.csv"
    )
```

Schema check sẽ bắt ngay tại runtime trước khi damage xảy ra, mạnh hơn staleness guard.

---

## Tóm Tắt Điểm Gãy

| # | Điểm gãy | File | Line(s) | Tác động |
|---|---------|------|---------|---------|
| 1 | Fetch script viết sai schema | `_probe_gua_apr_rebuild_20260817.py` | `fetch_lsr()` | Sinh `*_lsr_raw_20260817.csv` với cols Binance raw, không match A-0a |
| 2 | A-0a không nhận Binance raw cols | `build_case.py` | 147–150 | `longShortRatio` → None; 30 dates occupied với null |
| 3 | Freshwatch blocking guard | `build_case.py` | 162 | `dt in lsr_by_d` skip dates đã chiếm → freshwatch bị chặn cho Jul19-Aug17 |
| 4 | XLSX ghi trước guard | `build_case.py` | ~800-856 (write) vs 857-868 (guard) | Corrupted XLSX persists trên disk dù A-0b raise |
| 5 | Không có LSR staleness/schema guard | `build_case.py` | — | Schema mismatch không bị catch sớm |

**Phục hồi:** GUA cần rebuild từ bản backup `CASE_GUA_BACKUP_20260817_0315.xlsx` (hoặc re-fetch + rebuild sau khi fix). APR Jul19-Aug16 LSR cần phục hồi từ backup `CASE_APR_BACKUP_20260817_0315.xlsx`.

**CẤM close án bằng "fapi không có LSR"** — counter-evidence xác nhận LSR tồn tại, đây là lỗi pipeline không phải missing data.
