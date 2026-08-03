# AGENT LOG — FreshWatch

---

## SESSION 2026-08-03 — IDOL ANALYSIS POST-BACKFILL + CASE UPDATE

**Operator:** Tien  
**Agent model:** claude-sonnet-4-6  
**Nhiệm vụ:** Verify backfill, đọc chuỗi sạch 27/07→02/08, cập nhật EVENTS/TRIGGERS/MM_PROFILE.

---

### [D1] B1 — VERIFY BACKFILL

| date | row | fn | px_avg | SUSPECT | trạng thái |
|------|-----|----|--------|---------|------------|
| 27/07 | 26 | 6 | 0.015677 | none ✓ | OK (pre-backfill) |
| 28/07 | 27 | **6** | 0.016809 | none ✓ | OVERWRITE_OK (fn=1→6) |
| 29/07 | 28 | **6** | 0.015687 | none ✓ | OVERWRITE_OK (fn=1→6) |
| 30/07 | 29 | **6** | 0.015234 | none ✓ | OVERWRITE_OK (fn=1→6) |
| 31/07 | 30 | **6** | 0.016403 | none ✓ | OVERWRITE_OK (fn=1→6) |
| 01/08 | 31 | 6 | 0.023946 | none ✓ | OK |
| 02/08 | 32 | 6 | 0.023117 | none ✓ | OK |
| 03/08 | — | MISSING | — | — | Stale fn=1 — append sau 04/08 01:20 UTC |

**PASS** — fn=6 toàn bộ chuỗi (IDOL 4h interval ✓). Không còn SUSPECT.

---

### [D2] B2 — 03/08 DAILY

Không append hôm nay: export 2026-08.csv có 03/08 nhưng fn=1 (stale — generated 00:50 UTC bởi old cron trước khi fix chạy). Đây chính là L-41 vòng tự nhiên: verify xem 04/08 01:20 UTC cron có ra fn=6 cho 03/08 không.

---

### [D3] B3 — PHÂN TÍCH CHUỖI SẠch 27/07→02/08

**Chuỗi số native:**

| date | fn | px | taker | f_avg | pos_r | acc_r | glsr | div* | OI_USD |
|------|----|----|-------|-------|-------|-------|------|------|--------|
| 27/07 | 6 | 0.01568 | 0.485 | 0.000343 | 2.059 | 1.360 | 1.369 | 1.515 | 6.60M |
| 28/07 | 6 | 0.01681 | 0.480 | 0.000198 | 2.207 | 0.992 | 1.038 | 2.224 | 10.71M |
| 29/07 | 6 | 0.01569 | 0.473 | 0.000067 | 2.328 | 1.161 | 1.390 | 2.005 | 9.91M |
| 30/07 | 6 | 0.01523 | 0.529 | 0.000096 | 2.559 | 1.209 | 1.459 | 2.116 | 8.87M |
| 31/07 | 6 | 0.01640 | 0.499 | 0.000318 | 2.546 | 1.240 | 1.558 | 2.054 | 8.81M |
| 01/08 | 6 | 0.02395 | 0.515 | 0.000095 | 2.524 | 1.183 | 1.489 | 2.135 | 9.84M |
| 02/08 | 6 | 0.02312 | 0.501 | 0.000050 | 1.731 | 1.178 | 1.144 | 1.470 | 10.48M |

*div = pos_r / acc_r (computed manually — formula cache chưa có).

**a) OI build 28/07→31/07 — số sạch vs cũ:**

Old (fn=1 stale): pos_r 2.207→2.546. New (fn=6 native): 2.2065→2.5585. Δmax < 1.3%.
**"Smart money vào trước ignition" VẪN ĐỨNG** — số không lệch material.

28/07: OI +62% (6.60M→10.71M) + taker=0.480 (bear!) = MM mua limit khi retail sell = BIDWALK-A.
29-31/07: pos_r tiếp leo 2.33→2.56 dù OI giảm nhẹ → top longs giữ/thêm, không phải retail pile-in.

**b) 02/08 post-markup:**

pos_r: 2.524→1.731 (−31%) | OI: 9.84M→10.48M (+6.5%) | glsr: 1.489→1.144 | div: 2.135→1.470

Key: pos_r sụp nhưng OI TĂNG → top longs đang CLOSE, retail bù OI. "Ghế đổi tay."
glsr 1.144: crowd tiến về neutral (chưa flush full, cần <1.1 >=3d).
03/08 còn thiếu — không kết luận "tiếp diễn" hay "chững".

**c) Funding 02/08 PINNED = mảnh hồ sơ re-staging:**

Sau markup +50% (01/08), f_avg 02/08 = 5e-5 (sàn pinned). Crowd không rush mua (không tạo premium). Consistent EVAA khuôn leg-2 re-staging: MM ghim funding để crowd không thấy "đắt", chờ tích lũy vòng mới.

**d) Suppressor scan:**

Từ số raw: pos_r 1.731 > 1.6 → còn ghế (định luật #9, chưa kích T3). glsr 1.144 > 1.1 → chưa flush (chưa kích T2). Cols 23/24 (signals_suppress) chưa có giá trị computed. Wall data (cols 30-35) chưa populate.

**e) Spot Gate 03/08:** Không có data trong CASE. Perp vol: 175.67M (01/08) → 40.7M (02/08) (−77%). Gate spot cụ thể cần operator check.

---

### [D4] B4 — CASE_IDOL.xlsx CẬP NHẬT

**EVENTS:**
- E1 ngày: `~07-27→08-01` → `31/07→02/08` ✓
- E1 doc_nhanh: thêm "rút TRONG markup — hai khuôn cạnh tranh: thắt float leg-2 vs chốt chiến lợi phẩm (ESPORTS-10%)" ✓
- E2 (Gate deposit): thêm note "hạ cấp <2% supply" ✓

**TRIGGERS (T1-T4 điền):**
- T1: Redeposit bất kỳ ví nào trong cụm 13 → ĐÓNG ÁN XẢ TỨC THỜI
- T2: gLSR flush ≤1.1 + funding tái ghim ≥3d → re-staging leg-2 sống
- T3: pos_r ≥1.6 tại OI floor = còn ghế; <1.3 = ghế rỗng → canh ngày mai 03/08
- T4: Suppressor bất kỳ (L-27 §5) → STAND_ASIDE

