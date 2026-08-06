# E: P2 G1 — State-per-day replay (12 cases)
Generated: 2026-08-06T03:42:18Z

Signal abbreviations:
- A=lsr_accum  H=hedge_structure  PR=pos_rerate  FP=funding_pinned  FU=funding_unpin
- CF=crowd_flush  SG=stealth_grind  S3=s3_eve  OI=oi_ignition  AB=absorption
- FN=funding_neg_div  FE=funding_extreme  DW=dist_wall  LD=lsr_dist  DC=decay  PC=post_climax
- `.` = no signal

## State-per-day matrix

```
  date |       BANK        AKE        TAG        BAS      POWER      BASED        CLO        BTW        TUT      BULLA    ESPORTS       IDOL
-------------------------------------------------------------------------------------------------------------------------------------------
 06-19 |          .          .          .          .          .          .          .          .          .          .         PC          .
 06-20 |          .          .          .          .          .          .          .          .          .          .         PC          .
 06-21 |          .          .          .          .          .          .          .         PC          .          .         PC          .
 06-22 |          .          .          .          .          .          .          .         PC          .          .         PC          .
 06-23 |          .          .          .          .          .          .          .         PC          .          .      PC+DC          .
 06-24 |          .          .          .          .          .          .          .         PC          .         DC      PC+DC          .
 06-25 |         AB          .         FP          .          .          .          .         PC          .          .         PC         FP
 06-26 |         AB          .      FP+AB          .          .          .          .      PC+FN          .          .      PC+AB         FP
 06-27 |      AB+FP          .      FP+AB          .          H          .          .         PC          .          .         PC         FP
 06-28 |         AB          .      FP+AB          .       H+AB          .          .         PC          .          .         PC         FP
 06-29 |       AB+A          .      FP+AB          .          H          .          .         PC         AB          H    PC+FN+H         FP
 06-30 |       AB+A          .  FP+AB+FP!          .       H+AB          .          .         PC         AB          H       PC+H     FP+FP!
 07-01 |       AB+A          .  FP+AB+FP!          .       H+AB         OI          .         PC         AB          H       PC+H     FP+FP!
 07-02 |    AB+A+CF          .  FP+AB+FP!         PC       H+AB      OI+SG          .       PC+A          .       H+AB    PC+DC+H  FP+FP!+CF
 07-03 |    AB+A+CF         OI  FP+AB+FP!   PC+CF+OI       H+AB      OI+SG          .       PC+A         FP       H+AB       PC+H         CF
 07-04 |    AB+A+CF         OI     FP+FP!      PC+CF       H+AB      OI+SG         AB       PC+A         FP          H          H      CF+FU
 07-05 |    AB+A+CF         OI  FP+AB+FP!         PC       H+AB   OI+SG+CF         AB       PC+A         FP    H+AB+CF          H         FU
 07-06 |       AB+A         OI  FP+AB+FP!         PC       H+CF          .         AB          .         FP       H+AB          H       A+PR
 07-07 |       AB+A         OI  FP+AB+FP!         PC       H+CF          .         OI          .         FP       H+AB          H         PR
 07-08 |    AB+FP+A         DC     FP+FP!      PC+CF    H+CF+OI         CF         OI          .     FP+FP!       H+AB       DC+H      PR+AB
 07-09 | AB+FP+A+PR         CF         CF         PC      CF+OI          .          .          .     FP+FP!       H+AB          H         AB
 07-10 | AB+FP+A+PR         PR   CF+FU+OI       PC+A         OI          .          .         DC     FP+FP!          H          H         AB
 07-11 |       AB+A         PR      CF+OI       PC+A         OI          .         OI         DC FP+FP!+CF+SG       H+AB          H          .
 07-12 |       A+FU          .    CF+OI+A PC+A+PR+FP+AB       H+OI         FP   OI+CF+SG      DC+AB FP+FP!+CF+SG       H+AB          H         CF
 07-13 |       A+FU          .       OI+A PC+A+PR+FP          H         FP   OI+CF+SG         AB FP+FP!+CF+SG       H+AB          H         CF
 07-14 |    A+FU+SG         S3       OI+A    PC+A+FP          H      CF+FP   DW+OI+SG         AB      SG+PR       H+AB          H         CF
 07-15 | A+FU+SG+OI      OI+CF       FP+A      PC+FP          H      CF+FP   DW+OI+SG         AB         SG       H+CF          H         OI
 07-16 | A+FU+SG+OI      OI+CF       FP+A      PC+FP          H      CF+FP      DW+OI         AB         PR         CF       H+OI         OI
 07-17 |    A+SG+OI      OI+CF          A     FP+FP!          H  FP+FP!+AB      DW+LD         AB         AB   CF+SG+OI    H+OI+CF         OI
 07-18 |    A+SG+OI    OI+CF+A AB+FU+A+PR     FP+FP!       H+AB     FP+FP!         LD      DC+AB         AB      SG+OI      OI+CF         OI
 07-19 |    A+SG+OI          .          A          .          .          .         LD          .      AB+FP      SG+OI PC+FE+OI+SG         OI
 07-20 | A+CF+SG+OI          .          A         AB          .          .         LD          .         AB   SG+OI+PR PC+H+OI+SG      OI+SG
 07-21 |    A+SG+OI          .          .          .          .          .         LD          .          .         SG PC+H+OI+SG      OI+SG
```

