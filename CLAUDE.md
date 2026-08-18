\# FreshWatch — Agent Rulebook (ký 30/07/2026)



\## TẦNG HUMAN (chặn cứng, không tự làm)

1\. KHÔNG gọi bất kỳ API Nansen nào (mọi endpoint api.nansen.ai) —

&#x20;  kể cả khi task có vẻ cần. Cần data on-chain → ghi vào

&#x20;  `agent\_log.md` mục "CẦN OPERATOR" và dùng nguồn 0-credit

&#x20;  (BscScan free, export sẵn có) thay thế.

2\. KHÔNG ghi vào thresholds.yaml (CONFIRM). Được phép: chạy

&#x20;  regression, soạn changelog, chuẩn bị diff trong

&#x20;  proposals/yaml\_change\_<date>.md — cú apply cuối là operator.

3\. KHÔNG điền cột verdict trong CASE\_<TOKEN>.xlsx sheet CASE.

&#x20;  Được phép: append DAILY, chấm chốt canh, ghi "verdict đề xuất"

&#x20;  vào agent\_log.md.



\## TẦNG AUTO-THEO-SPEC (tự làm nếu PASS tiêu chí số)

\- Verify snapshot: daily\_2026-07.csv 526 dòng + schema §9 +

&#x20; TAGUSDT funding\_n=6 → PASS → tự commit.

\- Canh ngày TAG/BR: đọc export (KHÔNG qua Zone A), append DAILY,

&#x20; chấm chốt §1 handover. div đọc trên avg3. OI/med14 canonical =

&#x20; signals.py (window ending ngày-trước-check).

\- MISSING count, backfill 0-call, probe read-only: tự chạy,

&#x20; output ghi file.



\## TẦNG AUTO (tự do)

\- Mọi thứ read-only, test, regression, SCREEN yaml, sửa code bot,

&#x20; deploy theo Item đã ký, commit.



\## FACTS ĐÃ CHỐT (không hỏi lại)

\- Snapshot phủ TOÀN universe 527 by design (xác nhận 08-11 qua gom_state.json 527 tokens); filter 137 chỉ ở SCREEN.