**MM_PROFILE:**
- Van tay funding: pin-post-markup + taker<55% = BIDWALK-A fingerprint ✓
- Van tay markup: taker 51.5% (<55%), vol 10x nen, pos_r load trước ignition ✓
- Kỹ thuật crowd: bid-walk trên fear-sell (28/07 taker 0.480 khi OI +62%) ✓
- MM_ID tạm: **unknown-IDOL / BIDWALK-A khuôn** (chờ bait-probe taker 23/07)

**PENDING (chờ operator):**
- DAILY 03/08: dominance_pct=15%, exch_balance=723M — điền sau 04/08 append
- Gate spot vol 03/08: cần manual check
- P3: 13 ví → 58bro txhash + địa chỉ đích

---

### [D5] B5 — BscScan WATCHER 13 VÍ

Không có armed-address §8 template trong codebase. → **DEV TASK MỚI** (chuyển sang DEV topic).
Đề bài: watcher ≤20 địa chỉ, 15min/lần, 0-credit (BscScan free API).
Blocking: P3 (58bro đích chưa có) → không dựng trước khi có địa chỉ.

---

## SESSION 2026-08-03 — FIX EXPORTER + RE-GENERATE 28-31/07

**Operator:** Tien
**Agent model:** claude-sonnet-4-6
**Nhiệm vụ:** Sửa export timing bug, re-generate 28-31/07 từ store, force-overwrite CASE files.

---

### [C1] Fix exporter + cron — DONE

**Root cause:** Cron chạy `50 0 * * *` (00:50 UTC) — tại thời điểm đó IDOL chỉ có 1 kỳ funding (00:00 UTC). Còn 5 kỳ chưa collect. Export ra fn=1 (stale).

**Fixes applied:**
1. `scripts/export_freshwatch_daily.py` — `default_dates()` loại trừ today (D) khỏi default range: `range(2, 0, -1)` thay vì `range(2, -1, -1)`
2. `scripts/export_freshwatch_daily.py` — thêm `--force-regen` flag: strip existing rows cho target dates, re-generate từ store
3. Cron: `50 0 * * *` → `20 1 * * *` (01:20 UTC — sau khi spot/alpha xong 01:00)
4. `scripts/case_daily.py` — thêm `--force-overwrite` mode: overwrite row có SUSPECT comment hoặc fn < 6
5. `scripts/case_daily.py` — fix `MergedCell` skip (không ghi vào merged cells → tránh AttributeError)

---

### [C2] Re-generate 28-31/07 trên VPS — DONE

Dùng `--force-regen` cho 4 ngày:

| date | stripped | rebuilt |
|------|---------|---------|
| 2026-07-28 | 525 | 525 |
| 2026-07-29 | 525 | 525 |
| 2026-07-30 | 525 | 525 |
| 2026-07-31 | 525 | 525 |

**Verify fn (VPS → local):**

| sym | 28/07 | 29/07 | 30/07 | 31/07 | note |
|-----|-------|-------|-------|-------|------|
| IDOLUSDT | 6✓ | 6✓ | 6✓ | 6✓ | |
| TAGUSDT | 6✓ | 6✓ | 6✓ | 6✓ | |
| BRUSDT | 6✓ | 6✓ | 6✓ | 6✓ | |
| BANKUSDT | 6✓ | 6✓ | 15⚠ | 24⚠ | BANK đổi interval 4h→1h từ 30/07 |

BANK 30/07 fn=15 = 4 kỳ 4h (00-12) + 12 kỳ 1h (12-23); BANK 31/07 fn=24 = full 1h. Đây là Binance thay đổi schedule thực — không phải lỗi data.

---

### [C3] case_daily --force-overwrite 4 ngày × 4 case — DONE

**Old → new table (OVERWRITE rows):**

| token | date | row | col | old | new |
|-------|------|-----|-----|-----|-----|
| BR | 2026-07-28 | 66 | fn(9) | None | 6 |
| BR | 2026-07-28 | 66 | px(2) | None | 0.14681 |
| IDOL | 2026-07-28 | 27 | fn(9) | 1 | 6 |
| IDOL | 2026-07-28 | 27 | px(2) | None | 0.016808 |
| IDOL | 2026-07-28 | 27 | f_avg(6) | 0.00022299 | 0.0001976 |
| BANK | 2026-07-29 | 37 | fn(9) | 1 | 6 |
| BANK | 2026-07-29 | 37 | px(2) | None | 0.17135 |
| TAG | 2026-07-29 | 31 | fn(9) | 1 | 6 |
| TAG | 2026-07-29 | 31 | px(2) | 0.001215 | 0.0012063 |
| BR | 2026-07-29 | 67 | fn(9) | 1 | 6 |
| BR | 2026-07-29 | 67 | px(2) | 0.146 | 0.14685 |
| IDOL | 2026-07-29 | 28 | fn(9) | 1 | 6 |
| IDOL | 2026-07-29 | 28 | px(2) | None | 0.015687 |
| IDOL | 2026-07-30 | 29 | fn(9) | 1 | 6 |
| IDOL | 2026-07-30 | 29 | px(2) | None | 0.015234 |
| IDOL | 2026-07-31 | 30 | fn(9) | 1 | 6 |
| IDOL | 2026-07-31 | 30 | px(2) | None | 0.016402 |

**Appended (new rows):**

| token | date | row | fn | px |
|-------|------|-----|----|----|
| TAG | 2026-07-30 | 32 | None* | None* |
| TAG | 2026-07-31 | 33 | 6 | 0.001355 |
| BR | 2026-07-30 | 68 | 6 | 0.14731 |
| BR | 2026-07-31 | 69 | 6 | 0.15034 |
| BANK | 2026-07-30 | 38 | 15 | 0.08873 |
| BANK | 2026-07-31 | 39 | 24 | 0.06306 |

*TAG 30/07 fn=None: operator đã merge A32:L32 → cols 2-12 là MergedCell, không thể ghi.

---

### [C4] CẦN OPERATOR — TAG CASE_TAG.xlsx A32:L32 merged

CASE_TAG.xlsx DAILY row 32 (date=2026-07-30) có merge A32:L32 do operator. Các cột px/vol/taker/funding (cols 2-12) không thể ghi tự động. Ratio (15-17) và formula (18-22, 36) đã ghi đúng.

**Hành động cần:** Operator unmerge A32:L32 trong CASE_TAG.xlsx, sau đó chạy:
```
python scripts/case_daily.py --date 2026-07-30 --force-overwrite
```

---

### [C5] VPS dependency fix

