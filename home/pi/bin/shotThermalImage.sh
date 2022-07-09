#!/bin/bash
DATA_DIR='/data/thm_timelapse'
PROG_DIR='/home/pi/Optris/python'
SCPT_DIR='/home/pi/bin'
LOGS_DIR='/data/logs'
DATE=`date +%Y.%m.%d`
TIME=`date +%H:%M:%S`
LOG_FILE=${LOGS_DIR}/capture/VIGIA_Captura_${DATE}.log
GEN_LOGF="/soh/VIGIA_SOH_${DATE}.log"

echo "Capture started at ${TIME}" >> ${LOG_FILE}
if [[ ! -d /data/lost+found ]] ; then
    echo "Target directory not found. Trying to mount drive" >> ${LOG_FILE}
    echo "[${DATE}T${TIME}] Target directory not found. Trying to mount drive" >> ${GEN_LOGF}
    mount /data >> ${GEN_LOGF}
fi

cd ${SCPT_DIR}
CTRD_IMG=`python3 one_shot_thermal.py`
OUT_MSG=${CTRD_IMG%_*}
echo $OUT_MSG

if [[ ${CTRD_IMG##*.} == "npz" ]] ; then
    if [[ ${OUT_MSG%_*} == "VIGIA_IR" ]] ; then
    	python3 identifyVolcano.py ${DATA_DIR}/${DATE}/${CTRD_IMG}
        ${SCPT_DIR}/moveThRecent.sh >> ${LOG_FILE}
    else
    	echo "Img captured but other message" >> ${LOG_FILE}
    fi
else
	echo "Error capturing the thermal image" >> ${LOG_FILE}
fi

mv ${SCPT_DIR}/.tmp/th2min*.log ${LOGS_DIR}/thm_timelapse

if (( $(cat /home/pi/.status) )) ; then
	sudo cp /home/pi/config/default/crontab_actv /etc/crontab
    #crontab -u pi /home/pi/config/default/crontab_actv
#    ${SCPT_DIR}/serialize_raw
else
	sudo cp /home/pi/config/default/crontab_wait /etc/crontab
    #crontab -u pi /home/pi/config/default/crontab_wait
fi

pkill shotThermalImage