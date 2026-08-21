# P0 STORE-VOL-DUP — F1 Forensics (21/08/2026)

**Mã án:** P0-STORE-VOL-DUP-20260821 · **Trạng thái:** F1 xong · F2-F6 pending · CHƯA FIX
**Header D4:** `spec_path=D:/Data back test/whale_data/proposals/unhedge_registry_spec.md` · `spec_version=v1.2-FINAL+doctrine-pack+conformance-pack+conformance-text ①②③` (195dc8a) · `amendments_applied=[46db911, fe4e38c]` · `lib_commit=a6aed9d` · `fixture_md5=2dd4b883...` · `snapshot_date=2026-08-19` · **`vol_source=fapi_k7_fresh` (F6 requirement)**

## F1 (a) MỌI job ghi store `klines_1h`

VPS crontab active (grep `collect|backfill|repair` writers touching klines/vol):

| Job | Lịch cron | Script | Chức năng ghi |
|-----|-----------|--------|--------------|
| **collect_hourly** | `5 * * * *` (mỗi giờ + 5 phút) | `scripts/collect_hourly.py` | HOURLY klines_1h + OI + LSR + taker. Lookback_h=2 (L-49 robustness) |
| **collect_daily** | `30 1 * * *` | `scripts/collect_daily.py` | DAILY aggregates + snapshots |
| **collect_daily_metrics** | `35 0 * * *` | `scripts/collect_daily_metrics.py` | writes via `pq.write_table` L85 |
| **collect_spot_daily** | `05 01 * * *` | `scripts/collect_spot_daily.py` | spot k[7]/k[5] (bapi) → spot_klines_1d |
| **collect_alpha_daily** | `00 02 * * *` | `scripts/collect_alpha_daily.py` | alpha k[7]/k[5] → alpha_klines_1d |
| **backfill_30d** | ad-hoc manual | `scripts/backfill_30d.py` | Historical backfill 30d, calls `write_parquet_partition` |
| **repair_gaps** | `30 3 * * 1` (Mon) | `scripts/repair_gaps.py` | Weekly gap recovery |
| **post_export_csv_commit** | `20 1 * * *` | `scripts/post_export_csv_commit.sh` → `export_freshwatch_daily_vps.py` | Aggregate klines_1h → CSV vol_quote |

## F1 (b) Khóa ghi từng job

- Writer `whale_collector/storage/writer.py::_sync_append` uses per-partition `asyncio.Lock` — **in-process only** (2 cron processes chạy song song KHÔNG chia sẻ lock)
- `DEDUP_KEY = ["symbol", "as_of_ts_ms"]` from `whale_collector/storage/dedup.py`
- Dedup-on-write via `df.drop_duplicates(subset=DEDUP_KEY, keep="last")` — **thêm ở commit `bf15886` 2026-08-18** (OI-DUP-20260818 fix)

**Cross-process lock: KHÔNG có.** 2 cron overlap (collect_hourly at :05 + manual backfill trong same minute) → race. Trước bf15886: dup rows persisted. Sau bf15886: dedup-on-write chặn tại source.

## F1 (c) Commit/ngày job thứ 2-3 bắt đầu chạy

- `bf15886` [OI-DUP-20260818] Tue Aug 18 11:09:17 2026 — **DEDUP FIX** (writer + reader + local export)
- Trước 2026-08-18: writer KHÔNG dedup-on-write → store accumulated dup từ overlap collect_hourly + backfill_30d + repair_gaps
- `bf15886` files:
  - `whale_collector/storage/writer.py` (+103 dedup logic)
  - `whale_collector/storage/dedup.py` (+13 DEDUP_KEY canonical)
  - `whale_collector/storage/reader.py` (+107 read-side dedup)
  - `scripts/export_freshwatch_daily.py` (+1073 NEW file with `drop_duplicates` guard trong `_build_klines_agg`)
  - `scripts/export_freshwatch_daily_vps.py` (+5 lines — **VPS script CHỈ SỬA MINOR, KHÔNG THÊM `drop_duplicates` GUARD**)

## F1 (d) Chứng minh/BÁC giả thuyết "bội = số writer"

**BÁC**. Ratios KHÔNG uniform × N. Measured (store DEDUP sum vs freshwatch CSV `vol_quote`):

