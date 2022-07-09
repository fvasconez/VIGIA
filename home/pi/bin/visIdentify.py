import sys
import numpy as np
import cv2 as cv
from exif import Image
import time

# @author fvasconez
# @created 2022.06.17
# 
# This script is intended to recognize the volcano using visible pictures captured by VIGIA
#

BORD_UPPLIM = 45
BORD_DWNLIM = 8
THRESHOLD = 0.18

IMG_W = 640
IMG_H = 480

match_method = cv.TM_CCORR_NORMED
templt_img = '/home/pi/config/volcanoTemplate.npz'
#mask_img = 'WeightMaskCrater.npy'

log_file = "/data/logs/vis_recognition/visRec_"
stt_file = '/home/pi/.status'

def main(args):
    #logs = open(log_file,'a')
    stat = open(stt_file,'w')
    # generate an image from the contour of the template
    templ_read = np.load(templt_img)
    bw_tmp = np.zeros((templ_read['height'],templ_read['width']),np.uint8)
    cv.drawContours(bw_tmp,templ_read['contour'],-1,(255,255,255))
    
    ## [load_image]
    file_name = args[0]
    
    #if file_name.split(".")[-1] == "JPG":
    # read and scale the input image to 640*480 pixels
    pict = cv.resize(cv.imread(file_name), dsize=(IMG_W,IMG_H))
    picture = cv.equalizeHist(cv.cvtColor(pict,cv.COLOR_BGR2GRAY))
    cont = getContours(pict)
    result = cv.matchTemplate(cont, bw_tmp, match_method)
    _minVal, _maxVal, minLoc, maxLoc = cv.minMaxLoc(result, None)
    # evaluate the result
    if (match_method == cv.TM_SQDIFF or match_method == cv.TM_SQDIFF_NORMED):
        matchLoc = minLoc
        matchVal = _minVal
        condition = _minVal < THRESHOLD
    else:
        matchLoc = maxLoc
        matchVal = _maxVal
        condition = _maxVal > THRESHOLD
    logs = open(log_file+getLogName(file_name),'a')
    quality = getQuality(picture,matchLoc,templ_read['width'],templ_read['height'])
    if condition :
        print("["+getTimestamp(file_name)+"]:",np.around(matchVal,2),quality,"Cleared")
        logs.write(f'[{getTimestamp(file_name)}]: {np.around(matchVal,2)}\t {quality:.2f}\t {matchLoc}\tCleared\n')
        stat.write("1\n")
    else:
        print("["+getTimestamp(file_name)+"]:",np.around(_maxVal,2),quality,"Clouded")
        logs.write(f'[{getTimestamp(file_name)}]: {np.around(matchVal,2)}\t {quality:.2f}\t {matchLoc}\tClouded\n')
        stat.write("0\n")
    ## [match_loc]
    stat.close()
    print("Result:",matchVal)
    '''# draw a rectangle locating the template
    cv.rectangle(picture,matchLoc,(matchLoc[0]+templ_read['width'],matchLoc[1]+templ_read['height']),(255,255,255),1,1)
    cv.imshow("Rev",picture)
    cv.waitKey(0)
	'''

def getContours(image):
    bw_img = np.zeros(image.shape[:2],np.uint8)
    borders = cv.Canny(image,BORD_DWNLIM,BORD_UPPLIM)
    contours,hist = cv.findContours(borders,mode=cv.RETR_CCOMP,method=cv.CHAIN_APPROX_NONE,offset=(0,0))
    cv.drawContours(bw_img,contours,-1,(255,255,255))
    return(bw_img)

def getQuality(img,matchLoc,w,h):
    # get the region size and position
    over_w = int(3*w/4)
    over_h = 3*h
    l_lim = matchLoc[0]+int(w/8)
    v_lim = matchLoc[1]+int(3*h/4)
    region = img[v_lim-over_h:v_lim,l_lim:l_lim+over_w]

    min_t,max_t,mlx,mly = cv.minMaxLoc(region)
    over_contours = getContours(region)
    quality = (max_t-min_t)*(np.count_nonzero(over_contours)/(over_w*over_h))
    cv.rectangle(img,(l_lim,v_lim-over_h),(l_lim+over_w,v_lim),(255,255,255),1,1)
    # Show the result
    #cv.imshow("Rev",img)
    #cv.waitKey(0)
    return(np.around(quality,2))

def getTimestamp(img_file):
    with open(img_file,'rb') as image:
          mtdata = Image(image)
    aux = mtdata.get("datetime_original").replace(":","").replace(" ","T")
    return(aux)
    
def getLogName(img_file):
    with open(img_file,'rb') as image:
          mtdata = Image(image)
    aux = mtdata.get("datetime_original").replace(":","")
    return(aux.split(" ")[0]+".log")
        
if __name__ == "__main__":
    main(sys.argv[1:])