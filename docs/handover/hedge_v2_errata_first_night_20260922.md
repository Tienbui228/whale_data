# ERRATA đêm đầu HEDGE v2 (draft · β5 · chưa gửi · sẽ gửi cùng γ)

**data-source:** VPS canonical · hedge_v2 first live night
**machine:** VPS canonical
**target-date:** đêm đầu chạy live (TBD)
**code-commit:** git sha khi γ apply

## Nội dung ERRATA (Vietnamese · sẽ dán vào bản tin đêm đầu)

```
⚠ ERRATA HEDGE v2 · đêm đầu · thay WATCHLIST v1.4:
· 🎓 TỐT-NGHIỆP COVER: BỎ (định nghĩa cover cũ bắn trên POWER 02/09 · replaced by U0-CLASS L1)
· 🅱1/🅱2: đổi nghĩa · Δpos THẬT ≥+10% (pos_r(T)/pos_r(T-1)-1) · KHÔNG bằng Δdiv
· LIST A: registry hợp Bảng A ∪ List A (145 tokens) · cột `dải` + `nguồn` khai loại
· NEW: cột kr chưa wire · in `kr=?` cho tới khi có data
· MASTER events: SỰ KIỆN đọc events_<T>.jsonl (01:35 cron) · KHÔNG tính lại
· L2/L3: KHÔNG giấu · dán nhãn cạnh token (§KỶ-LUẬT #14)
```

## Rationale (chi tiết cho ANALYSIS)

1. **🎓 TỐT-NGHIỆP COVER BỎ** — spec §2: "Thay bằng U0-CLASS L1 (định nghĩa cover cũ bắn trên thứ không phải cover — POWER 02/09)."
2. **🅱 đổi nghĩa** — spec §2: "điều kiện 'pos bật' đo bằng **Δpos thật** (pos_r(T)/pos_r(T−1) − 1 ≥ +[10%]), KHÔNG bằng Δdiv."
3. **Registry hợp** — spec §2: "LIST A: registry hedge (div_avg3 ≤0.5 run ≥3d)". Nhưng AW6 mở thành hợp Bảng A ∪ List A (Q1 ANALYSIS 22/09).
4. **kr chưa wire** — spec §2: "thêm 4 cột acc_r · pos_r · funding state · kr_share". kr_share nguồn chưa được ký. AW-α' đánh dấu `kr=?` tạm.
5. **Master events read** — spec §1: "Nguồn sự kiện DUY NHẤT = bảng events của master (U0-BELL/U0-CLASS/U1, spec fb30dd88 + A1/A2/A3/A3.1'); HEDGE không tính lại — cite `[master-events]`."
6. **§14 doctrine** (22/09): "Nhãn thesis là NHÃN, không phải điều kiện hiển thị." → L2/L3 vẫn hiện trong SỰ KIỆN kèm `(không mở U1)`.

## Cấu hình ERRATA in body

- Header tăng 1 dòng (~180 chars) khi errata=True
- Chỉ in ĐÊM ĐẦU (γ set flag một lần, sau clear)
- Không lặp lại các đêm sau

## Trigger

Cron 01:40 UTC γ đầu tiên · file marker `data/state/hedge_v2_first_night.marker` control:
- Nếu file KHÔNG có → this is first night → in ERRATA + tạo marker
- Nếu file có → skip ERRATA

Marker chỉ ghi lần đầu · không xóa · nếu cần re-run: xóa marker để ERRATA in lại.