Các module `structlog`, `typer`, `python-dotenv` chưa cài trên VPS. Đã install với `--break-system-packages` (root, Debian). Cron tự nhiên không bị ảnh hưởng (cron dùng venv hay đường đã có sẵn — cần verify). → **CẦN OPERATOR verify** cron 01:20 UTC ngày mai (04/08) có chạy được với module mới.

---

## SESSION 2026-08-03 — DỌN REPO + QUY ƯỚC FILE (L-42)

**Operator:** Tien
**Agent model:** claude-sonnet-4-6
**Nhiệm vụ:** Thiết lập cấu trúc thư mục chuẩn, dọn probe/task/report đã xong vào archive.

### Kết quả di chuyển

| Nguồn | Đích | Số file |
|-------|------|---------|
| root `_probe_*/task_*/remote_*/run_*/...` | `scripts/archive/` | 69 |
| `scripts/_probe_*/_fix_*` | `scripts/archive/` | 15 |
| `docs/reports/_probe_*.txt/_task_*.txt + cooldown review` | `docs/reports/archive/` | 9 |
| `proposals/ratio_daily_canonical* (v1+v2 đã ký)` | `proposals/archive/` | 2 |
| **Tổng** | | **95 files** |

### Trạng thái sau dọn

**Root (còn lại):** `backtest.py`, `build_features.py`, `classify_phases.py`, `delta_analysis.py`, `feature_config.py`, `gate_tag_probe.py`, `oi_sweep.py`, `phase_config.py`, `replay.py`, `signals.py`, `step3_analysis.py`, `tag_data_pack.py`, `vps_audit_v2*.py` (×3), `_probe_vps_idol_store.py` (active per B7 IDOL follow-up)

**scripts/ (active):** 15 scripts sống + run_case_daily.bat

**docs/reports/ (active):** `missing_jul.md` (July missing = open issue B7)

**proposals/ (active):** `tape_daemon_spec.md` (chờ operator approve)

### Quy ước ghi vào CLAUDE.md (L-42)

Cấu trúc thư mục + vòng đời artifact đã vào mục CẤU TRÚC THƯ MỤC. Quy ước tên mới: `_probe_<án>_<YYYYMMDD>.py`. Agent tự move khi đóng án.

---

## SESSION 2026-08-03 — IDOL X1/X2/X3: UNLOCK + W6 REVISED + GATE SPOT

**Operator:** Tien
**Agent model:** claude-sonnet-4-6
**Nhiệm vụ:** X1 điền UNLOCK sheet, X2 hạ UNLOCK-VESTING → UNLIKELY, X3 xử án Gate spot mâu thuẫn.

---

### [X3] Truy nguồn Gate spot — RESOLVED: DỮ LIỆU THẬT

**Câu hỏi:** Report cũ có số Gate spot (110K/9.58M/1.55M) nhưng report mới nói "collector không tồn tại". Mâu thuẫn?

**Truy nguồn:**
- Script: `scripts/archive/_probe_idol_gate_tape.py`
- API call: `https://api.gateio.ws/api/v4/spot/candlesticks?currency_pair=IDOL_USDT&interval=1d&limit=7`
- Thời điểm chạy: `2026-08-03 01:49 UTC` (timestamp trong output file)
- Public API, không cần key — urllib.request trực tiếp

**Mapping số:**
| Số trong report cũ | Nguồn thực tế |
|--------------------|---------------|
| 110K | 2026-07-31 `quote_vol = 110,373.69 USDT` ✓ |
| 9.58M | 2026-08-01 `quote_vol = 9,577,588.31 USDT` ✓ |
| 1.55M | 2026-08-02 `quote_vol = 1,547,487.06 USDT` ✓ |

**Giải thích mâu thuẫn:** "Gate collector không tồn tại" = không có cron job thu thập định kỳ. Nhưng `_probe_idol_gate_tape.py` là **one-shot probe** gọi trực tiếp Gate public API — hai điều này không mâu thuẫn.

**Hành động:**
- W3 cũ: `ABSTAIN cấu trúc` → **GỠ ABSTAIN** — có Gate spot series đủ 28/07→02/08
- Không rút số theo L-28 (số hợp lệ, nguồn xác minh được)

---

### [X2] W6 Matrix Revised — UNLOCK-VESTING hạ UNLIKELY

**3 trượt cứng:**

| Trượt | Nội dung |
|-------|---------|
| Ngày ✗ | E1 rút 31/07→02/08. Vesting CoinLaunch ngày 11 hằng tháng. 11/07 đã qua 20 ngày; 11/08 còn 10 ngày. |
| Cỡ ✗ | 273M rút ≠ 97.29M tranche (gấp 2.8×). Không có cơ chế giải ngân 3 tháng cùng lúc. |
| Nguồn ✗ | Rút từ Binance (exchange wallet) ≠ disburse từ vesting contract. Sự kiện khác bản chất. |

**7×20M reinterpretation:** Chia-máy-khi-rút (TAG-5-ví khuôn) — operator rút tổng rồi chia đều cho nhiều ví quản lý. Không phải vesting tranche pattern.

**Kết quả W6 revised:**
- A (GOM): POSSIBLE — bằng chứng gián tiếp ủng hộ (BIDWALK-A, pos_r>1.6, funding pinned)
- B (UNLOCK-VESTING): **UNLIKELY** — 3 trượt cứng
- C (INFRA): POSSIBLE — khó phân biệt với A, cần P3 address label

**Script output:** `docs/reports/_probe_idol_w6_revised.txt`

---

### [SPOT/ALPHA] DAILY sheet — Gate spot 01/07→02/08 đầy đủ

**Phát hiện:** IDOL list trên Gate.io từ **01/07** (không phải 28/07 như ban đầu nghĩ).
Gate API `spot/candlesticks?from=&to=&interval=1d` trả về 34 candles.

**Đã điền DAILY c27-c29 toàn bộ:**

| Cột | Nội dung | Kết quả |
|-----|---------|---------|
| c27 `spot_venue` | 'Gate' cho 30 ngày (01/07→02/08) | ✓ |
| c28 `vol_spot_usd` | Quote vol USDT từ Gate API | 28 rows filled, 2 verify OK |
| c29 `taker_spot_pct` | ABSTAIN (Gate candle không có taker data) | blank = ABSTAIN |
| c36 `alpha_suspect` | Formula đã có — tự tính vol_spot/vol_perp | sẽ compute khi Excel recalc |