## Gate results (§10)

| Token | Pass | Fail | Status |
|-------|------|------|--------|
| BANK | 5 | 0 | PASS |
| AKE | 3 | 0 | PASS |
| TAG | 5 | 0 | PASS |
| BAS | 2 | 0 | PASS |
| POWER | 4 | 0 | PASS |
| BASED | 5 | 0 | PASS |
| CLO | 2 | 0 | PASS |
| BTW | 2 | 0 | PASS |
| TUT | 4 | 0 | PASS |
| BULLA | 5 | 0 | PASS |
| ESPORTS | 3 | 0 | PASS |
| IDOL | 3 | 0 | PASS |

**Total: 43 pass, 0 fail — ALL PASS ✓**

## Signal fire summary per case

### BANK
- `A` (lsr_accum): 06-29, 06-30, 07-01, 07-02, 07-03, 07-04, 07-05, 07-06, 07-07, 07-08, 07-09, 07-10, 07-11, 07-12, 07-13, 07-14, 07-15, 07-16, 07-17, 07-18, 07-19, 07-20, 07-21
- `PR` (pos_rerate): 07-09, 07-10
- `FP` (funding_pinned): 06-27, 07-08, 07-09, 07-10
- `FU` (funding_unpin): 07-12, 07-13, 07-14, 07-15, 07-16
- `CF` (crowd_flush): 07-02, 07-03, 07-04, 07-05, 07-20
- `SG` (stealth_grind): 07-14, 07-15, 07-16, 07-17, 07-18, 07-19, 07-20, 07-21
- `OI` (oi_ignition): 07-15, 07-16, 07-17, 07-18, 07-19, 07-20, 07-21
- `AB` (absorption): 06-25, 06-26, 06-27, 06-28, 06-29, 06-30, 07-01, 07-02, 07-03, 07-04, 07-05, 07-06, 07-07, 07-08, 07-09, 07-10, 07-11

### AKE
- `A` (lsr_accum): 07-18
- `PR` (pos_rerate): 07-10, 07-11
- `CF` (crowd_flush): 07-09, 07-15, 07-16, 07-17, 07-18
- `S3` (s3_eve): 07-14
- `OI` (oi_ignition): 07-03, 07-04, 07-05, 07-06, 07-07, 07-15, 07-16, 07-17, 07-18
- `DC` (decay): 07-08 [SUPP]

### TAG
- `A` (lsr_accum): 07-12, 07-13, 07-14, 07-15, 07-16, 07-17, 07-18, 07-19, 07-20
- `PR` (pos_rerate): 07-18
- `FP` (funding_pinned): 06-25, 06-26, 06-27, 06-28, 06-29, 06-30, 07-01, 07-02, 07-03, 07-04, 07-05, 07-06, 07-07, 07-08, 07-15, 07-16
- `FP!` (funding_pinned_strong): 06-30, 07-01, 07-02, 07-03, 07-04, 07-05, 07-06, 07-07, 07-08
- `FU` (funding_unpin): 07-10, 07-18
- `CF` (crowd_flush): 07-09, 07-10, 07-11, 07-12
- `OI` (oi_ignition): 07-10, 07-11, 07-12, 07-13, 07-14
- `AB` (absorption): 06-26, 06-27, 06-28, 06-29, 06-30, 07-01, 07-02, 07-03, 07-05, 07-06, 07-07, 07-18

### BAS
- `A` (lsr_accum): 07-10, 07-11, 07-12, 07-13, 07-14
- `PR` (pos_rerate): 07-12, 07-13
- `FP` (funding_pinned): 07-12, 07-13, 07-14, 07-15, 07-16, 07-17, 07-18
- `FP!` (funding_pinned_strong): 07-17, 07-18
- `CF` (crowd_flush): 07-03, 07-04, 07-08
- `OI` (oi_ignition): 07-03
- `AB` (absorption): 07-12, 07-20
- `PC` (post_climax): 07-02, 07-03, 07-04, 07-05, 07-06, 07-07, 07-08, 07-09, 07-10, 07-11, 07-12, 07-13, 07-14, 07-15, 07-16 [SUPP]

### POWER
- `H` (hedge_structure): 06-27, 06-28, 06-29, 06-30, 07-01, 07-02, 07-03, 07-04, 07-05, 07-06, 07-07, 07-08, 07-12, 07-13, 07-14, 07-15, 07-16, 07-17, 07-18
- `CF` (crowd_flush): 07-06, 07-07, 07-08, 07-09
- `OI` (oi_ignition): 07-08, 07-09, 07-10, 07-11, 07-12
- `AB` (absorption): 06-28, 06-30, 07-01, 07-02, 07-03, 07-04, 07-05, 07-18

