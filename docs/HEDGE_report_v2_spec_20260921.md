# HEDGE REPORT v2 — SPEC (ANALYSIS · 21/09/2026 · chữ Tiên "đồng ý gộp" 21/09) · DEV build · không tin mới, thay tin WATCHLIST hiện tại

## 0. Nguyên tắc
- Một tin HEDGE mỗi đêm, thay `WATCHLIST` v1.4. Tầng in = SỰ KIỆN + top-N; registry đầy đủ = audit file.
- Nguồn sự kiện DUY NHẤT = bảng events của master (U0-BELL/U0-CLASS/U1, spec fb30dd88 + A1/A2/A3/A3.1'); HEDGE không tính lại — cite `[master-events]`. Tránh hai câu chuyện cho một token (CROSS 20/09: 🅱2 "long mới" vs master "L1").
- Số in as-printed; thiếu → N/A-ERROR; mọi lead = lead_known. Mọi số [·] chờ 27/09 / hold-out 21/10; header một dòng `[CAL-ONLY]`.
- Luật nền V1.4-A áp: token ≥[2]× min_close_60d ∨ direction ∈ {POST, POST-DUMP, XẢ-WATCH} → không vào thân (audit ghi `[hậu-D0 +kd]`); epoch reset → `[đợt 2]` audit-only.
- Sender: qua U7 gate (len ≤4096 trước cap, parse_mode, HTML scan); cấm slice; vượt → không gửi + chân-đỏ + journal.

## 1. Khuôn thân (≤ [3.200] byte)
```
[HEDGE v2] 2026-09-20 · [scanned=k/N · blind=n] · registry=73 · bell=2 · cross=1 · U1-due=1 [CAL-ONLY]
── SỰ KIỆN (phía crowd → xác nhận) ── [master-events]
[U0-BELL D=20/09 · Δacc_bwd=−23% · pos_bwd=+2% · lead_known=0] MYX
[U0-BELL D=20/09 · Δacc_bwd=−32% · pos_bwd=+21% · lead_known=0] DRIFT
[U0-CLASS D_cross=18/09 · L1 · Δacc=−41% · |Δpos|=3%] CROSS → U1 due 23/09
[U1 D+5 · v1=0.52 ✓ v2=1.71 ✓ · pos_r 1.19] BULLA → CONFIRMED (+kd)
[U1 D+5 · v1=0.98 ✗ v2=0.79 ✗] LIGHT → FAILED
(không có → "hôm nay: không event")
── PHÍA WHALE (mô tả, KHÔNG phải chuông) ──
🅱1 short-cover (Δpos ≥+[10%] ∧ ΔOI ≤ −[3%]): ALPINE Δpos +… ΔOI −… · …
🅱2 whale đổi ghế (Δpos ≥+[10%] ∧ ΔOI ≥ +[3%]): DRIFT +21% · JOE +… · … → L2/B2, xem U0-CLASS
── LIST A · B-cand top-[15] (div thấp nhất; đủ 73 ở audit) ──
sym · div · acc_r · pos_r · fund(PIN|SHORT-TRẢ|NONE) · age(sn) · kr% · dist%
1000000BOB 0.176 · 7.8 · 0.9 · PIN · ≥83d[store] · 48 · +14%
…
── FAILED 14d ── m · 3 mới nhất (+n audit)   ── STALE ── (CONFIRMED >30d)
── Nguội (rời List A) ── tên
━━ footer ━━ universe_gen=228 [CHƯA KÝ] · registry_md5 · events_md5 · book=77d86654 · audit=data/artifacts/hedge_registry_<T>.csv
```

## 2. Định nghĩa từng khối
- **SỰ KIỆN**: đọc đúng ba dòng master: U0-BELL (biết tại D; div_avg3 ≤0.5 ∧ Δacc_bwd ≤ −[20%], w=3; pos_bwd mô tả) · U0-CLASS (D_cross+2; L1/L2/L3 theo A2.1; chỉ L1 mở U1) · U1 (D+5; v2 = OI(D+5)/OI(D−1) ≥[1.5] ∧ v1 = acc(D+5)/acc(D−1) ≤[0.6]; pos_r mô tả) → CONFIRMED / FAILED; CONFIRMED >30d → STALE. Tầng −15…−20% → `[U0-NEAR]` audit.
- **🎓 TỐT-NGHIỆP COVER**: BỎ. Thay bằng U0-CLASS L1 (định nghĩa cover cũ bắn trên thứ không phải cover — POWER 02/09).
- **PHÍA WHALE**: 🅱1/🅱2 giữ nhưng (a) tiêu đề mới "mô tả, không phải chuông", (b) điều kiện "pos bật" đo bằng **Δpos thật** (pos_r(T)/pos_r(T−1) − 1 ≥ +[10%]), KHÔNG bằng Δdiv, (c) mỗi dòng in Δpos, ΔOI as-printed, (d) token trong 🅱 đồng thời có U0-CLASS → ghi loại bên cạnh (`→ L2`), (e) sort Δpos DESC, trần [6] dòng mỗi khối.
- **LIST A**: registry hedge (div_avg3 ≤0.5 run ≥3d), thêm 4 cột acc_r · pos_r · funding state · kr_share; `sn` = tuổi episode, nếu bằng tuổi store (27/06) hoặc freshwatch (26/05) → in `≥Nd[store]`; age ≥30 → `30d+`. dist% giữ (tham khảo). Thân top-[15], audit đủ.
- **FAILED / STALE / Nguội**: đếm + tên mới nhất; Nguội = rời registry ≥[3]d.

## 3. Luật nền & epoch (V1.4-A) — áp cho SỰ KIỆN và LIST A thân
Không vào thân nếu ≥[2]× đáy 60d ∨ POST/XẢ; audit ghi `[hậu-D0 +kd]`. Epoch reset (trả ≥[40%] từ đỉnh ∨ hold ≥[14]d không đỉnh mới, rồi nền ≥[7]d ±[15%]) → đồng hồ về 0, `[đợt 2]` audit-only tới khi bảng đợt-2 n≥10.

## 4. Audit file `hedge_registry_<T>.csv`
token · div_avg3 · acc_r · pos_r · gLSR · funding_state · f_avg · sn · ep_len · start · dist% · kr_share · epoch_age · direction · event_today (BELL/CLASS-L?/U1-?) · Δpos · ΔOI. md5 trong footer.

## 5. Ngân sách (đổi chỗ, không cộng)
LIST A 20 dòng → 15 dòng (−5); 🅱 trần 6+6 (thay 4+9); 🎓 bỏ (−2 dòng); Nguội một dòng. Thêm: SỰ KIỆN ≤8 dòng. Ước ≤3.200 byte; pin p100: 6 đêm mẫu ≤4096 trước cap.

## 6. Pin đen-một-lần (registry f539ef0d)
p101 CROSS 20/09: SỰ KIỆN in L1 từ master; 🅱2 KHÔNG được ghi "long mới" nếu Δpos thật <10% → dòng 🅱2 CROSS biến hoặc in Δpos=+3% (đúng số) — hai bản không mâu thuẫn.
p102 DRIFT 20/09: 🅱2 + `→ L2` cùng dòng; SỰ KIỆN bell có pos_bwd +21%.
p103 sn store-start: token start=2026-06-27 in `≥83d[store]`, không in `83`.
p104 luật nền: BTR (POST, +39d) không trong thân; audit `[hậu-D0 +25d]`.
p105 U7: thân > 4096 → không gửi, chân-đỏ, journal FAIL-LEN (không slice).
p106 events_md5 khớp bảng master cùng target (không tính lại).

## 7. Thứ tự làm
1. Dry pipeline HEDGE v2 (render → len fail-closed → HTML scan → format check) ≥[2] đêm.
2. Wire đọc bảng events master + 4 cột LIST A + 🅱 theo Δpos thật + luật nền + audit CSV.
3. Pin p100-p106 đen; SCP; đêm đầu report-only + ERRATA (🎓 bỏ, 🅱 đổi nghĩa).
4. Báo: bản v2 nguyên văn target đầu + Δbytes + audit md5 + pin PASS/FAIL + git sha.
Ranh giới: không chạm động cơ, không seed, không đổi List-A gate sn=5 (registry đọc như cũ), SENT-only + SỔ-ĂN-SỰ-KIỆN bất khả xâm.