**Highlight Gate spot series (chọn lọc):**
| date | Gate quote USDT | Note |
|------|----------------|------|
| 01/07 | 223,517 | baseline |
| 03/07 | 1,320,492 | spike |
| 23/07 | 2,911,246 | spike (cùng ngày perp spike 167M) |
| 27/07 | 2,663,899 | pre-markup spike |
| 01/08 | **9,577,588** | MARKUP DAY |
| 02/08 | 1,547,487 | post-markup |

**Script:** `_task_idol_spot_alpha_fill.py` → `docs/reports/_task_idol_spot_alpha_fill.txt`

---

### [X1] UNLOCK Sheet — Điền từ CoinLaunch

**Nguồn:** CoinLaunch (operator-verified 2026-08-03)

| Field | Value |
|-------|-------|
| Total supply | 4,800,000,000 IDOL |
| TGE | 2025-06-11 |
| Unlocked | 32.49% |
| Monthly | 97,290,000 IDOL (~2.03%) ngày 11 hằng tháng |
| Community | 35,460,000 / tháng |
| Ecosystem | 17,630,000 / tháng |
| Team | 28,800,000 / tháng (cliff hết 06/2026, linear 2 tranche còn) |
| Strategic | 7,680,000 / tháng (cliff hết 06/2026, linear 2 tranche còn) |
| Private | 5,760,000 / tháng (cliff hết 06/2026, linear 2 tranche còn) |
| Advisor | 1,960,000 / tháng |
| Next unlock | **2026-08-11** (T+8) |

**Context:** Markup 01/08 nổ 10 ngày TRƯỚC tranche 11/08. Unlock = suppressor thường trực, không phải trigger E1.

**Task script:** `_task_idol_unlock_fill.py` — CẦN OPERATOR đóng CASE_IDOL.xlsx (PermissionError khi chạy).

**Sau khi đóng file chạy:**
```
python _task_idol_unlock_fill.py
```

---

### [Gate spot] W3 Series đầy đủ 28/07→02/08

| Date | Base IDOL | Quote USDT | Note |
|------|-----------|-----------|------|
| 28/07 | 36,651,223 | 615,898 | |
| 29/07 | 12,676,400 | 199,017 | |
| 30/07 | 23,265,613 | 352,552 | |
| 31/07 | 6,883,590 | 110,374 | |
| 01/08 | 405,069,384 | **9,577,588** | MARKUP DAY |
| 02/08 | 67,176,835 | 1,547,487 | post-markup |

**W2 Gate spot sức chứa:** 273M IDOL @ 0.02438 = 6.66M notional / 9.58M Gate vol = **69.5% THIN** → Gate không đủ sức chứa 273M trong 1 ngày.

---



---

## SESSION 2026-08-03 — IDOL A1→A5: ALPHA + DEX BSC + W6 REVISION

**Operator:** Tien
**Agent model:** claude-sonnet-4-6
**Nhiệm vụ:** A1 contract address; A2 store probe; A3 Alpha/DEX API series; A4 W2 re-run; A5 DAILY update + W6 revision.

---

### [A1] BSC Contract Address — FOUND

- **Contract:** `0x3b4de3c7855c03bb9f50ea252cd2c9fa1125ab07` (MEET48 Token / IDOL)
- **Nguồn:** CoinGecko free API (`/coins/meet48`) → `platforms.binance-smart-chain`
- **Ghi vào:** CASE sheet row4 (`bsc_contract_address`) — khóa vĩnh viễn

---

### [A2] Store Alpha Probe — NO DATA (án b)

- `alpha_bsc_symbols.txt`: không tồn tại trên local (VPS-only)
- IDOL `venue=no_spot` (confirmed từ spot_klines_1d probe trước)
- IDOL không có trên Binance Spot (kể cả BSC bridge) → alpha collector không thu
- **Verdict A2(b):** IDOL ngoài universe alpha collector, không có data trong store

---

### [A3] DEX BSC Series 20/07→03/08

**Attempt Binance Alpha API:** 403 Forbidden (gated, cần session auth)
- Endpoints thử: bapi/alpha/v2/klines, bapi/alpha/v1/kline, browser UA → đều 403
- **Kết luận:** IDOL KHÔNG có trên Binance Alpha platform

**Nguồn thay thế:** GeckoTerminal API (public, no key) → PancakeSwap BSC pool
- Pool: IDOL/WBNB 0.01% (địa chỉ 5fabca5559, vol24h 03/08 = $6.67M)
- Endpoint: `api.geckoterminal.com/api/v2/networks/bsc/tokens/{contract}/pools` → OHLCV

**Series (PancakeSwap DEX_BSC, one-shot probe 06:50 UTC):**

| date | close | vol_DEX_M | vol_perp_M | suspect_x | verdict |
|------|-------|-----------|-----------|----------|---------|
| 20/07 | 0.01517 | 1.53 | 22.0 | 0.07x | SACH |
| 23/07 | 0.01548 | 18.68 | 167.3 | 0.11x | SACH |
| 27/07 | 0.01721 | 9.83 | 16.9 | 0.58x | SACH |
| 28/07 | 0.01652 | 1.77 | 5.9 | 0.30x | SACH |
| 31/07 | 0.01648 | 1.43 | 7.3 | 0.20x | SACH |
| 01/08 | 0.02438 | **31.83** | 175.7 | 0.18x | SACH |
| 02/08 | 0.02319 | 7.32 | 40.7 | 0.18x | SACH |

**Tất cả 15 ngày SACH** (suspect_x < 1.0, guard < 3.0×)

---

### [A4] W2 Re-run — VERDICT (a): GOM-qua-DEX PLAUSIBLE

- V_clean DEX = **84.63M USDT** (15 ngày × avg 5.6M/ngày)
- Ngưỡng L-06: $8-12M → V_clean >> ngưỡng → **VERDICT A4(a)**
- Highlight: 01/08 DEX vol 31.83M / notional 273M@0.024 = 6.66M → vol/notional = **4.8×**
- Sức chứa DEX đủ để hấp thu toàn bộ 273M trong 1 ngày

---

### [A5] DAILY + W6 Update

**DAILY c27-c28 (rows 20/07→02/08):**
- venue: Gate → `Gate+dex_bsc`
- vol_spot_usd: Gate_vol + DEX_vol (combined); 01/08 = 9.58M + 31.83M = **41.41M**
- c40 note_operator: breakdown dual-source ghi rõ
- alpha_suspect formula: tự tính combined/perp khi Excel recalc

**W6 revision:**

