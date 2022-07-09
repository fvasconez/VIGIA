#!/usr/bin/python
#--------------------------------------
#    ___  ___  _ ____
#   / _ \/ _ \(_) __/__  __ __
#  / , _/ ___/ /\ \/ _ \/ // /
# /_/|_/_/  /_/___/ .__/\_, /
#                /_/   /___/
#
#           bme280.py
#  Read data from a digital pressure sensor.
#
#  Official datasheet available from :
#  https://www.bosch-sensortec.com/bst/products/all_products/bme280
#
# Author : Matt Hawkins
# Date   : 21/01/2018
#
# https://www.raspberrypi-spy.co.uk/
#
# @modified 15/11/2020 by fvasconez (freddy.vasconez@uca.fr)
# 
#--------------------------------------
import smbus
import time
import os
from ctypes import c_short
from ctypes import c_byte
from ctypes import c_ubyte

DEVICE = 0x76 # Default device I2C address
dig_T = [0, 0, 0]
dig_P = [0, 0, 0, 0, 0, 0, 0, 0, 0]
dig_H = [0, 0, 0, 0, 0, 0]

bus = smbus.SMBus(1) # Rev 2 Pi, Pi 2 & Pi 3 uses bus 1
                     # Rev 1 Pi uses bus 0

DataDir = "/data/envTPH/"
  
def getShort(data, index):
  # return two bytes from data as a signed 16-bit value
  return c_short((data[index+1] << 8) + data[index]).value

def getUShort(data, index):
  # return two bytes from data as an unsigned 16-bit value
  return (data[index+1] << 8) + data[index]

def getChar(data,index):
  # return one byte from data as a signed char
  result = data[index]
  if result > 127:
    result -= 256
  return result

def getUChar(data,index):
  # return one byte from data as an unsigned char
  result =  data[index] & 0xFF
  return result

def readBME280ID(addr=DEVICE):
  # Chip ID Register Address
  REG_ID     = 0xD0
  (chip_id, chip_version) = bus.read_i2c_block_data(addr, REG_ID, 2)
  return (chip_id, chip_version)
	
def confBME280(addr=DEVICE):
	# Register Addresses
  REG_DATA = 0xF7
  REG_CONTROL = 0xF4
  REG_CONFIG  = 0xF5

  REG_CONTROL_HUM = 0xF2
  REG_HUM_MSB = 0xFD
  REG_HUM_LSB = 0xFE

  # Oversample setting - page 27
  OVERSAMPLE_TEMP = 2
  OVERSAMPLE_PRES = 2
  MODE = 3

	# Turn off the filter
  bus.write_byte_data(addr, REG_CONFIG, 0)
	
  # Oversample setting for humidity register - page 26
  OVERSAMPLE_HUM = 2
  bus.write_byte_data(addr, REG_CONTROL_HUM, OVERSAMPLE_HUM)

  control = OVERSAMPLE_TEMP<<5 | OVERSAMPLE_PRES<<2 | MODE
  bus.write_byte_data(addr, REG_CONTROL, control)

  # Read blocks of calibration data from EEPROM
  # See Page 22 data sheet
  cal1 = bus.read_i2c_block_data(addr, 0x88, 24)
  cal2 = bus.read_i2c_block_data(addr, 0xA1, 1)
  cal3 = bus.read_i2c_block_data(addr, 0xE1, 7)

  # Convert byte data to word values
	
  dig_T1 = getUShort(cal1, 0)
  dig_T2 = getShort(cal1, 2)
  dig_T3 = getShort(cal1, 4)
  global dig_T 
  dig_T = [dig_T1, dig_T2, dig_T3]

  dig_P1 = getUShort(cal1, 6)
  dig_P2 = getShort(cal1, 8)
  dig_P3 = getShort(cal1, 10)
  dig_P4 = getShort(cal1, 12)
  dig_P5 = getShort(cal1, 14)
  dig_P6 = getShort(cal1, 16)
  dig_P7 = getShort(cal1, 18)
  dig_P8 = getShort(cal1, 20)
  dig_P9 = getShort(cal1, 22)
  global dig_P 
  dig_P = [dig_P1, dig_P2, dig_P3, dig_P4, dig_P5, dig_P6, dig_P7, dig_P8, dig_P9]

  dig_H1 = getUChar(cal2, 0)
  dig_H2 = getShort(cal3, 0)
  dig_H3 = getUChar(cal3, 2)

  dig_H4 = getChar(cal3, 3)
  dig_H4 = (dig_H4 << 24) >> 20
  dig_H4 = dig_H4 | (getChar(cal3, 4) & 0x0F)

  dig_H5 = getChar(cal3, 5)
  dig_H5 = (dig_H5 << 24) >> 20
  dig_H5 = dig_H5 | (getUChar(cal3, 4) >> 4 & 0x0F)

  dig_H6 = getChar(cal3, 6)

  global dig_H 
  dig_H = [dig_H1, dig_H2, dig_H3, dig_H4, dig_H5, dig_H6]

	
