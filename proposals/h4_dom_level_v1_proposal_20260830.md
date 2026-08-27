# H4 v1 — DOM-LEVEL: THESIS + SPEC + KẾ HOẠCH THI HÀNH (ký operator 30/08/2026)

**Trạng thái:** ĐÃ KÝ (operator chat 30/08 "ok tôi ký"); ngưỡng `[ ]` = PROVISIONAL chờ control-gate; REPORT-ONLY cho đến khi qua gate §4. Thay thế H4.1-v0 holders-trend (GATE-FAILED 30/08).

---

## §1. THESIS — vì sao mắt đúng cho loài captive là MỨC-SỞ-HỮU, không phải trend nào khác

**Bài toán:** loài captive (TUT, BTW-07, +7 captive-thật trong 18 SÓT U-v3) chạy campaign mà không để dấu trên bất kỳ trục nào máy đang nhìn. Ba tầng loại trừ đã chứng bằng số:

1. **Tape mù (findings §9.6):** TUT trên Binance spot — sàn thật, 43× Gate — cho CVD **âm gần như 15 tháng liên tục** kể cả kỳ gom; cơ chế: MM gom phía **maker** (ngồi bid) → tape in taker-SELL trong khi họ nhận hàng. Taker-CVD mù cấu trúc với gom-passive.
2. **Balance mù:** gom bằng cách MUA TRÊN SÀN → token đổi chủ **bên trong ví sàn** → `exch_balance` không động (TUT nền: 693.1→693.2M, phẳng tuyệt đối). H1 kho-step chỉ thấy hàng RA/VÀO sàn, không thấy hàng đổi chủ trong sàn.
3. **Holders-count mù (A3 gate-fail 30/08):** `exchange_holders` từ `/tgm/flows label=exchange` = **số địa chỉ CEX đang giữ token** — metric hạ tầng (sàn thêm ví, rotation), không phải sở hữu. Hai falsifier TUT/BTW đều phẳng (390-405 · 211-218). H4.1-v0 chết tại gate đúng luật, 0 credit.

**Cái còn lại — và là cái tracker operator vẫn nhìn mỗi ngày:** **top-100 dominance (MỨC)**. Bằng chứng mức tại nền của các captive đã niêm: **TUT 83% · BTW 96% · AKE 86%** (tracker, §10 findings) — vượt xa mọi token thường. Gom-đã-hoàn-tất không có trend để bắt (TUT gom từ 2025), nhưng nó **để lại MỨC**: hàng nằm ở ít tay. Câu machine đúng không phải "ai đang gom" mà **"hàng ĐÃ nằm trong tay ai"** — level, đọc một lần khi token vào vùng nghi (nén), không cần chuỗi.

**Một câu:** claim operator "TUT chỉ phát hiện được bằng spot được gom" đúng qua ba tầng loại trừ — dấu vết cuối cùng của gom-trên-sàn là **cấu-trúc-sở-hữu**, và nó đo được bằng một call có ngân sách.

## §2. SPEC TEXT — agent merge VERBATIM vào gom_detect_spec §1-H (thay block H4 cũ, giữ banner ARCHIVED của v0)

> **§1-H4 v1 — DOM-LEVEL (ký 30/08/2026, operator; thay H4.1-v0 GATE-FAILED):** mắt on-chain thứ hai cho loài captive — đo MỨC sở hữu, không đo trend.
> - **Trigger (compression-gated, tiết kiệm credit):** token đạt ≥[2] vế T0.1 ∧ chưa có dominance-snapshot trong [14] ngày → gọi `/tgm/holders` MỘT lần, ghi `top100_dom` + `snapshot_at`.
> - **H4.1 DOM-HIGH (mức):** `top100_dom ≥ [0.80]` → flag lane H4, dòng riêng CAMPAIGN-PRE: `H4 DOM-HIGH 83% (snap 30/08)`. REPORT-ONLY.
> - **H4.2 DOM-RISE (trend chậm, phụ):** dominance tăng ≥[+3pp] giữa hai snapshot liên tiếp của cùng token → nâng nhãn `DOM-RISING`.
> - **Credit (đã ký 30/08):** cap 2 call/ngày · vượt trigger → `[CREDIT-QUEUE]` sang hôm sau, không gọi lố · replay budget one-shot 10 call.
> - **Sentinel:** không snapshot → `N/A-NO-SNAPSHOT` (≠ False, in được); token ngoài coverage Nansen → `N/A-COVERAGE`.
> - **Cooldown:** lane {H4} theo §8.4(i) (14d ∧ 3d-sạch trên raw; raw của H4 = điều kiện DOM-HIGH tại snapshot mới).
> - **Conf:** dominance KHÔNG đếm vào conf 4-vế (mapping đã ký); in làm ngữ cảnh cạnh alert.
> - **GATE trước compose (§4 file proposal):** falsifier retro TUT/BTW + phân bố control — chưa qua = vĩnh viễn REPORT-ONLY.

