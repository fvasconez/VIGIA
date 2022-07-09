#! /usr/bin/env python3
from ctypes.util import find_library
import numpy as np
import ctypes as ct
import os
import time

# Get one thermal image each @period minutes.
# The format of the image is as a python-dictionary object (.pnz)
# which has 'metadata' and 'thermaldata' as fields

# @created 2021.08.18
# @author fvasconez

# General directory to place data
DATA_DIR_G = '/data/thm_timelapse/'
# Organizing data by date
DATA_DIR = DATA_DIR_G + time.strftime("%Y.%m.%d/")

# Create the directory in case it does not exists
if not os.path.isdir(DATA_DIR): os.mkdir(DATA_DIR)

# Constant to transform timestamps from Optris software
tstamp_factor = 10000000


#Define EvoIRFrameMetadata structure for additional frame infos
class EvoIRFrameMetadata(ct.Structure):
     _fields_ = [("counter", ct.c_uint),
                 ("counterHW", ct.c_uint),
                 ("timestamp", ct.c_longlong),
                 ("timestampMedia", ct.c_longlong),
                 ("flagState", ct.c_int),
                 ("tempChip", ct.c_float),
                 ("tempFlag", ct.c_float),
                 ("tempBox", ct.c_float),
                 ]
        
def old_filestamp(record):
    x_mon=''
    x_day=''
    x_hour=''
    x_min=''
    x_sec=''
    if record.tm_mon < 10 : x_mon='0'
    if record.tm_mday < 10 : x_day='0'
    if record.tm_hour < 10 : x_hour='0'
    if record.tm_min < 10 : x_min='0'
    if record.tm_sec < 10 : x_sec='0'
    
    time_annotation = str(record.tm_year)+ x_mon + str(record.tm_mon)+ x_day + str(record.tm_mday)+'_'+ x_hour + str(record.tm_hour)+ x_min + str(record.tm_min)+ x_sec + str(record.tm_sec)
    return(time_annotation)

def get_filestamp(record):
    return(time.strftime("%Y%m%d_%H%M%S",record))

if __name__ == "__main__":
        # load library
        if os.name == 'nt':
                #windows:
                libir = ct.CDLL("c:\\irDirectSDK\\sdk\\x64\\libirimager.dll") 
        else:
                #linux:
                libir = ct.cdll.LoadLibrary(ct.util.find_library("irdirectsdk"))

        #path to config xml file
        pathXml = ct.c_char_p(b'../config/generic.xml')

        # init vars
        pathFormat = ct.c_char_p()
        pathLog = ct.c_char_p(b'.tmp/th2min_TL')

        palette_width = ct.c_int()
        palette_height = ct.c_int()

        thermal_width = ct.c_int()
        thermal_height = ct.c_int()

        # init EvoIRFrameMetadata structure
        metadata = EvoIRFrameMetadata()
		# Free the camera if it was trapped by other hang process
        ret = libir.evo_irimager_terminate()
        
        # init lib
        ret = libir.evo_irimager_usb_init(pathXml, pathFormat, pathLog)
        if ret != 0:
                print("error at init")
                exit(ret)

        FLAG_OPEN = False
        
        # get thermal image size
        libir.evo_irimager_get_thermal_image_size(ct.byref(thermal_width), ct.byref(thermal_height))

        # init thermal data container
        np_thermal = np.zeros([thermal_width.value * thermal_height.value], dtype=np.uint16)
        npThermalPointer = np_thermal.ctypes.data_as(ct.POINTER(ct.c_ushort))

        # get palette image size, width is different to thermal image width duo to stride alignment!!!
        libir.evo_irimager_get_palette_image_size(ct.byref(palette_width), ct.byref(palette_height))

        # init image container
        np_img = np.zeros([palette_width.value * palette_height.value * 3], dtype=np.uint8)
        npImagePointer = np_img.ctypes.data_as(ct.POINTER(ct.c_ubyte))

        count = 0
        libir.evo_irimager_trigger_shutter_flag()
        # capture and display image till q is pressed
        while count < 128:
                ret = libir.evo_irimager_get_thermal_palette_image_metadata(thermal_width, thermal_height, npThermalPointer, palette_width, palette_height, npImagePointer, ct.byref(metadata))

                if ret != 0:
                        print('error on evo_irimager_get_thermal_palette_image ' + str(ret))
                        continue
                
                FLAG_OPEN = (metadata.flagState == 3)
                if FLAG_OPEN:
                        tstamp = get_filestamp(time.gmtime(metadata.timestamp/tstamp_factor))
                        np.savez(DATA_DIR+'VIGIA_IR_'+tstamp+'.npz', metadata=metadata,thermaldata=np_thermal)
                        print('VIGIA_IR_'+tstamp+'.npz')
                        break

                count += 1


        # clean shutdown
        libir.evo_irimager_terminate()