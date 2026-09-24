"""R1b · SKELETON RETIRED · điền tham số từ rulings 24/09 · thay bằng file thực.

TRẠNG THÁI: RETIRED · thay bằng:
  - `_probe_r1b_pseudo_bell_20260924.py` (md5 cec7dc892a3a969e343289b16a2fb267)
  - `_probe_r1b_detector_20260924.py`     (md5 72b880021f2662d9d7d0deeeaf9819d9)

Đính chính G3 skeleton cũ:
  - CŨ trích sai: "mục 2/4" của file rulings 23/09 (C5+C6 / C8)
  - ĐÚNG: "mục 2/4" trong R1b-1/R1b-2 chỉ các điểm 2 và 4 của Section 1 file rulings 24/09
    (docs/analysis_rulings_holdout_20260924.md · md5 04f2826b884bde92ceb994af75bc849d)

Placeholder cũ (GATE/LOOKAHEAD/ANCHOR/BUCKETS/THRESH) BỎ · tham số đã ký trong rulings 24/09:
  - Nền = pseudo-bell ngẫu nhiên (rulings 24/09 mục 1 point 2)
  - SEED=20260924 · R=500 · KHÔNG hoàn lại · gộp 14d · loại outage 24-26/07
  - Cửa sổ calib 2026-06-19 → 2026-09-05 · n≥50/dải · median + [5%, 95%]
  - Bucket [0, 0.3) · [0.3, 0.4) · [0.4, 0.5] (theo C9 · registration R1 L64)
  - Anchor = D_first · cross-check [D_first+1, D_first+10] (Q1)
  - Lift chấm = P_obs / Σ w_b · median(base_b)

Đối chứng đã ký (rulings 24/09 mục 1 point 4 · mục 2):
  - Detector: div_avg3(D) ∈ [0.4, 0.5] · KHÔNG Δacc · gộp 14d · window 10d
  - Thắng = precision_bell > precision_ctrl ∧ lead_bell ≥ lead_ctrl

Registration file: `docs/holdout_u0bell_r1b_registration_20260924.md` (pin body md5 d7a1e3a64e5af2c4524373d7cc4b1933)

File này CHỈ để đánh dấu skeleton cũ đã retired · không import · không chạy.
"""
if __name__ == "__main__":
    import sys, io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    print("R1b skeleton RETIRED · dùng _probe_r1b_pseudo_bell_20260924.py + _probe_r1b_detector_20260924.py")
    print("Nguồn phán: docs/analysis_rulings_holdout_20260924.md (md5 04f2826b884bde92ceb994af75bc849d)")
    print("Registration: docs/holdout_u0bell_r1b_registration_20260924.md (body md5 d7a1e3a64e5af2c4524373d7cc4b1933)")
