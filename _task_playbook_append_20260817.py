"""_task_playbook_append_20260817.py
Append §VIII (14 học thuyết) to docs/analysis_playbook.md.
Bump version 0.2 → 0.3. Update cross-ref table.
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from pathlib import Path
import re

ROOT = Path(r"D:\Data back test\whale_data")
pb   = ROOT / "docs" / "analysis_playbook.md"

with open(pb, encoding="utf-8") as f:
    content = f.read()

# ── 1. Bump version header ────────────────────────────────────────────────────
old_ver = "**Version:** 0.2 (06/08/2026)"
new_ver = "**Version:** 0.3 (17/08/2026)"
assert old_ver in content, "version header not found"
content = content.replace(old_ver, new_ver, 1)

# ── 2. Update cross-ref table: add §VIII row ──────────────────────────────────
old_data_row = "| DATA | **L-48** (Alpha fullyDelisted ABSTAIN) |"
new_data_row  = ("| DATA | **L-48** (Alpha fullyDelisted ABSTAIN) |\n"
                 "| §VIII (Học thuyết) | Học thuyết phiên 17/08 — "
                 "GOM THẬT 2×2, un-hedge anatomy, SPRINT/GRIND/BLEED, anti-look-ahead, "
                 "proven_pump, check-trạng-thái |")
assert old_data_row in content, "DATA row not found"
content = content.replace(old_data_row, new_data_row, 1)

# ── 3. Update version footer ──────────────────────────────────────────────────
old_footer = "*Playbook v0.2 —"
new_footer  = ("*Playbook v0.3 — cập nhật 17/08/2026: thêm §VIII Học Thuyết 14 block "
               "(phiên 17/08), bump version. ")
assert old_footer in content, "footer not found"
content = content.replace(old_footer, new_footer, 1)

# ── 4. Append §VIII before the cross-ref Phụ lục block ───────────────────────
# Insert after the last "---\n\n## Phụ lục: Cross-reference" heading
SEPARATOR = "---\n\n## Phụ lục: Cross-reference Lessons theo Lớp"
assert SEPARATOR in content, "Phụ lục separator not found"

SECTION_VIII = """\
---

## §VIII. Học Thuyết — Phiên 17/08/2026

*Nguồn: `docs/handover/analysis_handover_20260817.md` §2.
Cross-ref: ON, GUA, BTW, APR, AIN, BANK, TUT, PARTI, KOMA, BANANAS31.*

---

### VIII.1 Bốn-vân GOM THẬT + bảng 2×2

**Khung trung tâm phân loại:** Vân1 tự-số pos_r leo · Vân2 chi-phí (pin trả HOẶC div<1 thu) · Vân3 kiểm-soát-giá (dip bị mua-đảo) · Vân4 on-chain RÚT-tại-nền.

**Bảng 2×2** (pos leo? × rút/nạp?):
- Trên-trái = **GOM THẬT** (FF/ZBT/TUT — đi cùng)
- Dưới-phải = **STAGED-DIST** (ON/BTW/GUA/APR/AIN — tránh đường)

> "Gom bao nhiêu" với captive = câu sai thì. Không đặt câu hỏi này cho STAGED-DIST.

---

### VIII.2 Giải phẫu un-hedge ON (ground truth GOM-E)

**Trình tự chuẩn loài:**
`deposit(T−6) → flush(T−5) → un-pin+cover(T−2, pin vỡ + cover CÙNG NGÀY 17/07, pos +30%/1d + OI_token giảm êm 2d) → ignite(T0, trễ 1 ngày) → +230%/12d → div không bao giờ quay lại <1`

**Tự-mẫu bắt buộc:**
- cover thật = TỰ SỔ (pos_r tăng) + OI co
- DENOM-thaw (acc sắp bán) = flush, **không phải** un-hedge

---

### VIII.3 Hai tư thế chờ của captive

| Tư thế | Điều kiện | Ví dụ |
|--------|-----------|-------|
| **Hedged-waiting** | div<1, thu funding | ON, AGT, GUA, AIN |
| **Committed-long** | div≥1.3 | BTW |

> Pin KHÔNG phải điều kiện cần của loài (ON có pin 47d, BTW không pin).

---

### VIII.4 Thước rũ-đàn 4 màn (ON)

`bò-sửa → rũ-thật-bại (flush crash → đàn bò lại) → rũ-bằng-NỀN-XANH → lật phe (xuyên 1.0)`

- Mốc: gLSR 1.2 / 1.0
- Quy luật: nền lớn nhất chờ đến **SAU** đàn sạch
- **Cảnh báo:** "gLSR rơi trong rally" KHÔNG phải mất đà — đó là màn rũ đúng bài

---

### VIII.5 M6 HAI CHẾ ĐỘ (operator sửa khung, GUA 11/08)

