#!/usr/bin/python
#title   :buffCam.py
#description :recording video from raspberry camera in a circular buffer
#and if gpio 16 is high logical level then save the video with a posttrigger
#author :T.Latchimy CNRS/OPGC/SDT/UCA
#date :2018-08-27
#update         :020-03-27
#version :1.1.dev
#usage :python buffCam2.py
#notes   :
#python_version :2.7.13
#=======================================================================
import sys
import os
from time import strftime
import io
import picamera
from picamera import Color
import RPi.GPIO as gpio
import time
import datetime
#from pushbullet import Pushbullet as push

#####smartphone notification configuration###########
token='o.ovDkznzBYlufa5UhAf9W74SlIZplEpgj'
device='Samsung SM-G531F'
#pb=push(token)
#dev =pb.get_device(device)

#######GPIO input configuration to detect event######

gpio.setmode(gpio.BCM)
gpio.setup(16,gpio.IN,gpio.PUD_DOWN)

######################################################

eventFile="event.log"
eventFilePath="/home/pi/Videos/"+eventFile
########videos parameters#############################
#time before saving in second
timePost=10
#resolution of the video
width=960
heigth=720
#wait recording when event
timeRec=60
#bitrate
cam_rate=1000000
#rotation of the camera (0-359),it depends of the mechanical mount of
#the camera
rotation=0
#framerate for video compression (image/seconde)
frame='30'
flagBuffer=False
pathBufferFile='/home/pi/.buffer.save'
pathLocalData= '/home/pi/Videos/'
pathFinalData= '/data/vsvid/'
#path for external webserver
pathDest="/home/pi/"

def main():
  	## Writing video function
	def write_video(stream):
		print('Writing video!')

		pathFile="/home/pi/Visual/video_detect/"
		#pathDest="/var/www/php/"
		with io.open(pathLocalData+'before.h264','wb')as output:
		# find the first header frame in video
			for frame in stream.frames:
				if frame.header:
					stream.seek(frame.position)
					break
			while True:
				buf=stream.read1()
				if not buf:
					break
				output.write(buf)
			stream.seek(0)
			stream.truncate()
	## END of function
    
	camera = picamera.PiCamera()
	camera.framerate=int(frame)
	camera.rotation=rotation
	camera.resolution=(width,heigth)
	stream = picamera.PiCameraCircularIO(camera,seconds=timePost,bitrate=cam_rate)
	camera.start_recording(stream,format='h264',bitrate=cam_rate)
	start=time.time()
	while True:
		elapsed=int(time.time()-start)
		sys.stdout.write("Elapsed time:"+str(elapsed)+" sec\r")
		sys.stdout.flush()

		camera.wait_recording(1)
		exists = os.path.isfile(pathBufferFile)
		if exists:
			flagBuffer=True
		else:
			flagBuffer=False

		if ((gpio.input(16)) or (flagBuffer)):
			dt=datetime.datetime.now()
			strDt=dt.strftime("%Y-%m-%d %H:%M:%S")
			msg="Camera recording : "+strDt
		#	dev.push_note("!!Alert !!",msg)

			if flagBuffer==True:
				flagBuffer=False
				os.system("sudo rm "+pathDest+".buffer.save")
					
			if os.path.isfile(pathLocalData+"webcam.avi"):
				os.system("sudo rm "+pathLocalData+"webcam.avi")
				
			curDate=strftime("%Y%m%d_%H%M%S")
			aDate=curDate
			finalPath = pathFinalData+time.strftime("%Y.%m.%d")
			if not os.path.isdir(finalPath):
				os.system("sudo mkdir "+finalPath)
			fileName1="VIGIA_VSVID_"+curDate+".h264"
			fileName=finalPath+"/VIGIA_VSVID_"+curDate+".h264"
			camera.split_recording(pathLocalData+'after.h264')
			write_video(stream)

			camera.capture(pathLocalData+"img"+curDate+".jpg",use_video_port=True)
			camera.wait_recording(timeRec) 
			camera.split_recording(stream)
			cmdCat="sudo MP4Box -fps "+frame+" -add "+pathLocalData+"before.h264 -cat "+pathLocalData+"after.h264 "+fileName
			print(cmdCat)
			os.system(cmdCat)
			with open(eventFilePath,"a+") as logfile:
				logfile.write(curDate+"\n")
			os.system("sudo rm "+pathLocalData+"before.h264")
			os.system("sudo rm "+pathLocalData+"after.h264")

			cmd2="sudo MP4Box -fps "+frame+" -add "+fileName+"	"+pathLocalData+"webcam.avi"
			print(cmd2)
			os.system(cmd2)
			#send image file on server
			#send video .h264 in server directory in our case /home/pi/video_reventa
			#send video .avi and event logfile on the webserver at /var/www/html/
			# using putFtp.sh script
			cmdFtp2= "/home/pi/putFtp.sh reventa "+fileName1 + "img"+curDate+".jpg "+" webcam.avi"+" " +eventFile
			print(cmdFtp2)
		#	os.system(cmdFtp2)
			camera.stop_recording()
			stream = picamera.PiCameraCircularIO(camera,seconds=timePost,bitrate=cam_rate)
   
			camera.start_recording(stream,format='h264',bitrate=cam_rate)


if __name__ == '__main__':
	main()
