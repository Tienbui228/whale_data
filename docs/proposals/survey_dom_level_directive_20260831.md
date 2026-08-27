# SURVEY DOM-LEVEL directive — 2026-08-31 (operator khối)

**Nguồn:** operator chat turn 27/08 tham chiếu "khối operator 31/08" — save VERBATIM per operator directive KÝ 27/08 SAVE input-#1 unblock.

**Note L-59:** Chép chính xác từ operator paste; nếu operator drop khối 31/08 FULLER text riêng, append thay cho re-write.

---

## Nguyên văn (operator ky 27/08):

> **(3) SURVEY DOM-LEVEL** thi hành NGUYÊN VĂN khối operator 31/08 (4 nhóm ~45 token · 3 thước · BscScan-free 0-Nansen · luật đọc (i)-(iv) đăng ký — DEV/agent không kết luận). Ba ghi chú kỹ thuật:
>
> - (a) nhóm C cần SEED từ operator — chờ một số, không tự chọn;
> - (b) BscScan chỉ phủ BSC — token chain khác in N/A-SOURCE + cột chain, đếm coverage per-chain trong bảng tóm;
> - (c) nhóm A chép tracker §10, cấm fetch lại.
>
> Xuất CSV + md5 + wc + bảng tóm median/p25-p75 × nhóm × thước + đếm ≥0.80.

---

## Input dependencies status

| Input | Source | Status |
|-------|--------|--------|
| **#1** khối directive text | Operator chat 27/08 (this doc) | ✅ SAVED |
| **#2** §10 tracker findings | findings rev9 (7019a5d3) | 🛑 PENDING drop (không chép số từ trí nhớ) |
| **#3** nhóm C seeds | Operator ky riêng | 🛑 PENDING số |

## Scope tổng

- **4 nhóm** × ~45 token = ~180 tokens (est.) — universe cụ thể chờ operator paste khối FULLER hoặc mapping (A/B/C/D).
- **3 thước:** raw / ex-exchange / ex-structural (đề xuất từ WALLETSET §3 draft) — hoặc thước operator ky riêng.
- **BscScan-free 0-Nansen:** dùng BscScan API free tier, KHÔNG dùng Nansen credit.
- **Luật đọc (i)-(iv):** operator đăng ký · DEV/agent chỉ báo cáo, KHÔNG kết luận.

## Kỹ thuật (a)-(c) — memo cho execute (khi có input #2 + #3)

**(a) nhóm C SEED:** placeholder cấm tự chọn · CSV cột nhóm sẽ trống cho C until seed drops.

**(b) BscScan coverage:**
- Endpoint: `https://api.bscscan.com/api?module=token&action=tokenholderlist&contractaddress=<addr>`
- Chain filter: BSC only (chain_id=56)
- Token khác chain (ETH · SOL · Alpha-BSC · etc.) → CSV cột `chain` in giá trị + cột `dom_bscscan` in `N/A-SOURCE`
- Bảng tóm bổ sung cột `coverage_per_chain` = n_success / n_total mỗi chain

**(c) nhóm A tracker §10:** chờ file rev9 findings drop · KHÔNG re-fetch Nansen (tôn trọng cap 2/day + LUẬT MỚI raw-save).

## Output khi execute:

- **CSV:** `docs/reports/survey_dom_level_20260831.csv`
- **Md5 + wc trong commit + CSV header**
- **Bảng tóm:** median · p25 · p75 × nhóm × thước · đếm tokens ≥ 0.80
- **Rendered per-chain coverage** cho báo cáo ANALYSIS 27/09.

## Note KHÔNG kết luận

Per operator ky: DEV/agent xuất bảng NGUYÊN VĂN số, KHÔNG interpret · KHÔNG đề xuất thước operative · KHÔNG grade tokens. Đó là quyền ANALYSIS chốt 27/09 review-bundle.
