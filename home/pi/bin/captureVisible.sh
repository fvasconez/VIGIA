#!/bin/bash


# created 2021/03/11
# autor fvasconez
# Script to capture a picture using gphoto2 without focusing
# Note: If we use autofocus, in low light conditions the picture can't be acquired
# and the focus position remains in a random value, which makes useless the "bulb" 
# function for long exposure pictures.

# Use: shotPicture iso=ISO_SPD shutter=SHT_SPD aperture=APRTURE [mode=Burst] [test]
# During 
USR=$(whoami)
VCLR=`cat /home/pi/.status`
STAT="/home/pi/.vis_status"
SCR_DIR="/home/pi/bin"
FCAM=0
#VCLR=1
HOUR=`date +%H`

# Parameters to use when shooting the picture
MN_PARS=0
ISO_SPD=0
SHT_SPD=1/8
APRTURE=7.1
OP_TIME=480
ST_MODE=""

# Validate the arguments
for arg in $@; do
	if [[ $arg == *"iso"* ]] ; then
    	IFS="=" read -r n ISO_SPD <<< $arg
        MN_PARS=1
    elif [[ $arg == *"shutter"* ]] ; then
    	IFS="=" read -r n SHT_SPD <<< $arg
        MN_PARS=1
    elif [[ $arg == *"apert"* ]] ; then
    	IFS="=" read -r n APRTURE <<< $arg
        MN_PARS=1
    elif [[ $arg == *"mode"* ]] ; then
    	IFS="=" read -r n ST_MODE <<< $arg
        MN_PARS=1
    elif [[ $arg == *"test"* ]] ; then
    	VCLR=1
    fi
done

# Bug: if the hour starts with "0", it is not recognized as an integer and then it cannot be compared in the next step
if [[ ${HOUR:0:1} == "0" ]] ; then
	HOUR=${HOUR:1:1}
fi
echo "Cleared status: $VCLR @ $HOUR hours"

function freeUSB {

	MNT_DRV=$(gio mount -l | grep gphoto2 | awk -F"> " '{print $2}' | head -1)
	if [[ $MNT_DRV ]] ; then
    	# umount the camera to use the usb connection        
    	gio mount -u $MNT_DRV
	fi
    pkill gvfsd-gphoto2
}

function checkDir {

	# Create the output directory if necessary
	if [[ ! -d $1 ]] ; then
    	mkdir $1
	fi
}

function shotSingle {
	#ISO_SPD = $1; SHT_SPD=$2; APERTURE=$3

    if [[ $MN_PARS == 1 ]] ; then
        ISO_SPD=$1
        SHT_SPD=$2
        APRTURE=$3
    else
    	raspistill -o /home/pi/bin/.tmp/meas.jpg
        exiftool /home/pi/bin/.tmp/meas.jpg > exinfo
        ISO_SPD=$($SCR_DIR/cam_LUT.sh iso $(grep ISO exinfo | awk -F":" '{print $2}'))
        SHT_SPD=$($SCR_DIR/cam_LUT.sh shutter $(grep "Shutter Speed Value" exinfo | awk -F":" '{print $2}'))
        rm exinfo
        APRTURE=$3
    fi

	gphoto2 \
    	--set-config iso=$ISO_SPD  \
		--set-config capturetarget=1	\
    	--set-config shutterspeed=$SHT_SPD    \
		--set-config aperture=$APRTURE		\
		--set-config eosremoterelease="Immediate" \
		--set-config eosremoterelease="Release Full" \
		--wait-event-and-download=ObjectRemoved	\
		--force-overwrite | grep JPG | awk '{print $5}'
}

function shotBurst {
  echo "$(date +%s)" > $STAT
  ISO_SPD=$1
  SHT_SPD=$2
  APRTURE=$3
  gphoto2 \
    --set-config iso=$ISO_SPD  \
		--set-config capturetarget=1	\
    --set-config shutterspeed=$SHT_SPD    \
		--set-config aperture=$APRTURE		\
    --set-config drivemode="Continuous" \
		--set-config eosremoterelease="Immediate" \
   --wait-event=3s
		--set-config eosremoterelease="Release Full" \
		--wait-event-and-download=ObjectRemoved	\
		--force-overwrite | grep JPG | awk '{print $5}'
  echo "0" > $STAT
} 

function shotBulb {
    echo "$(date +%s)" > $STAT
    gphoto2 \
	--set-config capturetarget=1	\
	--set-config iso=3200	\
	--set-config aperture=32	\
	--set-config shutterspeed=bulb	\
	--set-config eosremoterelease="Immediate" \
	--wait-event=${1}s	\
	--set-config eosremoterelease="Release Full" \
	--wait-event-and-download=ObjectRemoved	\
	--force-overwrite | grep JPG | awk '{print $5}'
    echo "0" > $STAT
}

# Capture a picture if the volcano is unclouded during daylight hours
if (( $(cat $STAT) && $(echo "($(date +%s) - $(cat $STAT)) > 610" | bc) )) ; then
		echo "($(date +%s) - $(cat $STAT)) > 610" | bc
		echo "It seems like capture script is taking too long"
    	echo "0" > $STAT
        pkill captureVisible
fi

if (( $VCLR && !$(tail -1 $STAT)))  ; then
    	
		freeUSB
		TM_STMP=$(date +%Y%m%d_%H%M%S)
		OUT_DIR="/data/lxp_visible/"$(date +%Y.%m.%d)
    	LOG_DIR="/data/logs/vis_recognition/"
		checkDir $OUT_DIR
    	checkDir $LOG_DIR
    	# Synchronize the clock (system -> camera)
    	gphoto2 --set-config syncdatetime=1
    	if [[ $ST_MODE == "Burst" ]]  ; then
      		IMG=$(shotBurst $ISO_SPD $SHT_SPD $APRTURE)
		elif (( HOUR >= 11 )) && (( HOUR < 23 )) ; then
			## This takes the picture without performing the previous autofocus
			IMG=$(shotSingle $ISO_SPD $SHT_SPD $APRTURE)
		elif (( HOUR < 11 )) || (( HOUR == 23 )) ; then
    		## Take a long-exposure picture
    		IMG=$(shotBulb $OP_TIME)
    	fi
    
    	python $SCR_DIR/visIdentify.py $IMG
		mv $IMG $OUT_DIR/VIGIA_LX_$TM_STMP.jpg
    	echo "Captured image VIGIA_LX_$TM_STMP.jpg"

fi