def readBME280All(addr=DEVICE):
	# Register Addresses
  REG_DATA = 0xF7
  OVERSAMPLE_TEMP = 2
  OVERSAMPLE_PRES = 2
  OVERSAMPLE_HUM =2
	
  global dig_T, dig_P, dig_H
	
  # Wait in ms (Datasheet Appendix B: Measurement time and current calculation)
  wait_time = 1.25 + (2.3 * OVERSAMPLE_TEMP) + ((2.3 * OVERSAMPLE_PRES) + 0.575) + ((2.3 * OVERSAMPLE_HUM)+0.575)
  time.sleep(wait_time/1000)  # Wait the required time  

  # Read temperature/pressure/humidity
  data = bus.read_i2c_block_data(addr, REG_DATA, 8)
  pres_raw = (data[0] << 12) | (data[1] << 4) | (data[2] >> 4)
  temp_raw = (data[3] << 12) | (data[4] << 4) | (data[5] >> 4)
  hum_raw = (data[6] << 8) | data[7]

  #Refine temperature
  var1 = ((((temp_raw>>3)-(dig_T[0]<<1)))*(dig_T[1])) >> 11
  var2 = (((((temp_raw>>4) - (dig_T[0])) * ((temp_raw>>4) - (dig_T[0]))) >> 12) * (dig_T[2])) >> 14
  t_fine = var1+var2
  temperature = float(((t_fine * 5) + 128) >> 8);

  # Refine pressure and adjust for temperature
  var1 = t_fine / 2.0 - 64000.0
  var2 = var1 * var1 * dig_P[5] / 32768.0
  var2 = var2 + var1 * dig_P[4] * 2.0
  var2 = var2 / 4.0 + dig_P[3] * 65536.0
  var1 = (dig_P[2] * var1 * var1 / 524288.0 + dig_P[1] * var1) / 524288.0
  var1 = (1.0 + var1 / 32768.0) * dig_P[0]
  if var1 == 0:
    pressure=0
  else:
    pressure = 1048576.0 - pres_raw
    pressure = ((pressure - var2 / 4096.0) * 6250.0) / var1
    var1 = dig_P[8] * pressure * pressure / 2147483648.0
    var2 = pressure * dig_P[7] / 32768.0
    pressure = pressure + (var1 + var2 + dig_P[6]) / 16.0

  # Refine humidity
  humidity = t_fine - 76800.0
  humidity = (hum_raw - (dig_H[3] * 64.0 + dig_H[4] / 16384.0 * humidity)) * (dig_H[1] / 65536.0 * (1.0 + dig_H[5] / 67108864.0 * humidity * (1.0 + dig_H[2] / 67108864.0 * humidity)))
  humidity = humidity * (1.0 - dig_H[0] * humidity / 524288.0)
  if humidity > 100:
    humidity = 100
  elif humidity < 0:
    humidity = 0

  return temperature/100.0,pressure/100.0,humidity

def main():

  (chip_id, chip_version) = readBME280ID()
  print("Chip ID     :", chip_id)
  print("Version     :", chip_version)
  confBME280()
  tmts = time.gmtime()
  dirName = time.strftime("%Y.%m.%d")
  if not os.path.exists(DataDir+dirName):
    os.makedirs(DataDir+dirName)
  actSec = tmts.tm_sec
  actHour = tmts.tm_hour
  outPath = DataDir+dirName

  outFile = open(outPath+time.strftime("/%Y%m%d_%H.txt"),'w')
  outFile.write("//Minute Second Temperature [degC], Pressure [hPa], Rel. Hum [%]\n")
  fraction = 0
  while True:
    
    temperature,pressure,humidity = readBME280All()
    tmst = time.gmtime()
    curHour = tmst.tm_hour
    curSec = tmst.tm_sec
    if curSec != actSec :
      fraction = 0
      actSec = curSec

    if curHour != actHour : break

    outStr = time.strftime("%M %S.")+str(fraction)+" "+str(temperature)+" "+str(pressure)+" "+str(humidity)+"\n"
    outFile.write(outStr)
   # print "Pressure : ", pressure, "hPa"
   # print "Humidity : ", humidity, "%"
    fraction = fraction +1
    time.sleep(0.002)
  outFile.close()
			
if __name__=="__main__":
   main()