| Chế độ | Điều kiện | Mẫu |
|--------|-----------|-----|
| **STEALTH** | kho/MC ≤10% vol hiện hành | phần lớn case nhỏ |
| **FOMO-mode** | kho/MC >100% (GUA=260%) | GUA, KOMA ($1.2B/48h/MC $8.5M) |

- FOMO-mode: pump TỰ SẢN XUẤT vol; bán vào euphoria + bán tiếp vào collapse
- Kho/MC >100% = **bắt buộc** FOMO-mode/nhiều-wave/perp-centric
- Dùng stealth-math cho FOMO-campaign → kết luận "bất khả thi" là **giả**

---

### VIII.6 Taxonomy nạp-ký SPRINT / GRIND / BLEED

**Discriminator thắng/thua = CHIỀU GIÁ trong cửa sổ nạp** (hình dạng chỉ quyết TỐC ĐỘ đồng hồ):

| Loài | Pattern | Đồng hồ | Ví dụ |
|------|---------|---------|-------|
| **SPRINT** | nạp-BẬC + giá giữ | 1–6d | APR, BANK, BULLA, CAP, GUA |
| **GRIND** | nạp-ĐỀU + giá giữ | tuần–tháng (cuối >80%) | BTR, AT, TURTLE, BMT |
| **BLEED** | nạp + giá bleeding | suppress | RIVER |

*(ground truth: 70-fire dataset, 15/08/2026)*

---

### VIII.7 Composite fire→deposit = Đồng hồ ignite

Hai thì một câu: **fire = ghẻ xong; nạp-bậc sau fire 1–22d = đồng hồ ignite**.

Ví dụ: BANK fire 04/07 → nạp $11M 15–26/07 → +144.9%.

---

### VIII.8 Outcome-window THEO LOÀI

| Loài | Cửa sổ |
|------|--------|
| SPRINT | 7–14d |
| GRIND | 30–60d / tới-sự-kiện |

> Một cửa sổ chung tự chế nhóm "flat" **không tồn tại**.
> Án BTR/AT/TURTLE/BMT bị mg14 dán flat trong khi outcome >80%.

---

### VIII.9 Fire-date = mốc tiền-định + Anti-look-ahead

- **Fire-date** = mốc đo tiền-định (close-date = đo hậu-campaign, câu hỏi khác)
- **Anti-look-ahead rule:** filter chỉ dùng thông tin có tại điểm entry
  - net>0-tại-close = look-ahead (**không hợp lệ**)
  - Bản hợp lệ = **net-to-date tại fire+K**

---

### VIII.10 proven_pump prior (PARTI)

Team chưa từng đẩy +100%/≤7d → **mọi staging mang mùi xả**.

> Check EVENTS một dòng trước khi đánh giá intent của bất kỳ staging nào.

---

### VIII.11 net_k3 âm đậm = cờ xấu ổn định

- SKYAI −11.3M → hold 0.157 (flat/âm)
- Cụm −0.6M..−1M → đều flat/âm

> Dấu dương **không chọn người thắng** (BANK âm vẫn +145%).

---

### VIII.12 Định luật #5 + Pin vỡ + APR lesson GOM-A

- **Định luật #5 validated thêm:** TUT gLSR 1.11 → đỉnh sau ~24h
- **Pin vỡ = phát lệnh** (khuôn ON/TAG)
- **APR lesson:** pin/build KHÔNG phải điều kiện cần loài event-serial có fuel-short sẵn
  - GOM-A fire + oi_floor + gLSR≤1.2 + nhịp event = đủ nâng WATCH-B
  - Autopsy: WATCH-C miss ×3 vì đòi pin

---

### VIII.13 Hệ bệnh công thức (regression checklist)

| Bệnh | Mô tả | Fix |
|------|-------|-----|
| **M1** | mean-of-ratios | ratio-of-means |
| **h2 confound** | share-based metric mẫu-số phụ thuộc archetype | h2r ratio-log (3 cột: h2r · h2r_log · rate_neg_usd_hr) |
| **outcome-window đồng-loại** | đo mọi case cùng 1 window (§2.8) | window theo loài SPRINT/GRIND |

---

### VIII.14 Check-trạng-thái-trước-phát-biểu

Trước verdict nhắc một hồ/spec → **check sống/chết trong sổ TRƯỚC**.

> Án AIH 13/08: ANALYSIS viết trên H-tier đã archive vì đọc context nén — verdict sai loài.

---

"""

content = content.replace(SEPARATOR, SECTION_VIII + SEPARATOR)

# ── 5. Write back ─────────────────────────────────────────────────────────────
with open(pb, "w", encoding="utf-8") as f:
    f.write(content)

lines = content.count("\n")
print(f"Written: {pb.name} ({lines} lines)")
print("Version bump: 0.2 → 0.3")
print("§VIII appended: 14 blocks")
print("[DONE]")
