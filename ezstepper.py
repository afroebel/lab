# -*- coding: utf-8 -*-
"""
Created on Sun Nov  7 10:21:11 2021

@author: THz-FCS
"""

import serial
import pyvisa as visa              #Had to import from pyvisa to get it to work in new workstation
import time
from datetime import datetime

#ser1 is master stepper
ser1 = serial.Serial(
    'COM6', 9600, 
    timeout = 3,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    bytesize=serial.EIGHTBITS)

#ser2 is probe stepper
ser2 = serial.Serial(
    'COM7', 9600, 
    timeout = 3,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    bytesize=serial.EIGHTBITS)

#frequency counter
rm = visa.ResourceManager()
rm.list_resources()
inst = rm.open_resource('GPIB0::3::INSTR')

#SIM900
ser = serial.Serial('COM4', 9600, timeout = 3)
time.sleep(0.001)

def getrepratePU():
    inst.write("FU1")
    with inst.visalib.ignore_warning(inst.session, visa.constants.VI_SUCCESS_MAX_CNT):  #This took a while to figure out... 
        masterdata = inst.visalib.read(inst.session,17)
    a = str(masterdata[0])
    x = a.find("F")
    masterfreq = float(a[x+4:x+14])*10**7
    # print(masterfreq)
    return masterfreq

def getrepratePR():
    inst.write("FU3")
    with inst.visalib.ignore_warning(inst.session, visa.constants.VI_SUCCESS_MAX_CNT):  #This took a while to figure out... 
        masterdata = inst.visalib.read(inst.session,17)
    a = str(masterdata[0])
    x = a.find("F")
    masterfreq = float(a[x+4:x+14])*10**7
    # print(masterfreq)
    return masterfreq

#might cause problems trying to run reprate monitor at the same time
#try to make sure SIM900 0 V corresponds to max power. 
#pump plusminus 2V is about 1000 Hz in each direction, P/D50000 about +-800 Hz
#probe plusminuse 2V is about 1500 Hz in each direction 
#pump min stepper movement decided 150 Hz

def steptotargetPU(targetPU):    
    Hzperstep = 795/50000    #tuned
    repratern = getrepratePU()
    print(repratern)
    diff = targetPU - repratern
    if abs(diff) < 150:  #arbitrary, small movements too inconsistent
        print('diff < 150, skip to PZT control')
    elif abs(diff) > 25000:   #arbitrary
        print('diff > 25000, out of range')
    else:
        #print(diff)
        diffinsteps = diff/Hzperstep
        #print(diffinsteps)
        
        if diffinsteps > 0:
            direction = 'P'
        else:
            direction = 'D'
        #print(direction)    
        
        newsteps = round(abs(diffinsteps))
        #print(newsteps)
        
        newstring = '/1' + direction + str(newsteps) +'R\r\n'
        print(newstring)
        
        ser1.write(str.encode(newstring))
        
        waittime = abs(diff)/1400   #tuned
        #print(waittime)
        time.sleep(waittime)
        
        
def steptotargetPU2(targetPU2):
    stepcounter = 0
    while abs(targetPU2 - getrepratePU()) > 150:
        print('steptotargetPU2')
        steptotargetPU(targetPU2)
        stepcounter += 1
    else:
        print(stepcounter)
        steptotargetPU(targetPU2)
          
        
def steptotargetPR(targetPR):    
    Hzperstep = 791/50000 #tuned
    repratern = getrepratePR()
    print(repratern)
    diff = targetPR - repratern
    if abs(diff) < 150:  #arbitrary, small movements too inconsistent
        print('diff < 150, skip to PZT control')
    elif abs(diff) > 25000:   #arbitrary
        print('diff > 25000, out of range')
    else:
        #print(diff)
        diffinsteps = diff/Hzperstep
        #print(diffinsteps)
        
        if diffinsteps > 0:
            direction = 'D'
        else:
            direction = 'P'
        #print(direction)    
        
        newsteps = round(abs(diffinsteps))
        #print(newsteps)
        
        newstring = '/1' + direction + str(newsteps) +'R\r\n'
        print(newstring)
        
        ser2.write(str.encode(newstring))
        
        waittime = abs(diff)/1400   #tuned
        #print(waittime)
        time.sleep(waittime)
        
        
def steptotargetPR2(targetPR2):
    stepcounter = 0
    while abs(targetPR2 - getrepratePR()) > 150:
        print('steptotargetPU2')
        steptotargetPR(targetPR2)
        stepcounter += 1
    else:
        print(stepcounter)
        steptotargetPR(targetPR2)







# #For pump:
# startpump = getrepratePU()
# ser1.write(str.encode('/1D5000R\r\n'))
# time.sleep(3)
# endpump = getrepratePU()
# print(startpump)
# print(endpump)
# print(endpump - startpump)


# #For probe:
# startprobe = getrepratePR()
# ser2.write(str.encode('/1D50000R\r\n'))
# time.sleep(0.1)
# endprobe = getrepratePR()
# print(startprobe)
# print(endprobe)
# print(endprobe - startprobe)
        
        

        
        
# #how long to wait? About 1 sec per 1000 for PU
# repratern = getrepratePU()
# repratestart = repratern
# start = time.time()
# ser1.write(str.encode('/1D200000R\r\n'))
# while abs(getrepratePU() - repratern) > 10:
#     repratern = getrepratePU()
#     print(repratern)
# else:
#     end = time.time()
#     print(end - start)
#     print(repratern - repratestart)
        


# direction = 'P'
# newsteps = 10000

# newstring = '/1' + direction + str(round(newsteps)) + 'R\r\n'

# getrepratePU()



# ser1.write(str.encode('/1P5000R\r\n'))

# ser2.write(str.encode('/1P50000R\r\n'))

# ser1.close()
# ser2.close()

