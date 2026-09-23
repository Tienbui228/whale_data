# V8 · hedge_v2_first_night.marker · IN SỐ đo · KHÔNG SỬA

Doctrine áp: #16 mọi bảng NGUỒN. Agent CHỈ đọc code · KHÔNG sửa.

## 1 · Đường dẫn marker file

| item | value | NGUỒN |
|------|-------|-------|
| path constant | `REPO_ROOT / "data" / "state" / "hedge_v2_first_night.marker"` | `scripts/watchlist_daily.py:671` |
| tuyệt đối trên VPS | `/root/Data_back_test/whale_data/data/state/hedge_v2_first_night.marker` | REPO_ROOT resolved |
| trạng thái hiện tại | **absent** (HEDGE_V2=0 hiện tại · chưa bao giờ bật thành công) | ls check |

## 2 · Code path đọc marker

| file:line | code | mục đích |
|-----------|------|----------|
| `watchlist_daily.py:666` | `_hedge_v2 = os.environ.get("HEDGE_V2", "0") == "1"` | gate cờ · nếu False, cả block dưới KHÔNG chạy |
| `watchlist_daily.py:667` | `if _hedge_v2:` | block gate |
| `watchlist_daily.py:671` | `_marker_p = REPO_ROOT / "data" / "state" / "hedge_v2_first_night.marker"` | định path |
| `watchlist_daily.py:672` | `_errata = not _marker_p.exists()` | **quyết định có in ERRATA hay không** |
| `watchlist_daily.py:674-675` | `tg_out, _hv2_meta = _hv2.compose_body(target, report_only=True, errata=_errata, write_audit=True)` | pass errata vào body composer |
| `watchlist_daily.py:701-705` | `if ok_tg and _errata: _marker_p.write_text(f"{target}\n")` | **ghi marker SAU khi send OK** (đêm đầu thành công) |

## 3 · Marker điều khiển gì

**Marker vắng mặt (`not _marker_p.exists()` = True):**
- `_errata=True` → `hedge_v2.compose_body(..., errata=True)` → header body thêm 1 dòng ERRATA (~180 chars):
  ```
  ⚠ ERRATA đêm đầu: 🎓 TỐT-NGHIỆP BỎ · 🅱 nghĩa mới (Δpos thật ≥+10%) · registry = hợp Bảng A ∪ List A (không phải List A cũ)
  ```
- Sau khi send OK → marker được ghi (target date trong nội dung file)

**Marker tồn tại (`_marker_p.exists()` = True):**
- `_errata=False` → `compose_body(..., errata=False)` → header body KHÔNG có ERRATA line
- Block `if ok_tg and _errata:` không chạy → marker giữ nguyên (không rewrite)

## 4 · Toggle behavior (tắt cờ → bật lại · marker còn nằm đó)

| scenario | HEDGE_V2 env | marker | _errata | body ERRATA line | marker ghi mới? |
|----------|:---:|:---:|:---:|:---:|:---:|
| Đêm đầu bật cờ · marker absent | 1 | absent | **True** | **YES** (in ERRATA) | **YES** (ghi target đêm đầu) |
| Đêm sau vẫn bật cờ · marker present | 1 | present | False | no | no |
| Tắt cờ · rollback | 0 | present | (block gate off · không check) | (path cũ · WATCHLIST v1.4) | no |
| **Bật lại cờ · marker VẪN present** | 1 | **present** | **False** | **no** (KHÔNG in ERRATA lần nữa) | no |

**⚠ GOTCHA:** nếu:
1. Bật cờ đêm N (send OK · marker ghi)
2. Postcheck FAIL sáng N+1 → tắt cờ (revert)
3. Fix bugs
4. Bật lại cờ đêm N+K
→ Đêm N+K sẽ **KHÔNG in ERRATA** (marker vẫn còn từ đêm N) · Tiên nhận HEDGE v2 body **không có ERRATA line** · có thể nhầm là đã ổn từ trước.

**Muốn ERRATA in lại khi re-launch:** phải **xóa marker thủ công** trước khi bật cờ lại:
```bash
ssh root@5.223.67.21 "rm /root/Data_back_test/whale_data/data/state/hedge_v2_first_night.marker"
```

## 5 · Không sửa (chỉ báo)

Nợ ghi sổ · fix ở lịch sau khi ANALYSIS quyết cách handle re-launch:
- Option A: mỗi lần bật cờ mới xóa marker tự động (thay đổi ngữ nghĩa "đêm đầu" = "đêm đầu của lần bật")
- Option B: giữ như cũ (marker = one-shot lifetime · chỉ 1 ERRATA per repo lifetime)
- Option C: marker chứa `commit_sha` · nếu commit thay đổi → ERRATA in lại

Agent KHÔNG chọn · KHÔNG sửa · chỉ báo cho DEV rollback 24/09.

## 6 · Ranh giới V8

- Đọc code · KHÔNG sửa (§KỶ-LUẬT hold-out)
- KHÔNG chạy watchlist_daily · KHÔNG tạo/xóa marker file
- Chỉ báo file:line · behavior · gotcha