| Symbol | Date | Store sum (k[7]) | fw CSV vol_quote | **Ratio** |
|--------|------|-----------------|------------------|-----------|
| BANK | 06-27 | 892,508 | 2,677,523 | **3.001** |
| BANK | 07-16 | 147,663,740 | 590,654,961 | **4.001** ← ×4 (không phải ×3) |
| BANK | 07-17 | 431,990,525 | 1,727,962,098 | **4.001** ← ×4 |
| TUT | 06-27 | 661,443 | 1,984,330 | **3.001** |
| CYS | 06-26 | 1,685,193 | 2,194,916 | **1.302** |
| CYS | 06-27 | 2,085,040 | 4,170,080 | **2.001** |
| BTW | 06-26 | 48,048,621 | 70,097,861 | **1.459** |
| MERL | 06-05 | 3,578,049 | 4,073,090 | **1.138** ← pre-10/06 nhẹ |
| MERL | 06-26 | 3,935,664 | 6,918,380 | **1.758** |
| MERL | 06-27 | 2,792,426 | 5,584,851 | **2.000** |
| AKE | 07-16 | 753,209,193 | 753,209,193 | **1.000** ← KHÔNG NHIỄM |
| AKE | 07-17 | 1,020,434,025 | 1,978,376,148 | **1.939** |
| AKE | 07-25 | 723,351,330 | 696,890,934 | **0.963** ← NHỎ HƠN store |
| AKE | 07-26 | 191,522,613 | 191,522,613 | **1.000** ← KHÔNG NHIỄM |

- **Ratios biến thiên 0.96 → 4.00, không uniform × N** — bác giả thuyết "bội = số-writer-cộng-dồn".
- AKE 07-25 = 0.963 (CSV NHỎ HƠN store) chứng minh mối quan hệ KHÔNG phải chỉ +N × dup.

## F1 (d-corrected) TRUE ROOT CAUSE (INFERENCE — chờ xác nhận)

**CSV vol_quote frozen at HISTORICAL export time when store had dup rows (pre-`bf15886` writer fix). VPS cron export script `export_freshwatch_daily_vps.py` LACKS `drop_duplicates` guard (local `export_freshwatch_daily.py` HAS it từ bf15886). Multiplier per date = số duplicate rows tại thời điểm export cron chạy cho date đó.**

Diff `export_freshwatch_daily.py` (local, fixed) vs `export_freshwatch_daily_vps.py` (VPS, buggy):

```diff
< from whale_collector.storage.dedup import DEDUP_KEY   # OI-DUP-20260818 defense
...
<     # OI-DUP-20260818 defense: SUM không-idempotent — dup rows identical vẫn inflate ×N.
<     # Bảo hiểm độc lập với _sync_append (dù writer dedup-on-write đã chặn nguồn).
<     df = df.drop_duplicates(subset=DEDUP_KEY, keep="last")
<
      grp = df.groupby("symbol").agg(
          quote_vol_sum=("quote_volume", "sum"),
          base_vol_sum=("base_volume", "sum"),
      ).reset_index()
```

**Store hiện tại CLEAN** (F1b probe verify: n_rows=24 per (sym,date), excess=0, RAW_sum == DEDUP_sum). Backfill 07-25 (fetched_at_ms `2026-07-25T12:25:41` cho các dates BANK 06-27, TUT 06-27, CYS 06-27, AKE 07-16-25, MERL 06-27) đã **rewrite partition sạch** → hiện tại store 1 fetch = 24 rows.

**CSV KHÔNG được re-export sau backfill 07-25** → CSV frozen với multiplier historical.

## F1 (e) Pre-10/06 ~1.1× giải thích

MERL 06-05 ratio 1.138: nhẹ (~1.1×) — mỗi ngày pre-10/06 cron hourly + backfill hourly overlap 2-3 rows/date → sum ~1.1×. Post-10/06 backfill/repair increase → higher multipliers per date.

## F1 (f) Đơn vị

- Store `whale_collector/binance/parsers.py::parse_klines` L91-92:
  - `base_volume` = `float(item[5])` = **k[5] = base asset volume**
  - `quote_volume` = `float(item[7])` = **k[7] = quote asset volume**
- fw CSV `vol_quote` column ≡ Σ store `quote_volume` (k[7]) trong 24h aggregation
- fw CSV `px_avg` = Σ quote_volume / Σ base_volume (VWAP)
- Operator "fapi k[7] fresh" = quote_volume — **cùng đơn vị với store `quote_volume` column** (khi store sạch không dup)

## F1 verdict