## §3. OPERATIONALIZATION (DEV đọc từ đây, không tự suy)

- Nguồn: `/tgm/holders` (Nansen), field top-100 share; nếu response trả cấu trúc khác → DỪNG, paste schema, không map mò (L-51).
- `top100_dom` = Σ balance top-100 / total supply (hoặc field tương đương Nansen trả sẵn — paste field name khi build).
- Trigger đọc T0.1-count từ conf-labeler hiện có (cùng code path, không tính lại).
- Lưu: bảng `h4_dom_snapshots` (token · snapshot_at · top100_dom · nguồn call) — append-only, chính nó là dữ liệu cho H4.2 DOM-RISE và cho review 27/09.
- screen_thresholds khối `h4` GHI ĐÈ theo v1: `{dom: 0.80, dom_rise_pp: 3, t01_min: 2, resnap_days: 14, credit_cap_daily: 2, replay_budget_once: 10, provisional_unsigned: true (trừ credit đã ký), source: "operator ký 30/08 — H4 v1 DOM-LEVEL"}`. Các key v0 (conc_drop, bal_flat, window_days) xóa.

## §4. GATE TRƯỚC COMPOSE (đăng ký trước, không nới)

1. **Câu kỹ thuật quyết đường replay:** `/tgm/holders` có nhận **date param lịch sử** không? — agent trả lời trước.
   - CÓ → replay TUT (nền 06/2026) + BTW (07/2026) bằng budget 10-call: cả hai phải ≥[0.80] tại nền. Không đạt cả hai = v1 chết tại gate như v0, không nới.
   - KHÔNG → falsifier đứng trên số tracker đã niêm (TUT 83% · BTW 96% — §10 findings) + forward-verify khi hai con vào trigger.
2. **Phân bố control (bắt buộc trước khi [0.80] thành số ký):** chạy trigger-flow trên control-52 trong 30d report-only → phân bố `top100_dom` của token nén-mà-không-chạy. Nếu ≥[50%] control cũng ≥0.80 → mức đơn độc yếu → điều kiện thành cặp (nén ≥[3] vế ∧ mức) hoặc ngưỡng nâng — **số đặt từ phân bố, operator ký, không ai đề trước**.
3. **FP-tripwire:** fires H4 tính vào trần 0.4 alert/token/30d chung (lane riêng nhưng cùng ngân sách chú ý của operator).
4. Review 27/09 bundle += H4-v1 `[ ]` (giờ 7 món: ramp · [50%]-walletset · 2×2 · AKE-row2 · MA-shadow · V③-cutpoint · H4-v1).

## §5. VIỆC — thứ tự

| # | Việc | Ai |
|---|---|---|
| 1 | Merge §2 verbatim + banner ARCHIVED trên H4-v0 + yaml §3 | agent (diff + sha TRƯỚC code) |
| 2 | Trả lời date-param `/tgm/holders` + paste schema response 1 call mẫu (token bất kỳ, tính vào cap ngày) | agent |
| 3 | Code theo §3 (sau diff #1): trigger-flow · snapshots table · lane H4 render · sentinel · queue | DEV |
| 4 | Replay gate theo nhánh #2 → bảng cho ANALYSIS chấm falsifier | DEV |
| 5 | 30d control-distribution → ANALYSIS trình → operator điền [0.80]/[+3pp]/[2 vế] | DEV → ANALYSIS → operator |

*Hết. Mắt này sinh ra từ ba lần loại trừ có số — nếu gate §4 giết nó lần nữa, cái chết đó cũng sẽ sạch như v0: bằng bảng, không bằng cãi.*
