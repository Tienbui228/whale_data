# ANALYSIS rulings · HOLD-OUT U0-BELL · 23/09/2026 · NGUYÊN VĂN

Nguồn: tin ANALYSIS → DEV trong chat DEV 23/09, chép nguyên văn theo thứ tự thời gian.
Gom bởi DEV. Không sửa chữ. Agent: grep ký tự `\` lạ trước khi dùng, in md5 file này.

---

## 1 · Q1-Q6 + P1-P4

ANALYSIS → DEV · HOLD-OUT U0-BELL · phán Q1-Q6 + ký P1-P4 · 23/09/2026

Q1 · Kết cục = div_avg3 vượt 0.5 trong [10] ngày sau chuông — đúng thứ lưới 90 ngày đã đo (nền cross-10d 33.4%). KHÔNG phải ×2/60d. Precision ≥55% và lift ≥1.5× nhất quán trên nền đó (55/33 = 1.65). ×2/60d, U0-CLASS L1 trong 10d, U1 CONFIRMED trong 15d = ba cột MÔ TẢ, không phải pass. Tôi ghi thiếu ở A3.2; sửa vào registration.
Q2 · "lead ≥2d" = trung vị (D_cross − D_bell) trên các hit — đặt tên `lead_to_cross`. lead_known ≡ 0 là tính biết-được của chuông tại D, khác vật. Không đo tới D0.
Q3 · (ii) roster theo ngày, roster_<date>.txt + md5 (như E2). Token vào sau 20/09 được chấm từ ngày vào, cùng nền của ngày đó. Roster đóng băng 20/09 chạy song song làm dòng mô tả.
Q4 · MỘT ô chính: w=3, T=−20% (số đã đăng ký CAL-ONLY). 7 ô còn lại mô tả. Ổn định đa chiều A1.2 in ra, không là điều kiện pass. Đếm theo token-episode (gộp 14d), không theo sự kiện.
Q5 · Đóng băng bằng md5: code tính U0-BELL + events_build + roster + events_2026-09-20. Mọi thay đổi trong cửa sổ (HEDGE v2, A1, STALE, D2, BC1, U1-transition, N5) chỉ được SCP khi agent chứng minh dòng U0-BELL trong events_<date>.jsonl byte-identical so với snapshot đóng băng (không phải "cùng hàm"). Thay đổi nào chạm acc/pos/div đầu vào → CẤM trong cửa sổ. A1 chỉ lọc thân; audit phải ghi đủ mọi chuông (bell_near/blind kèm).
Q6 · AA1 27/09 = "ghi nhận lưới, không ký số" — không đổi định nghĩa, không đổi ngưỡng. Bất kỳ ngưỡng nào ký ở 27/09 KHÔNG áp vào cửa sổ đang mở; nếu có, đó là hold-out mới từ ngày ký. HEDGE spec §0 đọc theo nghĩa đó.
P1-P4 · KÝ. Ngày registration thật = ngày ghi file (23/09), ghi đúng vậy. 21/10 chấm chuông ≤11/10 (đủ 10 ngày); chuông 12-20/10 chấm 30/10; không rút horizon. Sổ "đã nhìn" ghi quyết định chạm U0, không ghi việc đọc báo.

---

## 2 · C5 + C6

`C5: (a), có điều kiện R3.` Mốc đóng băng thật = R0 23/09 00:57. Chuông 20-22/09 chấm lại bằng code R0 (shadow) — nếu R3 chứng minh AO1/AH5/AW-α' không đổi dòng U0-BELL (byte-identical trên 3 đêm) thì 20-22/09 vào cửa sổ chính thức với chú thích `[R0-shadow ≡ prod]`; nếu có sai khác dù một dòng → về (b), cửa sổ chính thức từ 23/09, 20-22/09 chỉ mô tả. Bằng chứng phải là diff thật, không suy luận từ commit.
`C6: data/artifacts/ (regen 22/09) là chuẩn cho Q5` — vì schema L2/L3 đã tách và events_md5 đã cite ở footer HEDGE/master; `event_ledger/` legacy giữ nguyên làm đối chứng, không chạm, không dùng để chấm. Ghi md5 hai bên vào registration để mai sau ai muốn đối chiếu thì có.

---

## 3 · C7

`C7: đồng ý tách từng đêm` — 09-20 mô tả (không có as-ran để so, không được khẳng định) · 09-21 theo diff thật (byte-identical → vào; khác một dòng → mô tả) · 09-22 vào (code R0 chạy thật). Ghi vào registration đúng từng đêm với lý do và md5; ngày bắt đầu cửa sổ chính thức = 21/09 hoặc 22/09 tùy kết quả 09-21, không phải 20/09 — mọi số "n đêm" sau này đếm từ đó. Luật "cả 3 hoặc không" bỏ: nó là luật tôi đặt khi tưởng ba đêm cùng bản chất; bằng chứng từng đêm khác nhau thì phán từng đêm.

---

## 4 · C8

ANALYSIS → DEV · C8 · phán TRƯỚC khi xem bảng in-sample theo dải (để không chọn nền sau khi thấy nền nào có lợi) · 23/09/2026

(a) Lift dùng cho PASS = lift PHÂN TẦNG: precision của chuông so với nền CÙNG DẢI, gộp có trọng số theo phân bố chuông trong 3 dải cố định {<0.3 · 0.3–0.4 · 0.4–0.5}. Nền gộp (33.45/36.72) chỉ in làm mô tả. Không đòi "cả hai" — cả hai chỉ làm pass dễ hơn khi chuông dồn về 0.4–0.5. Đây là phát hiện đúng của DEV: chuông không được là cách phát biểu lại "div đang gần 0.5". In thêm cột precision theo dải để 21/10 thấy chuông sống ở dải nào.
(b) Nền loại outage (36.72% / theo dải cũng loại) — [GAP-0724] bỏ khỏi cả tử lẫn mẫu, đúng luật đã có. Bản gốc in mô tả.
(c) Đơn vị phải khớp: precision đếm token-episode (gộp 14d) thì nền cũng token-episode. DEV đo xong nền episode theo dải → đó là nền chính; token-night giữ làm mô tả. Nếu 23/09 chưa có nền episode, registration ghi "nền chính = episode, sẽ điền trước 21/10", không đổi sau.
Ghi vào registration R1 cả ba điều trên trước khi mở bảng in-sample; bảng in-sample là calibration, xem sau khi ký.

---

## 5 · C9 + C10 + C11

`C9: (i)` — lift = P_obs / Σ w_b·base_b (chuẩn hoá gián tiếp), in P_b và lift_b từng dải làm mô tả. Ba quy tắc biên ký như DEV viết: dải [0, 0.3) · [0.3, 0.4) · [0.4, 0.5]; div đo tại D của chuông ĐẦU episode; dải 0 episode → w=0, in "∅".
`C10: (b)` — giữ 21/10 và 30/10, mốc chuông ≤10/10 và 11–20/10; R1 in cả `graded_at` và `data_through` để không ai đọc nhầm off-by-one lần nữa.
`C11: code đúng (3.600), đơn vị ký tự Telegram` — spec §1 "≤3.200 byte" lỗi thời sau khi tôi chấp nhận nâng ở α'; sửa spec một dòng: "thân ≤3.600 ký tự Telegram (UTF-16 sau markup), trần cứng 4.096"; pin p100 đổi theo. Không chặn 24/09.

---

## 6 · C12 + ok R1 pin trước V6

`C12: (a)` — đợt 2 chấm 31/10 cho chuông 11–20/10 (data_through 30/10). Đợt 1 giữ 21/10 / chuông ≤10/10. R1 in `graded_at · data_through · bell_range` cho từng đợt.
`ok R1 pin trước V6` — luật đủ thì pin ngay; số nền episode để trống, vào addendum R1a với md5 riêng, không đổi luật. R1 ghi rõ "nền chính = episode (R1a), token-night mô tả".

---

## Ghi chú đọc (DEV, không phải phán)

- Ngày chấm trong P1-P4 (21/10 ≤11/10 · 30/10 12-20/10) đã bị thay bởi C10 rồi C12: đợt 1 = 21/10 (data_through 20/10) chuông ≤10/10 · đợt 2 = 31/10 (data_through 30/10) chuông 11–20/10.
- Cửa sổ chính thức theo C7 + V5a (09-21 byte-identical, md5 canonical 2f41f23f): 21/09 → 20/10.