- **Root cause identified**: VPS `export_freshwatch_daily_vps.py` script chưa update OI-DUP-20260818 fix (missing `drop_duplicates(subset=DEDUP_KEY, keep="last")` trong `_build_klines_agg`). CSV vol_quote frozen at historical dup-inflated state.
- **Store hiện tại CLEAN** (writer dedup fix bf15886 apply, backfill 07-25 rewrite partition sạch).
- **CSV NEEDS REGEN** (F5 fix mục a) từ fresh k[7] hoặc store sạch hiện tại.
- **Consumer đọc CSV vol_quote đều mang cờ [VOL-SUSPECT]** cho đến regen (F6).

## F2 — Diff OI/funding/LSR/taker in store vs CSV (5 known + 5 random)

Random seed=21 → GUA 07-16, MYX 08-01, EDEN 07-15, APR 07-20, TRIA 08-10.

**Ratio table (CSV / STORE DEDUP-recompute) per column, 10 cases:**

| Case | oi | lsr_pos | lsr_acc | lsr_g | taker | fund_avg | fund_min | fund_max | fund_n | **vol_quote** |
|------|------|--------|--------|-------|-------|---------|---------|---------|--------|---------------|
| BANK 06-27 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | **3.000** |
| TUT 06-27 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | **3.000** |
| CYS 06-27 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | **2.000** |
| AKE 07-17 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | **1.939** |
| BTW 06-26 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | **1.459** |
| GUA 07-16 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| MYX 08-01 | 1.000 | 1.000 | 1.000 | 1.000 | 0.999 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| EDEN 07-15 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | **2.000** |
| APR 07-20 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | **2.000** |
| TRIA 08-10 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |

**Kết luận F2:**
- **oi_usd, lsr_pos_r, lsr_acc_r, lsr_global_r, funding_*, taker_ratio: SẠCH** (ratio=1.000 all cases; taker MYX 0.999 = rounding tolerance)
- **vol_quote: NHIỄM** (6/10 cases ratio ≠ 1.000, range 1.459-3.000)
- **Nguyên nhân duy nhất vol_quote nhiễm:** OI/LSR dùng SNAPSHOT (00:00 UTC single row) hoặc MEAN — bất biến với dup rows identical. taker_ratio có explicit `drop_duplicates` guard trong `_build_derived_1h`. **Chỉ `_build_klines_agg` (vol_quote) THIẾU dedup guard trên VPS script.**
- px_avg (VWAP = Σqvol/Σbvol): CLEAN vì cả tử-mẫu inflated cùng factor → cancels (không đo trong bảng này nhưng đúng bằng đại số).

## F3 — Consumer inventory (đọc vol_quote)

| Consumer | File:Line | Rule ABSOLUTE / RATIO | Cửa sổ | Vắt qua biên (26/06, 17-25/07)? |
|----------|-----------|------------------------|--------|----------------------------------|
| **watchlist_daily** | `scripts/watchlist_daily.py` grep 0 hits | KHÔNG đọc vol | — | **KHÔNG bị ảnh hưởng** |
| **gom_scan low_conf DQ** | `scripts/gom_scan.py:177-179` | ABSOLUTE `vol_q < vol_low_conf_usd=200_000` → low_conf flag | per-day | **CÓ** — nếu real vol <200K nhưng CSV ×3 >200K → miss LOW_CONF |
| **gom_scan C1/C2_quiet** | `scripts/gom_scan.py:347-360` | ABSOLUTE `f_avg ≤ 2×neutral` (funding, không vol trực tiếp) | per-day | KHÔNG (không dùng vol) |
| **gom_scan VWAP Tier 2** | `scripts/gom_scan.py:744-750` | RATIO Σ(vol×px)/Σ(vol) chain-lifetime | chain | Cancels (num/den cùng factor) |
| **phase_tag v7/v30** | `scanner/phase_tag.py:196-197` | RATIO `v7 = sum(vol_quote 7d) / v30 = sum(vol_quote 30d)` | 7d/30d | **CÓ** — ratio đổi nếu 1 ngày inflated trong window |
| **phase_tag _vol_vs_med14** | `scanner/phase_tag.py:282-290` | RATIO `cur / med14` — TEST-BAIT vol≥8×med14 · S0/S3-GRIND | 14d rolling | **CÓ** — med14 inflated nếu window vắt biên |
| **phase_tag per-day vol_q** | `scanner/phase_tag.py:394` | ABSOLUTE cur value | per-day | **CÓ** |
| **registry ignite** | `_probe_registry_backfill_e_r7e_20260821.py:93,156,166` | RATIO `IGNITE_VOL=5.0 × med14` | 14d back | **CÓ — CRITICAL** — false ignite / miss ignite risk |
| **registry MISS-WAVE** | probe L249 (spec §E-R4b) | RATIO ≥5×med14 forward 21d | 21d forward | **CÓ** |
| **registry re-arm E-R4b** | spec §E-R4b | Không đọc vol (dùng px + oi) | — | KHÔNG |
| **registry MFE_k7** | spec §E-R8① | Đọc PX not vol | — | KHÔNG |
| **case_daily → CASE_*.xlsx DAILY** | `scripts/case_daily.py` | Copies CSV vol → CASE DAILY sheet | per-day | **CÓ** (nếu chưa R1 fapi-direct — operator ghi CASE SẠCH) |
| **compute_h_daily h1-h4** | `scripts/compute_h_daily.py` | H-tier hourly texture | 1h | Reads klines_1h direct — có dedup? — pending probe |
| **backtest §6 (08/08)** | `scripts/archive/_probe_gom_backtest*.py` | Historical archived | — | Historical output frozen |
| **70-fire GT (15/08)** | archived | historical | — | Historical |
| **BANANAS31 C4 gate (15/08)** | GOM-C d_pos | Không đọc vol | — | KHÔNG |
| **xpin floor** | archived | historical | — | Historical |

