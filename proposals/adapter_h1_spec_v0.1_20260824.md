---
type: adapter-spec
name: H1 balance adapter (bot Nansen snapshot → DayData compose)
version: v0.1 (24/08/2026)
status: SIGNED — operator ký chat 24/08 tại ĐIỂM DỪNG 1 với 3 sửa
signed_by: operator (chat 24/08)
consumer: GOM-H (mm_stage_machine_v1 §6 T0.1/H1 provisional gate)
schema_source: D:/Check onchain fresh wallets/snapshots/YYYY-MM-DD.json (A1 forensics)
---

# adapter-H1-spec v0.1 — bot Nansen snapshot → H1 balance rule input

**Ký:** operator chat 24/08 tại ĐIỂM DỪNG 1 với 3 sửa (i)/(ii)/(iii) applied.

## Spec (7 mục, SIGNED nguyên văn với 3 sửa)

1. **Nguồn**: `D:/Check onchain fresh wallets/snapshots/YYYY-MM-DD.json` (daily cron 01:00 UTC · `cron_runner.py`).

2. **Input schema** (từ A1 forensics — 31 cols per row):
   - `token` (contract 0x hex, KHÓA CANONICAL — L-51 SAFE)
   - `symbol` (display, KHÔNG dùng làm khóa)
   - `exchange_balance_tokens` (MỨC balance level, T-1 UTC)
   - `exchange_balance_date` (T-1 UTC ISO)
   - `exchange_prev_tokens` (T-2 UTC prev level)
   - `exchange_prev_date` (T-2 UTC ISO)
   - `exchange_delta_pct` (per-day change bot đã compute)
   - `api_failed`, `exchange_api_failed` (status flags)
   - Bỏ row nếu `exchange_api_failed=true` (giữ `api_failed=true` → xử lý theo mục 6).

3. **Output bảng** (per token, per date):
   - `date` = `exchange_balance_date` (T-1 UTC, KHÔNG snapshot filename date — filename là ingest date T)
   - `exch_balance_level` = `exchange_balance_tokens` (float, tokens count)
   - `kho_step_pct` = `exchange_delta_pct` (bot compute). Fallback compute từ prev nếu null:
     `(balance − prev) / prev`; nếu `prev = 0` hoặc null → N/A (KHÔNG chia-0 câm, kiểu CAP ngày listing 0→130M)
   - `source_file` = basename JSON snapshot
   - `ingested_at` = `last_run.json.last_success` (ISO UTC)
   - Cột `flags` liệt kê tất cả cờ áp dụng (per row): `[SYMBOL-MAP-UNVERIFIED]`, `[LAST-SEEN-2D]`, `[MISSING-SNAPSHOT]`, `[API-FAILED]`.

4. **Token map**: dùng `token` (contract 0x) làm khóa canonical. Symbol column mang cờ `[SYMBOL-MAP-UNVERIFIED]` khi contract missing (per L-51). fw-139 mapping cần bảng contract→symbol_perp riêng (DEV write, chưa có).

5. **H1 rule apply** (per DEV-BỔ-SUNG v2 GOM-H section):
   Tồn tại cửa sổ ≤3 ngày liên tiếp với:
   `|balance(cuối) − balance(đầu)| / balance(đầu) ≥ 0.10`
   T0.1 evaluate tại ngày cuối cửa sổ.
   `balance(đầu) = 0` hoặc null → **H1 = N/A** ngày đó (không fire, không False-câm — phân biệt False vs N/A trong output).

6. **Coverage gap** (operator sửa (ii) 24/08):
   - **Option (b)+(c) combined**: last-seen backfill ≤2d với cờ `[LAST-SEEN-2D]`. Quá 2d → `N/A + [MISSING-SNAPSHOT]`.
   - **KHÔNG hạ `MIN_LIQUIDITY`** của bot (giữ $400K threshold hiện tại).
   - Áp dụng cho tất cả token khi snapshot missing (bao gồm AKE/BTW khi bị drop bởi liquidity filter).

7. **Ngày API-failed** (operator sửa (iii) 24/08):
   - `api_failed=true` (như 08-23/24 hiện tại) → **N/A + `[API-FAILED]`** cờ.
   - Adapter **KHÔNG retry**, **KHÔNG kích bot**. Lấp bằng ops tay nếu cần (operator quyết case-by-case).

8. **Coverage permanent N/A** (operator sửa (i) 24/08):
   fw-only 7 tokens KHÔNG có bot data. **Sửa (i): BỎ AKE/BTW** (có data lịch sử từ 06-30/07-05, chỉ tạm drop bởi liquidity filter — dùng option (b)+(c) fallback).
   **N/A permanent = 5 tokens**: `1000000BOB`, `1000CHEEMS`, `ARX`, `FF`, `PIEVERSE` — H1 luôn N/A cho những token này (không có contract mapping trong bot universe).

## Coverage 8 CASE (theo A1 forensics)

| CASE | Contract | first_has_balance | Note |
|------|----------|-------------------|------|
| BANK | 0x3aee7602b612de36088f3ffed8c8f10e86ebf2bf | 2026-06-30 | active |
| TUT  | 0xcaae2a2f939f51d97cdfa9a86e79e3f085b799f3 | 2026-06-30 | active |
| CYS  | 0x0c69199c1562233640e0db5ce2c399a88eb507c7 | 2026-06-30 | active |
| **AKE** | 0x2c3a8ee94ddd97244a93bc48298f97d2c412f7db | 2026-06-30 | active with liquidity filter drop → last-seen fallback |
| **BTW** | (contract chưa lấy — cần probe historical snapshot có balance) | 2026-07-05 | active with liquidity filter drop → last-seen fallback |
| HEMI | 0x5ffd0eadc186af9512542d0d5e5eafc65d5afc5b | 2026-06-30 | active (bal=null in 08-22 nhưng row present, cần probe) |
| ON   | 0x0e4f6209ed984b21edea43ace6e09559ed051d48 | 2026-06-30 | active |
| CAP  | 0x99991c6aabba5a096f24f250b73580f5179b9999 | 2026-07-05 | active |

## H1-contingency status

**KHÔNG kích hoạt** (verified A1): bot schema có `exchange_balance_tokens` (MỨC balance level) + `exchange_delta_pct` (bot pre-computed). H1 rule original áp trực tiếp trên `balance(cuối)−balance(đầu)/balance(đầu)`. ANALYSIS KHÔNG cần viết lại H1.

## Cross-ref

- A1 forensics: `docs/reports/_p0_store_vol_dup_forensics_20260821.md` (session này, PHA A A1)
- DEV-BỔ-SUNG v2: NGƯỠNG TẠM GOM-H section T0.1/H1/H2/H3/NaN semantics/Compose
- L-51: fail-loud symbol-map (contract canonical)
- L-56: guard exact-match before edit
- CLAUDE.md: TẦNG HUMAN #1 KHÔNG gọi Nansen API — adapter chỉ ĐỌC snapshot cache