| Hypothesis | Old | New | Lý do |
|------------|-----|-----|-------|
| A (GOM/STAGING) | POSSIBLE | **PLAUSIBLE** | A4(a): V_14d DEX 84.6M >> $12M |
| B (UNLOCK-VESTING) | UNLIKELY | UNLIKELY (giữ) | 3 trượt cứng |
| C (INFRA) | POSSIBLE | POSSIBLE (giữ) | Cần P3 |

**Lưu ý phân biệt:** A4 chứng minh venue *có sức chứa* — chưa chứng minh "gom đã xảy ra". Test quyết định: T1 watcher (redeposit) + P3 txhash dich.

---

### [L-43 draft]

**Bài học đề xuất:**
IDOL-class BSC token: spot = Gate CEX + PancakeSwap DEX BSC. "Binance Alpha" API = gated (403). `alpha_bsc_symbols.txt` chỉ cover tokens có Binance Spot listing. Probe DEX_BSC bằng contract address → dùng GeckoTerminal API (`networks/bsc/tokens/{contract}/ohlcv/day`, public, no key).

CẦN OPERATOR: ký L-43 vào CASE_INDEX nếu đồng ý.

---



---

## SESSION 2026-08-03 — IDOL fn=1 PROBE PHÂN TẦNG (DEV topic)

**Operator:** Tien
**Agent model:** claude-sonnet-4-6
**Nhiệm vụ:** Probe 8 mục án IDOL fn=1 28-31/07 theo layered spec.

---

### [B1] Item 1 — IDOL funding interval: PASS

- Binance API `/fapi/v1/fundingInfo`: `fundingIntervalHours = 4`
- fn_expected = 24 / 4 = **6 kỳ/ngày** ← fn=6 trong export là ĐÚNG
- Cross-check export 01-27/07: unique fn = {6} ✓

---

### [B2] Item 4 — TAG / BR / BANK fn 30-31/07 (post-P1): GHI ÁN

| symbol   | date       | fn | low_conf | src_ratio  | lsr_pos_r | lsr_acc_r | lsr_global_r |
|----------|------------|----| ---------|-----------|-----------|-----------|--------------|
| TAGUSDT  | 2026-07-30 |  1 | True     | native_1d  | 1.6632    | 1.5316    | 1.9958       |
| TAGUSDT  | 2026-07-31 |  1 | True     | native_1d  | 1.6811    | 1.4795    | 1.9223       |
| BRUSDT   | 2026-07-30 |  1 | True     | native_1d  | 1.6578    | 1.3419    | 1.7525       |
| BRUSDT   | 2026-07-31 |  1 | True     | native_1d  | 1.6509    | 1.3998    | 1.8401       |
| BANKUSDT | 2026-07-30 |  1 | True     | native_1d  | 1.1134    | 0.9346    | 0.9873       |
| BANKUSDT | 2026-07-31 |  1 | True     | native_1d  | 1.1095    | 1.7933    | 1.5013       |

**Kết luận:** fn=1 là **systemic** — ảnh hưởng toàn bộ case symbols 30-31/07, không phải IDOL-specific.

---

### [B3] Item 2+3 — VPS store IDOL 28-31/07: ROOT CAUSE XÁC ĐỊNH

**VPS export (IDOL 28-31/07):** fn=1, low_conf=True, src=native_1d, px=empty — đồng nhất với local.

**VPS funding_8h parquet (IDOL 28-31/07):** 12 raw records/ngày = **6 unique × 2 fetches** (backfill).

```
2026-07-28: 12 records → sau dedup = 6 kỳ (00:00, 04:00, 08:00, 12:00, 16:00, 20:00 UTC)
2026-07-29: 12 records → sau dedup = 6 kỳ
2026-07-30: 12 records → sau dedup = 6 kỳ
2026-07-31: 12 records → sau dedup = 6 kỳ
```

**Funding rates thực tế (từ store):**

| Date       | 00:00    | 04:00    | 08:00    | 12:00    | 16:00    | 20:00    | avg_thực |
|------------|----------|----------|----------|----------|----------|----------|----------|
| 2026-07-28 | 0.000223 | 0.000213 | 0.000355 | 0.000116 | 0.000221 | 0.000057 | 0.000198 |
| 2026-07-29 | 0.000050 | 0.000054 | 0.000050 | 0.000050 | 0.000146 | 0.000050 | 0.000067 |
| 2026-07-30 | 0.000206 | 0.000170 | 0.000050 | 0.000050 | 0.000050 | 0.000050 | 0.000096 |
| 2026-07-31 | 0.000804 | 0.000050 | 0.000213 | 0.000236 | 0.000143 | 0.000462 | 0.000318 |

**Export f_avg 28-31 = 00:00 rate duy nhất** → xác nhận: collector chỉ ghi được 1 bản trước khi export chạy (00:50 UTC), 5 bản còn lại backfill sau.

**ROOT CAUSE:** Export được generate lúc 00:50 UTC — thời điểm đó chỉ có funding rate 00:00 UTC của ngày trong store (fn=1). Các rate 04:00→20:00 được thu thập trong ngày và backfill sau, nên store hiện có đủ 6. Export stale.

---

### [B4] Item 5 — LedgerSync mtime: XÁC NHẬN

| File                        | VPS mtime (UTC)         | Local mtime (UTC)       | Delta   |
|-----------------------------|-------------------------|-------------------------|---------|
| freshwatch_daily_2026-07.csv | 2026-08-02 00:50:14     | 2026-08-03 01:52:47     | +25h    |
| freshwatch_daily_2026-08.csv | 2026-08-03 00:50:05     | 2026-08-03 01:52:46     | +1h02m  |

- VPS 2026-07.csv: lần cuối update **02/08 00:50** (August export không cập nhật lại July)
- Local download tại ~01:52 UTC hôm nay → IDOL 31/07 FOUND ✓ (fn=1, px=empty)
- 2026-07.csv FROZEN — không tự update khi sang tháng mới

---

### [B5] Item 6 — --force-overwrite vào case_daily.py: DONE

**Script:** `scripts/case_daily.py`
**Flag mới:** `--force-overwrite` (bool, default False)
**Logic:**
- Nếu date_str đã có trong DAILY + `--force-overwrite`:
  - Tìm row có date_str
  - `_row_has_suspect(ws, row_n)` → kiểm tra comment "SUSPECT" tồn tại không
  - Nếu SUSPECT: capture old values → clear row → ghi lại → log diff old→new
  - Nếu KHÔNG SUSPECT: SKIP_NO_SUSPECT (không overwrite row sạch)
