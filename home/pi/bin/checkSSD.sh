#!/bin/bash

DATA_DIR='/data/thm_timelapse'
TEST_DIR='/data/lost+found'
LOGS_DIR='/data/logs'
DATE=`date +%Y%m%d`
TIME=`date +%H%M%S`
LOG_FILE="/soh/VIGIA_SOH_${DATE}.log"

echo "[${DATE}T${TIME}] Verifying data drive" >> ${LOG_FILE}
if [[ ! -d $TEST_DIR ]] ; then
    echo "[${DATE}T${TIME}] Target directory not found. Trying to mount drive" >> ${LOG_FILE}
    mount /data >> ${LOG_FILE}
fi