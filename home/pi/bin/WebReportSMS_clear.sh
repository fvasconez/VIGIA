#!/bin/bash

#  WebReportSMS.sh
#  
#  @author fvasconez
#  @created 2021.02.10
# 
#  This script sends SMS using FreeMobile SMS API

# Wait some seconds to be sure that last image was processed
sleep 15
# Variables
TMP=`date +%Y%m%d_%H%M%S`
MSG="UTC:%20$TMP%0ADefault%20message%20from%20VIGIA%0A*Here%20I%20am!*"
PAG="https://smsapi.free-mobile.fr/sendmsg"
#USR="46371808"
#PSW="zxrZAmwJ2X7mLY"
USR="41545613"
PSW="bEjK9mtLCCm8qc"
LOG="/data/logs/SMS/`date +%Y%m%d`.log"

in_file="/data/logs/recognizing/volcRec_`date +%Y%m%d`.log"

# Read the state from the log file
RES=`tail -1 $in_file | grep -c Clear`
FFILE=".first.sgn"
# Has the state been reported yet?
FIRST=`cat $FFILE`

if [[ $RES == '1' ]]; then
    if [[ $FIRST == '1' ]]; then
    	# Write the message
      	MSG="Volcan%20cleared%20since%0A$TMP%20[UTC]"
        echo "0" > $FFILE
        echo "[$TMP] Sending message:$MSG" >> $LOG
        # Send the message
        curl "$PAG?user=$USR&pass=$PSW&msg=$MSG"
    fi
else	# the volcano is clouded, no message to send
    echo "1" > $FFILE
fi