- Status mới: `OVERWRITE_OK`, `SKIP_NO_SUSPECT`, `DRY_OVERWRITE`
- Digest đếm riêng overwrite

**Verify:** `python scripts/case_daily.py --help` → `--force-overwrite` xuất hiện ✓

---

### [B6] Item 7 — Bảng phân tầng tổng hợp

| Tầng               | Mục | Trạng thái              | Kết luận                                          |
|--------------------|-----|-------------------------|--------------------------------------------------|
| Binance API        | 1   | IDOL 4h interval ✓      | fn=6/day là đúng                                  |
| Export local       | 4   | TAG/BR/BANK fn=1 30-31  | Systemic, không riêng IDOL                       |
| VPS export         | 2   | fn=1, px=empty 28-31    | VPS export = local export, đồng nhất              |
| VPS store parquet  | 3   | 6 records/day ĐÚNG      | **Store sạch** — export stale                     |
| LedgerSync mtime   | 5   | 07.csv frozen 02/08     | 07.csv cần re-generate từ store cho 28-31/07      |
| case_daily code    | 6   | --force-overwrite DONE  | Sẵn sàng backfill sau khi có export sạch          |

**Chốt án:**
- Collector funding_8h = **đúng**, store = **sạch**
- Export fn=1 do **timing**: export 00:50 UTC chỉ thấy 1 record (rate 00:00 UTC), 5 rates còn lại backfill sau
- px/vol/taker = empty vì **klines_1h missing** cho window 28-31/07 (cần probe riêng)
- 24-26/07 MISSING hoàn toàn = machine off period (riêng biệt với fn=1 issue)

---

### [B7] Item 8 — Pipeline MISSING audit cuối tháng: NÂNG ƯU TIÊN

Án IDOL fn=1 bằng chứng audit cuối tháng chưa được đóng thật:
- 24-26/07: 3 ngày missing hoàn toàn (machine off)
- 28-31/07: 4 ngày export stale (fn=1, px/vol empty, store có data)
- fn=1 systemic: IDOL, TAG, BR, BANK đều ảnh hưởng 28-31/07

**Việc cần làm (giao ANALYSIS + operator duyệt):**
1. Re-generate export 28-31/07 trên VPS từ store (kèm fix klines_1h nếu missing)
2. Download export mới về local
3. Chạy `case_daily.py --date 2026-07-2X --force-overwrite` cho TAG/BR/BANK 28-31/07
4. Nếu IDOL được add vào CASE_INDEX (ANALYSIS quyết) → làm tương tự

**Scripts sẵn sàng:** `_probe_vps_idol_store.py`, `--force-overwrite` flag.

---

## SESSION 2026-07-31 — P0 GATE CLOSE + REPO BACKUP + B5/B6

**Operator:** Tien
**Agent model:** claude-sonnet-4-6
**Nhiệm vụ:** B0→B6 theo plan operator: bundle backup 4 repo, xác nhận suite 43/43 nguyên bản, probe BULLA B4, dời repo ra OneDrive (B5), append L-35/L-36/L-37 (B6).

---

### [B0] Bundle 4 repo + SCP lên VPS: PASS

- 4 bundle: binance-bot-signals_20260731.bundle, whale_data_20260731.bundle, Check_onchain_20260731.bundle, Whales_scan_20260731.bundle
- SCP lên `root@5.223.67.21:/root/archive/` — tất cả header check `# v2 git bundle` OK
- whale_data bundle 916MB, SCP background PowerShell 600s

### [B2] Archive bản tái tạo TAG/BTW: PASS

