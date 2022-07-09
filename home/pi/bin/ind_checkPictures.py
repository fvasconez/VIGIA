import sys
import numpy as np
import cv2 as cv
import matplotlib.pyplot as plt
import time

# Convert the thermal .npz image into a PNG picture
# @author fvasconez
# @created 2021.08.20
# @modified 2021.11.10

# Use: python ind_checkPictures.py <thermal_image.npz> <destiny_dir>
# The name of the output picture is always VIGIA_IR_0.png

tstamp_factor = 10000000
#defining the zone of interest (crater zone)
font = cv.FONT_HERSHEY_SIMPLEX
f_size = 0.4
f_col=(255,25,25)
b_col=(130,130,130)
f_line = cv.LINE_AA
colormap = cv.COLORMAP_INFERNO
colorRange = 5
dest_dir = '/home/pi/Pictures/Thermal/'

def get_timestamp(record):
    return(time.strftime("%Y.%m.%d_%H:%M:%S",record))

# Calculate the limits of the colormap to generate the image
# we are using a S-sigma method
def color_scale(image,S):
    im_mean = image.mean()
    im_stdv = image.std()
    im_max = np.min([image.max(),im_mean+S*im_stdv])
    im_min = np.max([image.min(),im_mean-S*im_stdv])
    return(int(im_min),int(im_max))

# Generate the colorbar
def gen_colorbar():
    scale = np.ones((12,256),int)
    scale[:,:]=255-np.linspace(0,255,256)
    return(scale.transpose())

def formatTempTxt(temp):
    if 0 <= temp < 10 :
        return("  "+str(temp))
    if 10 <= temp < 100:
        return(" "+str(temp))
    else:
        return(str(temp))

plt.figure()
file_name = ''
if len(sys.argv) > 1:
        file_name= sys.argv[1]
        dest_dir = sys.argv[2]

imfile = np.load(file_name)
image = imfile['thermaldata'].reshape(480,640)
metad = imfile['metadata']
time_rec = time.gmtime(metad['timestamp']/tstamp_factor)

# find the limits for the color scale of the image
# extreme values of the data
dt_min,dt_max,lc_min,lc_max = cv.minMaxLoc(image)
dt_min = np.around(dt_min/10-100,1)
dt_max = np.around(dt_max/10-100,1)
# limits for the color scale
im_min,im_max = color_scale(image,colorRange)
clip_im = np.clip(image,im_min,im_max)-im_min

frame = (255*(clip_im/(im_max-im_min))).astype(np.uint8)

# change the "format" of the image from 16-bit to 8-bit pixel
# so we can use OpenCV tools with the image

frame = cv.rotate(frame, cv.ROTATE_90_COUNTERCLOCKWISE)

im_min = np.round(im_min/10 - 100,1)
im_max = np.round(im_max/10 - 100,1)

frame[344:600,12:24] = gen_colorbar()

colored = cv.applyColorMap(frame, colormap)
colored[0:56,0:200] = (128+colored[0:56,0:200]/2).astype(np.uint8)
cv.putText(colored,'VIGIA Volcan Reventador',(4,14),font,f_size,f_col,1,f_line)
cv.putText(colored,get_timestamp(time_rec)+' [UTC]',(4,32),font,f_size,f_col,1,f_line)
cv.putText(colored,'LMV_UCA/OPGC/IGEPN',(4,50),font,f_size,f_col,1,f_line)

cv.rectangle(colored, (11,343),(24,600),b_col,1)
colored[325:340,8:42] = (128+colored[325:340,8:42]/2).astype(np.uint8)
colored[605:620,8:42] = (128+colored[605:620,8:42]/2).astype(np.uint8)
cv.putText(colored,str(im_max),(10,336),font,f_size,f_col,1,f_line)
cv.putText(colored,str(im_min),(10,616),font,f_size,f_col,1,f_line)
# Write max and min Temp info in the frame
colored[620:640,8:194] = (128+colored[620:640,8:194]/2).astype(np.uint8)
cv.putText(colored,"Raw Temp.: [     ,      ]",(10,633),font,f_size,f_col,1,f_line)
cv.putText(colored,formatTempTxt(dt_min),(90,633),font,f_size,f_col,1,f_line)
cv.putText(colored,formatTempTxt(dt_max),(132,633),font,f_size,f_col,1,f_line)
cv.putText(colored,"o",(178,629),font,f_size-0.1,f_col,1,f_line)
cv.putText(colored,"C",(184,633),font,f_size,f_col,1,f_line)

frame = cv.cvtColor(colored,cv.COLOR_BGR2RGB)
#plt.imshow(frame)
plt.imsave(dest_dir+'/VIGIA_IR_0.png',frame)
#plt.show()