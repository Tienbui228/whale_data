# RENDER-V2 · PRE-SPEC + LỊCH · KÝ 29/08 · zero-code hôm nay

**Status:** R1 CODE TREO chờ spec-diff · Đêm-4 TỐI NAY chạy render v1 nguyên trạng · không đụng gì trước verify.

Doc này pin data-mốc + khai split-ownership + đăng ký lịch triển khai. Fixture expected chờ spec chi tiết.

---

## §1 · PIN-ROW PRE-STAGE (data 28/08 · latest smoke-3 post-wire log block)

**Data source:** VPS `data/logs/gom_h_daily.log` latest `[TELEGRAM BLOCK]` target=2026-08-28 (SMOKE-3 append)  
**Row count niêm (a):** **n_v1 = 33 rows** (mốc fixture đếm-bảo-toàn · render-v2 output PHẢI giữ 33 rows total sau khi tách/format)

### 3 Pin-rows (chọn row · CHƯA viết expected · chờ spec-diff)

**(b) STRESS ∧ ret<0 → TACUSDT**
```
TACUSDT  [[suppressed:kho]]  conf=LOW (1/4; N/A: -)  H3=F  [SUPPRESSED 3/14 lane=kho]  [WALLETSET: BROAD-STRESS · vol=16.8x ret=-41.0%]
```
Đặc điểm: WALLETSET BROAD-STRESS 2-vế (vol + ret) · ret ÂM · lane=kho suppressed 3/14 · conf=LOW · H3=F.

**(c) H3=T-trong-suppressed → BTRUSDT**
```
BTRUSDT  [[suppressed:kho+perp]]  conf=LOW (0/4; N/A: -)  H3=T  [SUPPRESSED 1/14 lane=kho] [SUPPRESSED 1/14 lane=perp]  [WALLETSET: BROAD-STRESS · vol=87.5x]
```
Đặc điểm: H3=T (H3 raw pass · confidence booster) NHƯNG token đang trong SUPPRESSED cả 2 lane (kho + perp) · conf=LOW 0/4 · WALLETSET BROAD-STRESS 1-vế vol=87.5×.

**(d) HIGH-trong-suppressed → MIRAUSDT**
```
MIRAUSDT  [[suppressed:perp]]  conf=HIGH (4/4; N/A: -)  H3=F  [SUPPRESSED 4/14 lane=perp]
```
Đặc điểm: conf=HIGH 4/4 (đủ mạnh) NHƯNG lane=perp đang SUPPRESSED 4/14 (đợt cooldown dài hạn). Ma quái: mức tin cao nhất mà vẫn bị dập.

