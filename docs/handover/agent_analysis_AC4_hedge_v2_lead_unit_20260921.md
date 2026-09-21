# AGENT → ANALYSIS · HEDGE v2 · AC4 · HAI CÂU · MỘT DÒNG MỖI CÂU

**Bối cảnh (30s)**: chuẩn bị wire HEDGE v2 (thay WATCHLIST) per spec
`docs/HEDGE_report_v2_spec_20260921.md` (md5 `e2bab119dd789f2ec32a6a88dd3fc18d`).
Hai chỗ mập mờ cần chốt trước khi động code.

---

## Câu (lead) · Dòng chuông trong khối SỰ KIỆN

**Hiện tại (X1 sau N2)**: master body render `lead=?` cho chuông tại D (đã sửa từ
`lead=known` sai nghĩa).

Spec HEDGE v2 §1 dòng ví dụ:
```
[U0-BELL D=20/09 · Δacc_bwd=−23% · pos_bwd=+2% · lead_known=0] MYX
```

**Vấn đề**: chuông tại D chưa có cross → chưa có lead. `lead_known=0` sẽ là số SAI
nếu ai đó thay `?` bằng số.

**Xin chốt một dòng**:
1. **Bỏ trường `lead` khỏi dòng chuông** — chỉ in `[U0-BELL D · Δacc · pos_bwd]`.
   Trường `lead_known=k` chỉ xuất hiện trong dòng U0-CLASS/U1 khi biết k thật.
2. **Giữ `lead_known=0` (như spec ghi)** — chấp nhận số 0 là "chưa biết", quy ước chung.
3. **In `lead=?`** — hiển thị dấu hỏi, không chèn số 0 sai nghĩa.

DEV đề nghị (1). Phản đối (2) vì `0` là số sai (không có lead ≠ lead=0 ngày).

---

## Câu (unit) · Ngân sách thân HEDGE

**Spec §1 khuôn thân**: `≤ [3.200] byte` · dấu ngoặc vuông = số CHỜ chốt.

**Vấn đề**: Telegram API tính len bằng KÝ TỰ (Python `len(str)`), không phải byte.
1 ký tự tiếng Việt Unicode = 3 bytes UTF-8 · header như `Δacc_bwd`, `📥`, `🎯` — đủ để 3.200 byte có thể chỉ ~1.500 ký tự.

**Xin chốt một dòng**:
1. **KÝ TỰ · 3.200 chars** (như Telegram len, khớp master preview 4.096).
2. **BYTE · 3.200 bytes** (như spec ghi hiện tại).
3. **KÝ TỰ · số khác** (ghi số).

DEV đề nghị (1) · nhất quán master preview + U7 gate len.

---

## Ba đường trả lời

`AC4: lead=1|2|3 · unit=1|2|3(số=<x>)`

---

## Phụ · Sau chốt

Sau khi có chữ → DEV wire HEDGE v2 theo §7 spec:
1. `dryrun_hedge_v2_pipeline.py` ≥5 đêm (§KỶ-LUẬT #12)
2. Wire đọc bảng events master + 4 cột LIST A + 🅱 theo Δpos thật + luật nền + audit CSV
3. Pin p100-p106 đen
4. SCP + đêm đầu report-only + ERRATA
5. Báo bản v2 nguyên văn + Δbytes + audit md5 + pin PASS/FAIL + git sha

Agent chờ. KHÔNG code HEDGE v2 khi hai câu này chưa có chữ.