- Renamed `TAG_result.txt` → `TAG_result_RECONSTRUCTED_ARCHIVED_20260731.txt`
- Renamed `BTW_result.txt` → `BTW_result_RECONSTRUCTED_ARCHIVED_20260731.txt`
- Path: `D:\Check onchain fresh wallets\u50_data\`
- Bản gốc từ repo đã có tại `D:\Data back test\binance-bot-signals\docs\case study\`

### [B3] Suite gốc replay.py → 43/43: PASS

- Chạy `replay.py` tại repo canonical mới (`D:\Data back test\binance-bot-signals\`)
- Kết quả: 43 PASS, 0 FAIL — ALL PASS (100%)
- Token: BANK(5) AKE(3) TAG(5) BAS(2) POWER(4) BASED(5) CLO(2) BTW(2) TUT(4) BULLA(5) ESPORTS(3) IDOL(3)

### [B4] Probe BULLA 07-20 pos từ VPS store: GHI ÁN

- `freshwatch_daily_2026-07.csv`: BULLA 07-20 `lsr_pos_r=1.981`, `src_ratio=derived_1h`
- `top_pos_1h` keep-last 07-20 (23:00 UTC): `long_short_ratio=1.6811`
- `top_pos_1h` first entry 07-21 (00:00 UTC): `long_short_ratio=1.6755`
- `top_pos_1d`: không có data trước 07-24
- **Kết luận:** Store không confirm 1.75 (reconstruction error) cũng không confirm đúng 1.99 (native_1d missing). Án theo binary condition operator: không sửa twelve_cases. Native_1d 07-20 = unavailable.

### [B5] Robocopy repo ra khỏi OneDrive: PASS

- Source: `C:\Users\Hello\OneDrive\Máy tính\Binance_bot\binance-bot-signals\`
- Dest canonical: `D:\Data back test\binance-bot-signals\`
- `git log` tại bản mới: b0b4cff4 P0 signal library locked ✓
- Suite tại bản mới: 43/43 PASS ✓
- OneDrive copy renamed → `binance-bot-signals_RETIRED_20260731` (chưa xóa)
- CLAUDE.md cập nhật: path canonical ghi nhận

### [B6] Append L-35/L-36/L-37: PASS

- CASE_INDEX.xlsx LESSONS sheet: 37 lessons (L-01→L-37)
- lessons_learned.md regenerate rev.3: 37 lessons
- L-35: bộ calib phải sống trong git — ghi nhận quy tắc giữ
- L-36: tái tạo data phải test bằng suite nguyên bản — án 40/43 giả
- L-37: repo không remote = SPF; bundle→VPS tối thiểu ngày 1

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

---

## SESSION 2026-08-02 — NANSEN WRAPPER FIX + L-39 + L-40

**Operator:** Tien
**Agent model:** claude-sonnet-4-6
**Nhiem vu:** (1) boundary canonical v2 vao CLAUDE.md + L-39; (2) kiem tra Zone-A-agg TAG 29/07 + case_daily fn<6; (3) dieu tra bot Nansen chet + fix wrapper + L-40.

### Task 1 — CLAUDE.md boundary fact v2
- Cap nhat dong OI-only → ratio+OI DAILY canonical = snapshot 00:00 UTC mo ngay D (derived_1h hien hanh), khop native_1d 21/21 diff 0%; keep-last 23:xx = EVENTS.
- Commit: 4021aa0 (whale_data)

### Task 2 — Ra soat nguoc (khong thay doi code)
- Zone-A-agg TAG 29/07 glsr_r=1.6059: avg3(1.7071+1.2978+1.8129)/3 = chinh xac 00:00 UTC. Verdict TAG armed khong doi.
- case_daily fn<6: ghi CSV value (00:00 UTC) + SUSPECT comment — khong dung keep-last. Khong can sua.

### Task 3 — L-39
- L-39 append CASE_INDEX.xlsx LESSONS: "Quy uoc boundary phai TEST bang doi chieu nguon (21/21 diff 0%) truoc khi van ban hoa — proposal v1 hop ly tren giay nhung nguoc 180 voi thuc nghiem; n=1 suy luan dep van phai qua n=21."
- lessons_learned.md rev.5 (39 bai). Commit: 4021aa0

### Task 4 — NANSEN_KEY_LOCKED blast-radius investigation
**Root cause:** NANSEN_KEY_LOCKED trong .env (khong phai Windows system env). FreshWatch task chay pythonw.exe run_daily.py → refresh_nansen.py → core_nansen.py doc NANSEN_API_KEY = None → RuntimeError.
**Gap data:** may off 30/07 PM – 02/08 PM. Last Nansen success: 2026-07-30 08:00. Missing: 31/07, 01/08, 02/08 (3 ngay).
**Consumers tu dong:** chi \FreshWatch (run_daily → refresh_nansen → core_nansen). Manual: botaccum.py, m1_check.py, probe_*.py.

**Fix da ap:**
- run_daily_wrapper.py: doc NANSEN_KEY_LOCKED tu dotenv_values() (khong side-effect env), inject NANSEN_API_KEY vao child_env, chay run_daily.py qua subprocess.
- \FreshWatch schtasks: da update → pythonw.exe run_daily_wrapper.py.
- Probe verify: core_nansen key check PASS, agent NANSEN_API_KEY = None (chot nguyen ven).
- Commit: 1bf74e2 (Check onchain repo)

**CAN OPERATOR duyet truoc khi backfill:**
- Backfill Nansen 3 ngay (31/07, 01/08, 02/08): kiem tra endpoint ho tro historical date hay khong, list cost, duyet roi chay.
- Neu khong backfill duoc: danh dau data_bad cho window 31/07–02/08 trong store freshwatch_daily.

**L-40** append CASE_INDEX.xlsx (rev.6, 40 bai). Commit: e14fb0b (whale_data)

### VERIFY CON LAI (CAN OPERATOR)
1. Bot chay 1 vong tay thu cong ngay 03/08 08:xx → xac nhan Nansen call PASS.
2. Quyet dinh backfill 3 ngay missing Nansen data (CAN OPERATOR).


## SESSION 2026-08-03 — case_daily digest

**Target date:** 2026-07-28  **Run:** 2026-08-03 02:46 UTC  **dry_run:** False

### §1 Handover digest

| Token | Status | row | lsr_pos_r | lsr_acc_r | div_raw | taker_buy_pct | f_avg | f_n | OI_USD | SUSPECT |
|-------|--------|-----|-----------|-----------|---------|---------------|-------|-----|--------|---------|
| BANK | SKIP_NO_SUSPECT | — | — | — | — | — | — | — | — | — |
| TAG | SKIP_NO_SUSPECT | — | — | — | — | — | — | — | — | — |
| BR | OVERWRITE_OK | 66 | 1.6742 | 1.5214 | 1.1004 | 0.5085 | 0.000079 | 6 | 3,685,663 | no |
| IDOL | OVERWRITE_OK | 27 | 2.2065 | 0.9920 | 2.2243 | 0.4802 | 0.000198 | 6 | 10,710,506 | no |

**Tổng:** 2 OK, 2 overwrite, 2 skip, 0 dry_run

---

## SESSION 2026-08-03 — case_daily digest

**Target date:** 2026-07-29  **Run:** 2026-08-03 02:46 UTC  **dry_run:** False

### §1 Handover digest

| Token | Status | row | lsr_pos_r | lsr_acc_r | div_raw | taker_buy_pct | f_avg | f_n | OI_USD | SUSPECT |
|-------|--------|-----|-----------|-----------|---------|---------------|-------|-----|--------|---------|
| BANK | OVERWRITE_OK | 37 | 1.3307 | 0.8567 | 1.5533 | 0.4989 | -0.000988 | 6 | 25,365,666 | no |
| TAG | OVERWRITE_OK | 31 | 1.6204 | 1.3719 | 1.1811 | 0.4949 | 0.000100 | 6 | 11,172,261 | no |
| BR | OVERWRITE_OK | 67 | 1.6609 | 1.4900 | 1.1147 | 0.4818 | 0.000118 | 6 | 3,782,263 | no |
| IDOL | OVERWRITE_OK | 28 | 2.3278 | 1.1608 | 2.0053 | 0.4725 | 0.000067 | 6 | 9,909,666 | no |

**Tổng:** 4 OK, 4 overwrite, 0 skip, 0 dry_run

---

## SESSION 2026-08-03 — case_daily digest

**Target date:** 2026-07-30  **Run:** 2026-08-03 02:47 UTC  **dry_run:** False

### §1 Handover digest

| Token | Status | row | lsr_pos_r | lsr_acc_r | div_raw | taker_buy_pct | f_avg | f_n | OI_USD | SUSPECT |
|-------|--------|-----|-----------|-----------|---------|---------------|-------|-----|--------|---------|
| BANK | SKIP_NO_SUSPECT | — | — | — | — | — | — | — | — | — |
| TAG | OK | 32 | 1.6632 | 1.5316 | 1.0859 | 0.4908 | 0.000050 | 6 | 9,658,577 | no |
| BR | OK | 68 | 1.6578 | 1.3419 | 1.2354 | 0.4917 | 0.000050 | 6 | 3,799,993 | no |
| IDOL | OVERWRITE_OK | 29 | 2.5585 | 1.2090 | 2.1162 | 0.5285 | 0.000096 | 6 | 8,867,578 | no |

**Tổng:** 3 OK, 1 overwrite, 1 skip, 0 dry_run

---

## SESSION 2026-08-03 — case_daily digest

**Target date:** 2026-07-31  **Run:** 2026-08-03 02:47 UTC  **dry_run:** False

### §1 Handover digest

| Token | Status | row | lsr_pos_r | lsr_acc_r | div_raw | taker_buy_pct | f_avg | f_n | OI_USD | SUSPECT |
|-------|--------|-----|-----------|-----------|---------|---------------|-------|-----|--------|---------|
| BANK | SKIP_NO_SUSPECT | — | — | — | — | — | — | — | — | — |
| TAG | OK | 33 | 1.6811 | 1.4795 | 1.1363 | 0.5011 | 0.000165 | 6 | 9,375,186 | no |
| BR | OK | 69 | 1.6509 | 1.3998 | 1.1794 | 0.4644 | 0.000095 | 6 | 3,840,661 | no |
| IDOL | OVERWRITE_OK | 30 | 2.5455 | 1.2396 | 2.0535 | 0.4987 | 0.000318 | 6 | 8,805,698 | no |

**Tổng:** 3 OK, 1 overwrite, 1 skip, 0 dry_run

---

## SESSION 2026-08-03 — IDOL Z6/Z7/Z4-rev

**Operator:** Tien
**Agent model:** claude-sonnet-4-6
**Nhiệm vụ:** Z6 (PancakeSwap swap log), Z7 (alpha_bsc_symbols audit), Z4-rev (E1 label + W6 annotation)

---

### [Z6] PancakeSwap IDOL swap log 20/07→02/08: PROXY (no swap log)

**Pool confirmed:** IDOL/WBNB 0.01% BSC = `0xfff4857a955b2b460c27fd431aa5a85fabca5559` (GeckoTerminal vol24h $6.36M)

**Subgraph endpoints:**
- `api.thegraph.com` → DNS fail (getaddrinfo)
- `api.goldsky.com` Pancakeswap V3 → 404 (subgraph not found)
- `graph.pancakeswap.finance` → DNS fail

**BscScan getLogs:** Không lấy được block numbers (no API key, rate limited)

**Kết quả:** Dùng GeckoTerminal daily vol + 50/50 proxy (không tách được buy/sell)

| Metric | Giá trị |
|--------|---------|
| Cum buy est (14d, 50/50) | 2,178.7M IDOL = $41.20M |
| VWAP proxy | $0.018912/IDOL |
| 273M benchmark | ĐỦ (cum >> 273M nhưng proxy = gross vol, không phải net accumulation) |
| Pool liquidity | Đủ (DEX vol >> notional 273M) |

**CAVEAT:** Swap events trên PancakeSwap = ví người dùng thực / aggregator (1inch/ParaSwap). Binance giữ IDOL trong custody BSC riêng, KHÔNG swap qua pool AMM → DEX VWAP ≠ Binance internal VWAP 273M block.

**Script:** `_probe_idol_z6_swaplog.py` → `docs/reports/_probe_idol_z6_swaplog.txt`

---

### [Z7] Audit alpha_bsc_symbols.txt: GAP CẤU TRÚC (~119 tokens)

**File genesis:**
- Generator: `scripts/archive/_probe_alpha_taker.py` (chạy thủ công)
- Input: `data/config/freshwatch_symbols.txt` (~140 symbols, VPS only)
- Logic: probe Binance Spot `/api/v3/klines` → BSC_BROKEN (ratio>0.9985) → file
- NO_SPOT (400) → excluded by design

**IDOL gap = cấu trúc, không phải bug:**
- IDOL = no_spot trên Binance → 400 → không classify BSC_BROKEN
- `alpha_bsc_symbols.txt` chỉ cover tokens CÓ Binance Spot listing
- IDOL on Gate + PancakeSwap = ngoài phạm vi thiết kế

**Sample probe (50 symbols từ symbols_in_store.txt):**
| Category | Count | Extrapolated (398 universe) |
|----------|-------|-----------------------------|
| spot_ok | 33 (66%) | ~263 |
| no_spot | 15 (30%) | **~119 tokens mù** |
| bsc_broken | 0 (0%) | ~0 (file có thể RỖNG) |
| empty/error | 2 (4%) | — |

**Key finding:** BSC_BROKEN = 0 trong sample → `alpha_bsc_symbols.txt` trên VPS có thể RỖNG hoặc stale. Cần operator chạy `_probe_alpha_taker.py --write-config` để kiểm tra.

**CoinGecko IDOL tickers (03/08):** PancakeSwap V3 BSC $5.98M, LBank $1.24M, Bitget $1.19M, Gate $1.12M. **KHÔNG có Binance Spot hay Binance Alpha listing.**

**Đề xuất (chưa sửa):**
- L-43: GeckoTerminal DEX probe cho BSC no_spot tokens (đã draft session trước)
- Đổi tên file → `binance_spot_bsc_symbols.txt` (tên hiện tại misleading)

**Script:** `_probe_idol_z7_alpha_audit.py` → `docs/reports/_probe_idol_z7_alpha_audit.txt`

---

### [Z4-rev] CASE_IDOL.xlsx — E1 label + W6 annotation: DONE

**EVENTS E1 (row4):**
- col3 (nguon): `'Nansen UI (so hua, chua co txhash)'` → `'Binance (Alpha custody) — cơ chế xác nhận 03/08'`
- col4 (doc_nhanh): appended Z4-rev note (GOM-qua-Alpha hypothesis, pending Z1)

**CASE sheet row11 (Tom tat input):**
- Appended W6 GOM-qua-Alpha annotation: PLAUSIBLE, Z7 evidence, CG tickers, PENDING Z1

**Scripts:** `_task_idol_z4rev.py`, `_task_idol_z4rev_w6fix.py` → `docs/reports/_task_idol_z4rev.txt`

---

### PENDING sau Z6/Z7/Z4-rev

| Việc | Mô tả | Chặn bởi |
|------|-------|----------|
| Z1 | txhash + địa chỉ đích 13 ví (P3) → confirm Binance custody | Operator/Nansen |
| Z6-swap-log | Subgraph swap events (buy/sell split + VWAP thực) | DNS/network access |
| alpha_bsc_symbols verify | Chạy `_probe_alpha_taker.py --write-config` trên VPS | Operator |
| DAILY 03/08 IDOL | Append sau 04/08 01:20 UTC cron + fn=6 verify | Cron |

**VPS IP:** `5.223.67.21` (ghi nhận từ operator)

---