### Kỳ vọng render-v2 (chờ spec-diff)
- 4 pin-rows (a·b·c·d) mỗi row có expected output cụ thể trong fixture
- Fixture rebuild qua fixture-trọng-tài IMPORT prod (L-66)
- SELF-CHECK-COMPOSE-N pass ≥3 case cover leg-set (per PROBE-SUBMIT RULE án lệ #2)

---

## §2 · SPLIT-OWNERSHIP (điểm giao với TG-RELAY vừa vá)

### Chủ split · nhánh hiện tại
- **Relay `_split_at_line_boundary()`** (KÝ 29/08 · TRUNCATION FIX) — generic splitter, cắt tại ranh dòng, BẤT BIẾN trailing-3-dòng-tin-cuối, numbering `[GOM-H k/N]`
- Vai relay hiện: CHỦ split (khi Telegram-block > 3900 chars)

### Chủ split · sau RENDER-V2
- **Render-v2 = CHỦ split DUY NHẤT** (semantic split theo khối ⏳ · R1 spec)
  - Cắt theo semantic (RIPE / STRESS / SUPPRESSED / etc.) — biết nội dung, cắt đúng ranh
  - Ranh dòng (không cắt giữa row) — kế thừa từ relay
  - ≤ 4096 chars/tin (Telegram limit)
  - Numbering `[GOM-H k/N]` thống nhất khuôn với relay
- **Relay `_split_at_line_boundary()`** hạ xuống **GUARD cuối** — chỉ trigger khi render lỡ tràn part limit (defensive · không thay thế semantic split của render-v2)

### BẤT BIẾN xuyên qua render-v2
- **Trailing 3 dòng WIRE-V2** (`tripwire · ↳ 7 TP · # tripwire_v2 flag action`) **KHÔNG thuộc khối ⏳ nào** · LUÔN đóng tin CHÓT (tin cuối trong sequence `[GOM-H N/N]`)
- Render-v2 xử: trailing block emit SAU khi tất cả khối ⏳ split xong · nếu tin cuối + trailing > 4096 → trailing thành tin riêng `[GOM-H N/N]`
- Relay guard fallback: nếu render-v2 vô tình đặt trailing giữa · relay `_split_at_line_boundary()` re-check invariant

### Numbering thống nhất
Cả render-v2 (chủ) + relay (guard) dùng cùng khuôn `[GOM-H k/N]` header per part. Không lộn 2 hệ numbering.

---

## §3 · R3 · errata sort-RIPE + fixture sort-order pin GỘP vào render-v2 commit

**Chuyển nhà:** item "tg_render sort-RIPE fix" khỏi SCP-SAU checklist (scp_batch_revised_20260829.md) → gộp vào render-v2 deploy commit.

**Lý do:** render-v2 sẽ rewrite `scanner/tg_render.py` (thay logic sort · thêm semantic split · thêm ⏳ block partition). Fix sort-RIPE (spec §0 `RIPE trước, rồi conf`) đi CÙNG lượt sửa file · zero điểm merge riêng.

**Fixture sort-order pin:** thêm 1 fixture case verify sort order = `RIPE bucket first (S2-LATE, S2-MID↑) → within bucket sort by conf DESC`. Pin data 28/08 · expected output chờ spec-diff.

---

## §4 · LỊCH đề xuất (một-biến-một-đêm)

| đêm | date | biến | scope |
|---|---|---|---|
| **Đêm-4 verify** | 30/08 01:45 UTC | **KHÔNG ĐỔI** | cron 01:45 (tripwire trailing lần đầu VPS) + relay 01:55 (Telegram thật đầu tiên) · verify pipeline end-to-end · KHÔNG code |
| **Đêm-5 SHIFT** | 31/08 slot mới | zero-code | SHIFT slot dựa trên STALENESS-MAP (build sau Đêm-4) · điều kiện tiên quyết chống stale-19/08 · watchlist/regrade không đụng |
| **Đêm-6 RENDER-V2 deploy** | 01/09 | code | Render-v2 spec R1 · R3 gộp cùng · fixture 4-pin-row pass · SCP + smoke |
| **Đêm-6+7 R4 verify** | 01-02/09 | verify | 2 đêm cron chạy render-v2 · check sort-RIPE + semantic split + trailing invariant |

### Nếu operator muốn đảo (render trước, shift sau)
Một chữ **"đảo"** — swap Đêm-5 ↔ Đêm-6.

### Mặc định
Chuông về **08:26 VN sớm nhất** (SHIFT giảm sync-time · gom_h fires sớm hơn · relay follow).

---

## §5 · Không có việc code hôm nay

- Đêm-4 chạy render v1 nguyên trạng (chưa đụng gì · SCP đợt-1 batch-4 đã đóng sổ + WIRE-TRIPWIRE-V2 đã lên)
- Chờ spec-diff RENDER-V2 (Đêm-6 mới cần) · pre-stage này là mốc trước
- STALENESS-MAP sau Đêm-4 verify (không build trước · điều kiện tiên quyết chống mù)

## Ref cross-links

- Đêm-3 report: [dem3_c_report_20260829.md](../handover/dem3_c_report_20260829.md)
- WIRE-TRIPWIRE-V2 commit `3b82edb` + smoke `ccf504df`
- TG-RELAY truncation fix commit `238bc7e` (invariant trailing-cuối)
- A6(ii) audit finding (sort-RIPE spec vs impl drift): [audit_suite_phase_tag_v0_4_era_20260828.md](../reports/audit_suite_phase_tag_v0_4_era_20260828.md)
- SCP-SAU original: [scp_batch_revised_20260829.md](../handover/scp_batch_revised_20260829.md) (sẽ update rm sort-RIPE)
