# Proposal: Quy ước ratio-daily canonical
**Ngày soạn:** 2026-07-31  
**Trạng thái:** CHỜ OPERATOR KÝ  
**Tác giả:** Agent (claude-sonnet-4-6)  
**Đối xứng với:** L-21 (OI daily canonical = export 00:00 UTC)

---

## Vấn đề

BULLA 07-20 có **4 con số khác nhau** từ 4 nguồn, cùng trỏ vào 1 ngày:

| Nguồn | Giá trị | Thời điểm snapshot |
|---|---|---|
| native_1d Binance API (original calib repo) | **1.99** | Không rõ — likely daily settlement |
| derived_1h: 00:00 UTC 07-20 (đầu ngày) | **1.981** | top_pos_1h date=2026-07-20 first entry |
| top_pos_1h keep-last 07-20 (cuối ngày) | **1.6811** | 23:00 UTC 07-20 |
| top_pos_1h first entry 07-21 | **1.6755** | 00:00 UTC 07-21 |
| u50_data loose (nguồn không rõ) | **1.75** | RETIRED 31/07 |

Không có quy ước canonical → ai trích dẫn số nào là do nguồn họ đang nhìn.

---

## Định nghĩa hàm derived_1h hiện tại

File: `/root/Data_back_test/whale_data/scripts/export_freshwatch_daily.py`

```python
def _build_derived_1h(date_str: str, symbols: list[str]) -> pd.DataFrame:
    """
    LSR/OI: 00:00 UTC snapshot from 1h stores.
    """
    midnight_ms = _date_midnight_ms(date_str)   # = 00:00 UTC của date_str
    snap = df[df["as_of_ts_ms"] == midnight_ms]  # lấy đúng 1 snapshot = đầu ngày
```

→ **derived_1h = snapshot 00:00 UTC đầu ngày**. Không phải average, không phải max.  
→ Với BULLA 07-20: derived_1h = top_pos_1h tại 00:00 UTC 07-20 = **1.981**.

---

## Đề xuất: Quy ước keep-last canonical (đối xứng L-21)

**Rule được đề xuất:**

> `lsr_pos_r` DAILY canonical = **keep-last snapshot của ngày đó trong top_pos_1h**  
> = row có `as_of_ts_ms` lớn nhất trong partition `date=D` của `top_pos_1h`  
> (thường là 23:00 UTC ngày D).  
>  
> Tương tự L-21: "OI daily canonical = export 00:00 UTC" — nhất quán cho mọi metric DAILY  
> lấy tại một thời điểm cuối ngày UTC cố định.

**Đối với derived_1h (hiện tại):**  
- `_build_derived_1h` đang dùng 00:00 UTC (đầu ngày) — **khác với keep-last**  
- Nếu đề xuất này được duyệt: thay `snap[as_of_ts_ms == midnight_ms]` bằng `sort_values(as_of_ts_ms).tail(1)` trong `_snap()`  
- Chỉ áp dụng cho DAILY vận hành từ nay

---

## Phạm vi áp dụng

| Đối tượng | Áp dụng? |
|---|---|
| freshwatch_daily CSV mới (từ 31/07+) | **CÓ** — nếu operator ký |
| Backfill lịch sử (re-run export cũ) | Operator quyết định |
| 12 calib files trong `docs/case study/` | **KHÔNG** — suite locked, không hồi tố |
| `twelve_cases_reference.md` | **KHÔNG** — chỉ thêm footnote, không đổi số |

---

## Impact: BULLA 07-20 nếu đề xuất được áp

| | Derived_1h (hiện tại = 00:00 UTC đầu ngày) | Proposed keep-last (23:00 UTC cuối ngày) |
|---|---|---|
| BULLA 07-20 lsr_pos_r | 1.981 | **1.6811** |
| Chênh | — | −0.30 (−15%) |

→ Nếu áp quy ước mới và backfill, pos_rerate signal với BULLA 07-20 sẽ có số khác.  
→ Suite 43/43 KHÔNG bị ảnh hưởng (dùng file gốc đã lock).

---

## Rationale

Đối xứng với L-21 ("một cột DAILY một nguồn canonical"):
- OI: export 00:00 UTC ngày hôm sau (= closing của ngày D)  
- lsr_pos_r: keep-last cuối ngày D (= 23:00 UTC) ← **đề xuất này**  
- Cả hai đều biểu diễn "giá trị tại thời điểm đóng ngày UTC"

---

**Để operator ký:** comment vào file này hoặc commit `proposals/ratio_daily_canonical_20260731.md` với message "DUYỆT" / "TỪCHỐI: lý do".
