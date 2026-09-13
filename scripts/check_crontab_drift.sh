#!/bin/bash
# check_crontab_drift.sh · Option C guard · KÝ 13/09
#
# So sánh md5(crontab -l) với baseline data/state/crontab_expected.md5.
# Khớp → rm flag + log OK. Lệch → ghi flag + log DRIFT + exit 1.
# Baseline missing → log NO-BASELINE + ghi flag + exit 1 (KHÔNG tự sinh).
#
# Auto-sinh baseline = cổng tự khoét cửa hậu (bệnh harness L174).
#
# Env override for testing:
#   CRONTAB_DRIFT_CMD   = command to fetch crontab (default: "crontab -l")
#   CRONTAB_DRIFT_REPO  = repo root (default: /root/Data_back_test/whale_data)

set -u  # error on unset vars (không set -e vì exit non-zero là output có ý)

REPO="${CRONTAB_DRIFT_REPO:-/root/Data_back_test/whale_data}"
CMD="${CRONTAB_DRIFT_CMD:-crontab -l}"
EXPECTED_FILE="${REPO}/data/state/crontab_expected.md5"
FLAG_FILE="${REPO}/data/state/crontab_drift.flag"
TS="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

# Fetch current crontab md5 · cắt trường đầu (an toàn với format `<hash>  -` từ stdin)
CUR_RAW="$($CMD 2>/dev/null | md5sum)"
CUR="$(echo "$CUR_RAW" | cut -d' ' -f1)"
if [ -z "$CUR" ]; then
    echo "${TS}  ERROR  cannot read crontab (cmd='${CMD}')"
    echo "{\"ts\":\"${TS}\",\"reason\":\"CRONTAB-READ-FAIL\",\"cmd\":\"${CMD}\"}" > "$FLAG_FILE"
    exit 1
fi

# Baseline check
if [ ! -f "$EXPECTED_FILE" ]; then
    echo "${TS}  NO-BASELINE  expected=(missing:${EXPECTED_FILE})  actual=${CUR}"
    echo "{\"ts\":\"${TS}\",\"reason\":\"NO-BASELINE\",\"actual\":\"${CUR}\",\"expected_file\":\"${EXPECTED_FILE}\"}" > "$FLAG_FILE"
    exit 1
fi

# Read expected md5 · cắt trường đầu (chấp nhận `<hash>` HOẶC `<hash>  -` HOẶC `<hash>  filename`)
EXP_RAW="$(head -1 "$EXPECTED_FILE")"
EXP="$(echo "$EXP_RAW" | cut -d' ' -f1)"
if [ -z "$EXP" ]; then
    echo "${TS}  ERROR  baseline file empty or malformed: ${EXPECTED_FILE}"
    echo "{\"ts\":\"${TS}\",\"reason\":\"BASELINE-MALFORMED\",\"actual\":\"${CUR}\"}" > "$FLAG_FILE"
    exit 1
fi

# Compare · in CẢ expected LẪN actual mỗi lần (kể cả OK) để log tự-audit
if [ "$CUR" = "$EXP" ]; then
    rm -f "$FLAG_FILE"
    echo "${TS}  OK  expected=${EXP}  actual=${CUR}"
    exit 0
else
    echo "${TS}  DRIFT  expected=${EXP}  actual=${CUR}"
    echo "{\"ts\":\"${TS}\",\"reason\":\"DRIFT\",\"expected\":\"${EXP}\",\"actual\":\"${CUR}\"}" > "$FLAG_FILE"
    exit 1
fi