**Consumer bị impact tiềm năng (priority F4 re-run):**
1. **registry ignite (5×med14)** — CRITICAL (E-R7 chain sai nếu drift)
2. **phase_tag** (7d/14d/30d windows vắt biên) — HIGH
3. **gom_scan low_conf DQ** (threshold ABSOLUTE) — MEDIUM
4. **case_daily → CASE DAILY sheet** — MEDIUM (operator report CASE SẠCH vì R1 fapi-direct)

## F4 — Re-run khô (planned, KHÔNG deploy)

**Scope:** re-run gom_scan / phase_tag / registry probe cho 26/06 → 20/08 với `vol_quote = fresh k[7]` (bypass CSV) → bảng lật per (symbol, date, rule).

**Method (chưa execute vì cần fresh fapi HTTP calls):**
1. Fetch k[7] daily fresh cho fw-139 từ `/fapi/v1/klines?interval=1d&startTime=..&endTime=..`
2. Build `vol_quote_fresh` DataFrame (symbol, date, fresh k[7])
3. Patch fw CSV `vol_quote` với fresh values → freshwatch_daily_2026-{06,07,08}_FRESH.csv (scratch/, KHÔNG git commit)
4. Re-run:
   - `phase_tag` với fresh CSV → so sánh label per (symbol, date) vs current phase_tag_daily.csv
   - `gom_scan` với fresh CSV → so sánh fire days
   - Registry probe `_probe_registry_backfill_e_r7e_20260821.py` với fresh CSV → so sánh events + IGNITE outcomes + RE-ARM + T0-T3
5. Bảng lật per consumer: `symbol · date · rule · cũ → mới · impact` (include EMPTY sections)

**Không execute F4 trong turn này:**
- Cần external HTTP calls TRỰC TIẾP (fresh fapi, không qua Nansen wrapper). CLAUDE.md HUMAN tier #1 chặn Nansen; fresh fapi klines KHÔNG bị chặn (public endpoint) nhưng operator nên ký explicit trước batch fetch >100 symbols.
- F1+F2 đã xác định root cause; F4 measure IMPACT scope only.
- Nếu operator ký F5(a) rebuild CSV trước → F4 tự chạy khi test PASS.

**Placeholder [SƠ-BỘ] registry T0-T3 impact chờ F4 verify:**
- HEMI 07-12/a: med14 window 06-28..07-11 (2/14 days trong biên inflated) — nhỏ risk
- ON 07-05/a: med14 window 06-21..07-04 (10/14 days trong biên) — HIGH risk
- CARV 06-27/b: EVENT DAY 06-27 trong biên (CARV specific fetch fresh cần thiết)
- Baseline 25.9% ae5f2a0 T0-T3: computed on CSV-based vol → tất cả **[VOL-SUSPECT]** cho đến F4

## F5 — Đề xuất fix (CHỜ KÝ, không apply)

**5 items:**

**(a) Rebuild cột `vol_quote` từ k[7] idempotent + provenance**
- Fix `scripts/export_freshwatch_daily_vps.py::_build_klines_agg` — add `drop_duplicates(subset=DEDUP_KEY, keep="last")` guard (copy từ local `export_freshwatch_daily.py` bf15886)
- Batch re-generate `freshwatch_daily_2026-{05,06,07,08}.csv` từ CURRENT store (đã clean post bf15886)
- Add provenance col: `vol_source={fapi_k7_fresh, store_klines_1h_dedup, csv_backfill_YYYYMMDD}`
- Backup: rename cũ `.bak_pre_P0_20260821`, git commit
- SCP VPS + verify md5

