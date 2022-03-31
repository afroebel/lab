# -*- coding: utf-8 -*-
"""
Created on Tue Nov 30 00:19:38 2021

@author: THz-FCS
"""

import pyvisa as visa 
import serial
import time


#frequencycounter
rm = visa.ResourceManager()
rm.list_resources()
inst = rm.open_resource('GPIB0::3::INSTR')


#ser2 is probe stepper
ser2 = serial.Serial(
    'COM7', 9600, 
    timeout = 3,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    bytesize=serial.EIGHTBITS)


def getrepratePR():
    inst.write("FU3")
    with inst.visalib.ignore_warning(inst.session, visa.constants.VI_SUCCESS_MAX_CNT):  #This took a while to figure out... 
        masterdata = inst.visalib.read(inst.session,17)
    a = str(masterdata[0])
    x = a.find("F")
    masterfreq = float(a[x+4:x+14])*10**7
    # print(masterfreq)
    return masterfreq


def steptotargetPR(targetPR):    
    Hzperstep = 791/50000 #tuned
    repratern = getrepratePR()
    print(repratern)
    diff = targetPR - repratern
    if abs(diff) < 10:  #arbitrary, small movements too inconsistent
        print('done')
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
    while abs(targetPR2 - getrepratePR()) > 10:
        print('steptotargetPR2')
        steptotargetPR(targetPR2)
        stepcounter += 1
    else:
        print(stepcounter)
        steptotargetPR(targetPR2)
        

print('starting rep rate '+str(getrepratePR()))

steptotargetPR2(int(79216400))   # pre-october state 79216400, more recent 79227900, previously used 79217800

print('ending rep rate '+str(getrepratePR()))
ser2.close()