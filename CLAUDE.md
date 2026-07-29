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

\- Snapshot phủ TOÀN universe 525 by design; filter 137 chỉ ở SCREEN.

\- Án R1: export lành, bug ở join ledger (nghi symbol format

&#x20; TAG vs TAGUSDT hoặc date-join). Fix join, KHÔNG đụng export.

\- Excel oi\_vs\_med14 ≠ định nghĩa fire (window khác).



\## KỶ LUẬT

\- Mỗi session ghi agent\_log.md: việc + lệnh + kết quả số.

\- Commit message tiếng Việt ngắn, một change-set một chủ đề.

\- Output lớn ghi file, không đổ chat.

\- Số lệch giữa hai nguồn → ghi án vào agent\_log.md, không tự chọn.

\- DAILY data chỉ sống trong CASE\_<TOKEN>.xlsx sheet DAILY — cấm sinh CSV song song trong docs/case\_files/ (án 30/07, tái phạm 1 lần).

\- Ratio fn=1 (native\_1d low\_conf) → không dùng làm số chốt. Fallback: Zone A aggregate từ ledger\_v2.xlsx CAMPAIGNS, ghi rõ nguồn "Zone-A-agg". Quy ước tạm cho đến khi P1 screener snapshot 5-phút chạy ổn định.

