import sys
import glob
import numpy as np
import cv2 as cv
import time

#
# @author fvasconez
# @created 2021.08
# @modified 2021.11.12
# @modified 2021.12.17
#
# Open a thermal image (.npz file) find the contours
# and locate the crater from the contours of the template
# Use a mask to enphasize the borders of the flanks over the rim of the top
# Also defines the "quality" of the image based on what's over the top of the crater
# TO DO: change the definition of quality based on the plume and posible (pyroclastic) flows
#
# Set the THRESHOLD in 0.18. This value depends on the method for template matching and the quantity of borders
# 2021.12.17: THRESHOLD to 0.20. Subtly denoizing the image before all the process. Include Tmax-Tmin for the quality calculation

TEST = False
## [global_variables]
use_mask = False
img = None
templ = None
mask = None
imgmet = None
logs = None
stat = None
dt_constant = 10000000
image_window = "Source Image"
template_window = "Contours detected"
THRESHOLD = 0.18
BORD_UPPLIM = 45
BORD_DWNLIM = 8

match_method = cv.TM_CCORR_NORMED
templt_img = '/home/pi/.Templates/Crater_1.npy'
mask_img = '/home/pi/.Templates/WeightMaskCrater.npy'
log_file = '/data/logs/recognizing/volcRec_'+time.strftime("%Y%m%d")+'.log'
stt_file = '/home/pi/.status'
if TEST:
    templt_img = 'Crater_1.npy'
    mask_img = 'WeightMaskCrater.npy'
    log_file = 'testLog.log'

## [global_variables]

def main(args):
    file_name = args[0]
    ## [load_image]
    global img
    global templ
    global mask
    global imgmet
    global logs
    global stat
    logs = open(log_file,'a')
    stat = open(stt_file,'w')

    img_file = np.load(file_name)
    imgdat = img_file['thermaldata'].reshape(480,640)
    imgmet = img_file['metadata']['timestamp']
    img = imgdat
        
    templ = np.load(templt_img)
    templ = scale(templ)
    mask = np.load(mask_img)
        
    if ((img is None) or (templ is None) or (mask is None)):
        print('Can\'t read one of the images')
        logs.write('Can\'t read one of the images')
        return -1
    ## [load_image]

    MatchingMethod(match_method)
    return 0
    
def getQuality(matchLoc):
    # get the region size and position
    over_w = int(templ.shape[0]/2)
    over_h = 2*templ.shape[1]
    l_lim=matchLoc[1]+int(templ.shape[0]/4)
    v_lim=matchLoc[0]+int(templ.shape[1]/2)
    region = img[l_lim:l_lim+over_w,v_lim:v_lim+over_h]
    min_t,max_t,mlx,mly = cv.minMaxLoc(region)
    over_contours = getContours(scale(region))
    quality = (max_t-min_t)*(np.count_nonzero(over_contours)/(over_w*over_h))
    return(np.around(quality,2))
  
def scale(image):
    # As we are interested in finding the upper part of the edifice, we are scaling the image to the 
    # temperature typical of that part. Then, we clip the lower temperatures to 4°C and
    # the higher temperature to 4+25.5°C (29.5°C)
    mn = 1040
    image = image - mn
    return(np.clip(image,0,255).astype(np.uint8))

def getContours(image):
    global BOR_UPPLIM, BORD_DWNLIM
    bw_img = np.zeros(image.shape,np.uint8)
    borders = cv.Canny(image,BORD_DWNLIM,BORD_UPPLIM)
    contours,hist = cv.findContours(borders,mode=cv.RETR_CCOMP,method=cv.CHAIN_APPROX_NONE,offset=(0,0))
    return(cv.drawContours(bw_img,contours,-1,(255,255,255)))

def getTimestamp(meta):
    return(time.strftime("%Y%m%dT%H%M%S",time.gmtime(meta/dt_constant)))

def MatchingMethod(method):
    global THRESHOLD
    ## [copy_source]
    img_denoizd = cv.fastNlMeansDenoising(scale(img),0.4,3,5)
    img_display = getContours(img_denoizd)
    templ_c = getContours(templ)
    ## [match_template]
    result = cv.matchTemplate(img_display, templ_c, method, mask)
    ## [match_template]
    ## [best_match]
    _minVal, _maxVal, minLoc, maxLoc = cv.minMaxLoc(result, None)
    ## [best_match]
    ## [match_loc]
    if (method == cv.TM_SQDIFF or method == cv.TM_SQDIFF_NORMED):
        matchLoc = minLoc
        print("Val:",_minVal)
    else:
        matchLoc = maxLoc
        quality = getQuality(matchLoc)
        if _maxVal > THRESHOLD :
            print("["+getTimestamp(imgmet)+"]:",np.around(_maxVal,2),quality,"Cleared")
            logs.write(f'[{getTimestamp(imgmet)}]: {np.around(_maxVal,2)}\t {quality:.2f}\t {matchLoc}\tCleared\n')
            stat.write("1\n")
        else:
            print("["+getTimestamp(imgmet)+"]:",np.around(_maxVal,2),quality,"Clouded")
            logs.write(f'[{getTimestamp(imgmet)}]: {np.around(_maxVal,2)}\t {quality:.2f}\t {matchLoc}\tClouded\n')
            stat.write("0\n")
    ## [match_loc]
    stat.close()
    pass

if __name__ == "__main__":
    main(sys.argv[1:])