\- Án R1: export lành, bug ở join ledger (nghi symbol format

&#x20; TAG vs TAGUSDT hoặc date-join). Fix join, KHÔNG đụng export.

\- Excel oi\_vs\_med14 ≠ định nghĩa fire (window khác).
\- ratio+OI DAILY canonical = snapshot 00:00 UTC mở ngày D (derived_1h hiện hành), khớp native_1d 21/21 diff 0%; keep-last 23:xx = EVENTS, không vào cột DAILY. (chốt 31/07, proposal v2)
\- Repo canonical binance-bot-signals: `D:\Data back test\binance-bot-signals\` (chuyển 31/07 — OneDrive copy đã RETIRED). replay.py + 12 calib files ở đây.
\- Calib files chỉ đọc từ repo `D:\Data back test\binance-bot-signals\docs\case study\` — KHÔNG dùng bản rời trong `D:\Check onchain fresh wallets\u50_data\` (đã rename _LOOSE_RETIRED_20260731 ngày 31/07).



\## CẤU TRÚC THƯ MỤC (L-42, ký 03/08/2026)

```
scripts/           — script SỐNG: job chạy lịch, tool dùng lại
scripts/archive/   — probe/task ĐÃ XONG án (giữ vết, khỏi mắt)
docs/reports/      — report đang sống; đã xử xong → docs/reports/archive/
docs/case_files/   — chỉ CASE_*.xlsx + CASE_INDEX (cấm CSV song song)
docs/handover/     — file liên-topic từ ANALYSIS → agent (kênh chính thức thay đính-kèm)
proposals/         — active; SUPERSEDED/đã ký → proposals/archive/
scratch/           — data dump tạm (không commit)
backtest/          — module Python sống
```

**docs/handover/ quy ước (ký 11/08/2026):**
- Tên file: `<topic>_<YYYYMMDD>.md` (ví dụ: `gom_c_cookie_gate_20260811.md`)
- Khi ANALYSIS commit file vào đây: agent đọc, xác nhận từng file mở được + một dòng tóm mỗi file vào agent_log.md
- File trong handover/ không xóa sau đọc — giữ vết lịch sử; ANALYSIS archive bằng subfolder archive/ khi cần

Quy ước vòng đời artifact:
- Probe/task mới: tên `_probe_<án>_<YYYYMMDD>.py` / `_task_<mô_tả>_<YYYYMMDD>.py`
- Đóng án → agent TỰ move vào archive trong commit đóng án (KHÔNG đợi dọn định kỳ)
- Root chỉ chứa: tool sống (scripts không có cron-prefix), config, probe đang chạy dở

## KỶ LUẬT

\- **DATA PROVENANCE (L-48, ký 09/08/2026):** Mọi gate/rescan/backfill PHẢI khai
  header provenance tối thiểu 4 trường: `data-source` (file path hoặc endpoint),
  `machine` (local scratch / VPS canonical), `date-range` (YYYY-MM-DD → YYYY-MM-DD),
  `code-commit` (git hash). Gate dựng trên scratch local KHÔNG được swap lên VPS.
  Chỉ gate chạy trên VPS export canonical (path khai rõ) mới đủ tư cách production.

\- Mỗi session ghi agent\_log.md: việc + lệnh + kết quả số.

\- Commit message tiếng Việt ngắn, một change-set một chủ đề.

\- Output lớn ghi file, không đổ chat.

\- Số lệch giữa hai nguồn → ghi án vào agent\_log.md, không tự chọn.

\- DAILY data chỉ sống trong CASE\_<TOKEN>.xlsx sheet DAILY — cấm sinh CSV song song trong docs/case\_files/ (án 30/07, tái phạm 1 lần).

\- Ratio fn=1 (native\_1d low\_conf) → không dùng làm số chốt. Fallback: Zone A aggregate từ ledger\_v2.xlsx CAMPAIGNS, ghi rõ nguồn "Zone-A-agg". Quy ước tạm cho đến khi P1 screener snapshot 5-phút chạy ổn định.

\- lessons\_learned.md là view sinh từ sheet LESSONS của CASE\_INDEX.xlsx — mọi edit vào sheet, md chỉ regenerate (không edit md trực tiếp).

\- CẤM chạy `python -c` inline. Mọi đoạn Python ghi ra file `_probe_*.py` / `_task_*.py` rồi chạy `python <file>.py`. Lý do: (a) lệnh inline phức tạp luôn bị permission prompt chặn, (b) script ra file = audit được, chạy lại được — đúng kỷ luật probe→raw→duyệt.
\- Chạy ở chế độ skip-permissions. Chốt Nansen nằm ở tầng env (NANSEN\_KEY\_LOCKED) — CẤM tự rename ngược, cấm hardcode key, cấm truyền key qua tham số. Cần Nansen → ghi "CẦN OPERATOR" vào agent\_log.md.
\- Lệnh bash phải TRẦN, một lệnh một call: không chain ;/&&, không pipe Out-String, không cd đầu lệnh (đứng sẵn repo root). Python luôn chạy từ file \_probe\_\*.py / \_task\_\*.py, cấm python -c. Output lớn ghi file.
\- Tầng HUMAN không đổi: không ghi thresholds.yaml (đề xuất → proposals/), không điền verdict CASE sheet.
\- **PROBE STORE TRƯỚC** khi fetch external API: ssh VPS → kiểm tra partition tồn tại + log collector → chỉ fetch ngoài khi (b) cần lịch sử trước ngày store bắt đầu (one-off backfill, có nhãn) hoặc (c) data type không có trong store (ghi DEV task). KHÔNG lập đường collect song song ad-hoc.
\- **tape one-shot vào cron → cùng luật fail-behavior**: missing-dependency → ERROR + exit≠0 + alert (cấm no-op êm). (L-44)

## PHASE-TAG CASE_INDEX → case_state_map workflow (ký 18/08, án PHASE-TAG-v0.3.3)

Sau MỖI edit `CASE_INDEX.xlsx` sheet INDEX (đổi state token, thêm/xóa case, đổi ngày ký):

1. **local Windows:** `python _task_gen_case_state_map_20260818.py`
   → regen `docs/case_files/case_state_map.md` (VIEW SINH từ CASE_INDEX).
2. **SCP lên VPS:** `scp docs/case_files/case_state_map.md root@5.223.67.21:/root/Data_back_test/whale_data/docs/case_files/`
3. **Verify md5:** `md5sum` local vs VPS phải KHỚP.

**Quên bước 1-3:** cron phase_tag đọc map cũ → khối ⚠/🔻 route theo state CŨ (verdict ký mới không phản ánh trong Telegram scan). Ví dụ: operator downgrade BTW từ DISTRIBUTION-WATCH → CLOSED nhưng quên regen+SCP → BTW vẫn xuất hiện ⚠ STATE-CONFLICT trong report.

**Staleness guard:** `scripts/run_phase_tag.py` check mtime — sau **3 ngày** cũ → HÉT WARNING + Telegram alert (khi wire). KHÔNG block scan (chạy state cũ vẫn có giá trị, chỉ nhắc operator). Guard KHÔNG auto-regen vì CASE_INDEX.xlsx sống local Windows, VPS không có quyền đọc/pull.

**Lý do không auto-cron regen VPS:** CASE_INDEX.xlsx canonical ở local — VPS chỉ nhận `.md` qua SCP. Auto-cron trên VPS = đọc CASE_INDEX stale (nếu SCP xlsx theo cách khác, sync 2 chiều rắc rối). Guard-3d + operator workflow SCP tay = giải pháp tối giản hiện tại.

## FACTS ĐÃ CHỐT — ALPHA COLLECTOR V2 (04/08/2026)

\- **Alpha daily store:** `data/raw/spot_klines_1d` venue=`binance_alpha`, collector `scripts/collect_alpha_daily.py`, cron 02:00 UTC. **Price/vol only, taker=ABSTAIN** (klines[9]==klines[5] trên bapi/alpha). Forward-only từ 04/08.
\- **Backfill 04/08:** 126/137 symbols OK, 27,055 candles, 481 date partitions. Lịch sử từ 2025-06-11 (IDOL), 2025-10-21 (BLUAI), 2025-06-18 (TAG). 11 symbols fail = no klines data. Không dedup issue.
\- **collect_alpha_spot.py RETIRED 04/08:** archived → `scripts/archive/collect_alpha_spot_RETIRED_20260804.py`. Cron 01:10 UTC phải xóa trên VPS. venue=binance_spot_bsc = 0 rows toàn bộ store (no data to migrate).
\- **Alpha endpoint:** `https://www.binance.com/bapi/defi/v1/public/alpha-trade/klines` (public, no auth). Token-list: `/bapi/defi/v1/public/wallet-direct/buw/wallet/cex/alpha/all/token/list` (659 tokens, 485 BSC indexed). Source code khai quật: `D:\Check onchain fresh wallets\_s3_v2.py`.
\- **Alpha ID resolver:** `data/config/alpha_id_map.json` — 137/137 u50 resolved (FAIL=0). Regenerate: `python scripts/archive/_task_write_alpha_config_20260804.py`. CALIB_ALPHA dict 12 entries đã RETIRE (verify 12/12 khớp).
\- **IDOL (ALPHA_223):** có trong resolver map. Alpha klines từ 2025-06-11 (420 nến). Alpha vol IDOL trong CASE_IDOL DAILY = one-off (c42) — store pipeline forward-fill từ 04/08.
\- **spot_klines_1d local store:** không liên quan VPS — local machine chạy backfill + daily. Nếu VPS cần: SCP parquet sang hoặc chạy backfill script lại.
\- **freshwatch_symbols.txt MISSING trên VPS** — data/config/ chưa tồn tại. Probe alpha_taker dùng fallback 10 symbols (không ảnh hưởng collector mới).