### BASED
- `FP` (funding_pinned): 07-12, 07-13, 07-14, 07-15, 07-16, 07-17, 07-18
- `FP!` (funding_pinned_strong): 07-17, 07-18
- `CF` (crowd_flush): 07-05, 07-08, 07-14, 07-15, 07-16
- `SG` (stealth_grind): 07-02, 07-03, 07-04, 07-05
- `OI` (oi_ignition): 07-01, 07-02, 07-03, 07-04, 07-05
- `AB` (absorption): 07-17

### CLO
- `CF` (crowd_flush): 07-12, 07-13
- `SG` (stealth_grind): 07-12, 07-13, 07-14, 07-15
- `OI` (oi_ignition): 07-07, 07-08, 07-11, 07-12, 07-13, 07-14, 07-15, 07-16
- `AB` (absorption): 07-04, 07-05, 07-06
- `DW` (dist_wall): 07-14, 07-15, 07-16, 07-17 [SUPP]
- `LD` (lsr_dist): 07-17, 07-18, 07-19, 07-20, 07-21 [SUPP]

### BTW
- `A` (lsr_accum): 07-02, 07-03, 07-04, 07-05
- `AB` (absorption): 07-12, 07-13, 07-14, 07-15, 07-16, 07-17, 07-18
- `FN` (funding_neg_div): 06-26 [SUPP]
- `DC` (decay): 07-10, 07-11, 07-12, 07-18 [SUPP]
- `PC` (post_climax): 06-21, 06-22, 06-23, 06-24, 06-25, 06-26, 06-27, 06-28, 06-29, 06-30, 07-01, 07-02, 07-03, 07-04, 07-05 [SUPP]

### TUT
- `PR` (pos_rerate): 07-14, 07-16
- `FP` (funding_pinned): 07-03, 07-04, 07-05, 07-06, 07-07, 07-08, 07-09, 07-10, 07-11, 07-12, 07-13, 07-19
- `FP!` (funding_pinned_strong): 07-08, 07-09, 07-10, 07-11, 07-12, 07-13
- `CF` (crowd_flush): 07-11, 07-12, 07-13
- `SG` (stealth_grind): 07-11, 07-12, 07-13, 07-14, 07-15
- `AB` (absorption): 06-29, 06-30, 07-01, 07-17, 07-18, 07-19, 07-20

### BULLA
- `H` (hedge_structure): 06-29, 06-30, 07-01, 07-02, 07-03, 07-04, 07-05, 07-06, 07-07, 07-08, 07-09, 07-10, 07-11, 07-12, 07-13, 07-14, 07-15
- `PR` (pos_rerate): 07-20
- `CF` (crowd_flush): 07-05, 07-15, 07-16, 07-17
- `SG` (stealth_grind): 07-17, 07-18, 07-19, 07-20, 07-21
- `OI` (oi_ignition): 07-17, 07-18, 07-19, 07-20
- `AB` (absorption): 07-02, 07-03, 07-05, 07-06, 07-07, 07-08, 07-09, 07-11, 07-12, 07-13, 07-14
- `DC` (decay): 06-24 [SUPP]

### ESPORTS
- `H` (hedge_structure): 06-29, 06-30, 07-01, 07-02, 07-03, 07-04, 07-05, 07-06, 07-07, 07-08, 07-09, 07-10, 07-11, 07-12, 07-13, 07-14, 07-15, 07-16, 07-17, 07-20, 07-21
- `CF` (crowd_flush): 07-17, 07-18
- `SG` (stealth_grind): 07-19, 07-20, 07-21
- `OI` (oi_ignition): 07-16, 07-17, 07-18, 07-19, 07-20, 07-21
- `AB` (absorption): 06-26
- `FN` (funding_neg_div): 06-29 [SUPP]
- `FE` (funding_extreme): 07-19 [SUPP]
- `DC` (decay): 06-23, 06-24, 07-02, 07-08 [SUPP]
- `PC` (post_climax): 06-19, 06-20, 06-21, 06-22, 06-23, 06-24, 06-25, 06-26, 06-27, 06-28, 06-29, 06-30, 07-01, 07-02, 07-03, 07-19, 07-20, 07-21 [SUPP]

### IDOL
- `A` (lsr_accum): 07-06
- `PR` (pos_rerate): 07-06, 07-07, 07-08
- `FP` (funding_pinned): 06-25, 06-26, 06-27, 06-28, 06-29, 06-30, 07-01, 07-02
- `FP!` (funding_pinned_strong): 06-30, 07-01, 07-02
- `FU` (funding_unpin): 07-04, 07-05
- `CF` (crowd_flush): 07-02, 07-03, 07-04, 07-12, 07-13, 07-14
- `SG` (stealth_grind): 07-20, 07-21
- `OI` (oi_ignition): 07-15, 07-16, 07-17, 07-18, 07-19, 07-20, 07-21
- `AB` (absorption): 07-08, 07-09, 07-10