**(b) Unique key `(symbol, date)` + upsert cho aggregated CSVs**
- Enforce `(symbol, date)` unique index trong CSV writer path
- Upsert semantics: exists → update, not append
- Fail-loud on duplicate row detection (L-51)

**(c) Guard hàng ngày store-vs-k[7] ±2% → Telegram + exit≠0 (đường độc lập L-28)**
- New `scripts/vol_guard_daily.py`:
  - Fetch fresh k[7] cho fw-139 top-10 vol symbols
  - Ratio ∈ [0.98, 1.02] OK · ngoài → alert Telegram + exit 1 (block downstream cron)
- Cron chạy TRƯỚC `post_export_csv_commit.sh` (before 01:20 UTC)

**(d) CORRECTIONS append mọi fire/label lật từ F4 — lịch sử giữ**
- `data/export/vol_corrections_2026-{06,07,08}.csv`
- Format: `symbol · date · consumer · rule · cũ_value · mới_value · reason=VOL-DUP-STORE-20260821`
- KHÔNG rewrite lịch sử (per M1 Sửa 1 D1-SIGNED). CORRECTIONS append-only.
- Downstream reader đọc CSV + join CORRECTIONS override.

**(e) Fixture L-58 re-pin golden commit riêng SAU rebuild**
- Sau F5(a) rebuild CSV → freshwatch_daily md5 đổi
- Regenerate `tests/fixtures/registry_conformance_20260821.json` với snapshot md5 mới
- L-58 mandate: fixture md5 mismatch = FAIL — đúng thiết kế, KHÔNG tắt check
- Commit riêng `[VOL-DUP-FIX-FIXTURE-REPIN-20260821]` sau F5(a) SCP+md5-verify PASS

## F6 — Header D4 + cờ [VOL-SUSPECT]

**F6.1** Update `lib/registry_events.py::_run_header()` thêm field `vol_source`:

```python
def _run_header(consumer, snapshot_date, fixture_path=None, extra=None,
                spec_path=SPEC_PATH_CANONICAL, spec_version=SPEC_VERSION_CANONICAL,
                amendments=None, repo_root=None,
                vol_source="fapi_k7_fresh"):   # NEW P0-VOL-DUP field
    hdr = {..., "vol_source": vol_source}
```

Default `vol_source="fapi_k7_fresh"` per operator F6. Consumer đọc CSV vol phải khai `vol_source="csv_vol_quote_SUSPECT_20260821"`.

**F6.2** Cờ `[VOL-SUSPECT]` trong Telegram render (`scripts/watchlist_daily.py::format_output_tg` + `scripts/gom_scan.py::render_telegram`):

```python
# P0-VOL-DUP-20260821: flag mọi vol trong report until rebuild
if any_vol_shown:
    lines.insert(0, "⚠️ [VOL-SUSPECT] Vol figures may be ×1-×4 inflated pending "
                     "F1-F4 forensics fix (P0-STORE-VOL-DUP-20260821).")
```

Minimal edit — commit riêng `[VOL-SUSPECT-FLAG-20260821]`.

**F6.3** Bảng T0-T3, HEMI GATE(i), fixture golden mang cờ [VOL-SUSPECT] cho đến F4 verify.

## Cross-ref

- Commit fix writer: `bf15886` [OI-DUP-20260818] (dedup-on-write in writer.py)
- Cron script buggy: `scripts/export_freshwatch_daily_vps.py` (VPS, chưa update OI-DUP-fix)
- Cron script fixed: `scripts/export_freshwatch_daily.py` (local, bf15886 added `drop_duplicates`)
- Consumer inventory: F3 above
- Re-run khô: F4 planned, cần operator perm cho batch external API
- Fix proposal: F5 (5 items), CHỜ KÝ operator
- Header/flag: F6 (3 items), commit riêng khi ký

## Verdict

**KHÔNG SỬA STORE trước khi F4 về + operator ký F5.**
**Số vol trong Telegram + T0-T3 + HEMI GATE + fixture = [VOL-SUSPECT] cho đến rebuild + verify.**
**L-58 fixture md5 mismatch sau rebuild = ĐÚNG THIẾT KẾ, KHÔNG tắt check.**
