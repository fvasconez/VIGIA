#!/bin/bash

# This script copies the last 10 thermal images to use them for showing purposes

# @author fvasconez
# @created 2021.11.10

ORIG_DIR='/data/thm_timelapse'
DEST_DIR='/home/pi/Pictures/Thermal'
SCPT_DIR='/home/pi/bin'
LOGS_DIR='/data/logs/recognizing'

# Current day (2 formats), hour and minute
CUR_DAY=`date +%Y.%m.%d`
CUR_DAT=`date +%Y%m%d`
CUR_HOU=`date +%H`
CUR_MIN=`date +%M`

# Check destination 
function check_dest() {
	# number of png files in the directory
    N=`ls ${DEST_DIR} | grep -c .png`
    # list of png files
    exist_files=(`ls ${DEST_DIR}/*.png`)
    # Assuming all have the same suffix, extract it
    SUFFIX=${exist_files[0]%_*}
    
    # rename the files overwriting the last one
    if [[ ${N} -ge 10 ]] ; then
	N=9
    fi
    for ((i=${N} ; i > 0 ; i--)); do
		mv ${SUFFIX}_$((i-1)).png ${SUFFIX}_${i}.png
    done
}

LST_FILES=(`ls ${ORIG_DIR}/${CUR_DAY}/*_${CUR_HOU}*.npz`)

# Verify if the last picture has already been processed for volcano identifying
LOGGED="`tail -1 ${LOGS_DIR}/volcRec_${CUR_DAT}.log | awk -F']' '{print $1}' | awk -F'T' '{print $2}'`"
IMG_SX=${LST_FILES[-1]##*_} 
IMG_SX=${IMG_SX%.npz}
echo ${IMG_SX} ${LOGGED}
check_dest
# the use of 'bc' assures that the $IMG_SX and $LOGGED are treated as integers
if (( $(echo "${IMG_SX} < ${LOGGED}"| bc) )) ; then
	
	python3 ${SCPT_DIR}/identifyVolcano.py ${LST_FILES[-1]}
	#python3 ${SCPT_DIR}/ind_checkPictures.py ${LST_FILES[-1]} ${DEST_DIR}
fi
python3 ${SCPT_DIR}/ind_checkPictures.py ${LST_FILES[-1]} ${DEST_DIR}