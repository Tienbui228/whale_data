# TICKET · CRONTAB-IN-GIT · draft 2026-09-13

## Bối cảnh

Crontab VPS đang là "black-box": chỉ nằm ở `/var/spool/cron/crontabs/root` trên máy production.
Không có version history · không audit trail · không thấy được đổi gì lúc nào bởi ai.

Case 09-13: dời alpha cron 02:00 → 01:30 UTC để chữa race parquet. Phải SCP `crontab.bak`
thủ công về `ops/crontab_vps_20260913_pre_alpha_move.txt` để có bản lùi lịch sử. Bản chưa
dời (trước cả 02:00 alpha) không còn tra được.

## Đề xuất

**Option A · Manual commit mỗi lần đổi**:
- Mỗi lần chạm crontab: `ssh root@vps "crontab -l" > ops/crontab_vps_YYYYMMDD.txt`
- Commit với message ghi rõ thay đổi + lý do
- Ưu: minh bạch · sạch · không thêm cron nào
- Nhược: phụ thuộc kỷ luật (dễ quên nếu ai đó edit tay)

**Option B · Daily auto-dump cron**:
- Thêm cron nhỏ: `0 4 * * * crontab -l > /root/Data_back_test/whale_data/ops/crontab_vps.txt`
  (04:00 UTC · sau tất cả cron 01:xx-04:xx)
- Push vào git bằng cron riêng hoặc để agent thấy diff lần sau kéo về
- Ưu: tự động · bắt được mọi thay đổi
- Nhược: cần cron ghi vào repo path · push tự động phức tạp · commit noise

**Option C · Manual + guard**:
- Manual commit (Option A) + thêm daily diff-check
- Cron 04:00 UTC: `diff /var/spool/cron/crontabs/root <(cat ops/crontab_vps_LATEST.txt) > /dev/null || echo "CRONTAB DRIFT $(date -u)" >> data/logs/crontab_drift.log`
- Nếu VPS crontab đổi mà repo chưa update → drift.log ghi cảnh báo
- Ưu: giữ discipline manual · bắt drift · không noise commit
- Nhược: cần script drift-check

## Khuyến nghị DEV

**Option C** — giữ manual commit làm chính (kỷ luật rõ ràng), thêm drift-check làm lưới an toàn.

Steps:
1. Commit ngay: ops/crontab_vps_20260913.txt (post-alpha-move · current) + ops/crontab_vps_20260913_pre_alpha_move.txt (pre-move · rollback source)
2. Sau: mỗi lần chạm crontab → SCP về ops/ với date suffix + commit
3. (Nợ) wire drift-check cron sau khi test manual pattern ổn định 2-4 tuần

## Files

- ops/crontab_vps_20260913.txt (post-alpha-move · md5=db429ca69ee1)
- ops/crontab_vps_20260913_pre_alpha_move.txt (backup · md5=392e0f8c4df2)
- diff = 2 dòng (line 26+27 · alpha comment + schedule)

## Assign

DEV (auto-dump wire) + operator (kỷ luật commit)

## Chờ chữ ký

Chọn A/B/C. DEV không tự chạy · commit chỉ 3 file (2 crontab + ticket) hôm nay.
