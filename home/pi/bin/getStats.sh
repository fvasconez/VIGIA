#!/bin/bash

# @author fvasconez
# @created 2021.11.11
# @modified 2021.12.03 : spanish message
# @modified 2022.01.27 : included working hours information

# Check the basic stats based on cloud conditions of the volcano

LOG_DIR='/data/logs/recognizing'
# Statistics from one day. The last complete day is "yesterday"
SEC_NOW=`date +%s`
YESTDAY=`date --date=@$((SEC_NOW - 86400)) +%Y%m%d`
YESD_PT=`date --date=@$((SEC_NOW - 86400)) +%Y.%m.%d`
if [[ $2 != "" ]]; then
	YESTDAY=${2:0:4}${2:5:2}${2:8:2}
	YESD_PT=$2
fi
# Log files have the information to make a report
LOG_FLE="$LOG_DIR/volcRec_$YESTDAY.log"

formatHour() {
    HRS_CLR=$1
    if [[ $HRS_CLR -ne "" ]] ; then
        if [[ $HRS_CLR == 1 ]]; then 
        	HOURS="1 hour and "
            ES_HS="1 hora y "
        else 
        	HOURS="$HRS_CLR hours and "
            ES_HS="$HRS_CLR horas y "
        fi
    else
        HOURS=""
        ES_HS=""
    fi
    if [[ $2 == "esp" ]] ; then
        echo "${ES_HS}"
    else
        echo "${HOURS}"
    fi
}

# Message to send as a report (using a '_' instead of '\n')
MESSAGE="Summary ${YESD_PT}:_"
ESP_MSG="Resumen ${YESD_PT}:_"

# Count total pictures and clear pictures
if [[ -f ${LOG_FLE} ]] ; then
	TOTAL_PICS=`grep -c $YESTDAY $LOG_FLE`
	CLEAR_PICS=`grep -c Clear $LOG_FLE`
	CLOUD_PICS=`grep -c Cloud $LOG_FLE`

	# Calculate the time that the volcano was unclouded 
	#HRS_CLR=$((CLEAR_PICS/30)) this was the way to calculate when each picture represented 2 minutes
    HRS_CLR=$((CLEAR_PICS/60))
    HOURS=$(formatHour $HRS_CLR $1)
    # Calculate the MEASURABLE time that the volcano was unclouded
    MEA_CMN=`grep Clear $LOG_FLE | awk -F"T" '{print $2}' | awk -F']' 'BEGIN{total=0} {if ($1 > 120000 && $1 < 220000) total=total+1} END{print total}'`
    #MEA_CLR=$((MEA_CMN/30)) this was the way to calculate when each picture represented 2 minutes
    MEA_CLR=$((MEA_CMN/60))
    MEA_HRS=$(formatHour $MEA_CLR $1)
    # Calculate the portion of the day that was observed, as there might be gaps in the records
    TOT_MINS=$(($CLEAR_PICS + ($CLOUD_PICS*5)))
    OBS_PERD=$(echo "scale=2; $TOT_MINS/1440" | bc)
   
    if [[ $TOTAL_MINS -lt 1440 ]]; then
    	OBS_PERIOD="0${OBS_PERD} day"
        OBS_PER_ES="0${OBS_PERD} día"
    else
    	OBS_PERIOD="1 day"
        OBS_PER_ES="1 día"
    fi
    # Report
    MESSAGE=${MESSAGE}"Volcano clear approx. ${HOURS}$((CLEAR_PICS-HRS_CLR*60)) minutes ($((CLEAR_PICS*100/TOT_MINS))%) of the observed period (${OBS_PERIOD}),_"
    MESSAGE=${MESSAGE}"from which ${MEA_HRS}$((MEA_CMN-MEA_CLR*60)) minutes during working hours (07h-17h)._"
    ESP_MSG=${ESP_MSG}"Volcán despejado aprox. ${HOURS}$((CLEAR_PICS-HRS_CLR*60)) minutos ($((CLEAR_PICS*100/TOT_MINS))%) total del periodo observado (${OBS_PER_ES}),_"
    ESP_MSG=${ESP_MSG}"de donde ${MEA_HRS}$((MEA_CMN*2-MEA_CLR*60)) minutos durante horas hábiles (07h-17h)._"
	MESSAGE=${MESSAGE}"Total ${TOTAL_PICS} pictures captured. ${CLEAR_PICS} clear._"
    ESP_MSG=${ESP_MSG}"Total ${TOTAL_PICS} imágenes capturadas. ${CLEAR_PICS} despejadas._"

    # Find the last time it was clear
    LAST_CLR=`grep Clear ${LOG_FLE}| tail -1 | awk -F\T '{print $2}' | awk -F\] '{print $1}'`
    if [[ ${LAST_CLR} == "" ]] ; then
    	MESSAGE=${MESSAGE}"The volcano was clouded"
        ESP_MSG=${ESP_MSG}"El volcán no se vio despejado"
    else
    	MESSAGE=${MESSAGE}"Last time cleared at ${LAST_CLR:0:2}:${LAST_CLR:2:2} UTC."
    	ESP_MSG=${ESP_MSG}"Última vez despejado a las ${LAST_CLR:0:2}:${LAST_CLR:2:2} UTC."
	fi
    
	# Find the picture with the most features over the crater
    MAX_QLTY=`grep Clear ${LOG_FLE} | sort -n -k3 | tail -1 | awk -F\T '{print $2}' | awk -F\] '{print $1}'`
    QTY_PICT="/data/thm_timelapse/${YESD_PT}/VIGIA_IR_${YESTDAY}_${MAX_QLTY}.npz"
    # Find the CLEAR picture with the most features over the crater
    MAX_RECD=`grep Clear ${LOG_FLE} | sort -n -k3 | tail -1 | awk -F\T '{print $2}' | awk -F\] '{print $1}'`
    EXM_PICT="/data/thm_timelapse/${YESD_PT}/VIGIA_IR_${YESTDAY}_${MAX_RECD}.npz"

	# Generate the png files of the pictures found
    if [[ $EXM_PICT == "" ]] ; then
    	EXM_PICT=$QTY_PICT
    fi
    #echo "${ESP_MSG}_*****_${MESSAGE}"
    python3 /home/pi/bin/ind_checkPictures.py $QTY_PICT /home/pi/Pictures/Thermal/Clear
    #mv /home/pi/Pictures/Thermal/Clear/VIGIA_IR_0.png /home/pi/Pictures/Thermal/Clear/VIGIA_IR_1.png
    #python3 /home/pi/bin/ind_checkPictures.py $EXM_PICT /home/pi/Pictures/Thermal/Clear
    #gpicview /home/pi/Pictures/Thermal/Clear/VIGIA_IR_0.png
else
	# There was no logfile
    MESSAGE="Sorry: No information available for $YESTDAY"
    ESP_MSG="Lo sentimos: No hay información disponible de $YESTDAY"
fi

if [[ $1 == 'esp' ]]; then 
	echo ${ESP_MSG}
else 
	echo ${MESSAGE} 
fi